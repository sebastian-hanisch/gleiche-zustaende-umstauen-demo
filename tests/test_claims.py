"""JEDE Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über die vorberechneten Tabellen (gzu_bands.json, gegen eine frische Rechnung geprüft in
test_presets.py für die kleinen Zellen) und die Auswertungsfunktionen der App, über die festen Buchten je Zelle, nie über eine einzelne Bucht."""

import pytest

import gzu_constants as C
import gzu_evaluation as ev

BANDS = ev.load_bands()

# Tabelle A: Zelle -> (Buchten, Knoten (Median, Maximum), Zustände roh (Median, Maximum), bis auf Stapelvertauschen (Median), Knoten / Zustände (Median, Maximum), roh / kanonisch (Median, Maximum), über Limit)
BAUM = {
    (3, 2): (100, (9, 161), (4, 26), 4, (2.25, 6.19), (1.0, 1.62), 0),
    (4, 2): (100, (67, 20867), (8.5, 276), 7, (7.7, 79.65), (1.0, 3.73), 0),
    (3, 3): (100, (230, 13427), (23.5, 456), 22, (10.03, 49.54), (1.08, 1.7), 0),
    (5, 2): (60, (1785, 2255473), (24.5, 613), 17, (76.57, 3679.4), (1.2, 5.47), 0),
    (4, 3): (40, (39413.5, 158791356), (87.5, 12628), 65.5, (505.17, 22103.79), (1.18, 5.0), 0),
    (3, 4): (40, (18163.5, 696375), (175, 3112), 135, (89.76, 465.98), (1.12, 2.28), 0),
    (5, 3): (20, (159754794, 21722640688069), (665, 331855), 462, (185825.53, 117593697.64), (1.33, 9.91), 0),
    (4, 4): (30, (1930893700, 21298033897566), (1948, 289675), 1590, (521891.88, 87580805.32), (1.17, 2.99), 1),
}

# Tabelle B: Zelle -> (Basis (Median, Mittel, Maximum), Basis / Symmetriebruch (Median, Mittel, Maximum, Anteil mit Gewinn), Basis / Merken (Median, Mittel, Maximum, Anteil mit Gewinn),
#                      Treffer-Anteil (Median, Prozent), größte Tabelle (Median, Maximum))
IDA = {
    (3, 2): ((3, 4, 15), (1.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 0.0), 0.0, (2, 7)),
    (4, 2): ((3, 4, 10), (1.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 0.0), 0.0, (2, 5)),
    (3, 3): ((16, 25, 144), (1.0, 1.0, 1.1, 0.01), (1.0, 1.07, 1.75, 0.3), 0.0, (5, 40)),
    (5, 2): ((4, 6, 12), (1.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 0.0), 0.0, (3, 6)),
    (4, 3): ((12, 33, 360), (1.0, 1.0, 1.0, 0.0), (1.0, 1.05, 1.57, 0.2), 0.0, (5, 57)),
    (3, 4): ((65, 121, 672), (1.0, 1.01, 1.3, 0.05), (1.17, 1.23, 1.97, 0.75), 4.4, (16, 117)),
    (5, 3): ((18.5, 33, 218), (1.0, 1.0, 1.0, 0.0), (1.0, 1.02, 1.28, 0.1), 0.0, (6.5, 35)),
    (4, 4): ((291, 1106, 11739), (1.0, 1.0, 1.02, 0.03), (1.33, 1.5, 3.69, 0.73), 4.4, (43.5, 1656)),
    (5, 4): ((521.5, 50391, 487765), (1.0, 1.01, 1.12, 0.15), (1.17, 4.32, 44.61, 0.7), 1.9, (77, 10395)),
}

# Tabelle C1: Zelle -> (Buchten, Median je Verfahren: enum+canon, bb+canon, bblb+canon, ida, ida+canon, über Limit der Aufzählung, IDA* / bb+canon, IDA* / bblb+canon, größte Tabelle der Aufzählung (Median, Maximum))
MERKEN = {
    (3, 3): (100, (43, 26, 13, 16, 16), 0, 0.60, 1.17, (21, 374)),
    (4, 3): (40, (195.5, 81.5, 16, 12, 12), 0, 0.16, 0.74, (64.5, 3526)),
    (3, 4): (40, (293, 120, 38.5, 65, 53), 0, 0.50, 1.75, (134, 2840)),
    (5, 3): (20, (2047, 539, 31, 18.5, 18.5), 0, 0.04, 0.56, (461, 49714)),
    (4, 4): (30, (5731, 2188, 202.5, 291, 188), 1, 0.07, 1.39, (1589, 230570)),
}

# Tabelle C2: Zelle -> (Buchten, roh (Median, Maximum), kanonisch (Median), über Limit)
RAUM = {(3, 3): (5, (29, 111), 26, 0), (4, 3): (5, (133, 12628), 76, 0), (5, 3): (5, (1022, 331855), 567, 0), (6, 3): (5, (2148, 555370), 1383, 0),
        (4, 4): (5, (2108, 12414), 1457, 1), (5, 4): (5, (380533, 627271), 302428, 1)}


@pytest.mark.parametrize("cell", list(BAUM))
def test_readme_tree_cell(cell):
    n, nodes, raw, canon, paths, sym, over = BAUM[cell]
    st = BANDS["baum"][ev.cell_key(*cell)]
    assert st["n"] == n and (st["nodes"]["median"], st["nodes"]["max"]) == nodes and (st["raw"]["median"], st["raw"]["max"]) == raw and st["canon"]["median"] == canon
    assert (round(st["paths"]["median"], 2), round(st["paths"]["max"], 2)) == paths and (round(st["sym"]["median"], 2), round(st["sym"]["max"], 2)) == sym
    assert st["nodes"]["over"] == over and st["paths"]["n"] == n - over


