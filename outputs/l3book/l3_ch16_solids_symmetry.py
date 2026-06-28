#!/usr/bin/env python3
"""L3 Chapter 16 — Solids, Nets & Symmetry (Geometry · Space & Surface).
3D solids and their faces/edges/vertices, Euler's surprise (F+V−E=2), nets and
which nets fold to a cube, dice (opposite faces sum to 7), line & rotational
symmetry, and mirror images."""
import math
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, solid, cube_net, symmetry_fig)
from l3_figs import INK, ORANGE, SKY, GRASS, BERRY, PURPLE, GOLD


# ── local inline figures ────────────────────────────────────────────────
def labelled_cube():
    """A cube labelling a face, an edge, and a vertex."""
    ox = 56
    wdt, dp = 120, 34
    s = [f'<rect x="{ox}" y="55" width="{wdt}" height="100" fill="{SKY}22" stroke="{SKY}" stroke-width="2"/>',
         f'<polygon points="{ox},55 {ox+dp},25 {ox+wdt+dp},25 {ox+wdt},55" fill="{SKY}33" stroke="{SKY}" stroke-width="2"/>',
         f'<polygon points="{ox+wdt},55 {ox+wdt+dp},25 {ox+wdt+dp},125 {ox+wdt},155" fill="{SKY}18" stroke="{SKY}" stroke-width="2"/>',
         # callouts
         f'<text x="{ox+wdt/2:.0f}" y="110" text-anchor="middle" font-size="13" font-weight="800" fill="{BERRY}">face</text>',
         f'<circle cx="{ox}" cy="155" r="4.5" fill="{ORANGE}"/>',
         f'<text x="{ox+8}" y="178" text-anchor="middle" font-size="12" font-weight="800" fill="{ORANGE}">vertex</text>',
         f'<text x="{ox+wdt+dp+6}" y="95" text-anchor="start" font-size="12" font-weight="800" fill="{GRASS}">← edge</text>']
    return svg("".join(s), 300, 190)


def die_face(n, x0=0, y0=0, size=70, col=BERRY):
    """Draw a single die face with n pips. Returns list of svg strings."""
    s = [f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="10" fill="#fff" stroke="{col}" stroke-width="2"/>']
    # pip positions in a 3x3 grid
    g = size / 4
    pos = {
        1: [(2, 2)],
        2: [(1, 1), (3, 3)],
        3: [(1, 1), (2, 2), (3, 3)],
        4: [(1, 1), (1, 3), (3, 1), (3, 3)],
        5: [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)],
        6: [(1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3)],
    }
    for (c, r) in pos[n]:
        s.append(f'<circle cx="{x0+c*g:.0f}" cy="{y0+r*g:.0f}" r="{size*0.07:.0f}" fill="{INK}"/>')
    return s


def dice_pairs():
    """Show the three opposite-face pairs of a die: 1-6, 2-5, 3-4."""
    s = []
    pairs = [(1, 6), (2, 5), (3, 4)]
    x = 10
    for a, c in pairs:
        s += die_face(a, x, 20, 60, BERRY)
        s.append(f'<text x="{x+72}" y="56" font-size="20" font-weight="800" fill="{ORANGE}">+</text>')
        s += die_face(c, x + 92, 20, 60, SKY)
        s.append(f'<text x="{x+76}" y="104" text-anchor="middle" font-size="12" fill="{INK}">= 7</text>')
        x += 180
    return svg("".join(s), 550, 120)


def good_bad_net(good=True):
    """A cube net layout; good=True is a valid cross net, good=False is an invalid one."""
    c = 36
    if good:
        cells = [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (1, 3)]  # plus/cross
        col = GRASS
    else:
        cells = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (3, 1)]  # cannot fold
        col = BERRY
    s = []
    for (cx, cy) in cells:
        s.append(f'<rect x="{16+cx*c}" y="{12+cy*c}" width="{c}" height="{c}" fill="{col}22" stroke="{col}" stroke-width="1.8"/>')
    return svg("".join(s), 16 + 4 * c + 16, 12 + 4 * c + 12)


