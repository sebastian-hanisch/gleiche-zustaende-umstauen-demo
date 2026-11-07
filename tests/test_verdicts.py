"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import gzu_algorithm as A
import gzu_constants as C
import gzu_evaluation as ev


def _res(nodes, opt=5, capped=False):
    return A.SearchResult(None if capped else opt, nodes, 1, capped, None if capped else opt, (), 0, 0)


def _analysis(tree, ida=11, canon=11, capped=False, canon_capped=False):
    results = {v: _res(50) for v in C.VARIANTS}
    results[C.VARIANTS[0]] = _res(ida, capped=capped)
    results[C.VARIANTS[3]] = _res(canon, capped=canon_capped)
    return ev.Analysis(((1,),), 4, 4, tree, results)


def test_bay_verdict_names_nodes_states_factor_symmetry_and_ida():
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(229, 114, 20, 18)))
    assert kind == "success"
    assert ("Der Baum der vollen Aufzählung hat 229 Knoten, aber nur 20 verschiedene Zustände (18 bis auf Vertauschen der Stapel): das 11-Fache an Wiederholung, "
            "davon die Stapelsymmetrie nur das 1,1-Fache. IDA* braucht 11 Knoten, mit Merken 11.") in text
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(2_703_457, 1_802_241, 1028, 619), ida=26, canon=26))
    assert kind == "success" and "2 703 457 Knoten" in text and "das 2 630-Fache an Wiederholung" in text


def test_bay_verdict_thresholds_at_two_and_ten():
    assert ev.verdict_bay(_analysis(A.TreeCount(100, 50, 10, 10)))[0] == "success"            # genau das Zehnfache zählt
    assert ev.verdict_bay(_analysis(A.TreeCount(99, 50, 10, 10)))[0] == "info"
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(20, 10, 10, 10)))
    assert kind == "info" and "das 2,0-Fache an Wiederholung" in text and not text.startswith("Die Bucht ist so klein")      # genau das Doppelte zählt als Wiederholung
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(19, 10, 10, 10)))
    assert kind == "info" and text.startswith("Die Bucht ist so klein, dass der Baum kaum Wiederholungen hat.") and "das 1,9-Fache" in text
    assert C.REP_STRONG == 10.0 and C.REP_WEAK == 2.0


def test_bay_verdict_when_the_tree_is_not_counted_and_when_ida_gives_up():
    kind, text = ev.verdict_bay(_analysis(None, ida=400_339, canon=8_975))
    assert kind == "warning" and "Mehr als 100 000 verschiedene Zustände: Der Baum der vollen Aufzählung wird hier nicht gezählt. IDA* braucht 400 339 Knoten, mit Merken 8 975." in text
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(229, 114, 20, 18), ida=500_000, canon=500_000, capped=True, canon_capped=True))
    assert "IDA* gibt bei 500 000 Knoten auf, mit und ohne Merken." in text
    kind, text = ev.verdict_bay(_analysis(A.TreeCount(229, 114, 20, 18), ida=500_000, canon=900, capped=True))
    assert "IDA* braucht mehr als 500 000 Knoten, mit Merken 900." in text


def test_result_rows_and_count_rows_by_hand():
    a = _analysis(A.TreeCount(229, 114, 20, 18))
    rows = ev.result_rows(a)
    assert [r["name"] for r in rows] == [C.VARIANT_NAMES[v] for v in C.VARIANTS] and [r["memo"] for r in rows] == [False, False, True, True, True, True, True]
    assert rows[0]["nodes_text"] == "11" and rows[0]["optimum"] == "5"
    capped = ev.result_rows(_analysis(None, capped=True))[0]
    assert capped["nodes_text"] == "mehr als 11" and capped["optimum"] == "nicht bewiesen" and capped["capped"]
    assert ev.count_rows(a) == [{"name": "Knoten des Baums", "value": 229}, {"name": "verschiedene Zustände", "value": 20}, {"name": "bis auf Stapelvertauschen", "value": 18}]
    assert ev.count_rows(_analysis(None)) == []


def _ratio(median, mean=None, mx=None, n=40, gain=0.5):
    return {"n": n, "median": median, "mean": median if mean is None else mean, "min": 1.0, "max": mx if mx is not None else median, "gain": gain}


def _tree(paths=100.0, sym=1.2, n=40):
    return {"n": n, "paths": _ratio(paths, mx=900.0, n=n), "sym": _ratio(sym, mx=2.5, n=n)}


def test_tree_verdict_three_states_and_numbers():
    kind, text = ev.verdict_tree(_tree(paths=505.17))
    assert kind == "success"
    assert ("Der Baum hat im Median das 505-Fache der Knoten gegenüber den verschiedenen Zuständen (Mehrfachwege, 40 Buchten, Maximum 900); "
            "die Stapelsymmetrie erklärt davon im Median nur das 1,20-Fache (Maximum 2,50). Der Baum besteht hier fast nur aus Wiederholungen.") in text
    assert ev.verdict_tree(_tree(paths=10.0))[0] == "success" and ev.verdict_tree(_tree(paths=9.99))[0] == "info"
    assert "Ein großer Teil des Baums sind Wiederholungen" in ev.verdict_tree(_tree(paths=2.0))[1]
    kind, text = ev.verdict_tree(_tree(paths=1.99))
    assert kind == "info" and "kaum Wiederholungen" in text
    assert ev.verdict_tree({"n": 0, "paths": _ratio(None, n=0), "sym": _ratio(None, n=0)})[0] == "warning"


