"""Gleiche Zustände: Zustandsmerken und Symmetriebruch beim Umstauen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 6 der Reihe „Umstauen: Untergrenze und Suche“. Stück 4 zeigte die Knotenexplosion, Stück 5 die Untergrenze und IDA*. Hier die zweite Quelle der Ersparnis: Viele Knoten des
Suchbaums sind dieselbe Bucht. Die Demo zählt den Baum der vollen Aufzählung (ohne ihn zu durchlaufen) gegen die verschiedenen Zustände, trennt die Wiederholung in Mehrfachwege und
Stapelsymmetrie und misst, was Zustandsmerken und Symmetriebruch IDA* bringen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gzu_algorithm as A
import gzu_constants as C
from gzu_evaluation import (
    Settings,
    analyse,
    cell_key,
    count_rows,
    factor_text,
    load_bands,
    num,
    num_f,
    ratio_text,
    result_rows,
    verdict_bay,
    verdict_ida,
    verdict_replace,
    verdict_space,
    verdict_symmetry_break,
    verdict_tree,
)
from gzu_layout import dunkles_design, kopf_css
from gzu_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from gzu_visualization import build_bay, build_counts, build_gain, build_memo, build_nodes, build_space, build_tree_cells

st.set_page_config(page_title="Gleiche Zustände – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _mini():
    """Zustände der Mini-Bucht und des Gegenbeispiels aus Stück 1 mit der Zahl ihrer Besuche im Baum, dazu die Zählung und IDA* mit Merken."""
    out = []
    for bay, h in ((C.MINI_BAY, C.MINI_HEIGHT), (C.COUNTER_BAY, C.COUNTER_HEIGHT)):
        out.append((A.state_visits(bay, h), A.count_tree(bay, h), A.search(bay, h, "ida", "tight"), A.search(bay, h, "ida", "tight", memo="canon")))
    return out


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gzu_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔁 Gleiche Zustände: Merken und Symmetriebruch")
st.markdown(
    """
Stück 5 hat die Suche mit der **Untergrenze** klein gemacht. Hier die **zweite** Quelle der Ersparnis: Viele Knoten des Suchbaums sind **dieselbe Bucht**. Die Demo **zählt** den Baum der vollen Aufzählung, ohne ihn zu durchlaufen, und stellt ihn der Zahl der **verschiedenen Zustände** gegenüber. Dann trennt sie die Wiederholung in **Mehrfachwege** (derselbe Zustand auf verschiedenen Wegen) und **Stapelsymmetrie** (Buchten, die sich nur durch Vertauschen der Stapel unterscheiden) und misst, was **Zustandsmerken** und **Symmetriebruch** für IDA\\* bringen.

Weiter unten: die Abschnitte **🔬 Experiment** (die Mini-Bucht von Hand, wie viele Zustände gleich sind, Merken und Symmetriebruch für IDA\\*, Merken ohne Untergrenze, wie weit der Zustandsraum trägt), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das sechste Stück der Reihe „Umstauen: Untergrenze und Suche“.
"""
)

with st.expander("So funktionieren Zustandsmerken und Symmetriebruch", expanded=True):
    st.markdown(
        """
