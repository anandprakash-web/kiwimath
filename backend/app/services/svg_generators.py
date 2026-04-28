"""
SVG generators for Kiwimath visual questions.

Each generator is a function that takes a params dict and returns an SVG string.
The app displays the SVG inline — no image hosting needed, and it scales crisply.

Shipped:
    - object_row_with_cross_out: row of emoji objects, last K crossed out
    - dice_face:                 standard 1-6 pip die face
    - triangle_subdivision:      big triangle with internal lines (counting triangles)
    - grid_colored:              NxN grid with specified cells colored

Next generators planned: cube_stack, number_strip, coin_pile.

Added (batch 2):
    - ten_frame:        classic 2x5 ten-frame with filled dots
    - number_line:      horizontal number line with optional highlight
    - bar_model:        Singapore-style part-whole bar
    - comparison_bars:  two bars for quantity comparison
    - clock_face:       analog clock (hour and half-hour)
    - pattern_strip:    repeating pattern of colored shapes
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Any, Callable, Dict, List, Optional


class UnknownGeneratorError(ValueError):
    pass


# Simple emoji-style icons for each object — swap with real SVG icons later.
_OBJECT_ICONS: Dict[str, str] = {
    "balloons":  "🎈",
    "apples":    "🍎",
    "stickers":  "⭐",
    "marbles":   "🔵",
    "cookies":   "🍪",
    "pencils":   "✏️",
    "laddoos":   "🟡",
}


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def object_row_with_cross_out(params: Dict[str, Any]) -> str:
    """
    Render a row of emoji objects, with the last `cross_out` of them crossed out.

    Params:
        count_from: int — total number of objects
        cross_out:  int — how many at the end to cross out
        object:     str — key into _OBJECT_ICONS (optional, default balloon)
    """
    # Alias: total -> count_from, remove -> cross_out, remaining -> compute cross_out
    _total_raw = params.get("count_from") or params.get("total")
    n = int(_total_raw) if _total_raw is not None else 5
    _cross_raw = params.get("cross_out") or params.get("remove")
    if _cross_raw is not None:
        k = int(_cross_raw)
    elif params.get("remaining") is not None and _total_raw is not None:
        k = int(_total_raw) - int(params["remaining"])
    else:
        k = 0
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")

    if n <= 0:
        n = 1
    k = max(0, min(k, n))

    cell_w = 50
    pad = 10
    width = n * cell_w + pad * 2
    height = 80

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} {_escape(obj_key)}, {k} crossed out">'
    ]
    for i in range(n):
        cx = pad + i * cell_w + cell_w // 2
        cy = height // 2
        parts.append(
            f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" '
            f'font-size="32">{icon}</text>'
        )
        if i >= n - k:
            # Draw a red X over this object.
            x1 = cx - 18
            y1 = cy - 18
            x2 = cx + 18
            y2 = cy + 18
            parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="#e53935" stroke-width="3" stroke-linecap="round"/>'
            )
            parts.append(
                f'<line x1="{x2}" y1="{y1}" x2="{x1}" y2="{y2}" '
                f'stroke="#e53935" stroke-width="3" stroke-linecap="round"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# dice_face — a standard 1-6 pip die.
# ---------------------------------------------------------------------------

# Pip positions on a 3x3 grid (column, row) — standard die face layouts.
_DICE_PIPS: Dict[int, List[tuple]] = {
    1: [(1, 1)],
    2: [(0, 0), (2, 2)],
    3: [(0, 0), (1, 1), (2, 2)],
    4: [(0, 0), (2, 0), (0, 2), (2, 2)],
    5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)],
}


def dice_face(params: Dict[str, Any]) -> str:
    """Render a single die face with the given number of dots (1–6)."""
    dots = int(params.get("dots", 1))
    dots = max(1, min(6, dots))

    size = 140
    pad = 20
    face_size = size - 2 * pad
    pip_r = 12
    # Place pips on a 3x3 grid.
    step = face_size / 4

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'role="img" aria-label="Die face showing {dots}">',
        f'<rect x="{pad}" y="{pad}" width="{face_size}" height="{face_size}" '
        f'rx="18" ry="18" fill="#FFFFFF" stroke="#424242" stroke-width="4"/>',
    ]
    for (col, row) in _DICE_PIPS[dots]:
        cx = pad + step + col * step
        cy = pad + step + row * step
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{pip_r}" fill="#212121"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# triangle_subdivision — a triangle cut into sub-triangles by internal lines.
# ---------------------------------------------------------------------------


def triangle_subdivision(params: Dict[str, Any]) -> str:
    """
    Render a triangle with internal subdivisions. Used for "count all the
    triangles you can see" questions.

    Params:
        side: number of rows for a full equilateral subdivision grid.
              side=2 → 4 small triangles (3 up + 1 down).
              side=3 → 9 small triangles (6 up + 3 down).
              side=4 → 16 small triangles (10 up + 6 down).
        layout: one of the preset layouts (legacy, used if side not given).
            - "basic_3":   Big triangle with a horizontal line at mid-height.
            - "basic_4":   Big triangle divided into 4 sub-triangles (= side 2).
            - "fan":       Big triangle with 2 lines from apex to base.
    """
    W, H = 240, 200
    # Apex at top-center, base on bottom corners
    Apex = (W / 2, 20)
    BL = (30, H - 20)
    BR = (W - 30, H - 20)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="Triangle figure">',
        # Outer triangle
        f'<polygon points="{Apex[0]},{Apex[1]} {BL[0]},{BL[1]} {BR[0]},{BR[1]}" '
        f'fill="none" stroke="#1976D2" stroke-width="3" stroke-linejoin="round"/>',
    ]

    def line(p1, p2):
        return (f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
                f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                f'stroke="#1976D2" stroke-width="2" stroke-linecap="round"/>')

    def lerp(p1, p2, t):
        """Linear interpolation between two points."""
        return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)

    # Check for side-based subdivision first
    side = params.get("side")
    if side is not None:
        n = _safe_int(side, 2)
        n = max(2, min(n, 6))  # clamp 2-6

        # Build grid of vertices.
        # Row r (0 = apex, n = base) has (r+1) vertices evenly spaced
        # between the left edge and right edge of the triangle at that row.
        rows = []
        for r in range(n + 1):
            t = r / n  # fraction from apex to base
            left = lerp(Apex, BL, t)
            right = lerp(Apex, BR, t)
            row_pts = []
            cols = r + 1
            for c in range(cols):
                if cols == 1:
                    row_pts.append(left)
                else:
                    row_pts.append(lerp(left, right, c / (cols - 1)))
            rows.append(row_pts)

        # Draw all internal edges (skip the 3 outer edges of the big triangle).
        drawn = set()

        def edge_key(p1, p2):
            return (round(p1[0], 1), round(p1[1], 1),
                    round(p2[0], 1), round(p2[1], 1))

        def draw_edge(p1, p2):
            k1 = edge_key(p1, p2)
            k2 = edge_key(p2, p1)
            if k1 not in drawn and k2 not in drawn:
                drawn.add(k1)
                parts.append(line(p1, p2))

        for r in range(n):
            for c in range(len(rows[r])):
                # Downward-pointing triangle edges: connect row[r][c] to
                # row[r+1][c] and row[r+1][c+1], plus horizontal row[r+1][c]→[c+1]
                draw_edge(rows[r][c], rows[r + 1][c])
                draw_edge(rows[r][c], rows[r + 1][c + 1])
            # Horizontal edges within row r+1
            for c in range(len(rows[r + 1]) - 1):
                draw_edge(rows[r + 1][c], rows[r + 1][c + 1])
            # Upward-pointing (inverted) triangle edges within this row band
            if r < n - 1:
                pass  # Already covered by the diagonal edges above

        parts.append("</svg>")
        return "".join(parts)

    # Legacy preset layouts
    layout = params.get("layout") or params.get("mode")
    if not layout:
        _count = params.get("count")
        if _count is not None:
            _c = _safe_int(_count, 3)
            if _c <= 3:
                layout = "basic_3"
            elif _c <= 4:
                layout = "basic_4"
            else:
                layout = "fan"
        else:
            layout = "basic_3"

    if layout == "basic_3":
        M_AB = ((Apex[0] + BL[0]) / 2, (Apex[1] + BL[1]) / 2)
        M_AC = ((Apex[0] + BR[0]) / 2, (Apex[1] + BR[1]) / 2)
        parts.append(line(M_AB, M_AC))
    elif layout == "basic_4":
        M_AB = ((Apex[0] + BL[0]) / 2, (Apex[1] + BL[1]) / 2)
        M_AC = ((Apex[0] + BR[0]) / 2, (Apex[1] + BR[1]) / 2)
        M_BC = ((BL[0] + BR[0]) / 2, (BL[1] + BR[1]) / 2)
        parts.append(line(M_AB, M_AC))
        parts.append(line(M_AB, M_BC))
        parts.append(line(M_AC, M_BC))
    elif layout == "fan":
        p1 = (BL[0] + (BR[0] - BL[0]) / 3, BL[1])
        p2 = (BL[0] + 2 * (BR[0] - BL[0]) / 3, BL[1])
        parts.append(line(Apex, p1))
        parts.append(line(Apex, p2))

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# grid_colored — NxN grid with specified cells colored.
# ---------------------------------------------------------------------------


def grid_colored(params: Dict[str, Any]) -> str:
    """
    Render an NxN grid, coloring specified cells.

    Params:
        size: int — grid dimension (e.g. 4 for 4x4)
        colored_cells: list of [row, col] pairs (0-indexed from top-left)
        color: optional hex string (default pink)
    """
    # Aliases: grid_size/cols/rows -> size, cells/count -> colored_cells
    _size_raw = params.get("size") or params.get("grid_size") or params.get("cols") or params.get("rows")
    n = int(_size_raw) if _size_raw is not None else 4
    n = max(1, min(10, n))
    colored = params.get("colored_cells") or params.get("cells") or []
    # If count provided but no colored_cells, generate first N cells
    if not colored and params.get("count") is not None:
        _cnt = _safe_int(params.get("count"), 0)
        colored = [[i // n, i % n] for i in range(min(_cnt, n * n))]
    color = params.get("color", "#FFB6C1")

    cell = 40
    pad = 4
    width = n * cell + 2 * pad
    height = n * cell + 2 * pad

    # Normalize colored cells to a set of (row, col) tuples.
    colored_set = set()
    for pair in colored:
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            colored_set.add((int(pair[0]), int(pair[1])))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} by {n} grid with {len(colored_set)} colored cells">',
    ]
    for r in range(n):
        for c in range(n):
            x = pad + c * cell
            y = pad + r * cell
            fill = color if (r, c) in colored_set else "#FFFFFF"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'fill="{fill}" stroke="#333333" stroke-width="2"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# ten_frame — classic 2x5 ten-frame with filled / empty dots.
# ---------------------------------------------------------------------------


def ten_frame(params: Dict[str, Any]) -> str:
    """
    Render a ten-frame (2 rows x 5 columns) with filled dots.

    Params:
        filled: int (0-10) — number of filled dots
        color:  optional hex string (default green)
    """
    # Alias: count -> filled
    filled = int(params.get("filled") or params.get("count") or 0)
    filled = max(0, min(10, filled))
    color = params.get("color", "#4CAF50")

    cell = 50
    gap = 4
    cols = 5
    rows = 2
    pad = 12
    frame_w = cols * cell + (cols - 1) * gap
    frame_h = rows * cell + (rows - 1) * gap
    width = frame_w + 2 * pad
    height = frame_h + 2 * pad

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Ten frame with {filled} filled">',
        # Rounded border around the whole frame.
        f'<rect x="{pad - 4}" y="{pad - 4}" width="{frame_w + 8}" '
        f'height="{frame_h + 8}" rx="8" ry="8" fill="none" '
        f'stroke="#424242" stroke-width="2"/>',
    ]

    dot_index = 0
    for r in range(rows):
        for c in range(cols):
            cx = pad + c * (cell + gap) + cell // 2
            cy = pad + r * (cell + gap) + cell // 2
            if dot_index < filled:
                # Filled dot — solid colored circle.
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="18" fill="{_escape(color)}"/>'
                )
            else:
                # Empty cell — light gray outline circle.
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="18" fill="none" '
                    f'stroke="#BDBDBD" stroke-width="2"/>'
                )
            dot_index += 1

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# number_line — horizontal number line with tick marks and optional highlight.
# ---------------------------------------------------------------------------


def number_line(params: Dict[str, Any]) -> str:
    """
    Render a horizontal number line with tick marks and optional highlight.

    Params:
        start:     int — starting number
        end:       int — ending number
        highlight: int (optional) — position to highlight with a red marker
        step:      int (default 1) — interval between tick marks
    """
    start = int(params.get("start", 0))
    end_raw = params.get("end")
    step = int(params.get("step", 1))
    # Alias: hops -> highlight
    highlight = params.get("highlight") or params.get("hops")
    if highlight is not None:
        highlight = int(highlight)
    # Smart default for end: if not specified, make sure the range covers
    # at least 0-20 or extends well past the start value (for addition questions
    # where start=6 but answer could be 12).
    if end_raw is not None:
        end = int(end_raw)
    else:
        end = max(start + 10, 20)  # always show enough range

    if step < 1:
        step = 1
    if end <= start:
        end = start + 1

    span = end - start
    # Width scales with span, capped at 500px.
    line_w = min(500, max(200, span * 40))
    pad = 40
    width = line_w + 2 * pad
    height = 80
    y_line = 30

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Number line from {start} to {end}'
        f'{f", {highlight} highlighted" if highlight is not None else ""}">',
        # Main horizontal line.
        f'<line x1="{pad}" y1="{y_line}" x2="{pad + line_w}" y2="{y_line}" '
        f'stroke="#424242" stroke-width="2" stroke-linecap="round"/>',
    ]

    # Tick marks and labels.
    num_ticks = (end - start) // step + 1
    for i in range(num_ticks):
        val = start + i * step
        if val > end:
            break
        x = pad + (val - start) / span * line_w
        # Tick mark.
        parts.append(
            f'<line x1="{x}" y1="{y_line - 8}" x2="{x}" y2="{y_line + 8}" '
            f'stroke="#424242" stroke-width="2"/>'
        )
        # Number label below tick.
        parts.append(
            f'<text x="{x}" y="{y_line + 28}" text-anchor="middle" '
            f'font-size="14" font-family="sans-serif" fill="#333333">{val}</text>'
        )

    # Optional highlight marker.
    if highlight is not None and start <= highlight <= end:
        hx = pad + (highlight - start) / span * line_w
        # Red circle above the line.
        parts.append(
            f'<circle cx="{hx}" cy="{y_line - 16}" r="6" fill="#e53935"/>'
        )
        # Arrow pointing down to the line.
        parts.append(
            f'<line x1="{hx}" y1="{y_line - 10}" x2="{hx}" y2="{y_line}" '
            f'stroke="#e53935" stroke-width="2" stroke-linecap="round"/>'
        )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# bar_model — Singapore-style part-whole bar model.
# ---------------------------------------------------------------------------


def bar_model(params: Dict[str, Any]) -> str:
    """
    Render a part-whole bar model (Singapore math style).

    Params:
        total:      int — the whole
        part1:      int — first part (part2 = total - part1)
        show_total: bool (default true) — whether to label the total above
        color1:     optional hex (default light blue)
        color2:     optional hex (default light orange)
    """
    # Aliases: tens/ones for place-value context (total = tens + ones, part1 = tens)
    _tens = params.get("tens")
    _ones = params.get("ones")
    if _tens is not None and _ones is not None and params.get("total") is None:
        total = int(_tens) + int(_ones)
        part1 = int(_tens)
    else:
        total = int(params.get("total", 10))
        part1 = int(params.get("part1", 0))
    show_total = params.get("show_total", True)
    color1 = params.get("color1", "#BBDEFB")
    color2 = params.get("color2", "#FFE0B2")

    if total <= 0:
        total = 1
    part1 = max(0, min(part1, total))
    part2 = total - part1

    bar_w = 400
    bar_h = 50
    pad = 30
    top_offset = 50 if show_total else 20
    width = bar_w + 2 * pad
    height = bar_h + top_offset + 40

    p1_w = (part1 / total) * bar_w if total > 0 else 0
    p2_w = bar_w - p1_w

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Bar model: {part1} and {part2} make {total}">',
    ]

    # Total bracket and label above the bar.
    if show_total:
        bracket_y = top_offset - 20
        # Left bracket arm.
        parts.append(
            f'<line x1="{pad}" y1="{top_offset - 4}" x2="{pad}" '
            f'y2="{bracket_y}" stroke="#424242" stroke-width="2"/>'
        )
        # Horizontal bracket line.
        parts.append(
            f'<line x1="{pad}" y1="{bracket_y}" x2="{pad + bar_w}" '
            f'y2="{bracket_y}" stroke="#424242" stroke-width="2"/>'
        )
        # Right bracket arm.
        parts.append(
            f'<line x1="{pad + bar_w}" y1="{bracket_y}" '
            f'x2="{pad + bar_w}" y2="{top_offset - 4}" '
            f'stroke="#424242" stroke-width="2"/>'
        )
        # Total label.
        parts.append(
            f'<text x="{pad + bar_w / 2}" y="{bracket_y - 6}" '
            f'text-anchor="middle" font-size="16" font-family="sans-serif" '
            f'font-weight="bold" fill="#333333">{total}</text>'
        )

    # Part 1 rectangle.
    if part1 > 0:
        parts.append(
            f'<rect x="{pad}" y="{top_offset}" width="{p1_w}" '
            f'height="{bar_h}" fill="{_escape(color1)}" '
            f'stroke="#424242" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{pad + p1_w / 2}" y="{top_offset + bar_h / 2 + 6}" '
            f'text-anchor="middle" font-size="16" font-family="sans-serif" '
            f'fill="#333333">{part1}</text>'
        )

    # Part 2 rectangle.
    if part2 > 0:
        parts.append(
            f'<rect x="{pad + p1_w}" y="{top_offset}" width="{p2_w}" '
            f'height="{bar_h}" fill="{_escape(color2)}" '
            f'stroke="#424242" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{pad + p1_w + p2_w / 2}" '
            f'y="{top_offset + bar_h / 2 + 6}" '
            f'text-anchor="middle" font-size="16" font-family="sans-serif" '
            f'fill="#333333">{part2}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# comparison_bars — two horizontal bars for comparing quantities.
# ---------------------------------------------------------------------------


def comparison_bars(params: Dict[str, Any]) -> str:
    """
    Render two horizontal bars for comparing quantities.

    Params:
        value1: int — first quantity
        value2: int — second quantity
        label1: str (optional) — label for first bar
        label2: str (optional) — label for second bar
        color1: optional hex (default light blue)
        color2: optional hex (default light coral)
    """
    # Aliases: bigger/left/a -> value1, smaller/right/b -> value2
    value1 = int(params.get("value1") or params.get("bigger") or params.get("left") or params.get("a") or 0)
    value2 = int(params.get("value2") or params.get("smaller") or params.get("right") or params.get("b") or 0)
    label1 = params.get("label1", "A")
    label2 = params.get("label2", "B")
    color1 = params.get("color1", "#BBDEFB")
    color2 = params.get("color2", "#FFCDD2")

    max_val = max(value1, value2, 1)
    max_bar_w = 400
    label_area = 60
    value_area = 50
    pad = 10
    bar_h = 36
    bar_gap = 16
    width = label_area + max_bar_w + value_area + 2 * pad
    height = 2 * bar_h + bar_gap + 2 * pad

    def bar_w(val: int) -> float:
        return (val / max_val) * max_bar_w if max_val > 0 else 0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Comparison: '
        f'{_escape(str(label1))} is {value1}, '
        f'{_escape(str(label2))} is {value2}">',
    ]

    for i, (val, label, color) in enumerate([
        (value1, label1, color1), (value2, label2, color2)
    ]):
        y = pad + i * (bar_h + bar_gap)
        w = bar_w(val)

        # Label on the left.
        parts.append(
            f'<text x="{pad + label_area - 8}" y="{y + bar_h / 2 + 6}" '
            f'text-anchor="end" font-size="14" font-family="sans-serif" '
            f'fill="#333333">{_escape(str(label))}</text>'
        )
        # Bar.
        if w > 0:
            parts.append(
                f'<rect x="{pad + label_area}" y="{y}" width="{w}" '
                f'height="{bar_h}" rx="4" ry="4" fill="{_escape(color)}" '
                f'stroke="#424242" stroke-width="1.5"/>'
            )
        # Value on the right of the bar.
        parts.append(
            f'<text x="{pad + label_area + w + 8}" y="{y + bar_h / 2 + 6}" '
            f'text-anchor="start" font-size="14" font-family="sans-serif" '
            f'font-weight="bold" fill="#333333">{val}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# clock_face — analog clock showing hour and half-hour times.
# ---------------------------------------------------------------------------


def clock_face(params: Dict[str, Any]) -> str:
    """
    Render an analog clock face for a given time.

    Params:
        hour:   int (1-12)
        minute: int (0 or 30 — only hour and half-hour for Grade 1)
    """
    hour = int(params.get("hour", 12))
    minute = int(params.get("minute", 0))
    hour = max(1, min(12, hour))
    # Only support :00 and :30 for Grade 1.
    minute = 30 if minute >= 15 else 0

    size = 200
    cx = size / 2
    cy = size / 2
    r = 80  # clock radius

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'role="img" aria-label="Clock showing {hour}:{minute:02d}">',
        # Clock circle.
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFDE7" '
        f'stroke="#424242" stroke-width="3"/>',
        # Center dot.
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#424242"/>',
    ]

    # Hour numbers around the edge.
    for h in range(1, 13):
        angle = math.radians(h * 30 - 90)  # 12 o'clock = -90 degrees
        nx = cx + (r - 18) * math.cos(angle)
        ny = cy + (r - 18) * math.sin(angle)
        parts.append(
            f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="14" '
            f'font-family="sans-serif" fill="#333333">{h}</text>'
        )

    # Small tick marks at each hour position.
    for h in range(12):
        angle = math.radians(h * 30 - 90)
        x1 = cx + (r - 6) * math.cos(angle)
        y1 = cy + (r - 6) * math.sin(angle)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="#424242" stroke-width="2"/>'
        )

    # Hour hand — shorter, thicker.
    # For half-hour the hour hand sits halfway between the current and next hour.
    hour_angle_deg = (hour % 12) * 30 + (minute / 60) * 30 - 90
    hour_angle = math.radians(hour_angle_deg)
    hour_len = r * 0.5
    hx = cx + hour_len * math.cos(hour_angle)
    hy = cy + hour_len * math.sin(hour_angle)
    parts.append(
        f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" '
        f'stroke="#212121" stroke-width="4" stroke-linecap="round"/>'
    )

    # Minute hand — longer, thinner.
    min_angle = math.radians(minute * 6 - 90)
    min_len = r * 0.75
    mx = cx + min_len * math.cos(min_angle)
    my = cy + min_len * math.sin(min_angle)
    parts.append(
        f'<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" '
        f'stroke="#1976D2" stroke-width="2.5" stroke-linecap="round"/>'
    )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# pattern_strip — repeating pattern of colored shapes.
# ---------------------------------------------------------------------------

# Supported colors for pattern shapes.
_PATTERN_COLORS: Dict[str, str] = {
    "red":    "#e53935",
    "blue":   "#1976D2",
    "green":  "#4CAF50",
    "yellow": "#FDD835",
    "orange": "#FB8C00",
    "purple": "#8E24AA",
}


def _draw_shape(shape: str, color_hex: str, cx: float, cy: float,
                r: float) -> str:
    """Return an SVG element for a shape centered at (cx, cy) with radius r."""
    if shape == "circle":
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color_hex}"/>')
    elif shape == "square":
        half = r * 0.85
        return (
            f'<rect x="{cx - half}" y="{cy - half}" '
            f'width="{2 * half}" height="{2 * half}" fill="{color_hex}"/>'
        )
    elif shape == "triangle":
        x1, y1 = cx, cy - r
        x2, y2 = cx - r, cy + r * 0.7
        x3, y3 = cx + r, cy + r * 0.7
        return (
            f'<polygon points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} '
            f'{x3:.1f},{y3:.1f}" fill="{color_hex}"/>'
        )
    # Fallback: circle.
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color_hex}"/>'


def pattern_strip(params: Dict[str, Any]) -> str:
    """
    Render a repeating pattern of colored shapes.

    Params:
        pattern: list of strings like ["red_circle", "blue_square"]
                 Format: "{color}_{shape}"
        repeat:  int (default 2) — how many times to repeat the pattern
    """
    pattern = params.get("pattern", ["red_circle", "blue_square"])
    repeat = int(params.get("repeat", 2))
    repeat = max(1, min(6, repeat))

    if not isinstance(pattern, list) or len(pattern) == 0:
        pattern = ["red_circle"]

    items = pattern * repeat
    cell = 44
    pad = 8
    shape_r = 16
    width = len(items) * cell + 2 * pad
    height = cell + 2 * pad

    label_parts = ", ".join(items[:len(pattern)])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Pattern: {_escape(label_parts)} '
        f'repeated {repeat} times">',
    ]

    for i, item in enumerate(items):
        # Parse "{color}_{shape}" format.
        tokens = item.split("_", 1)
        if len(tokens) == 2:
            color_name, shape = tokens
        else:
            color_name, shape = "red", "circle"

        color_hex = _PATTERN_COLORS.get(color_name, "#e53935")
        ix = pad + i * cell + cell // 2
        iy = pad + cell // 2
        parts.append(_draw_shape(shape, color_hex, ix, iy, shape_r))

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# BATCH 3 — Missing generators referenced by academic content.
# ===========================================================================

# ---------------------------------------------------------------------------
# Helpers for deterministic-random layouts (seeded by param hash).
# ---------------------------------------------------------------------------


def _seed_from_params(params: Dict[str, Any]) -> int:
    """Deterministic seed so the same params always produce the same layout."""
    raw = str(sorted(params.items())).encode()
    return int(hashlib.md5(raw).hexdigest()[:8], 16)


def _safe_int(val: Any, default: int = 0) -> int:
    """Coerce a value to int, handling template strings gracefully."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# tally_marks — vertical tally marks in groups of 5.
