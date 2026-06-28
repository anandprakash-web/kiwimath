#!/usr/bin/env python3
"""Chapter 21 — Kangaroo Thinking Tricks  (Kangaroo · Brain Benders).

Teaches signature Math-Kangaroo-style (Écolier, Grades 3-4) problem types Socratically:
cuts-vs-pieces, fold-and-cut, cube stacks / 3D counting, grid paths, digit puzzles,
logical elimination, clever counting, working backwards, balance logic.
Every numeric answer enumerated/verified in Python before writing.
"""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)
from math import comb


# ── little custom figures, made just for this chapter ───────────────────
def rope_cuts(pieces, length_each, unit="m", col=ORANGE):
    """A rope drawn as `pieces` segments with scissors marks at the cuts between them."""
    x0, w_each, y = 30, 64, 52
    s = [f'<text x="{x0}" y="28" text-anchor="start" font-size="13" fill="{INK}">'
         f'A rope cut into {pieces} pieces of {length_each} {unit} each:</text>']
    for i in range(pieces):
        x = x0 + i * w_each
        s.append(f'<rect x="{x}" y="{y}" width="{w_each-6}" height="20" rx="6" '
                 f'fill="{col}33" stroke="{col}" stroke-width="2"/>')
        s.append(f'<text x="{x+(w_each-6)/2:.0f}" y="{y+15}" text-anchor="middle" '
                 f'font-size="12" fill="{INK}">{length_each}</text>')
        if i < pieces - 1:  # a cut mark (scissors) between this piece and the next
            cx = x + w_each - 6
            s.append(f'<text x="{cx:.0f}" y="{y-6}" text-anchor="middle" font-size="16">&#9986;</text>')
            s.append(f'<line x1="{cx:.0f}" y1="{y-2}" x2="{cx:.0f}" y2="{y+24}" '
                     f'stroke="{BERRY}" stroke-width="2" stroke-dasharray="3 3"/>')
    s.append(f'<text x="{x0}" y="{y+44}" text-anchor="start" font-size="13" '
             f'font-weight="700" fill="{BERRY}">{pieces} pieces need only {pieces-1} cuts!</text>')
    return svg("".join(s), x0 + pieces * w_each + 10, y + 56)


def cube_column(n, between=False):
    """An isometric stack (column) of n unit cubes. If between, the middle ones glow.
    Each cube is outlined in INK so the individual cubes are clearly visible."""
    cw, dp, x0, base = 46, 20, 70, 240
    s = []
    top, bot = 0, n - 1
    for i in range(n):  # draw from bottom up so higher cubes overlap correctly
        idx = n - 1 - i           # 0 = top cube
        y = base - (idx + 1) * cw
        is_end = (idx == top or idx == bot)
        mid = between and (0 < idx < n - 1)
        face = (f"{ORANGE}66" if is_end and between else (f"{GRASS}66" if mid else f"{SKY}33"))
        # front face (INK outline so each cube reads separately)
        s.append(f'<rect x="{x0}" y="{y}" width="{cw}" height="{cw}" fill="{face}" stroke="{INK}" stroke-width="1.8"/>')
        # top face
        s.append(f'<polygon points="{x0},{y} {x0+dp},{y-dp} {x0+cw+dp},{y-dp} {x0+cw},{y}" '
                 f'fill="{face}" stroke="{INK}" stroke-width="1.8"/>')
        # right face
        s.append(f'<polygon points="{x0+cw},{y} {x0+cw+dp},{y-dp} {x0+cw+dp},{y+cw-dp} {x0+cw},{y+cw}" '
                 f'fill="{face}" fill-opacity="0.65" stroke="{INK}" stroke-width="1.8"/>')
    # little labels for the red/blue ends
    if between:
        s.append(f'<text x="{x0+cw+dp+10}" y="{base-cw/2+5:.0f}" text-anchor="start" font-size="12" fill="{SKY}">bottom (blue)</text>')
        s.append(f'<text x="{x0+cw+dp+10}" y="{base-(n-0.5)*cw+5:.0f}" text-anchor="start" font-size="12" fill="{BERRY}">top (red)</text>')
    s.append(f'<text x="{x0}" y="{base+24}" text-anchor="start" font-size="13" fill="{INK}">'
             f'{n} cubes in the column</text>')
    return svg("".join(s), x0 + cw + dp + 150, base + 36, vb=f"0 -8 {x0+cw+dp+150} {base+44}")


