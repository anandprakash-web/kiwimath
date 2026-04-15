"""
Preview API for content authors.

GET /preview/svg/{generator}?...     → returns raw SVG (image/svg+xml)
GET /preview/gallery                 → HTML gallery page showing every
                                        generator with a few sample param sets

The content team uses these while authoring visual questions — they can
see exactly what a question will look like before wiring it into a JSON file.
"""

from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response

from app.services.svg_generators import (
    UnknownGeneratorError,
    available_generators,
    render_svg,
)

router = APIRouter()


def _parse_params(raw: str) -> Dict[str, Any]:
    """Accept either a JSON object string or URL-encoded k=v pairs."""
    if not raw:
        return {}
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"invalid JSON params: {e}")
    # Fallback: k=v,k=v
    out: Dict[str, Any] = {}
    for pair in raw.split(","):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k, v = k.strip(), v.strip()
        # Try to coerce to number
        try:
            out[k] = int(v)
            continue
        except ValueError:
            pass
        try:
            out[k] = float(v)
            continue
        except ValueError:
            pass
        # Try JSON (for lists)
        if v.startswith("[") or v.startswith("{"):
            try:
                out[k] = json.loads(v)
                continue
            except json.JSONDecodeError:
                pass
        out[k] = v
    return out


@router.get("/preview/svg/{generator}")
def preview_svg(
    generator: str,
    params: str = Query(
        "", description="JSON object or k=v,k=v string of generator params"
    ),
):
    """Return raw SVG for a generator + params. Use in <img> tags or browser."""
    try:
        parsed = _parse_params(params)
        svg = render_svg(generator, parsed)
    except UnknownGeneratorError as e:
        raise HTTPException(404, str(e))
    return Response(content=svg, media_type="image/svg+xml")


# ---------------------------------------------------------------------------
# Gallery: an HTML page showing every generator with sample parameter sets.
# ---------------------------------------------------------------------------


# (generator, title, list of example param sets)
_GALLERY_EXAMPLES = [
    (
        "object_row_with_cross_out",
        "Object Row with Cross-Out",
        [
            {"count_from": 5, "cross_out": 2, "object": "apples"},
            {"count_from": 9, "cross_out": 3, "object": "balloons"},
            {"count_from": 7, "cross_out": 4, "object": "stickers"},
        ],
    ),
    (
        "dice_face",
        "Dice Face",
        [{"dots": n} for n in range(1, 7)],
    ),
    (
        "triangle_subdivision",
        "Triangle Subdivision",
        [
            {"layout": "basic_3"},
            {"layout": "basic_4"},
            {"layout": "fan"},
        ],
    ),
    (
        "grid_colored",
        "Grid Colored",
        [
            {"size": 4, "colored_cells": [[0, 0], [0, 1], [1, 0], [3, 3]]},
            {"size": 5, "colored_cells": [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]]},
            {"size": 3, "colored_cells": [[0, 1], [1, 0], [1, 2], [2, 1]]},
        ],
    ),
]


@router.get("/preview/gallery", response_class=HTMLResponse)
def preview_gallery():
    """Browsable page showing every generator rendered with sample params."""
    registered = set(available_generators())
    sections: list[str] = []

    for gen_name, title, examples in _GALLERY_EXAMPLES:
        if gen_name not in registered:
            continue
        tiles = []
        for params in examples:
            params_str = urllib.parse.quote(json.dumps(params))
            src = f"/preview/svg/{gen_name}?params={params_str}"
            label = json.dumps(params, separators=(",", ":"))
            tiles.append(
                f'<figure class="tile">'
                f'<img src="{src}" alt="{label}"/>'
                f'<figcaption><code>{label}</code></figcaption>'
                f"</figure>"
            )
        sections.append(
            f'<section><h2>{title} <small>({gen_name})</small></h2>'
            f'<div class="grid">{"".join(tiles)}</div></section>'
        )

    # Unknown or not-yet-exampled generators
    not_shown = sorted(registered - {g for (g, _, _) in _GALLERY_EXAMPLES})
    if not_shown:
        sections.append(
            '<section><h2>Other registered generators</h2>'
            f'<p>{", ".join(f"<code>{n}</code>" for n in not_shown)}</p>'
            "</section>"
        )

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Kiwimath SVG Gallery</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    max-width: 1100px; margin: 40px auto; padding: 0 20px;
    background: #FFFBF0; color: #2E2E2E;
  }}
  h1 {{ color: #558B2F; }}
  h2 {{ margin-top: 36px; color: #558B2F; }}
  h2 small {{ color: #999; font-weight: normal; font-size: 0.6em; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }}
  .tile {{
    background: white; border: 2px solid #DCEDC8; border-radius: 12px;
    padding: 14px; margin: 0; text-align: center;
  }}
  .tile img {{ max-width: 100%; height: 160px; object-fit: contain; }}
  .tile figcaption {{ margin-top: 8px; font-size: 12px; }}
  code {{ background: #F0F0F0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
  .tip {{ background: #FFF3E0; border-left: 4px solid #FFB74D;
          padding: 12px 16px; border-radius: 8px; margin: 20px 0; }}
</style>
</head>
<body>
<h1>Kiwimath SVG Gallery 🥝</h1>
<p>Every registered SVG generator, rendered with a few example parameter sets.</p>
<div class="tip">
  <strong>For content authors:</strong> To use a generator in a question, set its
  <code>visual</code> field to <code>{{"type": "svg_generator", "generator": "&lt;name&gt;", "params": {{...}}}}</code>.
  To test your own params live, hit
  <code>/preview/svg/&lt;generator&gt;?params={{"...":"..."}}</code> in the browser.
</div>
{"".join(sections)}
</body>
</html>"""
    return HTMLResponse(content=html)
