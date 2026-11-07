# Gleiche Zustände: Zustandsmerken und Symmetriebruch beim Umstauen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-gleiche-zustaende-umstauen-demo.streamlit.app/)** -->

Sechstes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. [Stück 4](https://sebastianhanisch-knotenexplosion-umstauen-demo.streamlit.app/) zeigt, wie die Suche über alle Hubfolgen explodiert, [Stück 5](https://sebastianhanisch-iterative-vertiefung-umstauen-demo.streamlit.app/), wie die Untergrenze sie klein macht. Dieses Stück fragt: **Wie viele Knoten des Suchbaums sind dieselbe Bucht?** Die Demo **zählt** den Baum der vollen Aufzählung, ohne ihn zu durchlaufen, stellt ihn den **verschiedenen Zuständen** gegenüber, trennt die Wiederholung in **Mehrfachwege** und **Stapelsymmetrie** und misst, was **Zustandsmerken** und **Symmetriebruch** für IDA\* bringen.

## Warum dieses Problem

Die Hypothese lag nahe: „Gleiche Konfigurationen zusammenfassen halbiert die Knotenzahl oder besser.“ Die Messung widerlegt sie **zweimal**: Für den Baum ohne Untergrenze ist die Wiederholung um Größenordnungen größer als „halbiert“ (der Baum hat bei 4 × 3 im Median 39 414 Knoten, aber nur 88 verschiedene Zustände), für IDA\* mit Untergrenze bringt das Merken im Median **nichts** (1,00- bis 1,33-Fache). Und die Wiederholung kommt fast nur aus **Mehrfachwegen**, nicht aus Symmetrie (Stapelvertauschen: 1,0- bis 1,3-Fache). **Die Untergrenze und das Zustandsmerken beseitigen dieselbe Wiederholung.**

## Modell

Eine Bucht aus *s* Stapeln mit Höchsthöhe *H* = Lagen + Platz (Platz 1 bis 4, Standard 2), anfangs jeder Stapel gleich hoch gefüllt, Abrufnummern 1 bis *N* zufällig verteilt (Familie wie in Stück 1 bis 5, gleiche festen Buchten). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; **restricted**: nur der Blocker über der nächsten abzurufenden Nummer wird bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt.

**Suchbaum** wie in Stück 4 und 5: Ein **Knoten** ist ein Aufruf der Suche, ein **Blatt** eine leere Bucht. Ein **Zustand** ist die Bucht nach den kostenlosen Abrufen; verschiedene Hubfolgen können im selben Zustand enden. Weil jede Nummer nur einmal vorkommt, sind nur **leere** Stapel einander gleich. Formal im Expander „📐 Mathematische Formulierung“.

## Methodik

- **Gezählt, nicht durchlaufen:** Die Knoten (und Blätter) des Baums der vollen Aufzählung werden mit einer gemerkten Zählung bestimmt (Knoten eines Zustands = 1 + Knoten seiner Kinder); so steht auch bei Milliarden Knoten die exakte Zahl da. Live bis 100 000 verschiedene Zustände, in den Tabellen bis 3 Mio.
- **Zustandsmerken:** je Zustand die kleinste Hubzahl *g* merken, mit der er bearbeitet wurde; kommt er mit *g'* ≥ *g* wieder, wird er nicht noch einmal bearbeitet (er zählt als Knoten und als Treffer). Bei IDA\* je Budgetstufe zurückgesetzt. **Roh** (Stapel in fester Reihenfolge) und **kanonisch** (Stapel sortiert, also bis auf Stapelvertauschen).
- **Symmetriebruch:** von mehreren leeren Zielstapeln nur den ersten probieren.
- **Sieben Verfahren live:** IDA\* (Stück 5), IDA\* mit Symmetriebruch, IDA\* mit Merken roh und kanonisch, volle Aufzählung, Branch and Bound ohne Untergrenze und Branch and Bound mit Untergrenze, die letzten drei mit kanonischem Merken. Reihenfolge der Kinder immer „engste Passung zuerst“.
- **Knotenlimit:** Läufe über 500 000 Knoten (live) beziehungsweise 1 000 000 (vorberechnet) werden abgebrochen und als „über Limit“ gezählt; gezählt werden Knoten, keine Sekunden.
- **Abschnitte der App:** Ergebnis (Baum gegen Zustände, sieben Verfahren, live); die Zustände der Mini-Bucht und des Gegenbeispiels von Hand; Tabelle „wie viele Zustände sind gleich“; Merken und Symmetriebruch für IDA\*; Merken ohne Untergrenze; Größe des Zustandsraums. Die Tabellen sind vorberechnet (`gzu_bands.json`, erzeugt von `generate_precomputed.py`, rund 20 bis 30 Minuten auf mehreren Kernen).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den festen Buchten 0 bis (Zahl der Buchten − 1) je Zelle bei Platz 2 (Python-Zufallsfolge, `random.shuffle`, **dieselben Buchten wie in Stück 4 und 5**), nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_gleiche_zustaende_umstauen.py`.

**A: Wie viele Zustände sind gleich?** (volle Aufzählung aus Stück 4, gezählt; Median / Maximum über die Buchten)

| Zelle (Buchten) | Knoten des Baums | verschiedene Zustände | bis auf Stapelvertauschen | Knoten / Zustände (Median, Maximum) | Zustände roh / kanonisch (Median, Maximum) |
|---|---|---|---|---|---|
| 3 × 2 (100) | 9 / 161 | 4 / 26 | 4 / 16 | 2,2 (6,2) | 1,00 (1,62) |
| 4 × 2 (100) | 67 / 20 867 | 8,5 / 276 | 7 / 74 | 7,7 (80) | 1,00 (3,73) |
| 3 × 3 (100) | 230 / 13 427 | 23,5 / 456 | 22 / 375 | 10 (50) | 1,08 (1,70) |
| 5 × 2 (60) | 1 785 / 2 255 473 | 24,5 / 613 | 17 / 112 | 77 (3 679) | 1,20 (5,47) |
| 4 × 3 (40) | 39 413,5 / 158 791 356 | 87,5 / 12 628 | 65,5 / 3 527 | 505 (22 104) | 1,18 (5,00) |
| 3 × 4 (40) | 18 163,5 / 696 375 | 175 / 3 112 | 135 / 2 841 | 90 (466) | 1,12 (2,28) |
| 5 × 3 (20) | 159 754 794 / 21 722 640 688 069 | 665 / 331 855 | 462 / 49 715 | 185 826 (117 593 698) | 1,33 (9,91) |
| 4 × 4 (30) | 1 930 893 700 / 21 298 033 897 566, 1 über dem Limit | 1 948 / 289 675 | 1 590 / 230 571 | 521 892 (87 580 805) | 1,17 (2,99) |

„Über dem Limit“: eine Bucht bei 4 × 4 hat mehr als 3 Millionen Zustände und fehlt in allen Spalten (29 gezählte Buchten). **Korrektur gegenüber dem Plan:** Die Phase 0 rechnete ohne Limit und nahm diese Bucht mit (Median 2 042 586 564 Knoten, 2 183 Zustände); mit dem Limit der Demo sind es 1 930 893 700 und 1 948.

**B: IDA\* (Stück 5) mit Symmetriebruch und Zustandsmerken** (Knoten Median / Mittel / Maximum, Limit 1 000 000, kein Lauf darüber)

| Zelle (Buchten) | IDA\* ohne | mit Symmetriebruch | Merken roh | Merken bis auf Stapelvertauschen |
|---|---|---|---|---|
| 3 × 2 (100) | 3 / 4 / 15 | 3 / 4 / 15 | 3 / 4 / 15 | 3 / 4 / 15 |
| 4 × 2 (100) | 3 / 4 / 10 | 3 / 4 / 10 | 3 / 4 / 10 | 3 / 4 / 10 |
| 3 × 3 (100) | 16 / 25 / 144 | 16 / 25 / 144 | 16 / 22 / 123 | 16 / 22 / 123 |
| 5 × 2 (60) | 4 / 6 / 12 | 4 / 6 / 12 | 4 / 6 / 12 | 4 / 6 / 12 |
| 4 × 3 (40) | 12 / 33 / 360 | 12 / 33 / 360 | 12 / 29 / 281 | 12 / 29 / 281 |
| 3 × 4 (40) | 65 / 121 / 672 | 65 / 119 / 672 | 53 / 93 / 478 | 53 / 92 / 478 |
| 5 × 3 (20) | 18,5 / 33 / 218 | 18,5 / 33 / 218 | 18,5 / 30 / 170 | 18,5 / 30 / 170 |
| 4 × 4 (30) | 291 / 1 106 / 11 739 | 291 / 1 104 / 11 739 | 188 / 656 / 7 168 | 188 / 655 / 7 168 |
| 5 × 4 (20) | 521,5 / 50 391 / 487 765 | 494 / 49 619 / 473 083 | 434 / 5 265 / 62 204 | 415 / 4 980 / 56 710 |

| Zelle | ohne / Symmetriebruch (Median, Mittel, Maximum, Buchten mit Gewinn) | ohne / Merken (Median, Mittel, Maximum, Buchten mit Gewinn) | Treffer des Merkens (Median) | größte Tabelle (Median, Maximum) |
|---|---|---|---|---|
| 3 × 2 | 1,00, 1,00, 1,0, 0 % | 1,00, 1,00, 1,0, 0 % | 0,0 % | 2, 7 |
| 4 × 2 | 1,00, 1,00, 1,0, 0 % | 1,00, 1,00, 1,0, 0 % | 0,0 % | 2, 5 |
| 3 × 3 | 1,00, 1,00, 1,1, 1 % | 1,00, 1,07, 1,8, 30 % | 0,0 % | 5, 40 |
| 5 × 2 | 1,00, 1,00, 1,0, 0 % | 1,00, 1,00, 1,0, 0 % | 0,0 % | 3, 6 |
| 4 × 3 | 1,00, 1,00, 1,0, 0 % | 1,00, 1,05, 1,6, 20 % | 0,0 % | 5, 57 |
| 3 × 4 | 1,00, 1,01, 1,3, 5 % | 1,17, 1,23, 2,0, 75 % | 4,4 % | 16, 117 |
| 5 × 3 | 1,00, 1,00, 1,0, 0 % | 1,00, 1,02, 1,3, 10 % | 0,0 % | 6,5, 35 |
| 4 × 4 | 1,00, 1,00, 1,0, 3 % | 1,33, 1,50, 3,7, 73 % | 4,4 % | 43,5, 1 656 |
| 5 × 4 | 1,00, 1,01, 1,1, 15 % | 1,17, 4,32, 45, 70 % | 1,9 % | 77, 10 395 |

Verhältnisse je Bucht (Knoten ohne / Knoten mit), dann Median, Mittel, Maximum und Anteil der Buchten mit Gewinn. Merken roh und kanonisch unterscheiden sich in den Medianen der Knoten nur bei 5 × 4 (434 gegen 415), in den Medianen der Verhältnisse kaum (1,15 gegen 1,17).

**C1: Merken ohne Untergrenze** (kanonisch; Median / Mittel / Maximum der Knoten, Treffer zählen mit, Limit 1 000 000)

| Zelle (Buchten) | volle Aufzählung + Merken | B&B ohne UG + Merken | B&B mit UG + Merken | IDA\* (ohne Merken) | IDA\* + Merken |
|---|---|---|---|---|---|
| 3 × 3 (100) | 43 / 105 / 777 | 26 / 40 / 257 | 13 / 18 / 99 | 16 / 25 / 144 | 16 / 22 / 123 |
| 4 × 3 (40) | 195,5 / 1 372 / 11 935 | 81,5 / 292 / 2 504 | 16 / 30 / 233 | 12 / 33 / 360 | 12 / 29 / 281 |
| 3 × 4 (40) | 293 / 861 / 6 016 | 120 / 225 / 1 083 | 38,5 / 56 / 232 | 65 / 121 / 672 | 53 / 92 / 478 |
| 5 × 3 (20) | 2 047 / 34 052 / 363 550 | 539 / 2 188 / 16 418 | 31 / 40 / 158 | 18,5 / 33 / 218 | 18,5 / 30 / 170 |
| 4 × 4 (30) | 5 731 / 151 941 / 895 575, 1 über Limit | 2 188 / 23 681 / 268 702 | 202,5 / 585 / 5 489 | 291 / 1 106 / 11 739 | 188 / 655 / 7 168 |

**C2: Wie weit trägt der Zustandsraum?** (alle verschiedenen Zustände, Breitensuche, Median / Maximum über je **5 Buchten**, Limit 3 Mio.): 3 × 3 29 / 111, 4 × 3 133 / 12 628, 5 × 3 1 022 / 331 855, 6 × 3 2 148 / 555 370, 4 × 4 2 108 / 12 414 (1 von 5 über dem Limit), 5 × 4 380 533 / 627 271 (1 von 5 über dem Limit).

| Frage | Befund |
|---|---|
| **Wie viele Zustände sind gleich?** | Der Baum der vollen Aufzählung hat im Median das **2,2- bis 521 892-Fache** der Knoten gegenüber den verschiedenen Zuständen: 2,2 bei 3 × 2, 7,7 bei 4 × 2, 10 bei 3 × 3, 77 bei 5 × 2, 90 bei 3 × 4, 505 bei 4 × 3, 185 826 bei 5 × 3, 521 892 bei 4 × 4. Bei 4 × 3 hat der Baum 39 414 Knoten und 88 Zustände, bei 5 × 3 160 Millionen und 665, bei 4 × 4 zwei Milliarden und 1 948. |
| **Woher kommt die Wiederholung?** | Fast nur aus **Mehrfachwegen** (derselbe Zustand auf verschiedenen Wegen, zum Beispiel ein Container zuerst auf Stapel A und später auf B oder gleich auf B). Die **Stapelsymmetrie** erklärt im Median nur das 1,00- bis 1,33-Fache (Maximum je Zelle 1,62 bis 9,91). |
| **Was bringt der Symmetriebruch (leere Stapel)?** | Für IDA\* im Median **nichts** (1,00 in allen neun Zellen), im Mittel höchstens das 1,01-Fache, im Maximum 1,30 (3 × 4); in 0 bis 15 % der Buchten ein Gewinn. Für die volle Aufzählung dagegen viel (Gegenbeispiel aus Stück 1: 153 auf 87 Knoten). |
| **Was bringt das Zustandsmerken für IDA\*?** | Im Median 1,00 bis 1,33-fach (1,00 in sechs von neun Zellen, 1,17 bei 3 × 4 und 5 × 4, 1,33 bei 4 × 4), im Mittel bis 1,50 bei 4 × 4, **aber 4,32 bei 5 × 4**, im Maximum **44,6 bei 5 × 4** (Bucht 1: 400 339 gegen 8 975 Knoten). Der Gewinn liegt im **Schwanz**. Treffer des Merkens: im Median höchstens 4,4 % der Knoten. |
| **Ersetzt das Merken die Untergrenze?** | Nein. Branch and Bound **ohne** Untergrenze mit Merken braucht im Median das **1,7- bis 25-Fache** der Knoten von IDA\* ohne Merken (3 × 3: 1,7, 4 × 3: 6,2, 3 × 4: 2,0, 5 × 3: 25, 4 × 4: 14), die volle Aufzählung mit Merken das 2,9- bis 100-Fache. Branch and Bound **mit** Untergrenze und Merken liegt gleichauf: IDA\* ohne Merken braucht das 0,56- bis 1,75-Fache seiner Knoten. Untergrenze und Merken beseitigen **dieselbe** Wiederholung; wer die Untergrenze hat, braucht das Merken im Median nicht. |
| **Wie groß wird die Tabelle des Merkens?** | Bei IDA\* im Median 2 bis 77 Zustände (Maximum 5 bis 10 395), bei der Aufzählung mit Merken im Median 21 bis 1 589 (Maximum 374 bis 230 570). |
| **Wie weit trägt der Zustandsraum?** | Er ist klein und wächst mit einem **schweren Schwanz**: Median 29 Zustände bei 3 × 3, 1 022 bei 5 × 3, 2 108 bei 4 × 4, 380 533 bei 5 × 4; je eine von fünf Buchten bei 4 × 4 und 5 × 4 hat mehr als 3 Millionen. Sehr grob (5 Buchten). |
| **Die Mini-Bucht** | (1, 4), (5, 2), (6, 3), Höchsthöhe 4: der Baum hat **9 Knoten und 4 verschiedene Zustände**: die Ausgangsbucht, `() \| (5, 2, 4) \| (6, 3)` (die 4 auf Stapel 2), `() \| (5) \| (6, 3, 4)` (die 4 auf Stapel 3) und die leere Bucht. Der dritte Zustand wird **zweimal** erreicht (aus der Ausgangsbucht mit 1 Hub, aus dem zweiten Zustand mit 2 Hüben), die leere Bucht fünfmal. IDA\* braucht mit und ohne Merken 6 Knoten. Die volle Aufzählung mit Merken in der Reihenfolge der engsten Passung: 7 Knoten, 3 Blätter, 1 Treffer (in der Reihenfolge der Stapelnummern kommt der Zustand zuerst über den längeren Weg und wird erneut bearbeitet: 9 Knoten, kein Treffer). |
| **Das Gegenbeispiel aus Stück 1** | (3, 6), (2, 4), (1, 5): der Baum hat **153 Knoten, 77 Blätter und 25 verschiedene Zustände (16 bis auf Stapelvertauschen)**; IDA\* 15 Knoten mit und ohne Merken (Tabelle 1 und 7); volle Aufzählung mit Merken (bis auf Stapelvertauschen) 31 bis 71 Knoten je Reihenfolge, Branch and Bound ohne Untergrenze mit Merken 21 statt 27, mit Untergrenze 17 wie ohne. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (3 × 3, Bucht 12: Baum 229 Knoten, 20 Zustände (18), IDA\* 11 Knoten, mit Merken 11), „Die Mini-Bucht“ (3 × 2, Bucht 223: 9 Knoten, 4 Zustände), „Fast nur Wiederholung“ (4 × 3, Bucht 3: Baum 2 703 457 Knoten, 1 028 Zustände (619), IDA\* 26 Knoten), „Wo das Merken hilft“ (5 × 4, Bucht 1: IDA\* 400 339 Knoten, mit Merken 8 975, das 44,6-Fache; der Baum wird nicht gezählt, mehr als 100 000 Zustände; die Berechnung dauert rund 20 Sekunden).

**Zeit (nur diese Einzelmessung, Windows, ein Lauf, Prototyp der Phase 0 in Python, nicht die Demo und nicht in der CI):** IDA\* ohne gegen mit kanonischem Merken, Gesamtzeit über die Buchten: 3 × 3 1,15-mal schneller, 4 × 4 1,45-mal, 5 × 4 **8,8-mal** (Knoten insgesamt 10,1-mal weniger). Je 1000 Knoten kostet das Merken rund 15 bis 20 % mehr (19 gegen 20, 25 gegen 29, 24 gegen 28 ms). Im Median je Bucht kein Unterschied (5 × 4: 10,8 gegen 11,3 ms): **die Zeit gewinnt der Schwanz.**

## Ehrliche Grenzen

- **Knoten statt Zeit.** Das Merken kostet pro Knoten Rechenzeit; die Zeitzahlen oben sind eine Einzelmessung eines Prototyps, keine Demo-Messung.
- **Nur die Symmetrie der Stapelreihenfolge.** Stärkere Formen (Dominanzregeln, Vertauschbarkeit unabhängiger Hübe) sind nicht untersucht.
- **Der Baum wird live nur bis 100 000 Zustände gezählt** (darüber „nicht gezählt“); die Tabellen reichen bis 4 × 4, 5 × 4 fehlt in Tabelle A und C1.
- **Der Zustandsraum ist grob gemessen:** 5 Buchten je Zelle, bei 4 × 4 und 5 × 4 je eine über 3 Millionen Zuständen. Der Median sagt wenig über den schweren Schwanz.
- **Große Zellen mit wenigen Buchten:** 5 × 3 mit 20, 4 × 4 mit 30, 5 × 4 mit 20 Buchten; die Maxima (zum Beispiel das 117-Millionen-Fache bei 5 × 3) sind Einzelwerte.
- **Nur restricted, nur volle Buchten mit gleich hohen Stapeln, Platz 2 in den Tabellen.** Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich Baum und Zustandsraum.
- **„Untergrenze und Merken ersetzen sich“ ist eine Messung** an neun beziehungsweise fünf Zellen, kein Satz.
- **Zahlen aus Zufallsbuchten:** feste Buchten aus der Zufallsfolge von Python (`random.shuffle`), keine Messung an einem echten Terminal oder Lager; die CI prüft die Zahlen unter Linux.
- **Die Literatur zu Transpositionstabellen und Symmetriebrechung beim Relocation-Problem wurde nicht gelesen;** die Verfahren und die Zählung sind hier selbst gebaut.

## Verifikation

- **Kern:** Zustände, Besuche und Zählung gegen Handzählung an zwei Mini-Buchten (9 Knoten und 4 Zustände, 153 und 25); Knoten, Treffer und Tabellengröße jedes Verfahrens an der Mini-Bucht von Hand; die Tabellen der Stufen addieren sich; sortierte Bucht hat genau einen Knoten; das Knotenlimit stoppt genau beim Überschreiten (auch bei IDA\* mitten in einer Stufe); Zustandslimit der Zählung.
- **Orakel:** das Optimum jedes Verfahrens in jeder Reihenfolge mit jedem Merken und Symmetriebruch gegen eine **Breitensuche** über alle Zustände (3 × 2, 4 × 2, 3 × 3); die Zahl der verschiedenen Zustände gegen eine **eigene Erreichbarkeitssuche** (3 × 2 bis 4 × 3); Knoten und Blätter der vollen Aufzählung gegen einen **echten Durchlauf ohne Merken** (alle 3 × 2-Buchten, 4 × 2, 3 × 3) und die Besuche je Zustand gegen `state_visits`; Knoten, Treffer und Tabellengrößen jeder Tiefensuche und jeder IDA\*-Stufe gegen eine **zweite, iterative Fassung** mit eigenem Stapel und eigener Zählung der Blocker; die **Kostengleichheit** bei Vertauschen der Stapel.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (Tabellen A, B, C1, C2 und die Aussagen darüber); kleine Zellen gegen eine frische Rechnung (`tests/test_presets.py`).
- **Verdikte:** reine Funktionen, jede Schwelle (Wiederholung 2 und 10, Merken 1,25 und 2,0, Ersatz 1,5) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, Zustandstabelle, Tabellenzeilen, Permalink), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Reglerwirkung), Footer, Laufzeit-Importe.
- **Abbildungen:** Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, fehlende Mediane übersprungen.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `gzu_bands.json` (Baum, IDA\*, Merken ohne Untergrenze, Zustandsraum) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `gzu_algorithm.py` | Kern: Tiefensuche mit Merken und Symmetriebruch, Zählung des Baums und der Zustände, Besuche je Zustand |
| `gzu_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `gzu_constants.py` | Regler-Grenzen, Limits, Zellen, Farben, Sonderbuchten, Presets |
| `gzu_evaluation.py` | Analyse einer Bucht, Stichproben, Verdikte (reine Funktionen) |
| `gzu_layout.py` | Fester Kopf (Stylesheet), Tabellen scrollen im eigenen Rahmen |
| `gzu_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `gzu_scenario.py` | Buchten (volle Buchten, Zufallsbuchten) |
| `gzu_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Stärkere Symmetrie und Dominanzregeln.**
- **Eine Zeitmessung in der App oder der CI:** nur Knotenzahlen, weil die Rechenzeit je Gerät schwankt.
- **Die Zählung des Baums bei 5 × 4 und mehr als 100 000 Zuständen live.**
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

123 Tests, rund eine Minute.

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
