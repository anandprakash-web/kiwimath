#!/usr/bin/env python3
"""L3 Chapter 15 — Perimeter, Area & Circles (Geometry · Space & Surface).
Perimeter & area of rectangle/square/triangle/parallelogram, composite shapes,
then the circle: radius/diameter/circumference, the surprise ratio π = C/d,
and area = πr². Uses π ≈ 22/7 or 3.14."""
import math
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, area_grid, rect_fig)
from l3_figs import polygon, INK, ORANGE, SKY, GRASS, BERRY, PURPLE, GOLD


# ── local inline figures ────────────────────────────────────────────────
def parallelogram_fig(base, height, slant=40):
    """A parallelogram with base and a dashed height line."""
    x0, y0 = 115, 150
    w, h = 180, 100
    pts = [(x0 + slant, y0 - h), (x0 + slant + w, y0 - h), (x0 + w, y0), (x0, y0)]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{PURPLE}1f" stroke="{PURPLE}" stroke-width="2.4"/>',
         # height (dashed vertical from top-left vertex down to base)
         f'<line x1="{x0+slant}" y1="{y0-h}" x2="{x0+slant}" y2="{y0}" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>',
         f'<polyline points="{x0+slant+12},{y0} {x0+slant+12},{y0-12} {x0+slant},{y0-12}" fill="none" stroke="{ORANGE}" stroke-width="1.2"/>',
         f'<text x="{x0+w/2+slant/2:.0f}" y="{y0+22}" text-anchor="middle" font-size="14" font-weight="800" fill="{PURPLE}">base = {base}</text>',
         f'<text x="{x0+slant-8}" y="{y0-h/2:.0f}" text-anchor="end" font-size="13" font-weight="800" fill="{ORANGE}">height = {height}</text>']
    return svg("".join(s), 360, 184)


def triangle_area_fig(base, height):
    """A triangle with base and dashed height (altitude)."""
    pts = [(110, 30), (40, 165), (270, 165)]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2.4"/>',
         f'<line x1="110" y1="30" x2="110" y2="165" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>',
         f'<polyline points="122,165 122,153 110,153" fill="none" stroke="{ORANGE}" stroke-width="1.2"/>',
         f'<text x="155" y="186" text-anchor="middle" font-size="14" font-weight="800" fill="{GRASS}">base = {base}</text>',
         f'<text x="100" y="105" text-anchor="end" font-size="14" font-weight="800" fill="{ORANGE}">height = {height}</text>']
    return svg("".join(s), 320, 200)


def composite_L():
    """An L-shape made of two rectangles, with dimensions."""
    s = [
        # outer L outline (units in px)
        f'<path d="M40,30 L200,30 L200,100 L300,100 L300,180 L40,180 Z" fill="{SKY}1f" stroke="{SKY}" stroke-width="2.4"/>',
        # split dashed line
        f'<line x1="200" y1="100" x2="200" y2="180" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="5 4"/>',
        f'<text x="120" y="22" text-anchor="middle" font-size="13" font-weight="800" fill="{SKY}">8 cm</text>',
        f'<text x="32" y="108" text-anchor="end" font-size="13" font-weight="800" fill="{SKY}">7 cm</text>',
        f'<text x="170" y="200" text-anchor="middle" font-size="12" fill="{INK}">total width 13 cm, foot height 4 cm</text>',
    ]
    return svg("".join(s), 330, 210)


def circle_parts(r_lab="r", d_lab="d"):
    """A circle showing centre, radius and diameter."""
    cx, cy, r = 150, 110, 90
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{ORANGE}12" stroke="{ORANGE}" stroke-width="2.6"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>',
         # radius
         f'<line x1="{cx}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{BERRY}" stroke-width="2.4"/>',
         f'<text x="{cx+r/2}" y="{cy-8}" text-anchor="middle" font-size="14" font-weight="800" fill="{BERRY}">{r_lab}</text>',
         # diameter
         f'<line x1="{cx-r}" y1="{cy+24}" x2="{cx+r}" y2="{cy+24}" stroke="{SKY}" stroke-width="2.4"/>',
         f'<text x="{cx}" y="{cy+44}" text-anchor="middle" font-size="14" font-weight="800" fill="{SKY}">{d_lab}</text>',
         f'<text x="{cx}" y="{cy-50}" text-anchor="middle" font-size="12" fill="{INK}">centre</text>']
    return svg("".join(s), 300, 224)