def rotation_fig(order):
    """A regular polygon hint showing rotational symmetry order."""
    cx, cy, r = 110, 100, 70
    pts = []
    n = order
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{PURPLE}1f" stroke="{PURPLE}" stroke-width="2.4"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{ORANGE}"/>',
         f'<text x="{cx}" y="{cy+r+24:.0f}" text-anchor="middle" font-size="13" font-weight="800" fill="{INK}">order {order}</text>',
         # curved arrow
         f'<path d="M{cx+34},{cy-34} A48,48 0 0 1 {cx+48},{cy+8}" fill="none" stroke="{ORANGE}" stroke-width="2"/>',
         f'<polygon points="{cx+48},{cy+8} {cx+40},{cy} {cx+54},{cy-2}" fill="{ORANGE}"/>']
    return svg("".join(s), 220, 200)


def build(chapter):
    b = []; A = b.append

    # ── HOOK ────────────────────────────────────────────────────────────
    A(big_q("Pick up a dice, a cardboard box, a can, a party hat. Count their flat <b>faces</b>, their "
            "<b>edges</b> (where two faces meet) and their <b>corners</b> (vertices). Now do a strange sum: "
            "faces + corners − edges. For the box you get… and for the dice… <em>the same number every "
            "time</em>. What is it, and how did a Swiss mathematician spot it 250 years ago?"))
    A(kiwi("Hi explorer, it's <b>Kiwi</b>! 🧊 We step off the flat page into <b>3D</b> — solids you can "
           "hold. We'll count their faces, edges and vertices, uncover Euler's jaw-dropping pattern, "
           "unfold solids into flat <b>nets</b>, crack the secret of dice, and finish by spinning and "
           "mirroring shapes. Hands-on geometry — grab a box if you have one!"))

    # ── SOLIDS: F/V/E ───────────────────────────────────────────────────
    A(H("Solids and their faces, edges & vertices"))
    A(P("A <b>solid</b> (or 3D shape) takes up space. Three things to count on a solid with flat faces:"))
    A(P("• <b>Face</b> — a flat surface.<br>"
        "• <b>Edge</b> — a line where two faces meet.<br>"
        "• <b>Vertex</b> — a corner point where edges meet (plural: vertices)."))
    A(figure(labelled_cube(), "A cube: a face (flat side), an edge (where two faces meet), a vertex (corner)."))
    A(figure(solid("cuboid"), "A cuboid (box): 6 faces, 12 edges, 8 vertices."))
    A(P("Let's meet the family of common solids — count carefully:"))
    A(_solids_table())
    A(figure(solid("cylinder"), "A cylinder: 2 flat circular faces + 1 curved surface (3 faces in this book's convention), 2 curved edges, 0 vertices."))
    A(figure(solid("cone"), "A cone: 1 flat circular face + 1 curved surface (2 faces in this book's convention), 1 curved edge, 1 vertex (the tip)."))
    A(figure(solid("sphere"), "A sphere (ball): 1 curved surface (counted as 1 face here), no edges, no vertices."))
    A(kiwi("Be careful with curved solids! A <b>sphere</b> has a surface but no flat faces, no edges and "
           "no corners. A <b>cone</b> has 1 flat face, 1 curved surface, and 1 pointy vertex. Euler's "
           "rule (next!) is about solids with <em>flat</em> faces, so try it on cubes, cuboids, prisms "
           "and pyramids."))
    A(kiwi("&#128221; <b>A note on counting curved surfaces.</b> In this book a <em>curved surface</em> "
           "counts as a face &mdash; so we say a cylinder has 3 faces (2 flat + 1 curved) and a cone "
           "has 2 (1 flat + 1 curved). Your school may instead name the curved part a &lsquo;curved "
           "surface&rsquo; separately and <em>not</em> call it a face, so its face counts can differ "
           "from ours. Either way is fine &mdash; just be clear which convention a question is using. "
           "(Euler's F + V &minus; E = 2 is only promised for <b>flat-faced</b> solids anyway, so the "
           "curved ones never enter that formula.)"))
    A(tryit("How many faces, edges and vertices does a cube have?",
            "<b>6 faces, 12 edges, 8 vertices.</b>"))

    # ── EULER ───────────────────────────────────────────────────────────
    A(H("Euler's surprise: F + V − E = 2"))
    A(P("Now the magic from our Big Question. For <em>any</em> solid with flat faces, try "
        "<b>Faces + Vertices − Edges</b>:"))
    A(_euler_table())
    A(P("Every single line gives <b>2</b>! This is <b>Euler's formula</b>: <b>F + V − E = 2</b>. The "
        "great mathematician Leonhard Euler discovered it in the 1700s, and it holds for cubes, "
        "pyramids, prisms — any solid you can puff up into a ball-shape without holes."))
    A(example("check Euler's formula on a square pyramid", steps([
        "A square pyramid has <b>5 faces</b> (1 square base + 4 triangles), <b>8 edges</b>, <b>5 vertices</b>.",
        "F + V − E = 5 + 5 − 8 = <b>2</b> ✓.",
        "It works! And you can use it backwards: if you know two of the three counts, you can find the "
        "third.",
    ])))
    A(kiwi("Euler's formula is a true 'wow' of mathematics — a hidden rule connecting three counts that "
           "seem unrelated, true for shapes nobody had even drawn yet. Whenever your face/edge/vertex "
           "counts <em>don't</em> give 2, you've miscounted somewhere — it's a built-in checker!"))
    A(tryit("A triangular prism has 5 faces and 9 edges. Use Euler's formula to find its number of "
            "vertices.",
            "F + V − E = 2 → 5 + V − 9 = 2 → V − 4 = 2 → V = <b>6</b>. (A triangular prism does have 6 "
            "corners ✓.)"))

    # ── NETS ────────────────────────────────────────────────────────────
    A(H("Nets — solids unfolded flat"))
    A(P("A <b>net</b> is what you get when you carefully unfold a solid and lay it flat — like flattening "
        "a cardboard box. Fold it back up and you rebuild the solid. A cube unfolds into <b>six</b> "
        "squares, but not every arrangement of six squares folds into a cube!"))
    A(figure(cube_net(), "A valid cube net: six squares in a cross. Fold along the lines and it makes a cube."))
    A(figure(good_bad_net(False), "NOT a cube net: six squares in a row plus two extras overlap when folded."))
    A(kiwi("There are exactly <b>11</b> different nets that fold into a cube — a fun thing to hunt for! "
           "Quick test: when you mentally fold it, every square must become a separate side with "
           "<em>no overlaps</em> and <em>no gaps</em>. If two squares would land on the same face, it's "
           "not a valid net."))
    A(tryit("A cube has 6 faces. How many squares must its net contain?",
            "Exactly <b>6</b> — one for each face."))

    # ── DICE ────────────────────────────────────────────────────────────
    A(H("The secret of dice: opposite faces add to 7"))
    A(P("A standard dice (die) is a cube with 1 to 6 pips. Its hidden rule: every pair of <b>opposite "
        "faces adds up to 7</b>. So 1 is opposite 6, 2 is opposite 5, and 3 is opposite 4."))
    A(figure(dice_pairs(), "The three opposite pairs of a standard die: 1+6, 2+5, 3+4 — each totals 7."))
    A(example("if the top shows 2, what's on the bottom?", steps([
        "Opposite faces add to 7.",
        "Bottom = 7 − top = 7 − 2 = <b>5</b>.",
        "Bonus: the three faces you can see plus their three hidden opposites always total 3 × 7 = 21 — "
        "that's every number from 1 to 6 added up!",
    ])))
    A(tryit("A die rests with 4 on top. What number is face-down on the table?",
            "7 − 4 = <b>3</b>."))

    # ── SYMMETRY: LINE ──────────────────────────────────────────────────
    A(H("Line symmetry — the fold-in-half test"))
    A(P("A shape has <b>line symmetry</b> (also called reflection symmetry) if you can fold it along a "
        "straight line so the two halves match <em>exactly</em>. That fold line is a <b>line of "
        "symmetry</b>."))
    A(figure(symmetry_fig("heart", lines=1), "A heart has 1 line of symmetry (the vertical fold)."))
    A(figure(symmetry_fig("square", lines=2), "A square has 4 lines of symmetry (2 shown — plus both diagonals)."))
    A(P("Different shapes have different numbers of symmetry lines: a rectangle has 2, an equilateral "
        "triangle has 3, a regular hexagon has 6, and a circle has <em>infinitely many</em> — any line "
        "through its centre works!"))
    A(tryit("How many lines of symmetry does an equilateral triangle have?",
            "<b>3</b> — one from each corner to the middle of the opposite side."))

    # ── SYMMETRY: ROTATIONAL ────────────────────────────────────────────
    A(H("Rotational symmetry — spin without noticing"))
    A(P("A shape has <b>rotational symmetry</b> if you can spin it less than a full turn and it looks "
        "<em>exactly the same</em>. The number of times it matches in one full turn is its <b>order</b> "
        "of rotational symmetry."))
    A(figure(rotation_fig(3), "An equilateral triangle: spin it 120° and it looks identical → order 3."))
    A(P("A square has order 4 (it matches every 90°). A regular pentagon has order 5. The letter "
        "<b>S</b> has order 2 (it looks the same upside down). Every shape has at least order 1 (a full "
        "turn always brings it back), but we only call it 'rotational symmetry' when the order is 2 or "
        "more."))
    A(kiwi("Line symmetry and rotational symmetry are different talents! A shape can have one, both, or "
           "neither. A square has the full set — 4 lines of symmetry <em>and</em> order-4 rotation. The "
           "letter S is a neat opposite: order-2 rotation but <em>no</em> line of symmetry at all. Once "
           "you can name both kinds separately, you can size up any shape."))
    A(tryit("What is the order of rotational symmetry of a square?",
            "<b>4</b> — it matches itself every 90° (90°, 180°, 270°, 360°)."))

    # ── MIRROR IMAGES ───────────────────────────────────────────────────
    A(H("Mirror images — left becomes right"))
    A(P("Hold something up to a mirror and it flips <b>left-to-right</b> — that flipped version is its "
        "<b>mirror image</b>. The letter <b>b</b> reflects into <b>d</b>; the word <b>WOW</b> still reads "
        "WOW (it's symmetric!), but <b>3</b> reflects into a backwards Ɛ. Mirror reflection is exactly "
        "the 'flip' you used to test line symmetry — a shape with line symmetry is its own mirror image "
        "across that line."))
    A(kiwi("One honest catch about letters: whether a letter has a line of symmetry depends on the "
           "<b>font</b>! Everything we say here is for plain <b>block capitals</b> (the upright, even "
           "kind, like A B C). A swirly or slanted font can break the symmetry, so the letter answers "
           "below are <em>in this block-letter font</em>. Shapes are different — a <b>perfect circle</b> "
           "has <em>infinitely many</em> lines of symmetry, no font needed."))
    A(tryit("In a mirror, the digit 2 appears reversed. In plain block capitals, which of these look the "
            "SAME in a vertical mirror? (Try A, B, M, P.)",
            "In this block-letter font: A and M look the same (they have a vertical line of symmetry); "
            "B and P do not."))

    # ── BLOOM LADDER ────────────────────────────────────────────────────
    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What do we call a flat surface of a solid?", "A face."),
        ("How many faces does a cube have?", "6."),
        ("State Euler's formula.", "F + V − E = 2."),
        ("On a die, what do two opposite faces add up to?", "7."),
        ("A fold line that makes two matching halves is called…?", "A line of symmetry."),
    ]))
    A(practice("Understand", [
        ("How many edges and vertices does a cuboid have?", "12 edges and 8 vertices."),
        ("Does a sphere have any edges or vertices?", "No — it has only one curved surface."),
        ("A cone has how many vertices?", "1 (the pointed tip)."),
        ("How many lines of symmetry does a rectangle (not a square) have?", "2."),
        ("What is the order of rotational symmetry of the letter S?", "2."),
    ]))
    A(practice("Apply", [
        ("A square pyramid has 5 vertices and 8 edges. Use Euler's formula to find its number of faces.",
         "F + 5 − 8 = 2 → F − 3 = 2 → F = 5."),
        ("The top face of a die shows 6. What's on the bottom?", "7 − 6 = 1."),
        ("How many lines of symmetry does a regular hexagon have?", "6."),
        ("What is the order of rotational symmetry of an equilateral triangle?", "3."),
        ("A pentagonal prism has 7 faces and 10 vertices. Find its number of edges (Euler).",
         "7 + 10 − E = 2 → 17 − E = 2 → E = 15."),
        ("A net has 6 identical squares. What solid might it fold into?", "A cube."),
    ]))
    A(practice("Analyze", [
        ("Two opposite faces of a die show 2 and… what? Then if a third visible face shows 3, what is its "
         "opposite?", "2's opposite is 5; 3's opposite is 4."),
        ("A solid has 4 faces and 4 vertices. Use Euler's formula to find its edges, then name it.",
         "4 + 4 − E = 2 → E = 6. A solid with 4 triangular faces is a triangular pyramid (tetrahedron)."),
        ("A shape has rotational symmetry of order 4. Through how many degrees must you turn it to match "
         "the FIRST time?", "360 ÷ 4 = 90°."),
        ("Can a shape have rotational symmetry but no line of symmetry? Give an example.",
         "Yes — the letter S (or Z), or a pinwheel: order 2 rotation, but no fold line matches the halves."),
    ]))
    A(practice("Create", [
        ("Draw a different valid net for a cube from the one shown. Describe its layout.",
         "Many work — e.g. a 'T' shape, or a 2×3 block of squares, or a staircase of 4 with one above and "
         "one below. (There are 11 in all.)"),
        ("Invent a letter or symbol (in plain block capitals) that has BOTH a line of symmetry and "
         "rotational symmetry. What did you pick?",
         "E.g. the block-capital letters H, I, O, or X — they fold to match AND spin to match. (A fancy "
         "font might spoil it, so picture upright block letters.)"),
        ("Build a dice puzzle: 'The top shows 5 and the front shows 3. What three numbers are hidden?' "
         "Solve it.", "Bottom = 7 − 5 = 2; back = 7 − 3 = 4; the left/right pair is 1 and 6 in some order."),
    ]))

    # ── CHALLENGE ───────────────────────────────────────────────────────
    A(challenge(
        P("A wooden cube is painted red on all 6 outside faces, then sliced into <b>27</b> little cubes "
          "(3 along each edge). Now sort the little cubes by how many red faces they have. How many have "
          "<b>3</b> red faces? How many have <b>2</b>? How many have <b>1</b>? And how many have "
          "<b>0</b> (completely unpainted)?") +
        tryit("Think about where each little cube sits: corner, edge, face-centre, or deep inside.",
              "<b>Corners</b> (3 red faces): a cube has 8 corners → <b>8</b>. <b>Edge-middles</b> (2 red): "
              "12 edges × 1 middle each → <b>12</b>. <b>Face-centres</b> (1 red): 6 faces × 1 centre each → "
              "<b>6</b>. <b>Hidden centre</b> (0 red): just the 1 cube buried in the middle → <b>1</b>. "
              "Check: 8 + 12 + 6 + 1 = 27 ✓. A beautiful blend of 3D geometry and counting! 🎲")))

    A(kiwi("Nicely done — that was a lot of careful counting. You can now find faces/edges/vertices, use "
           "Euler's F + V − E = 2 as a built-in checker, fold nets, read dice, and tell line symmetry "
           "from rotational symmetry. One geometry adventure remains: finding our way with "
           "<b>directions, maps and coordinates</b>. 🗺️"))

    chapter("Part 5 · Shapes, Space & Maps", 16, "Solids, Nets & Symmetry",
            "Geometry · Space & Surface", "".join(b))


