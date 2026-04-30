"""
Grade 3-4 (Écolier) SVG Visual Generators
==========================================
Parametric SVG generators for complex Math Kangaroo visuals.
Each function returns a complete SVG string.

Visual categories (from Écolier papers 2009-2025):
  1. 3D Structures (isometric cubes, dice nets, box folding)
  2. Grid & Board puzzles (colored grids, dominoes, chessboards)
  3. Balance / Algebra visuals (scales, equations with shapes)
  4. Paper folding & cutting (fold lines, punch holes, unfold)
  5. Mazes & Paths (arrow grids, path finding)
  6. Geometry (tangrams, overlapping shapes, area shading)
  7. Pattern & Sequence visuals (shape sequences, growing patterns)
  8. Counting & Arrangement (coins, stamps, objects)

Usage:
    from svg_generators_g3g4 import isometric_cubes, balance_scale, grid_colored
    svg = isometric_cubes(structure=[[1,1],[1,0]], color="#4ECDC4")
    svg = balance_scale(left_items=[("circle",3)], right_items=[("square",2)])
"""

from __future__ import annotations
import math
from typing import List, Tuple, Optional, Dict, Any

# ---------------------------------------------------------------------------
# Color palette — child-friendly, high-contrast
# ---------------------------------------------------------------------------
COLORS = {
    "red": "#FF6B6B", "blue": "#4ECDC4", "green": "#2ECC71", "yellow": "#F1C40F",
    "orange": "#F39C12", "purple": "#9B59B6", "pink": "#E91E63", "teal": "#00BCD4",
    "navy": "#2C3E50", "gray": "#95A5A6", "white": "#FFFFFF", "light_gray": "#ECF0F1",
    "dark": "#333333", "coral": "#FF7675", "mint": "#55EFC4", "sky": "#74B9FF",
}

SHAPE_COLORS = ["#FF6B6B", "#4ECDC4", "#F1C40F", "#9B59B6", "#2ECC71",
                "#FF7675", "#74B9FF", "#00BCD4", "#F39C12", "#E91E63"]


def _svg_wrap(content: str, width: int = 400, height: int = 300) -> str:
    return (f'<svg viewBox="0 0 {width} {height}" '
            f'xmlns="http://www.w3.org/2000/svg">\n{content}\n</svg>')


# ===================================================================
# 1. ISOMETRIC / 3D CUBE STRUCTURES
# ===================================================================

def isometric_cubes(
    structure: List[List[List[int]]],
    color: str = "#4ECDC4",
    highlight_color: str = "#FF6B6B",
    highlight_cells: Optional[List[Tuple[int, int, int]]] = None,
    show_count: bool = False,
    width: int = 400, height: int = 300,
) -> str:
    """
    Draw an isometric 3D cube structure.

    structure: 3D array [layer][row][col] where 1=cube, 0=empty
                layer 0 = bottom, layer[-1] = top
    highlight_cells: list of (layer, row, col) to color differently
    """
    highlight_cells = highlight_cells or []
    cx, cy = width // 2, height - 40
    s = 25  # cube edge size in pixels

    # Isometric projection helpers
    def iso_x(col, row, layer):
        return cx + (col - row) * s * 0.866

    def iso_y(col, row, layer):
        return cy - (col + row) * s * 0.5 - layer * s

    def cube_face(x, y, s, fill, stroke="#2C3E50"):
        """Draw one isometric cube (top + left + right faces)."""
        dx = s * 0.866
        dy = s * 0.5
        # Top face
        top = f"{x},{y - s} {x + dx},{y - s + dy} {x},{y} {x - dx},{y - s + dy}"
        # Left face
        left = f"{x - dx},{y - s + dy} {x},{y} {x},{y + s} {x - dx},{y + dy}"
        # Right face
        right = f"{x},{y} {x + dx},{y - s + dy} {x + dx},{y + dy} {x},{y + s}"

        # Darken sides
        import colorsys
        r, g, b = int(fill[1:3], 16)/255, int(fill[3:5], 16)/255, int(fill[5:7], 16)/255
        h, l, sat = colorsys.rgb_to_hls(r, g, b)
        lr, lg, lb = colorsys.hls_to_rgb(h, max(0, l - 0.15), sat)
        left_fill = f"#{int(lr*255):02x}{int(lg*255):02x}{int(lb*255):02x}"
        rr, rg, rb = colorsys.hls_to_rgb(h, max(0, l - 0.08), sat)
        right_fill = f"#{int(rr*255):02x}{int(rg*255):02x}{int(rb*255):02x}"

        return (
            f'  <polygon points="{top}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
            f'  <polygon points="{left}" fill="{left_fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
            f'  <polygon points="{right}" fill="{right_fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
        )

    parts = []
    total = 0
    # Draw bottom-to-top, back-to-front for correct occlusion
    for layer_i, layer in enumerate(structure):
        for row_i, row in enumerate(layer):
            for col_i, val in enumerate(row):
                if val:
                    total += 1
                    x = iso_x(col_i, row_i, layer_i)
                    y = iso_y(col_i, row_i, layer_i)
                    c = highlight_color if (layer_i, row_i, col_i) in highlight_cells else color
                    parts.append(cube_face(x, y, s, c))

    content = "".join(parts)
    if show_count:
        content += (f'  <text x="{width - 30}" y="25" text-anchor="end" '
                    f'font-family="system-ui" font-size="16" fill="#333" '
                    f'font-weight="bold">= ?</text>\n')

    return _svg_wrap(content, width, height)