# ---------------------------------------------------------------------------


def tally_marks(params: Dict[str, Any]) -> str:
    """
    Render tally marks. Groups of 5 (4 vertical + 1 diagonal), then singles.

    Params:
        count: int — number of tally marks
    """
    n = _safe_int(params.get("count"), 5)
    n = max(1, min(20, n))

    groups = n // 5
    singles = n % 5
    total_slots = groups + (1 if singles > 0 else 0)

    group_w = 60
    pad = 12
    width = total_slots * group_w + 2 * pad
    height = 80
    base_y = 15
    mark_h = 50

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} tally marks">',
    ]

    slot = 0
    # Full groups of 5.
    for _ in range(groups):
        gx = pad + slot * group_w
        for j in range(4):
            x = gx + j * 12 + 6
            parts.append(
                f'<line x1="{x}" y1="{base_y}" x2="{x}" y2="{base_y + mark_h}" '
                f'stroke="#333" stroke-width="3" stroke-linecap="round"/>'
            )
        # Diagonal strike-through.
        parts.append(
            f'<line x1="{gx}" y1="{base_y + mark_h - 8}" '
            f'x2="{gx + 46}" y2="{base_y + 8}" '
            f'stroke="#333" stroke-width="3" stroke-linecap="round"/>'
        )
        slot += 1

    # Remaining singles.
    if singles > 0:
        gx = pad + slot * group_w
        for j in range(singles):
            x = gx + j * 12 + 6
            parts.append(
                f'<line x1="{x}" y1="{base_y}" x2="{x}" y2="{base_y + mark_h}" '
                f'stroke="#333" stroke-width="3" stroke-linecap="round"/>'
            )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# dot_row — a horizontal row of filled dots.
