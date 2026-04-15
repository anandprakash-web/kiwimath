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


# ---------------------------------------------------------------------------
# dice_face
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dots", [1, 2, 3, 4, 5, 6])
def test_dice_face_pip_count(dots: int):
    svg = render_svg("dice_face", {"dots": dots})
    assert svg.startswith("<svg")
    # One <circle> per pip
    assert svg.count("<circle") == dots


def test_dice_face_out_of_range_clamped():
    svg_hi = render_svg("dice_face", {"dots": 999})
    assert svg_hi.count("<circle") == 6
    svg_lo = render_svg("dice_face", {"dots": 0})
    assert svg_lo.count("<circle") == 1


# ---------------------------------------------------------------------------
# triangle_subdivision
# ---------------------------------------------------------------------------


def test_triangle_basic_3_has_one_internal_line():
    svg = render_svg("triangle_subdivision", {"layout": "basic_3"})
    assert svg.startswith("<svg")
    assert svg.count("<polygon") == 1
    assert svg.count("<line") == 1


def test_triangle_basic_4_has_three_internal_lines():
    svg = render_svg("triangle_subdivision", {"layout": "basic_4"})
    assert svg.count("<line") == 3


def test_triangle_fan_has_two_internal_lines():
    svg = render_svg("triangle_subdivision", {"layout": "fan"})
    assert svg.count("<line") == 2


def test_triangle_unknown_layout_falls_back_to_empty():
    svg = render_svg("triangle_subdivision", {"layout": "this_is_not_a_layout"})
    # Just the outer polygon, no subdivisions
    assert svg.count("<polygon") == 1
    assert svg.count("<line") == 0


# ---------------------------------------------------------------------------
# grid_colored
# ---------------------------------------------------------------------------


def test_grid_colored_cell_count():
    svg = render_svg("grid_colored", {"size": 4, "colored_cells": [[0, 0], [1, 2]]})
    # 16 total rects
    assert svg.count("<rect") == 16


def test_grid_colored_uses_custom_color():
    svg = render_svg(
        "grid_colored",
        {"size": 3, "colored_cells": [[0, 0]], "color": "#123456"},
    )
    assert "#123456" in svg


def test_grid_colored_handles_no_colored_cells():
    svg = render_svg("grid_colored", {"size": 2, "colored_cells": []})
    assert svg.count("<rect") == 4


def test_grid_colored_size_clamped():
    svg = render_svg("grid_colored", {"size": 999, "colored_cells": []})
    # 10 is the max, so 100 rects
    assert svg.count("<rect") == 100
