#!/usr/bin/env python3
"""L3 Chapter 14 — Triangles & Polygons (Geometry · Angle Chasers). Discover the
triangle angle sum = 180°, the exterior-angle rule, quadrilateral sum = 360°,
the (n-2)×180° interior-angle formula, and regular polygons."""
import math
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg)
from l3_figs import polygon, INK, ORANGE, SKY, GRASS, BERRY, PURPLE, GOLD


# ── local inline figures ────────────────────────────────────────────────
def triangle_angles(a, b, c, col=GRASS):
    """A triangle with the three interior angles labelled at the vertices."""
    pts = [(150, 28), (40, 168), (260, 168)]  # apex, bottom-left, bottom-right
    poly = " ".join(f"{x},{y}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{col}1f" stroke="{col}" stroke-width="2.4"/>',
         f'<text x="150" y="52" text-anchor="middle" font-size="15" font-weight="800" fill="{BERRY}">{a}&#176;</text>',
         f'<text x="60" y="158" text-anchor="middle" font-size="15" font-weight="800" fill="{SKY}">{b}&#176;</text>',
         f'<text x="238" y="158" text-anchor="middle" font-size="15" font-weight="800" fill="{ORANGE}">{c}&#176;</text>']
    return svg("".join(s), 300, 196)


def torn_triangle():
    """Three torn corners of a triangle laid along a straight line to show 180°."""
    s = [f'<line x1="20" y1="110" x2="300" y2="110" stroke="{INK}" stroke-width="2.4"/>',
         # corner 1 (berry)
         f'<polygon points="60,110 110,110 86,70" fill="{BERRY}33" stroke="{BERRY}" stroke-width="1.8"/>',
         # corner 2 (sky) - sits next, sharing apex area
         f'<polygon points="110,110 175,110 110,70" fill="{SKY}33" stroke="{SKY}" stroke-width="1.8"/>',
         # corner 3 (orange)
         f'<polygon points="175,110 235,110 175,72" fill="{ORANGE}33" stroke="{ORANGE}" stroke-width="1.8"/>',
         f'<text x="150" y="135" text-anchor="middle" font-size="13" fill="{INK}">three corners fill a straight line = 180°</text>']
    return svg("".join(s), 320, 150)


def exterior_angle_fig(a, b):
    """Triangle with one side extended, showing exterior angle = a + b."""
    pts = [(120, 30), (60, 160), (230, 160)]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2.4"/>',
         # extend the bottom side to the right
         f'<line x1="230" y1="160" x2="330" y2="160" stroke="{INK}" stroke-width="2.2" stroke-dasharray="2 0"/>',
         f'<text x="120" y="54" text-anchor="middle" font-size="14" font-weight="800" fill="{BERRY}">{a}&#176;</text>',
         f'<text x="78" y="152" text-anchor="middle" font-size="14" font-weight="800" fill="{SKY}">{b}&#176;</text>',
         # interior angle at C
         f'<text x="212" y="151" text-anchor="middle" font-size="13" font-weight="800" fill="{GRASS}">{180-a-b}&#176;</text>',
         # exterior angle (orange) outside C
         f'<text x="258" y="151" text-anchor="middle" font-size="14" font-weight="800" fill="{ORANGE}">{a+b}&#176;</text>']
    return svg("".join(s), 350, 184)


def quad_diagonal():
    """A quadrilateral split by one diagonal into 2 triangles."""
    pts = [(40, 40), (250, 30), (270, 160), (60, 175)]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{PURPLE}1f" stroke="{PURPLE}" stroke-width="2.4"/>',
         f'<line x1="40" y1="40" x2="270" y2="160" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>',
         f'<text x="150" y="95" text-anchor="middle" font-size="13" fill="{ORANGE}">one diagonal = 2 triangles</text>']
    return svg("".join(s), 320, 200)


def reg_polygon(n, label=""):
    """A regular n-gon."""
    cx, cy, r = 150, 110, 90
    pts = []
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{SKY}1f" stroke="{SKY}" stroke-width="2.4"/>']
    if label:
        s.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="15" font-weight="800" fill="{INK}">{label}</text>')
    return svg("".join(s), 300, 220)


