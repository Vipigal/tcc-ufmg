"""Módulo 6 — peças de resultado do grafo: métricas + matriz de fluxo.

Consome o `CommunityResult` (M5) e produz, **recalculado da base** (nada à mão):

  - `GraphMetrics`  — dataclass com nós, arestas, grupos, modularidade Q,
    assortatividade por grupo, peso intragrupo, e a matriz de fluxo reduzida
    (grupos grandes + faixa "outras") já em % do peso total, com seus rótulos;
  - duas figuras de alto contraste, fundo branco (renderizadas sob demanda):
        matriz_fluxo.png      matriz de fluxo entre grupos
        metricas_basicas.png  métricas empilhadas na vertical

`compute` (dados) e `render` (figuras) são separados de propósito: as métricas
podem ser reusadas fora do banner (tabelas, comparação entre eventos, etc.). O
Stage cacheia só os dados (`graph_metrics.json`); as PNGs são render, não cache.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from modules.stage import Stage

INK, MUTED, RULE, WHITE = "#14172A", "#3a4055", "#d4d8e0", "#FFFFFF"


# --- formatadores (pt-BR) ---
def _br(s: str) -> str:
    return s.replace(".", ",")


def _int(v) -> str:               # 33305 -> "33.305"
    return f"{int(v):,}".replace(",", ".")


def _big(v) -> str:               # contagem grande, abreviada
    if v >= 1e6:
        return _br(f"{v / 1e6:.1f} mi")
    if v >= 1e4:
        return _br(f"{v / 1e3:.0f} mil")
    return _int(v)


def _f2(v) -> str:                # 0.5 -> "0,50"
    return _br(f"{v:.2f}")


def _pct(v) -> str:               # 83.5 -> "83,5%"
    return _br(f"{v:.1f}%")


def _cell(v) -> str:              # célula da matriz
    s = f"{v:.1f}" if v >= 0.1 else (f"{v:.2f}" if v > 0 else "0")
    return _br(s)


@dataclass
class GraphMetrics:
    """Métricas do grafo e matriz de fluxo, recalculadas da base."""

    n_nodes: int
    n_edges: int
    n_comm: int
    n_big: int                    # nº de grupos "grandes" (>= min_frac dos nós)
    cov_big: float                # % dos nós cobertos pelos grupos grandes
    modularity: float
    assortativity: float
    intra_pct: float              # % do peso de arestas dentro dos grupos
    flow: np.ndarray              # matriz reduzida (% do peso total), grandes [+ "outras"]
    labels: list                  # rótulos das linhas/colunas de `flow`

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["flow"] = self.flow.tolist()
        path = out / "graph_metrics.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    @classmethod
    def load(cls, out_dir) -> "GraphMetrics":
        d = json.loads((Path(out_dir) / "graph_metrics.json").read_text())
        d["flow"] = np.asarray(d["flow"])
        return cls(**d)


class GraphResults(Stage):
    """M6 — métricas + matriz de fluxo a partir do `CommunityResult` (M5)."""

    FILES = ("graph_metrics.json",)   # PNGs são render (ver `render`), não cache

    def __init__(self, min_frac: float = 0.01):
        self.min_frac = min_frac

    # --- computação (reusável, sem desenhar nada) ---
    def compute(self, cr) -> GraphMetrics:
        membership = np.asarray(cr.membership)
        n_nodes = len(membership)
        n_comm = int(membership.max()) + 1
        n_edges = int(cr.W.nnz)

        Wc = cr.W.tocoo()
        w = Wc.data.astype(np.float64)
        W = w.sum()
        # matriz comunidade×comunidade (arestas guardadas 1x, src<dst)
        src_c, dst_c = membership[Wc.row], membership[Wc.col]
        M = np.bincount(src_c * n_comm + dst_c, weights=w,
                        minlength=n_comm ** 2).reshape(n_comm, n_comm)

        e = (M + M.T) / (2 * W)
        a = e.sum(axis=1)
        Q = float(np.trace(e) - np.sum(a ** 2))
        assort = float((np.trace(e) - np.sum(a ** 2)) / (1 - np.sum(a ** 2)))
        intra_pct = 100 * float(np.trace(M)) / W

        sizes = pd.Series(membership).value_counts()           # descendente
        big = sizes[sizes >= self.min_frac * n_nodes].index.to_numpy()
        n_big = len(big)
        has_res = n_big < n_comm
        n_lab = n_big + (1 if has_res else 0)
        cov_big = 100 * sizes.loc[big].sum() / n_nodes

        lab_of = np.full(n_comm, n_big, dtype=int)
        for i, c in enumerate(big):
            lab_of[c] = i
        R = np.zeros((n_lab, n_lab))
        np.add.at(R, (lab_of[np.arange(n_comm)][:, None],
                      lab_of[np.arange(n_comm)][None, :]), M)
        F = (R + R.T - np.diag(np.diag(R))) / W * 100
        labels = [f"Grupo {i + 1}" for i in range(n_big)] + (["outras"] if has_res else [])
        # "outras" some da MATRIZ quando seu peso é invisível (segue contada em n_comm)
        if has_res and max(F[-1, :].max(), F[:, -1].max()) < 0.1:
            F = F[:n_big, :n_big]
            labels = labels[:n_big]

        return GraphMetrics(n_nodes=n_nodes, n_edges=n_edges, n_comm=n_comm,
                            n_big=n_big, cov_big=cov_big, modularity=Q,
                            assortativity=assort, intra_pct=intra_pct,
                            flow=F, labels=labels)

    # --- renderização (figuras a partir das métricas) ---
    def render(self, m: GraphMetrics, out_dir) -> tuple[Path, Path]:
        """Desenha e salva matriz_fluxo.png + metricas_basicas.png. Não fecha as
        figuras (o backend inline do Jupyter as exibe ao fim da célula)."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        plt.rcParams["font.family"] = "DejaVu Sans"

        # PEÇA A — matriz de fluxo
        F, labels = m.flow, m.labels
        n_lab = len(labels)
        vmax = max(F.max(), 1e-9)
        figA = plt.figure(figsize=(6.8, 6.8), facecolor=WHITE)
        figA.text(0.5, 0.945, "Matriz de fluxo", color=INK, fontsize=21,
                  fontweight="bold", ha="center")
        figA.text(0.5, 0.900, "% do peso total das arestas", color=MUTED, fontsize=13,
                  ha="center")
        ax = figA.add_axes([0.175, 0.115, 0.70, 0.73])
        cmap = LinearSegmentedColormap.from_list("nv", ["#f4f6f9", "#aeb8d6", "#5566a0", INK])
        ax.imshow(F, cmap=cmap, vmin=0, vmax=vmax, aspect="equal")
        lab_fs = 14 if n_lab <= 4 else 11
        ax.set_xticks(range(n_lab)); ax.set_yticks(range(n_lab))
        ax.set_xticklabels(labels, fontsize=lab_fs, color=INK)
        ax.set_yticklabels(labels, fontsize=lab_fs, color=INK, rotation=90, va="center")
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks(np.arange(-0.5, n_lab, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, n_lab, 1), minor=True)
        ax.grid(which="minor", color=RULE, lw=1.5)
        ax.tick_params(which="minor", length=0)
        cell_fs = 16 if n_lab <= 4 else 12
        for i in range(n_lab):
            for j in range(n_lab):
                v = F[i, j]
                ax.text(j, i, _cell(v), ha="center", va="center",
                        color=(WHITE if v >= 0.45 * vmax else INK),
                        fontsize=cell_fs, fontweight="bold")
        figA.text(0.5, 0.045,
                  "diagonal = peso interno de cada grupo  ·  fora da diagonal = fluxo entre grupos",
                  color=MUTED, fontsize=11, ha="center")
        out_a = out / "matriz_fluxo.png"
        figA.savefig(out_a, dpi=200, facecolor=WHITE)

        # PEÇA B — métricas do grafo (vertical)
        metrics = [
            (_int(m.n_nodes), "usuários (nós)"),
            (_big(m.n_edges), "arestas (peso Jaccard)"),
            (str(m.n_comm), f"grupos ({m.n_big} = {_pct(m.cov_big)})"),
            (_f2(m.modularity), "modularidade Q"),
            (_f2(m.assortativity), "assortatividade (grupo)"),
            (_pct(m.intra_pct), "peso intragrupo"),
        ]
        figB = plt.figure(figsize=(3.6, 6.8), facecolor=WHITE)
        figB.text(0.5, 0.95, "Métricas do grafo", color=INK, fontsize=16,
                  fontweight="bold", ha="center")
        figB.add_artist(plt.Line2D([0.12, 0.88], [0.915, 0.915], color=RULE, lw=1.3,
                                   transform=figB.transFigure))
        y_top, y_bot, nm = 0.83, 0.10, len(metrics)
        centers = [y_top - (y_top - y_bot) * i / (nm - 1) for i in range(nm)]
        for (big_v, lab), yc in zip(metrics, centers):
            figB.text(0.5, yc + 0.028, big_v, color=INK, fontsize=28, fontweight="bold",
                      ha="center", va="center")
            figB.text(0.5, yc - 0.035, lab, color=MUTED, fontsize=12, ha="center", va="center")
        for k in range(nm - 1):
            ymid = (centers[k] + centers[k + 1]) / 2
            figB.add_artist(plt.Line2D([0.12, 0.88], [ymid, ymid], color=RULE, lw=1.0,
                                       transform=figB.transFigure))
        out_b = out / "metricas_basicas.png"
        figB.savefig(out_b, dpi=200, facecolor=WHITE)
        return out_a, out_b

    # --- hooks de cache (Stage) ---
    def _compute(self, cr) -> GraphMetrics:
        return self.compute(cr)

    def _save(self, m: GraphMetrics, out_dir) -> None:
        m.save(out_dir)

    def _load(self, out_dir) -> GraphMetrics:
        return GraphMetrics.load(out_dir)