def cube_box(w, d, h):
    """A solid w×d×h block built from unit cubes, drawn isometrically (front grid + top + side).
    Unit cubes are outlined in INK so every little cube is visible."""
    cw, dp = 28, 16
    ox, oy = 40, 24 + d * dp
    s = []
    # front face: w columns, h rows of little squares
    for r in range(h):
        for c in range(w):
            x = ox + c * cw
            y = oy + r * cw
            s.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{cw}" fill="{SKY}33" stroke="{INK}" stroke-width="1.4"/>')
    # top face: w by d parallelogram grid
    for c in range(w):
        for k in range(d):
            x = ox + c * cw + k * dp
            y = oy - k * dp
            s.append(f'<polygon points="{x},{y} {x+cw},{y} {x+cw+dp},{y-dp} {x+dp},{y-dp}" '
                     f'fill="{SKY}55" stroke="{INK}" stroke-width="1.2"/>')
    # right face: d by h grid
    fx = ox + w * cw
    for r in range(h):
        for k in range(d):
            x = fx + k * dp
            y = oy + r * cw - k * dp
            s.append(f'<polygon points="{x},{y} {x+dp},{y-dp} {x+dp},{y+cw-dp} {x},{y+cw}" '
                     f'fill="{SKY}22" stroke="{INK}" stroke-width="1.2"/>')
    W = fx + d * dp + 30
    s.append(f'<text x="{W/2}" y="{oy+h*cw+24}" text-anchor="middle" font-size="13" fill="{INK}">'
             f'{w} long &#215; {d} deep &#215; {h} tall = {w*d*h} cubes</text>')
    return svg("".join(s), W, oy + h * cw + 36)


def staircase(steps_n):
    """A staircase of unit cubes: column heights steps_n, steps_n-1, ... 1."""
    cw = 30
    cols = list(range(steps_n, 0, -1))   # heights left→right
    W = len(cols) * cw + 60
    H = steps_n * cw + 46
    base = steps_n * cw + 18
    s = []
    cnt = 0
    for c, hgt in enumerate(cols):
        for r in range(hgt):
            x = 30 + c * cw
            y = base - (r + 1) * cw
            s.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{cw}" fill="{GRASS}33" stroke="{GRASS}" stroke-width="1.6"/>')
            cnt += 1
    s.append(f'<text x="{W/2}" y="{base+24}" text-anchor="middle" font-size="13" fill="{INK}">'
             f'{"+".join(str(h) for h in cols)} = {cnt} cubes</text>')
    return svg("".join(s), W, H)


def painted_cube_2():
    """A 2×2×2 painted (orange) cube, shown whole, hinting each piece is a corner."""
    cw, dp, ox, oy = 70, 34, 40, 50
    s = []
    # front (2x2)
    for r in range(2):
        for c in range(2):
            s.append(f'<rect x="{ox+c*cw}" y="{oy+r*cw}" width="{cw}" height="{cw}" '
                     f'fill="{ORANGE}44" stroke="{INK}" stroke-width="2"/>')
    # top
    for c in range(2):
        for k in range(2):
            x = ox + c * cw + k * dp / 2
            y = oy - k * dp / 2
            s.append(f'<polygon points="{x},{y} {x+cw},{y} {x+cw+dp/2},{y-dp/2} {x+dp/2},{y-dp/2}" '
                     f'fill="{ORANGE}55" stroke="{INK}" stroke-width="1.6"/>')
    # right
    fx = ox + 2 * cw
    for r in range(2):
        for k in range(2):
            x = fx + k * dp / 2
            y = oy + r * cw - k * dp / 2
            s.append(f'<polygon points="{x},{y} {x+dp/2},{y-dp/2} {x+dp/2},{y+cw-dp/2} {x},{y+cw}" '
                     f'fill="{ORANGE}33" stroke="{INK}" stroke-width="1.6"/>')
    s.append(f'<text x="{ox+cw}" y="{oy+2*cw+24}" text-anchor="middle" font-size="13" fill="{INK}">'
             f'painted on the outside, then chopped into 8 little cubes</text>')
    return svg("".join(s), fx + dp + 40, oy + 2 * cw + 34)


def grid_paths(w, h, show_one=True):
    """A w×h grid of cells (corner-to-corner), with a sample shortest path highlighted."""
    cell = 44
    ox, oy = 30, 24
    W = w * cell + 60
    Hh = h * cell + 60
    s = []
    # grid lines
    for r in range(h + 1):
        s.append(f'<line x1="{ox}" y1="{oy+r*cell}" x2="{ox+w*cell}" y2="{oy+r*cell}" stroke="{SKY}" stroke-width="1.5" opacity=".55"/>')
    for c in range(w + 1):
        s.append(f'<line x1="{ox+c*cell}" y1="{oy}" x2="{ox+c*cell}" y2="{oy+h*cell}" stroke="{SKY}" stroke-width="1.5" opacity=".55"/>')
    # start (bottom-left) & end (top-right)
    sx, sy = ox, oy + h * cell
    ex, ey = ox + w * cell, oy
    if show_one:
        # one sample monotone path: go right w times then up h times
        path = [(sx, sy)]
        for c in range(w):
            path.append((ox + (c + 1) * cell, sy))
        for r in range(h):
            path.append((ex, sy - (r + 1) * cell))
        pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in path)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{ORANGE}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<circle cx="{sx}" cy="{sy}" r="7" fill="{GRASS}"/>')
    s.append(f'<text x="{sx-4}" y="{sy+20}" text-anchor="middle" font-size="12" font-weight="700" fill="{GRASS}">Start</text>')
    s.append(f'<circle cx="{ex}" cy="{ey}" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="{ex}" y="{ey-10}" text-anchor="middle" font-size="12" font-weight="700" fill="{BERRY}">End</text>')
    return svg("".join(s), W, Hh)


