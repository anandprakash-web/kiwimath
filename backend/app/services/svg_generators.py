"""
SVG generators for Kiwimath visual questions.

Each generator is a function that takes a params dict and returns an SVG string.
The app displays the SVG inline — no image hosting needed, and it scales crisply.

v0 ships one generator: `object_row_with_cross_out`.
Next generators planned: `triangle_subdivision`, `grid_colored`, `cube_stack`.
"""

from __future__ import annotations

from typing import Any, Callable, Dict


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


# Registry: generator name -> function
_REGISTRY: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "object_row_with_cross_out": object_row_with_cross_out,
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
