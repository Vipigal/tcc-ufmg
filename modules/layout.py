"""Módulo 7 — mapa das comunidades por layout DRL.

Consome o `CommunityResult` (M5) e posiciona cada usuário (nó) no plano por
layout DRL, colorindo por grupo. Pipeline interna:

  1) esparsificação por nó: cada nó mantém só suas `top_k` arestas mais fortes
     (preserva a conectividade local e a estrutura de comunidades — um corte
     global por peso fragmentaria as bolhas e isolaria muitos nós);
  2) componente gigante (descarta nós soltos, sem "poeira" aleatória);
  3) layout DRL ponderado.

`layout` (coordenadas) e `render` (figura) são separados: o DRL é a etapa cara,
então o Stage cacheia as COORDENADAS (`drl_layout.parquet` + `drl_layout.json`)
e o PNG é desenhado sob demanda — as coordenadas viram artefato reutilizável
para qualquer outra visualização.
"""
from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import igraph as ig
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from modules.stage import Stage

INK, MUTED, WHITE, GREY = "#14172A", "#3a4055", "#FFFFFF", "#c7ccd6"
# cores por grupo (1 = roxo, 2 = teal, 3 = laranja, ...); estende p/ mais grupos
PALETTE = ["#5E4FA2", "#26A69A", "#E8852B", "#D7263D", "#3C6E9E",
           "#B5651D", "#7A8B3A", "#9C4DCC", "#00897B", "#C2185B"]
SUBTITLE = ("Layout DRL  ·  cada ponto = 1 usuário  ·  proximidade = retweets "
            "em comum  ·  cor = grupo")


@dataclass
class CommunityLayout:
    """Coordenadas DRL dos nós da componente gigante + tamanhos dos grupos."""

    coords: np.ndarray            # (m, 2) posições dos nós plotados
    community: np.ndarray         # (m,) comunidade de cada nó plotado
    sizes: pd.Series              # comunidade -> nº de nós (TODOS os nós), descendente
    n_nodes: int                  # total de nós do grafo (denominador das %)
    top_k: int
    seed: int

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"x": self.coords[:, 0], "y": self.coords[:, 1],
                      "community": self.community}).to_parquet(
            out / "drl_layout.parquet", index=False)
        meta = {"sizes": {int(k): int(v) for k, v in self.sizes.items()},
                "n_nodes": int(self.n_nodes), "top_k": int(self.top_k),
                "seed": int(self.seed)}
        (out / "drl_layout.json").write_text(json.dumps(meta))
        return out

    @classmethod
    def load(cls, out_dir) -> "CommunityLayout":
        out = Path(out_dir)
        df = pd.read_parquet(out / "drl_layout.parquet")
        meta = json.loads((out / "drl_layout.json").read_text())
        sizes = pd.Series({int(k): v for k, v in meta["sizes"].items()}).sort_values(
            ascending=False)
        return cls(coords=df[["x", "y"]].to_numpy(),
                   community=df["community"].to_numpy(), sizes=sizes,
                   n_nodes=meta["n_nodes"], top_k=meta["top_k"], seed=meta["seed"])


