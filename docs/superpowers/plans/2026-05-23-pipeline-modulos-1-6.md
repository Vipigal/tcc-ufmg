# Pipeline de Co-retweet — Módulos 1 a 6 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir os seis primeiros módulos da pipeline (carga de retweets, filtragem de ruído, matriz bipartida, projeção Jaccard, backbone e detecção de comunidades) como classes Python independentes e testadas.

**Architecture:** Cada etapa é um arquivo em `modules/` com uma classe principal. Os módulos operam em memória e persistem sob demanda em `data/processed/<evento>/`. O contrato de dados é: DataFrame de retweets → DataFrame filtrado → `BipartiteGraph` (matriz esparsa) → `ProjectedGraph` (matriz Jaccard) → `ProjectedGraph` (backbone) → `CommunityResult` (igraph + partição). O `user_index` (posição inteira → `author_id`) é propagado a partir do Módulo 3 para rastrear nós de volta aos usuários reais.

**Tech Stack:** Python 3.10, pandas, numpy, scipy.sparse, python-igraph, pyarrow (Parquet), pytest.

**Specs:** `docs/superpowers/specs/2026-05-23-pipeline-modulos-1-3-design.md`, `docs/superpowers/specs/2026-05-23-pipeline-modulos-4-6-design.md`.

---

## Task 1: Setup do projeto e scaffolding de testes

**Files:**
- Create: `modules/__init__.py`
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Criar `modules/__init__.py` vazio**

Arquivo vazio (transforma `modules/` em pacote importável):

```python
```

- [ ] **Step 2: Criar `requirements.txt`**

```
pandas
numpy
scipy
pyarrow
python-igraph>=0.11
requests
python-dotenv
pytest
```

- [ ] **Step 3: Criar `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 4: Instalar dependências**

Run: `.venv/bin/pip install -r requirements.txt`
Expected: instalação concluída sem erro; `scipy`, `pyarrow`, `igraph`, `pytest` presentes.

- [ ] **Step 5: Escrever um smoke test que prova que o import funciona**

`tests/test_smoke.py`:

```python
def test_imports_work():
    import numpy
    import pandas
    import scipy.sparse
    import igraph
    assert True
```

- [ ] **Step 6: Rodar o smoke test**

Run: `.venv/bin/pytest tests/test_smoke.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add modules/__init__.py requirements.txt pytest.ini tests/test_smoke.py
git commit -m "chore: setup de dependências e scaffolding de testes da pipeline"
```

---

## Task 2: Módulo 1 — `RetweetLoader`

**Files:**
- Create: `modules/load.py`
- Test: `tests/test_load.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_load.py`:

```python
import pandas as pd
from modules.load import RetweetLoader, parse_referenced_tweets


def test_parse_referenced_tweets_extracts_id_and_type():
    val = "[<ReferencedTweet id=5001 type=retweeted]"
    assert parse_referenced_tweets(val) == [("5001", "retweeted")]


def test_parse_referenced_tweets_empty():
    assert parse_referenced_tweets(None) == []
    assert parse_referenced_tweets(float("nan")) == []


def test_loader_keeps_only_retweets(tmp_path):
    csv = tmp_path / "event.csv"
    csv.write_text(
        "conversation_id,Created_at_convert,author_id,referenced_tweets\n"
        "111,2023-01-08 18:00:00-03:00,1001,[<ReferencedTweet id=5001 type=retweeted]\n"
        "112,2023-01-08 18:01:00-03:00,1002,[<ReferencedTweet id=5002 type=replied_to]\n"
        "113,2023-01-08 18:02:00-03:00,1003,[<ReferencedTweet id=5003 type=quoted]\n"
        "114,2023-01-08 18:03:00-03:00,1004,\n"
    )
    df = RetweetLoader(csv).load()
    assert list(df.columns) == ["author_id", "referenced_tweet_id", "created_at"]
    assert len(df) == 1
    assert df.loc[0, "author_id"] == "1001"
    assert df.loc[0, "referenced_tweet_id"] == "5001"


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
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_load.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.load'`.