def _ida(canon=_ratio(1.0, 1.0, 1.0, gain=0.0), sym=_ratio(1.0, 1.0, 1.0, gain=0.0)):
    return {"canon": canon, "sym": sym}


def test_ida_verdict_three_states_and_numbers():
    kind, text = ev.verdict_ida(_ida(_ratio(1.17, 4.32, 44.61, n=20, gain=0.7)))
    assert kind == "success"
    assert ("Das Merken spart IDA* im Median das 1,17-Fache der Knoten, im Mittel das 4,32-Fache, im Maximum das 45-Fache (20 Buchten, in 70 % mit Gewinn). "
            "Der Gewinn liegt im Schwanz: wenige schwere Buchten.") in text
    assert ev.verdict_ida(_ida(_ratio(1.0, 2.0, 5.0)))[0] == "success" and ev.verdict_ida(_ida(_ratio(1.0, 1.99, 5.0)))[0] == "info"       # genau das Doppelte im Mittel zählt
    assert "auch im Median spürbar" in ev.verdict_ida(_ida(_ratio(1.25, 1.5, 3.0)))[1] and "kaum etwas" in ev.verdict_ida(_ida(_ratio(1.24, 1.5, 3.0)))[1]
    assert ev.verdict_ida(_ida(_ratio(None, n=0)))[0] == "warning"
    assert C.MEMO_NOTICEABLE == 1.25 and C.MEMO_TAIL == 2.0


def test_symmetry_break_verdict_two_states_and_numbers():
    kind, text = ev.verdict_symmetry_break(_ida(sym=_ratio(1.0, 1.01, 1.3, n=40, gain=0.05)))
    assert kind == "info" and "spart im Median das 1,00-Fache, im Maximum das 1,30-Fache der Knoten (40 Buchten, in 5 % mit Gewinn)" in text and "Nur leere Stapel sind gleich" in text
    assert "auch im Median spürbar" in ev.verdict_symmetry_break(_ida(sym=_ratio(1.25, 1.3, 2.0)))[1]
    assert ev.verdict_symmetry_break(_ida(sym=_ratio(None, n=0)))[0] == "warning"


def _memo(bb=0.16, bblb=0.74, n=40):
    return {"r_bb+canon": _ratio(bb, n=n), "r_bblb+canon": _ratio(bblb, n=n)}


def test_replace_verdict_two_states_and_numbers():
    kind, text = ev.verdict_replace(_memo(bb=0.16, bblb=0.74))
    assert kind == "success"
    assert ("Branch and Bound ohne Untergrenze mit Merken braucht im Median das 6,2-Fache der Knoten von IDA* ohne Merken; Branch and Bound mit Untergrenze und Merken liegt bei "
            "1,35-fach (40 Buchten). Das Merken allein holt die Untergrenze nicht ein.") in text
    assert ev.verdict_replace(_memo(bb=1 / 1.5))[0] == "success" and ev.verdict_replace(_memo(bb=0.7))[0] == "info"      # genau das 1,5-Fache zählt
    assert "kommt hier an die Untergrenze heran" in ev.verdict_replace(_memo(bb=0.9))[1]
    assert ev.verdict_replace({"r_bb+canon": _ratio(None, n=0), "r_bblb+canon": _ratio(None, n=0)})[0] == "warning"
    assert C.REPLACE_STRONG == 1.5


def test_space_verdict_and_over_limit():
    kind, text = ev.verdict_space({"n": 5, "raw": {"ok": 5, "over": 0, "median": 1022, "mean": 1, "max": 331855}, "canon": {"ok": 5, "over": 0, "median": 567, "mean": 1, "max": 1}}, "5 × 3")
    assert kind == "info" and "5 × 3: Der Zustandsraum hat im Median 1 022 Zustände (567 bis auf Stapelvertauschen), im Maximum 331 855." in text
    kind, text = ev.verdict_space({"n": 5, "raw": {"ok": 4, "over": 1, "median": 380533.0, "mean": 1, "max": 627271}, "canon": {"ok": 4, "over": 1, "median": 302428.0, "mean": 1, "max": 1}}, "5 × 4")
    assert kind == "warning" and "im Median 380 533 Zustände (302 428 bis auf Stapelvertauschen)" in text and "Buchten über dem Limit: 1 von 5 (mehr als 3 000 000 Zustände), sie fehlen im Median." in text
    none = {"n": 5, "raw": {"ok": 0, "over": 5, "median": None, "mean": None, "max": None}, "canon": {"ok": 0, "over": 5, "median": None, "mean": None, "max": None}}
    assert ev.verdict_space(none, "x")[0] == "warning"


def test_num_f_by_hand():
    assert ev.num_f(5.0) == "5" and ev.num_f(71.5) == "71,5" and ev.num_f(525188.5) == "525 188,5" and ev.num_f(1234.0) == "1 234"
