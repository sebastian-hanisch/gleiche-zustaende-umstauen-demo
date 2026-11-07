"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Eigenschaften der Sonderbuchten und der vorberechneten Tabellen."""

import gzu_algorithm as A
import gzu_constants as C
import gzu_evaluation as ev
import gzu_presets as P
from gzu_scenario import canonical, make_bay, max_height


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.STACKS_MIN <= preset["stacks"] <= C.STACKS_MAX and C.LAYERS_MIN <= preset["layers"] <= C.LAYERS_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]))


def _nodes(a):
    return {v: a.res(v).nodes for v in C.VARIANTS}


def test_everyday_preset():
    a = _analysis("Alltag (3 Stapel, 3 Lagen)")
    n = _nodes(a)
    assert (a.lower, a.optimum) == (4, 5) and a.tree == A.TreeCount(229, 114, 20, 18) and not any(r.capped for r in a.results.values())
    assert [n[v] for v in C.VARIANTS] == [11, 11, 11, 11, 34, 22, 11]


def test_mini_preset_is_the_stage_two_bay_with_nine_nodes_and_four_states():
    p = C.PRESETS["Die Mini-Bucht"]
    assert canonical(make_bay(p["stacks"], p["layers"], p["seed"])) == canonical(C.MINI_BAY)
    a = _analysis("Die Mini-Bucht")
    assert (a.lower, a.optimum) == (1, 2) and a.tree == A.TreeCount(9, 5, 4, 4)
    assert [n for n in _nodes(a).values()] == [6, 6, 6, 6, 7, 5, 5]


def test_repeat_preset_has_a_huge_tree_and_few_states():
    a = _analysis("Fast nur Wiederholung (4 Stapel, 3 Lagen)")
    assert a.tree == A.TreeCount(2_703_457, 1_802_241, 1028, 619) and a.tree.nodes / a.tree.raw > 2600
    assert (a.lower, a.optimum) == (6, 8) and a.res(C.VARIANTS[0]).nodes == 26 and not any(r.capped for r in a.results.values())


def test_tail_preset_the_memo_saves_a_factor_of_44_and_the_tree_is_not_counted():
    a = _analysis("Wo das Merken hilft (5 Stapel, 4 Lagen)")
    ida, canon = a.res(C.VARIANTS[0]), a.res(C.VARIANTS[3])
    assert a.tree is None and (ida.nodes, canon.nodes, canon.hits, canon.table) == (400_339, 8_975, 1429, 1411) and round(ida.nodes / canon.nodes, 1) == 44.6
    assert (a.lower, a.optimum) == (8, 15) and a.res(C.VARIANTS[4]).capped and not ida.capped and not canon.capped and not a.res(C.VARIANTS[6]).capped


def test_the_named_seeds_are_the_documented_bays():
    assert (C.MINI_SEED, C.EVERYDAY_SEED, C.REPEAT_SEED, C.TAIL_SEED) == (223, 12, 3, 1) and C.MINI_HEIGHT == C.COUNTER_HEIGHT == 4


def test_stored_cells_equal_a_fresh_computation():
    bands = ev.load_bands()
    for stacks, layers, n in ((3, 2, 100), (4, 2, 100), (3, 3, 100)):
        key = ev.cell_key(stacks, layers)
        assert bands["baum"][key] == ev.tree_stats(ev.tree_rows(stacks, layers, C.DEFAULT_EXTRA, range(n))), key
        assert bands["ida"][key] == ev.ida_stats(ev.ida_rows(stacks, layers, C.DEFAULT_EXTRA, range(n))), key
    assert bands["merken"][ev.cell_key(3, 3)] == ev.memo_stats(ev.memo_rows(3, 3, C.DEFAULT_EXTRA, range(100)))
    assert bands["raum"][ev.cell_key(3, 3)] == ev.space_stats(ev.space_rows(3, 3, C.DEFAULT_EXTRA, range(5)))
    assert bands["baum"][ev.cell_key(5, 2)] == ev.tree_stats(ev.tree_rows(5, 2, C.DEFAULT_EXTRA, range(60)))


def test_every_band_cell_exists():
    bands = ev.load_bands()
    assert set(bands["baum"]) == {ev.cell_key(s, l) for s, l, _ in C.TREE_CELLS} and set(bands["ida"]) == {ev.cell_key(s, l) for s, l, _ in C.IDA_CELLS}
    assert set(bands["merken"]) == {ev.cell_key(s, l) for s, l, _ in C.MEMO_CELLS} and set(bands["raum"]) == {ev.cell_key(s, l) for s, l, _ in C.SPACE_CELLS}
    for kind, cells in (("baum", C.TREE_CELLS), ("ida", C.IDA_CELLS), ("merken", C.MEMO_CELLS), ("raum", C.SPACE_CELLS)):
        assert all(bands[kind][ev.cell_key(s, l)]["n"] == n for s, l, n in cells), kind


def test_every_slider_combination_of_stacks_and_layers_has_an_ida_cell():
    cells = {(s, l) for s, l, _ in C.IDA_CELLS}
    assert cells == {(s, l) for s in range(C.STACKS_MIN, C.STACKS_MAX + 1) for l in range(C.LAYERS_MIN, C.LAYERS_MAX + 1)}


def test_rows_use_the_fixed_seeds_and_cap():
    rows = ev.tree_rows(3, 2, 2, range(10))
    assert [r["seed"] for r in rows] == list(range(10))
    for r in rows:
        bay = make_bay(3, 2, r["seed"])
        t = A.count_tree(bay, max_height(2, 2))
        assert (r["nodes"], r["raw"], r["canon"]) == (t.nodes, t.raw, t.canon)
    assert ev.tree_rows(4, 3, 2, [3], state_cap=500)[0] == {"seed": 3, "nodes": None, "raw": None, "canon": None}          # Bucht 3 hat 1 028 Zustände
    irows = ev.ida_rows(3, 2, 2, range(5))
    for r in irows:
        bay = make_bay(3, 2, r["seed"])
        c = A.search(bay, max_height(2, 2), "ida", "tight", memo="canon")
        assert r["base"] == A.search(bay, max_height(2, 2), "ida", "tight").nodes and r["canon"] == c.nodes and r["table"] == c.table and r["hits"] == c.hits / c.nodes
    capped = ev.ida_rows(4, 3, 2, [3], cap=10)[0]
    assert capped["base"] is None and capped["canon"] is None and capped["hits"] is None
    assert ev.memo_rows(3, 2, 2, [0])[0]["enum+canon"] == A.search(make_bay(3, 2, 0), 4, "enum", "tight", memo="canon").nodes
    assert ev.space_rows(3, 3, 2, [0], cap=5)[0]["raw"] is None