- [ ] **Step 3: Implementar `modules/load.py`**

```python
"""Módulo 1 — carga e filtragem para retweets."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

_REF_RE = re.compile(r"<ReferencedTweet id=(\d+) type=(\w+)")


def parse_referenced_tweets(value) -> list[tuple[str, str]]:
    """Extrai (id, type) do repr Python do campo referenced_tweets.

    O campo NÃO é JSON; é um repr de objeto, ex.:
        [<ReferencedTweet id=123 type=retweeted]
    Retorna lista de tuplas (id, type); vazia se nulo/sem match.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [(m.group(1), m.group(2)) for m in _REF_RE.finditer(str(value))]


def _resolve_paths(csv_paths) -> list[Path]:
    if isinstance(csv_paths, (str, Path)):
        p = Path(csv_paths)
        if p.is_dir():
            return sorted(p.glob("*.csv"))
        return [p]
    return [Path(x) for x in csv_paths]


class RetweetLoader:
    """Lê os CSV(s) de um evento e mantém apenas os retweets.

    Aceita um caminho de arquivo, uma lista de caminhos ou um diretório
    (carrega todos os .csv contidos). Um evento pode ter vários CSVs.
    """

    def __init__(self, csv_paths):
        self.paths = _resolve_paths(csv_paths)

    def load(self) -> pd.DataFrame:
        frames = [pd.read_csv(p, dtype=str) for p in self.paths]
        raw = pd.concat(frames, ignore_index=True)

        # Extração vetorizada do primeiro referenced tweet de cada linha.
        # Retweets têm uma única referência, de tipo "retweeted".
        ext = raw["referenced_tweets"].str.extract(
            r"<ReferencedTweet id=(?P<rid>\d+) type=(?P<rtype>\w+)"
        )
        mask = ext["rtype"] == "retweeted"

        df = pd.DataFrame(
            {
                "author_id": raw.loc[mask, "author_id"].astype("string").values,
                "referenced_tweet_id": ext.loc[mask, "rid"].astype("string").values,
                "created_at": pd.to_datetime(
                    raw.loc[mask, "Created_at_convert"], utc=True
                ).values,
            }
        )
        return df.reset_index(drop=True)

    def save(self, df: pd.DataFrame, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "retweets.parquet"
        df.to_parquet(path, index=False)
        return path
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_load.py -v`
Expected: PASS (5 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/load.py tests/test_load.py
git commit -m "feat: módulo 1 RetweetLoader (carga e filtragem para retweets)"
```

---

## Task 3: Módulo 2 — `NoiseFilter`

**Files:**
- Create: `modules/filter.py`
- Test: `tests/test_filter.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_filter.py`:

```python
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
    nf = NoiseFilter(min_user_retweets=2, viral_user_fraction=0.9)
    out = nf.apply(_df())
    assert "U4" not in set(out["author_id"])  # U4 só tem 1 retweet


def test_viral_filter_drops_ubiquitous_tweet():
    nf = NoiseFilter(min_user_retweets=2, viral_user_fraction=0.9)
    out = nf.apply(_df())
    assert "TV" not in set(out["referenced_tweet_id"])
    assert set(out["referenced_tweet_id"]) == {"TA", "TB"}


def test_stats_recorded():
    nf = NoiseFilter(min_user_retweets=2, viral_user_fraction=0.9)
    nf.apply(_df())
    assert nf.stats["initial"]["users"] == 4
    assert nf.stats["after_user_filter"]["users"] == 3
    assert nf.stats["after_viral_filter"]["rows"] == 3


def test_filter_save(tmp_path):
    nf = NoiseFilter(min_user_retweets=2, viral_user_fraction=0.9)
    out = nf.apply(_df())
    nf.save(out, tmp_path)
    assert (tmp_path / "filtered_retweets.parquet").exists()
    stats = json.loads((tmp_path / "filter_stats.json").read_text())
    assert stats["after_viral_filter"]["rows"] == 3
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_filter.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.filter'`.

- [ ] **Step 3: Implementar `modules/filter.py`**

```python
"""Módulo 2 — filtragem de ruído (usuários inativos + tweets virais)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _counts(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "users": int(df["author_id"].nunique()),
        "tweets": int(df["referenced_tweet_id"].nunique()),
    }


class NoiseFilter:
    """Dois filtros sequenciais: usuários inativos e tweets virais espúrios."""

    def __init__(self, min_user_retweets: int = 3, viral_user_fraction: float = 0.30):
        self.min_user_retweets = min_user_retweets
        self.viral_user_fraction = viral_user_fraction
        self.stats: dict = {}

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        self.stats = {"initial": _counts(df)}

        # Filtro 1 — usuários com menos de N retweets (ações)
        user_size = df.groupby("author_id")["referenced_tweet_id"].transform("size")
        df = df[user_size >= self.min_user_retweets]
        self.stats["after_user_filter"] = _counts(df)

        # Filtro 2 — tweets retuitados por mais de X% dos usuários remanescentes
        n_users = df["author_id"].nunique()
        max_users = self.viral_user_fraction * n_users
        users_per_tweet = df.groupby("referenced_tweet_id")["author_id"].transform("nunique")
        df = df[users_per_tweet <= max_users]
        self.stats["after_viral_filter"] = _counts(df)

        return df.reset_index(drop=True)

    def save(self, df: pd.DataFrame, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / "filtered_retweets.parquet", index=False)
        with open(out / "filter_stats.json", "w") as f:
            json.dump(self.stats, f, indent=2)
        return out / "filtered_retweets.parquet"
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_filter.py -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/filter.py tests/test_filter.py
git commit -m "feat: módulo 2 NoiseFilter (filtragem de usuários e tweets virais)"
```

---

## Task 4: Módulo 3 — `BipartiteBuilder` e `BipartiteGraph`

**Files:**
- Create: `modules/bipartite.py`
- Test: `tests/test_bipartite.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_bipartite.py`:

```python
import scipy.sparse as sp
import pandas as pd
from modules.bipartite import BipartiteBuilder


def test_build_binary_matrix():
    df = pd.DataFrame(
        [("U1", "T1"), ("U1", "T2"), ("U2", "T1"), ("U2", "T1")],
        columns=["author_id", "referenced_tweet_id"],
    )
    bg = BipartiteBuilder().build(df)
    assert bg.B.shape == (2, 2)
    assert bg.B.nnz == 3                # (U1,T1),(U1,T2),(U2,T1); duplicata colapsada
    assert bg.B.max() == 1             # binária
    assert set(bg.user_index) == {"U1", "U2"}
    assert set(bg.tweet_index) == {"T1", "T2"}


def test_build_matrix_alignment():
    df = pd.DataFrame(
        [("U1", "T1"), ("U1", "T2"), ("U2", "T1")],
        columns=["author_id", "referenced_tweet_id"],
    )
    bg = BipartiteBuilder().build(df)
    u = list(bg.user_index).index("U1")
    t = list(bg.tweet_index).index("T2")
    assert bg.B[u, t] == 1
    u2 = list(bg.user_index).index("U2")
    assert bg.B[u2, t] == 0            # U2 não retuitou T2


def test_bipartite_save(tmp_path):
    df = pd.DataFrame([("U1", "T1")], columns=["author_id", "referenced_tweet_id"])
    bg = BipartiteBuilder().build(df)
    bg.save(tmp_path)
    assert (tmp_path / "bipartite_B.npz").exists()
    B2 = sp.load_npz(tmp_path / "bipartite_B.npz")
    assert B2.shape == bg.B.shape
    idx = pd.read_parquet(tmp_path / "bipartite_user_index.parquet")
    assert list(idx["user_id"]) == ["U1"]
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_bipartite.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.bipartite'`.

- [ ] **Step 3: Implementar `modules/bipartite.py`**

```python
"""Módulo 3 — construção da matriz bipartida usuário × tweet."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp


@dataclass
class BipartiteGraph:
    """Matriz de incidência binária usuário × tweet + mapeamentos de índice."""

    B: sp.csr_matrix
    user_index: np.ndarray   # posição (linha) -> author_id
    tweet_index: np.ndarray  # posição (coluna) -> referenced_tweet_id

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        sp.save_npz(out / "bipartite_B.npz", self.B)
        pd.DataFrame({"user_id": self.user_index}).to_parquet(
            out / "bipartite_user_index.parquet", index=False
        )
        pd.DataFrame({"tweet_id": self.tweet_index}).to_parquet(
            out / "bipartite_tweet_index.parquet", index=False
        )
        return out


class BipartiteBuilder:
    """Constrói o BipartiteGraph a partir do DataFrame de retweets filtrado."""

    def build(self, df: pd.DataFrame) -> BipartiteGraph:
        user_codes, user_index = pd.factorize(df["author_id"])
        tweet_codes, tweet_index = pd.factorize(df["referenced_tweet_id"])

        data = np.ones(len(df), dtype=np.int8)
        B = sp.coo_matrix(
            (data, (user_codes, tweet_codes)),
            shape=(len(user_index), len(tweet_index)),
        ).tocsr()
        B.sum_duplicates()
        B.data = np.ones_like(B.data)  # binariza: retweet repetido conta 1

        return BipartiteGraph(
            B=B,
            user_index=np.asarray(user_index),
            tweet_index=np.asarray(tweet_index),
        )
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_bipartite.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/bipartite.py tests/test_bipartite.py
git commit -m "feat: módulo 3 BipartiteBuilder (matriz esparsa usuário × tweet)"
```

---

## Task 5: Módulo 4 — `JaccardProjector` e `ProjectedGraph`

**Files:**
- Create: `modules/project.py`
- Test: `tests/test_project.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_project.py`:

```python
import numpy as np
import scipy.sparse as sp
from modules.bipartite import BipartiteGraph
from modules.project import JaccardProjector


def _bg():
    # U1:{T1,T2}, U2:{T1,T2}, U3:{T2,T3}
    B = sp.csr_matrix(np.array([
        [1, 1, 0],
        [1, 1, 0],
        [0, 1, 1],
    ], dtype=np.int8))
    return BipartiteGraph(
        B=B,
        user_index=np.array(["U1", "U2", "U3"]),
        tweet_index=np.array(["T1", "T2", "T3"]),
    )


def test_jaccard_weights():
    pg = JaccardProjector().project(_bg())
    W = pg.W.toarray()
    assert W[0, 1] == 1.0                 # U1,U2 idênticos
    assert abs(W[0, 2] - 1 / 3) < 1e-9    # U1,U3 -> 1/3
    assert abs(W[1, 2] - 1 / 3) < 1e-9


def test_projection_is_upper_triangular():
    pg = JaccardProjector().project(_bg())
    W = pg.W.toarray()
    assert W[1, 0] == 0.0                 # nada no triângulo inferior
    assert W[0, 0] == 0.0                 # sem diagonal
    assert list(pg.user_index) == ["U1", "U2", "U3"]


def test_projection_save(tmp_path):
    pg = JaccardProjector().project(_bg())
    pg.save(tmp_path)
    assert (tmp_path / "projection_W.npz").exists()
    assert (tmp_path / "projection_user_index.parquet").exists()
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_project.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.project'`.

- [ ] **Step 3: Implementar `modules/project.py`**

```python
"""Módulo 4 — projeção unipartida com peso Jaccard."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from modules.bipartite import BipartiteGraph


@dataclass
class ProjectedGraph:
    """Grafo unipartido usuário×usuário, triangular superior, peso Jaccard."""

    W: sp.csr_matrix
    user_index: np.ndarray

    def save(self, out_dir, prefix: str = "projection") -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        sp.save_npz(out / f"{prefix}_W.npz", self.W)
        pd.DataFrame({"user_id": self.user_index}).to_parquet(
            out / f"{prefix}_user_index.parquet", index=False
        )
        return out


class JaccardProjector:
    """Projeta a matriz bipartida em grafo de co-retweet com peso Jaccard."""

    def project(self, bg: BipartiteGraph) -> ProjectedGraph:
        # int64 evita overflow no produto B·Bᵀ (B é int8)
        B = bg.B.astype(np.int64)
        C = (B @ B.T).tocoo()                     # |T_u ∩ T_v|
        deg = np.asarray(B.sum(axis=1)).ravel()   # |T_u|

        # apenas triângulo superior (i < j), sem diagonal
        mask = C.row < C.col
        rows = C.row[mask]
        cols = C.col[mask]
        inter = C.data[mask]
        union = deg[rows] + deg[cols] - inter
        jac = inter / union

        n = len(bg.user_index)
        W = sp.coo_matrix((jac, (rows, cols)), shape=(n, n)).tocsr()
        return ProjectedGraph(W=W, user_index=bg.user_index)
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_project.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/project.py tests/test_project.py
git commit -m "feat: módulo 4 JaccardProjector (projeção co-retweet com peso Jaccard)"
```

---

## Task 6: Módulo 5 — `BackboneExtractor`

**Files:**
- Create: `modules/backbone.py`
- Test: `tests/test_backbone.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_backbone.py`:

```python
import json
import numpy as np
import scipy.sparse as sp
from modules.project import ProjectedGraph
from modules.backbone import BackboneExtractor


def _pg():
    # arestas: (0,1)=0.5 e (2,3)=0.05  -> tau=0.1 mantém só (0,1)
    W = sp.csr_matrix(np.array([
        [0.0, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.05],
        [0.0, 0.0, 0.0, 0.0],
    ]))
    return ProjectedGraph(W=W, user_index=np.array(["U0", "U1", "U2", "U3"]))


def test_backbone_thresholds_and_drops_isolates():
    bb = BackboneExtractor(tau=0.1)
    pg2 = bb.extract(_pg())
    assert pg2.W.shape == (2, 2)             # U2,U3 viraram isolados e saíram
    assert list(pg2.user_index) == ["U0", "U1"]
    assert pg2.W.toarray()[0, 1] == 0.5


def test_backbone_stats():
    bb = BackboneExtractor(tau=0.1)
    bb.extract(_pg())
    assert bb.stats["before"] == {"nodes": 4, "edges": 2}
    assert bb.stats["after"] == {"nodes": 2, "edges": 1}


def test_backbone_save_stats(tmp_path):
    bb = BackboneExtractor(tau=0.1)
    bb.extract(_pg())
    bb.save_stats(tmp_path)
    s = json.loads((tmp_path / "backbone_stats.json").read_text())
    assert s["after"]["nodes"] == 2
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_backbone.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.backbone'`.

- [ ] **Step 3: Implementar `modules/backbone.py`**

```python
"""Módulo 5 — backbone extraction por universal threshold."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from modules.project import ProjectedGraph


class BackboneExtractor:
    """Mantém arestas com peso ≥ tau e descarta nós que ficaram isolados."""

    def __init__(self, tau: float = 0.1):
        self.tau = tau
        self.stats: dict = {}

    def extract(self, pg: ProjectedGraph) -> ProjectedGraph:
        W = pg.W.tocoo()
        self.stats = {"before": {"nodes": int(len(pg.user_index)),
                                 "edges": int(W.nnz)}}

        keep = W.data >= self.tau
        rows, cols, vals = W.row[keep], W.col[keep], W.data[keep]

        # nós que ainda participam de alguma aresta
        if len(rows):
            used = np.unique(np.concatenate([rows, cols]))
        else:
            used = np.array([], dtype=int)

        remap = {int(old): new for new, old in enumerate(used)}
        new_rows = np.array([remap[int(r)] for r in rows], dtype=int)
        new_cols = np.array([remap[int(c)] for c in cols], dtype=int)

        W_new = sp.coo_matrix(
            (vals, (new_rows, new_cols)), shape=(len(used), len(used))
        ).tocsr()
        user_index = pg.user_index[used]

        self.stats["after"] = {"nodes": int(len(used)), "edges": int(W_new.nnz)}
        return ProjectedGraph(W=W_new, user_index=user_index)

    def save_stats(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "backbone_stats.json"
        with open(path, "w") as f:
            json.dump(self.stats, f, indent=2)
        return path
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_backbone.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/backbone.py tests/test_backbone.py
git commit -m "feat: módulo 5 BackboneExtractor (universal threshold + remoção de isolados)"
```

---

## Task 7: Módulo 6 — `CommunityDetector` e `CommunityResult`

**Files:**
- Create: `modules/community.py`
- Test: `tests/test_community.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_community.py`:

```python
import numpy as np
import pandas as pd
import scipy.sparse as sp
from modules.project import ProjectedGraph
from modules.community import CommunityDetector


def _two_cliques():
    # {0,1,2} clique e {3,4,5} clique, sem pontes
    edges = [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)]
    rows = [e[0] for e in edges]
    cols = [e[1] for e in edges]
    data = [1.0] * len(edges)
    W = sp.coo_matrix((data, (rows, cols)), shape=(6, 6)).tocsr()
    return ProjectedGraph(W=W, user_index=np.array(["U%d" % i for i in range(6)]))


def test_detects_two_communities():
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    assert len(set(cr.membership)) == 2
    assert cr.membership[0] == cr.membership[1] == cr.membership[2]
    assert cr.membership[3] == cr.membership[4] == cr.membership[5]
    assert cr.membership[0] != cr.membership[3]


def test_partition_modularity_positive():
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    assert cr.partition.modularity > 0
    assert cr.g.vcount() == 6


def test_community_save(tmp_path):
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    cr.save(tmp_path)
    assert (tmp_path / "community_graph.graphml").exists()
    m = pd.read_parquet(tmp_path / "membership.parquet")
    assert set(m.columns) == {"user_id", "community"}
    assert len(m) == 6
```

- [ ] **Step 2: Rodar para confirmar a falha**

Run: `.venv/bin/pytest tests/test_community.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'modules.community'`.

- [ ] **Step 3: Implementar `modules/community.py`**

```python
"""Módulo 6 — detecção de comunidades (Leiden)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import igraph as ig
import numpy as np
import pandas as pd

from modules.project import ProjectedGraph


@dataclass
class CommunityResult:
    """Grafo igraph com comunidades + partição crua + mapeamento de usuário."""

    g: ig.Graph
    partition: ig.VertexClustering
    membership: list
    user_index: np.ndarray

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        self.g.write_graphml(str(out / "community_graph.graphml"))
        pd.DataFrame(
            {"user_id": self.user_index, "community": self.membership}
        ).to_parquet(out / "membership.parquet", index=False)
        return out


class CommunityDetector:
    """Roda Leiden (objetivo de modularidade) sobre o grafo de backbone."""

    def __init__(self, resolution: float = 1.0,
                 objective_function: str = "modularity",
                 n_iterations: int = -1):
        self.resolution = resolution
        self.objective_function = objective_function
        self.n_iterations = n_iterations

    def detect(self, pg: ProjectedGraph) -> CommunityResult:
        W = pg.W.tocoo()
        n = len(pg.user_index)
        edges = list(zip(W.row.tolist(), W.col.tolist()))

        g = ig.Graph(n=n, edges=edges, directed=False)
        g.es["weight"] = W.data.tolist()
        g.vs["user_id"] = [str(u) for u in pg.user_index]

        partition = g.community_leiden(
            weights="weight",
            objective_function=self.objective_function,
            resolution=self.resolution,
            n_iterations=self.n_iterations,
        )
        membership = list(partition.membership)
        g.vs["community"] = membership

        return CommunityResult(
            g=g,
            partition=partition,
            membership=membership,
            user_index=pg.user_index,
        )
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/pytest tests/test_community.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add modules/community.py tests/test_community.py
git commit -m "feat: módulo 6 CommunityDetector (Leiden com objetivo de modularidade)"
```

---

## Task 8: Teste de integração ponta-a-ponta (Módulos 1→6)

**Files:**
- Test: `tests/test_integration.py`

- [ ] **Step 1: Escrever o teste de integração que falha (se algum contrato estiver errado)**

`tests/test_integration.py`:

```python
import pandas as pd
from modules.filter import NoiseFilter
from modules.bipartite import BipartiteBuilder
from modules.project import JaccardProjector
from modules.backbone import BackboneExtractor
from modules.community import CommunityDetector


def _two_group_retweets():
    rows = []
    for u in ["A1", "A2", "A3"]:
        for t in ["a1", "a2", "a3"]:
            rows.append((u, t))
    for u in ["B1", "B2", "B3"]:
        for t in ["b1", "b2", "b3"]:
            rows.append((u, t))
    return pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"])


def test_pipeline_recovers_two_communities():
    df = _two_group_retweets()

    # filtros frouxos para preservar o sinal sintético
    df_f = NoiseFilter(min_user_retweets=1, viral_user_fraction=0.99).apply(df)
    bg = BipartiteBuilder().build(df_f)
    pg = JaccardProjector().project(bg)
    pg_bb = BackboneExtractor(tau=0.1).extract(pg)
    cr = CommunityDetector(resolution=1.0).detect(pg_bb)

    comm = dict(zip(cr.user_index, cr.membership))
    assert len(set(cr.membership)) == 2
    assert comm["A1"] == comm["A2"] == comm["A3"]
    assert comm["B1"] == comm["B2"] == comm["B3"]
    assert comm["A1"] != comm["B1"]
```

- [ ] **Step 2: Rodar o teste de integração**

Run: `.venv/bin/pytest tests/test_integration.py -v`
Expected: PASS. (Se falhar, indica incompatibilidade de contrato entre módulos — corrigir antes de prosseguir.)

- [ ] **Step 3: Rodar a suíte completa**

Run: `.venv/bin/pytest -v`
Expected: PASS em todos os testes (smoke + 6 módulos + integração).

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integração ponta-a-ponta dos módulos 1-6 (recupera 2 comunidades)"
```

---

## Notas de execução

- O notebook `notebooks/pipeline.ipynb` é deixado para uso interativo (exploração e calibração de parâmetros); ele importa estas classes e as encadeia conforme os exemplos de uso dos specs. A autoria das células não faz parte deste plano por não ser adequada a TDD.
- A análise de sensibilidade ao threshold (τ = 0,05 / 0,10 / 0,15) é orquestrada no notebook, re-instanciando `BackboneExtractor` com cada `tau`.
- O Módulo 7 (métricas estruturais) será especificado e planejado separadamente, consumindo `CommunityResult`.

## Self-review (cobertura do spec)

- M1 carga + filtro de retweets → Task 2 ✓ (parsing por regex do repr, não JSON).
- M2 filtragem de ruído (N usuários, X% virais) + stats → Task 3 ✓.
- M3 matriz bipartida esparsa + user_index/tweet_index → Task 4 ✓.
- M4 projeção Jaccard via B·Bᵀ, triangular superior → Task 5 ✓.
- M5 backbone por τ + remoção de isolados + reindex → Task 6 ✓.
- M6 Leiden com `objective_function="modularity"` + GraphML → Task 7 ✓.
- Persistência Parquet + NPZ + GraphML → coberta nos `save` de cada task ✓.
- Propagação do `user_index` 3→4→5→6 → verificada no teste de integração (Task 8) ✓.
- Fora de escopo (Módulo 7, hidratação, frontend) → registrado nas notas ✓.