def digit_cards(digits, col=PURPLE):
    """Little digit cards in a row."""
    cw, x0 = 50, 24
    s = [f'<text x="{x0}" y="18" text-anchor="start" font-size="13" fill="{INK}">Your digit cards:</text>']
    for i, d in enumerate(digits):
        x = x0 + i * (cw + 14)
        s.append(f'<rect x="{x}" y="26" width="{cw}" height="{cw+12}" rx="9" fill="#fff" stroke="{col}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+cw/2:.0f}" y="{26+(cw+12)/2+10:.0f}" text-anchor="middle" '
                 f'font-size="30" font-weight="800" fill="{col}">{d}</text>')
    return svg("".join(s), x0 + len(digits) * (cw + 14) + 10, 26 + cw + 28)


def number_pair(prod, sm):
    """Show the 'two numbers' puzzle: a box with product on top, sum below, two mystery cards."""
    s = [f'<rect x="20" y="14" width="120" height="50" rx="10" fill="{ORANGE}1f" stroke="{ORANGE}" stroke-width="2"/>',
         f'<text x="80" y="36" text-anchor="middle" font-size="13" fill="{INK}">they MULTIPLY to</text>',
         f'<text x="80" y="56" text-anchor="middle" font-size="20" font-weight="800" fill="{ORANGE}">{prod}</text>',
         f'<rect x="20" y="78" width="120" height="50" rx="10" fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2"/>',
         f'<text x="80" y="100" text-anchor="middle" font-size="13" fill="{INK}">they ADD to</text>',
         f'<text x="80" y="120" text-anchor="middle" font-size="20" font-weight="800" fill="{GRASS}">{sm}</text>',
         f'<text x="180" y="48" text-anchor="middle" font-size="40" fill="{INK}">?</text>',
         f'<text x="240" y="48" text-anchor="middle" font-size="40" fill="{INK}">?</text>',
         f'<text x="210" y="90" text-anchor="middle" font-size="13" fill="{BERRY}">two secret numbers</text>']
    return svg("".join(s), 300, 142)


def fruit_balance(left_items, right_items, lab=""):
    """A balance scale; left_items/right_items are lists of emoji drawn in the pans."""
    s = [f'<polygon points="150,150 128,172 172,172" fill="{INK}"/>',
         f'<line x1="150" y1="48" x2="150" y2="152" stroke="{INK}" stroke-width="3"/>',
         f'<line x1="55" y1="48" x2="245" y2="48" stroke="{INK}" stroke-width="3"/>',
         f'<line x1="65" y1="48" x2="65" y2="70" stroke="{INK}" stroke-width="1.5"/>',
         f'<line x1="235" y1="48" x2="235" y2="70" stroke="{INK}" stroke-width="1.5"/>',
         f'<path d="M35 70 A30 14 0 0 0 95 70" fill="{SKY}22" stroke="{SKY}" stroke-width="2"/>',
         f'<path d="M205 70 A30 14 0 0 0 265 70" fill="{BERRY}22" stroke="{BERRY}" stroke-width="2"/>']
    for i, em in enumerate(left_items):
        s.append(f'<text x="{50+i*20}" y="66" text-anchor="middle" font-size="18">{em}</text>')
    for i, em in enumerate(right_items):
        s.append(f'<text x="{215+i*18}" y="66" text-anchor="middle" font-size="18">{em}</text>')
    s.append(f'<text x="150" y="42" text-anchor="middle" font-size="22" fill="{GRASS}" font-weight="800">=</text>')
    if lab:
        s.append(f'<text x="150" y="186" text-anchor="middle" font-size="13" fill="{INK}">{lab}</text>')
    return svg("".join(s), 300, 196)


def back_machine():
    """A 'number machine' showing input ? -> +5 -> ×2 -> 26 (working backwards)."""
    s = []
    boxes = [("?", BERRY), ("+ 5", SKY), ("&#215; 2", GRASS), ("26", ORANGE)]
    x = 16
    for i, (t, c) in enumerate(boxes):
        s.append(f'<rect x="{x}" y="30" width="70" height="44" rx="10" fill="{c}1f" stroke="{c}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+35}" y="58" text-anchor="middle" font-size="19" font-weight="800" fill="{c}">{t}</text>')
        if i < len(boxes) - 1:
            ax = x + 70
            s.append(f'<line x1="{ax}" y1="52" x2="{ax+22}" y2="52" stroke="{INK}" stroke-width="2.5"/>')
            s.append(f'<polygon points="{ax+22},52 {ax+14},47 {ax+14},57" fill="{INK}"/>')
        x += 70 + 22
    s.append(f'<text x="{x/2}" y="20" text-anchor="middle" font-size="13" fill="{INK}">Forwards: do each step left &#8594; right.</text>')
    s.append(f'<text x="{x/2}" y="92" text-anchor="middle" font-size="13" font-weight="700" fill="{BERRY}">'
             f'To find ?, walk BACKWARDS and UNDO each step.</text>')
    return svg("".join(s), x + 8, 104)


