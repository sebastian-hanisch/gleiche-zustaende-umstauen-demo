"""Kern: Zustandsmerken und Symmetriebruch beim Umstauen (restricted), mit Knotenzählung. Aufbauend auf Stück 2 (Untergrenze), Stück 4 (Suchbaum) und Stück 5 (IDA*).

Eine Bucht besteht aus Stapeln (Tupel von unten nach oben). Die Abrufnummer 1 kommt zuerst dran; nur der oberste Container eines Stapels ist erreichbar.
Liegt die nächste Nummer nicht oben, wird der oberste Container ihres Stapels (ein Blocker) auf einen anderen Stapel mit Platz gesetzt, jeder Hub kostet 1;
die nächste Nummer wird kostenlos entnommen, sobald sie oben liegt (restricted: nur Container über dem gesuchten werden bewegt).

Suchbaum wie in Stück 4 und 5: Ein **Knoten** ist ein Aufruf der Suche mit einer Bucht (und den bisherigen Hüben g), seine **Kinder** entstehen, indem der Blocker auf jeden anderen
Stapel mit Platz gesetzt wird; ein **Blatt** ist eine leere Bucht. Ein **Zustand** ist die Bucht nach den kostenlosen Abrufen.

  search       vier Verfahren (`mode`): "enum" (volle Aufzählung), "bb" (Branch and Bound wie Stück 4: Abbruch bei g + 1 >= beste Lösung), "bblb" (Branch and Bound mit Untergrenze:
               Abbruch bei g + Untergrenze >= beste Lösung), "ida" (iterative Vertiefung, Stück 5), jeweils mit
                 memo  None | "raw" | "canon"  Zustandsmerken: je Zustand die kleinste Hubzahl g merken, mit der er expandiert wurde; kommt er mit g' >= g wieder, wird er nicht noch
                       einmal expandiert (er zählt als besuchter Knoten und als Treffer). "raw": Zustand = Stapel in fester Reihenfolge, "canon": bis auf Vertauschen der Stapel.
                       Bei IDA* wird das Merken je Budgetstufe zurückgesetzt.
                 sym   False | True  Symmetriebruch: von mehreren LEEREN Zielstapeln nur den ersten probieren (nur leere Stapel sind gleich, Nummern kommen einmal vor).
  count_tree   Zahl der Knoten und Blätter des Baums der vollen Aufzählung und der verschiedenen Zustände (roh und kanonisch), per memoisierter Zählung: der Baum wird gezählt, nicht durchlaufen
  count_states Zahl der verschiedenen Zustände per Breitensuche über den Zustandsgraphen (anderer Rechenweg als count_tree)
  state_visits die Zustände des Baums mit der Zahl ihrer Besuche (nur für kleine Buchten)
"""

from dataclasses import dataclass

INF = 10 ** 9
MODES = ("enum", "bb", "bblb", "ida")
ORDERS = ("index", "tight", "anti")
MEMOS = (None, "raw", "canon")