class CommunityMap(Stage):
    """M7 — coordenadas DRL das comunidades a partir do `CommunityResult` (M5)."""

    FILES = ("drl_layout.parquet", "drl_layout.json")

    def __init__(self, top_k: int = 12, seed: int = 42, min_frac: float = 0.01):
        self.top_k = top_k
        self.seed = seed
        self.min_frac = min_frac      # grupos >= min_frac dos nós são coloridos/rotulados

    # --- layout (parte cara: esparsifica + comp. gigante + DRL) ---
    def layout(self, cr) -> CommunityLayout:
        Wc = cr.W.tocoo()
        src, dst, w = Wc.row, Wc.col, Wc.data
        membership = np.asarray(cr.membership)
        n_nodes = len(membership)

        # 1) cada nó mantém suas top_k arestas mais fortes (união)
        t0 = time.time()
        eid = np.arange(len(w))
        node = np.concatenate([src, dst])
        wt = np.concatenate([w, w])
        ee = np.concatenate([eid, eid])
        o = np.lexsort((-wt, node))
        node_s, ee_s = node[o], ee[o]
        _, start = np.unique(node_s, return_index=True)
        pos = np.arange(len(node_s)) - np.repeat(start, np.diff(np.append(start, len(node_s))))
        kept = np.unique(ee_s[pos < self.top_k])

        # 2) componente gigante
        random.seed(self.seed)
        try:
            ig.set_random_number_generator(random)
        except Exception:
            pass
        g = ig.Graph(n=n_nodes, edges=np.column_stack([src[kept], dst[kept]]).tolist())
        g.es["weight"] = w[kept].tolist()
        gc_nodes = np.array(max(g.connected_components(), key=len))
        sub = g.induced_subgraph(gc_nodes.tolist())

        # 3) layout DRL
        xy = np.array(sub.layout_drl(weights="weight").coords)
        sizes = pd.Series(membership).value_counts()
        print(f"top-{self.top_k}/nó -> {len(kept):,} arestas | "
              f"comp.gigante={len(gc_nodes):,} ({100*len(gc_nodes)/n_nodes:.1f}% dos nós) | "
              f"DRL {time.time()-t0:.0f}s")
        return CommunityLayout(coords=xy, community=membership[gc_nodes], sizes=sizes,
                               n_nodes=n_nodes, top_k=self.top_k, seed=self.seed)

    # --- renderização (scatter + rótulos a partir das coordenadas) ---
    def render(self, layout: CommunityLayout, out_dir, title: str = "") -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        plt.rcParams["font.family"] = "DejaVu Sans"

        xy, memb_gc, sizes, n_nodes = (layout.coords, layout.community,
                                       layout.sizes, layout.n_nodes)
        order_c = list(sizes.index)
        rank = {c: i for i, c in enumerate(order_c)}
        big = [c for c in order_c if sizes[c] >= self.min_frac * n_nodes]

        fig = plt.figure(figsize=(12, 8), facecolor=WHITE)
        ax = fig.add_axes([0.02, 0.105, 0.96, 0.80]); ax.set_facecolor(WHITE)
        for c in reversed(order_c):                    # pequenos primeiro, grandes por cima
            m = memb_gc == c
            if m.any():
                ax.scatter(xy[m, 0], xy[m, 1], s=3.0, linewidths=0, alpha=0.5,
                           rasterized=True,
                           c=(PALETTE[rank[c] % len(PALETTE)] if c in big else GREY))
        ax.set_aspect("equal"); ax.axis("off")
        lo, hi = np.percentile(xy, [0.5, 99.5], axis=0); pad = 0.05 * (hi - lo)
        ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0]); ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1])

        # rótulos "Grupo k · XX%" no centróide, com anti-sobreposição (empilha em y)
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        fr = []
        for c in big:
            m = memb_gc == c
            if m.any():
                fr.append([(np.median(xy[m, 0]) - xlim[0]) / (xlim[1] - xlim[0]),
                           (np.median(xy[m, 1]) - ylim[0]) / (ylim[1] - ylim[0]), c])
        fr.sort(key=lambda r: -r[1])
        for _ in range(200):
            moved = False
            for i in range(len(fr)):
                for j in range(i + 1, len(fr)):
                    if abs(fr[i][0] - fr[j][0]) < 0.16 and abs(fr[i][1] - fr[j][1]) < 0.075:
                        push = (0.075 - abs(fr[i][1] - fr[j][1])) / 2 + 0.005
                        hi_i = fr[i][1] >= fr[j][1]
                        fr[i][1] += push if hi_i else -push
                        fr[j][1] += -push if hi_i else push
                        moved = True
            if not moved:
                break
        halo = [pe.withStroke(linewidth=5, foreground="white")]
        for fx, fy, c in fr:
            fx, fy = min(max(fx, 0.06), 0.94), min(max(fy, 0.04), 0.96)
            ax.text(xlim[0] + fx * (xlim[1] - xlim[0]), ylim[0] + fy * (ylim[1] - ylim[0]),
                    f"Grupo {rank[c] + 1} · {100 * sizes[c] / n_nodes:.0f}%",
                    ha="center", va="center", fontsize=28, fontweight="bold",
                    color=PALETTE[rank[c] % len(PALETTE)], path_effects=halo, zorder=10)

        head = "Grupos no grafo de co-retweet" + (f" — {title}" if title else "")
        fig.text(0.5, 0.965, head, ha="center", va="top", fontsize=17,
                 fontweight="bold", color=INK)
        fig.text(0.5, 0.066, SUBTITLE, ha="center", va="center", fontsize=13, color=MUTED)
        fig.text(0.5, 0.028, f"As porcentagens indicam a parcela dos {n_nodes:,} usuários "
                 "(nós) em cada grupo.".replace(",", "."), ha="center", va="center",
                 fontsize=13, color=MUTED)

        out_png = out / "grafo-comunidades-drl.png"
        fig.savefig(out_png, dpi=200, facecolor=WHITE)
        return out_png

    # --- hooks de cache (Stage) ---
    def _compute(self, cr) -> CommunityLayout:
        return self.layout(cr)

    def _save(self, layout: CommunityLayout, out_dir) -> None:
        layout.save(out_dir)

    def _load(self, out_dir) -> CommunityLayout:
        return CommunityLayout.load(out_dir)