def build(chapter):
    b = []; A = b.append

    # ── HOOK ────────────────────────────────────────────────────────────
    A(big_q("Draw <em>any</em> triangle you like — long and skinny, fat and squat, tilted any way. "
            "Measure its three corner angles and add them up. Try a totally different triangle and add "
            "again. Something almost magical happens: you keep getting the <b>same number</b>. What is it, "
            "and why can it never change?"))
    A(kiwi("Welcome back, it's <b>Kiwi</b>! 🔺 In the last chapter you learned to chase angles on lines. "
           "Now we close those lines into <b>shapes</b> — starting with the triangle, the simplest and "
           "strongest shape of all. We'll <em>discover</em> a rule that every triangle in the universe "
           "obeys, then ride it all the way up to many-sided polygons."))

    # ── TYPES OF TRIANGLES ──────────────────────────────────────────────
    A(H("Naming triangles — by sides and by angles"))
    A(P("A <b>triangle</b> is a closed shape with three straight sides and three corners (vertices). "
        "We can name a triangle two ways:"))
    A(P("<b>By its sides:</b><br>"
        "• <b>Equilateral</b> — all three sides equal.<br>"
        "• <b>Isosceles</b> — exactly two sides equal.<br>"
        "• <b>Scalene</b> — all three sides different."))
    A(P("<b>By its angles:</b><br>"
        "• <b>Acute</b> triangle — all three angles less than 90°.<br>"
        "• <b>Right</b> triangle — one angle exactly 90°.<br>"
        "• <b>Obtuse</b> triangle — one angle more than 90°."))
    A(figure(polygon([(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)], labels=["", "", ""], fill=GRASS),
             "An equilateral-looking triangle: three sides, three corners."))
    A(kiwi("A neat fact to remember: in an <b>equilateral</b> triangle, all three angles are equal too — "
           "and since they must add to 180° (you'll prove that next!), each one is exactly "
           "180 ÷ 3 = <b>60°</b>. In an <b>isosceles</b> triangle, the two angles opposite the equal sides "
           "are also equal — a super-useful shortcut."))
    A(tryit("A triangle has sides 6 cm, 6 cm, 9 cm. What type is it (by sides)?",
            "Two sides are equal, the third is different → <b>isosceles</b>."))

    # ── DISCOVER THE 180 ────────────────────────────────────────────────
    A(H("The big discovery: a triangle's angles add to 180°"))
    A(P("Here's a hands-on way to <em>see</em> it. Tear the three corners off a paper triangle and lay "
        "them side by side, point to point. They snap together to make a perfectly <b>straight line</b> — "
        "and a straight line is <b>180°</b>!"))
    A(figure(torn_triangle(), "The three corners of any triangle fit together along a straight line — so they total 180°."))
    A(P("That's not a coincidence for one lucky triangle — it's true for <em>every</em> triangle. "
        "Mathematicians call it the <b>Angle Sum Property</b>:"))
    A(kiwi("<b>In every triangle, the three interior angles add up to exactly 180°.</b> This one fact is "
           "the master key to all triangle problems. Know two angles → you instantly know the third."))
    A(figure(triangle_angles(80, 60, 40), "80° + 60° + 40° = 180° ✓ — like every triangle, it adds to 180°."))
    A(example("find the missing angle of a triangle", steps([
        "Two angles of a triangle are <b>80°</b> and <b>60°</b>.",
        "All three add to 180°, so the third = 180 − 80 − 60.",
        "Third angle = 180 − 140 = <b>40°</b>. Check: 80 + 60 + 40 = 180 ✓.",
    ])))
    A(tryit("A right triangle has one angle of 35° (besides its 90° corner). Find the third angle.",
            "180 − 90 − 35 = <b>55°</b>."))
    A(tryit("Each angle of an equilateral triangle is the same. What is each one?",
            "180 ÷ 3 = <b>60°</b>."))

    # ── EXTERIOR ANGLE ──────────────────────────────────────────────────
    A(H("A bonus rule: the exterior angle"))
    A(P("Extend one side of a triangle past a corner. The angle that opens up <em>outside</em> the "
        "triangle is the <b>exterior angle</b>. Surprise: it equals the <b>sum of the two far interior "
        "angles</b> (the two it does <em>not</em> touch)."))
    A(figure(exterior_angle_fig(70, 60), "Exterior angle (orange) = 70° + 60° = 130°, the two far interior angles."))
    A(P("Why? The exterior angle and the interior angle next to it sit on a straight line, so they add "
        "to 180°. And the three interior angles also add to 180°. Subtract the shared interior angle "
        "from both and — out pops the rule: <b>exterior angle = sum of the other two interior angles</b>."))
    A(example("use the exterior-angle rule", steps([
        "Two far interior angles are <b>70°</b> and <b>60°</b>.",
        "Exterior angle = 70 + 60 = <b>130°</b>.",
        "Double-check: the interior angle at that corner = 180 − 130 = 50°, and 70 + 60 + 50 = 180 ✓.",
    ])))
    A(tryit("A triangle's two remote interior angles are 45° and 65°. What is the exterior angle at the "
            "third vertex?",
            "45 + 65 = <b>110°</b>."))

    # ── QUADRILATERAL SUM ───────────────────────────────────────────────
    A(H("From triangles to quadrilaterals: the angles add to 360°"))
    A(P("A <b>quadrilateral</b> is a four-sided shape (square, rectangle, kite, any four-corner shape). "
        "Here's a slick trick: draw one <b>diagonal</b> and it splits the quadrilateral into <b>two "
        "triangles</b>."))
    A(figure(quad_diagonal(), "One diagonal cuts any quadrilateral into 2 triangles."))
    A(example("why a quadrilateral's angles total 360°", steps([
        "The diagonal makes <b>2 triangles</b>.",
        "Each triangle's angles add to 180°.",
        "Together: 2 × 180 = <b>360°</b>. So every quadrilateral's four angles add to 360°!",
    ])))
    A(tryit("Three angles of a quadrilateral are 100°, 80° and 95°. Find the fourth.",
            "360 − 100 − 80 − 95 = <b>85°</b>."))

    # ── (n-2) FORMULA ───────────────────────────────────────────────────
    A(H("The grand pattern: any polygon's angle sum"))
    A(P("That diagonal trick keeps working! From <em>one</em> corner of any polygon, draw diagonals to "
        "every other corner. A shape with <b>n</b> sides always splits into <b>(n − 2)</b> triangles. "
        "Multiply by 180° and you have the total of all its interior angles:"))
    A(figure(reg_polygon(5, "5 sides"), "A pentagon (5 sides) splits into 5 − 2 = 3 triangles → 3 × 180 = 540°."))
    A(P("<b>Interior-angle sum of an n-sided polygon = (n − 2) × 180°.</b>"))
    A(_polygon_table())
    A(example("angle sum of an octagon (8 sides)", steps([
        "n = 8, so it splits into 8 − 2 = <b>6</b> triangles.",
        "Total of interior angles = 6 × 180 = <b>1080°</b>.",
    ])))
    A(tryit("What is the interior-angle sum of a hexagon (6 sides)?",
            "(6 − 2) × 180 = 4 × 180 = <b>720°</b>."))

    # ── REGULAR POLYGONS ────────────────────────────────────────────────
    A(H("Regular polygons — every angle the same"))
    A(P("A <b>regular</b> polygon has all sides equal <em>and</em> all angles equal (like a stop sign, "
        "which is a regular octagon). Since every angle is the same, just share the total fairly:"))
    A(P("<b>Each interior angle of a regular n-gon = (n − 2) × 180° ÷ n.</b>"))
    A(figure(reg_polygon(6, "regular"), "A regular hexagon — six equal sides, six equal 120° angles."))
    A(example("each angle of a regular hexagon", steps([
        "Total interior angles = (6 − 2) × 180 = 720°.",
        "Share equally among 6 corners: 720 ÷ 6 = <b>120°</b> each.",
        "That's why honeycomb cells (regular hexagons) tile so perfectly — three 120° angles meet at a "
        "point and 3 × 120 = 360° fills the gap exactly. 🐝",
    ])))
    A(kiwi("There's a second, often-faster route: the <b>exterior</b> angles of <em>any</em> polygon "
           "always add to <b>360°</b> (imagine walking once around the shape — you turn a full circle in "
           "total). For a regular n-gon, each exterior angle = 360 ÷ n, and each interior angle = "
           "180 − that. For a hexagon: 360 ÷ 6 = 60° exterior → 180 − 60 = 120° interior. Same answer! ✓"))
    A(tryit("Find each interior angle of a regular pentagon (5 sides).",
            "Total = (5 − 2) × 180 = 540°; each angle = 540 ÷ 5 = <b>108°</b>. "
            "(Or 360 ÷ 5 = 72° exterior → 180 − 72 = 108°.)"))

    # ── BLOOM LADDER ────────────────────────────────────────────────────
    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What do the three angles of a triangle add up to?", "180°."),
        ("What do the four angles of a quadrilateral add up to?", "360°."),
        ("A triangle with all sides equal is called…?", "Equilateral."),
        ("A polygon with all sides and all angles equal is called…?", "Regular."),
        ("The exterior angles of any polygon add up to…?", "360°."),
    ]))
    A(practice("Understand", [
        ("Two angles of a triangle are 50° and 60°. What is the third?", "180 − 50 − 60 = 70°."),
        ("Can a triangle have two right angles? Why or why not?",
         "No — two right angles already total 180°, leaving 0° for the third angle, which is impossible."),
        ("How many triangles does a hexagon split into from one corner?", "6 − 2 = 4 triangles."),
        ("Each angle of an equilateral triangle is what?", "60°."),
        ("Why does a quadrilateral's angle sum equal 360°?",
         "A diagonal splits it into two triangles, and 2 × 180 = 360°."),
    ]))
    A(practice("Apply", [
        ("A triangle has angles 90°, x, x. Find x.", "90 + 2x = 180 → 2x = 90 → x = 45°."),
        ("Three angles of a quadrilateral are 70°, 110° and 95°. Find the fourth.", "360 − 70 − 110 − 95 = 85°."),
        ("Find the interior-angle sum of a polygon with 10 sides.", "(10 − 2) × 180 = 8 × 180 = 1440°."),
        ("Find each interior angle of a regular octagon.", "Total = 1080°; 1080 ÷ 8 = 135°."),
        ("A triangle's exterior angle is 120° and one remote interior angle is 50°. Find the other remote "
         "interior angle.", "Exterior = sum of remotes, so 120 = 50 + ? → ? = 70°."),
        ("An isosceles triangle has a 40° angle at its apex. Find the two equal base angles.",
         "180 − 40 = 140° shared by two equal angles → each is 70°."),
    ]))
    A(practice("Analyze", [
        ("The angles of a triangle are in the ratio 1 : 2 : 3. Find them.",
         "The 6 parts make 180°, so one part = 30°. Angles: 30°, 60°, 90° (a right triangle!)."),
        ("Each interior angle of a regular polygon is 140°. How many sides does it have?",
         "Each exterior angle = 180 − 140 = 40°; sides = 360 ÷ 40 = 9."),
        ("A quadrilateral's angles are x, x, x and 120°. Find x.",
         "3x + 120 = 360 → 3x = 240 → x = 80°."),
        ("Can a regular polygon have an interior angle of exactly 100°? Explain.",
         "Exterior would be 180 − 100 = 80°, and 360 ÷ 80 = 4.5 — not a whole number of sides, so no."),
    ]))
    A(practice("Create", [
        ("Invent a triangle whose three angles are all different and add to 180°. What are they?",
         "Any scalene set, e.g. 50°, 60°, 70° (sum 180°)."),
        ("Design a regular polygon whose each interior angle is 150°, and say how many sides it has.",
         "Exterior = 180 − 150 = 30°; sides = 360 ÷ 30 = 12 (a regular dodecagon)."),
        ("Make up a quadrilateral-angle puzzle whose missing angle is 90°, and write the solution.",
         "E.g. angles 120°, 80°, 70° and x → x = 360 − 270 = 90°."),
    ]))

    # ── CHALLENGE ───────────────────────────────────────────────────────
    A(challenge(
        P("A famous shape: the <b>five-pointed star</b> ⭐ you draw without lifting your pen. "
          "Surprisingly, the five sharp tip-angles always add to the same total. Here's the chase: each "
          "tip is the apex of a little triangle, and each tip angle equals the difference of two arcs… "
          "but you don't need circles. Use the exterior-angle rule: walking around the star you make "
          "<b>two</b> full turns (720°) of turning, and the turning at each tip is 180° − (tip angle). "
          "Set up: 5 × (180 − tip) = 720. Find the sum of the five tip angles.") +
        tryit("Solve for the total of the five tips.",
              "5 × (180 − tip) = 720 → 900 − 5·tip = 720 → 5·tip = 180 → the five tip angles add to "
              "<b>180°</b>! (For a regular star each tip is 180 ÷ 5 = 36°.) A perfect five-pointed star "
              "hides a triangle's angle sum inside it. ⭐")))

    A(kiwi("Magnificent! You discovered the 180° triangle rule, met the exterior-angle shortcut, and "
           "climbed to the (n − 2) × 180° formula that governs <em>every</em> polygon. Next we measure "
           "the space <em>inside</em> these shapes — perimeter and area — and meet the most famous number "
           "in geometry: <b>π</b>. 🟠"))

    chapter("Part 5 · Shapes, Space & Maps", 14, "Triangles & Polygons",
            "Geometry · Angle Chasers", "".join(b))


# ── table of polygon angle sums ─────────────────────────────────────────
def _polygon_table():
    rows = [("Triangle", 3), ("Quadrilateral", 4), ("Pentagon", 5),
            ("Hexagon", 6), ("Octagon", 8), ("Decagon", 10)]
    head = "<tr><th>Polygon</th><th>Sides (n)</th><th>Triangles (n−2)</th><th>Angle sum</th></tr>"
    body = ""
    for name, n in rows:
        body += f"<tr><td>{name}</td><td>{n}</td><td>{n-2}</td><td>{(n-2)*180}&#176;</td></tr>"
    return f'<table class="pv">{head}{body}</table>'
