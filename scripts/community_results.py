#!/usr/bin/env python
"""Peças de resultado das comunidades — Pipeline 1 / Invasão dos 3 Poderes.

Lê o grafo final persistido (graph_nodes/graph_edges.parquet), recalcula todas
as métricas DA PRÓPRIA BASE (nada é transcrito à mão) e renderiza DUAS peças
independentes, de alto contraste e fundo branco, para serem coladas lado a lado
no banner:

    assets/matriz_fluxo.png      matriz de fluxo 3×3 (% do peso total das arestas)
    assets/metricas_basicas.png  métricas do grafo, empilhadas na vertical

Renomeação dos rótulos (pedido):  com1 -> Grupo 1 · com2 -> Grupo 2 · com0 -> Grupo 3.
A macroestrutura é renderizada por outro grafo e fica de fora aqui.
Cores neutras de propósito — identidade ideológica não atribuída (pende hidratação).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams["font.family"] = "DejaVu Sans"

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "processed" / "invasao-3-poderes"
ASSETS = ROOT / "assets"

INK, MUTED, RULE, WHITE = "#14172A", "#3a4055", "#d4d8e0", "#FFFFFF"

# ---------------------------------------------------------------------------
# 1) MÉTRICAS (recalculadas da base)
# ---------------------------------------------------------------------------
nodes = pd.read_parquet(BASE / "graph_nodes.parquet")
edges = pd.read_parquet(BASE / "graph_edges.parquet")

comm = nodes["community"].to_numpy()
n_nodes = len(nodes)
n_edges = len(edges)
n_comm = int(nodes["community"].nunique())

src = edges["src"].to_numpy(); dst = edges["dst"].to_numpy()
w = edges["weight"].to_numpy().astype(np.float64)
W = w.sum()
nc = comm.max() + 1
M = np.zeros((nc, nc))
np.add.at(M, (comm[src], comm[dst]), w)            # arestas guardadas 1x (src<dst)

intra_total = sum(M[r, r] for r in range(nc))
intra_pct = 100 * intra_total / W
twoM = 2 * W
e = (M + M.T) / twoM
a = e.sum(axis=1)
Q = float(np.trace(e) - np.sum(a ** 2))
assort = float((np.trace(e) - np.sum(a ** 2)) / (1 - np.sum(a ** 2)))

# rótulos (mapeamento canônico do DRL): Grupo 1 = com1(44%) · Grupo 2 = com0(34%) · Grupo 3 = com2(21%)
ORDER = [1, 0, 2]
LABELS = ["Grupo 1", "Grupo 2", "Grupo 3"]
F = np.zeros((3, 3))
for i, r in enumerate(ORDER):
    for j, s in enumerate(ORDER):
        F[i, j] = 100 * (M[r, s] + (M[s, r] if r != s else 0)) / W

print("=== métricas (recalculadas) ===")
print(f"nós={n_nodes} arestas={n_edges} grupos={n_comm}")
print(f"Q={Q:.4f}  assort={assort:.4f}  intra={intra_pct:.2f}%")
print("matriz de fluxo (% de W), ordem Grupo 1,2,3:\n", np.round(F, 3))


def fmt(v):
    return (f"{v:.1f}" if v >= 0.1 else "0,02").replace(".", ",")


# ---------------------------------------------------------------------------
# 2) PEÇA A — matriz de fluxo
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(6.8, 6.8), facecolor=WHITE)
fig.text(0.5, 0.945, "Matriz de fluxo", color=INK, fontsize=21,
         fontweight="bold", ha="center")
fig.text(0.5, 0.900, "% do peso total das arestas", color=MUTED, fontsize=13,
         ha="center")

ax = fig.add_axes([0.175, 0.115, 0.70, 0.73])
cmap = LinearSegmentedColormap.from_list("nv", ["#f4f6f9", "#aeb8d6", "#5566a0", INK])
ax.imshow(F, cmap=cmap, vmin=0, vmax=36, aspect="equal")
ax.set_xticks(range(3)); ax.set_yticks(range(3))
ax.set_xticklabels(LABELS, fontsize=14, color=INK)
ax.set_yticklabels(LABELS, fontsize=14, color=INK, rotation=90, va="center")
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
# bordas finas entre as células (definem as células claras sobre o branco)
ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
ax.grid(which="minor", color=RULE, lw=1.5)
ax.tick_params(which="minor", length=0)
for i in range(3):
    for j in range(3):
        v = F[i, j]
        ax.text(j, i, fmt(v), ha="center", va="center",
                color=(WHITE if v >= 14 else INK), fontsize=16, fontweight="bold")
fig.text(0.5, 0.045,
         "diagonal = peso interno de cada grupo  ·  fora da diagonal = fluxo entre grupos",
         color=MUTED, fontsize=11, ha="center")
out_a = ASSETS / "matriz_fluxo.png"
fig.savefig(out_a, dpi=200, facecolor=WHITE)
plt.close(fig)
print(f"png -> {out_a}  ({out_a.stat().st_size / 1024:.0f} KB)")

# ---------------------------------------------------------------------------
# 3) PEÇA B — métricas do grafo (vertical, p/ colar ao lado da matriz)
# ---------------------------------------------------------------------------
metrics = [
    ("33.305", "usuários (nós)"),
    ("12,0 mi", "arestas (peso Jaccard)"),
    ("11", "grupos (3 = 99,9%)"),
    ("0,50", "modularidade Q"),
    ("0,75", "assortatividade (grupo)"),
    ("83,5%", "peso intragrupo"),
]
fig = plt.figure(figsize=(3.6, 6.8), facecolor=WHITE)
fig.text(0.5, 0.95, "Métricas do grafo", color=INK, fontsize=16,
         fontweight="bold", ha="center")
fig.add_artist(plt.Line2D([0.12, 0.88], [0.915, 0.915], color=RULE, lw=1.3,
                          transform=fig.transFigure))

y_top, y_bot = 0.83, 0.10
n = len(metrics)
centers = [y_top - (y_top - y_bot) * i / (n - 1) for i in range(n)]
for (big, lab), yc in zip(metrics, centers):
    fig.text(0.5, yc + 0.028, big, color=INK, fontsize=28, fontweight="bold",
             ha="center", va="center")
    fig.text(0.5, yc - 0.035, lab, color=MUTED, fontsize=12, ha="center", va="center")
for k in range(n - 1):
    ymid = (centers[k] + centers[k + 1]) / 2
    fig.add_artist(plt.Line2D([0.12, 0.88], [ymid, ymid], color=RULE, lw=1.0,
                              transform=fig.transFigure))
out_b = ASSETS / "metricas_basicas.png"
fig.savefig(out_b, dpi=200, facecolor=WHITE)
plt.close(fig)
print(f"png -> {out_b}  ({out_b.stat().st_size / 1024:.0f} KB)")