# ---------------------------------------------------------------------------


def dot_row(params: Dict[str, Any]) -> str:
    # Aliases: counts (list, use first element), count_a, left_count -> count
    _counts = params.get("counts")
    _count_raw = params.get("count") or (_counts[0] if isinstance(_counts, list) and _counts else None) or params.get("count_a") or params.get("left_count")
    n = _safe_int(_count_raw, 5)
    n = max(1, min(20, n))
    r = 14
    gap = 36
    pad = 12
    width = n * gap + 2 * pad
    height = 2 * r + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Row of {n} dots">',
    ]
    for i in range(n):
        cx = pad + i * gap + gap // 2
        cy = pad + r
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1976D2"/>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# object_row — row of emoji objects (no cross-out).
# ---------------------------------------------------------------------------


def object_row(params: Dict[str, Any]) -> str:
    # Alias: objects (list, use length) -> count
    _objects = params.get("objects")
    _count_raw = params.get("count_from") or params.get("count") or (len(_objects) if isinstance(_objects, list) else None)
    n = _safe_int(_count_raw, 5)
    n = max(1, min(20, n))
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    cell_w = 50
    pad = 10
    width = n * cell_w + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} {_escape(obj_key)}">',
    ]
    for i in range(n):
        cx = pad + i * cell_w + cell_w // 2
        parts.append(
            f'<text x="{cx}" y="{height // 2 + 10}" text-anchor="middle" '
            f'font-size="32">{icon}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# row_with_cross_out — like object_row_with_cross_out but simpler params.
# ---------------------------------------------------------------------------


def row_with_cross_out(params: Dict[str, Any]) -> str:
    """Maps simplified params to the existing object_row_with_cross_out."""
    mapped = {
        "count_from": params.get("count", 5),
        "cross_out": params.get("cross_out", 0),
        "object": params.get("object", "balloons"),
    }
    return object_row_with_cross_out(mapped)


# ---------------------------------------------------------------------------
# coin_row — row of coin circles.
# ---------------------------------------------------------------------------


def coin_row(params: Dict[str, Any]) -> str:
    # Alias: values (list, use length) -> count
    _values = params.get("values")
    _count_raw = params.get("count") or (len(_values) if isinstance(_values, list) else None)
    n = _safe_int(_count_raw, 5)
    n = max(1, min(20, n))
    r = 16
    gap = 40
    pad = 12
    width = n * gap + 2 * pad
    height = 2 * r + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} coins">',
    ]
    for i in range(n):
        cx = pad + i * gap + gap // 2
        cy = pad + r
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FDD835" '
            f'stroke="#F9A825" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" '
            f'font-size="12" font-family="sans-serif" fill="#795548">{i + 1}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# cube_row — row of cube outlines (isometric-ish).
# ---------------------------------------------------------------------------


