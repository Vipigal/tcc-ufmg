import requests
import os
import time
import json
import csv
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
BASE_URL = "https://api.x.com/2"

# ── Campos solicitados por tipo de recurso ──────────────────────────────
# Selecionar mais ou menos campos NAO altera o custo; a cobranca e por
# recurso retornado ($0.005/tweet, $0.010/user), nao por campo.

TWEET_FIELDS = ",".join([
    "author_id",
    "conversation_id",
    "created_at",
    "entities",          # hashtags, mentions, urls, annotations — sem expansion
    "geo",
    "in_reply_to_user_id",
    "lang",
    "public_metrics",
    "possibly_sensitive",
    "referenced_tweets",
    "reply_settings",
    "source",
    "text",
    "withheld",
])

USER_FIELDS = ",".join([
    "created_at",
    "description",
    "entities",
    "location",
    "name",
    "profile_image_url",
    "protected",
    "public_metrics",
    "url",
    "username",
    "verified",
    "verified_type",
])

# ── Constantes de custo (referencia para estimativas) ───────────────────
COST_PER_TWEET = 0.005   # USD por tweet lido
COST_PER_USER  = 0.010   # USD por user lido


# ── Helpers internos ────────────────────────────────────────────────────

def _headers():
    return {"Authorization": f"Bearer {BEARER_TOKEN}"}


def _handle_rate_limit(response):
    """Aguarda automaticamente se atingiu rate limit (429)."""
    if response.status_code == 429:
        reset = int(response.headers.get("x-rate-limit-reset", 0))
        wait = max(reset - int(time.time()), 1) + 1
        print(f"  Rate limit atingido. Aguardando {wait}s...")
        time.sleep(wait)
        return True
    return False