def circ_unroll():
    """A circle of diameter d 'rolled out' to show C is about 3.14 d long."""
    s = [f'<circle cx="60" cy="50" r="40" fill="{ORANGE}12" stroke="{ORANGE}" stroke-width="2.4"/>',
         f'<line x1="20" y1="50" x2="100" y2="50" stroke="{SKY}" stroke-width="2"/>',
         f'<text x="60" y="44" text-anchor="middle" font-size="12" font-weight="800" fill="{SKY}">d</text>',
         # rolled out line below, length ~ pi*d
         f'<line x1="20" y1="130" x2="20" y2="142" stroke="{INK}" stroke-width="2"/>',
         f'<line x1="20" y1="136" x2="271" y2="136" stroke="{ORANGE}" stroke-width="3"/>',
         f'<line x1="271" y1="130" x2="271" y2="142" stroke="{INK}" stroke-width="2"/>',
         # tick at each d
         f'<line x1="100" y1="131" x2="100" y2="141" stroke="{INK}" stroke-width="1.4" stroke-dasharray="2 2"/>',
         f'<line x1="180" y1="131" x2="180" y2="141" stroke="{INK}" stroke-width="1.4" stroke-dasharray="2 2"/>',
         f'<line x1="260" y1="131" x2="260" y2="141" stroke="{INK}" stroke-width="1.4" stroke-dasharray="2 2"/>',
         f'<text x="145" y="162" text-anchor="middle" font-size="12" fill="{INK}">the rolled-out edge ≈ 3 diameters + a little = π × d</text>']
    return svg("".join(s), 300, 176)


