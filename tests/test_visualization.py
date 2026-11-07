"""Abbildungen: Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Zahlen der Kurven."""

import gzu_algorithm as A
import gzu_constants as C
import gzu_evaluation as ev
import gzu_visualization as V


def _cell_colors(fig):
    out = {}
    for tr in fig.data:
        for txt, color in zip(tr.text, tr.marker.color):
            if txt:
                out[int(txt)] = color
    return out


def test_bay_colours_by_role(mini):
    bay, h = mini
    cols = _cell_colors(V.build_bay(bay, h, target=1))
    assert cols[1] == C.COLOR_TARGET and cols[4] == C.COLOR_BLOCK and cols[5] == cols[2] == cols[6] == cols[3] == C.COLOR_CELL
    assert sorted(_cell_colors(V.build_bay(bay, h))) == [1, 2, 3, 4, 5, 6] and len(V.build_bay(bay, h).data) == h


def test_blocker_cells_agree_with_the_kernel():
    from gzu_scenario import make_bay
    assert V.blocker_cells(((1, 4), (5, 2), (6, 3))) == {(0, 1)}
    for sd in range(20):
        bay = make_bay(4, 3, sd)
        assert len(V.blocker_cells(bay)) == A.blocker_count(bay)


def test_axes_are_locked_in_every_figure():
    a = ev.analyse(ev.Settings(3, 2, 2, C.MINI_SEED))
    bands = ev.load_bands()
    figs = [V.build_bay(a.bay, a.height), V.build_counts(ev.count_rows(a)), V.build_nodes(ev.result_rows(a)), V.build_tree_cells(bands["baum"]), V.build_gain(bands["ida"]),
            V.build_memo(bands["merken"]), V.build_space(bands["raum"])]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_counts_figure_has_three_log_bars_with_the_exact_numbers():
    fig = V.build_counts([{"name": "Knoten des Baums", "value": 2_703_457}, {"name": "verschiedene Zustände", "value": 1028}, {"name": "bis auf Stapelvertauschen", "value": 619}])
    assert fig.layout.yaxis.type == "log" and list(fig.data[0].y) == [2_703_457, 1028, 619] and list(fig.data[0].text) == ["2 703 457", "1 028", "619"]


def test_nodes_figure_marks_capped_runs_and_uses_a_log_axis():
    rows = [{"variant": C.VARIANTS[4], "nodes": 500_000, "capped": True, "nodes_text": "mehr als 500 000"}, {"variant": C.VARIANTS[3], "nodes": 8975, "capped": False, "nodes_text": "8 975"}]
    fig = V.build_nodes(rows)
    assert fig.layout.yaxis.type == "log" and list(fig.data[0].y) == [500_000, 8975] and list(fig.data[0].text) == ["mehr als 500 000", "8 975"]
    assert list(fig.data[0].marker.color) == [C.COLOR_CAPPED, C.COLOR_VARIANT[C.VARIANTS[3]]] and list(fig.data[0].x) == ["Aufzählung Merken", "IDA* Merken"]


def _stat(median):
    return {"median": median}


def test_tree_cells_figure_has_three_series_on_a_log_axis():
    cells = {"3 × 3": {"nodes": _stat(230), "raw": _stat(23.5), "canon": _stat(22)}}
    fig = V.build_tree_cells(cells)
    assert [t.name for t in fig.data] == ["Knoten des Baums", "verschiedene Zustände", "bis auf Stapelvertauschen"] and fig.layout.yaxis.type == "log"
    assert [t.y[0] for t in fig.data] == [230, 23.5, 22]


def test_gain_figure_skips_cells_without_a_comparison_and_has_median_mean_maximum():
    ok = {"canon": {"median": 1.17, "mean": 4.32, "max": 44.6}}
    none = {"canon": {"median": None, "mean": None, "max": None}}
    fig = V.build_gain({"5 × 4": ok, "x": none})
    assert [t.name for t in fig.data] == ["Median", "Mittel", "Maximum"] and list(fig.data[0].x) == ["5 × 4"] and fig.layout.yaxis.type == "log"
    assert [t.y[0] for t in fig.data] == [1.17, 4.32, 44.6]


def test_memo_figure_plots_the_inverse_ratios():
    cells = {"4 × 3": {"r_enum+canon": {"median": 0.05}, "r_bb+canon": {"median": 0.16}, "r_bblb+canon": {"median": 0.74}}}
    fig = V.build_memo(cells)
    assert len(fig.data) == 3 and fig.layout.yaxis.type == "log"
    assert [round(t.y[0], 2) for t in fig.data] == [20.0, 6.25, 1.35]


def test_space_figure_skips_cells_without_a_finished_run():
    cells = {"a": {"raw": {"median": 29}, "canon": {"median": 26}}, "b": {"raw": {"median": None}, "canon": {"median": None}}}
    fig = V.build_space(cells)
    assert [t.name for t in fig.data] == ["roh", "bis auf Stapelvertauschen"] and list(fig.data[0].x) == ["a"] and fig.layout.yaxis.type == "log"