# ── the chapter ─────────────────────────────────────────────────────────
def build(chapter):
    b = []
    A = b.append

    A(big_q("Across <b>90+ countries</b>, millions of kids sit down on the same day for a famous maths "
            "contest called the <b>Math Kangaroo</b> &#129432;. The problems aren't about doing huge sums "
            "&mdash; they're clever little puzzles that reward <em>smart thinking</em>. So&hellip; what are "
            "the secret tricks the champions use? Today, you learn them all!"))
    A(kiwi("Hi, it's <b>Kiwi</b>! Let me tell you about my favourite contest. In the Math Kangaroo, the "
           "level for Grades 3 and 4 is called <b>&Eacute;colier</b> (say it ek-oh-lee-AY &mdash; it's French "
           "for little school-kid). Every question is <b>multiple choice</b> with <b>five</b> answers, "
           "labelled (A), (B), (C), (D), (E). The questions come in three flavours: <b>3-point</b> "
           "warm-ups, <b>4-point</b> thinkers, and <b>5-point</b> stars. No calculators allowed &mdash; "
           "just your brain! Here are the tricks that turn tricky problems into easy ones. &#128640;"))

    # ===================== TRICK 1 . CUTS vs PIECES =====================
    A(H("Trick 1 \U0001F99C — Cuts are one less than pieces"))
    A(P("Here's a classic Kangaroo trap. <b>To cut a rope into pieces, you always make one fewer cut than "
        "the number of pieces.</b> Why? Because the very last piece is finished by the cut <em>before</em> "
        "it &mdash; you don't need a cut at the loose end!"))
    A(figure(rope_cuts(4, 3), "A 12 m rope makes 4 pieces, but only 3 cuts (scissor marks)."))
    A(P("Count the scissors in the picture: just <b>3</b> cuts make <b>4</b> pieces. The pattern is simple "
        "and worth remembering forever:"))
    A(P("<em>pieces = cuts + 1</em>, so <em>cuts = pieces &minus; 1</em>."))
    A(example("A 12 m rope is cut into 3 m pieces. How many cuts?", steps([
        "First find the number of <b>pieces</b>: 12 &divide; 3 = <b>4 pieces</b>.",
        "Cuts are always <em>one fewer</em> than pieces: 4 &minus; 1 = <b>3 cuts</b>.",
        "Picture it: piece, cut, piece, cut, piece, cut, piece &mdash; yes, 3 snips. &#10003;",
    ]) + P("<b>Watch the trap!</b> The lazy answer is 4 (the number of pieces). The careful answer is "
           "<b>3</b>. Kangaroo loves this one!")))
    A(tryit("A log is sawn into <b>5</b> equal pieces. How many saw-cuts are needed?",
            "Cuts = pieces &minus; 1 = 5 &minus; 1 = <b>4 cuts</b>."))
    A(tryit("A 20 m ribbon is cut into 4 m pieces. How many pieces, and how many cuts?",
            "Pieces: 20 &divide; 4 = <b>5 pieces</b>. Cuts: 5 &minus; 1 = <b>4 cuts</b>."))

    # ===================== TRICK 2 . FOLD AND CUT =====================
    A(H("Trick 2 \U0001F99C — Fold and punch: each fold doubles the holes"))
    A(P("Fold a piece of paper, punch <em>one</em> hole, then imagine opening it. How many holes appear? "
        "The secret is <b>layers</b>: folding stacks the paper, and the punch goes through every layer at "
        "once. <b>Each fold doubles the number of layers.</b>"))
    A(figure(svg(
        f'<rect x="20" y="34" width="60" height="84" fill="{GOLD}18" stroke="{INK}" stroke-width="2"/>'
        f'<text x="50" y="28" text-anchor="middle" font-size="11" fill="{ORANGE}">folded twice</text>'
        f'<circle cx="50" cy="76" r="8" fill="{BERRY}"/>'
        f'<text x="50" y="134" text-anchor="middle" font-size="11" fill="{INK}">1 punch &#183; 4 layers</text>'
        f'<text x="120" y="82" text-anchor="middle" font-size="26" fill="{INK}">&#8594;</text>'
        f'<rect x="170" y="34" width="120" height="84" fill="{GOLD}18" stroke="{INK}" stroke-width="2"/>'
        f'<line x1="230" y1="34" x2="230" y2="118" stroke="{ORANGE}" stroke-width="1.4" stroke-dasharray="4 4"/>'
        f'<line x1="170" y1="76" x2="290" y2="76" stroke="{ORANGE}" stroke-width="1.4" stroke-dasharray="4 4"/>'
        f'<circle cx="200" cy="58" r="8" fill="{BERRY}"/><circle cx="260" cy="58" r="8" fill="{BERRY}"/>'
        f'<circle cx="200" cy="94" r="8" fill="{BERRY}"/><circle cx="260" cy="94" r="8" fill="{BERRY}"/>'
        f'<text x="230" y="134" text-anchor="middle" font-size="11" fill="{INK}">unfolded &#183; 4 holes</text>',
        320, 150), "Two folds make 4 layers, so one punch gives 4 holes &mdash; mirrored across both fold lines."))
    A(kiwi("Here's the doubling ladder, and it's worth memorising:<br>"
           "&bull; fold <b>1</b> time &rarr; 2 layers &rarr; 1 punch = <b>2</b> holes,<br>"
           "&bull; fold <b>2</b> times &rarr; 4 layers &rarr; 1 punch = <b>4</b> holes,<br>"
           "&bull; fold <b>3</b> times &rarr; 8 layers &rarr; 1 punch = <b>8</b> holes.<br>"
           "Each fold <em>doubles</em> the last answer: 2, 4, 8, 16&hellip; &#129529;"))
    A(example("Fold a paper in half twice, punch one hole. How many holes when opened?", steps([
        "First fold &rarr; <b>2</b> layers.",
        "Second fold &rarr; 2 &times; 2 = <b>4</b> layers stacked together.",
        "One punch pierces all 4, so opening it shows <b>4 holes</b>. &#10003;",
    ])))
    A(tryit("You fold a square in half <b>three</b> times, then snip one hole. How many holes appear "
            "when you unfold it?",
            "Three folds &rarr; 2 &times; 2 &times; 2 = 8 layers &rarr; one snip = <b>8 holes</b>."))

    # ===================== TRICK 3 . CUBE STACKS / 3D COUNTING =====================
    A(H("Trick 3 \U0001F99C — Counting cubes you can and can't see"))
    A(P("Kangaroo loves <b>cube</b> problems. Sometimes cubes are stacked in a tower; sometimes they're "
        "packed into a box; sometimes they hide behind one another. The trick is to <b>count layer by "
        "layer</b> and remember the cubes you cannot see are still there!"))
    A(P("First, an easy tower. Five cubes are stacked in a single column. The bottom one is blue, the top "
        "one is red. How many cubes sit <em>between</em> them?"))
    A(figure(cube_column(5, between=True), "A column of 5 cubes. The 3 green ones are between top and bottom."))
    A(example("how many cubes are between the top and bottom?", steps([
        "There are <b>5</b> cubes in the column.",
        "Take away the <b>top</b> one and the <b>bottom</b> one: 5 &minus; 2 = <b>3</b>.",
        "So <b>3</b> cubes are sandwiched in between. &#10003;",
    ])))
    A(P("Now a solid box. These little cubes are stacked into a block that is <b>4 long, 3 deep and 2 "
        "tall</b>. How many cubes is that?"))
    A(figure(cube_box(4, 3, 2), "A 4 &times; 3 &times; 2 block of unit cubes."))
    A(example("how many cubes fill the box?", steps([
        "Multiply the three sides together: length &times; depth &times; height.",
        "4 &times; 3 &times; 2 = <b>24 cubes</b>. &#10003;",
        "Tip: count one flat layer first (4 &times; 3 = 12), then double it for the 2 layers &rarr; 24.",
    ])))
    A(kiwi("Big secret for the <b>painted cube</b> puzzle: take a cube, paint the whole outside, then chop "
           "it into 8 little cubes (a 2 &times; 2 &times; 2). Because it's so small, <em>every</em> little "
           "cube is a corner &mdash; and a corner shows <b>3</b> painted faces. So all 8 little cubes have "
           "exactly 3 painted faces!"))
    A(figure(painted_cube_2(), "Paint the outside, then cut into 8 — each piece is a corner with 3 painted faces."))
    A(tryit("A staircase is built from cubes: the bottom row has 4 cubes, then 3, then 2, then 1 on top. "
            "How many cubes in the whole staircase?",
            "Add the rows: 4 + 3 + 2 + 1 = <b>10 cubes</b>."))
    A(figure(staircase(4), "A 4-step staircase: 4 + 3 + 2 + 1 = 10 cubes."))

    # ===================== TRICK 4 . GRID PATHS =====================
    A(H("Trick 4 \U0001F99C — Counting routes on a grid"))
    A(P("Imagine a tiny town drawn as a grid. You start at the bottom-left corner and want to reach the "
        "top-right corner, only ever going <b>right</b> or <b>up</b> (never backward). How many shortest "
        "routes are there? The clever way is to <b>write the number of ways to reach each corner</b>, "
        "building up from the start."))
    A(figure(grid_paths(2, 2), "A 2 &times; 2 grid. One shortest route (right, right, up, up) is shown in orange."))
    A(P("Here's the building trick: the number of ways to reach a corner is the <b>sum</b> of the ways to "
        "reach the corner just below it and the corner just to its left (because you can only arrive from "
        "below or from the left). Start every edge corner with a <b>1</b>, then add your way to the top:"))
    A(example("counting the routes across a 2 &times; 2 grid", steps([
        "Every corner along the bottom edge and the left edge has just <b>1</b> way to reach it (straight along).",
        "The first inside corner = (way from below) + (way from left) = 1 + 1 = <b>2</b>.",
        "Keep adding corner by corner up to the top-right&hellip; you reach <b>6</b>.",
        "So there are <b>6</b> shortest routes from Start to End. &#10003;",
    ]) + P("<b>Smart check:</b> you must take 2 steps right and 2 steps up in some order &mdash; and there "
           "are exactly 6 different orders. Same answer!")))
    A(tryit("On a grid that is <b>3 wide and 2 tall</b> (cells), how many shortest routes go from the "
            "bottom-left corner to the top-right corner, moving only right or up?",
            "Build the corner sums (1s along the edges, then add): the top-right corner comes out to "
            "<b>10</b> routes."))

    # ===================== TRICK 5 . DIGIT PUZZLES =====================
    A(H("Trick 5 \U0001F99C — Two numbers from a product and a sum"))
    A(P("A Kangaroo-style favourite: <b>two whole numbers multiply to give one total and add to give "
        "another &mdash; find them!</b> The trick is to <b>list the multiplication pairs first</b>, then "
        "check which pair has the right sum."))
    A(figure(number_pair(12, 7), "Two mystery numbers: they multiply to 12 and add to 7."))
    A(example("two numbers multiply to 12 and add to 7", steps([
        "List pairs that multiply to <b>12</b>: 1&times;12, 2&times;6, 3&times;4.",
        "Now check each <b>sum</b>: 1+12 = 13 &#10007;, 2+6 = 8 &#10007;, 3+4 = <b>7</b> &#10003;.",
        "The two numbers are <b>3 and 4</b>. &#10003;",
    ])))
    A(kiwi("The other digit puzzle uses <b>digit cards</b>. With cards <b>1, 3, 5</b> you can build "
           "different numbers. To make the <b>largest</b> number, put the biggest digit first (5, then 3, "
           "then 1 &rarr; 531). For the <b>smallest</b>, put the smallest digit first (1, 3, 5 &rarr; 135)."))
    A(figure(digit_cards([1, 3, 5]), "Three digit cards — rearrange them to make different numbers."))
    A(example("largest and smallest 3-digit number from cards 1, 3, 5", steps([
        "<b>Largest:</b> biggest digit on the left &rarr; 5, then 3, then 1 = <b>531</b>.",
        "<b>Smallest:</b> smallest digit on the left &rarr; 1, then 3, then 5 = <b>135</b>.",
        "(Using each card once, you can make 6 different numbers in all.)",
    ])))
    A(tryit("Two whole numbers multiply to <b>48</b> and add to <b>14</b>. What are they?",
            "Pairs for 48: 6 &times; 8 gives a sum of 6 + 8 = 14 &#10003;. The numbers are <b>6 and 8</b>."))
    A(tryit("Using the digit cards <b>2, 4, 7</b> once each, what is the largest 3-digit number you can "
            "make? And the smallest?",
            "Largest <b>742</b> (big digit first); smallest <b>247</b> (small digit first)."))

    # ===================== TRICK 6 . LOGICAL ELIMINATION + WEIGHING =====================
    A(H("Trick 6 \U0001F99C — Line them up: most, least, heaviest, lightest"))
    A(P("When clues compare things &mdash; taller, older, heavier &mdash; the trick is to <b>line "
        "everything up in order</b>, like beads on a string. Then the answer just reads off one end."))
    A(P("Clue 1: a <b>watermelon</b> is heavier than a <b>pumpkin</b>. Clue 2: a <b>pumpkin</b> is heavier "
        "than an <b>apple</b>. Which is lightest? Chain the clues: watermelon &gt; pumpkin &gt; apple. "
        "Reading the small end, the <b>apple</b> is lightest, and the <b>watermelon</b> is heaviest."))
    A(figure(fruit_balance(["\U0001F349"], ["\U0001F383", "\U0001F383", "\U0001F383"],
                           "1 watermelon balances 3 pumpkins"),
             "A balance shows when two sides weigh the same — here 1 watermelon equals 3 pumpkins."))
    A(example("Sara is 9, Tom is 12, Ravi is 7. Who is the youngest?", steps([
        "Line up the ages from small to big: 7 (Ravi), 9 (Sara), 12 (Tom).",
        "The <b>smallest</b> age is 7.",
        "So <b>Ravi</b> is the youngest. &#10003;",
    ])))
    A(kiwi("Balance puzzles use the same idea, but with <em>equal</em> weights. If 1 melon balances 3 "
           "apples, and 1 apple balances 2 plums, then 1 melon balances 3 &times; 2 = <b>6 plums</b>. You "
           "just swap each thing for what it equals &mdash; step by step."))
    A(tryit("A feather is lighter than a stone, and a stone is lighter than a brick. Which is the "
            "heaviest?",
            "Chain it: feather &lt; stone &lt; brick. The <b>brick</b> is heaviest."))

    # ===================== TRICK 7 . CLEVER COUNTING =====================
    A(H("Trick 7 \U0001F99C — Clever counting (don't count one by one!)"))
    A(P("Some problems look like you must count a hundred things &mdash; but a smart shortcut hides inside. "
        "<b>Group, multiply, and subtract</b> instead of counting one at a time."))
    A(example("A hall has 4 rows of 5 chairs, but 3 chairs are broken. How many good chairs?", steps([
        "Count <em>all</em> the chairs first: 4 rows &times; 5 = <b>20 chairs</b>.",
        "Take away the broken ones: 20 &minus; 3 = <b>17</b>.",
        "So there are <b>17</b> good chairs. &#10003;",
    ])))
    A(example("Tickets cost &#8377;40 for an adult and &#8377;20 for a child. What do 2 adults and 3 "
              "children pay?", steps([
        "Adults: 2 &times; &#8377;40 = <b>&#8377;80</b>.",
        "Children: 3 &times; &#8377;20 = <b>&#8377;60</b>.",
        "Add the two groups: &#8377;80 + &#8377;60 = <b>&#8377;140</b>. &#10003;",
    ])))
    A(tryit("A car park has 6 rows with 8 cars in each row, but 5 spaces are empty. How many cars are "
            "parked?",
            "All spaces: 6 &times; 8 = 48. Empty: 5. Cars: 48 &minus; 5 = <b>43 cars</b>."))

    # ===================== TRICK 8 . CALENDAR & CLOCK =====================
    A(H("Trick 8 \U0001F99C — Calendar and clock loops"))
    A(P("Days and months go in <b>loops</b>, so the trick is to use the size of the loop. There are "
        "<b>7</b> days in a week and <b>12</b> months in a year &mdash; so jumping a whole loop brings you "
        "right back where you started."))
    A(example("Today is Wednesday. What day is it after 10 days?", steps([
        "A whole week is 7 days and lands on the <b>same</b> day, so ignore 7 of the 10 days.",
        "That leaves 10 &minus; 7 = <b>3</b> days to step forward.",
        "Wed &rarr; Thu (1) &rarr; Fri (2) &rarr; <b>Sat</b> (3).",
        "So 10 days after Wednesday is a <b>Saturday</b>. &#10003;",
    ])))
    A(P("Clocks loop too. To find an end time, <b>count up to the next whole hour first</b>, then add the "
        "leftover minutes."))
    A(example("A cartoon starts at 9:50 and lasts 25 minutes. When does it end?", steps([
        "From <b>9:50</b>, 10 minutes reaches <b>10:00</b> (the next whole hour).",
        "We've used 10 of the 25 minutes; 25 &minus; 10 = <b>15</b> minutes left.",
        "15 minutes after 10:00 is <b>10:15</b>. &#10003;",
    ])))
    A(tryit("The month right after <b>September</b> is which month? And 3 months after <b>October</b>?",
            "After September comes <b>October</b>. Three months after October: Nov &rarr; Dec &rarr; "
            "<b>January</b>."))

    # ===================== TRICK 9 . WORKING BACKWARDS =====================
    A(H("Trick 9 \U0001F99C — Working backwards (undo the steps)"))
    A(P("&ldquo;I think of a number, do some steps, and end with 26 &mdash; what did I start with?&rdquo; "
        "The trick is to go through the steps <b>in reverse</b>, and <b>undo</b> each one: + becomes "
        "&minus;, &times; becomes &divide;."))
    A(figure(back_machine(), "A number machine. To find the secret start, walk back and undo each step."))
    A(example("I think of a number, add 5, then double it, and get 26. What was my number?", steps([
        "Last step was <b>&times; 2</b> &rarr; undo it with <b>&divide; 2</b>: 26 &divide; 2 = <b>13</b>.",
        "Step before was <b>+ 5</b> &rarr; undo it with <b>&minus; 5</b>: 13 &minus; 5 = <b>8</b>.",
        "So the secret number was <b>8</b>.",
        "Check forwards: 8 + 5 = 13, then 13 &times; 2 = 26. &#10003;",
    ])))
    A(tryit("I think of a number, multiply it by 3, then subtract 4, and get 17. What was my number?",
            "Undo backwards: 17 + 4 = 21, then 21 &divide; 3 = <b>7</b>. (Check: 7 &times; 3 = 21, "
            "21 &minus; 4 = 17. &#10003;)"))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now you try — climb the Kangaroo ladder \U0001F99C"))
    A(P("These are written in the Kangaroo spirit &mdash; a little trickier as you go up. Try each one "
        "yourself, then peek. Remember: <em>think smart, not hard.</em>"))

    A(practice("Remember", [
        ("To cut a rope into 6 pieces, how many cuts do you make?", "6 &minus; 1 = <b>5 cuts</b>."),
        ("Fold a paper in half once and punch one hole. How many holes when unfolded?", "<b>2 holes</b>."),
        ("How many little cubes are in a 2 &times; 2 &times; 2 stack?", "2 &times; 2 &times; 2 = <b>8 cubes</b>."),
        ("How many days are in one week?", "<b>7 days</b>."),
        ("The month right after May is ____.", "<b>June</b>."),
    ]))
    A(practice("Understand", [
        ("A 15 m rope is cut into 5 m pieces. How many pieces, and how many cuts?",
         "Pieces 15 &divide; 5 = 3; cuts 3 &minus; 1 = <b>2 cuts</b>."),
        ("Fold a paper twice, then punch one hole. How many holes appear?",
         "2 &times; 2 = 4 layers &rarr; <b>4 holes</b>."),
        ("Five cubes are stacked in a column. How many are between the top and bottom cubes?",
         "5 &minus; 2 = <b>3 cubes</b>."),
        ("Two numbers multiply to 24 and add to 11. What are they?",
         "Pairs for 24: 3 &times; 8 add to 11 &rarr; <b>3 and 8</b>."),
        ("Today is Tuesday. What day is it after exactly 7 days?",
         "The same day &mdash; <b>Tuesday</b> (7 days = one full week)."),
    ]))
    A(practice("Apply", [
        ("A block of cubes is 4 long, 3 wide and 2 tall. How many cubes is that?",
         "4 &times; 3 &times; 2 = <b>24 cubes</b>."),
        ("A hall has 5 rows of 6 chairs, but 4 chairs are broken. How many good chairs?",
         "5 &times; 6 = 30; 30 &minus; 4 = <b>26 chairs</b>."),
        ("A film starts at 9:50 and runs for 25 minutes. What time does it end?",
         "9:50 + 10 min = 10:00; + 15 min = <b>10:15</b>."),
        ("Using digit cards 2, 4, 7 once each, make the largest and smallest 3-digit numbers.",
         "Largest <b>742</b>, smallest <b>247</b>."),
        ("I think of a number, add 4, then double it, and get 20. What was my number?",
         "Undo: 20 &divide; 2 = 10, then 10 &minus; 4 = <b>6</b>."),
    ]))
    A(practice("Analyze", [
        ("On a grid 2 cells wide and 2 cells tall, how many shortest routes go from the bottom-left to the "
         "top-right corner, moving only right or up?",
         "Build the corner-sums (1 along each edge, then add): you reach <b>6</b> routes."),
        ("A cube is painted all over and then cut into 8 equal little cubes (a 2 &times; 2 &times; 2). How "
         "many little cubes have exactly 3 painted faces?",
         "Every little cube is a corner, and corners show 3 faces, so <b>all 8</b> have 3 painted faces."),
        ("A watermelon is heavier than a pumpkin, and a pumpkin is heavier than an apple. List the three "
         "from lightest to heaviest.",
         "<b>apple, pumpkin, watermelon</b> (chain the clues: apple &lt; pumpkin &lt; watermelon)."),
        ("Today is Wednesday. What day will it be after 10 days?",
         "10 &minus; 7 = 3 days past Wednesday &rarr; <b>Saturday</b>."),
        ("I think of a number, multiply by 3, subtract 4, and get 17. What was the number?",
         "Undo: 17 + 4 = 21, then 21 &divide; 3 = <b>7</b>."),
    ]))
    A(practice("Create", [
        ("Make up your own cuts-and-pieces puzzle whose answer is <b>4 cuts</b>. (One example given.)",
         "&ldquo;A 25 m rope is cut into 5 m pieces &mdash; how many cuts?&rdquo; &rarr; 5 pieces, 4 cuts. "
         "Any rope giving 5 pieces works."),
        ("Invent a 'two-number' puzzle where the numbers are <b>4 and 9</b>. Give the product and the sum.",
         "They multiply to 4 &times; 9 = 36 and add to 4 + 9 = 13. So: &ldquo;Two numbers multiply to 36 "
         "and add to 13 &mdash; find them.&rdquo;"),
        ("Design a folding puzzle whose answer is <b>8 holes</b>. How many folds and how many punches?",
         "Fold the paper <b>3</b> times and make <b>1</b> punch: 2 &times; 2 &times; 2 = 8 layers = 8 holes."),
    ]))

    A(challenge(
        P("\U0001F99C <b>The Kangaroo Triple.</b> Put three tricks together! "
          "(a) A 21 m rope is cut into 3 m pieces &mdash; how many <b>cuts</b>? "
          "(b) A paper is folded in half twice, then one hole is punched &mdash; how many <b>holes</b> when "
          "unfolded? "
          "(c) Two whole numbers multiply to <b>36</b> and add to <b>13</b> &mdash; what are they? "
          "Now add together the cuts, the holes, and the <em>larger</em> of the two numbers. What total "
          "do you get?") +
        tryit("Solve each part, then add the three.",
              "(a) Pieces = 21 &divide; 3 = 7, so cuts = 7 &minus; 1 = <b>6</b>. "
              "(b) Two folds &rarr; 4 layers &rarr; <b>4</b> holes. "
              "(c) Pairs of 36: 4 &times; 9 = 36 and 4 + 9 = 13 &#10003;, so the numbers are 4 and 9; the "
              "larger is <b>9</b>. "
              "Add them up: 6 + 4 + 9 = <b>19</b>. &#127881;")))

    A(kiwi("Look what you can do now! Cuts-and-pieces, fold-and-punch, cube counting, grid routes, "
           "two-number puzzles, lining things up, clever counting, calendar and clock loops, and working "
           "backwards. These nine tricks are exactly the thinking Kangaroo stars use. In the very next "
           "chapter, you'll put them to the test in a <b>Kangaroo-style Challenge Set</b> &mdash; 3-point, "
           "4-point, and 5-point problems, in the style of the contest. Sharpen your pencil! &#129432;&#10024;"))

    chapter("Part 7 · 🦘 Kangaroo Corner", 21, "Kangaroo Thinking Tricks",
            "Kangaroo · Brain Benders", "".join(b))
