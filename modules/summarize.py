"""Módulo 11 — síntese de cada (evento, cluster) por LLM (E3; D8 revisado em 2026-10-13).

O LLM **condensa** o material de um cluster para os rotuladores humanos; não categoriza.
Spec: `docs/superpowers/specs/2026-10-13-sintese-clusters-llm-design.md`.

Fluxo por (evento, cluster):

  1. `build_input` — junta o que a pipeline **calcula** (tamanho do cluster, atrição,
     contas mais retuitadas = soma de `rt_cluster` por autor) e o corpus hidratado em
     dois blocos: A = top-K (M8, mais amplificados) e B = cauda (M8b, característicos).
  2. `render_prompt` — preenche o template versionado (`prompts/sintese_cluster_v1.md`).
  3. runner — por padrão `ClaudeCliRunner` (`claude -p`, assinatura), com saída
     estruturada pelo `OUTPUT_SCHEMA`. Injetável, para os testes.
  4. `extract_citations` — confere os `[tweet_id]` citados contra o corpus do cluster;
     os inválidos são registrados, não apagados.
  5. grava em `cluster_summaries` (uma linha por evento × cluster × modelo × prompt).

`FILES = ()` como no M9/M10: o cache é o banco. `summarize()` só chama o modelo para os
pares sem linha `ok`; `redo=True` refaz. Falha → 1 nova tentativa → linha `error` com a
saída bruta; nunca se inventa saída.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from modules.stage import Stage

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "sintese_cluster_v1.md"
PROMPT_VERSION = "v1"
DEFAULT_MODEL = "claude-sonnet-5-5"
N_ACCOUNTS = 15                   # linhas da tabela de contas no prompt
CONFIANCA = ("alta", "media", "baixa")

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "sintese": {"type": "string"},
        "contas_prevalentes": {"type": "string"},
        "inclinacao_politica": {
            "type": "object",
            "properties": {"texto": {"type": "string"},
                           "confianca": {"type": "string", "enum": list(CONFIANCA)}},
            "required": ["texto", "confianca"],
        },
        "limites": {"type": "string"},
    },
    "required": ["sintese", "contas_prevalentes", "inclinacao_politica", "limites"],
}

SYSTEM_PROMPT = ("Você é um assistente de pesquisa em computação social. Siga estritamente "
                 "as instruções da mensagem e responda só com o JSON pedido.")

BLOCK_SQL = """
    SELECT s.tweet_id, s.rank, s.rt_cluster, s.rt_graph, {lift} AS lift,
           t.text, t.author_id, u.username, u.name, u.description, u.verified
    FROM {table} s
    LEFT JOIN tweets t ON t.tweet_id = s.tweet_id
    LEFT JOIN users u  ON u.user_id = t.author_id
    WHERE s.event_slug = ? AND s.community = ?
    ORDER BY s.rank"""


class RunnerError(RuntimeError):
    """O modelo não devolveu uma saída utilizável."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── 1. insumo ─────────────────────────────────────────────────────────────
def _block(db, table, slug, community, baseline):
    lift = "s.lift" if table == "event_tail_tweets" else "NULL"
    rows = db.conn.execute(BLOCK_SQL.format(table=table, lift=lift), (slug, community)).fetchall()
    tweets = []
    for r in rows:
        if r["text"] is None:                                  # não hidratado / não devolvido
            continue
        lift_v = (r["lift"] if r["lift"] is not None
                  else (r["rt_cluster"] / r["rt_graph"]) / baseline if r["rt_graph"] and baseline
                  else None)
        tweets.append({
            "tweet_id": r["tweet_id"], "rank": int(r["rank"]), "rt_cluster": int(r["rt_cluster"]),
            "lift": lift_v, "text": r["text"], "author_id": r["author_id"],
            "username": r["username"], "name": r["name"], "description": r["description"],
            "verified": None if r["verified"] is None else bool(r["verified"]),
        })
    return tweets, len(rows)


def _top_accounts(tweets, n=N_ACCOUNTS):
    acc = {}
    for t in tweets:
        a = acc.setdefault(t["author_id"], {
            "author_id": t["author_id"], "username": t["username"], "name": t["name"],
            "description": t["description"], "verified": t["verified"],
            "rt_cluster": 0, "n_tweets": 0})
        a["rt_cluster"] += t["rt_cluster"]
        a["n_tweets"] += 1
    ranked = sorted(acc.values(), key=lambda a: (-a["rt_cluster"], str(a["author_id"])))
    return ranked[:n]