1. **Zustand:** die Bucht nach den kostenlosen Abrufen. Verschiedene Hubfolgen können im selben Zustand enden, zum Beispiel wenn ein Container erst auf Stapel A und später auf Stapel B landet oder gleich auf B.
2. **Zustandsmerken:** Je Zustand wird die kleinste Hubzahl *g* gemerkt, mit der er schon bearbeitet wurde. Kommt er mit gleichem oder größerem *g* wieder, wird er nicht noch einmal bearbeitet. Bei IDA\\* gilt das je Budgetstufe.
3. **Symmetrie:** Buchten, die sich nur durch Vertauschen der Stapel unterscheiden, haben dieselben Kosten. Das Merken kann Zustände **bis auf Stapelvertauschen** gleichsetzen (kanonisch) oder nur genau gleiche (roh).
4. **Symmetriebruch:** Da jede Nummer nur einmal vorkommt, sind nur **leere** Stapel einander gleich. Von mehreren leeren Zielstapeln wird nur der erste probiert.
5. **Zum Vergleich:** IDA\\* aus Stück 5 ohne beides; die Tiefensuchen aus Stück 4 und 5 (volle Aufzählung, Branch and Bound ohne und mit Untergrenze) mit Merken.
6. **Gezählt, nicht durchlaufen:** Die Knoten des Baums der vollen Aufzählung werden mit einer gemerkten Zählung bestimmt (Knoten eines Zustands = 1 + Knoten seiner Kinder); so steht auch bei Milliarden Knoten die exakte Zahl da. Bei mehr als 100 000 verschiedenen Zuständen wird nicht gezählt.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    layers = st.slider("Lagen je Stapel", *bounds("layers_slider"), key="layers_slider", help="So viele Container stehen anfangs auf jedem Stapel.")
    extra = st.slider("Platz (Lagen über der Anfangshöhe)", *bounds("extra_slider"), key="extra_slider",
                      help="Höchsthöhe = Lagen + Platz. Standard 2. Die vorberechneten Tabellen gelten für Platz 2.")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Plätze verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "layers_slider": int(layers), "extra_slider": int(extra), "seed_input": int(seed)})

