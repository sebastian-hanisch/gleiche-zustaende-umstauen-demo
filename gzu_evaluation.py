"""Kennzahlen, Verdikt-Logik, vorberechnete Tabellen. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import gzu_algorithm as A
import gzu_constants as C
from gzu_scenario import make_bay, max_height

BANDS_FILE = Path(__file__).resolve().parent / "gzu_bands.json"

IDA, IDA_SYM, IDA_RAW, IDA_CANON = C.VARIANTS[0], C.VARIANTS[1], C.VARIANTS[2], C.VARIANTS[3]
ENUM_M, BB_M, BBLB_M = C.VARIANTS[4], C.VARIANTS[5], C.VARIANTS[6]
# Verfahren der Zeilen in den Tabellen B und C1: Schlüssel -> (Verfahren, Merken, Symmetriebruch)
IDA_ROWS = {"base": ("ida", None, False), "sym": ("ida", None, True), "raw": ("ida", "raw", False), "canon": ("ida", "canon", False)}
MEMO_ROWS = {"ida": ("ida", None, False), "ida+canon": ("ida", "canon", False), "enum+canon": ("enum", "canon", False),
             "bb+canon": ("bb", "canon", False), "bblb+canon": ("bblb", "canon", False)}


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    layers: int = C.DEFAULT_LAYERS
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.EVERYDAY_SEED


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    lower: int                      # Untergrenze: blockierende Container (Stück 2)
    tree: A.TreeCount | None        # Baum der vollen Aufzählung, gezählt (None: mehr als LIVE_STATE_CAP Zustände)
    results: dict                   # (Verfahren, Merken, Symmetriebruch) -> SearchResult

    def res(self, variant) -> A.SearchResult:
        return self.results[variant]

    @property
    def optimum(self):
        """Das Optimum, sobald ein Verfahren es bewiesen hat (alle, die fertig werden, liefern dasselbe); sonst None."""
        found = {r.optimum for r in self.results.values() if not r.capped}
        assert len(found) <= 1, found
        return found.pop() if found else None


def analyse(settings: Settings, cap: int = C.LIVE_CAP, state_cap: int = C.LIVE_STATE_CAP) -> Analysis:
    bay = make_bay(settings.stacks, settings.layers, settings.seed)
    height = max_height(settings.layers, settings.extra)
    results = {v: A.search(bay, height, v[0], "tight", cap, memo=v[1], sym=v[2]) for v in C.VARIANTS}
    return Analysis(bay, height, A.blocker_count(bay), A.count_tree(bay, height, state_cap), results)


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def num_f(x: float) -> str:
    """Zahl mit Leerzeichen als Tausendertrenner; hat sie einen Nachkommaanteil (Median einer geraden Zahl von Läufen), mit einer Nachkommastelle und Komma."""
    if float(x).is_integer():
        return num(int(x))
    whole, frac = f"{x:.1f}".split(".")
    return f"{num(int(whole))},{frac}"


def nodes_text(r: A.SearchResult) -> str:
    return f"mehr als {num(r.nodes)}" if r.capped else num(r.nodes)


def factor_text(x: float) -> str:
    """Verhältnis mit einer Nachkommastelle unter 10, sonst ganzzahlig gerundet (mit Tausendertrenner)."""
    return f"{x:.1f}".replace(".", ",") if x < 10 else num(round(x))


def ratio_text(x: float) -> str:
    """Verhältnis mit zwei Nachkommastellen (Tabellen)."""
    return f"{x:.2f}".replace(".", ",")


# ---------------------------------------------------------------- Verdikt einer Bucht

def verdict_bay(a: Analysis, cap: int = C.LIVE_CAP, state_cap: int = C.LIVE_STATE_CAP) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viele Knoten des Baums sind Wiederholungen, und woher kommen sie (Mehrfachwege oder Stapelsymmetrie)?"""
    ida, canon = a.res(IDA), a.res(IDA_CANON)
    ida_text = (f" IDA* braucht {nodes_text(ida)} Knoten, mit Merken {nodes_text(canon)}." if not (ida.capped and canon.capped)
                else f" IDA* gibt bei {num(cap)} Knoten auf, mit und ohne Merken.")
    if a.tree is None:
        return "warning", (f"Mehr als {num(state_cap)} verschiedene Zustände: Der Baum der vollen Aufzählung wird hier nicht gezählt." + ida_text)
    t = a.tree
    rep, sym = t.nodes / t.raw, t.raw / t.canon
    text = (f"Der Baum der vollen Aufzählung hat {num(t.nodes)} Knoten, aber nur {num(t.raw)} verschiedene Zustände ({num(t.canon)} bis auf Vertauschen der Stapel): "
            f"das {factor_text(rep)}-Fache an Wiederholung, davon die Stapelsymmetrie nur das {factor_text(sym)}-Fache.")
    if rep >= C.REP_STRONG:
        return "success", text + ida_text
    if rep >= C.REP_WEAK:
        return "info", text + ida_text
    return "info", "Die Bucht ist so klein, dass der Baum kaum Wiederholungen hat. " + text + ida_text


