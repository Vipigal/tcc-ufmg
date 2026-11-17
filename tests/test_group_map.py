import json

import numpy as np
import pandas as pd

from modules.group_map import (GroupMap, GroupMapRenderer, arrange_units, dominant_pairs, hit_grid,
                               placement_units, top_k_edges)


def _cluster(c, shared, shared_with, frac=0.3, group=1):
    return {"community": c, "group": group, "label": f"Grupo {group}", "frac_nodes": frac,
            "n_nodes": int(frac * 1000), "shared": shared, "shared_with": shared_with}


def test_top_k_edges_keeps_the_strongest_edges_of_each_node():
    src = np.array([0, 0, 0, 1])
    dst = np.array([1, 2, 3, 2])
    w = np.array([0.9, 0.5, 0.1, 0.2])
    # k=1: nó 0 → (0,1); nó 1 → (0,1); nó 2 → (0,2); nó 3 → (0,3)
    assert sorted(top_k_edges(src, dst, w, 1).tolist()) == [0, 1, 2]


def test_dominant_pair_needs_high_share_concentrated_in_one_partner():
    clusters = [
        _cluster(1, 0.016, {"0": 0.012, "2": 0.001}),
        _cluster(0, 0.224, {"1": 0.015, "2": 0.208}),
        _cluster(2, 0.515, {"0": 0.501, "1": 0.013}),
    ]
    assert dominant_pairs(clusters) == [(0, 2, 0.501)]


def test_spread_sharing_has_no_dominant_pair():
    clusters = [
        _cluster(1, 0.517, {"0": 0.204, "2": 0.165, "4": 0.147}),
        _cluster(4, 0.77, {"0": 0.226, "1": 0.353, "2": 0.19}),
        _cluster(0, 0.628, {"1": 0.293, "2": 0.198, "4": 0.135}),
        _cluster(2, 0.645, {"0": 0.233, "1": 0.279, "4": 0.133}),
    ]
    assert dominant_pairs(clusters) == []


def test_dominant_pair_becomes_one_placement_unit():
    assert placement_units([1, 0, 2], [(0, 2, 0.5)]) == [(0, 2), (1,)]


def test_units_without_dominant_pair_keep_the_minimum_gap():
    units = [(0,), (1,), (2,), (3,)]
    radius = {u: 0.5 for u in units}
    start = {u: np.array([0.01 * i, 0.0]) for i, u in enumerate(units)}
    pos = arrange_units(units, radius, start, strength=lambda a, b: 1.0, gap=1.5, isolated=set())
    for i, a in enumerate(units):
        for b in units[i + 1:]:
            assert np.linalg.norm(pos[a] - pos[b]) >= 1.5 * (radius[a] + radius[b]) - 1e-6


def test_isolated_unit_goes_outside_the_others():
    units = [(0,), (1,), (2,), (9,)]
    radius = {(0,): 0.6, (1,): 0.6, (2,): 0.6, (9,): 0.2}
    start = {(0,): np.array([0.0, 1.0]), (1,): np.array([1.0, -1.0]), (2,): np.array([-1.0, -1.0]),
             (9,): np.array([0.0, 0.0])}
    pos = arrange_units(units, radius, start, strength=lambda a, b: 0.5, gap=1.2, isolated={(9,)})
    center = np.mean([pos[u] for u in units[:3]], axis=0)
    reach = max(np.linalg.norm(pos[u] - center) + radius[u] for u in units[:3])
    assert np.linalg.norm(pos[(9,)] - center) > reach


def test_hit_grid_assigns_each_cell_to_its_majority_group():
    x = np.array([0.05, 0.06, 0.07, 0.95])
    y = np.array([0.05, 0.05, 0.05, 0.95])
    comm = np.array([3, 3, 4, 7])
    grid = hit_grid(x, y, comm, n=10)
    assert grid[0] == 3
    assert grid[99] == 7
    assert grid[1] == 3
    assert grid[55] == -1


def _toy_processed(tmp_path):
    rng = np.random.default_rng(0)
    n = 40
    comm = np.array([0] * 20 + [1] * 20, dtype=np.int32)
    src, dst, w = [], [], []
    for i in range(n):
        for j in range(i + 1, n):
            same = comm[i] == comm[j]
            if rng.random() < (0.6 if same else 0.05):
                src.append(i)
                dst.append(j)
                w.append(0.5 if same else 0.15)
    d = tmp_path / "toy"
    d.mkdir()
    pd.DataFrame({"user_id": [f"u{i}" for i in range(n)], "community": comm}).to_parquet(d / "graph_nodes.parquet")
    pd.DataFrame({"src": src, "dst": dst, "weight": w}).to_parquet(d / "graph_edges.parquet")
    pd.DataFrame({"x": rng.random(n), "y": rng.random(n), "community": comm}).to_parquet(d / "drl_layout.parquet")
    (d / "run_config.json").write_text(json.dumps({"layout_top_k": 12, "layout_seed": 42}))
    return d


def test_group_map_stage_caches_fa2_and_drl_coordinates_per_node(tmp_path):
    d = _toy_processed(tmp_path)
    result = GroupMap(top_k=12, iterations=20).run(d, out_dir=d)
    nodes, edges = result["nodes"], result["edges"]
    assert set(nodes.columns) >= {"node", "community", "fa2_x", "fa2_y", "drl_x", "drl_y", "degree"}
    assert len(nodes) == 40
    bridges = edges[edges["kind"] == "bridge"]
    assert len(bridges) > 0
    assert (nodes["community"].to_numpy()[bridges["a"]] != nodes["community"].to_numpy()[bridges["b"]]).all()
    assert result["pair_counts"]["0-1"] > 0
    assert (d / "group_map_nodes.parquet").exists()


def test_renderer_writes_images_and_click_map(tmp_path):
    d = _toy_processed(tmp_path)
    GroupMap(top_k=12, iterations=20).run(d, out_dir=d)
    meta = {"clusters": [_cluster(0, 0.1, {"1": 0.1}, frac=0.5, group=1),
                         _cluster(1, 0.1, {"0": 0.1}, frac=0.5, group=2)]}
    out = tmp_path / "export"
    info = GroupMapRenderer(gap=1.25, max_bridges=10, grid=20).render(d, meta, out)
    for f in ("grafo-claro.webp", "grafo-escuro.webp", "grafo-claro-mini.webp", "grafo-escuro-mini.webp", "grafo.json",
              "grafo-claro-g0.webp", "grafo-claro-g1.webp", "grafo-escuro-g0.webp", "grafo-escuro-g1.webp"):
        assert (out / f).exists()
    saved = json.loads((out / "grafo.json").read_text())
    assert len(saved["grid"]["cells"]) == 400
    assert {g["community"] for g in saved["groups"]} == {0, 1}
    assert info["dominant_pairs"] == []


def test_layout_keeps_every_point_inside_the_frame_with_room_for_labels(tmp_path):
    from modules.group_map import EXTENT, FILL
    d = _toy_processed(tmp_path)
    GroupMap(top_k=12, iterations=20).run(d, out_dir=d)
    clusters = [_cluster(0, 0.1, {"1": 0.1}, frac=0.5, group=1), _cluster(1, 0.1, {"0": 0.1}, frac=0.5, group=2)]
    lay = GroupMapRenderer(gap=1.25, max_bridges=10, grid=20).layout(GroupMap()._load(d), clusters)
    pts = lay["xy"][lay["keep"]]
    assert np.abs(pts).max() <= FILL + 1e-9 < EXTENT
