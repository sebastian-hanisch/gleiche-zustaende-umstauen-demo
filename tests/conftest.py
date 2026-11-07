"""Gemeinsame Fixtures: die Mini-Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Die Mini-Bucht (einzelner Blocker aus Stück 2): 3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3). Untergrenze 1, Optimum 2.

    Handrechnung der Zustände (nach den kostenlosen Abrufen): A = (1, 4) | (5, 2) | (6, 3) (Wurzel). Die 4 auf Stapel 2: B = () | (5, 2, 4) | (6, 3) (die 1 wird abgerufen).
    Die 4 auf Stapel 3: C = () | (5) | (6, 3, 4) (die 1 und die 2 werden abgerufen). Von B: die 4 auf Stapel 1 oder Stapel 3: leere Bucht (alles wird abgerufen), bzw. C.
    Von C: die 4 auf Stapel 1 oder Stapel 2: leere Bucht. Das sind 9 Knoten (A, B, leer, C, leer, leer, C, leer, leer) und **4 verschiedene Zustände**: C wird zweimal erreicht
    (aus A mit 1 Hub, aus B mit 2 Hüben), die leere Bucht fünfmal."""
    return ((1, 4), (5, 2), (6, 3)), 4


@pytest.fixture
def counter():
    """Das Gegenbeispiel aus Stück 1: (3, 6), (2, 4), (1, 5), Höchsthöhe 4. Untergrenze 3, Optimum 4. Der Baum der vollen Aufzählung hat 153 Knoten und 77 Blätter,
    aber nur 25 verschiedene Zustände (16 bis auf Vertauschen der Stapel). IDA* braucht 15 Knoten (3 + 12), mit Merken ebenfalls (Tabellen 1 und 7)."""
    return ((3, 6), (2, 4), (1, 5)), 4