def cube_row(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count"), 5)
    n = max(1, min(15, n))
    s = 34
    pad = 12
    off = 10  # isometric offset
    width = n * (s + 8) + off + 2 * pad
    height = s + off + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Row of {n} cubes">',
    ]
    for i in range(n):
        x = pad + i * (s + 8)
        y = pad + off
        # Front face.
        parts.append(
            f'<rect x="{x}" y="{y}" width="{s}" height="{s}" '
            f'fill="#BBDEFB" stroke="#1976D2" stroke-width="2"/>'
        )
        # Top face.
        parts.append(
            f'<polygon points="{x},{y} {x + off},{y - off} '
            f'{x + s + off},{y - off} {x + s},{y}" '
            f'fill="#90CAF9" stroke="#1976D2" stroke-width="2"/>'
        )
        # Right face.
        parts.append(
            f'<polygon points="{x + s},{y} {x + s + off},{y - off} '
            f'{x + s + off},{y + s - off} {x + s},{y + s}" '
            f'fill="#64B5F6" stroke="#1976D2" stroke-width="2"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# row — generic row of filled circles (simplest possible).
# ---------------------------------------------------------------------------


def row(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count"), 5)
    return dot_row({"count": n})


# ---------------------------------------------------------------------------
# scattered_dots — dots in pseudo-random positions.
# ---------------------------------------------------------------------------


def scattered_dots(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count"), 5)
    n = max(1, min(20, n))
    numbered = params.get("numbered", False)
    width, height = 300, 160
    pad = 20
    r = 14

    rng = random.Random(_seed_from_params(params))
    positions = []
    for _ in range(n * 20):
        if len(positions) >= n:
            break
        x = rng.randint(pad + r, width - pad - r)
        y = rng.randint(pad + r, height - pad - r)
        if all(((x - px) ** 2 + (y - py) ** 2) > (3 * r) ** 2
               for px, py in positions):
            positions.append((x, y))
    # Fallback: grid layout.
    while len(positions) < n:
        i = len(positions)
        positions.append((pad + r + (i % 8) * 34, pad + r + (i // 8) * 34))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} scattered dots">',
    ]
    for idx, (x, y) in enumerate(positions):
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#1976D2"/>')
        if numbered:
            parts.append(
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
                f'font-size="11" fill="white" font-weight="bold">{idx + 1}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# scattered_coins — coins in pseudo-random positions.
# ---------------------------------------------------------------------------


def scattered_coins(params: Dict[str, Any]) -> str:
    # Aliases: values (list, use length), options, available, setA/setB -> count
    _values = params.get("values")
    _count_raw = params.get("count")
    if _count_raw is None:
        if isinstance(_values, list):
            _count_raw = len(_values)
        else:
            _count_raw = params.get("options") or params.get("available")
            if _count_raw is None:
                _setA = params.get("setA")
                _setB = params.get("setB")
                if isinstance(_setA, list) and isinstance(_setB, list):
                    _count_raw = len(_setA) + len(_setB)
                elif isinstance(_setA, list):
                    _count_raw = len(_setA)
    n = _safe_int(_count_raw, 5)
    n = max(1, min(20, n))
    numbered = params.get("numbered", False)
    width, height = 300, 160
    pad = 20
    r = 16

    rng = random.Random(_seed_from_params(params))
    positions = []
    for _ in range(n * 20):
        if len(positions) >= n:
            break
        x = rng.randint(pad + r, width - pad - r)
        y = rng.randint(pad + r, height - pad - r)
        if all(((x - px) ** 2 + (y - py) ** 2) > (3 * r) ** 2
               for px, py in positions):
            positions.append((x, y))
    while len(positions) < n:
        i = len(positions)
        positions.append((pad + r + (i % 8) * 38, pad + r + (i // 8) * 38))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} scattered coins">',
    ]
    for idx, (x, y) in enumerate(positions):
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FDD835" '
            f'stroke="#F9A825" stroke-width="2"/>'
        )
        if numbered:
            parts.append(
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
                f'font-size="11" fill="#795548" font-weight="bold">{idx + 1}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# scattered_objects — emoji objects in pseudo-random positions.
# ---------------------------------------------------------------------------


def scattered_objects(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count_from") or params.get("count"), 5)
    n = max(1, min(20, n))
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    width, height = 300, 160
    pad = 24
    rng = random.Random(_seed_from_params(params))
    positions = []
    for _ in range(n * 20):
        if len(positions) >= n:
            break
        x = rng.randint(pad, width - pad)
        y = rng.randint(pad + 10, height - pad)
        if all(((x - px) ** 2 + (y - py) ** 2) > 1200
               for px, py in positions):
            positions.append((x, y))
    while len(positions) < n:
        i = len(positions)
        positions.append((pad + (i % 8) * 34, pad + 10 + (i // 8) * 34))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} scattered {_escape(obj_key)}">',
    ]
    for x, y in positions:
        parts.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" font-size="28">{icon}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# paired_rows — two labelled rows of dots for comparison.
# ---------------------------------------------------------------------------


def paired_rows(params: Dict[str, Any]) -> str:
    # Alias: count -> both top and bottom (same value)
    _count = params.get("count")
    top = _safe_int(params.get("top") or _count, 5)
    bottom = _safe_int(params.get("bottom") or _count, 3)
    top_label = params.get("top_label", "A")
    bottom_label = params.get("bottom_label", "B")
    top = max(0, min(20, top))
    bottom = max(0, min(20, bottom))
    r = 12
    gap = 30
    pad = 12
    label_w = 70
    max_n = max(top, bottom, 1)
    width = label_w + max_n * gap + 2 * pad
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{_escape(str(top_label))}: {top}, '
        f'{_escape(str(bottom_label))}: {bottom}">',
    ]
    for row_i, (count, label, color) in enumerate([
        (top, top_label, "#4CAF50"), (bottom, bottom_label, "#FF7043")
    ]):
        y = pad + row_i * 40 + 18
        parts.append(
            f'<text x="{pad + label_w - 8}" y="{y + 5}" text-anchor="end" '
            f'font-size="13" font-family="sans-serif" fill="#333">'
            f'{_escape(str(label))}</text>'
        )
        for j in range(count):
            cx = pad + label_w + j * gap + gap // 2
            parts.append(
                f'<circle cx="{cx}" cy="{y}" r="{r}" fill="{color}"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# two_groups — two labelled clusters of objects.
# ---------------------------------------------------------------------------


def two_groups(params: Dict[str, Any]) -> str:
    # Aliases: left_count/right_count -> group_a/group_b
    a = _safe_int(params.get("group_a") or params.get("left_count"), 3)
    b = _safe_int(params.get("group_b") or params.get("right_count"), 4)
    label_a = params.get("label_a", "A")
    label_b = params.get("label_b", "B")
    a, b = max(0, min(15, a)), max(0, min(15, b))
    return _render_groups(
        [(a, str(label_a), "#4CAF50"), (b, str(label_b), "#FF7043")],
        f"{label_a}: {a}, {label_b}: {b}"
    )


def single_group(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count"), 5)
    label = params.get("label", "items")
    n = max(0, min(20, n))
    return _render_groups(
        [(n, str(label), "#1976D2")],
        f"{label}: {n}"
    )


def _render_groups(groups: list, aria_label: str) -> str:
    """Shared renderer for labelled groups of dots."""
    r = 10
    group_gap = 40
    pad = 14
    total_w = 0
    for count, _, _ in groups:
        cols = min(count, 5)
        total_w += max(cols, 1) * 26 + group_gap
    width = total_w + 2 * pad
    height = 110
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{_escape(aria_label)}">',
    ]
    x_offset = pad
    for count, label, color in groups:
        cols = min(count, 5)
        rows_n = math.ceil(count / max(cols, 1))
        gw = max(cols, 1) * 26
        # Label above.
        parts.append(
            f'<text x="{x_offset + gw // 2}" y="{pad}" text-anchor="middle" '
            f'font-size="12" font-family="sans-serif" fill="#555">'
            f'{_escape(str(label))}</text>'
        )
        # Dots.
        idx = 0
        for ri in range(rows_n):
            for ci in range(cols):
                if idx >= count:
                    break
                cx = x_offset + ci * 26 + 13
                cy = pad + 20 + ri * 26 + 13
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
                )
                idx += 1
        x_offset += gw + group_gap
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# combine_groups — two groups with a plus sign between them.
# ---------------------------------------------------------------------------


def combine_groups(params: Dict[str, Any]) -> str:
    left = _safe_int(params.get("left"), 3)
    right = _safe_int(params.get("right"), 2)
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    left, right = max(0, min(15, left)), max(0, min(15, right))
    cell = 36
    pad = 12
    plus_w = 30
    width = (left + right) * cell + plus_w + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{left} plus {right} {_escape(obj_key)}">',
    ]
    cy = height // 2
    x = pad
    for i in range(left):
        parts.append(
            f'<text x="{x + cell // 2}" y="{cy + 10}" text-anchor="middle" '
            f'font-size="26">{icon}</text>'
        )
        x += cell
    # Plus sign.
    parts.append(
        f'<text x="{x + plus_w // 2}" y="{cy + 8}" text-anchor="middle" '
        f'font-size="22" fill="#666">+</text>'
    )
    x += plus_w
    for i in range(right):
        parts.append(
            f'<text x="{x + cell // 2}" y="{cy + 10}" text-anchor="middle" '
            f'font-size="26">{icon}</text>'
        )
        x += cell
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# combine_groups_coloured — two colored groups of objects.
# ---------------------------------------------------------------------------


def combine_groups_coloured(params: Dict[str, Any]) -> str:
    # Aliases: a -> red, b -> blue, c -> (additional group, added to blue)
    n_red = _safe_int(params.get("red") or params.get("a"), 3)
    n_blue = _safe_int(params.get("blue") or params.get("b"), 2)
    _c = _safe_int(params.get("c"), 0)
    n_blue = n_blue + _c
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    n_red, n_blue = max(0, min(15, n_red)), max(0, min(15, n_blue))

    cell = 36
    pad = 12
    plus_w = 30
    width = (n_red + n_blue) * cell + plus_w + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n_red} red and {n_blue} blue {_escape(obj_key)}">',
    ]
    cy = height // 2
    x = pad
    for i in range(n_red):
        parts.append(
            f'<circle cx="{x + cell // 2}" cy="{cy}" r="14" fill="#e53935"/>'
        )
        x += cell
    parts.append(
        f'<text x="{x + plus_w // 2}" y="{cy + 8}" text-anchor="middle" '
        f'font-size="22" fill="#666">+</text>'
    )
    x += plus_w
    for i in range(n_blue):
        parts.append(
            f'<circle cx="{x + cell // 2}" cy="{cy}" r="14" fill="#1976D2"/>'
        )
        x += cell
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# equal_groups — G groups of K objects each.
# ---------------------------------------------------------------------------


def equal_groups(params: Dict[str, Any]) -> str:
    g = _safe_int(params.get("groups"), 3)
    k = _safe_int(params.get("per_group"), 2)
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    g, k = max(1, min(8, g)), max(1, min(10, k))

    item_w = 32
    group_gap = 20
    pad = 12
    group_w = k * item_w
    width = g * group_w + (g - 1) * group_gap + 2 * pad
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{g} groups of {k} {_escape(obj_key)}">',
    ]
    cy = height // 2
    for gi in range(g):
        gx = pad + gi * (group_w + group_gap)
        # Group border.
        parts.append(
            f'<rect x="{gx - 4}" y="{cy - 24}" width="{group_w + 8}" '
            f'height="48" rx="8" fill="none" stroke="#BDBDBD" '
            f'stroke-width="1.5" stroke-dasharray="4,3"/>'
        )
        for ki in range(k):
            x = gx + ki * item_w + item_w // 2
            parts.append(
                f'<text x="{x}" y="{cy + 10}" text-anchor="middle" '
                f'font-size="24">{icon}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# two_rows_compare — two labelled rows for comparison (like paired_rows).
# ---------------------------------------------------------------------------


def two_rows_compare(params: Dict[str, Any]) -> str:
    return paired_rows({
        "top": params.get("row_a_count", 5),
        "bottom": params.get("row_b_count", 3),
        "top_label": params.get("row_a_label", "A"),
        "bottom_label": params.get("row_b_label", "B"),
    })


# ---------------------------------------------------------------------------
# Shape-based generators.
# ---------------------------------------------------------------------------

_SHAPE_NAMES = ["circle", "square", "triangle", "star", "hexagon", "diamond"]
_SHAPE_COLORS = ["#e53935", "#1976D2", "#4CAF50", "#FDD835", "#8E24AA", "#FF7043"]


def _draw_basic_shape(shape: str, cx: float, cy: float, r: float,
                      color: str = "#1976D2", stroke: str = "#333") -> str:
    """Draw a basic geometric shape."""
    if shape == "circle":
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
                f'stroke="{stroke}" stroke-width="2"/>')
    elif shape == "square":
        h = r * 0.85
        return (f'<rect x="{cx - h}" y="{cy - h}" width="{2 * h}" '
                f'height="{2 * h}" fill="{color}" stroke="{stroke}" stroke-width="2"/>')
    elif shape == "triangle":
        x1, y1 = cx, cy - r
        x2, y2 = cx - r, cy + r * 0.7
        x3, y3 = cx + r, cy + r * 0.7
        return (f'<polygon points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} '
                f'{x3:.1f},{y3:.1f}" fill="{color}" stroke="{stroke}" stroke-width="2"/>')
    elif shape == "star":
        pts = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            rad = r if i % 2 == 0 else r * 0.45
            pts.append(f"{cx + rad * math.cos(angle):.1f},{cy + rad * math.sin(angle):.1f}")
        return (f'<polygon points="{" ".join(pts)}" fill="{color}" '
                f'stroke="{stroke}" stroke-width="2"/>')
    elif shape == "hexagon":
        pts = []
        for i in range(6):
            angle = math.radians(i * 60 - 90)
            pts.append(f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
        return (f'<polygon points="{" ".join(pts)}" fill="{color}" '
                f'stroke="{stroke}" stroke-width="2"/>')
    elif shape == "diamond":
        return (f'<polygon points="{cx},{cy - r} {cx + r * 0.7},{cy} '
                f'{cx},{cy + r} {cx - r * 0.7},{cy}" fill="{color}" '
                f'stroke="{stroke}" stroke-width="2"/>')
    # Fallback.
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
            f'stroke="{stroke}" stroke-width="2"/>')


def four_shapes_one_different(params: Dict[str, Any]) -> str:
    """
    Four shapes where one is different from the rest.

    Params:
        shape_family: str — what the majority shapes are
        odd_index: int — which one (0-3) is the odd one out
        highlight_matching: bool — highlight the matching ones
    """
    # Aliases: majority -> shape_family, odd/target -> odd_index
    family = params.get("shape_family") or params.get("majority") or "circle"
    odd_idx = _safe_int(params.get("odd_index") or params.get("odd") or params.get("target"), 2)
    highlight = params.get("highlight_matching", False)
    odd_idx = max(0, min(3, odd_idx))

    # Pick the odd shape.
    odd_shape = "triangle" if family != "triangle" else "circle"
    shapes = [family] * 4
    shapes[odd_idx] = odd_shape

    r = 22
    gap = 70
    pad = 16
    width = 4 * gap + 2 * pad
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Four shapes, one different">',
    ]
    for i, s in enumerate(shapes):
        cx = pad + i * gap + gap // 2
        cy = height // 2
        color = "#BBDEFB" if (i != odd_idx or not highlight) else "#FFCDD2"
        if highlight and i != odd_idx:
            color = "#C8E6C9"
        parts.append(_draw_basic_shape(s, cx, cy, r, color))
    parts.append("</svg>")
    return "".join(parts)


def four_balls_one_different_size(params: Dict[str, Any]) -> str:
    """Four circles where one is a different size."""
    odd_idx = _safe_int(params.get("odd_index"), 2)
    odd_smaller = params.get("odd_smaller", True)
    highlight = params.get("highlight_matching", False)
    odd_idx = max(0, min(3, odd_idx))

    big_r = 22
    small_r = 13
    gap = 70
    pad = 16
    width = 4 * gap + 2 * pad
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Four balls, one different size">',
    ]
    for i in range(4):
        cx = pad + i * gap + gap // 2
        cy = height // 2
        if i == odd_idx:
            r = small_r if odd_smaller else big_r
            color = "#FFCDD2" if highlight else "#BBDEFB"
        else:
            r = big_r if odd_smaller else small_r
            color = "#C8E6C9" if highlight else "#BBDEFB"
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
                     f'stroke="#333" stroke-width="2"/>')
    parts.append("</svg>")
    return "".join(parts)


def two_shapes_compare(params: Dict[str, Any]) -> str:
    """Two shapes for comparison — same or different."""
    # Aliases: rotated, shape, fold_line, mode, shape_a/shape_b
    same = params.get("same")
    if same is None:
        # If shape_a and shape_b provided, same = (shape_a == shape_b)
        _sa = params.get("shape_a")
        _sb = params.get("shape_b")
        if _sa is not None and _sb is not None:
            same = (_sa == _sb)
        elif params.get("rotated") is not None:
            same = True  # rotated implies same shape
        elif params.get("shape") is not None or params.get("fold_line") is not None:
            same = True  # symmetry/fold context implies same shape
        elif params.get("mode") is not None:
            same = True
        else:
            same = True
    r = 28
    gap = 120
    pad = 20
    width = 2 * gap + 2 * pad
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Two shapes to compare">',
    ]
    s1 = "circle"
    s2 = "circle" if same else "square"
    for i, s in enumerate([s1, s2]):
        cx = pad + i * gap + gap // 2
        parts.append(_draw_basic_shape(s, cx, height // 2, r, "#BBDEFB"))
    parts.append("</svg>")
    return "".join(parts)


def two_balls_different_size(params: Dict[str, Any]) -> str:
    """Two balls of different sizes."""
    width, height = 200, 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Two balls of different sizes">',
        f'<circle cx="60" cy="{height // 2}" r="28" fill="#BBDEFB" stroke="#333" stroke-width="2"/>',
        f'<circle cx="150" cy="{height // 2}" r="16" fill="#FFCDD2" stroke="#333" stroke-width="2"/>',
    ]
    parts.append("</svg>")
    return "".join(parts)


def mixed_shapes(params: Dict[str, Any]) -> str:
    """
    Display a mix of shapes (e.g. triangles + circles) for counting.

    Params:
        total: int — total shapes
        triangles: int — how many are triangles (rest are circles)
        highlight: str (optional) — which type to highlight
    """
    total = _safe_int(params.get("total"), 6)
    triangles = _safe_int(params.get("triangles"), 3)
    # Alias: highlight_sides -> highlight
    highlight = params.get("highlight") or params.get("highlight_sides")
    total = max(1, min(15, total))
    triangles = max(0, min(total, triangles))
    circles = total - triangles

    r = 16
    gap = 42
    pad = 12
    width = total * gap + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{triangles} triangles and {circles} circles">',
    ]
    shapes_list = (["triangle"] * triangles) + (["circle"] * circles)
    rng = random.Random(_seed_from_params(params))
    rng.shuffle(shapes_list)

    for i, s in enumerate(shapes_list):
        cx = pad + i * gap + gap // 2
        cy = height // 2
        if highlight == "triangles" and s == "triangle":
            color = "#FFF9C4"
        elif highlight == "circles" and s == "circle":
            color = "#FFF9C4"
        else:
            color = "#BBDEFB" if s == "circle" else "#C8E6C9"
        parts.append(_draw_basic_shape(s, cx, cy, r, color))
    parts.append("</svg>")
    return "".join(parts)


def overlapping_circles(params: Dict[str, Any]) -> str:
    """Overlapping circles for counting/geometry."""
    n = _safe_int(params.get("count"), 3)
    show_centres = params.get("show_centres", False)
    n = max(1, min(8, n))
    r = 30
    overlap = 18
    pad = 16
    width = n * (2 * r - overlap) + overlap + 2 * pad
    height = 2 * r + 2 * pad
    colors = ["#BBDEFB", "#C8E6C9", "#FFCDD2", "#FFF9C4",
              "#E1BEE7", "#FFE0B2", "#B2DFDB", "#F8BBD0"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} overlapping circles">',
    ]
    for i in range(n):
        cx = pad + r + i * (2 * r - overlap)
        cy = pad + r
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{colors[i % len(colors)]}" '
            f'fill-opacity="0.6" stroke="#333" stroke-width="2"/>'
        )
        if show_centres:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="#333"/>')
    parts.append("</svg>")
    return "".join(parts)