def _batches(lst, size=100):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def _load_checkpoint(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_checkpoint(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


# ── Funcoes de fetch unitarias (1 batch) ────────────────────────────────

def fetch_tweets_batch(tweet_ids):
    """Busca ate 100 tweets SEM expansions.

    Custo: $0.005 x len(tweet_ids).
    Retorna o tweet object completo (text, entities, public_metrics, etc.)
    sem trazer users/media/polls no includes — isso evita cobranças extras.
    """
    if not tweet_ids:
        return None

    params = {
        "ids": ",".join(str(tid) for tid in tweet_ids[:100]),
        "tweet.fields": TWEET_FIELDS,
    }

    while True:
        resp = requests.get(f"{BASE_URL}/tweets", headers=_headers(), params=params)
        if _handle_rate_limit(resp):
            continue
        resp.raise_for_status()
        return resp.json()


def fetch_users_batch(user_ids):
    """Busca ate 100 usuarios.

    Custo: $0.010 x len(user_ids).
    """
    if not user_ids:
        return None

    params = {
        "ids": ",".join(str(uid) for uid in user_ids[:100]),
        "user.fields": USER_FIELDS,
    }

    while True:
        resp = requests.get(f"{BASE_URL}/users", headers=_headers(), params=params)
        if _handle_rate_limit(resp):
            continue
        resp.raise_for_status()
        return resp.json()


# ── Orquestradores com checkpoint ───────────────────────────────────────

def hydrate_tweets(tweet_ids, output_path="hydrated_tweets.jsonl", checkpoint_path="checkpoint_tweets.json"):
    """Hidrata tweets SEM expansions — apenas dados do tweet.

    Cada tweet retorna text, entities (hashtags, mentions, urls),
    public_metrics, lang, source, geo, etc. por $0.005/tweet.

    Progresso salvo em checkpoint a cada 10 batches.
    Resultado gravado em JSONL (1 tweet JSON por linha) para append eficiente.

    Args:
        tweet_ids: lista de IDs de tweets.
        output_path: arquivo JSONL de saida.
        checkpoint_path: arquivo de checkpoint.

    Returns:
        int com o total de tweets hidratados.
    """
    tweet_ids = list({str(tid) for tid in tweet_ids})

    checkpoint = _load_checkpoint(checkpoint_path)
    already_fetched = set(checkpoint.get("fetched_ids", []))

    remaining = [tid for tid in tweet_ids if tid not in already_fetched]
    batches_list = list(_batches(remaining))
    total_batches = len(batches_list)
    total_hydrated = checkpoint.get("total_hydrated", 0)

    cost = len(remaining) * COST_PER_TWEET
    print(f"Tweets — Total: {len(tweet_ids)} | Ja buscados: {len(already_fetched)} | Restantes: {len(remaining)}")
    print(f"  Custo estimado restante: ${cost:.2f} ({total_batches} batches)")

    # Abre JSONL em modo append para nao perder dados ja escritos
    with open(output_path, "a", encoding="utf-8") as out:
        for i, batch in enumerate(batches_list):
            print(f"  Batch {i + 1}/{total_batches} ({len(batch)} IDs)...")

            result = fetch_tweets_batch(batch)
            if result is None:
                continue

            for tweet in result.get("data", []):
                out.write(json.dumps(tweet, ensure_ascii=False) + "\n")
                total_hydrated += 1

            already_fetched.update(batch)

            if (i + 1) % 10 == 0:
                out.flush()
                _save_checkpoint(checkpoint_path, {
                    "fetched_ids": list(already_fetched),
                    "total_hydrated": total_hydrated,
                })
                print(f"    Checkpoint salvo ({total_hydrated} tweets)")

            if i < total_batches - 1:
                time.sleep(1)

    # Checkpoint final
    _save_checkpoint(checkpoint_path, {
        "fetched_ids": list(already_fetched),
        "total_hydrated": total_hydrated,
    })
    print(f"Concluido: {total_hydrated} tweets em '{output_path}'")
    return total_hydrated


def hydrate_users(user_ids, output_path="hydrated_users.json", checkpoint_path="checkpoint_users.json"):
    """Hidrata uma lista de user IDs unicos.

    Custo: $0.010 por user. Deduplica IDs antes de buscar.
    Salva um dict {user_id: user_object} em JSON.

    Args:
        user_ids: lista de IDs de usuarios (aceita duplicatas, serao removidas).
        output_path: arquivo JSON de saida.
        checkpoint_path: arquivo de checkpoint.

    Returns:
        dict mapeando user_id -> user object.
    """
    user_ids = list({str(uid) for uid in user_ids})

    checkpoint = _load_checkpoint(checkpoint_path)
    already_fetched = set(checkpoint.get("fetched_ids", []))
    users_map = checkpoint.get("users", {})

    remaining = [uid for uid in user_ids if uid not in already_fetched]
    batches_list = list(_batches(remaining))
    total_batches = len(batches_list)

    cost = len(remaining) * COST_PER_USER
    print(f"Users — Total unicos: {len(user_ids)} | Ja buscados: {len(already_fetched)} | Restantes: {len(remaining)}")
    print(f"  Custo estimado restante: ${cost:.2f} ({total_batches} batches)")

    for i, batch in enumerate(batches_list):
        print(f"  Batch {i + 1}/{total_batches} ({len(batch)} IDs)...")

        result = fetch_users_batch(batch)
        if result is None:
            continue

        for user in result.get("data", []):
            users_map[user["id"]] = user

        already_fetched.update(batch)

        if (i + 1) % 10 == 0:
            _save_checkpoint(checkpoint_path, {
                "fetched_ids": list(already_fetched),
                "users": users_map,
            })
            print(f"    Checkpoint salvo ({len(users_map)} usuarios)")

        if i < total_batches - 1:
            time.sleep(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(users_map, f, ensure_ascii=False, indent=2)
    print(f"Concluido: {len(users_map)} usuarios em '{output_path}'")

    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    return users_map


# ── Merge e exportacao ──────────────────────────────────────────────────

def load_hydrated_tweets(path="hydrated_tweets.jsonl"):
    """Carrega tweets do JSONL em uma lista de dicts."""
    tweets = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tweets.append(json.loads(line))
    return tweets


def load_hydrated_users(path="hydrated_users.json"):
    """Carrega users do JSON em um dict {id: user}."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_to_csv(tweets_path="hydrated_tweets.jsonl", users_path="hydrated_users.json", output_csv="hydrated_tweets.csv"):
    """Junta tweets + autores em um CSV flat para analise.

    Le os arquivos gerados por hydrate_tweets e hydrate_users,
    faz o join por author_id e achata os campos aninhados.
    """
    tweets = load_hydrated_tweets(tweets_path)
    users = load_hydrated_users(users_path)

    rows = []
    for tw in tweets:
        author = users.get(tw.get("author_id", ""), {})
        metrics = tw.get("public_metrics", {})
        entities = tw.get("entities", {})
        author_metrics = author.get("public_metrics", {})

        hashtags = [h["tag"] for h in entities.get("hashtags", [])]
        mentions = [m["username"] for m in entities.get("mentions", [])]
        urls = [u.get("expanded_url", u.get("url", "")) for u in entities.get("urls", [])]
        annotations = [a["normalized_text"] for a in entities.get("annotations", [])]

        rows.append({
            "tweet_id": tw.get("id"),
            "text": tw.get("text"),
            "created_at": tw.get("created_at"),
            "lang": tw.get("lang"),
            "source": tw.get("source"),
            "conversation_id": tw.get("conversation_id"),
            "in_reply_to_user_id": tw.get("in_reply_to_user_id"),
            "possibly_sensitive": tw.get("possibly_sensitive"),
            "reply_settings": tw.get("reply_settings"),
            "retweet_count": metrics.get("retweet_count"),
            "reply_count": metrics.get("reply_count"),
            "like_count": metrics.get("like_count"),
            "quote_count": metrics.get("quote_count"),
            "bookmark_count": metrics.get("bookmark_count"),
            "impression_count": metrics.get("impression_count"),
            "hashtags": ";".join(hashtags),
            "mentions": ";".join(mentions),
            "urls": ";".join(urls),
            "annotations": ";".join(annotations),
            "geo_place_id": (tw.get("geo") or {}).get("place_id", ""),
            "author_id": tw.get("author_id"),
            "author_name": author.get("name"),
            "author_username": author.get("username"),
            "author_description": author.get("description"),
            "author_location": author.get("location"),
            "author_created_at": author.get("created_at"),
            "author_verified": author.get("verified"),
            "author_verified_type": author.get("verified_type"),
            "author_protected": author.get("protected"),
            "author_profile_image_url": author.get("profile_image_url"),
            "author_url": author.get("url"),
            "author_followers_count": author_metrics.get("followers_count"),
            "author_following_count": author_metrics.get("following_count"),
            "author_tweet_count": author_metrics.get("tweet_count"),
            "author_listed_count": author_metrics.get("listed_count"),
        })

    if not rows:
        print("Nenhum tweet para exportar.")
        return

    fieldnames = list(rows[0].keys())
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV exportado: '{output_csv}' ({len(rows)} linhas)")


def estimate_cost(tweet_ids, author_ids):
    """Estima o custo total da hidratacao sem fazer nenhuma chamada.

    Args:
        tweet_ids: lista de tweet IDs (pode ter duplicatas).
        author_ids: lista de author IDs (pode ter duplicatas).

    Returns:
        dict com a estimativa detalhada.
    """
    unique_tweets = len(set(str(t) for t in tweet_ids))
    unique_users = len(set(str(u) for u in author_ids))

    tweet_cost = unique_tweets * COST_PER_TWEET
    user_cost = unique_users * COST_PER_USER
    total = tweet_cost + user_cost

    tweet_batches = (unique_tweets + 99) // 100
    user_batches = (unique_users + 99) // 100

    # Rate limits: tweets 3500/15min, users 300/15min
    # Com sleep(1) entre batches, o bottleneck e o sleep
    tweet_time_s = tweet_batches  # 1s por batch
    user_time_s = user_batches
    total_time_s = tweet_time_s + user_time_s

    est = {
        "unique_tweets": unique_tweets,
        "unique_users": unique_users,
        "tweet_batches": tweet_batches,
        "user_batches": user_batches,
        "tweet_cost_usd": tweet_cost,
        "user_cost_usd": user_cost,
        "total_cost_usd": total,
        "estimated_time_min": total_time_s / 60,
    }

    print(f"=== Estimativa de custo ===")
    print(f"Tweets: {unique_tweets:,} unicos → {tweet_batches:,} batches → ${tweet_cost:,.2f}")
    print(f"Users:  {unique_users:,} unicos → {user_batches:,} batches → ${user_cost:,.2f}")
    print(f"Total:  ${total:,.2f}")
    print(f"Tempo estimado: ~{total_time_s / 60:.0f} min ({total_time_s:,}s com 1s/batch)")

    return est
