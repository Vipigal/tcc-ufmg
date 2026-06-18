import pandas as pd
from modules.load import RetweetLoader


def test_loader_keeps_only_retweets(tmp_path):
    csv = tmp_path / "event.csv"
    csv.write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "111,2023-01-08 18:00:00-03:00,1001,[<ReferencedTweet id=5001 type=retweeted]\n"
        "112,2023-01-08 18:01:00-03:00,1002,[<ReferencedTweet id=5002 type=replied_to]\n"
        "113,2023-01-08 18:02:00-03:00,1003,[<ReferencedTweet id=5003 type=quoted]\n"
    )
    df = RetweetLoader(csv).load()
    assert list(df.columns) == ["author_id", "referenced_tweet_id", "created_at"]
    assert len(df) == 1
    assert df.loc[0, "author_id"] == "1001"
    assert df.loc[0, "referenced_tweet_id"] == "5001"
    assert "5002" not in set(df["referenced_tweet_id"])
    assert "5003" not in set(df["referenced_tweet_id"])


def test_loader_drops_null_and_malformed_referenced_tweets(tmp_path):
    """Bordas do parsing exercitadas pelo caminho real (load), não por função à parte."""
    csv = tmp_path / "event.csv"
    csv.write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "111,2023-01-08 18:00:00-03:00,1001,[<ReferencedTweet id=5001 type=retweeted]\n"
        "114,2023-01-08 18:03:00-03:00,1004,\n"
        "115,2023-01-08 18:04:00-03:00,1005,not-a-referenced-tweet\n"
    )
    df = RetweetLoader(csv).load()
    assert len(df) == 1
    assert set(df["author_id"]) == {"1001"}


def test_loader_reads_directory(tmp_path):
    (tmp_path / "a.csv").write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "1,2023-01-08 18:00:00-03:00,1,[<ReferencedTweet id=9 type=retweeted]\n"
    )
    (tmp_path / "b.csv").write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "2,2023-01-08 18:00:00-03:00,2,[<ReferencedTweet id=8 type=retweeted]\n"
    )
    df = RetweetLoader(tmp_path).load()
    assert len(df) == 2


def test_loader_save(tmp_path):
    csv = tmp_path / "event.csv"
    csv.write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "111,2023-01-08 18:00:00-03:00,1001,[<ReferencedTweet id=5001 type=retweeted]\n"
    )
    loader = RetweetLoader(csv)
    df = loader.load()
    loader.save(df, tmp_path / "proc")
    assert (tmp_path / "proc" / "retweets.parquet").exists()
    back = pd.read_parquet(tmp_path / "proc" / "retweets.parquet")
    assert len(back) == 1