def separated_circles(params: Dict[str, Any]) -> str:
    """Non-overlapping circles in a row."""
    n = _safe_int(params.get("count"), 5)
    n = max(1, min(15, n))
    r = 16
    gap = 40
    pad = 12
    width = n * gap + 2 * pad
    height = 2 * r + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} separated circles">',
    ]
    for i in range(n):
        cx = pad + i * gap + gap // 2
        cy = pad + r
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#BBDEFB" '
            f'stroke="#333" stroke-width="2"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def subdivided_triangle(params: Dict[str, Any]) -> str:
    """
    Triangle with subdivisions. Maps to existing triangle_subdivision
    with different param interface.

    Params:
        side: str — which type of subdivision
        highlight_mode: str — 'none' or 'numbered'
    """
    layout = params.get("layout", "basic_4")
    if params.get("side") == "side":
        layout = "basic_4"
    return triangle_subdivision({"layout": layout})


# ---------------------------------------------------------------------------
# Container generators (jars, plates).
# ---------------------------------------------------------------------------


def _jar_svg(x: float, y: float, w: float, h: float,
             count: int, color: str = "#1976D2",
             label: Optional[str] = None) -> str:
    """Draw a jar shape with dots inside."""
    parts = []
    # Jar body (rounded rect).
    parts.append(
        f'<rect x="{x}" y="{y + 12}" width="{w}" height="{h - 12}" '
        f'rx="10" fill="#E3F2FD" stroke="#333" stroke-width="2"/>'
    )
    # Jar lid.
    parts.append(
        f'<rect x="{x + 5}" y="{y}" width="{w - 10}" height="14" '
        f'rx="3" fill="#90CAF9" stroke="#333" stroke-width="2"/>'
    )
    # Dots inside.
    cols = min(count, 3)
    if cols == 0:
        cols = 1
    rows_n = math.ceil(count / cols) if count > 0 else 0
    dot_r = min(8, (w - 20) / (2 * cols))
    for i in range(count):
        r_idx = i // cols
        c_idx = i % cols
        cx = x + 14 + c_idx * (w - 28) / max(cols - 1, 1) if cols > 1 else x + w / 2
        cy = y + h - 16 - r_idx * 20
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r:.1f}" fill="{color}"/>')
    # Label below.
    if label:
        parts.append(
            f'<text x="{x + w / 2}" y="{y + h + 16}" text-anchor="middle" '
            f'font-size="12" font-family="sans-serif" fill="#333">{_escape(str(label))}</text>'
        )
    return "".join(parts)