def result_rows(a: Analysis) -> list[dict]:
    """Eine Zeile je Verfahren: Name, Knoten (Text), Treffer des Merkens, größte Tabelle, Optimum (oder „nicht bewiesen“)."""
    rows = []
    for v in C.VARIANTS:
        r = a.res(v)
        rows.append({"variant": v, "name": C.VARIANT_NAMES[v], "nodes": r.nodes, "capped": r.capped, "nodes_text": nodes_text(r),
                     "hits": r.hits, "table": r.table, "memo": v[1] is not None, "optimum": "nicht bewiesen" if r.capped else str(r.optimum)})
    return rows


def count_rows(a: Analysis) -> list[dict]:
    """Die Zählung des Baums als Balken: Knoten des Baums, verschiedene Zustände roh, bis auf Stapelvertauschen (leer, wenn der Baum nicht gezählt wurde)."""
    if a.tree is None:
        return []
    t = a.tree
    return [{"name": "Knoten des Baums", "value": t.nodes}, {"name": "verschiedene Zustände", "value": t.raw}, {"name": "bis auf Stapelvertauschen", "value": t.canon}]


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def _stat(xs):
    ok = [x for x in xs if x is not None]
    if not ok:
        return {"ok": 0, "over": len(xs), "median": None, "mean": None, "max": None}
    return {"ok": len(ok), "over": len(xs) - len(ok), "median": median(ok), "mean": mean(ok), "max": max(ok)}


def _ratio_stat(xs):
    if not xs:
        return {"n": 0, "median": None, "mean": None, "min": None, "max": None, "gain": None}
    return {"n": len(xs), "median": median(xs), "mean": mean(xs), "min": min(xs), "max": max(xs), "gain": sum(x > 1 for x in xs) / len(xs)}