def dice_net(
    faces: Dict[str, int],
    fold_face: Optional[str] = None,
    width: int = 400, height: int = 300,
) -> str:
    """
    Draw a dice/cube net (cross shape) with pip values on faces.

    faces: dict with keys "top","front","right","bottom","back","left"
           values are pip counts (1-6)
    fold_face: which face to highlight as "fold here"
    """
    s = 50  # face size
    cx, cy = width // 2, height // 2

    # Cross layout: top, left-front-right-back in a row, bottom
    positions = {
        "top":    (cx, cy - s),
        "left":   (cx - s, cy),
        "front":  (cx, cy),
        "right":  (cx + s, cy),
        "back":   (cx + 2 * s, cy),
        "bottom": (cx, cy + s),
    }

    def draw_pips(x, y, count):
        """Draw dice pips inside a face."""
        pips = []
        pip_r = 4
        offsets = {
            1: [(0, 0)],
            2: [(-12, -12), (12, 12)],
            3: [(-12, -12), (0, 0), (12, 12)],
            4: [(-12, -12), (12, -12), (-12, 12), (12, 12)],
            5: [(-12, -12), (12, -12), (0, 0), (-12, 12), (12, 12)],
            6: [(-12, -12), (12, -12), (-12, 0), (12, 0), (-12, 12), (12, 12)],
        }
        for dx, dy in offsets.get(count, []):
            pips.append(f'  <circle cx="{x + dx}" cy="{y + dy}" r="{pip_r}" fill="#333"/>')
        return "\n".join(pips)

    parts = []
    for name, (px, py) in positions.items():
        fill = "#FFF3CD" if name == fold_face else "#FFFFFF"
        stroke = "#E67E22" if name == fold_face else "#2C3E50"
        sw = 2.5 if name == fold_face else 1.5
        x0, y0 = px - s // 2, py - s // 2
        parts.append(f'  <rect x="{x0}" y="{y0}" width="{s}" height="{s}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="3"/>')
        if name in faces:
            parts.append(draw_pips(px, py, faces[name]))

    # Fold lines (dashed)
    parts.append(f'  <line x1="{cx - s//2}" y1="{cy - s//2}" x2="{cx + s//2}" y2="{cy - s//2}" '
                 f'stroke="#999" stroke-width="1" stroke-dasharray="4,3"/>')
    parts.append(f'  <line x1="{cx - s//2}" y1="{cy + s//2}" x2="{cx + s//2}" y2="{cy + s//2}" '
                 f'stroke="#999" stroke-width="1" stroke-dasharray="4,3"/>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 2. BALANCE SCALES / ALGEBRA
# ===================================================================

def balance_scale(
    left_items: List[Tuple[str, str, int]],
    right_items: List[Tuple[str, str, int]],
    balanced: bool = True,
    width: int = 400, height: int = 250,
) -> str:
    """
    Draw a balance scale with shapes on each side.

    items: list of (shape, color, count) tuples
           shape: "circle", "square", "triangle", "star", "?"
    balanced: if True, beam is level; if False, tilts left-heavy
    """
    cx, cy_base = width // 2, height - 30
    tilt = 0 if balanced else -8

    parts = []
    # Base triangle
    parts.append(f'  <polygon points="{cx - 20},{cy_base} {cx + 20},{cy_base} {cx},{cy_base - 25}" '
                 f'fill="#95A5A6" stroke="#7F8C8D" stroke-width="2"/>')
    # Fulcrum post
    parts.append(f'  <rect x="{cx - 3}" y="{cy_base - 100}" width="6" height="75" '
                 f'fill="#BDC3C7" stroke="#95A5A6" stroke-width="1"/>')

    # Beam
    beam_y = cy_base - 100
    beam_len = 140
    parts.append(f'  <line x1="{cx - beam_len}" y1="{beam_y + tilt}" '
                 f'x2="{cx + beam_len}" y2="{beam_y - tilt}" '
                 f'stroke="#2C3E50" stroke-width="4" stroke-linecap="round"/>')

    # Pans (chains + plate)
    for side, items, sign in [("left", left_items, -1), ("right", right_items, 1)]:
        pan_x = cx + sign * (beam_len - 10)
        pan_y = beam_y + (-tilt if sign == 1 else tilt)
        chain_len = 30
        # Chains
        parts.append(f'  <line x1="{pan_x}" y1="{pan_y}" '
                     f'x2="{pan_x}" y2="{pan_y + chain_len}" '
                     f'stroke="#7F8C8D" stroke-width="1.5"/>')
        # Pan plate
        plate_y = pan_y + chain_len
        parts.append(f'  <ellipse cx="{pan_x}" cy="{plate_y}" rx="50" ry="8" '
                     f'fill="#ECF0F1" stroke="#BDC3C7" stroke-width="1.5"/>')

        # Draw items on pan
        total_items = sum(c for _, _, c in items)
        item_x_start = pan_x - (total_items - 1) * 12
        idx = 0
        for shape, color, count in items:
            for _ in range(count):
                ix = item_x_start + idx * 24
                iy = plate_y - 22
                if shape == "circle":
                    parts.append(f'  <circle cx="{ix}" cy="{iy}" r="10" '
                                 f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
                elif shape == "square":
                    parts.append(f'  <rect x="{ix - 9}" y="{iy - 9}" width="18" height="18" '
                                 f'fill="{color}" stroke="#333" stroke-width="1.5" rx="2"/>')
                elif shape == "triangle":
                    parts.append(f'  <polygon points="{ix},{iy - 11} {ix - 10},{iy + 7} {ix + 10},{iy + 7}" '
                                 f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
                elif shape == "?":
                    parts.append(f'  <circle cx="{ix}" cy="{iy}" r="12" '
                                 f'fill="#FFF3CD" stroke="#E67E22" stroke-width="2"/>')
                    parts.append(f'  <text x="{ix}" y="{iy + 5}" text-anchor="middle" '
                                 f'font-family="system-ui" font-size="14" fill="#E67E22" '
                                 f'font-weight="bold">?</text>')
                idx += 1

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 3. GRID / BOARD PUZZLES
# ===================================================================

def colored_grid(
    rows: int, cols: int,
    colored_cells: Dict[Tuple[int, int], str],
    cell_size: int = 35,
    labels: Optional[Dict[Tuple[int, int], str]] = None,
    show_coords: bool = False,
    border_color: str = "#2C3E50",
    width: int = 400, height: int = 300,
) -> str:
    """
    Draw a grid with colored cells, labels, and optional coordinates.

    colored_cells: {(row, col): "#color"}
    labels: {(row, col): "text"} to place inside cells
    """
    labels = labels or {}
    gw = cols * cell_size
    gh = rows * cell_size
    ox = (width - gw) // 2
    oy = (height - gh) // 2

    parts = []
    for r in range(rows):
        for c in range(cols):
            x = ox + c * cell_size
            y = oy + r * cell_size
            fill = colored_cells.get((r, c), "#FFFFFF")
            parts.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                         f'fill="{fill}" stroke="{border_color}" stroke-width="1"/>')
            if (r, c) in labels:
                parts.append(f'  <text x="{x + cell_size//2}" y="{y + cell_size//2 + 5}" '
                             f'text-anchor="middle" font-family="system-ui" font-size="12" '
                             f'fill="#333" font-weight="bold">{labels[(r, c)]}</text>')

    if show_coords:
        for c in range(cols):
            parts.append(f'  <text x="{ox + c * cell_size + cell_size//2}" y="{oy - 5}" '
                         f'text-anchor="middle" font-family="system-ui" font-size="10" '
                         f'fill="#999">{c + 1}</text>')
        for r in range(rows):
            parts.append(f'  <text x="{ox - 8}" y="{oy + r * cell_size + cell_size//2 + 4}" '
                         f'text-anchor="end" font-family="system-ui" font-size="10" '
                         f'fill="#999">{r + 1}</text>')

    return _svg_wrap("\n".join(parts), width, height)


def chessboard_pattern(
    size: int = 8,
    highlighted: Optional[List[Tuple[int, int]]] = None,
    piece_positions: Optional[Dict[Tuple[int, int], str]] = None,
    cell_size: int = 35,
    width: int = 400, height: int = 350,
) -> str:
    """
    Draw a chessboard with optional highlights and pieces.

    piece_positions: {(row,col): emoji_or_letter}
    highlighted: cells to mark with a colored border
    """
    highlighted = highlighted or []
    piece_positions = piece_positions or {}
    gw = size * cell_size
    ox = (width - gw) // 2
    oy = (height - gw) // 2

    parts = []
    for r in range(size):
        for c in range(size):
            x = ox + c * cell_size
            y = oy + r * cell_size
            fill = "#FFFFFF" if (r + c) % 2 == 0 else "#D4A574"
            parts.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                         f'fill="{fill}" stroke="#8B7355" stroke-width="0.5"/>')
            if (r, c) in highlighted:
                parts.append(f'  <rect x="{x + 2}" y="{y + 2}" width="{cell_size - 4}" '
                             f'height="{cell_size - 4}" fill="none" stroke="#FF6B6B" '
                             f'stroke-width="2.5" rx="3"/>')
            if (r, c) in piece_positions:
                parts.append(f'  <text x="{x + cell_size//2}" y="{y + cell_size//2 + 6}" '
                             f'text-anchor="middle" font-family="system-ui" font-size="18" '
                             f'fill="#333">{piece_positions[(r, c)]}</text>')

    # Border
    parts.append(f'  <rect x="{ox}" y="{oy}" width="{gw}" height="{gw}" '
                 f'fill="none" stroke="#5D4E37" stroke-width="2"/>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 4. PAPER FOLDING & CUTTING
# ===================================================================

def paper_fold(
    paper_size: int = 160,
    fold_direction: str = "vertical",
    punch_holes: Optional[List[Tuple[int, int]]] = None,
    show_fold_line: bool = True,
    show_unfolded: bool = False,
    width: int = 400, height: int = 250,
) -> str:
    """
    Draw a paper folding/cutting problem.

    fold_direction: "vertical", "horizontal", "diagonal", "both"
    punch_holes: list of (x_offset, y_offset) relative to paper center
    show_unfolded: if True, show the unfolded result with mirrored holes
    """
    punch_holes = punch_holes or [(15, 15)]
    cx, cy = width // 2, height // 2
    half = paper_size // 2

    parts = []

    if not show_unfolded:
        # Folded paper
        if fold_direction == "vertical":
            # Show right half folded onto left
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{paper_size}" height="{paper_size}" '
                         f'fill="#F8F9FA" stroke="#CCC" stroke-width="1" stroke-dasharray="5,3"/>')
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{half}" height="{paper_size}" '
                         f'fill="#FFFFFF" stroke="#2C3E50" stroke-width="1.5"/>')
            if show_fold_line:
                parts.append(f'  <line x1="{cx}" y1="{cy - half - 5}" '
                             f'x2="{cx}" y2="{cy + half + 5}" '
                             f'stroke="#E74C3C" stroke-width="1.5" stroke-dasharray="6,4"/>')
                parts.append(f'  <text x="{cx + 5}" y="{cy - half - 8}" '
                             f'font-family="system-ui" font-size="9" fill="#E74C3C">fold</text>')
            # Arrow showing fold direction
            parts.append(f'  <path d="M{cx + 40},{cy - half - 15} C{cx + 20},{cy - half - 25} '
                         f'{cx - 10},{cy - half - 25} {cx - 30},{cy - half - 15}" '
                         f'fill="none" stroke="#999" stroke-width="1.5" '
                         f'marker-end="url(#fold-arrow)"/>')
        elif fold_direction == "horizontal":
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{paper_size}" height="{paper_size}" '
                         f'fill="#F8F9FA" stroke="#CCC" stroke-width="1" stroke-dasharray="5,3"/>')
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{paper_size}" height="{half}" '
                         f'fill="#FFFFFF" stroke="#2C3E50" stroke-width="1.5"/>')
            if show_fold_line:
                parts.append(f'  <line x1="{cx - half - 5}" y1="{cy}" '
                             f'x2="{cx + half + 5}" y2="{cy}" '
                             f'stroke="#E74C3C" stroke-width="1.5" stroke-dasharray="6,4"/>')
        elif fold_direction == "both":
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{paper_size}" height="{paper_size}" '
                         f'fill="#F8F9FA" stroke="#CCC" stroke-width="1" stroke-dasharray="5,3"/>')
            parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                         f'width="{half}" height="{half}" '
                         f'fill="#FFFFFF" stroke="#2C3E50" stroke-width="1.5"/>')

        # Punch holes
        for hx, hy in punch_holes:
            parts.append(f'  <circle cx="{cx - half + 20 + hx}" cy="{cy - half + 20 + hy}" '
                         f'r="6" fill="#333" stroke="#111" stroke-width="1"/>')

    else:
        # Unfolded paper with mirrored holes
        parts.append(f'  <rect x="{cx - half}" y="{cy - half}" '
                     f'width="{paper_size}" height="{paper_size}" '
                     f'fill="#FFFFFF" stroke="#2C3E50" stroke-width="1.5"/>')
        if fold_direction in ("vertical", "both"):
            parts.append(f'  <line x1="{cx}" y1="{cy - half}" x2="{cx}" y2="{cy + half}" '
                         f'stroke="#CCC" stroke-width="1" stroke-dasharray="4,3"/>')
        if fold_direction in ("horizontal", "both"):
            parts.append(f'  <line x1="{cx - half}" y1="{cy}" x2="{cx + half}" y2="{cy}" '
                         f'stroke="#CCC" stroke-width="1" stroke-dasharray="4,3"/>')

        for hx, hy in punch_holes:
            base_x = cx - half + 20 + hx
            base_y = cy - half + 20 + hy
            # Original hole
            parts.append(f'  <circle cx="{base_x}" cy="{base_y}" r="6" fill="#333"/>')
            # Mirrored holes
            if fold_direction in ("vertical", "both"):
                mirror_x = 2 * cx - base_x
                parts.append(f'  <circle cx="{mirror_x}" cy="{base_y}" r="6" fill="#333"/>')
            if fold_direction in ("horizontal", "both"):
                mirror_y = 2 * cy - base_y
                parts.append(f'  <circle cx="{base_x}" cy="{mirror_y}" r="6" fill="#333"/>')
            if fold_direction == "both":
                parts.append(f'  <circle cx="{2 * cx - base_x}" cy="{2 * cy - base_y}" r="6" fill="#333"/>')

    # Arrow marker def
    parts.append('  <defs><marker id="fold-arrow" markerWidth="8" markerHeight="6" '
                 'refX="8" refY="3" orient="auto">'
                 '<polygon points="0 0,8 3,0 6" fill="#999"/></marker></defs>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 5. ARROW MAZE / PATH GRID
# ===================================================================

def arrow_maze(
    rows: int, cols: int,
    arrows: Dict[Tuple[int, int], str],
    start: Optional[Tuple[int, int]] = None,
    end: Optional[Tuple[int, int]] = None,
    cell_size: int = 45,
    width: int = 400, height: int = 350,
) -> str:
    """
    Draw a grid where each cell has an arrow showing allowed movement.

    arrows: {(row, col): direction} where direction is
            "up", "down", "left", "right", "up-left", "up-right", etc.
    start/end: (row, col) for start/finish markers
    """
    gw = cols * cell_size
    gh = rows * cell_size
    ox = (width - gw) // 2
    oy = (height - gh) // 2

    arrow_chars = {
        "up": "↑", "down": "↓", "left": "←", "right": "→",
        "up-left": "↖", "up-right": "↗", "down-left": "↙", "down-right": "↘",
    }

    parts = []
    for r in range(rows):
        for c in range(cols):
            x = ox + c * cell_size
            y = oy + r * cell_size
            fill = "#FFFFFF"
            if start and (r, c) == start:
                fill = "#D5F5E3"
            elif end and (r, c) == end:
                fill = "#FADBD8"
            parts.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                         f'fill="{fill}" stroke="#BDC3C7" stroke-width="1"/>')

            if (r, c) in arrows:
                char = arrow_chars.get(arrows[(r, c)], "?")
                parts.append(f'  <text x="{x + cell_size//2}" y="{y + cell_size//2 + 7}" '
                             f'text-anchor="middle" font-family="system-ui" font-size="20" '
                             f'fill="#2C3E50" font-weight="bold">{char}</text>')

    # Start/end labels
    if start:
        sx = ox + start[1] * cell_size + cell_size // 2
        sy = oy + start[0] * cell_size - 5
        parts.append(f'  <text x="{sx}" y="{sy}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="10" fill="#27AE60" '
                     f'font-weight="bold">START</text>')
    if end:
        ex = ox + end[1] * cell_size + cell_size // 2
        ey = oy + end[0] * cell_size - 5
        parts.append(f'  <text x="{ex}" y="{ey}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="10" fill="#E74C3C" '
                     f'font-weight="bold">END</text>')

    # Border
    parts.append(f'  <rect x="{ox}" y="{oy}" width="{gw}" height="{gh}" '
                 f'fill="none" stroke="#2C3E50" stroke-width="2"/>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 6. GEOMETRY — OVERLAPPING SHAPES, TANGRAMS, AREA SHADING
# ===================================================================

def overlapping_shapes(
    shapes: List[Dict[str, Any]],
    width: int = 400, height: int = 300,
) -> str:
    """
    Draw overlapping geometric shapes with transparency.

    shapes: list of dicts with keys:
        type: "circle", "rectangle", "triangle"
        x, y: center position
        size: radius or half-width
        color: fill color
        opacity: 0.0-1.0
        label: optional text label
    """
    parts = []
    for s in shapes:
        opacity = s.get("opacity", 0.5)
        color = s.get("color", SHAPE_COLORS[0])
        x, y = s["x"], s["y"]
        sz = s.get("size", 40)

        if s["type"] == "circle":
            parts.append(f'  <circle cx="{x}" cy="{y}" r="{sz}" '
                         f'fill="{color}" fill-opacity="{opacity}" '
                         f'stroke="#333" stroke-width="1.5"/>')
        elif s["type"] == "rectangle":
            parts.append(f'  <rect x="{x - sz}" y="{y - sz * 0.7}" '
                         f'width="{sz * 2}" height="{sz * 1.4}" '
                         f'fill="{color}" fill-opacity="{opacity}" '
                         f'stroke="#333" stroke-width="1.5" rx="3"/>')
        elif s["type"] == "triangle":
            pts = f"{x},{y - sz} {x - sz},{y + sz * 0.6} {x + sz},{y + sz * 0.6}"
            parts.append(f'  <polygon points="{pts}" '
                         f'fill="{color}" fill-opacity="{opacity}" '
                         f'stroke="#333" stroke-width="1.5"/>')

        if "label" in s:
            parts.append(f'  <text x="{x}" y="{y + 5}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="14" fill="#333" '
                         f'font-weight="bold">{s["label"]}</text>')

    return _svg_wrap("\n".join(parts), width, height)


def tangram_pieces(
    pieces: List[Dict[str, Any]],
    outline_only: bool = False,
    width: int = 400, height: int = 300,
) -> str:
    """
    Draw tangram-style puzzle pieces.

    pieces: list of dicts with keys:
        points: list of (x, y) tuples defining the polygon
        color: fill color
        label: optional label
    """
    parts = []
    for i, piece in enumerate(pieces):
        pts_str = " ".join(f"{x},{y}" for x, y in piece["points"])
        color = piece.get("color", SHAPE_COLORS[i % len(SHAPE_COLORS)])
        fill = "none" if outline_only else color
        parts.append(f'  <polygon points="{pts_str}" fill="{fill}" '
                     f'stroke="#2C3E50" stroke-width="2" fill-opacity="0.7"/>')
        if "label" in piece:
            cx = sum(x for x, y in piece["points"]) / len(piece["points"])
            cy = sum(y for x, y in piece["points"]) / len(piece["points"])
            parts.append(f'  <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="12" fill="#333" '
                         f'font-weight="bold">{piece["label"]}</text>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 7. PATTERN / SEQUENCE VISUALS
# ===================================================================

def shape_sequence(
    shapes: List[Tuple[str, str]],
    blank_index: int = -1,
    spacing: int = 55,
    width: int = 400, height: int = 120,
) -> str:
    """
    Draw a sequence of shapes with one blank (the question).

    shapes: list of (shape_type, color) tuples
    blank_index: which position to show as "?" (-1 = last)
    """
    if blank_index == -1:
        blank_index = len(shapes) - 1

    n = len(shapes)
    total_w = (n - 1) * spacing
    start_x = (width - total_w) // 2
    cy = height // 2
    r = 18

    parts = []
    for i, (shape, color) in enumerate(shapes):
        x = start_x + i * spacing

        if i == blank_index:
            # Question mark
            parts.append(f'  <circle cx="{x}" cy="{cy}" r="{r + 2}" '
                         f'fill="#FFF3CD" stroke="#E67E22" stroke-width="2" stroke-dasharray="5,3"/>')
            parts.append(f'  <text x="{x}" y="{cy + 7}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="22" fill="#E67E22" '
                         f'font-weight="bold">?</text>')
        else:
            if shape == "circle":
                parts.append(f'  <circle cx="{x}" cy="{cy}" r="{r}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
            elif shape == "square":
                parts.append(f'  <rect x="{x - r}" y="{cy - r}" width="{r * 2}" height="{r * 2}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5" rx="2"/>')
            elif shape == "triangle":
                pts = f"{x},{cy - r} {x - r},{cy + r * 0.7} {x + r},{cy + r * 0.7}"
                parts.append(f'  <polygon points="{pts}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
            elif shape == "star":
                # 5-pointed star
                star_pts = []
                for j in range(10):
                    angle = math.pi / 2 + j * math.pi / 5
                    rad = r if j % 2 == 0 else r * 0.45
                    star_pts.append(f"{x + rad * math.cos(angle):.1f},{cy - rad * math.sin(angle):.1f}")
                parts.append(f'  <polygon points="{" ".join(star_pts)}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
            elif shape == "diamond":
                pts = f"{x},{cy - r} {x + r},{cy} {x},{cy + r} {x - r},{cy}"
                parts.append(f'  <polygon points="{pts}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5"/>')
            elif shape == "hexagon":
                hex_pts = []
                for j in range(6):
                    angle = j * math.pi / 3
                    hex_pts.append(f"{x + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
                parts.append(f'  <polygon points="{" ".join(hex_pts)}" '
                             f'fill="{color}" stroke="#333" stroke-width="1.5"/>')

        # Separator dots between shapes (not after last)
        if i < n - 1:
            parts.append(f'  <text x="{x + spacing // 2}" y="{cy + 5}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="14" fill="#CCC">,</text>')

    return _svg_wrap("\n".join(parts), width, height)


def growing_pattern(
    stages: List[List[Tuple[int, int]]],
    cell_size: int = 12,
    color: str = "#4ECDC4",
    width: int = 400, height: int = 150,
) -> str:
    """
    Draw a growing pattern of cells at each stage.

    stages: list of cell coordinate lists [(row, col), ...]
            Each stage is drawn side by side with a stage number
    """
    parts = []
    n = len(stages)
    gap = width // (n + 1)

    for i, cells in enumerate(stages):
        cx = gap * (i + 1)
        if not cells:
            continue
        min_r = min(r for r, c in cells)
        max_r = max(r for r, c in cells)
        min_c = min(c for r, c in cells)
        max_c = max(c for r, c in cells)
        gw = (max_c - min_c + 1) * cell_size
        gh = (max_r - min_r + 1) * cell_size
        ox = cx - gw // 2
        oy = height // 2 - gh // 2

        for r, c in cells:
            x = ox + (c - min_c) * cell_size
            y = oy + (r - min_r) * cell_size
            parts.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                         f'fill="{color}" stroke="#333" stroke-width="0.8" rx="1"/>')

        # Stage label
        parts.append(f'  <text x="{cx}" y="{oy + gh + 18}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="11" fill="#666">Stage {i + 1}</text>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 8. COINS, STAMPS, COUNTING OBJECTS
# ===================================================================

def coin_arrangement(
    coins: List[Tuple[int, str]],
    layout: str = "row",
    width: int = 400, height: int = 150,
) -> str:
    """
    Draw coins with denominations.

    coins: list of (value, currency_symbol) — e.g. [(5, "¢"), (10, "¢"), (25, "¢")]
    layout: "row" or "scattered"
    """
    parts = []
    n = len(coins)

    if layout == "row":
        spacing = min(60, (width - 40) // max(n, 1))
        start_x = (width - (n - 1) * spacing) // 2
        cy = height // 2

        for i, (val, sym) in enumerate(coins):
            x = start_x + i * spacing
            r = 22
            # Coin body
            parts.append(f'  <circle cx="{x}" cy="{cy}" r="{r}" '
                         f'fill="#F1C40F" stroke="#D4AC0D" stroke-width="2"/>')
            parts.append(f'  <circle cx="{x}" cy="{cy}" r="{r - 4}" '
                         f'fill="none" stroke="#D4AC0D" stroke-width="1" stroke-dasharray="2,2"/>')
            # Value
            parts.append(f'  <text x="{x}" y="{cy + 1}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="12" fill="#7D6608" '
                         f'font-weight="bold">{val}{sym}</text>')

    return _svg_wrap("\n".join(parts), width, height)


def domino_tile(
    top: int, bottom: int,
    x: int = 0, y: int = 0,
    tile_w: int = 40, tile_h: int = 80,
) -> str:
    """Return SVG elements for a single domino tile (not wrapped)."""
    parts = []
    parts.append(f'  <rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" '
                 f'rx="5" fill="#FDFEFE" stroke="#2C3E50" stroke-width="2"/>')
    # Divider line
    parts.append(f'  <line x1="{x + 3}" y1="{y + tile_h//2}" '
                 f'x2="{x + tile_w - 3}" y2="{y + tile_h//2}" '
                 f'stroke="#2C3E50" stroke-width="1.5"/>')

    # Pips for top half
    def draw_half_pips(cx, cy, count, r=3):
        pip_parts = []
        offsets = {
            0: [],
            1: [(0, 0)],
            2: [(-7, -7), (7, 7)],
            3: [(-7, -7), (0, 0), (7, 7)],
            4: [(-7, -7), (7, -7), (-7, 7), (7, 7)],
            5: [(-7, -7), (7, -7), (0, 0), (-7, 7), (7, 7)],
            6: [(-7, -7), (7, -7), (-7, 0), (7, 0), (-7, 7), (7, 7)],
        }
        for dx, dy in offsets.get(count, []):
            pip_parts.append(f'  <circle cx="{cx + dx}" cy="{cy + dy}" r="{r}" fill="#2C3E50"/>')
        return "\n".join(pip_parts)

    parts.append(draw_half_pips(x + tile_w // 2, y + tile_h // 4, top))
    parts.append(draw_half_pips(x + tile_w // 2, y + 3 * tile_h // 4, bottom))

    return "\n".join(parts)


def domino_row(
    dominoes: List[Tuple[int, int]],
    width: int = 400, height: int = 150,
) -> str:
    """Draw a row of domino tiles."""
    tile_w, tile_h = 40, 80
    n = len(dominoes)
    spacing = min(55, (width - 40) // max(n, 1))
    start_x = (width - (n - 1) * spacing - tile_w) // 2
    oy = (height - tile_h) // 2

    parts = []
    for i, (top, bottom) in enumerate(dominoes):
        x = start_x + i * spacing
        parts.append(domino_tile(top, bottom, x, oy, tile_w, tile_h))

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 9. FLOW DIAGRAMS / MACHINES
# ===================================================================

def number_machine(
    inputs: List[int],
    operations: List[str],
    outputs: List[Optional[int]],
    width: int = 400, height: int = 200,
) -> str:
    """
    Draw a number machine / function machine.

    inputs: list of input values
    operations: list of operation labels (e.g., ["×2", "+3"])
    outputs: list of output values (None = "?")
    """
    parts = []
    n_ops = len(operations)
    total_stages = 1 + n_ops + 1  # input + ops + output
    stage_w = width // total_stages
    cy = height // 2

    # Arrow marker
    parts.append('  <defs><marker id="m-arw" markerWidth="10" markerHeight="7" '
                 'refX="10" refY="3.5" orient="auto">'
                 '<polygon points="0 0,10 3.5,0 7" fill="#333"/></marker></defs>')

    # Input box
    ix = stage_w // 2
    for i, val in enumerate(inputs):
        iy = cy + (i - (len(inputs) - 1) / 2) * 35
        parts.append(f'  <rect x="{ix - 25}" y="{iy - 18}" width="50" height="36" '
                     f'rx="5" fill="#3498DB" stroke="#2C3E50" stroke-width="2"/>')
        parts.append(f'  <text x="{ix}" y="{iy + 6}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="16" fill="white" '
                     f'font-weight="bold">{val}</text>')

    # Operation boxes
    for j, op in enumerate(operations):
        ox = stage_w * (j + 1) + stage_w // 2
        # Arrow in
        parts.append(f'  <line x1="{ox - stage_w//2 + 30}" y1="{cy}" '
                     f'x2="{ox - 40}" y2="{cy}" stroke="#333" stroke-width="2" '
                     f'marker-end="url(#m-arw)"/>')
        # Machine box
        parts.append(f'  <rect x="{ox - 35}" y="{cy - 30}" width="70" height="60" '
                     f'rx="10" fill="#F39C12" stroke="#E67E22" stroke-width="3"/>')
        parts.append(f'  <text x="{ox}" y="{cy - 5}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="10" fill="#333">MACHINE</text>')
        parts.append(f'  <text x="{ox}" y="{cy + 15}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="16" fill="#333" '
                     f'font-weight="bold">{op}</text>')

    # Arrow to output
    last_ox = stage_w * n_ops + stage_w // 2
    out_x = stage_w * (n_ops + 1) + stage_w // 2
    parts.append(f'  <line x1="{last_ox + 40}" y1="{cy}" '
                 f'x2="{out_x - 30}" y2="{cy}" stroke="#333" stroke-width="2" '
                 f'marker-end="url(#m-arw)"/>')

    # Output box
    for i, val in enumerate(outputs):
        oy = cy + (i - (len(outputs) - 1) / 2) * 35
        color = "#2ECC71" if val is not None else "#FFF3CD"
        text = str(val) if val is not None else "?"
        text_color = "white" if val is not None else "#E67E22"
        parts.append(f'  <rect x="{out_x - 25}" y="{oy - 18}" width="50" height="36" '
                     f'rx="5" fill="{color}" stroke="#27AE60" stroke-width="2"/>')
        parts.append(f'  <text x="{out_x}" y="{oy + 6}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="16" fill="{text_color}" '
                     f'font-weight="bold">{text}</text>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 10. CLOCK / TIME VISUALS
# ===================================================================

def analog_clock(
    hour: int, minute: int,
    show_numbers: bool = True,
    highlight_angle: bool = False,
    radius: int = 70,
    width: int = 200, height: int = 200,
) -> str:
    """Draw an analog clock face showing a specific time."""
    cx, cy = width // 2, height // 2
    r = radius

    parts = []
    # Clock face
    parts.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" '
                 f'fill="#FFFFFF" stroke="#2C3E50" stroke-width="3"/>')

    # Hour markers
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = cx + (r - 8) * math.cos(angle)
        y1 = cy + (r - 8) * math.sin(angle)
        x2 = cx + (r - 2) * math.cos(angle)
        y2 = cy + (r - 2) * math.sin(angle)
        parts.append(f'  <line x1="{x1:.1f}" y1="{y1:.1f}" '
                     f'x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="#2C3E50" stroke-width="2"/>')
        if show_numbers:
            tx = cx + (r - 18) * math.cos(angle)
            ty = cy + (r - 18) * math.sin(angle)
            num = 12 if i == 0 else i
            parts.append(f'  <text x="{tx:.1f}" y="{ty + 4:.1f}" text-anchor="middle" '
                         f'font-family="system-ui" font-size="11" fill="#333" '
                         f'font-weight="bold">{num}</text>')

    # Hour hand
    h_angle = math.radians((hour % 12 + minute / 60) * 30 - 90)
    hx = cx + (r * 0.5) * math.cos(h_angle)
    hy = cy + (r * 0.5) * math.sin(h_angle)
    parts.append(f'  <line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" '
                 f'stroke="#2C3E50" stroke-width="4" stroke-linecap="round"/>')

    # Minute hand
    m_angle = math.radians(minute * 6 - 90)
    mx = cx + (r * 0.7) * math.cos(m_angle)
    my = cy + (r * 0.7) * math.sin(m_angle)
    parts.append(f'  <line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" '
                 f'stroke="#E74C3C" stroke-width="2.5" stroke-linecap="round"/>')

    # Center dot
    parts.append(f'  <circle cx="{cx}" cy="{cy}" r="4" fill="#2C3E50"/>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# 11. MIRROR / SYMMETRY
# ===================================================================

def mirror_image(
    left_cells: List[Tuple[int, int]],
    grid_rows: int = 5, grid_cols: int = 10,
    mirror_axis: str = "vertical",
    cell_size: int = 25,
    fill_color: str = "#4ECDC4",
    show_mirror: bool = True,
    width: int = 400, height: int = 200,
) -> str:
    """
    Draw a grid with a pattern on one side and a mirror line.
    The student must find the reflected pattern.

    left_cells: list of (row, col) for the filled cells on the left side
    mirror_axis: "vertical" — mirror line is in the middle column
    """
    gw = grid_cols * cell_size
    gh = grid_rows * cell_size
    ox = (width - gw) // 2
    oy = (height - gh) // 2

    parts = []
    # Grid
    for r in range(grid_rows):
        for c in range(grid_cols):
            x = ox + c * cell_size
            y = oy + r * cell_size
            fill = fill_color if (r, c) in left_cells else "#FFFFFF"
            parts.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                         f'fill="{fill}" stroke="#BDC3C7" stroke-width="0.8"/>')

    # Mirror line
    if show_mirror and mirror_axis == "vertical":
        mx = ox + (grid_cols // 2) * cell_size
        parts.append(f'  <line x1="{mx}" y1="{oy - 8}" x2="{mx}" y2="{oy + gh + 8}" '
                     f'stroke="#E74C3C" stroke-width="2" stroke-dasharray="6,4"/>')
        parts.append(f'  <text x="{mx}" y="{oy - 12}" text-anchor="middle" '
                     f'font-family="system-ui" font-size="9" fill="#E74C3C">mirror</text>')

    return _svg_wrap("\n".join(parts), width, height)


# ===================================================================
# DEMO: Generate sample SVGs for each type
# ===================================================================

if __name__ == "__main__":
    import os

    demo_dir = "svg_demos_g3g4"
    os.makedirs(demo_dir, exist_ok=True)

    demos = {
        "01_isometric_cubes": isometric_cubes(
            structure=[
                [[1, 1, 1], [1, 1, 0], [1, 0, 0]],  # bottom layer
                [[1, 1, 0], [1, 0, 0], [0, 0, 0]],  # middle layer
                [[1, 0, 0], [0, 0, 0], [0, 0, 0]],  # top layer
            ],
            highlight_cells=[(2, 0, 0)],
            show_count=True,
        ),
        "02_dice_net": dice_net(
            faces={"top": 1, "front": 3, "right": 5, "bottom": 6, "left": 2, "back": 4},
            fold_face="top",
        ),
        "03_balance_scale": balance_scale(
            left_items=[("circle", "#FF6B6B", 2), ("square", "#4ECDC4", 1)],
            right_items=[("triangle", "#F1C40F", 3)],
        ),
        "04_colored_grid": colored_grid(
            rows=4, cols=4,
            colored_cells={
                (0, 0): "#FF6B6B", (0, 3): "#4ECDC4",
                (1, 1): "#F1C40F", (1, 2): "#9B59B6",
                (2, 1): "#2ECC71", (2, 2): "#FF6B6B",
                (3, 0): "#4ECDC4", (3, 3): "#F1C40F",
            },
            show_coords=True,
        ),
        "05_paper_fold": paper_fold(
            fold_direction="vertical",
            punch_holes=[(20, 30), (20, 60)],
        ),
        "06_paper_unfold": paper_fold(
            fold_direction="vertical",
            punch_holes=[(20, 30), (20, 60)],
            show_unfolded=True,
        ),
        "07_arrow_maze": arrow_maze(
            rows=3, cols=4,
            arrows={
                (0, 0): "right", (0, 1): "down", (0, 2): "right", (0, 3): "down",
                (1, 0): "down", (1, 1): "right", (1, 2): "down", (1, 3): "down",
                (2, 0): "right", (2, 1): "right", (2, 2): "right", (2, 3): "right",
            },
            start=(0, 0), end=(2, 3),
        ),
        "08_shape_sequence": shape_sequence(
            shapes=[
                ("circle", "#FF6B6B"), ("square", "#4ECDC4"),
                ("circle", "#FF6B6B"), ("square", "#4ECDC4"),
                ("circle", "#FF6B6B"), ("square", "#4ECDC4"),
            ],
            blank_index=5,
        ),
        "09_growing_pattern": growing_pattern(
            stages=[
                [(0, 0)],
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)],
            ],
        ),
        "10_number_machine": number_machine(
            inputs=[7],
            operations=["×3", "-4"],
            outputs=[None],
        ),
        "11_clock": analog_clock(hour=3, minute=45),
        "12_dominos": domino_row(
            dominoes=[(3, 5), (5, 2), (2, 6), (6, 1)],
        ),
        "13_coins": coin_arrangement(
            coins=[(5, "¢"), (10, "¢"), (25, "¢"), (10, "¢"), (5, "¢")],
        ),
        "14_mirror": mirror_image(
            left_cells=[(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 0), (3, 2)],
            grid_rows=4, grid_cols=8,
        ),
        "15_overlapping": overlapping_shapes(
            shapes=[
                {"type": "circle", "x": 170, "y": 150, "size": 60, "color": "#FF6B6B", "opacity": 0.4, "label": "A"},
                {"type": "circle", "x": 230, "y": 150, "size": 60, "color": "#4ECDC4", "opacity": 0.4, "label": "B"},
            ],
        ),
        "16_chessboard": chessboard_pattern(
            size=5,
            highlighted=[(1, 2), (2, 3)],
            piece_positions={(0, 0): "♔", (4, 4): "♚"},
            cell_size=40,
            width=300, height=280,
        ),
    }

    for name, svg in demos.items():
        path = os.path.join(demo_dir, f"{name}.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"  ✓ {name}.svg")

    print(f"\n{len(demos)} demo SVGs saved to {demo_dir}/")