def single_jar(params: Dict[str, Any]) -> str:
    n = _safe_int(params.get("count"), 5)
    n = max(0, min(15, n))
    width, height = 120, 130
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Jar with {n} items">',
        _jar_svg(25, 10, 70, 90, n),
    ]
    parts.append("</svg>")
    return "".join(parts)


def two_jars(params: Dict[str, Any]) -> str:
    a = _safe_int(params.get("jar_a"), 3)
    b = _safe_int(params.get("jar_b"), 4)
    a, b = max(0, min(15, a)), max(0, min(15, b))
    width, height = 240, 140
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Jar A: {a}, Jar B: {b}">',
        _jar_svg(20, 10, 70, 90, a, "#4CAF50", "A"),
        _jar_svg(140, 10, 70, 90, b, "#FF7043", "B"),
    ]
    parts.append("</svg>")
    return "".join(parts)


def three_jars(params: Dict[str, Any]) -> str:
    a = _safe_int(params.get("jar_a"), 2)
    b = _safe_int(params.get("jar_b"), 3)
    c = _safe_int(params.get("jar_c"), 4)
    a, b, c = [max(0, min(12, x)) for x in (a, b, c)]
    width, height = 340, 140
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Jar A: {a}, B: {b}, C: {c}">',
        _jar_svg(15, 10, 70, 90, a, "#4CAF50", "A"),
        _jar_svg(130, 10, 70, 90, b, "#FF7043", "B"),
        _jar_svg(245, 10, 70, 90, c, "#1976D2", "C"),
    ]
    parts.append("</svg>")
    return "".join(parts)


def marbles_partial_cover(params: Dict[str, Any]) -> str:
    """Some marbles visible, some hidden behind a cover."""
    visible = _safe_int(params.get("visible"), 3)
    total = _safe_int(params.get("total"), 5)
    visible, total = max(0, min(15, visible)), max(1, min(20, total))
    hidden = max(0, total - visible)
    r = 14
    gap = 34
    pad = 12
    cover_x = pad + visible * gap
    width = total * gap + 2 * pad + 20
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{visible} visible, {hidden} hidden marbles">',
    ]
    cy = height // 2
    for i in range(visible):
        cx = pad + i * gap + gap // 2
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1976D2"/>')
    # Cover.
    if hidden > 0:
        parts.append(
            f'<rect x="{cover_x}" y="{cy - 24}" width="{hidden * gap + 10}" '
            f'height="48" rx="8" fill="#9E9E9E" opacity="0.7"/>'
        )
        parts.append(
            f'<text x="{cover_x + hidden * gap / 2 + 5}" y="{cy + 6}" '
            f'text-anchor="middle" font-size="18" fill="white" '
            f'font-weight="bold">?</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def marbles_revealed(params: Dict[str, Any]) -> str:
    """Marbles that were hidden are now shown."""
    hidden = _safe_int(params.get("hidden"), 3)
    hidden = max(1, min(15, hidden))
    r = 14
    gap = 34
    pad = 12
    width = hidden * gap + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{hidden} revealed marbles">',
    ]
    cy = height // 2
    for i in range(hidden):
        cx = pad + i * gap + gap // 2
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#4CAF50" '
            f'stroke="#2E7D32" stroke-width="2"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Sequence / pattern generators.
# ---------------------------------------------------------------------------


_COLOUR_MAP = {
    "red": "#e53935", "blue": "#1976D2", "green": "#4CAF50",
    "yellow": "#FDD835", "orange": "#FB8C00", "purple": "#8E24AA",
}


def colour_sequence(params: Dict[str, Any]) -> str:
    """
    Color pattern sequence — e.g. ABABA with colour mapping.

    Params:
        pattern: str like "ABABA"
        colours: list of colour names, mapped to A, B, C...
    """
    colours = params.get("colours", ["red", "blue"])
    if not isinstance(colours, list):
        colours = ["red", "blue"]
    # If pattern is omitted, infer from colours list length
    pattern = params.get("pattern")
    if not pattern:
        _letters = [chr(65 + i) for i in range(len(colours))]
        # Default repeating pattern from available colours
        pattern = "".join(_letters) * 2 if _letters else "ABAB"

    cell = 40
    pad = 10
    width = len(pattern) * cell + 2 * pad
    height = 60
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Colour pattern: {_escape(pattern)}">',
    ]
    letter_map = {}
    for i, letter in enumerate(sorted(set(pattern))):
        if i < len(colours):
            letter_map[letter] = _COLOUR_MAP.get(colours[i], colours[i])
        else:
            letter_map[letter] = "#999"

    for i, ch in enumerate(pattern):
        cx = pad + i * cell + cell // 2
        cy = height // 2
        color = letter_map.get(ch, "#999")
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="16" fill="{color}"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def colour_sequence_with_arrows(params: Dict[str, Any]) -> str:
    """Same as colour_sequence but with arrows showing the repeat."""
    pattern = params.get("pattern", "ABAB")
    colours = params.get("colours", ["red", "blue"])
    if not isinstance(colours, list):
        colours = ["red", "blue"]

    cell = 40
    pad = 10
    width = len(pattern) * cell + 2 * pad
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Colour pattern with arrows: {_escape(pattern)}">',
    ]
    letter_map = {}
    for i, letter in enumerate(sorted(set(pattern))):
        if i < len(colours):
            letter_map[letter] = _COLOUR_MAP.get(colours[i], colours[i])
        else:
            letter_map[letter] = "#999"

    for i, ch in enumerate(pattern):
        cx = pad + i * cell + cell // 2
        cy = 30
        color = letter_map.get(ch, "#999")
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="14" fill="{color}"/>')
        if i < len(pattern) - 1:
            parts.append(
                f'<line x1="{cx + 16}" y1="{cy}" x2="{cx + cell - 16}" y2="{cy}" '
                f'stroke="#999" stroke-width="1.5" marker-end="url(#arrow)"/>'
            )

    # Arrow marker definition.
    parts.insert(1,
        '<defs><marker id="arrow" markerWidth="6" markerHeight="6" '
        'refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" '
        'fill="#999"/></marker></defs>'
    )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Split / sharing / plates.
# ---------------------------------------------------------------------------


def split_object(params: Dict[str, Any]) -> str:
    """Two groups split from a whole — left and right."""
    # Aliases: parts/total -> compute left=parts, right=total-parts
    _parts = params.get("parts")
    _total = params.get("total")
    if params.get("left_count") is None and _parts is not None:
        left = _safe_int(_parts, 3)
        right = _safe_int(_total, left) - left if _total is not None else _safe_int(params.get("right_count"), 2)
    else:
        left = _safe_int(params.get("left_count"), 3)
        right = _safe_int(params.get("right_count"), 2)
    obj_key = params.get("object", "balloons")
    icon = _OBJECT_ICONS.get(obj_key, "●")
    left, right = max(0, min(10, left)), max(0, min(10, right))

    cell = 36
    pad = 12
    divider = 30
    width = (left + right) * cell + divider + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Split: {left} and {right}">',
    ]
    cy = height // 2
    x = pad
    for i in range(left):
        parts.append(
            f'<text x="{x + cell // 2}" y="{cy + 10}" text-anchor="middle" '
            f'font-size="26">{icon}</text>'
        )
        x += cell
    # Divider line.
    parts.append(
        f'<line x1="{x + divider // 2}" y1="10" x2="{x + divider // 2}" '
        f'y2="{height - 10}" stroke="#999" stroke-width="2" stroke-dasharray="4,3"/>'
    )
    x += divider
    for i in range(right):
        parts.append(
            f'<text x="{x + cell // 2}" y="{cy + 10}" text-anchor="middle" '
            f'font-size="26">{icon}</text>'
        )
        x += cell
    parts.append("</svg>")
    return "".join(parts)


def sharing_animation(params: Dict[str, Any]) -> str:
    """Total items being shared into groups (equal division visual)."""
    total = _safe_int(params.get("total"), 6)
    groups = _safe_int(params.get("groups"), 3)
    total, groups = max(1, min(20, total)), max(1, min(8, groups))
    per = total // groups if groups > 0 else total
    return equal_groups({"groups": groups, "per_group": per, "object": "balloons"})


def equal_plates(params: Dict[str, Any]) -> str:
    """Items distributed equally on plates."""
    total = _safe_int(params.get("total"), 6)
    groups = _safe_int(params.get("groups"), 3)
    total, groups = max(1, min(20, total)), max(1, min(8, groups))
    per = total // groups if groups > 0 else total

    plate_w = 60
    plate_gap = 20
    pad = 12
    width = groups * (plate_w + plate_gap) + 2 * pad
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{total} items on {groups} plates">',
    ]
    for gi in range(groups):
        px = pad + gi * (plate_w + plate_gap)
        # Plate (ellipse).
        parts.append(
            f'<ellipse cx="{px + plate_w // 2}" cy="55" rx="{plate_w // 2}" '
            f'ry="18" fill="#EFEBE9" stroke="#795548" stroke-width="2"/>'
        )
        # Items on plate.
        for j in range(per):
            ix = px + 10 + j * min(14, (plate_w - 20) // max(per, 1))
            parts.append(
                f'<circle cx="{ix + 7}" cy="50" r="6" fill="#FF7043"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Number line highlight (alias for existing number_line with highlight).
# ---------------------------------------------------------------------------


def number_line_highlight(params: Dict[str, Any]) -> str:
    # Aliases: start/end/highlights, step, count/start, marks -> focus
    _focus_raw = params.get("focus") or params.get("count") or params.get("marks")
    focus = _safe_int(_focus_raw, 5)
    _start = _safe_int(params.get("start"), 0)
    _end = params.get("end")
    _step = params.get("step")
    _highlights = params.get("highlights")
    nl_params: Dict[str, Any] = {
        "start": _start,
        "end": int(_end) if _end is not None else max(focus + 2, 10),
        "highlight": focus,
    }
    if _step is not None:
        nl_params["step"] = int(_step)
    return number_line(nl_params)


# ---------------------------------------------------------------------------
# Domino.
# ---------------------------------------------------------------------------


def domino(params: Dict[str, Any]) -> str:
    """
    Render a domino piece with left and right pip counts.

    Params:
        left: int (0-6)
        right: int (0-6)
    """
    left_n = _safe_int(params.get("left"), 3)
    right_n = _safe_int(params.get("right"), 4)
    left_n, right_n = max(0, min(6, left_n)), max(0, min(6, right_n))

    half_w = 60
    h = 80
    pad = 10
    width = 2 * half_w + 2 * pad + 4
    height = h + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Domino: {left_n} | {right_n}">',
        # Outer border.
        f'<rect x="{pad}" y="{pad}" width="{2 * half_w + 4}" height="{h}" '
        f'rx="8" fill="#FAFAFA" stroke="#333" stroke-width="2"/>',
        # Divider line.
        f'<line x1="{pad + half_w + 2}" y1="{pad + 6}" '
        f'x2="{pad + half_w + 2}" y2="{pad + h - 6}" '
        f'stroke="#333" stroke-width="2"/>',
    ]

    def _place_pips(n: int, ox: float) -> list:
        """Place pips using standard positions within a half."""
        pip_parts = []
        pip_r = 5
        cx_center = ox + half_w / 2
        cy_center = pad + h / 2
        # Offsets for 3x3 grid.
        dx = half_w * 0.28
        dy = h * 0.28
        positions = _DICE_PIPS.get(n, [])
        for (col, row_p) in positions:
            px = cx_center + (col - 1) * dx
            py = cy_center + (row_p - 1) * dy
            pip_parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{pip_r}" fill="#333"/>'
            )
        return pip_parts

    parts.extend(_place_pips(left_n, pad))
    parts.extend(_place_pips(right_n, pad + half_w + 4))
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# cube_stack — isometric stack of cubes.
# ---------------------------------------------------------------------------