def tree_rows(stacks: int, layers: int, extra: int, seeds, state_cap: int = C.BAND_STATE_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Knoten des Baums, verschiedene Zustände roh und kanonisch (None, wenn mehr als `state_cap` Zustände)."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        t = A.count_tree(make_bay(stacks, layers, sd), height, state_cap)
        rows.append({"seed": sd, "nodes": None if t is None else t.nodes, "raw": None if t is None else t.raw, "canon": None if t is None else t.canon})
    return rows


def tree_stats(rows: list[dict]) -> dict:
    """Kennzahlen: Knoten, Zustände roh und kanonisch (Median, Mittel, Maximum) und die Verhältnisse Knoten / roh (Mehrfachwege) und roh / kanonisch (Stapelsymmetrie)."""
    ok = [r for r in rows if r["nodes"] is not None]
    return {"n": len(rows), "nodes": _stat([r["nodes"] for r in rows]), "raw": _stat([r["raw"] for r in rows]), "canon": _stat([r["canon"] for r in rows]),
            "paths": _ratio_stat([r["nodes"] / r["raw"] for r in ok]), "sym": _ratio_stat([r["raw"] / r["canon"] for r in ok])}


def ida_rows(stacks: int, layers: int, extra: int, seeds, cap: int = C.BAND_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Knoten von IDA* in den vier Fassungen (None = über Limit), Treffer-Anteil und größte Tabelle des Merkens (kanonisch)."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        row = {"seed": sd, "hits": None, "table": None}
        for key, (mode, memo, sym) in IDA_ROWS.items():
            r = A.search(bay, height, mode, "tight", cap, memo=memo, sym=sym)
            row[key] = None if r.capped else r.nodes
            if key == "canon" and not r.capped:
                row["hits"], row["table"] = r.hits / r.nodes, r.table
        rows.append(row)
    return rows


def ida_stats(rows: list[dict]) -> dict:
    """Kennzahlen: Knoten je Fassung (Median, Mittel, Maximum) und die Verhältnisse Basis / Fassung je Bucht (Median, Mittel, Maximum, Anteil der Buchten mit Gewinn),
    Treffer-Anteil (Median) und größte Tabelle (Median, Maximum)."""
    out = {"n": len(rows), "variants": {k: _stat([r[k] for r in rows]) for k in IDA_ROWS}}
    for key in ("sym", "raw", "canon"):
        out[key] = _ratio_stat([r["base"] / r[key] for r in rows if r["base"] is not None and r[key] is not None])
    hits = [r["hits"] for r in rows if r["hits"] is not None]
    tabs = [r["table"] for r in rows if r["table"] is not None]
    out["hits"] = median(hits) if hits else None
    out["table"] = {"median": median(tabs) if tabs else None, "max": max(tabs) if tabs else None}
    return out


def memo_rows(stacks: int, layers: int, extra: int, seeds, cap: int = C.BAND_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Knoten von IDA* ohne und mit Merken und der Tiefensuchen mit Merken (None = über Limit), größte Tabelle der Aufzählung mit Merken."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        row = {"seed": sd, "table": None}
        for key, (mode, memo, sym) in MEMO_ROWS.items():
            r = A.search(bay, height, mode, "tight", cap, memo=memo, sym=sym)
            row[key] = None if r.capped else r.nodes
            if key == "enum+canon" and not r.capped:
                row["table"] = r.table
        rows.append(row)
    return rows


def memo_stats(rows: list[dict]) -> dict:
    """Kennzahlen: Knoten je Verfahren und die Verhältnisse IDA* (ohne Merken) / Verfahren je Bucht (Median, Minimum, Maximum), größte Tabelle der Aufzählung (Median, Maximum)."""
    out = {"n": len(rows), "variants": {k: _stat([r[k] for r in rows]) for k in MEMO_ROWS}}
    for key in ("ida+canon", "enum+canon", "bb+canon", "bblb+canon"):
        out["r_" + key] = _ratio_stat([r["ida"] / r[key] for r in rows if r["ida"] is not None and r[key]])
    tabs = [r["table"] for r in rows if r["table"] is not None]
    out["table"] = {"median": median(tabs) if tabs else None, "max": max(tabs) if tabs else None}
    return out


def space_rows(stacks: int, layers: int, extra: int, seeds, cap: int = C.BAND_STATE_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: verschiedene Zustände roh und kanonisch des ganzen Zustandsgraphen (None, wenn mehr als `cap`)."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        r = A.count_states(make_bay(stacks, layers, sd), height, cap)
        rows.append({"seed": sd, "raw": None if r is None else r[0], "canon": None if r is None else r[1]})
    return rows


def space_stats(rows: list[dict]) -> dict:
    return {"n": len(rows), "raw": _stat([r["raw"] for r in rows]), "canon": _stat([r["canon"] for r in rows])}


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"baum": {"s,l": ...}, "ida": {...}, "merken": {...}, "raum": {...}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


def cell_key(stacks: int, layers: int) -> str:
    return f"{stacks},{layers}"


# ---------------------------------------------------------------- Verdikte der Tabellen

def verdict_tree(stats: dict) -> tuple[str, str]:
    """Verdikt „wie viele Zustände sind gleich?“ nach dem Median des Verhältnisses Knoten / verschiedene Zustände, mit der Aufspaltung in Mehrfachwege und Stapelsymmetrie."""
    p, s = stats["paths"], stats["sym"]
    if p["median"] is None:
        return "warning", "In dieser Zelle wurde kein Baum gezählt."
    text = (f"Der Baum hat im Median das {factor_text(p['median'])}-Fache der Knoten gegenüber den verschiedenen Zuständen (Mehrfachwege, {p['n']} Buchten, Maximum {factor_text(p['max'])}); "
            f"die Stapelsymmetrie erklärt davon im Median nur das {ratio_text(s['median'])}-Fache (Maximum {ratio_text(s['max'])}).")
    if p["median"] >= C.REP_STRONG:
        return "success", text + " Der Baum besteht hier fast nur aus Wiederholungen."
    if p["median"] >= C.REP_WEAK:
        return "info", text + " Ein großer Teil des Baums sind Wiederholungen."
    return "info", text + " Die Bucht ist so klein, dass es kaum Wiederholungen gibt."


def verdict_ida(stats: dict) -> tuple[str, str]:
    """Verdikt „was bringt das Merken für IDA*?“: Median, Mittel und Maximum des Verhältnisses Basis / Merken (kanonisch) in drei Zuständen."""
    c = stats["canon"]
    if c["median"] is None:
        return "warning", "In dieser Zelle liegt kein vollständiger Vergleich von IDA* mit und ohne Merken vor."
    text = (f"Das Merken spart IDA* im Median das {ratio_text(c['median'])}-Fache der Knoten, im Mittel das {ratio_text(c['mean'])}-Fache, im Maximum das {factor_text(c['max'])}-Fache "
            f"({c['n']} Buchten, in {c['gain'] * 100:.0f} % mit Gewinn).")
    if c["mean"] >= C.MEMO_TAIL:
        return "success", text + " Der Gewinn liegt im Schwanz: wenige schwere Buchten."
    if c["median"] >= C.MEMO_NOTICEABLE:
        return "info", text + " Das Merken ist hier auch im Median spürbar."
    return "info", text + " Das Merken bringt hier kaum etwas: Die Untergrenze hat die Wiederholungen schon beseitigt."


def verdict_symmetry_break(stats: dict) -> tuple[str, str]:
    """Verdikt „was bringt der Symmetriebruch (leere Stapel)?“: Median und Maximum des Verhältnisses Basis / Symmetriebruch."""
    s = stats["sym"]
    if s["median"] is None:
        return "warning", "In dieser Zelle liegt kein vollständiger Vergleich vor."
    text = (f"Der Symmetriebruch spart im Median das {ratio_text(s['median'])}-Fache, im Maximum das {ratio_text(s['max'])}-Fache der Knoten ({s['n']} Buchten, in {s['gain'] * 100:.0f} % mit Gewinn).")
    if s["median"] >= C.MEMO_NOTICEABLE:
        return "info", text + " Er ist hier auch im Median spürbar."
    return "info", text + " Er bringt hier im Median nichts: Nur leere Stapel sind gleich."


def verdict_replace(stats: dict) -> tuple[str, str]:
    """Verdikt „ersetzt das Merken die Untergrenze?“: Median des Verhältnisses IDA* / Branch and Bound ohne Untergrenze mit Merken (kleiner als 1: IDA* braucht weniger)."""
    r, b = stats["r_bb+canon"], stats["r_bblb+canon"]
    if r["median"] is None or b["median"] is None:
        return "warning", "In dieser Zelle liegt kein vollständiger Vergleich vor."
    text = (f"Branch and Bound ohne Untergrenze mit Merken braucht im Median das {factor_text(1 / r['median'])}-Fache der Knoten von IDA* ohne Merken; "
            f"Branch and Bound mit Untergrenze und Merken liegt bei {ratio_text(1 / b['median'])}-fach ({r['n']} Buchten).")
    if 1 / r["median"] >= C.REPLACE_STRONG:
        return "success", text + " Das Merken allein holt die Untergrenze nicht ein."
    return "info", text + " Das Merken allein kommt hier an die Untergrenze heran."


def verdict_space(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wie groß ist der Zustandsraum?“: Median der verschiedenen Zustände einer Zelle, mit Zahl der Läufe über dem Limit."""
    r, c = stats["raw"], stats["canon"]
    if r["median"] is None:
        return "warning", f"{name}: Alle {r['over']} Buchten haben mehr als {num(C.BAND_STATE_CAP)} Zustände."
    over = f" Buchten über dem Limit: {r['over']} von {stats['n']} (mehr als {num(C.BAND_STATE_CAP)} Zustände), sie fehlen im Median." if r["over"] else ""
    text = f"{name}: Der Zustandsraum hat im Median {num_f(r['median'])} Zustände ({num_f(c['median'])} bis auf Stapelvertauschen), im Maximum {num(r['max'])}." + over
    return ("warning" if r["over"] else "info"), text