settings = Settings(int(stacks), int(layers), int(extra), int(seed))
with st.spinner(f"Zähle den Baum und rechne sieben Verfahren (höchstens {num(C.LIVE_CAP)} Knoten je Verfahren) …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
rows = result_rows(a)
by_variant = {r["variant"]: r for r in rows}
m1, m2, m3, m4 = st.columns(4)
m1.metric("Knoten des Baums (volle Aufzählung)", "nicht gezählt" if a.tree is None else num(a.tree.nodes),
          help=f"Gezählt, nicht durchlaufen. Bei mehr als {num(C.LIVE_STATE_CAP)} verschiedenen Zuständen wird nicht gezählt.")
m2.metric("Verschiedene Zustände", "–" if a.tree is None else num(a.tree.raw), delta=None if a.tree is None else f"{num(a.tree.canon)} bis auf Stapelvertauschen", delta_color="off",
          help="Buchten nach den kostenlosen Abrufen, die im Baum vorkommen.")
m3.metric("IDA* ohne / mit Merken (Knoten)", f"{by_variant[C.VARIANTS[0]]['nodes_text']} / {by_variant[C.VARIANTS[3]]['nodes_text']}",
          help="Aus Stück 5 und mit Merken (bis auf Stapelvertauschen), engste Passung zuerst.")
m4.metric("Optimum", "nicht bewiesen" if a.optimum is None else a.optimum, delta=f"Untergrenze {a.lower}, Bucht {settings.stacks} × {settings.layers}", delta_color="off",
          help="Alle Verfahren, die fertig werden, liefern dasselbe Optimum.")
st.plotly_chart(build_bay(a.bay, a.height, target=min(c for s in a.bay for c in s)), width="stretch", key="chart_bay")
st.caption("Rot: blockierende Container (liegen über einem früher abzurufenden), grün: der nächste Abruf, grau-blau: alle übrigen.")
crows = count_rows(a)
if crows:
    st.plotly_chart(build_counts(crows), width="stretch", key="chart_counts")
else:
    st.warning(f"Mehr als {num(C.LIVE_STATE_CAP)} verschiedene Zustände: Der Baum der vollen Aufzählung wird hier nicht gezählt.")
table = ["| Verfahren | Knoten | Treffer des Merkens | größte Tabelle | Optimum |", "|---|---|---|---|---|"]
for r in rows:
    table.append(f"| {r['name']} | {r['nodes_text']} | {num(r['hits']) if r['memo'] else ''} | {num(r['table']) if r['memo'] else ''} | {r['optimum']} |")
st.markdown("\n".join(table))
st.caption(f"Knoten: besuchte Aufrufe der Suche (bei IDA* die Summe über alle Budgetstufen, Treffer des Merkens zählen mit); „mehr als“ heißt: am Limit von {num(C.LIVE_CAP)} abgebrochen. "
           "Treffer: Knoten, deren Zustand schon mit höchstens so vielen Hüben bearbeitet war. Tabelle: größte Zahl gemerkter Zustände (bei IDA* in einer Stufe).")
st.plotly_chart(build_nodes(rows), width="stretch", key="chart_nodes")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Konfigurationen sind gleich?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: die Mini-Bucht ------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Die Zustände der Mini-Bucht von Hand")
(mini_states, mini_count, mini_ida, mini_ida_m), (counter_states, counter_count, counter_ida, counter_ida_m) = _mini()
st.caption("3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3): nur die 4 blockiert (Untergrenze 1). Der Baum der vollen Aufzählung aus Stück 4 hat 9 Knoten; "
           "hier die **verschiedenen Zustände** darin, in der Reihenfolge des ersten Besuchs, mit der Zahl der Besuche.")
st.plotly_chart(build_bay(C.MINI_BAY, C.MINI_HEIGHT, target=1), width="stretch", key="chart_mini")
mt = ["| Zustand | Besuche im Baum | kleinste Hubzahl |", "|---|---|---|"]
for s, v, g in mini_states:
    mt.append(f"| {A.fmt_state(s)}{' (leer)' if not any(s) else ''} | {v} | {g} |")
st.markdown("\n".join(mt))
twice = [s for s, v, g in mini_states if v > 1 and any(s)]
st.success(f"{mini_count.nodes} Knoten, aber nur {mini_count.raw} verschiedene Zustände. " + (f"Der Zustand {A.fmt_state(twice[0])} wird zweimal erreicht: die 4 landet sofort auf Stapel 3 (1 Hub) oder erst auf Stapel 2 und dann auf Stapel 3 (2 Hübe). " if twice else "")
           + f"Die leere Bucht wird {max(v for s, v, g in mini_states if not any(s))}-mal erreicht, einmal je Blatt. IDA* braucht {mini_ida.nodes} Knoten, mit Merken {mini_ida_m.nodes}: In so kleinen Buchten gibt es noch nichts zu merken.")
top = sorted(counter_states, key=lambda x: -x[1])[:4]
st.markdown(f"**Das Gegenbeispiel aus Stück 1** ((3, 6), (2, 4), (1, 5), Höchsthöhe 4): der Baum hat **{counter_count.nodes} Knoten**, aber nur **{counter_count.raw} verschiedene Zustände** "
            f"({counter_count.canon} bis auf Stapelvertauschen). Am häufigsten besucht: " + "; ".join(f"{A.fmt_state(s)} ({v}-mal)" for s, v, g in top)
            + f". IDA\\* braucht {counter_ida.nodes} Knoten, mit Merken {counter_ida_m.nodes} (größte Tabelle {counter_ida_m.table}).")

st.markdown("---")

# --- Experiment: Wie viele Zustände sind gleich? -------------------------------------------------------------------------------------------------

bands = _bands()
tree, ida, memo, space = bands["baum"], bands["ida"], bands["merken"], bands["raum"]
st.subheader("🔬 Experiment: Wie viele Zustände sind gleich?")
st.caption("Je Zelle feste Buchten (Platz 2, dieselben wie in Stück 4 und 5), vorberechnet (`generate_precomputed.py`). Der Baum der vollen Aufzählung wird gezählt (auch bei Milliarden Knoten), "
           "dazu die verschiedenen Zustände. Median / Maximum über die Buchten.")


def _mm(v):
    return f"{num_f(v['median'])} / {num(v['max'])}"


ta = ["| Zelle (Buchten) | Knoten des Baums | verschiedene Zustände | bis auf Stapelvertauschen | Knoten / Zustände (Median, Maximum) | Zustände roh / bis auf Stapelvertauschen (Median, Maximum) |", "|---|---|---|---|---|---|"]
for s_, l_, n_ in C.TREE_CELLS:
    c = tree[cell_key(s_, l_)]
    over = f", {c['nodes']['over']} über dem Limit" if c["nodes"]["over"] else ""
    ta.append(f"| {s_} × {l_} ({c['n']}) | {_mm(c['nodes'])}{over} | {_mm(c['raw'])} | {_mm(c['canon'])} | {factor_text(c['paths']['median'])} ({factor_text(c['paths']['max'])}) | "
              f"{ratio_text(c['sym']['median'])} ({ratio_text(c['sym']['max'])}) |")
st.markdown("\n".join(ta))
st.caption(f"5 × 4 fehlt: Dort wurde der Baum nicht gezählt. „Über dem Limit“: Buchten mit mehr als {num(C.BAND_STATE_CAP)} Zuständen, die im Median fehlen (bei 4 × 4 eine von 30).")
cells_a = {f"{s_} × {l_}": tree[cell_key(s_, l_)] for s_, l_, _ in C.TREE_CELLS}
st.plotly_chart(build_tree_cells(cells_a), width="stretch", key="chart_tree")
here_tree = tree.get(cell_key(settings.stacks, settings.layers))
st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung)**" + ("" if settings.extra == C.DEFAULT_EXTRA else f", Tabellen gelten für Platz {C.DEFAULT_EXTRA}, hier ist Platz {settings.extra} eingestellt") + ":")
if here_tree is None:
    st.info(f"Für {settings.stacks} × {settings.layers} wurde der Baum nicht gezählt (zu viele Zustände).")
