import pytest

from app.services.svg_generators import (
    UnknownGeneratorError,
    available_generators,
    render_svg,
)


def test_object_row_with_cross_out_renders():
    svg = render_svg("object_row_with_cross_out", {"count_from": 5, "cross_out": 2, "object": "apples"})
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    # 5 apple emojis × 1 text element each = 5 text tags
    assert svg.count("<text") == 5
    # 2 crossed out × 2 lines per X = 4 lines
    assert svg.count("<line") == 4


def test_unknown_generator_raises():
    with pytest.raises(UnknownGeneratorError):
        render_svg("not_a_real_thing", {})


def test_available_generators_registry():
    gens = available_generators()
    assert "object_row_with_cross_out" in gens


def test_cross_out_clamped_to_total():
    # Crossing out more than exist → clamped
    svg = render_svg("object_row_with_cross_out", {"count_from": 3, "cross_out": 10})
    # 3 objects × 2 lines per X = 6 lines max
    assert svg.count("<line") == 6
