"""SVG renderer for olympiad visual_ref objects.

Imported by backend/app/api/olympiad.py (this directory is added to sys.path).
Resolves {"component": "stored_svg", "key": <question_id>} against the
sidecar svg_store.json (inline SVGs copied from the QA-verified v2 bank).
"""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_store = None


def _load():
    global _store
    if _store is None:
        path = os.path.join(_DIR, "svg_store.json")
        try:
            with open(path) as f:
                _store = json.load(f)
        except OSError:
            _store = {}
    return _store


def render_visual_ref(ref):
    if not isinstance(ref, dict):
        return None
    if ref.get("component") == "stored_svg":
        return _load().get(ref.get("key"))
    if isinstance(ref.get("svg"), str):
        return ref["svg"]
    return None
