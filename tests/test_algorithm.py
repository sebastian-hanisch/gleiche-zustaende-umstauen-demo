"""Kern gegen Handrechnung und Eigenschaften (DEMO-PLAYBOOK §1b und §12)."""

import pytest

import gzu_algorithm as A
from gzu_scenario import make_bay, max_height


def test_autopop_blockers_and_canon_by_hand(mini):
    bay, _ = mini
    assert A.autopop(bay) == (bay, [])                                 # die 1 liegt unter der 4
    assert A.autopop(((2, 1), (3,))) == (((), ()), [1, 2, 3])
    assert A.blocker_count(bay) == 1 and A.stack_blockers((1, 2, 3)) == 2 and A.stack_blockers((3, 2, 1)) == 0
    assert A.target_stack(bay) == (1, 0) and A.target_stack(((5, 3), (2, 1))) == (1, 1)
    assert A.canon(((5, 2), (), (1, 4))) == ((), (1, 4), (5, 2)) and A.canon(((1,), (2,))) == A.canon(((2,), (1,)))


def test_tree_count_of_the_mini_bay_by_hand(mini):
    t = A.count_tree(*mini)
    assert (t.nodes, t.leaves, t.raw, t.canon) == (9, 5, 4, 4)
    assert A.count_states(*mini) == (4, 4)


def test_state_visits_of_the_mini_bay_by_hand(mini):
    visits = A.state_visits(*mini)
    assert [(A.fmt_state(s), v, g) for s, v, g in visits] == [("(1, 4) | (5, 2) | (6, 3)", 1, 0), ("() | (5, 2, 4) | (6, 3)", 1, 1), ("() | () | ()", 5, 2), ("() | (5) | (6, 3, 4)", 2, 1)]
    assert sum(v for _, v, _ in visits) == 9


def test_tree_count_of_the_counterexample_by_hand(counter):
    t = A.count_tree(*counter)
    assert (t.nodes, t.leaves, t.raw, t.canon) == (153, 77, 25, 16) and A.count_states(*counter) == (25, 16)
    assert len(A.state_visits(*counter)) == 25 and sum(v for _, v, _ in A.state_visits(*counter)) == 153


def test_mini_bay_by_hand_in_every_variant(mini):
    bay, h = mini
    assert A.search(bay, h, "enum", "index").nodes == 9
    # Merken: in Stapelreihenfolge kommt der Zustand C zuerst mit 2 Hüben (über B), dann mit 1 Hub: er wird erneut bearbeitet (kein Treffer); in der Reihenfolge der engsten
    # Passung kommt C zuerst mit 1 Hub, der Besuch über B mit 2 Hüben ist ein Treffer und fällt weg (7 statt 9 Knoten, 3 statt 5 Blätter).
    r = A.search(bay, h, "enum", "index", memo="canon")
    assert (r.nodes, r.leaves, r.hits, r.table) == (9, 5, 0, 3)
    r = A.search(bay, h, "enum", "tight", memo="canon")
    assert (r.optimum, r.nodes, r.leaves, r.hits, r.table) == (2, 7, 3, 1, 3)
    for order in ("index", "tight"):
        ida = A.search(bay, h, "ida", order, memo="canon")
        assert (ida.nodes, ida.hits, ida.table, ida.stages) == (6, 0, 2, ((1, 3, False, 0, 1), (2, 3, True, 0, 2)))


def test_counterexample_by_hand_in_every_variant(counter):
    bay, h = counter
    ida = A.search(bay, h, "ida", "tight", memo="canon")
    assert (ida.optimum, ida.nodes, ida.hits, ida.table) == (4, 15, 0, 7) and ida.stages == ((3, 3, False, 0, 1), (4, 12, True, 0, 7))
    assert A.search(bay, h, "ida", "tight").nodes == 15 == A.search(bay, h, "ida", "tight", sym=True).nodes
    expected = {("enum", "index", "raw"): (73, 6, 24), ("enum", "index", "canon"): (53, 7, 15), ("enum", "tight", "canon"): (31, 8, 15),
                ("bb", "tight", "raw"): (23, 2, 11), ("bb", "tight", "canon"): (21, 3, 10), ("bblb", "tight", "canon"): (17, 0, 8)}
    for (mode, order, memo), (nodes, hits, table) in expected.items():
        r = A.search(bay, h, mode, order, memo=memo)
        assert (r.optimum, r.nodes, r.hits, r.table) == (4, nodes, hits, table), (mode, order, memo)
    assert A.search(bay, h, "enum", "index", sym=True).nodes == 87           # Symmetriebruch allein: die vollen Aufzählung schrumpft von 153 auf 87