def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def stack_blockers(stack):
    """Container in einem Stapel (unten nach oben), die über einem früher abzurufenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def blocker_count(stacks):
    """Zahl der blockierenden Container (Untergrenze der Hubzahl, Stück 2)."""
    return sum(stack_blockers(s) for s in stacks)


def target_stack(stacks):
    """(nächste Abrufnummer, Index ihres Stapels). Die Bucht darf nicht leer sein."""
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


def canon(stacks):
    """Kanonische Form: die Stapel sortiert (die Reihenfolge der Stapel spielt für die Kosten keine Rolle)."""
    return tuple(sorted(stacks))


def _fit_key(stacks, j, c):
    """Sortierschlüssel der engsten Passung für den Zielstapel j (Stück 1)."""
    m = min(stacks[j]) if stacks[j] else INF
    return (0, m) if m > c else (1, -m)


def child_targets(stacks, src, height, c, order, sym=False):
    """Zielstapel für den Blocker c (Stapel `src`, Bucht ohne c) in der Reihenfolge `order`; nur Stapel mit Platz. Mit `sym` bleibt von mehreren leeren Stapeln nur der erste."""
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    dests = [j for j in range(len(stacks)) if j != src and len(stacks[j]) < height]
    if order != "index":
        dests.sort(key=lambda j: (_fit_key(stacks, j, c), j))
        if order == "anti":
            dests.reverse()
    if not sym:
        return dests
    out, seen_empty = [], False
    for j in dests:
        if not stacks[j]:
            if seen_empty:
                continue
            seen_empty = True
        out.append(j)
    return out


@dataclass(frozen=True)
class SearchResult:
    optimum: int | None     # None, wenn das Knotenlimit erreicht wurde
    nodes: int              # Zahl der besuchten Knoten (bei capped: das Limit), bei IDA* die Summe über alle Budgetstufen; Treffer des Merkens zählen mit
    leaves: int             # Zahl der besuchten Blätter
    capped: bool
    first_leaf: int | None  # Hubzahl des ersten besuchten Blatts
    stages: tuple = ()      # nur IDA*: (Budget, Knoten, gefunden, Treffer, Tabellengröße) je Stufe; bei capped endet die Liste mit der abgebrochenen Stufe
    hits: int = 0           # Zahl der Knoten, die das Merken nicht expandiert hat (bei IDA* Summe über die Stufen)
    table: int = 0          # größte Zahl gemerkter Zustände (bei IDA* die größte einer Stufe)


class _CapReached(Exception):
    pass


class _Found(Exception):
    pass


def _dfs(start, height, order, prune, cap, stop_at_leaf, memo, sym):
    """Eine Tiefensuche. `prune(g, state, best)` -> True schneidet den Teilbaum eines Nicht-Blatts ab; `stop_at_leaf` beendet die Suche am ersten Blatt.
    Gibt (Knoten, Blätter, Hubzahl des ersten Blatts, beste Hubzahl, gefunden, Treffer, Tabellengröße) zurück; wirft _CapReached, wenn mehr als `cap` Knoten gebraucht werden."""
    nodes, leaves, hits = [0], [0], [0]
    first, best = [None], [INF]
    table = {}

    def rec(state, g):
        nodes[0] += 1
        if nodes[0] > cap:
            raise _CapReached(nodes[0] - 1, leaves[0], hits[0], len(table))
        st, _ = autopop(state)
        if not any(st):
            leaves[0] += 1
            if first[0] is None:
                first[0] = g
            if g < best[0]:
                best[0] = g
            if stop_at_leaf:
                raise _Found
            return
        if prune(g, st, best[0]):
            return
        if memo:
            key = canon(st) if memo == "canon" else st
            if table.get(key, INF) <= g:
                hits[0] += 1
                return
            table[key] = g
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        for j in child_targets(base, i, height, c, order, sym):
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            rec(tuple(tuple(s) for s in nxt), g + 1)

    found = False
    try:
        rec(start, 0)
    except _Found:
        found = True
    return nodes[0], leaves[0], first[0], best[0], found, hits[0], len(table)


def search(stacks, height, mode="ida", order="tight", cap=1_000_000, memo=None, sym=False) -> SearchResult:
    """Tiefensuche über die Hubfolgen mit Knotenzählung (siehe Moduldoc)."""
    if mode not in MODES:
        raise ValueError(f"unbekanntes Verfahren {mode!r}")
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    if memo not in MEMOS:
        raise ValueError(f"unbekanntes Merken {memo!r}")
    start = tuple(tuple(s) for s in stacks)
    if mode != "ida":
        if mode == "enum":
            prune = lambda g, st, best: False                                   # noqa: E731
        elif mode == "bb":
            prune = lambda g, st, best: g + 1 >= best                           # noqa: E731  jeder weitere Hub kostet mindestens 1
        else:
            prune = lambda g, st, best: g + blocker_count(st) >= best           # noqa: E731
        try:
            nodes, leaves, first, best, _, hits, table = _dfs(start, height, order, prune, cap, False, memo, sym)
        except _CapReached as e:
            return SearchResult(None, cap, e.args[1], True, None, (), e.args[2], e.args[3])
        return SearchResult(best, nodes, leaves, False, first, (), hits, table)
    budget = blocker_count(start)
    total, leaves_total, hits_total, table_max, stages = 0, 0, 0, 0, []
    while True:
        b = budget
        try:
            nodes, leaves, first, best, found, hits, table = _dfs(start, height, order, lambda g, st, _best, b=b: g + blocker_count(st) > b, cap - total, True, memo, sym)
        except _CapReached as e:
            stages.append((b, e.args[0], False, e.args[2], e.args[3]))
            return SearchResult(None, cap, leaves_total + e.args[1], True, None, tuple(stages), hits_total + e.args[2], max(table_max, e.args[3]))
        total += nodes
        leaves_total += leaves
        hits_total += hits
        table_max = max(table_max, table)
        stages.append((b, nodes, found, hits, table))
        if found:
            return SearchResult(first, total, leaves_total, False, first, tuple(stages), hits_total, table_max)
        budget += 1


@dataclass(frozen=True)
class TreeCount:
    nodes: int      # Knoten des Baums der vollen Aufzählung (Aufrufe der Suche)
    leaves: int     # Blätter dieses Baums
    raw: int        # verschiedene Zustände (nach den Abrufen), Stapel in fester Reihenfolge
    canon: int      # verschiedene Zustände bis auf Vertauschen der Stapel


class StateCapReached(Exception):
    pass


def count_tree(stacks, height, state_cap=100_000) -> TreeCount | None:
    """Der Baum der vollen Aufzählung, gezählt statt durchlaufen: Knoten(Zustand) = 1 + Summe über die Kinder, jeder Zustand wird nur einmal berechnet. None, wenn
    mehr als `state_cap` verschiedene Zustände vorkommen (die Zählung braucht Zeit und Speicher je Zustand)."""
    memo = {}
    entered = set()

    def rec(state):
        st, _ = autopop(state)
        got = memo.get(st)
        if got is not None:
            return got
        entered.add(st)
        if len(entered) > state_cap:
            raise StateCapReached
        if not any(st):
            memo[st] = (1, 1)
            return memo[st]
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        n, lv = 1, 0
        for j in child_targets(base, i, height, c, "index"):
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            a, b = rec(tuple(tuple(s) for s in nxt))
            n += a
            lv += b
        memo[st] = (n, lv)
        return memo[st]

    try:
        nodes, leaves = rec(tuple(tuple(s) for s in stacks))
    except StateCapReached:
        return None
    return TreeCount(nodes, leaves, len(memo), len({canon(s) for s in memo}))


def count_states(stacks, height, cap=3_000_000):
    """(verschiedene Zustände roh, bis auf Stapelvertauschen) des Zustandsgraphen, per Breitensuche; None bei mehr als `cap` Zuständen."""
    start, _ = autopop(tuple(tuple(s) for s in stacks))
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for state in frontier:
            if not any(state):
                continue
            _, i = target_stack(state)
            lst = [list(s) for s in state]
            c = lst[i].pop()
            base = tuple(tuple(s) for s in lst)
            for j in child_targets(base, i, height, c, "index"):
                new = [list(s) for s in lst]
                new[j].append(c)
                new, _ = autopop(tuple(tuple(s) for s in new))
                if new not in seen:
                    seen.add(new)
                    nxt.append(new)
                    if len(seen) > cap:
                        return None
        frontier = nxt
    return len(seen), len({canon(s) for s in seen})


def state_visits(stacks, height, max_nodes=400):
    """Die Zustände des Baums der vollen Aufzählung in der Reihenfolge des ersten Besuchs: [(Zustand, Zahl der Besuche, kleinste Hubzahl beim Besuch)].
    Läuft den Baum wirklich durch; wirft ValueError, wenn er mehr als `max_nodes` Knoten hat (nur für kleine Buchten gedacht)."""
    seen = {}
    order = []
    count = [0]

    def rec(state, g):
        count[0] += 1
        if count[0] > max_nodes:
            raise ValueError("Baum zu groß")
        st, _ = autopop(state)
        if st not in seen:
            seen[st] = [0, g]
            order.append(st)
        seen[st][0] += 1
        seen[st][1] = min(seen[st][1], g)
        if not any(st):
            return
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        for j in child_targets(base, i, height, c, "index"):
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            rec(tuple(tuple(s) for s in nxt), g + 1)

    rec(tuple(tuple(s) for s in stacks), 0)
    return [(s, seen[s][0], seen[s][1]) for s in order]


def fmt_state(stacks):
    return " | ".join("(" + ", ".join(str(c) for c in s) + ")" if s else "()" for s in stacks)