def build_input(db, slug: str, community: int, cluster_stats: dict) -> dict:
    """Tudo que o prompt precisa sobre um (evento, cluster). `cluster_stats` vem de
    `top_tweets_stats.json` (n_nodes, frac_nodes) + `tail_tweets_stats.json`
    (baseline_share = RT_c / RT_graph, para o lift dos tweets do top-K)."""
    ev = db.conn.execute("SELECT name, event_date FROM events WHERE slug = ?", (slug,)).fetchone()
    base = cluster_stats.get("baseline_share")
    amp, n_amp = _block(db, "event_top_tweets", slug, community, base)
    car, n_car = _block(db, "event_tail_tweets", slug, community, base)
    return {
        "evento_slug": slug,
        "evento_nome": ev["name"] if ev else slug,
        "evento_data": ev["event_date"] if ev else "",
        "cluster_id": int(community),
        "n_usuarios": int(cluster_stats["n_nodes"]),
        "frac_usuarios": float(cluster_stats["frac_nodes"]),
        "top_accounts": _top_accounts(amp + car),
        "amplificados": amp,
        "caracteristicos": car,
        "n_selecionados": n_amp + n_car,
        "n_indisponiveis": (n_amp - len(amp)) + (n_car - len(car)),
        "corpus_ids": sorted({t["tweet_id"] for t in amp + car}),
    }


