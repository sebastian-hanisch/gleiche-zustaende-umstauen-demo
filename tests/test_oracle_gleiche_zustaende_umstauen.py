"""Orakel-Test gleiche-zustaende-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Optimum, Zustandszahlen und Knotenzahlen gegen ANDERE Rechenwege.

Orakel 1: Breitensuche über alle Buchtzustände (restricted) liefert das Optimum; jedes Verfahren mit jedem Merken und Symmetriebruch muss es treffen.
Orakel 2: Die Zahl der verschiedenen Zustände aus einer eigenen Erreichbarkeitssuche (Menge der erreichbaren Zustände) gegen `count_tree` (gemerkte Zählung) und `count_states`.
Orakel 3: Die Knoten und Blätter des Baums der vollen Aufzählung per echtem Durchlauf ohne Merken (eigene Rekursion) gegen die gemerkte Zählung und die Besuche je Zustand gegen `state_visits`.
Orakel 4: Knoten, Treffer und Tabellengrößen von Tiefensuche und IDA* mit Merken gegen eine zweite, **iterative** Fassung mit eigenem Stapel.
Orakel 5: Kostengleichheit bis auf Vertauschen der Stapel (Grundlage der kanonischen Form).
Vorher an den Handzahlen geprüft: Mini-Bucht 9 Knoten und 4 Zustände (C zweimal), Gegenbeispiel 153 und 25 (16)."""

from collections import Counter
from itertools import permutations

import gzu_algorithm as A
from gzu_scenario import canonical, make_bay, max_height

INF = 10 ** 9


def _pop(st):
    st = [list(s) for s in st]
    while True:
        items = [c for s in st for c in s]
        if not items:
            return tuple(tuple(s) for s in st)
        t = min(items)
        hit = [s for s in st if s and s[-1] == t]
        if not hit:
            return tuple(tuple(s) for s in st)
        hit[0].pop()


def own_blockers(state):
    """Untergrenze neu gezählt: Container, unter denen ein kleinerer im selben Stapel liegt."""
    return sum(1 for s in state for i, c in enumerate(s) if any(d < c for d in s[:i]))


def own_children(state, height):
    """Kinder eines Knotens (Bucht nach den Abrufen), alle Zielstapel in Stapelreihenfolge, als Buchten nach dem Hub (noch vor den Abrufen)."""
    items = [c for s in state for c in s]
    t = min(items)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    out = []
    for dst in range(len(state)):
        if dst == src or len(state[dst]) >= height:
            continue
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[dst].append(c)
        out.append(tuple(tuple(s) for s in nxt))
    return out


def bfs_optimum(bay, height):
    start = _pop(bay)
    if not any(start):
        return 0
    frontier, seen, depth = {start}, {start}, 0
    while frontier:
        depth += 1
        nxt = set()
        for state in frontier:
            for child in own_children(state, height):
                new = _pop(child)
                if not any(new):
                    return depth
                if new not in seen:
                    seen.add(new)
                    nxt.add(new)
        frontier = nxt
    raise AssertionError("keine Lösung")


def reachable_states(bay, height):
    """Alle Zustände (nach den Abrufen) im Zustandsgraphen, eigene Erreichbarkeitssuche."""
    start = _pop(bay)
    seen, todo = {start}, [start]
    while todo:
        state = todo.pop()
        if not any(state):
            continue
        for child in own_children(state, height):
            new = _pop(child)
            if new not in seen:
                seen.add(new)
                todo.append(new)
    return seen


def walk_tree(bay, height):
    """Echter Durchlauf des Baums der vollen Aufzählung ohne Merken: (Knoten, Blätter, Besuche je Zustand)."""
    visits = Counter()
    leaves = [0]

    def rec(state):
        st = _pop(state)
        visits[st] += 1
        if not any(st):
            leaves[0] += 1
            return
        for child in own_children(st, height):
            rec(child)

    rec(bay)
    return sum(visits.values()), leaves[0], visits


def ordered_children(state, height, order, sym):
    t = min(c for s in state for c in s)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    base = [list(s) for s in state]
    base[src].pop()
    dests = [j for j in range(len(state)) if j != src and len(state[j]) < height]
    if order != "index":
        def key(j):
            m = min(base[j]) if base[j] else INF
            return (0, m) if m > c else (1, -m)
        dests.sort(key=lambda j: (key(j), j))
        if order == "anti":
            dests.reverse()
    if sym:
        kept, seen_empty = [], False
        for j in dests:
            if not base[j]:
                if seen_empty:
                    continue
                seen_empty = True
            kept.append(j)
        dests = kept
    return src, c, dests


def iterative_search(bay, height, order, prune, stop_at_leaf, memo, sym):
    """Tiefensuche mit eigenem Stapel statt Rekursion. Gibt (Knoten, bestes Blatt, gefunden, Treffer, Tabellengröße) zurück."""
    best, nodes, hits = INF, 0, 0
    table = {}
    stack = [(tuple(tuple(s) for s in bay), 0, None, None)]            # (Zustand vor den Abrufen, Hübe, noch nicht abgearbeitete Kinder, Kontext)
    while stack:
        state, g, kids, ctx = stack.pop()
        if kids is None:                                                # Knoten wird zum ersten Mal besucht
            nodes += 1
            state = _pop(state)
            if not any(state):
                best = min(best, g)
                if stop_at_leaf:
                    return nodes, best, True, hits, len(table)
                continue
            if prune(g, state, best):
                continue
            if memo:
                key = tuple(sorted(state)) if memo == "canon" else state
                if table.get(key, INF) <= g:
                    hits += 1
                    continue
                table[key] = g
            src, c, dests = ordered_children(state, height, order, sym)
            kids, ctx = list(dests), (src, c)
        if not kids:
            continue
        j = kids.pop(0)
        stack.append((state, g, kids, ctx))
        src, c = ctx
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[j].append(c)
        stack.append((tuple(tuple(s) for s in nxt), g + 1, None, None))
    return nodes, best, False, hits, len(table)


