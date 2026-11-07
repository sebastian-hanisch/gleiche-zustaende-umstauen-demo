"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import gzu_algorithm as A
import gzu_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = A.INF
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_counts(rows):
    """Knoten des Baums gegen verschiedene Zustände als Balken (logarithmische Achse). `rows`: Zeilen aus count_rows."""
    fig = go.Figure(go.Bar(x=[r["name"] for r in rows], y=[r["value"] for r in rows], marker_color=[C.COLOR_LINES[0], C.COLOR_LINES[1], C.COLOR_LINES[3]][:len(rows)],
                           text=[f"{r['value']:,}".replace(",", " ") for r in rows], textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{text}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Anzahl (logarithmisch)", type="log")
    return _base(fig, height=300)


def build_nodes(rows):
    """Knoten je Verfahren als Balken (logarithmische Achse); Läufe am Knotenlimit sind rot und als „mehr als“ beschriftet. `rows`: Zeilen aus result_rows."""
    fig = go.Figure(go.Bar(
        x=[C.VARIANT_SHORT[r["variant"]] for r in rows], y=[r["nodes"] for r in rows],
        marker_color=[C.COLOR_CAPPED if r["capped"] else C.COLOR_VARIANT[r["variant"]] for r in rows],
        text=[r["nodes_text"] for r in rows], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{text} Knoten<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten (logarithmisch)", type="log")
    return _base(fig, height=340)


def build_tree_cells(cells):
    """Knoten des Baums, verschiedene Zustände (roh) und bis auf Stapelvertauschen je Zelle, Median (logarithmisch). `cells`: {Zellname: tree_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("Knoten des Baums", "nodes", C.COLOR_LINES[0]), ("verschiedene Zustände", "raw", C.COLOR_LINES[1]), ("bis auf Stapelvertauschen", "canon", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=names, y=[cells[n][key]["median"] for n in names], name=label, marker_color=color, hovertemplate="%{x}: Median %{y:,.1f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Median (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_gain(cells):
    """Gewinn des Merkens für IDA* je Zelle: Median, Mittel und Maximum des Verhältnisses Knoten ohne / mit Merken (logarithmisch). `cells`: {Zellname: ida_stats}."""
    names = [n for n in cells if cells[n]["canon"]["median"] is not None]
    fig = go.Figure()
    for label, key, color in (("Median", "median", C.COLOR_LINES[1]), ("Mittel", "mean", C.COLOR_LINES[2]), ("Maximum", "max", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=names, y=[cells[n]["canon"][key] for n in names], name=label, marker_color=color, hovertemplate="%{x}: %{y:.2f}-fach<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten ohne / mit Merken (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_memo(cells):
    """Merken ohne Untergrenze je Zelle (logarithmisch): Median des Verhältnisses Knoten der Tiefensuche mit Merken / Knoten von IDA* ohne Merken für die volle Aufzählung,
    Branch and Bound ohne und mit Untergrenze. `cells`: {Zellname: memo_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("volle Aufzählung mit Merken", "r_enum+canon", C.COLOR_VARIANT[("enum", "canon", False)]), ("B&B ohne Untergrenze mit Merken", "r_bb+canon", C.COLOR_VARIANT[("bb", "canon", False)]),
                              ("B&B mit Untergrenze mit Merken", "r_bblb+canon", C.COLOR_VARIANT[("bblb", "canon", False)])):
        fig.add_trace(go.Bar(x=names, y=[1 / cells[n][key]["median"] for n in names], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:.2f}-fach<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten / Knoten von IDA* (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_space(cells):
    """Verschiedene Zustände des ganzen Zustandsgraphen je Zelle, Median über wenige Buchten (logarithmisch); Zellen ohne fertige Bucht fehlen. `cells`: {Zellname: space_stats}."""
    names = [n for n in cells if cells[n]["raw"]["median"] is not None]
    fig = go.Figure()
    for label, key, color in (("roh", "raw", C.COLOR_LINES[1]), ("bis auf Stapelvertauschen", "canon", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=names, y=[cells[n][key]["median"] for n in names], name=label, marker_color=color, hovertemplate="%{x}: Median %{y:,.0f} Zustände<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Zustände (logarithmisch)", type="log")
    return _base(fig, height=340)
