"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 3          # Zahl der Stapel
LAYERS_MIN, LAYERS_MAX, DEFAULT_LAYERS = 2, 4, 3          # Anfangsfüllung je Stapel (Lagen)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 1, 4, 2             # Platz: Höchsthöhe = Lagen + Zuschlag (Standard 2 wie in Stück 1 bis 5)
SEED_MAX = 999999

LIVE_CAP = 500_000                                        # Knotenlimit der Live-Suchläufe; darüber: „gibt auf“
LIVE_STATE_CAP = 100_000                                  # Live-Zählung des Baums: mehr verschiedene Zustände werden nicht gezählt (rund drei Sekunden)
BAND_CAP = 1_000_000                                      # Knotenlimit der vorberechneten Suchläufe
BAND_STATE_CAP = 3_000_000                                # Limit der vorberechneten Zählung der Zustände (Raumtabelle)

# Zellen der vorberechneten Tabellen: (Stapel, Lagen, Zahl der festen Buchten). Dieselben Buchten wie in Stück 4 und 5 (Seeds ab 0, Platz 2).
TREE_CELLS = ((3, 2, 100), (4, 2, 100), (3, 3, 100), (5, 2, 60), (4, 3, 40), (3, 4, 40), (5, 3, 20), (4, 4, 30))      # Baum gegen Zustände (A); 5 x 4 nicht gezählt
IDA_CELLS = TREE_CELLS + ((5, 4, 20),)                                                                                 # IDA* mit Merken und Symmetriebruch (B)
MEMO_CELLS = ((3, 3, 100), (4, 3, 40), (3, 4, 40), (5, 3, 20), (4, 4, 30))                                              # Merken ohne Untergrenze (C1)
SPACE_CELLS = ((3, 3, 5), (4, 3, 5), (5, 3, 5), (6, 3, 5), (4, 4, 5), (5, 4, 5))                                      # Größe des Zustandsraums (C2), nur wenige Buchten

REP_STRONG, REP_WEAK = 10.0, 2.0                          # Verdikt „Wiederholung“: Knoten des Baums / verschiedene Zustände
SYM_SMALL = 1.5                                           # bis hier gilt die Stapelsymmetrie (roh / kanonisch) als klein
MEMO_NOTICEABLE, MEMO_TAIL = 1.25, 2.0                    # Verdikt „Merken für IDA*“: Median ab hier spürbar, Mittel ab hier „Gewinn im Schwanz“
REPLACE_STRONG = 1.5                                      # Verdikt „Merken ersetzt die Untergrenze nicht“: Merken ohne Untergrenze braucht mindestens das 1,5-Fache von IDA*

# Live-Verfahren: (Verfahren, Merken, Symmetriebruch); Reihenfolge der Kinder immer „engste Passung zuerst“
VARIANTS = (("ida", None, False), ("ida", None, True), ("ida", "raw", False), ("ida", "canon", False),
            ("enum", "canon", False), ("bb", "canon", False), ("bblb", "canon", False))
VARIANT_NAMES = {
    ("ida", None, False): "IDA* (Stück 5)",
    ("ida", None, True): "IDA* mit Symmetriebruch",
    ("ida", "raw", False): "IDA* mit Merken (roh)",
    ("ida", "canon", False): "IDA* mit Merken (bis auf Stapelvertauschen)",
    ("enum", "canon", False): "Volle Aufzählung mit Merken",
    ("bb", "canon", False): "Branch and Bound ohne Untergrenze mit Merken",
    ("bblb", "canon", False): "Branch and Bound mit Untergrenze mit Merken",
}
VARIANT_SHORT = {("ida", None, False): "IDA*", ("ida", None, True): "IDA* Symm.", ("ida", "raw", False): "IDA* Merken roh", ("ida", "canon", False): "IDA* Merken",
                 ("enum", "canon", False): "Aufzählung Merken", ("bb", "canon", False): "B&B ohne UG Merken", ("bblb", "canon", False): "B&B mit UG Merken"}

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_CAPPED = "#b5545a"       # Lauf am Knotenlimit abgebrochen
COLOR_VARIANT = {("ida", None, False): "#2F6B65", ("ida", None, True): "#9bc7c0", ("ida", "raw", False): "#4c78a8", ("ida", "canon", False): "#1c4742",
                 ("enum", "canon", False): "#7a8fa6", ("bb", "canon", False): "#d9822b", ("bblb", "canon", False): "#b5545a"}
COLOR_LINES = ("#7a8fa6", "#2F6B65", "#d9822b", "#4c78a8")

# Sonderbuchten (in der Vormessung gefunden, Eigenschaften in tests/test_presets.py festgehalten)
MINI_SEED = 223        # 3 x 2: (5, 2), (1, 4), (6, 3) = der einzelne Blocker aus Stück 2 bis auf Vertauschen der Stapel: Baum 9 Knoten, 4 Zustände
EVERYDAY_SEED = 12     # 3 x 3, Platz 2: Baum 229 Knoten, 20 Zustände (18 bis auf Stapelvertauschen), IDA* 11 Knoten
REPEAT_SEED = 3        # 4 x 3, Platz 2: Baum 2 703 457 Knoten, nur 1 028 Zustände (619), IDA* 26 Knoten
TAIL_SEED = 1          # 5 x 4, Platz 2: IDA* 400 339 Knoten, mit Merken 8 975 (das 44,6-Fache); mehr als 100 000 Zustände, der Baum wird nicht gezählt
MINI_BAY = ((1, 4), (5, 2), (6, 3))                       # die Mini-Bucht des ausgeschriebenen Zustandsgraphen (Stück 2: einzelner Blocker), Höchsthöhe 4
MINI_HEIGHT = 4
COUNTER_BAY = ((3, 6), (2, 4), (1, 5))                    # das Gegenbeispiel aus Stück 1, Höchsthöhe 4
COUNTER_HEIGHT = 4

PRESETS = {
    "Alltag (3 Stapel, 3 Lagen)": {"stacks": 3, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EVERYDAY_SEED},
    "Die Mini-Bucht": {"stacks": 3, "layers": 2, "extra": DEFAULT_EXTRA, "seed": MINI_SEED},
    "Fast nur Wiederholung (4 Stapel, 3 Lagen)": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": REPEAT_SEED},
    "Wo das Merken hilft (5 Stapel, 4 Lagen)": {"stacks": 5, "layers": 4, "extra": DEFAULT_EXTRA, "seed": TAIL_SEED},
}
PRESET_HELP = {
    "Alltag (3 Stapel, 3 Lagen)": "9 Container: Baum 229 Knoten, aber nur 20 verschiedene Zustände; IDA* braucht 11 Knoten, das Merken ändert daran nichts.",
    "Die Mini-Bucht": "6 Container, ein einziger Blocker: Baum 9 Knoten, 4 Zustände, einer davon wird zweimal erreicht.",
    "Fast nur Wiederholung (4 Stapel, 3 Lagen)": "12 Container: der Baum hat rund 2,7 Millionen Knoten und nur 1 028 verschiedene Zustände; IDA* braucht 26 Knoten.",
    "Wo das Merken hilft (5 Stapel, 4 Lagen)": "20 Container: IDA* braucht rund 400 000 Knoten, mit Merken rund 9 000. Der Baum wird nicht gezählt (zu viele Zustände); die Berechnung dauert rund 20 Sekunden.",
}