def iterative_dfs(bay, height, mode, order, memo, sym=False):
    prune = {"enum": lambda g, st, b: False, "bb": lambda g, st, b: g + 1 >= b, "bblb": lambda g, st, b: g + own_blockers(st) >= b}[mode]
    nodes, best, _, hits, table = iterative_search(bay, height, order, prune, False, memo, sym)
    return best, nodes, hits, table


def iterative_ida(bay, height, order, memo, sym=False):
    budget = own_blockers(_pop(bay))
    stages = []
    while True:
        nodes, best, found, hits, table = iterative_search(bay, height, order, lambda g, st, b, budget=budget: g + own_blockers(st) > budget, True, memo, sym)
        stages.append((budget, nodes, found, hits, table))
        if found:
            return best, tuple(stages)
        budget += 1


def all_bays_3x2():
    seen = {}
    for perm in permutations(range(1, 7)):
        bay = tuple(tuple(perm[i * 2:(i + 1) * 2]) for i in range(3))
        seen.setdefault(canonical(bay), bay)
    return list(seen.values())


VARIANTS = ((None, False), (None, True), ("raw", False), ("canon", False), ("canon", True))


def test_oracle_on_the_hand_numbers(mini, counter):
    assert bfs_optimum(*mini) == 2 and bfs_optimum(*counter) == 4
    nodes, leaves, visits = walk_tree(*mini)
    assert (nodes, leaves, len(visits)) == (9, 5, 4) and sorted(visits.values()) == [1, 1, 2, 5]
    nodes, leaves, visits = walk_tree(*counter)
    assert (nodes, leaves, len(visits), len({tuple(sorted(s)) for s in visits})) == (153, 77, 25, 16)
    assert iterative_dfs(*mini, "enum", "tight", "canon") == (2, 7, 1, 3)
    assert iterative_ida(*counter, "tight", "canon") == (4, ((3, 3, False, 0, 1), (4, 12, True, 0, 7)))


def test_every_variant_finds_the_optimum_of_the_breadth_first_search():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            opt = bfs_optimum(bay, h)
            for mode in A.MODES:
                for order in A.ORDERS:
                    for memo, sym in VARIANTS:
                        r = A.search(bay, h, mode, order, memo=memo, sym=sym)
                        assert (r.optimum, r.capped) == (opt, False), (stacks, layers, sd, mode, order, memo, sym)


def test_distinct_state_counts_equal_an_own_reachability_search():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 100), (3, 3, 100), (4, 3, 15)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            states = reachable_states(bay, h)
            expected = (len(states), len({tuple(sorted(s)) for s in states}))
            t = A.count_tree(bay, h)
            assert (t.raw, t.canon) == expected and A.count_states(bay, h) == expected, (stacks, layers, sd)


def test_node_and_leaf_counts_equal_the_real_walk_and_the_visits_equal_state_visits():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 30)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            nodes, leaves, visits = walk_tree(bay, h)
            t = A.count_tree(bay, h)
            assert (t.nodes, t.leaves) == (nodes, leaves) == (A.search(bay, h, "enum", "index").nodes, A.search(bay, h, "enum", "index").leaves), bay
            got = {s: v for s, v, g in A.state_visits(bay, h, max_nodes=100_000)}
            assert got == dict(visits), bay
    for sd in range(20):                                                 # auch ein größerer Baum durch den echten Durchlauf (4 x 3 bis 40 000 Knoten)
        bay = make_bay(4, 3, sd)
        t = A.count_tree(bay, 5)
        if t.nodes <= 40_000:
            assert walk_tree(bay, 5)[:2] == (t.nodes, t.leaves)


def test_search_with_memo_matches_an_iterative_second_implementation():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            for order in A.ORDERS:
                for mode in ("enum", "bb", "bblb"):
                    for memo, sym in ((None, False), ("raw", False), ("canon", False), ("canon", True)):
                        r = A.search(bay, h, mode, order, memo=memo, sym=sym)
                        assert (r.optimum, r.nodes, r.hits, r.table) == iterative_dfs(bay, h, mode, order, memo, sym), (stacks, layers, bay, mode, order, memo, sym)


def test_ida_with_memo_and_symmetry_break_matches_an_iterative_second_implementation_stage_by_stage():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 40), (4, 3, 15)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            for order in A.ORDERS:
                for memo, sym in VARIANTS:
                    r = A.search(bay, h, "ida", order, memo=memo, sym=sym)
                    opt, stages = iterative_ida(bay, h, order, memo, sym)
                    assert (r.optimum, r.stages) == (opt, stages), (stacks, layers, bay, order, memo, sym)


def test_the_cost_of_a_bay_does_not_change_when_the_stacks_are_permuted():
    for sd in range(25):
        bay = make_bay(3, 3, sd)
        opt = bfs_optimum(bay, 5)
        for perm in permutations(bay):
            assert bfs_optimum(perm, 5) == opt == A.search(perm, 5, "ida", "tight").optimum, (sd, perm)
    bay = ((1, 4), (), (5, 2), (6, 3))                                  # mit einem leeren Stapel
    for perm in permutations(bay):
        assert bfs_optimum(perm, 4) == bfs_optimum(bay, 4)