# ── tables ──────────────────────────────────────────────────────────────
def _solids_table():
    rows = [("Cube", 6, 12, 8), ("Cuboid (box)", 6, 12, 8),
            ("Triangular prism", 5, 9, 6), ("Square pyramid", 5, 8, 5),
            ("Triangular pyramid", 4, 6, 4)]
    head = "<tr><th>Solid</th><th>Faces</th><th>Edges</th><th>Vertices</th></tr>"
    body = "".join(f"<tr><td>{n}</td><td>{f}</td><td>{e}</td><td>{v}</td></tr>" for n, f, e, v in rows)
    return f'<table class="pv">{head}{body}</table>'


def _euler_table():
    rows = [("Cube", 6, 8, 12), ("Cuboid", 6, 8, 12),
            ("Square pyramid", 5, 5, 8), ("Triangular prism", 5, 6, 9),
            ("Triangular pyramid", 4, 4, 6)]
    head = "<tr><th>Solid</th><th>F</th><th>V</th><th>E</th><th>F + V − E</th></tr>"
    body = "".join(f"<tr><td>{n}</td><td>{f}</td><td>{v}</td><td>{e}</td><td><b>{f+v-e}</b></td></tr>"
                   for n, f, v, e in rows)
    return f'<table class="pv">{head}{body}</table>'