def test_symmetry_break_only_skips_all_but_the_first_empty_stack():
    stacks = ((7,), (), (5, 8), ())                                    # Blocker 3 von Stapel 1; leer sind Stapel 2 und 4
    assert A.child_targets(stacks, 0, 6, 3, "index") == [1, 2, 3] and A.child_targets(stacks, 0, 6, 3, "index", sym=True) == [1, 2]
    assert A.child_targets(stacks, 0, 6, 3, "tight") == [2, 1, 3] and A.child_targets(stacks, 0, 6, 3, "tight", sym=True) == [2, 1]      # engste Passung: erst Stapel 3 (5 > 3), dann die leeren
    assert A.child_targets(stacks, 0, 6, 3, "anti", sym=True) == [3, 2]                                                                   # umgekehrt: zuerst der letzte leere Stapel, der andere entfällt
    full = ((7,), (5, 8), (9,))
    assert A.child_targets(full, 0, 6, 3, "index", sym=True) == A.child_targets(full, 0, 6, 3, "index")      # ohne leere Stapel ändert sich nichts


def test_child_targets_orders_by_hand():
    stacks = ((7,), (5, 8), (9,), ())                                  # Blocker 3 kommt von Stapel 1 (Index 0), die übergebene Bucht ist die ohne ihn
    assert A.child_targets(stacks, 0, 6, 3, "index") == [1, 2, 3]
    assert A.child_targets(stacks, 0, 6, 3, "tight") == [1, 2, 3]
    assert A.child_targets(stacks, 0, 6, 3, "anti") == [3, 2, 1]
    assert A.child_targets(((7,), (2, 8), (1,), (4,)), 0, 6, 9, "tight") == [3, 1, 2]
    assert A.child_targets(((1, 2), (3, 4), (5,)), 0, 2, 9, "index") == [2]


def test_stage_hits_and_tables_add_up():
    for sd in range(60):
        bay, h = make_bay(3, 3, sd), max_height(3, 2)
        r = A.search(bay, h, "ida", "tight", memo="canon")
        assert sum(s[1] for s in r.stages) == r.nodes and sum(s[3] for s in r.stages) == r.hits and max(s[4] for s in r.stages) == r.table
        assert r.first_leaf == r.optimum == r.stages[-1][0]


def test_sorted_bay_has_exactly_one_node_and_an_empty_table_in_every_variant():
    for mode in A.MODES:
        for memo in A.MEMOS:
            r = A.search(((5, 3), (2, 1), (6, 4)), 4, mode, "tight", memo=memo, sym=memo is None)
            assert (r.optimum, r.nodes, r.leaves, r.hits, r.table) == (0, 1, 1, 0, 0), (mode, memo)
    assert A.count_tree(((5, 3), (2, 1), (6, 4)), 4) == A.TreeCount(1, 1, 1, 1)


def test_cap_counts_nodes_over_all_stages_and_reports_hits_and_table(counter):
    bay, h = counter
    ok = A.search(bay, h, "ida", "tight", cap=15, memo="canon")
    assert not ok.capped and ok.nodes == 15
    r = A.search(bay, h, "ida", "tight", cap=14, memo="canon")           # genau ein Knoten zu wenig
    assert r.capped and r.optimum is None and r.nodes == 14 and sum(s[1] for s in r.stages) == 14 and r.stages[-1][2] is False
    r = A.search(bay, h, "enum", "index", cap=40, memo="canon")
    assert r.capped and r.nodes == 40 and r.optimum is None
    assert not A.search(bay, h, "enum", "index", cap=53, memo="canon").capped and A.search(bay, h, "enum", "index", cap=52, memo="canon").capped


def test_state_cap_of_the_tree_count(counter):
    bay, h = counter
    assert A.count_tree(bay, h, state_cap=25) is not None and A.count_tree(bay, h, state_cap=24) is None
    assert A.count_states(bay, h, cap=25) == (25, 16) and A.count_states(bay, h, cap=24) is None


def test_state_visits_refuses_big_trees(counter):
    with pytest.raises(ValueError):
        A.state_visits(*counter, max_nodes=100)                         # der Baum hat 153 Knoten
    assert A.state_visits(*counter, max_nodes=153)


def test_unknown_options_are_rejected(mini):
    with pytest.raises(ValueError):
        A.search(*mini, "x", "tight")
    with pytest.raises(ValueError):
        A.search(*mini, "ida", "x")
    with pytest.raises(ValueError):
        A.search(*mini, "ida", "tight", memo="x")
    with pytest.raises(ValueError):
        A.child_targets(((1,), ()), 0, 3, 2, "x")