else:
    kind, text = verdict_tree(here_tree)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Merken und Symmetriebruch für IDA* ----------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Was bringen Merken und Symmetriebruch für IDA*?")
st.caption("IDA* aus Stück 5 (engste Passung zuerst) in vier Fassungen: ohne, mit Symmetriebruch (leere Stapel), mit Merken roh und mit Merken bis auf Stapelvertauschen. "
           f"Knotenlimit {num(C.BAND_CAP)}. Median / Mittel / Maximum der Knoten.")


def _mmm(v):
    return f"{num_f(v['median'])} / {num(round(v['mean']))} / {num(v['max'])}"


tb = ["| Zelle (Buchten) | IDA* ohne | mit Symmetriebruch | Merken roh | Merken bis auf Stapelvertauschen |", "|---|---|---|---|---|"]
for s_, l_, n_ in C.IDA_CELLS:
    c = ida[cell_key(s_, l_)]["variants"]
    tb.append(f"| {s_} × {l_} ({n_}) | {_mmm(c['base'])} | {_mmm(c['sym'])} | {_mmm(c['raw'])} | {_mmm(c['canon'])} |")
st.markdown("\n".join(tb))


def _ratio(r):
    return f"{ratio_text(r['median'])}, {ratio_text(r['mean'])}, {factor_text(r['max'])}, {r['gain'] * 100:.0f} %"


tr = ["| Zelle | ohne / Symmetriebruch (Median, Mittel, Maximum, Buchten mit Gewinn) | ohne / Merken (Median, Mittel, Maximum, Buchten mit Gewinn) | Treffer des Merkens (Median) | größte Tabelle (Median, Maximum) |", "|---|---|---|---|---|"]
for s_, l_, _n in C.IDA_CELLS:
    c = ida[cell_key(s_, l_)]
    hits_txt = f"{c['hits'] * 100:.1f}".replace(".", ",")
    tr.append(f"| {s_} × {l_} | {_ratio(c['sym'])} | {_ratio(c['canon'])} | {hits_txt} % | {num_f(c['table']['median'])}, {num(c['table']['max'])} |")
st.markdown("\n".join(tr))
st.caption("Verhältnisse je Bucht (Knoten ohne / Knoten mit), dann Median, Mittel, Maximum und Anteil der Buchten mit Gewinn. Merken roh und bis auf Stapelvertauschen unterscheiden sich in den Medianen der Knoten nur bei 5 × 4 (434 gegen 415).")
cells_b = {f"{s_} × {l_}": ida[cell_key(s_, l_)] for s_, l_, _ in C.IDA_CELLS}
st.plotly_chart(build_gain(cells_b), width="stretch", key="chart_gain")
here_ida = ida[cell_key(settings.stacks, settings.layers)]
st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung):**")
for verdict in (verdict_ida, verdict_symmetry_break):
    kind, text = verdict(here_ida)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Merken ohne Untergrenze ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Merken ohne Untergrenze")
st.caption("Tiefensuchen mit Merken (bis auf Stapelvertauschen) gegen IDA* ohne Merken: Hat das Merken die Untergrenze ersetzt? Median / Mittel / Maximum der Knoten, Limit "
           f"{num(C.BAND_CAP)}.")