@pytest.mark.parametrize("cell", list(IDA))
def test_readme_ida_cell(cell):
    base, sym, canon, hits, table = IDA[cell]
    st = BANDS["ida"][ev.cell_key(*cell)]
    b = st["variants"]["base"]
    assert (b["median"], round(b["mean"]), b["max"], b["over"]) == base + (0,)
    for key, want in (("sym", sym), ("canon", canon)):
        r = st[key]
        assert (round(r["median"], 2), round(r["mean"], 2), round(r["max"], 2), round(r["gain"], 2)) == want, key
    assert round(st["hits"] * 100, 1) == hits and (st["table"]["median"], st["table"]["max"]) == table
    assert all(st["variants"][k]["over"] == 0 for k in st["variants"])


@pytest.mark.parametrize("cell", list(MERKEN))
def test_readme_memo_cell(cell):
    n, medians, over, bb, bblb, table = MERKEN[cell]
    st = BANDS["merken"][ev.cell_key(*cell)]
    assert st["n"] == n
    for key, want in zip(("enum+canon", "bb+canon", "bblb+canon", "ida", "ida+canon"), medians):
        assert st["variants"][key]["median"] == want, key
    assert st["variants"]["enum+canon"]["over"] == over and round(st["r_bb+canon"]["median"], 2) == bb and round(st["r_bblb+canon"]["median"], 2) == bblb
    assert (st["table"]["median"], st["table"]["max"]) == table


@pytest.mark.parametrize("cell", list(RAUM))
def test_readme_space_cell(cell):
    n, raw, canon, over = RAUM[cell]
    st = BANDS["raum"][ev.cell_key(*cell)]
    assert st["n"] == n and (st["raw"]["median"], st["raw"]["max"]) == raw and st["canon"]["median"] == canon and st["raw"]["over"] == over


def test_the_repetition_grows_with_the_size_and_the_symmetry_stays_small():
    paths = [BAUM[c][4][0] for c in ((3, 2), (4, 2), (3, 3), (5, 2), (4, 3), (5, 3), (4, 4))]
    assert paths == sorted(paths) and min(paths) == 2.25 and max(paths) > 500_000                       # die Wiederholung wächst mit der Größe (bis auf 3 x 4 bei 4 Lagen)
    assert max(v[5][0] for v in BAUM.values()) == 1.33 and min(v[5][0] for v in BAUM.values()) == 1.0
    assert all(v[4][0] >= C.REP_WEAK for v in BAUM.values()) and sum(v[4][0] >= C.REP_STRONG for v in BAUM.values()) == 6


def test_the_memo_for_ida_has_a_median_of_at_most_1_33_and_a_big_tail():
    meds = [v[2][0] for v in IDA.values()]
    assert max(meds) == 1.33 and sorted(meds)[:6] == [1.0] * 6
    assert max(v[2][1] for v in IDA.values()) == 4.32 and max(v[2][2] for v in IDA.values()) == 44.61
    assert [c for c, v in IDA.items() if v[2][1] >= C.MEMO_TAIL] == [(5, 4)] and [c for c, v in IDA.items() if v[2][0] >= C.MEMO_NOTICEABLE] == [(4, 4)]
    assert max(v[1][0] for v in IDA.values()) == 1.0 and max(v[1][2] for v in IDA.values()) == 1.3        # Symmetriebruch: Median nie über 1,00, Maximum bis 1,30


def test_the_untergrenze_and_the_memo_replace_each_other():
    assert all(1 / v[3] >= C.REPLACE_STRONG for v in MERKEN.values()) and round(1 / 0.60, 1) == 1.7 and round(1 / 0.04) == 25
    assert min(v[4] for v in MERKEN.values()) == 0.56 and max(v[4] for v in MERKEN.values()) == 1.75
    assert round(MERKEN[(3, 3)][1][0] / MERKEN[(3, 3)][1][1], 1) == 1.7                # volle Aufzählung mit Merken 43 gegen B&B ohne Untergrenze mit Merken 26 in 3 x 3


def test_the_tail_of_the_biggest_cell_and_the_space_jump():
    v = BANDS["ida"]["5,4"]["variants"]["base"]
    assert (v["median"], round(v["mean"]), v["max"]) == (521.5, 50391, 487765) and round(v["mean"] / v["median"]) == 97
    assert round(RAUM[(5, 4)][1][0] / RAUM[(4, 4)][1][0]) == 181 and RAUM[(5, 4)][3] == RAUM[(4, 4)][3] == 1


def test_the_table_cells_and_the_documented_cells_agree():
    assert [(s, l, n) for s, l, n in C.TREE_CELLS] == [(s, l, BAUM[(s, l)][0]) for s, l, _ in C.TREE_CELLS]
    assert {(s, l) for s, l, _ in C.IDA_CELLS} == set(IDA) and {(s, l) for s, l, _ in C.MEMO_CELLS} == set(MERKEN) and {(s, l) for s, l, _ in C.SPACE_CELLS} == set(RAUM)


def test_raw_and_canonical_memo_differ_in_the_median_only_at_5x4():
    diff = [c for c in IDA if BANDS["ida"][ev.cell_key(*c)]["variants"]["raw"]["median"] != BANDS["ida"][ev.cell_key(*c)]["variants"]["canon"]["median"]]
    assert diff == [(5, 4)]
    v = BANDS["ida"]["5,4"]["variants"]
    assert (v["raw"]["median"], v["canon"]["median"]) == (434, 415) and round(BANDS["ida"]["5,4"]["raw"]["median"], 2) == 1.15