def cube_stack(params: Dict[str, Any]) -> str:
    """
    Stack of cubes — some visible, some hidden.

    Params:
        visible: int — visible cubes
        hidden: int — hidden cubes (shown as ghosted)
        reveal_hidden: bool — if true, show hidden cubes differently
    """
    # Alias: count -> visible
    visible = _safe_int(params.get("visible") or params.get("count"), 3)
    hidden = _safe_int(params.get("hidden"), 2)
    reveal = params.get("reveal_hidden", False)
    visible, hidden = max(0, min(10, visible)), max(0, min(10, hidden))
    total = visible + hidden

    s = 36
    off = 12
    pad = 16
    width = s + off + 2 * pad
    height = total * (s - off) + off + 2 * pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Stack: {visible} visible, {hidden} hidden cubes">',
    ]
    for i in range(total):
        idx = total - 1 - i  # draw bottom to top
        x = pad
        y = pad + idx * (s - off)
        is_hidden = idx >= visible
        opacity = "0.3" if (is_hidden and reveal) else "1"
        fill_front = "#BBDEFB" if not is_hidden else "#E0E0E0"
        fill_top = "#90CAF9" if not is_hidden else "#BDBDBD"
        fill_right = "#64B5F6" if not is_hidden else "#9E9E9E"

        if is_hidden and not reveal:
            continue
        parts.append(f'<g opacity="{opacity}">')
        parts.append(
            f'<rect x="{x}" y="{y + off}" width="{s}" height="{s - off}" '
            f'fill="{fill_front}" stroke="#333" stroke-width="1.5"/>'
        )
        parts.append(
            f'<polygon points="{x},{y + off} {x + off},{y} '
            f'{x + s + off},{y} {x + s},{y + off}" '
            f'fill="{fill_top}" stroke="#333" stroke-width="1.5"/>'
        )
        parts.append(
            f'<polygon points="{x + s},{y + off} {x + s + off},{y} '
            f'{x + s + off},{y + s - off} {x + s},{y + s}" '
            f'fill="{fill_right}" stroke="#333" stroke-width="1.5"/>'
        )
        parts.append('</g>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Balloon generators.
# ---------------------------------------------------------------------------


def balloons_with_popped(params: Dict[str, Any]) -> str:
    """Balloons with some popped (shown as deflated)."""
    total = _safe_int(params.get("total"), 5)
    remaining = _safe_int(params.get("remaining"), 3)
    total, remaining = max(1, min(15, total)), max(0, min(total, remaining))
    popped = total - remaining

    cell = 40
    pad = 12
    width = total * cell + 2 * pad
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{total} balloons, {popped} popped">',
    ]
    for i in range(total):
        cx = pad + i * cell + cell // 2
        if i < remaining:
            # Full balloon.
            parts.append(
                f'<ellipse cx="{cx}" cy="30" rx="14" ry="18" '
                f'fill="#e53935" stroke="#c62828" stroke-width="1.5"/>'
            )
            parts.append(
                f'<line x1="{cx}" y1="48" x2="{cx}" y2="68" '
                f'stroke="#999" stroke-width="1.5"/>'
            )
        else:
            # Popped — small zigzag.
            parts.append(
                f'<text x="{cx}" y="38" text-anchor="middle" '
                f'font-size="10" fill="#999">💥</text>'
            )
            parts.append(
                f'<line x1="{cx}" y1="42" x2="{cx}" y2="68" '
                f'stroke="#999" stroke-width="1" stroke-dasharray="3,2"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


def popped_only(params: Dict[str, Any]) -> str:
    """Show only the popped/removed count as empty spots."""
    n = _safe_int(params.get("count"), 3)
    n = max(1, min(15, n))
    cell = 40
    pad = 12
    width = n * cell + 2 * pad
    height = 60
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} removed items">',
    ]
    for i in range(n):
        cx = pad + i * cell + cell // 2
        parts.append(
            f'<circle cx="{cx}" cy="{height // 2}" r="14" fill="none" '
            f'stroke="#999" stroke-width="2" stroke-dasharray="4,3"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# two_hands — objects in two hands.
# ---------------------------------------------------------------------------


def two_hands(params: Dict[str, Any]) -> str:
    """Two hands, each holding a (possibly different) number of items."""
    # Support both symmetric (per_hand/A) and asymmetric (left/right, A/B) modes.
    left_count = _safe_int(
        params.get("left") or params.get("per_hand") or params.get("A"),
        3,
    )
    right_count = _safe_int(
        params.get("right") or params.get("B") or params.get("per_hand") or params.get("A"),
        left_count,  # default right = left (symmetric)
    )
    left_count = max(0, min(10, left_count))
    right_count = max(0, min(10, right_count))
    counts = [left_count, right_count]
    hand_w = 80
    gap = 40
    pad = 12
    width = 2 * hand_w + gap + 2 * pad
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Hand 1: {left_count} items, Hand 2: {right_count} items">',
    ]
    for hi in range(2):
        hx = pad + hi * (hand_w + gap)
        n = counts[hi]
        # Hand outline.
        parts.append(
            f'<rect x="{hx}" y="10" width="{hand_w}" height="60" rx="12" '
            f'fill="#FFF3E0" stroke="#795548" stroke-width="2"/>'
        )
        # Label.
        parts.append(
            f'<text x="{hx + hand_w // 2}" y="80" text-anchor="middle" '
            f'font-size="11" fill="#795548">Hand {hi + 1}</text>'
        )
        # Dots.
        for j in range(n):
            spacing = min(16, (hand_w - 28) / max(n - 1, 1))
            cx = hx + 14 + j * spacing
            parts.append(
                f'<circle cx="{cx}" cy="40" r="6" fill="#FF7043"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# BATCH 4 — Missing generators referenced by Grade-1 content files.
# ===========================================================================


# ---------------------------------------------------------------------------
# dot_addition — two groups of dots with a plus sign (addition visualization).
# ---------------------------------------------------------------------------


def dot_addition(params: Dict[str, Any]) -> str:
    """Two groups of coloured dots separated by a '+' sign."""
    a = _safe_int(params.get("A") or params.get("left"), 3)
    b = _safe_int(params.get("B") or params.get("right"), 2)
    a, b = max(1, min(10, a)), max(1, min(10, b))
    dot_r = 10
    gap = 28
    pad = 14
    plus_w = 30
    width = (a + b) * gap + plus_w + 2 * pad
    height = 60
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{a} plus {b} dots">',
    ]
    cy = height // 2
    x = pad
    for i in range(a):
        cx = x + gap // 2
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{dot_r}" fill="#FF7043"/>'
        )
        x += gap
    parts.append(
        f'<text x="{x + plus_w // 2}" y="{cy + 7}" text-anchor="middle" '
        f'font-size="22" font-family="sans-serif" fill="#666">+</text>'
    )
    x += plus_w
    for i in range(b):
        cx = x + gap // 2
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{dot_r}" fill="#42A5F5"/>'
        )
        x += gap
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# tens_blocks — base-10 blocks (tall rods for tens, small squares for ones).
# ---------------------------------------------------------------------------


