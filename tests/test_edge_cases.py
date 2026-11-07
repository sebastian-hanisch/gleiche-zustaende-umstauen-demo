"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import gzu_algorithm as A
import gzu_evaluation as ev


def test_two_stacks_one_hub_in_every_mode_memo_and_symmetry():
    for mode in A.MODES:
        for memo in A.MEMOS:
            for sym in (False, True):
                r = A.search(((1, 2), ()), 3, mode, "tight", memo=memo, sym=sym)
                assert (r.optimum, r.nodes, r.leaves) == (1, 2, 1), (mode, memo, sym)           # Wurzel, ein Hub auf den leeren Stapel, Blatt


def test_single_container_and_empty_bay():
    assert A.count_tree(((1,), ()), 2) == A.TreeCount(1, 1, 1, 1)
    assert A.count_tree(((), ()), 2) == A.TreeCount(1, 1, 1, 1)
    assert A.search(((), ()), 2, "ida", "tight", memo="canon").stages == ((0, 1, True, 0, 0),)


def test_two_empty_stacks_make_the_symmetry_break_bite_exactly_there():
    bay = ((1, 3, 2), (), ())                                           # die 2 muss weg und kann auf zwei gleiche leere Stapel; danach die 3 ebenso
    full, broken = A.search(bay, 3, "enum", "index"), A.search(bay, 3, "enum", "index", sym=True)
    assert (full.optimum, full.nodes, full.leaves) == (2, 11, 6) and (broken.optimum, broken.nodes, broken.leaves) == (2, 5, 2)
    assert A.count_tree(bay, 3) == A.TreeCount(11, 6, 6, 4)             # 6 verschiedene Zustände, 4 bis auf Vertauschen der beiden leeren Stapel


def test_exactly_two_containers_in_each_order():
    assert A.search(((2,), (1,)), 2, "ida", "index", memo="canon").optimum == 0
    assert A.search(((2, 1),), 2, "ida", "index", memo="raw").optimum == 0
    assert A.search(((1, 2), ()), 2, "ida", "index", memo="canon", sym=True).optimum == 1


def test_only_one_free_slot_leaves_exactly_one_child_per_hub():
    r = A.search(((1, 5), (2, 3), (4, 6)), 3, "ida", "index", memo="canon")       # Höchsthöhe 3: jeder Blocker findet höchstens einen freien Platz
    assert r.optimum is not None and r.leaves == 1


def test_capped_result_never_claims_an_optimum_and_the_bay_analysis_says_so(counter):
    bay, h = counter
    r = A.search(bay, h, "enum", "index", cap=10)
    assert r.optimum is None and r.capped and r.leaves <= 10
    capped = A.SearchResult(None, 10, 2, True, None)
    a = ev.Analysis(bay, h, 3, None, {v: capped for v in ev.C.VARIANTS})
    assert a.optimum is None


def test_num_and_factor_text():
    assert ev.num(5) == "5" and ev.num(1234) == "1 234" and ev.num(1_000_000) == "1 000 000"
    assert ev.factor_text(1.0) == "1,0" and ev.factor_text(9.94) == "9,9" and ev.factor_text(10.0) == "10" and ev.factor_text(47.4) == "47" and ev.factor_text(185825.5) == "185 826"
    assert ev.ratio_text(1.5) == "1,50" and ev.ratio_text(0.714) == "0,71"


def test_stats_with_all_runs_over_the_limit_have_no_medians():
    rows = [{"seed": 0, "nodes": None, "raw": None, "canon": None}]
    st = ev.tree_stats(rows)
    assert st["nodes"] == {"ok": 0, "over": 1, "median": None, "mean": None, "max": None} and st["paths"]["median"] is None and st["sym"]["n"] == 0
    rows = [{"seed": 0, "base": None, "sym": None, "raw": None, "canon": None, "hits": None, "table": None}]
    st = ev.ida_stats(rows)
    assert st["canon"]["median"] is None and st["hits"] is None and st["table"] == {"median": None, "max": None}
    rows = [{"seed": 0, "table": None, "ida": None, "ida+canon": None, "enum+canon": None, "bb+canon": None, "bblb+canon": None}]
    st = ev.memo_stats(rows)
    assert st["r_bb+canon"]["median"] is None and st["table"]["median"] is None
    assert ev.space_stats([{"seed": 0, "raw": None, "canon": None}])["raw"]["median"] is None


def test_ratio_stat_gain_counts_only_real_gains():
    st = ev.ida_stats([{"seed": 0, "base": 10, "sym": 10, "raw": 5, "canon": 5, "hits": 0.2, "table": 4}, {"seed": 1, "base": 4, "sym": 4, "raw": 4, "canon": 4, "hits": 0.0, "table": 2}])
    assert st["canon"] == {"n": 2, "median": 1.5, "mean": 1.5, "min": 1.0, "max": 2.0, "gain": 0.5} and st["sym"]["gain"] == 0.0
    assert st["hits"] == 0.1 and st["table"] == {"median": 3.0, "max": 4}
