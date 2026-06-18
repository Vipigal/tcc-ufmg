import json
import pandas as pd
from modules.filter import NoiseFilter


def _df():
    rows = [
        ("U1", "TV"), ("U1", "TA"),
        ("U2", "TV"), ("U2", "TA"),
        ("U3", "TV"), ("U3", "TB"),
        ("U4", "TV"),
    ]
    return pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"])


def test_user_filter_drops_inactive():
    nf = NoiseFilter(min_user_retweets=2)
    out = nf.apply(_df())
    assert "U4" not in set(out["author_id"])  # U4 só tem 1 retweet


def test_viral_tweets_are_preserved():
    nf = NoiseFilter(min_user_retweets=2)
    out = nf.apply(_df())
    # TV é retuitado por todos, mas agora é mantido (sinal relevante para a análise)
    assert "TV" in set(out["referenced_tweet_id"])


def test_stats_recorded():
    nf = NoiseFilter(min_user_retweets=2)
    nf.apply(_df())
    assert nf.stats["initial"]["users"] == 4
    assert nf.stats["after_user_filter"]["users"] == 3


def test_filter_save(tmp_path):
    nf = NoiseFilter(min_user_retweets=2)
    out = nf.apply(_df())
    nf.save(out, tmp_path)
    assert (tmp_path / "filtered_retweets.parquet").exists()
    stats = json.loads((tmp_path / "filter_stats.json").read_text())
    assert stats["after_user_filter"]["users"] == 3