def tens_blocks(params: Dict[str, Any]) -> str:
    """Render base-10 blocks: tall rectangles for tens, small squares for ones."""
    tens = _safe_int(params.get("T") or params.get("tens"), 2)
    ones = _safe_int(params.get("O") or params.get("ones"), 3)
    tens, ones = max(0, min(9, tens)), max(0, min(9, ones))
    pad = 14
    rod_w = 16
    rod_h = 60
    rod_gap = 22
    cube_s = 14
    cube_gap = 20
    spacer = 24
    width = tens * rod_gap + spacer + ones * cube_gap + 2 * pad
    width = max(width, 60)
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{tens} tens and {ones} ones">',
    ]
    x = pad
    for i in range(tens):
        parts.append(
            f'<rect x="{x}" y="10" width="{rod_w}" height="{rod_h}" rx="3" '
            f'fill="#42A5F5" stroke="#1E88E5" stroke-width="1.5"/>'
        )
        x += rod_gap
    x += spacer
    cube_y = 10 + rod_h - cube_s
    for i in range(ones):
        parts.append(
            f'<rect x="{x}" y="{cube_y}" width="{cube_s}" height="{cube_s}" rx="2" '
            f'fill="#66BB6A" stroke="#43A047" stroke-width="1.5"/>'
        )
        x += cube_gap
    # Label
    parts.append(
        f'<text x="{width // 2}" y="{height - 4}" text-anchor="middle" '
        f'font-size="11" font-family="sans-serif" fill="#795548">'
        f'{tens} tens, {ones} ones</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# timeline — horizontal number line with labeled events / marked points.
# ---------------------------------------------------------------------------


def timeline(params: Dict[str, Any]) -> str:
    """Horizontal timeline / number line from 1 to 12 with marked points."""
    start = _safe_int(params.get("start"), 1)
    end = _safe_int(params.get("end"), 12)
    h1 = _safe_int(params.get("H1") or params.get("mark1"), 0)
    h2 = _safe_int(params.get("H2") or params.get("mark2"), 0)
    marks_raw = params.get("marks", [])
    marks: List[int] = []
    if isinstance(marks_raw, list):
        marks = [_safe_int(m, 0) for m in marks_raw]
    if h1:
        marks.append(h1)
    if h2:
        marks.append(h2)

    end = max(end, start + 1)
    n = end - start + 1
    pad = 30
    tick_gap = 36
    width = n * tick_gap + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Timeline from {start} to {end}">',
    ]
    line_y = 30
    lx = pad
    rx = pad + (n - 1) * tick_gap
    parts.append(
        f'<line x1="{lx}" y1="{line_y}" x2="{rx}" y2="{line_y}" '
        f'stroke="#795548" stroke-width="2"/>'
    )
    for i in range(n):
        val = start + i
        tx = pad + i * tick_gap
        parts.append(
            f'<line x1="{tx}" y1="{line_y - 6}" x2="{tx}" y2="{line_y + 6}" '
            f'stroke="#795548" stroke-width="1.5"/>'
        )
        color = "#FF7043" if val in marks else "#795548"
        weight = "bold" if val in marks else "normal"
        parts.append(
            f'<text x="{tx}" y="{line_y + 22}" text-anchor="middle" '
            f'font-size="12" font-family="sans-serif" fill="{color}" '
            f'font-weight="{weight}">{val}</text>'
        )
        if val in marks:
            parts.append(
                f'<circle cx="{tx}" cy="{line_y}" r="5" fill="#FF7043"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# number_comparison — two numbers with >, <, = comparison.
# ---------------------------------------------------------------------------


def number_comparison(params: Dict[str, Any]) -> str:
    """Show two numbers side by side with a comparison symbol between them."""
    a = _safe_int(params.get("A") or params.get("left"), 3)
    b = _safe_int(params.get("B") or params.get("right"), 7)
    a, b = max(0, min(99, a)), max(0, min(99, b))
    if a > b:
        symbol = "&gt;"
    elif a < b:
        symbol = "&lt;"
    else:
        symbol = "="
    width = 220
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{a} compared with {b}">',
        # Background boxes
        f'<rect x="10" y="10" width="60" height="50" rx="10" fill="#FFF3E0" '
        f'stroke="#FF7043" stroke-width="2"/>',
        f'<rect x="150" y="10" width="60" height="50" rx="10" fill="#E3F2FD" '
        f'stroke="#42A5F5" stroke-width="2"/>',
        # Numbers
        f'<text x="40" y="45" text-anchor="middle" font-size="28" '
        f'font-family="sans-serif" font-weight="bold" fill="#E65100">{a}</text>',
        f'<text x="180" y="45" text-anchor="middle" font-size="28" '
        f'font-family="sans-serif" font-weight="bold" fill="#1565C0">{b}</text>',
        # Symbol
        f'<text x="110" y="47" text-anchor="middle" font-size="30" '
        f'font-family="sans-serif" fill="#666">{symbol}</text>',
    ]
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# dot_subtraction — dots with some crossed out (subtraction visualization).
# ---------------------------------------------------------------------------


def dot_subtraction(params: Dict[str, Any]) -> str:
    """Row of dots with the last B crossed out to show A - B."""
    a = _safe_int(params.get("A") or params.get("total"), 7)
    b = _safe_int(params.get("B") or params.get("remove"), 3)
    a = max(1, min(15, a))
    b = max(0, min(a, b))
    dot_r = 10
    gap = 28
    pad = 14
    width = a * gap + 2 * pad
    height = 60
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{a} dots with {b} crossed out">',
    ]
    cy = height // 2
    for i in range(a):
        cx = pad + i * gap + gap // 2
        crossed = i >= (a - b)
        fill = "#BDBDBD" if crossed else "#FF7043"
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{dot_r}" fill="{fill}"/>'
        )
        if crossed:
            parts.append(
                f'<line x1="{cx - dot_r}" y1="{cy - dot_r}" '
                f'x2="{cx + dot_r}" y2="{cy + dot_r}" '
                f'stroke="#D32F2F" stroke-width="2.5"/>'
            )
            parts.append(
                f'<line x1="{cx + dot_r}" y1="{cy - dot_r}" '
                f'x2="{cx - dot_r}" y2="{cy + dot_r}" '
                f'stroke="#D32F2F" stroke-width="2.5"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# dot_counter — simple row of dots for counting.
# ---------------------------------------------------------------------------


def dot_counter(params: Dict[str, Any]) -> str:
    """Simple row of dots with numbers underneath for counting practice."""
    n = _safe_int(params.get("A") or params.get("count"), 4)
    n = max(1, min(10, n))
    dot_r = 12
    gap = 34
    pad = 14
    width = n * gap + 2 * pad
    height = 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{n} dots to count">',
    ]
    for i in range(n):
        cx = pad + i * gap + gap // 2
        parts.append(
            f'<circle cx="{cx}" cy="25" r="{dot_r}" fill="#66BB6A"/>'
        )
        parts.append(
            f'<text x="{cx}" y="58" text-anchor="middle" '
            f'font-size="13" font-family="sans-serif" fill="#795548">{i + 1}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# sharing_circles — items distributed equally among circles (division).
# ---------------------------------------------------------------------------


def sharing_circles(params: Dict[str, Any]) -> str:
    """Show items distributed equally into circles (sharing / division)."""
    total = _safe_int(params.get("A") or params.get("total"), 6)
    groups = _safe_int(params.get("B") or params.get("groups"), 2)
    total, groups = max(1, min(20, total)), max(1, min(6, groups))
    per = total // groups if groups > 0 else total
    circle_r = 30
    circle_gap = 80
    pad = 16
    width = groups * circle_gap + 2 * pad
    height = 90
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{total} items shared into {groups} circles">',
    ]
    for gi in range(groups):
        cx = pad + gi * circle_gap + circle_gap // 2
        cy = 40
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{circle_r}" fill="#FFF3E0" '
            f'stroke="#FF7043" stroke-width="2"/>'
        )
        # Place dots inside the circle.
        for j in range(per):
            angle = (2 * math.pi * j) / max(per, 1)
            ir = 14 if per > 1 else 0
            dx = cx + ir * math.cos(angle)
            dy = cy + ir * math.sin(angle)
            parts.append(
                f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="5" fill="#FF7043"/>'
            )
        # Label
        parts.append(
            f'<text x="{cx}" y="{height - 4}" text-anchor="middle" '
            f'font-size="11" font-family="sans-serif" fill="#795548">{per}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# coin_counting — coins with values being added up.
# ---------------------------------------------------------------------------


def coin_counting(params: Dict[str, Any]) -> str:
    """Show coins with values labelled, for counting money."""
    a = _safe_int(params.get("A") or params.get("coin1"), 3)
    b = _safe_int(params.get("B") or params.get("coin2"), 2)
    a, b = max(1, min(20, a)), max(1, min(20, b))
    coin_r = 18
    gap = 50
    pad = 16
    width = 2 * gap + pad * 2 + 60
    height = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Coins worth {a} and {b}">',
    ]
    coins = [a, b]
    plus_x = pad + gap + 10
    for ci, val in enumerate(coins):
        cx = pad + coin_r + 6
        if ci == 1:
            cx = plus_x + 30 + coin_r
        cy = 34
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{coin_r}" fill="#FDD835" '
            f'stroke="#F9A825" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" '
            f'font-size="14" font-family="sans-serif" font-weight="bold" '
            f'fill="#795548">{val}</text>'
        )
    # Plus sign between coins
    parts.append(
        f'<text x="{plus_x}" y="39" text-anchor="middle" '
        f'font-size="20" font-family="sans-serif" fill="#666">+</text>'
    )
    # Total label
    parts.append(
        f'<text x="{width // 2}" y="{height - 6}" text-anchor="middle" '
        f'font-size="13" font-family="sans-serif" fill="#795548">'
        f'= {a + b}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


# Registry: generator name -> function
_REGISTRY: Dict[str, Callable[[Dict[str, Any]], str]] = {
    # Batch 1 — original.
    "object_row_with_cross_out": object_row_with_cross_out,
    "dice_face": dice_face,
    "triangle_subdivision": triangle_subdivision,
    "grid_colored": grid_colored,
    # Batch 2.
    "ten_frame": ten_frame,
    "number_line": number_line,
    "bar_model": bar_model,
    "comparison_bars": comparison_bars,
    "clock_face": clock_face,
    "pattern_strip": pattern_strip,
    # Batch 3 — rows / dots / objects.
    "tally_marks": tally_marks,
    "dot_row": dot_row,
    "object_row": object_row,
    "row_with_cross_out": row_with_cross_out,
    "coin_row": coin_row,
    "cube_row": cube_row,
    "row": row,
    # Batch 3 — scattered.
    "scattered_dots": scattered_dots,
    "scattered_coins": scattered_coins,
    "scattered_objects": scattered_objects,
    # Batch 3 — groups / comparison.
    "paired_rows": paired_rows,
    "two_groups": two_groups,
    "single_group": single_group,
    "combine_groups": combine_groups,
    "combine_groups_coloured": combine_groups_coloured,
    "equal_groups": equal_groups,
    "two_rows_compare": two_rows_compare,
    # Batch 3 — shapes.
    "four_shapes_one_different": four_shapes_one_different,
    "four_balls_one_different_size": four_balls_one_different_size,
    "two_shapes_compare": two_shapes_compare,
    "two_balls_different_size": two_balls_different_size,
    "mixed_shapes": mixed_shapes,
    "overlapping_circles": overlapping_circles,
    "separated_circles": separated_circles,
    "subdivided_triangle": subdivided_triangle,
    # Batch 3 — containers.
    "single_jar": single_jar,
    "two_jars": two_jars,
    "three_jars": three_jars,
    "marbles_partial_cover": marbles_partial_cover,
    "marbles_revealed": marbles_revealed,
    # Batch 3 — sequences / patterns.
    "colour_sequence": colour_sequence,
    "colour_sequence_with_arrows": colour_sequence_with_arrows,
    # Batch 3 — split / sharing.
    "split_object": split_object,
    "sharing_animation": sharing_animation,
    "equal_plates": equal_plates,
    # Batch 3 — number line variant.
    "number_line_highlight": number_line_highlight,
    # Batch 3 — special.
    "domino": domino,
    "cube_stack": cube_stack,
    "balloons_with_popped": balloons_with_popped,
    "popped_only": popped_only,
    "two_hands": two_hands,
    # Batch 4 — missing generators for Grade-1 content.
    "dot_addition": dot_addition,
    "tens_blocks": tens_blocks,
    "timeline": timeline,
    "number_comparison": number_comparison,
    "dot_subtraction": dot_subtraction,
    "dot_counter": dot_counter,
    "sharing_circles": sharing_circles,
    "coin_counting": coin_counting,
}


def render_svg(generator_name: str, params: Dict[str, Any]) -> str:
    fn = _REGISTRY.get(generator_name)
    if fn is None:
        raise UnknownGeneratorError(
            f"no SVG generator named '{generator_name}'. "
            f"Registered: {sorted(_REGISTRY.keys())}"
        )
    return fn(params)


def available_generators() -> list[str]:
    return sorted(_REGISTRY.keys())