tc = ["| Zelle (Buchten) | volle Aufzählung + Merken | B&B ohne UG + Merken | B&B mit UG + Merken | IDA* (ohne Merken) | IDA* + Merken |", "|---|---|---|---|---|---|"]


def _mmm_over(v):
    if v["median"] is None:
        return f"alle {v['over']} über Limit"
    return _mmm(v) + (f", {v['over']} über Limit" if v["over"] else "")


for s_, l_, n_ in C.MEMO_CELLS:
    c = memo[cell_key(s_, l_)]["variants"]
    tc.append(f"| {s_} × {l_} ({n_}) | {_mmm_over(c['enum+canon'])} | {_mmm_over(c['bb+canon'])} | {_mmm_over(c['bblb+canon'])} | {_mmm_over(c['ida'])} | {_mmm_over(c['ida+canon'])} |")
st.markdown("\n".join(tc))
cells_c = {f"{s_} × {l_}": memo[cell_key(s_, l_)] for s_, l_, _ in C.MEMO_CELLS}
st.plotly_chart(build_memo(cells_c), width="stretch", key="chart_memo")
st.caption("Die Abbildung zeigt den Median des Verhältnisses Knoten des Verfahrens / Knoten von IDA* ohne Merken je Bucht; über 1 heißt: mehr Knoten als IDA*.")
here_memo = memo.get(cell_key(settings.stacks, settings.layers))
st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung):**")
if here_memo is None:
    st.info(f"Für {settings.stacks} × {settings.layers} wurde Merken ohne Untergrenze nicht gerechnet; die Tabelle zeigt die Zellen, die gerechnet wurden.")
else:
    kind, text = verdict_replace(here_memo)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Wie weit trägt der Zustandsraum? ------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie weit trägt der Zustandsraum?")
st.caption(f"Zahl aller verschiedenen Zustände des Zustandsgraphen (Breitensuche), Median über je 5 Buchten, Limit {num(C.BAND_STATE_CAP)} Zustände. **Sehr grob:** 5 Buchten je Zelle, Läufe über dem Limit fehlen im Median.")
ts = ["| Zelle (Buchten) | Zustände roh (Median, Maximum) | bis auf Stapelvertauschen (Median) | über Limit |", "|---|---|---|---|"]
for s_, l_, n_ in C.SPACE_CELLS:
    c = space[cell_key(s_, l_)]
    ts.append(f"| {s_} × {l_} ({n_}) | {_mm(c['raw'])} | {num_f(c['canon']['median'])} | {c['raw']['over']} |")
st.markdown("\n".join(ts))
cells_d = {f"{s_} × {l_}": space[cell_key(s_, l_)] for s_, l_, _ in C.SPACE_CELLS}
st.plotly_chart(build_space(cells_d), width="stretch", key="chart_space")
for s_, l_, _ in C.SPACE_CELLS:
    if (s_, l_) in ((5, 3), (4, 4), (5, 4)):
        kind, text = verdict_space(space[cell_key(s_, l_)], f"{s_} × {l_}")
        getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Knoten statt Zeit** | Das Merken kostet pro Knoten Rechenzeit (Tabelle, Schlüssel, Sortieren); Sekunden sind hier nicht gemessen. Im README steht eine Einzelmessung. | – |
| **Nur Symmetrie der Stapelreihenfolge** | Stärkere Formen (Dominanzregeln, Vertauschbarkeit unabhängiger Hübe) sind nicht untersucht. | – |
| **Der Baum wird nur bis 100 000 Zustände gezählt** | Darüber zeigt die App „nicht gezählt“; die vorberechneten Tabellen reichen bis 4 × 4. | – |
| **Der Zustandsraum ist grob gemessen** | 5 Buchten je Zelle, bei 4 × 4 und 5 × 4 je eine Bucht über dem Limit von 3 Millionen Zuständen. Der Median sagt wenig über den schweren Schwanz. | – |
| **Nur restricted, nur volle Buchten, Platz 2 in den Tabellen** | Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich Baum und Zustandsraum. | – |
| **Zahlen aus Zufallsbuchten** | Größenordnungen aus festen Buchten, keine Messung an einem echten Terminal oder Lager. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** eine Bucht aus $s$ Stapeln der Höchsthöhe $H$, die Container tragen die Abrufnummern $1, \dots, N$ (kleiner = früher). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; im *restricted* Modell werden nur Container über der nächsten abzurufenden Nummer bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt. Der Suchbaum und die Zählung der **Knoten** (besuchte Aufrufe der Suche) sind die aus Stück 4 und 5.

