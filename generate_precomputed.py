"""Erzeugt gzu_bands.json: Kennzahlen der festen Buchten (Seeds ab 0, Platz 2) für vier Auswertungen.

    python generate_precomputed.py

"baum":   je Zelle Knoten des Baums der vollen Aufzählung gegen verschiedene Zustände (gzu_constants.TREE_CELLS), gezählt statt durchlaufen.
"ida":    je Zelle IDA* in vier Fassungen (ohne, Symmetriebruch, Merken roh, Merken kanonisch; IDA_CELLS).
"merken": je Zelle Merken ohne Untergrenze: IDA* mit und ohne Merken, volle Aufzählung, Branch and Bound ohne und mit Untergrenze mit Merken (MEMO_CELLS).
"raum":   je Zelle Größe des ganzen Zustandsgraphen für wenige Buchten (SPACE_CELLS, Limit 3 Mio. Zustände).

Rechenzeit rund fünfzehn bis zwanzig Minuten (die Zellen laufen in getrennten Prozessen; 4 x 4 in "baum" und "raum" sind die teuren). Dieselben Funktionen wie die Tests
(`gzu_evaluation.tree_rows`, `ida_rows`, `memo_rows`, `space_rows` und die zugehörigen `*_stats`); die Datei speichert nur Kennzahlen, keine Zeilen.
tests/test_presets.py rechnet kleine Zellen neu und vergleicht."""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import gzu_constants as C
import gzu_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def job(kind, stacks, layers, n):
    seeds = range(n)
    if kind == "baum":
        return kind, stacks, layers, ev.tree_stats(ev.tree_rows(stacks, layers, C.DEFAULT_EXTRA, seeds))
    if kind == "ida":
        return kind, stacks, layers, ev.ida_stats(ev.ida_rows(stacks, layers, C.DEFAULT_EXTRA, seeds))
    if kind == "merken":
        return kind, stacks, layers, ev.memo_stats(ev.memo_rows(stacks, layers, C.DEFAULT_EXTRA, seeds))
    return kind, stacks, layers, ev.space_stats(ev.space_rows(stacks, layers, C.DEFAULT_EXTRA, seeds))


def main():
    tasks = ([("baum", *c) for c in C.TREE_CELLS] + [("ida", *c) for c in C.IDA_CELLS] + [("merken", *c) for c in C.MEMO_CELLS] + [("raum", *c) for c in C.SPACE_CELLS])
    tasks.sort(key=lambda t: -(t[1] * t[2] * (3 if t[0] in ("baum", "raum") else 1)))          # die teuren Zellen zuerst
    bands = {"baum": {}, "ida": {}, "merken": {}, "raum": {}}
    with ProcessPoolExecutor(max_workers=max(2, min(6, (os.cpu_count() or 2) - 1))) as pool:
        futures = [pool.submit(job, *t) for t in tasks]
        for f in as_completed(futures):
            kind, stacks, layers, stats = f.result()
            bands[kind][ev.cell_key(stacks, layers)] = stats
            print(f"{kind} {stacks} x {layers}: fertig", flush=True)
    ev.BANDS_FILE.write_text(json.dumps(bands, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("geschrieben:", ev.BANDS_FILE.name)


if __name__ == "__main__":
    main()
