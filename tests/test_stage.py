from modules.stage import Stage


class DummyStage(Stage):
    """Estágio de brinquedo: conta quantas vezes computou e persiste um arquivo."""

    FILES = ("dummy.txt",)

    def __init__(self):
        self.compute_calls = 0

    def _compute(self, value):
        self.compute_calls += 1
        return value

    def _save(self, result, out_dir):
        (out_dir / "dummy.txt").write_text(str(result))

    def _load(self, out_dir):
        return (out_dir / "dummy.txt").read_text()


def test_cold_run_computes_and_persists(tmp_path):
    s = DummyStage()
    out = s.run("hello", out_dir=tmp_path)
    assert out == "hello"
    assert s.compute_calls == 1
    assert (tmp_path / "dummy.txt").exists()


def test_cache_hit_skips_compute(tmp_path):
    DummyStage().run("hello", out_dir=tmp_path)   # cria o cache
    s2 = DummyStage()
    out = s2.run("ignored", out_dir=tmp_path)      # deve carregar, não computar
    assert s2.compute_calls == 0
    assert out == "hello"                          # veio do disco, não do input


def test_force_recomputes_and_overwrites(tmp_path):
    DummyStage().run("v1", out_dir=tmp_path)
    s2 = DummyStage()
    out = s2.run("v2", out_dir=tmp_path, force=True)
    assert s2.compute_calls == 1
    assert out == "v2"
    assert (tmp_path / "dummy.txt").read_text() == "v2"


def test_force_cleans_stale_artifacts(tmp_path):
    # artefato antigo presente; force deve removê-lo antes de regravar
    (tmp_path / "dummy.txt").write_text("stale")
    s = DummyStage()
    s.run("fresh", out_dir=tmp_path, force=True)
    assert (tmp_path / "dummy.txt").read_text() == "fresh"
    assert s.compute_calls == 1