**Zustandsgraph.** Ein *Zustand* $B$ ist eine Bucht nach den kostenlosen Abrufen. Seine Kinder $\mathrm{ch}(B)$ entstehen durch den Hub des Blockers auf jeden anderen Stapel mit Platz (und die folgenden Abrufe); die leere Bucht hat keine. Der Baum der vollen Aufzählung entfaltet diesen Graphen zu einem Baum: Mehrere Wege können denselben Zustand erreichen.

**Zählen statt Durchlaufen.** Die Knotenzahl $n(B)$ des Baums unter $B$ erfüllt $n(B) = 1 + \sum_{B' \in \mathrm{ch}(B)} n(B')$ (mit Vielfachheit der Kinder), $n(\text{leer}) = 1$. Mit gemerkten Werten braucht die Rechnung eine Auswertung je verschiedenem Zustand, nicht je Knoten; so lässt sich ein Baum mit $10^{12}$ Knoten über einige $10^5$ Zustände zählen.

**Zustandsmerken ist korrekt.** Wurde ein Zustand $B$ schon mit $g'$ Hüben bearbeitet und kommt er mit $g \ge g'$ wieder, kann der Teilbaum unter ihm nichts Besseres liefern als beim ersten Besuch: Die Kosten der Fortsetzung hängen nur von $B$ ab, und $g + \mathrm{Rest} \ge g' + \mathrm{Rest}$. *Bei IDA\*:* Die Stufe fragt, ob eine Fortsetzung mit $g + \mathrm{Rest} \le b$ existiert; hat der erste Besuch keine gefunden, findet sie auch der spätere nicht. Darum wird die Tabelle je Stufe zurückgesetzt: Mit größerem Budget kann derselbe Zustand eine Fortsetzung haben, die der Stufe davor fehlte. *Bei Branch and Bound:* Die beste bisher gefundene Lösung sinkt nur, der Schnitt bleibt gültig.

**Symmetrie.** Vertauscht man die Stapel einer Bucht, ändern sich die Kosten nicht (die Regeln unterscheiden Stapel nur durch ihren Inhalt). Die *kanonische Form* sortiert die Stapel. Da jede Nummer nur einmal vorkommt, sind zwei **nicht leere** Stapel nie gleich; zwei Buchten sind also nur dann bis auf Vertauschen gleich, wenn ihre Stapel dieselbe Menge bilden. Der *Symmetriebruch* lässt von mehreren **leeren** Zielstapeln nur den ersten zu: Die Kinder unterscheiden sich nur durch Vertauschen der beiden leeren Stapel.

**Aufspaltung der Wiederholung.** $\dfrac{\text{Knoten}}{\text{kanonische Zustände}} = \dfrac{\text{Knoten}}{\text{rohe Zustände}} \cdot \dfrac{\text{rohe Zustände}}{\text{kanonische Zustände}}$: der erste Faktor sind die Mehrfachwege, der zweite die Stapelsymmetrie.

**Warum die Untergrenze und das Merken sich im Median ersetzen.** Die Untergrenze schneidet Knoten ab, deren Hubzahl schon das Budget sprengt; das sind wohl vor allem Wege, die Container mehrfach bewegen und deshalb im selben Zustand enden wie kürzere (der Mechanismus ist nicht direkt gemessen). Was das Merken streichen würde, hat die Untergrenze im Median meist schon gestrichen; im Schwanz bringt das Merken darüber hinaus noch viel. Das ist ein Messbefund (siehe die Tabellen), kein Satz.

**Literatur.** Das Problem heißt in der Literatur Block Relocation Problem. Die Literatur zu Transpositionstabellen und Symmetriebrechung für dieses Problem wurde nicht gelesen; die Verfahren und die Zählung sind hier selbst gebaut.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