# ── 2. prompt ─────────────────────────────────────────────────────────────
def _num(x, nd=2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _one_line(s) -> str:
    return " ".join(str(s or "").split())


def _handle(t) -> str:
    return f"@{t['username']}" if t.get("username") else f"(autor sem perfil, id {t['author_id']})"


def _tweet_line(t) -> str:
    lift = _num(t["lift"]) if t["lift"] is not None else "?"
    return (f"[{t['tweet_id']}] {_handle(t)} (RTs na comunidade: {t['rt_cluster']}; "
            f"lift {lift}) — {_one_line(t['text'])}")


def _account_line(a) -> str:
    verified = {True: "sim", False: "não", None: "?"}[a["verified"]]
    return " | ".join([_handle(a), _one_line(a["name"]) or "?",
                       _one_line(a["description"]) or "—", verified, str(a["rt_cluster"])])


def render_prompt(template: str, inp: dict) -> str:
    values = {
        "evento_nome": inp["evento_nome"],
        "evento_data": inp["evento_data"],
        "cluster_id": str(inp["cluster_id"]),
        "n_usuarios": f"{inp['n_usuarios']:,}".replace(",", "."),
        "frac_usuarios": _num(100 * inp["frac_usuarios"], 1) + "%",
        "tabela_contas": "\n".join(map(_account_line, inp["top_accounts"])) or "(nenhuma)",
        "n_indisponiveis": str(inp["n_indisponiveis"]),
        "n_selecionados": str(inp["n_selecionados"]),
        "bloco_amplificados": "\n".join(map(_tweet_line, inp["amplificados"])) or "(vazio)",
        "bloco_caracteristicos": "\n".join(map(_tweet_line, inp["caracteristicos"])) or "(vazio)",
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


# ── 4. citações e schema ──────────────────────────────────────────────────
def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def extract_citations(output: dict) -> list[str]:
    """IDs citados em qualquer campo: `[123]`, `[123, 456]`, `[123; 456]`."""
    ids = set()
    for s in _strings(output):
        for group in re.findall(r"\[([\d,;\s]+)\]", s):
            ids.update(re.findall(r"\d+", group))
    return sorted(ids)


def _check_schema(o) -> None:
    if not isinstance(o, dict):
        raise RunnerError("saída não é um objeto JSON")
    for k in OUTPUT_SCHEMA["required"]:
        if k not in o:
            raise RunnerError(f"campo ausente: {k}")
    for k in ("sintese", "contas_prevalentes", "limites"):
        if not isinstance(o[k], str):
            raise RunnerError(f"campo não é texto: {k}")
    inc = o["inclinacao_politica"]
    if (not isinstance(inc, dict) or not isinstance(inc.get("texto"), str)
            or inc.get("confianca") not in CONFIANCA):
        raise RunnerError(f"inclinacao_politica fora do schema: {inc!r}")


# ── 3. runner padrão: Claude Code headless (assinatura) ───────────────────
class ClaudeCliRunner:
    """Chama `claude -p` com o prompt no stdin, sem ferramentas, sem sessão salva e sem
    settings/CLAUDE.md (roda num diretório temporário vazio). `temperature` não é
    controlável por esse caminho; a reprodutibilidade vem de guardar prompt e resposta."""

    def __init__(self, model: str = DEFAULT_MODEL, timeout_s: int = 600, binary: str = "claude"):
        self.model = model
        self.timeout_s = timeout_s
        self.binary = binary

    def __call__(self, prompt: str, schema: dict) -> dict:
        cmd = [self.binary, "-p", "--model", self.model, "--output-format", "json",
               "--json-schema", json.dumps(schema), "--tools", "",
               "--system-prompt", SYSTEM_PROMPT, "--no-session-persistence",
               "--setting-sources", ""]
        with tempfile.TemporaryDirectory() as cwd:
            try:
                p = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                   cwd=cwd, timeout=self.timeout_s)
            except subprocess.TimeoutExpired as e:
                raise RunnerError(f"timeout após {self.timeout_s}s") from e
        if p.returncode != 0:
            raise RunnerError(f"exit {p.returncode}: {p.stderr.strip() or p.stdout.strip()}")
        try:
            res = json.loads(p.stdout)
        except json.JSONDecodeError as e:
            raise RunnerError(f"stdout não é JSON: {p.stdout[:500]}") from e
        if res.get("is_error") or res.get("structured_output") is None:
            raise RunnerError(f"sem structured_output: {p.stdout[:1000]}")
        return {"output": res["structured_output"], "raw": p.stdout}


# ── 5. estágio ────────────────────────────────────────────────────────────
class ClusterSummarizer(Stage):
    """M11 — uma síntese por cluster de um evento, gravada em `cluster_summaries`."""

    FILES = ()                    # o cache é o banco (ver docstring do módulo)

    def __init__(self, db, runner=None, template: str | None = None,
                 model: str = DEFAULT_MODEL, prompt_version: str = PROMPT_VERSION,
                 retries: int = 1, redo: bool = False):
        self.db = db
        self.model = model
        self.runner = runner or ClaudeCliRunner(model)
        self.template = template if template is not None else PROMPT_PATH.read_text()
        self.prompt_version = prompt_version
        self.retries = retries
        self.redo = redo

    def _done(self, slug, community) -> bool:
        return self.db.conn.execute(
            "SELECT 1 FROM cluster_summaries WHERE event_slug=? AND community=? AND model=? "
            "AND prompt_version=? AND status='ok'",
            (slug, community, self.model, self.prompt_version)).fetchone() is not None

    def _call(self, prompt):
        last = None
        for _ in range(1 + self.retries):
            try:
                res = self.runner(prompt, OUTPUT_SCHEMA)
                _check_schema(res["output"])
                return res, None
            except RunnerError as e:
                last = e
        return None, last

    def summarize_one(self, slug: str, community: int, cluster_stats: dict) -> dict:
        inp = build_input(self.db, slug, community, cluster_stats)
        prompt = render_prompt(self.template, inp)
        res, err = self._call(prompt)
        row = {
            "event_slug": slug, "community": int(community), "model": self.model,
            "prompt_version": self.prompt_version,
            "status": "ok" if res else "error",
            "output_json": json.dumps(res["output"], ensure_ascii=False) if res else None,
            "raw_response": res["raw"] if res else str(err),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "input_json": json.dumps(inp, ensure_ascii=False),
            "cited_ids_json": None, "invalid_ids_json": None,
            "generated_at": _now(),
        }
        report = {"event_slug": slug, "community": int(community), "status": row["status"],
                  "n_corpus": len(inp["corpus_ids"]), "n_cited": 0, "n_invalid": 0}
        if res:
            cited = extract_citations(res["output"])
            invalid = sorted(set(cited) - set(inp["corpus_ids"]))
            row["cited_ids_json"] = json.dumps(cited)
            row["invalid_ids_json"] = json.dumps(invalid)
            report.update(n_cited=len(cited), n_invalid=len(invalid))
        self.db.upsert_cluster_summary(row)
        return report

    def summarize(self, slug: str, clusters: dict) -> list[dict]:
        """`clusters`: {community (str): cluster_stats}, na ordem em que devem rodar."""
        reports = []
        for c, cs in clusters.items():
            c = int(c)
            if not self.redo and self._done(slug, c):
                reports.append({"event_slug": slug, "community": c, "status": "cached"})
                continue
            reports.append(self.summarize_one(slug, c, cs))
        return reports

    # --- hooks de cache (Stage): FILES vazio → run() sempre computa ---------
    def _compute(self, slug, clusters):
        return self.summarize(slug, clusters)

    def _save(self, result, out_dir) -> None:
        pass                      # já gravado no banco, par a par

    def _load(self, out_dir):
        raise NotImplementedError("FILES vazio — este estágio nunca carrega de disco")
