"""Inhalt der App: Kennzahlen der Presets, Tabelle der Verfahren, Zustände der Mini-Bucht, Verdikte, Permalink (AppTest, DEMO-PLAYBOOK §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import gzu_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(at=None):
    if at is None:                                              # nicht `at or ...`: ein ungelaufener AppTest ist falsy
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def _deltas(at):
    return {m.label: m.delta for m in at.metric}


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(md.value for md in at.markdown)


def _bodies(at):
    return " ".join(e.value for kind in (at.success, at.info, at.warning) for e in kind)


TREE, STATES, IDA, OPT = "Knoten des Baums (volle Aufzählung)", "Verschiedene Zustände", "IDA* ohne / mit Merken (Knoten)", "Optimum"


def test_default_bay_shows_tree_states_and_the_seven_methods():
    at = _run()
    m = _metrics(at)
    assert m[TREE] == "229" and m[STATES] == "20" and m[IDA] == "11 / 11" and m[OPT] == "5"
    assert _deltas(at)[STATES] == "18 bis auf Stapelvertauschen" and _deltas(at)[OPT] == "Untergrenze 4, Bucht 3 × 3"
    text = _texts(at)
    assert "| IDA* (Stück 5) | 11 |  |  | 5 |" in text and "| IDA* mit Symmetriebruch | 11 |  |  | 5 |" in text
    assert "| IDA* mit Merken (roh) | 11 | 0 | 5 | 5 |" in text and "| IDA* mit Merken (bis auf Stapelvertauschen) | 11 | 0 | 5 | 5 |" in text
    assert "| Volle Aufzählung mit Merken | 34 | 11 | 17 | 5 |" in text and "| Branch and Bound ohne Untergrenze mit Merken | 22 | 2 | 11 | 5 |" in text
    assert "| Branch and Bound mit Untergrenze mit Merken | 11 | 0 | 5 | 5 |" in text
    assert any("das 11-Fache an Wiederholung, davon die Stapelsymmetrie nur das 1,1-Fache" in s.value for s in at.success)


def test_mini_preset_shows_nine_nodes_four_states_and_the_state_visited_twice():
    at = _preset(_run(), "Die Mini-Bucht")
    m = _metrics(at)
    assert m[TREE] == "9" and m[STATES] == "4" and m[IDA] == "6 / 6"
    text = _texts(at)
    assert "| () | (5) | (6, 3, 4) | 2 | 1 |" in text and "| () | () | () (leer) | 5 | 2 |" in text and "| (1, 4) | (5, 2) | (6, 3) | 1 | 0 |" in text
    assert any("9 Knoten, aber nur 4 verschiedene Zustände. Der Zustand () | (5) | (6, 3, 4) wird zweimal erreicht" in s.value for s in at.success)
    assert "| Volle Aufzählung mit Merken | 7 | 1 | 3 | 2 |" in text


def test_repeat_preset_counts_a_tree_of_millions_without_walking_it():
    at = _preset(_run(), "Fast nur Wiederholung (4 Stapel, 3 Lagen)")
    m = _metrics(at)
    assert m[TREE] == "2 703 457" and m[STATES] == "1 028" and m[IDA] == "26 / 26" and _deltas(at)[STATES] == "619 bis auf Stapelvertauschen"
    assert any("das 2 630-Fache an Wiederholung" in s.value for s in at.success)


def test_tail_preset_does_not_count_the_tree_and_shows_the_memo_gain():
    at = _preset(_run(), "Wo das Merken hilft (5 Stapel, 4 Lagen)")
    m = _metrics(at)
    assert m[TREE] == "nicht gezählt" and m[STATES] == "–" and m[IDA] == "400 339 / 8 975" and m[OPT] == "15"
    text = _texts(at)
    assert "| IDA* mit Merken (bis auf Stapelvertauschen) | 8 975 | 1 429 | 1 411 | 15 |" in text and "| Volle Aufzählung mit Merken | mehr als 500 000 |" in text
    assert any("Mehr als 100 000 verschiedene Zustände: Der Baum der vollen Aufzählung wird hier nicht gezählt. IDA* braucht 400 339 Knoten, mit Merken 8 975." in w.value for w in at.warning)


def test_the_counterexample_is_counted_for_every_setting():
    text = _texts(_run())
    assert "der Baum hat **153 Knoten**, aber nur **25 verschiedene Zustände** (16 bis auf Stapelvertauschen)" in text
    assert "IDA\\* braucht 15 Knoten, mit Merken 15 (größte Tabelle 7)." in text


def test_the_tables_and_the_verdicts_name_the_numbers_of_the_default_cell():
    at = _run()
    text = _texts(at)
    assert "| 3 × 3 (100) | 230 / 13 427 | 23,5 / 456 | 22 / 375 | 10 (50) | 1,08 (1,70) |" in text
    assert "| 4 × 4 (30) | 1 930 893 700 / 21 298 033 897 566, 1 über dem Limit | 1 948 / 289 675 | 1 590 / 230 571 | 521 892 (87 580 805) | 1,17 (2,99) |" in text
    assert "| 3 × 3 (100) | 16 / 25 / 144 | 16 / 25 / 144 | 16 / 22 / 123 | 16 / 22 / 123 |" in text
    assert "| 5 × 4 | 1,00, 1,01, 1,1, 15 % | 1,17, 4,32, 45, 70 % | 1,9 % | 77, 10 395 |" in text and "| 3 × 4 | 1,00, 1,01, 1,3, 5 % | 1,17, 1,23, 2,0, 75 % | 4,4 % | 16, 117 |" in text
    assert "| 4 × 4 (30) | 5 731 / 151 941 / 895 575, 1 über Limit | 2 188 / 23 681 / 268 702 | 202,5 / 585 / 5 489 | 291 / 1 106 / 11 739 | 188 / 655 / 7 168 |" in text
    assert "| 5 × 4 (5) | 380 533 / 627 271 | 302 428 | 1 |" in text
    bodies = _bodies(at)
    assert "Der Baum hat im Median das 10-Fache der Knoten gegenüber den verschiedenen Zuständen (Mehrfachwege, 100 Buchten, Maximum 50)" in bodies
    assert "Das Merken spart IDA* im Median das 1,00-Fache der Knoten, im Mittel das 1,07-Fache, im Maximum das 1,8-Fache (100 Buchten, in 30 % mit Gewinn)" in bodies
    assert "Der Symmetriebruch spart im Median das 1,00-Fache, im Maximum das 1,10-Fache der Knoten (100 Buchten, in 1 % mit Gewinn)" in bodies
    assert "Branch and Bound ohne Untergrenze mit Merken braucht im Median das 1,7-Fache der Knoten von IDA* ohne Merken" in bodies
    assert "5 × 4: Der Zustandsraum hat im Median 380 533 Zustände (302 428 bis auf Stapelvertauschen), im Maximum 627 271." in bodies


def test_a_cell_without_the_old_methods_says_so_and_the_space_note_appears_for_other_space():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params.update({"stacks": "5", "layers": "4", "extra": "1", "seed": "2"})
    _run(at)
    text = _texts(at)
    assert "**Zelle 5 × 4 (Ihre Einstellung)**, Tabellen gelten für Platz 2, hier ist Platz 1 eingestellt:" in text
    assert any("wurde der Baum nicht gezählt (zu viele Zustände)" in i.value for i in at.info) and any("wurde Merken ohne Untergrenze nicht gerechnet" in i.value for i in at.info)
    assert "**Zelle 3 × 3 (Ihre Einstellung)**:" in _texts(_run())


def test_every_combination_of_the_stack_and_layer_sliders_has_an_ida_cell():
    assert {(s, l) for s, l, _ in C.IDA_CELLS} == {(s, l) for s in range(C.STACKS_MIN, C.STACKS_MAX + 1) for l in range(C.LAYERS_MIN, C.LAYERS_MAX + 1)}


def test_permalink_is_clamped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["stacks"] = "99"
    at.query_params["layers"] = "-4"
    at.query_params["extra"] = "17"
    _run(at)
    assert at.sidebar.slider(key="stacks_slider").value == C.STACKS_MAX
    assert at.sidebar.slider(key="layers_slider").value == C.LAYERS_MIN
    assert at.sidebar.slider(key="extra_slider").value == C.EXTRA_MAX
