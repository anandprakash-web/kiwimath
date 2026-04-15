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
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List


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
    n = int(params.get("count_from", 5))
    k = int(params.get("cross_out", 0))
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
        layout: one of the preset layouts.
            - "basic_3":   Big triangle with a horizontal line at mid-height
                           forming 3 small triangles (5 visible total incl nested).
            - "basic_4":   Big triangle divided into 4 sub-triangles (rows of 1,3).
            - "fan":       Big triangle with 2 lines from apex to base, forming 3 triangles.
    """
    layout = params.get("layout", "basic_3")

    W, H = 240, 200
    # Apex at top-center, base on bottom corners
    A = (W / 2, 20)
    B = (30, H - 20)
    C = (W - 30, H - 20)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="Triangle figure">',
        # Outer triangle
        f'<polygon points="{A[0]},{A[1]} {B[0]},{B[1]} {C[0]},{C[1]}" '
        f'fill="none" stroke="#1976D2" stroke-width="3" stroke-linejoin="round"/>',
    ]

    def line(p1, p2):
        return (f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" '
                f'stroke="#1976D2" stroke-width="3" stroke-linecap="round"/>')

    if layout == "basic_3":
        # Horizontal midline from midpoint of AB to midpoint of AC
        M_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
        M_AC = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
        parts.append(line(M_AB, M_AC))
    elif layout == "basic_4":
        M_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
        M_AC = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
        M_BC = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)
        parts.append(line(M_AB, M_AC))
        parts.append(line(M_AB, M_BC))
        parts.append(line(M_AC, M_BC))
    elif layout == "fan":
        # Two lines from apex to 1/3 and 2/3 of BC
        p1 = (B[0] + (C[0] - B[0]) / 3, B[1])
        p2 = (B[0] + 2 * (C[0] - B[0]) / 3, B[1])
        parts.append(line(A, p1))
        parts.append(line(A, p2))

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
    n = int(params.get("size", 4))
    n = max(1, min(10, n))
    colored = params.get("colored_cells", [])
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


# Registry: generator name -> function
_REGISTRY: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "object_row_with_cross_out": object_row_with_cross_out,
    "dice_face": dice_face,
    "triangle_subdivision": triangle_subdivision,
    "grid_colored": grid_colored,
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
