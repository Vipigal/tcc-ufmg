#!/usr/bin/env python
"""Análise de sensibilidade do parâmetro N (metade estrutural).

Ver design em docs/superpowers/specs/2026-06-19-sensibilidade-N-design.md.

Reusa os módulos de produção (NoiseFilter, BipartiteBuilder, CommunityDetector)
e usa uma projeção Jaccard memory-lean (int32/float32) validada bit-a-bit contra
modules.project.JaccardProjector no subcomando `validate`. Cada N roda em um
processo separado (`run --n N`) para liberar memória entre execuções; `summarize`
e `plots` consomem apenas os artefatos compactos por N.

Subcomandos:
  load                 regenera retweets.parquet a partir dos CSVs brutos (M1)
  validate             projeção lean == módulo de produção em N=10
  run --n N            roda o pipeline em N, persiste métricas + tabela de nós
  summarize            Peça 2 (estabilidade macro) + Peça 3 (faixa incremental)
  plots                gera PNGs em assets/
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.load import RetweetLoader          # noqa: E402
from modules.filter import NoiseFilter           # noqa: E402
from modules.bipartite import BipartiteBuilder, BipartiteGraph  # noqa: E402
from modules.project import JaccardProjector, ProjectedGraph    # noqa: E402
from modules.community import CommunityDetector   # noqa: E402

import igraph as ig                               # noqa: E402

# ---- parâmetros do experimento (ver §4.1 do design) ----
EVENTO = "invasao-3-poderes"
GRID = [5, 7, 10, 15, 20]
TAU = 0.10
RESOLUTION = 1.0
DOMINANT_FRAC = 0.01      # bloco "dominante" = >= 1% dos nós
THETA_FLOW = 0.10         # L2: par de blocos co-amplificadores se fluxo >= θ·min(interno)
THETA_FLOW_SENS = [0.05, 0.20]  # sensibilidade reportada

RAW_DIR = PROJECT_ROOT / "data" / "raw" / EVENTO
OUT_DIR = PROJECT_ROOT / "data" / "processed" / EVENTO / "sensitivity"
WORK_DIR = Path("/tmp/claude-1000/-home-vinicius-tcc/"
                "71aa390c-d64d-4561-8333-9f017e62cc40/scratchpad/sensitivity")
ASSETS = PROJECT_ROOT / "assets"
RETWEETS = WORK_DIR / "retweets.parquet"


# ----------------------------------------------------------------------------
# projeção Jaccard memory-lean (matematicamente idêntica a JaccardProjector)
# ----------------------------------------------------------------------------
def project_lean(bg: BipartiteGraph, tau: float, block_size: int = 2000) -> ProjectedGraph:
    """Igual a JaccardProjector.project, mas índices int32 e peso float32.

    A decisão de manter cada aresta (jaccard >= tau) é feita em float64, idêntica
    ao módulo; só o armazenamento é mais enxuto. Validado por `validate`.
    """
    incidence = bg.B.astype(np.int32).tocsr()
    incidence_T = incidence.T.tocsr()
    tweets_per_user = np.asarray(incidence.sum(axis=1)).ravel().astype(np.int64)
    n_users = incidence.shape[0]

    ii, jj, ww = [], [], []
    for bs in range(0, n_users, block_size):
        be = min(bs + block_size, n_users)
        shared = (incidence[bs:be] @ incidence_T).tocoo()
        ui = shared.row + bs
        uj = shared.col
        upper = uj > ui
        ui, uj = ui[upper], uj[upper]
        inter = shared.data[upper].astype(np.int64)
        union = tweets_per_user[ui] + tweets_per_user[uj] - inter
        jac = inter / union                       # float64, igual ao módulo
        keep = jac >= tau
        ii.append(ui[keep].astype(np.int32))
        jj.append(uj[keep].astype(np.int32))
        ww.append(jac[keep].astype(np.float32))
        del shared, ui, uj, inter, union, jac, keep
    edge_i = np.concatenate(ii) if ii else np.empty(0, np.int32)
    edge_j = np.concatenate(jj) if jj else np.empty(0, np.int32)
    edge_w = np.concatenate(ww) if ww else np.empty(0, np.float32)
    del ii, jj, ww, incidence, incidence_T
    gc.collect()

    active = (np.unique(np.concatenate([edge_i, edge_j])) if len(edge_i)
              else np.empty(0, np.int32))
    new_index = np.full(n_users, -1, np.int64)
    new_index[active] = np.arange(len(active))
    W = sp.coo_matrix(
        (edge_w, (new_index[edge_i], new_index[edge_j])),
        shape=(len(active), len(active)),
    ).tocsr()
    return ProjectedGraph(W=W, user_index=bg.user_index[active])


# ----------------------------------------------------------------------------
# helpers de estrutura
# ----------------------------------------------------------------------------
def macro_labels(membership: np.ndarray, W: sp.csr_matrix, n_nodes: int):
    """Devolve (macro_L3, macro_L2, info) por nó.

    L3: blocos dominantes (>= DOMINANT_FRAC dos nós) ranqueados por tamanho
        (0,1,2,...); resíduo = -1.
    L2: super-polos = componentes conexos dos blocos dominantes sob a relação
        "fluxo mútuo >= THETA_FLOW * min(peso interno dos dois)". Resíduo = -1.
    """
    sizes = pd.Series(membership).value_counts()
    dominant = sizes[sizes >= DOMINANT_FRAC * n_nodes].index.to_numpy()
    rank_of = {c: r for r, c in enumerate(dominant)}     # comunidade nativa -> rank L3
    macro_L3 = np.array([rank_of.get(c, -1) for c in membership], dtype=np.int32)

    # matriz de fluxo simetrizada entre blocos dominantes (peso, não %)
    k = len(dominant)
    Wc = W.tocoo()
    lab = np.full(int(membership.max()) + 1, -1, np.int64)
    for c, r in rank_of.items():
        lab[c] = r
    a = lab[membership[Wc.row]]
    b = lab[membership[Wc.col]]
    m = (a >= 0) & (b >= 0)
    M = np.zeros((k, k))
    np.add.at(M, (a[m], b[m]), Wc.data[m])
    S = M + M.T - np.diag(np.diag(M))                    # simetriza off-diagonais

    # agglomeração por fluxo -> super-polos (componentes conexos)
    def superpoles(theta):
        adj = np.zeros((k, k), dtype=bool)
        for i in range(k):
            for j in range(i + 1, k):
                internal = min(S[i, i], S[j, j])
                if internal > 0 and S[i, j] >= theta * internal:
                    adj[i, j] = adj[j, i] = True
        # componentes conexos sobre k blocos (k pequeno)
        comp = np.full(k, -1)
        cid = 0
        for s in range(k):
            if comp[s] >= 0:
                continue
            stack, comp[s] = [s], cid
            while stack:
                u = stack.pop()
                for v in range(k):
                    if adj[u, v] and comp[v] < 0:
                        comp[v] = cid
                        stack.append(v)
            cid += 1
        return comp, cid

    comp, n_super = superpoles(THETA_FLOW)
    rank_to_super = {r: int(comp[r]) for r in range(k)}
    macro_L2 = np.array(
        [rank_to_super.get(int(r), -1) if r >= 0 else -1 for r in macro_L3],
        dtype=np.int32,
    )

    sens = {}
    for th in THETA_FLOW_SENS:
        _, ns = superpoles(th)
        sens[str(th)] = int(ns)

    info = {
        "dominant_communities": [int(c) for c in dominant],
        "dominant_sizes": [int(sizes[c]) for c in dominant],
        "dominant_frac": [float(sizes[c] / n_nodes) for c in dominant],
        "flow_matrix_weight": S.tolist(),
        "n_super_poles": int(n_super),
        "super_pole_of_rank": rank_to_super,
        "n_super_poles_sens": sens,
    }
    return macro_L3, macro_L2, info


def participation_and_degree(membership: np.ndarray, W: sp.csr_matrix):
    """Participation coefficient (sobre comunidades nativas) e grau ponderado.

    P_i = 1 - sum_c (k_{i,c}/k_i)^2 ; k = grau ponderado simétrico.
    """
    n = W.shape[0]
    n_comm = int(membership.max()) + 1
    Wc = W.tocoo()
    src, dst, w = Wc.row, Wc.col, Wc.data.astype(np.float64)
    comm = membership
    # peso de cada nó para cada comunidade (arestas contam dos dois lados)
    idx_src = src * n_comm + comm[dst]   # nó src -> comunidade do dst
    idx_dst = dst * n_comm + comm[src]   # nó dst -> comunidade do src
    kc = np.bincount(np.concatenate([idx_src, idx_dst]),
                     weights=np.concatenate([w, w]),
                     minlength=n * n_comm).reshape(n, n_comm)
    k = kc.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = kc / k[:, None]
        part = 1.0 - np.nansum(frac ** 2, axis=1)
    part[k == 0] = 0.0
    return part.astype(np.float32), k.astype(np.float32)


def intra_weight_fraction(membership: np.ndarray, W: sp.csr_matrix) -> float:
    Wc = W.tocoo()
    same = membership[Wc.row] == membership[Wc.col]
    tot = Wc.data.sum()
    return float(Wc.data[same].sum() / tot) if tot else 0.0


# ----------------------------------------------------------------------------
# subcomandos
# ----------------------------------------------------------------------------
def cmd_load(args):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    df = RetweetLoader(RAW_DIR).load()
    df.to_parquet(RETWEETS, index=False)
    print(f"[load] retweets: {len(df):,} linhas, "
          f"{df['author_id'].nunique():,} usuários, "
          f"{df['referenced_tweet_id'].nunique():,} tweets -> {RETWEETS}")


def _build_graph(n: int, block_size: int):
    retweets = pd.read_parquet(RETWEETS)
    filtered = NoiseFilter(min_user_retweets=n).apply(retweets)
    del retweets
    bg = BipartiteBuilder().build(filtered)
    del filtered
    gc.collect()
    pg = project_lean(bg, tau=TAU, block_size=block_size)
    del bg
    gc.collect()
    return pg


def cmd_validate(args):
    """Projeção lean idêntica ao módulo de produção (nós, arestas, soma de pesos)."""
    n = args.n
    retweets = pd.read_parquet(RETWEETS)
    filtered = NoiseFilter(min_user_retweets=n).apply(retweets)
    bg = BipartiteBuilder().build(filtered)

    pg_mod = JaccardProjector(tau=TAU, block_size=args.block_size).project(bg)
    pg_lean = project_lean(bg, tau=TAU, block_size=args.block_size)

    same_nodes = pg_mod.W.shape[0] == pg_lean.W.shape[0]
    same_edges = pg_mod.W.nnz == pg_lean.W.nnz
    same_index = bool(np.array_equal(
        np.asarray(pg_mod.user_index).astype(str),
        np.asarray(pg_lean.user_index).astype(str)))
    print(f"[validate N={n}] módulo: {pg_mod.W.shape[0]:,} nós / {pg_mod.W.nnz:,} arestas")
    print(f"[validate N={n}] lean:   {pg_lean.W.shape[0]:,} nós / {pg_lean.W.nnz:,} arestas")

    # comparação aresta-a-aresta: mesmo conjunto (row,col), peso igual a menos
    # do arredondamento float32 (o módulo guarda float64; produção final é float32)
    same_edge_set = max_rel = float("nan")
    if same_nodes and same_edges:
        cm, cl = pg_mod.W.tocoo(), pg_lean.W.tocoo()
        om = np.lexsort((cm.col, cm.row)); ol = np.lexsort((cl.col, cl.row))
        same_edge_set = bool(np.array_equal(cm.row[om], cl.row[ol])
                             and np.array_equal(cm.col[om], cl.col[ol]))
        if same_edge_set:
            wm = cm.data[om].astype(np.float64); wl = cl.data[ol].astype(np.float64)
            max_rel = float(np.max(np.abs(wm - wl) / wm))
    sum_mod, sum_lean = float(pg_mod.W.data.sum()), float(pg_lean.W.data.sum())
    print(f"[validate] nós={same_nodes} arestas={same_edges} index={same_index} "
          f"conjunto_arestas={same_edge_set} max_rel_peso={max_rel:.2e} "
          f"(soma {sum_mod:.4f} vs {sum_lean:.4f})")
    # float32 tem ~7 dígitos -> erro relativo por peso ~1e-6
    ok = same_nodes and same_edges and same_index and same_edge_set and max_rel < 1e-5
    print("[validate] RESULTADO:",
          "IDÊNTICO (a menos do float32) ✓" if ok else "DIVERGENTE ✗")
    sys.exit(0 if ok else 1)


def cmd_run(args):
    n, block_size = args.n, args.block_size
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    pg = _build_graph(n, block_size)
    n_nodes, n_edges = pg.W.shape[0], pg.W.nnz
    print(f"[run N={n}] backbone: {n_nodes:,} nós / {n_edges:,} arestas")

    # Um igraph vivo por vez (crítico para N baixo / muitas arestas em pouca RAM):
    # extrai o que precisa da 1ª partição e libera o grafo antes da 2ª execução.
    cr = CommunityDetector(resolution=RESOLUTION).detect(pg)
    membership = np.asarray(cr.membership, dtype=np.int64)
    Q = float(cr.partition.modularity)
    user_index = np.asarray(cr.user_index).astype(str)
    membership_list = list(cr.membership)
    del cr
    gc.collect()

    # piso de ruído: segunda execução do Leiden no mesmo grafo
    cr2 = CommunityDetector(resolution=RESOLUTION).detect(pg)
    ari_floor = ig.compare_communities(membership_list, cr2.membership, method="adjusted_rand")
    nmi_floor = ig.compare_communities(membership_list, cr2.membership, method="nmi")
    del cr2, membership_list
    gc.collect()

    macro_L3, macro_L2, info = macro_labels(membership, pg.W, n_nodes)
    part, wdeg = participation_and_degree(membership, pg.W)
    intra = intra_weight_fraction(membership, pg.W)

    sizes = pd.Series(membership).value_counts()
    metrics = {
        "N": n, "tau": TAU, "resolution": RESOLUTION,
        "n_nodes": int(n_nodes), "n_edges": int(n_edges),
        "modularity": Q,
        "n_communities": int(len(sizes)),
        "intra_weight_fraction": intra,
        "noise_floor": {"ari": float(ari_floor), "nmi": float(nmi_floor)},
        "macro": info,
        "weight_min": float(pg.W.data.min()), "weight_max": float(pg.W.data.max()),
        "weight_mean": float(pg.W.data.mean()),
    }
    (OUT_DIR / f"N{n}_metrics.json").write_text(json.dumps(metrics, indent=2))

    nodes = pd.DataFrame({
        "user_id": user_index,
        "community": membership.astype(np.int32),
        "macro_L3": macro_L3,
        "macro_L2": macro_L2,
        "participation": part,
        "wdeg": wdeg,
    })
    nodes.to_parquet(OUT_DIR / f"N{n}_nodes.parquet", index=False)
    # arestas em scratch (debug/recompute), não committadas
    Wc = pg.W.tocoo()
    pd.DataFrame({"src": Wc.row.astype(np.int32),
                  "dst": Wc.col.astype(np.int32),
                  "weight": Wc.data.astype(np.float32)}).to_parquet(
        WORK_DIR / f"N{n}_edges.parquet", index=False)

    print(f"[run N={n}] Q={Q:.4f} | comunidades={len(sizes)} | "
          f"dominantes={len(info['dominant_communities'])} "
          f"{info['dominant_frac']} | super-polos={info['n_super_poles']} | "
          f"intra={intra:.3f} | piso ARI={ari_floor:.4f}")
    print(f"[run N={n}] artefatos -> {OUT_DIR}/N{n}_*")


def _load_all():
    metrics, nodes = {}, {}
    for f in sorted(OUT_DIR.glob("N*_metrics.json")):
        m = json.loads(f.read_text())
        n = m["N"]
        metrics[n] = m
        nodes[n] = pd.read_parquet(OUT_DIR / f"N{n}_nodes.parquet").set_index("user_id")
    return metrics, dict(sorted(nodes.items()))


def _aligned_concordance(a, b):
    """Concordância após alinhamento guloso de rótulos (k pequeno). Devolve (taxa, crosstab)."""
    ct = pd.crosstab(pd.Series(np.asarray(a)), pd.Series(np.asarray(b)))
    M = ct.values.astype(float)
    total = M.sum()
    flat = sorted(((M[i, j], i, j) for i in range(M.shape[0]) for j in range(M.shape[1])),
                  reverse=True)
    used_r, used_c, matched = set(), set(), 0.0
    for val, i, j in flat:
        if i in used_r or j in used_c:
            continue
        used_r.add(i); used_c.add(j); matched += val
    return (matched / total if total else 0.0), ct


def _cmp(a, b):
    a, b = list(a), list(b)
    return {
        "ari": float(ig.compare_communities(a, b, method="adjusted_rand")),
        "nmi": float(ig.compare_communities(a, b, method="nmi")),
        "vi": float(ig.compare_communities(a, b, method="vi")),
    }


def cmd_summarize(args):
    metrics, nodes = _load_all()
    grid = sorted(nodes.keys())

    # ---- Peça 1: trajetória ----
    trajectory = []
    for n in grid:
        m = metrics[n]
        total_w = m["weight_mean"] * m["n_edges"]
        S = np.array(m["macro"]["flow_matrix_weight"])
        flow_pct = (S / total_w * 100).tolist() if total_w else S.tolist()
        trajectory.append({
            "N": n, "n_nodes": m["n_nodes"], "n_edges": m["n_edges"],
            "Q": m["modularity"], "n_communities": m["n_communities"],
            "n_dominant": len(m["macro"]["dominant_communities"]),
            "dominant_frac": m["macro"]["dominant_frac"],
            "n_super_poles": m["macro"]["n_super_poles"],
            "intra": m["intra_weight_fraction"],
            "floor_ari": m["noise_floor"]["ari"], "floor_nmi": m["noise_floor"]["nmi"],
            "flow_pct": flow_pct,
        })

    # ---- Peça 2: estabilidade macro (todos os pares hi>lo) ----
    macro_pairs = []
    for hi in grid:
        for lo in grid:
            if hi <= lo:
                continue
            common = nodes[hi].index.intersection(nodes[lo].index)
            if len(common) == 0:
                continue
            a2 = nodes[hi].loc[common, "macro_L2"].to_numpy()
            b2 = nodes[lo].loc[common, "macro_L2"].to_numpy()
            a3 = nodes[hi].loc[common, "macro_L3"].to_numpy()
            b3 = nodes[lo].loc[common, "macro_L3"].to_numpy()
            conc2, ct2 = _aligned_concordance(a2, b2)
            conc3, ct3 = _aligned_concordance(a3, b3)
            macro_pairs.append({
                "hi": hi, "lo": lo, "n_common": int(len(common)),
                "L2": {**_cmp(a2, b2), "concordance": conc2,
                       "confusion": {"rows": [str(x) for x in ct2.index],
                                     "cols": [str(x) for x in ct2.columns],
                                     "matrix": ct2.values.tolist()}},
                "L3": {**_cmp(a3, b3), "concordance": conc3},
                "floor_ari_hi": metrics[hi]["noise_floor"]["ari"],
                "floor_ari_lo": metrics[lo]["noise_floor"]["ari"],
            })

    # ---- Peça 3: faixa incremental (degraus adjacentes) ----
    incremental = []
    for hi, lo in zip(grid[1:], grid[:-1]):   # (10,7),(15,10),(20,15) -> lo<hi adjacentes
        df_lo = nodes[lo]
        in_hi = df_lo.index.isin(nodes[hi].index)
        incr, core = df_lo[~in_hi], df_lo[in_hi]

        def dist(df):
            d = df["macro_L2"].value_counts(normalize=True)
            return {str(k): float(v) for k, v in d.items()}
        incremental.append({
            "hi": hi, "lo": lo, "n_incr": int(len(incr)), "n_core": int(len(core)),
            "incr_dist_L2": dist(incr), "core_dist_L2": dist(core),
            "mean_part_incr": float(incr["participation"].mean()),
            "mean_part_core": float(core["participation"].mean()),
            "mean_wdeg_incr": float(incr["wdeg"].mean()),
            "mean_wdeg_core": float(core["wdeg"].mean()),
            "residue_frac_incr": float((incr["macro_L2"] == -1).mean()),
            "residue_frac_core": float((core["macro_L2"] == -1).mean()),
        })

    summary = {"grid": grid, "tau": TAU, "resolution": RESOLUTION,
               "theta_flow": THETA_FLOW, "dominant_frac": DOMINANT_FRAC,
               "trajectory": trajectory, "macro_pairs": macro_pairs,
               "incremental": incremental}
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---- impressão legível ----
    print("\n=== PEÇA 1 — TRAJETÓRIA ESTRUTURAL ===")
    print(f"{'N':>3} {'nodes':>7} {'edges':>11} {'Q':>6} {'#com':>5} {'#dom':>4} "
          f"{'#SP':>3} {'intra':>6} {'floor':>6}  dominant_frac")
    for t in trajectory:
        print(f"{t['N']:>3} {t['n_nodes']:>7,} {t['n_edges']:>11,} {t['Q']:>6.3f} "
              f"{t['n_communities']:>5} {t['n_dominant']:>4} {t['n_super_poles']:>3} "
              f"{t['intra']:>6.3f} {t['floor_ari']:>6.3f}  "
              f"{[round(x,3) for x in t['dominant_frac']]}")

    print("\n=== PEÇA 2 — ESTABILIDADE MACRO (núcleo comum) ===")
    print(f"{'hi':>3} {'lo':>3} {'n_common':>8}  | L2: {'ARI':>6} {'NMI':>6} {'VI':>6} "
          f"{'conc':>6}  | L3: {'ARI':>6} {'conc':>6}  (piso ARI hi/lo)")
    for p in macro_pairs:
        print(f"{p['hi']:>3} {p['lo']:>3} {p['n_common']:>8,}  | "
              f"     {p['L2']['ari']:>6.3f} {p['L2']['nmi']:>6.3f} {p['L2']['vi']:>6.3f} "
              f"{p['L2']['concordance']:>6.3f}  | "
              f"     {p['L3']['ari']:>6.3f} {p['L3']['concordance']:>6.3f}   "
              f"({p['floor_ari_hi']:.3f}/{p['floor_ari_lo']:.3f})")

    print("\n=== PEÇA 3 — FAIXA INCREMENTAL (usuários que entram ao baixar N) ===")
    for inc in incremental:
        print(f"\n{inc['lo']}<-{inc['hi']}: +{inc['n_incr']:,} entram "
              f"(núcleo {inc['n_core']:,})")
        print(f"   dist L2 incremental: {inc['incr_dist_L2']}")
        print(f"   dist L2 núcleo:      {inc['core_dist_L2']}")
        print(f"   participation  incr={inc['mean_part_incr']:.3f} vs core={inc['mean_part_core']:.3f}")
        print(f"   wdeg médio     incr={inc['mean_wdeg_incr']:.2f} vs core={inc['mean_wdeg_core']:.2f}")
        print(f"   resíduo frac   incr={inc['residue_frac_incr']:.3f} vs core={inc['residue_frac_core']:.3f}")
    print(f"\nsummary -> {OUT_DIR/'summary.json'}")


def cmd_plots(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    summary = json.loads((OUT_DIR / "summary.json").read_text())
    ASSETS.mkdir(parents=True, exist_ok=True)
    traj = summary["trajectory"]
    Ns = [t["N"] for t in traj]

    # fig 1: Q & intra vs N ; blocos dominantes vs N
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.3))
    ax1.plot(Ns, [t["Q"] for t in traj], "o-", label="Modularidade Q")
    ax1.plot(Ns, [t["intra"] for t in traj], "s--", label="% peso intra-comunidade")
    ax1.set_xlabel("N (mín. retweets/usuário)"); ax1.set_ylim(0, 1.05)
    ax1.set_title("Coesão estrutural vs N"); ax1.legend(); ax1.grid(alpha=.3)
    ax1.invert_xaxis()
    # tamanhos dos 3 maiores blocos
    for rank, color in zip(range(3), ["#1f77b4", "#ff7f0e", "#2ca02c"]):
        ys = [t["dominant_frac"][rank] if len(t["dominant_frac"]) > rank else 0 for t in traj]
        ax2.plot(Ns, ys, "o-", color=color, label=f"{rank+1}º maior bloco")
    ax2.set_xlabel("N (mín. retweets/usuário)"); ax2.set_ylabel("fração dos nós")
    ax2.set_title("Tamanho dos maiores blocos vs N\n(3º bloco surge só em N baixo)")
    ax2.legend(); ax2.grid(alpha=.3); ax2.invert_xaxis()
    fig.tight_layout(); fig.savefig(ASSETS / "sensibilidade_N_trajetoria.png", dpi=130)
    plt.close(fig)

    # fig 2: heatmaps de fluxo por N
    k = len(Ns)
    fig, axes = plt.subplots(1, k, figsize=(3.4 * k, 3.4))
    if k == 1:
        axes = [axes]
    for ax, t in zip(axes, traj):
        F = np.array(t["flow_pct"])
        im = ax.imshow(F, cmap="magma_r", vmin=0)
        ax.set_title(f"N={t['N']} · {t['n_super_poles']} super-polos")
        for i in range(F.shape[0]):
            for j in range(F.shape[1]):
                ax.text(j, i, f"{F[i,j]:.1f}", ha="center", va="center",
                        fontsize=8, color="white" if F[i, j] > F.max()*.5 else "black")
        ax.set_xticks(range(F.shape[0])); ax.set_yticks(range(F.shape[0]))
        ax.set_xticklabels([f"b{i}" for i in range(F.shape[0])])
        ax.set_yticklabels([f"b{i}" for i in range(F.shape[0])])
    fig.suptitle("Fluxo de co-amplificação entre blocos dominantes (% do peso total)")
    fig.tight_layout(); fig.savefig(ASSETS / "sensibilidade_N_fluxo.png", dpi=130)
    plt.close(fig)

    # fig 3: matrizes de confusão L2 dos pares adjacentes
    adj = [p for p in summary["macro_pairs"]
           if (p["hi"], p["lo"]) in list(zip(Ns[1:], Ns[:-1]))]
    if adj:
        fig, axes = plt.subplots(1, len(adj), figsize=(3.6 * len(adj), 3.4))
        if len(adj) == 1:
            axes = [axes]
        for ax, p in zip(axes, adj):
            C = np.array(p["L2"]["confusion"]["matrix"], dtype=float)
            Cn = C / C.sum() * 100
            im = ax.imshow(Cn, cmap="Blues", vmin=0)
            for i in range(C.shape[0]):
                for j in range(C.shape[1]):
                    ax.text(j, i, f"{Cn[i,j]:.1f}", ha="center", va="center", fontsize=8,
                            color="white" if Cn[i, j] > Cn.max()*.5 else "black")
            ax.set_title(f"N={p['hi']} (linhas) × N={p['lo']} (col)\n"
                         f"ARI={p['L2']['ari']:.3f} conc={p['L2']['concordance']:.2f}")
            ax.set_yticks(range(len(p["L2"]["confusion"]["rows"])))
            ax.set_yticklabels(p["L2"]["confusion"]["rows"])
            ax.set_xticks(range(len(p["L2"]["confusion"]["cols"])))
            ax.set_xticklabels(p["L2"]["confusion"]["cols"])
        fig.suptitle("Matriz de confusão dos super-polos (L2) no núcleo comum (% usuários)")
        fig.tight_layout(); fig.savefig(ASSETS / "sensibilidade_N_confusao.png", dpi=130)
        plt.close(fig)

    # fig 4: faixa incremental — distribuição de super-polo + participation
    inc = summary["incremental"]
    if inc:
        fig, (axa, axb) = plt.subplots(1, 2, figsize=(12, 4.3))
        labels = sorted({k for d in inc for k in d["incr_dist_L2"]} |
                        {k for d in inc for k in d["core_dist_L2"]})
        x = np.arange(len(inc)); w = 0.8 / max(len(labels), 1)
        for li, lab in enumerate(labels):
            axa.bar(x + li*w, [d["incr_dist_L2"].get(lab, 0) for d in inc], w,
                    label=f"super-polo {lab}")
        axa.set_xticks(x + w*(len(labels)-1)/2)
        axa.set_xticklabels([f"{d['lo']}<-{d['hi']}" for d in inc])
        axa.set_title("Distribuição de super-polo da FAIXA INCREMENTAL")
        axa.set_ylabel("fração"); axa.legend(); axa.grid(alpha=.3)
        axb.plot(x, [d["mean_part_incr"] for d in inc], "o-", label="incremental")
        axb.plot(x, [d["mean_part_core"] for d in inc], "s--", label="núcleo")
        axb.set_xticks(x); axb.set_xticklabels([f"{d['lo']}<-{d['hi']}" for d in inc])
        axb.set_title("Participation coefficient médio (fronteira)")
        axb.legend(); axb.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(ASSETS / "sensibilidade_N_faixa.png", dpi=130)
        plt.close(fig)
    print(f"[plots] -> {ASSETS}/sensibilidade_N_*.png")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Sensibilidade de N (estrutural)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load")
    pv = sub.add_parser("validate"); pv.add_argument("--n", type=int, default=10)
    pv.add_argument("--block-size", type=int, default=2000)
    pr = sub.add_parser("run"); pr.add_argument("--n", type=int, required=True)
    pr.add_argument("--block-size", type=int, default=2000)
    sub.add_parser("summarize")
    sub.add_parser("plots")
    args = p.parse_args()

    {"load": cmd_load, "validate": cmd_validate, "run": cmd_run,
     "summarize": cmd_summarize, "plots": cmd_plots}[args.cmd](args)