def build(chapter):
    b = []; A = b.append

    # ── HOOK ────────────────────────────────────────────────────────────
    A(big_q("You have <b>20 metres</b> of fence. What shape of garden gives you the <em>most growing "
            "space</em> inside? A long thin strip? A square? Could a <b>circle</b> beat them all? Hidden in "
            "this question is the difference between <b>perimeter</b> (the fence) and <b>area</b> (the "
            "space) — and a number so special it has its own symbol: <b>π</b>."))
    A(kiwi("Hello again, it's <b>Kiwi</b>! 🟠 Two different questions live in every flat shape: "
           "<b>how far around?</b> (perimeter) and <b>how much surface inside?</b> (area). We measure "
           "perimeter in length units like cm, and area in <em>square</em> units like cm². Let's build "
           "every area formula from one simple idea — counting squares — and finish with the magic of "
           "circles."))

    # ── RECTANGLE & SQUARE ──────────────────────────────────────────────
    A(H("Area by counting squares: rectangle & square"))
    A(P("<b>Area</b> is the number of unit squares that fit inside a shape. Look at this rectangle "
        "covered in 1-cm squares:"))
    A(figure(area_grid(5, 3, "1 cm"), "A 5 × 3 rectangle holds 15 unit squares → area = 15 cm²."))
    A(P("Counting one by one works, but notice: 3 rows of 5 squares is just <b>5 × 3</b>. That's the "
        "shortcut for every rectangle."))
    A(example("rectangle area & perimeter", steps([
        "Rectangle: length 5 cm, width 3 cm.",
        "<b>Area</b> = length × width = 5 × 3 = <b>15 cm²</b> (square units!).",
        "<b>Perimeter</b> = 2 × (length + width) = 2 × (5 + 3) = <b>16 cm</b> (length units).",
        "Same shape, two very different measurements — never mix them up!",
    ])))
    A(P("A <b>square</b> is a rectangle whose sides are all equal, so its area is side × side:"))
    A(figure(rect_fig("6 cm", "6 cm", px=120, py=120, fill="#39A85B"), "A square of side 6 cm."))
    A(example("square area & perimeter (side 6 cm)", steps([
        "<b>Area</b> = side × side = 6 × 6 = <b>36 cm²</b>.",
        "<b>Perimeter</b> = 4 × side = 4 × 6 = <b>24 cm</b>.",
    ])))
    A(tryit("A rectangle is 9 m long and 4 m wide. Find its area and perimeter.",
            "Area = 9 × 4 = <b>36 m²</b>. Perimeter = 2 × (9 + 4) = 2 × 13 = <b>26 m</b>."))

    # ── TRIANGLE AREA ───────────────────────────────────────────────────
    A(H("Area of a triangle — half of a rectangle"))
    A(P("Here's a lovely surprise. Take any triangle, copy it, flip the copy, and the two together make "
        "a <b>parallelogram</b> (and a right triangle makes a perfect rectangle). So a triangle is "
        "exactly <b>half</b> of that box around it:"))
    A(figure(triangle_area_fig("8 cm", "5 cm"), "Triangle with base 8 cm and height 5 cm."))
    A(P("<b>Area of a triangle = ½ × base × height.</b> The <b>height</b> must be measured "
        "<em>straight</em> (perpendicular) from the base to the opposite tip — that's the dashed line."))
    A(example("triangle area (base 8, height 5)", steps([
        "Area = ½ × base × height = ½ × 8 × 5.",
        "½ × 8 = 4, then 4 × 5 = <b>20 cm²</b>.",
        "Sense-check: the surrounding 8 × 5 = 40 cm² rectangle is twice as big — and 20 is half of 40 ✓.",
    ])))
    A(kiwi("Watch out: the <b>height is not always a side</b>! For a slanted (obtuse) triangle, the "
           "perpendicular height might even fall outside the triangle. Always use the straight, "
           "perpendicular distance from the base to the far corner."))
    A(tryit("A triangular sail has base 6 m and height 9 m. Find its area.",
            "½ × 6 × 9 = ½ × 54 = <b>27 m²</b>."))

    # ── PARALLELOGRAM ───────────────────────────────────────────────────
    A(H("Area of a parallelogram — straighten it into a rectangle"))
    A(P("A <b>parallelogram</b> looks like a pushed-over rectangle. Slice a triangle off one slanted end "
        "and slide it to the other end — it becomes a plain rectangle of the same base and height. So:"))
    A(figure(parallelogram_fig("10 cm", "6 cm"), "Parallelogram: base 10 cm, perpendicular height 6 cm."))
    A(P("<b>Area of a parallelogram = base × height</b> (height measured perpendicular to the base, "
        "<em>not</em> the slanted side)."))
    A(example("parallelogram area (base 10, height 6)", steps([
        "Area = base × height = 10 × 6 = <b>60 cm²</b>.",
        "The slanted side length doesn't matter for area — only the straight-up height does.",
    ])))
    A(tryit("A parallelogram has base 12 cm and height 5 cm. Find its area.",
            "12 × 5 = <b>60 cm²</b>."))

    # ── COMPOSITE SHAPES ────────────────────────────────────────────────
    A(H("Composite shapes — cut into friendly pieces"))
    A(P("Real shapes (like an L-shaped room) aren't always one neat rectangle. The trick: <b>chop the "
        "shape into rectangles</b>, find each area, and add them up."))
    A(figure(composite_L(), "An L-shaped floor: split it into two rectangles along the dashed line."))
    A(example("area of the L-shape", steps([
        "Split into a tall left rectangle and a short right rectangle.",
        "Left rectangle: 5 cm wide × 7 cm tall = 35 cm². (Top arm width 5, full height 7.)",
        "Right rectangle: 8 cm wide × 4 cm tall = 32 cm². (Bottom foot.)",
        "Total area = 35 + 32 = <b>67 cm²</b>. Add the pieces — never count any square twice!",
    ])))
    A(kiwi("Two ways to handle composites: <b>add</b> the pieces (split into rectangles) <em>or</em> "
           "<b>subtract</b> — find the area of a big enclosing rectangle and take away the missing corner. "
           "Both give the same answer; pick whichever is easier for the picture."))
    A(tryit("A 10 cm × 6 cm rectangle has a 3 cm × 2 cm bite cut out of one corner. What area is left?",
            "Whole = 10 × 6 = 60 cm²; bite = 3 × 2 = 6 cm²; left = 60 − 6 = <b>54 cm²</b>."))

    # ── CIRCLE: PARTS ───────────────────────────────────────────────────
    A(H("Meet the circle — radius, diameter, circumference"))
    A(P("A <b>circle</b> is the set of all points the same distance from a centre. Three words you need:"))
    A(P("• <b>Radius</b> (r): centre to edge.<br>"
        "• <b>Diameter</b> (d): all the way across through the centre — exactly <b>twice</b> the radius, "
        "so <b>d = 2r</b>.<br>"
        "• <b>Circumference</b> (C): the distance <em>around</em> the circle (its 'perimeter')."))
    A(figure(circle_parts(), "A circle: radius (red) from centre to edge, diameter (blue) all the way across."))
    A(tryit("A circle has radius 7 cm. What is its diameter?",
            "d = 2r = 2 × 7 = <b>14 cm</b>."))

    # ── PI SURPRISE ─────────────────────────────────────────────────────
    A(H("The surprise of all surprises: π"))
    A(P("Here's an experiment people have done for thousands of years. Take <em>any</em> circle — a coin, "
        "a plate, a wheel — and measure two things: the distance <b>around</b> it (C) and the distance "
        "<b>across</b> it (d). Now divide C by d. You always get the <b>same number</b>, a little more "
        "than 3:"))
    A(figure(circ_unroll(), "Roll any circle one full turn: the track it leaves is about 3.14 diameters long."))
    A(P("That never-changing ratio C ÷ d is the famous number <b>π</b> (\"pi\"). "
        "π ≈ <b>3.14</b> ≈ <b>22/7</b>. It goes on forever without repeating "
        "(3.14159265…), but for school we use 3.14 or 22/7."))
    A(kiwi("Read that again — it's astonishing. It doesn't matter if the circle is a tiny button or as "
           "big as a planet: go around it and across it, divide, and you <em>always</em> get π. The "
           "circle carries this secret number baked right into its shape. From C ÷ d = π we get the "
           "circumference formula:"))
    A(P("<b>Circumference C = π × d = 2 × π × r.</b>"))
    A(example("circumference of a wheel (radius 7 cm)", steps([
        "Use π ≈ 22/7 because the radius is 7 (the 7s cancel beautifully).",
        "C = 2 × π × r = 2 × (22/7) × 7.",
        "The 7 in the bottom cancels the 7 on top: 2 × 22 = <b>44 cm</b>.",
    ])))
    A(tryit("A circular pond has diameter 10 m. Find its circumference (use π ≈ 3.14).",
            "C = π × d = 3.14 × 10 = <b>31.4 m</b>."))

    # ── CIRCLE AREA ─────────────────────────────────────────────────────
    A(H("Area of a circle = π r²"))
    A(P("There's a clever way to see this. Slice a circle into many thin wedges and re-arrange them, "
        "tips pointing up and down alternately. They form an almost-rectangle: its long side is half the "
        "circumference (π r) and its short side is the radius (r). So the area is π r × r = "
        "<b>π r²</b>."))
    A(P("<b>Area of a circle = π × r × r = π r².</b> (Remember: use the <em>radius</em>, and square it.)"))
    A(example("area of a circle (radius 7 cm)", steps([
        "Area = π × r² = (22/7) × 7 × 7.",
        "(22/7) × 7 = 22, then 22 × 7 = <b>154 cm²</b>.",
        "Careful: r² means r × r = 49, not 14. Square the radius, then multiply by π.",
    ])))
    A(kiwi("Don't confuse the two circle formulas! <b>Circumference uses r once</b> (C = 2πr) and is a "
           "length (cm). <b>Area uses r twice</b> (A = πr²) and is a surface (cm²). The little 'squared' "
           "tells you it's area."))
    A(tryit("Find the area of a circle with radius 10 cm (use π ≈ 3.14).",
            "A = π r² = 3.14 × 10 × 10 = 3.14 × 100 = <b>314 cm²</b>."))

    # ── BLOOM LADDER ────────────────────────────────────────────────────
    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What units do we use for area?", "Square units, like cm² or m²."),
        ("Area of a rectangle = ?", "length × width."),
        ("Area of a triangle = ?", "½ × base × height."),
        ("What is the diameter of a circle in terms of its radius?", "d = 2 × r."),
        ("What is π approximately equal to?", "About 3.14, or 22/7."),
    ]))
    A(practice("Understand", [
        ("A square has side 5 cm. Find its area and perimeter.",
         "Area = 5 × 5 = 25 cm²; perimeter = 4 × 5 = 20 cm."),
        ("Why is a triangle's area half of base × height?",
         "Two copies of the triangle fit together to make a parallelogram of base × height, so one "
         "triangle is half of that."),
        ("A parallelogram has base 8 cm and height 4 cm. Find its area.", "8 × 4 = 32 cm²."),
        ("Circumference uses r once or twice? Area uses r once or twice?",
         "Circumference once (2πr); area twice (πr²)."),
        ("A circle has radius 3 cm. Find its diameter.", "2 × 3 = 6 cm."),
    ]))
    A(practice("Apply", [
        ("Find the area of a triangle with base 12 cm and height 7 cm.", "½ × 12 × 7 = ½ × 84 = 42 cm²."),
        ("Find the perimeter of a rectangle 15 m by 8 m.", "2 × (15 + 8) = 2 × 23 = 46 m."),
        ("Find the circumference of a circle with radius 14 cm (π ≈ 22/7).", "2 × (22/7) × 14 = 2 × 44 = 88 cm."),
        ("Find the area of a circle with radius 7 m (π ≈ 22/7).", "(22/7) × 7 × 7 = 22 × 7 = 154 m²."),
        ("An L-shape splits into a 6×3 rectangle and a 2×4 rectangle. Find its total area.",
         "(6 × 3) + (2 × 4) = 18 + 8 = 26 square units."),
        ("Find the area of a parallelogram with base 9 cm and height 6 cm.", "9 × 6 = 54 cm²."),
    ]))
    A(practice("Analyze", [
        ("A square and a rectangle both have perimeter 24 cm. The rectangle is 8 cm by 4 cm. Which has "
         "the bigger area?",
         "Square side = 24 ÷ 4 = 6 cm, area = 36 cm². Rectangle area = 8 × 4 = 32 cm². "
         "The square wins (36 > 32) — for a fixed perimeter, the more 'square' shape holds more area."),
        ("A circle's circumference is 44 cm. Find its radius (π ≈ 22/7).",
         "C = 2πr → 44 = 2 × (22/7) × r → 44 = (44/7) r → r = 7 cm."),
        ("A triangle has area 30 cm² and base 10 cm. Find its height.",
         "30 = ½ × 10 × h → 30 = 5h → h = 6 cm."),
        ("A rectangle has area 48 cm² and length 8 cm. Find its perimeter.",
         "Width = 48 ÷ 8 = 6 cm; perimeter = 2 × (8 + 6) = 28 cm."),
    ]))
    A(practice("Create", [
        ("Design a rectangle and a triangle that have the SAME area. Give their dimensions.",
         "E.g. rectangle 6 × 4 = 24 cm² and triangle base 8, height 6 → ½ × 8 × 6 = 24 cm². Many answers."),
        ("Invent a composite shape made of two rectangles whose total area is 100 cm². Describe it.",
         "E.g. a 10×8 rectangle (80) joined to a 10×2 rectangle (20) → 80 + 20 = 100 cm²."),
        ("Answer the opening puzzle: with 20 m of fence, sketch the shape that gives the most area, and "
         "say roughly how much.",
         "A circle wins. 20 m around → diameter ≈ 20 ÷ 3.14 ≈ 6.37 m, radius ≈ 3.18 m, area ≈ 3.14 × "
         "3.18² ≈ 31.8 m² — far more than a 5 m × 5 m square (25 m²). Round shapes are the champions of "
         "area! ⭕"),
    ]))

    # ── CHALLENGE ───────────────────────────────────────────────────────
    A(challenge(
        P("A goat is tied by a <b>7 m</b> rope to a corner peg in the middle of a huge open field. "
          "It can graze every spot the rope reaches. <b>What area of grass can the goat eat?</b> "
          "(Use π ≈ 22/7.) Then a twist: if the rope is tied to the outside <em>corner</em> of a square "
          "shed wall, the goat can only sweep a <b>quarter</b> of the full circle — now what area?") +
        tryit("Work out both the full circle and the quarter.",
              "Full circle: the rope is the radius r = 7 m, so area = π r² = (22/7) × 7 × 7 = "
              "<b>154 m²</b>. Tied to an outside corner (a right-angle wall blocks three-quarters), the "
              "goat sweeps a quarter-circle: 154 ÷ 4 = <b>38.5 m²</b>. Same rope, very different lunch — "
              "geometry decides! 🐐")))

    A(kiwi("Superb work. You can now measure both the fence (perimeter) and the field (area) of "
           "rectangles, triangles, parallelograms, composites — and circles, powered by the unforgettable "
           "π. Next we leave the flat page and build <b>3D solids</b>, where another surprise number is "
           "waiting: Euler's. 🧊"))

    chapter("Part 5 · Shapes, Space & Maps", 15, "Perimeter, Area & Circles",
            "Geometry · Space & Surface", "".join(b))
