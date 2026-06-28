#!/usr/bin/env python3
"""Chapter 22 — Kangaroo-style Challenge Set (3·4·5 points)  (Kangaroo · Brain Benders).

A GRADED problem set in the style of Math Kangaroo (Écolier, Grades 3-4).
Three tiers via practice(): 3-Point Warm-ups, 4-Point Thinkers, 5-Point Stars
(8 problems each = 24 MCQs). Each problem is a five-option MCQ; the reveal gives
the correct LETTER plus a short worked solution. Every answer enumerated in Python.
"""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)
from math import comb


# ── helpers for laying out 5-option MCQs ────────────────────────────────
def opts(a, b, c, d, e):
    """Render the five Kangaroo answer choices (A)..(E) on one tidy line."""
    items = [("A", a), ("B", b), ("C", c), ("D", d), ("E", e)]
    inner = " &nbsp; ".join(f"<b>({L})</b>&nbsp;{v}" for L, v in items)
    return f'<div class="kopts" style="margin-top:6px;font-size:15px">{inner}</div>'


def Q(text, a, b, c, d, e):
    """A Kangaroo question stem followed by its five options."""
    return text + opts(a, b, c, d, e)


# ── custom figures for the visual problems ──────────────────────────────
def rope_seg(pieces, col=ORANGE):
    """A rope shown as `pieces` joined segments with scissor marks between."""
    x0, w_each, y = 24, 56, 30
    s = []
    for i in range(pieces):
        x = x0 + i * w_each
        s.append(f'<rect x="{x}" y="{y}" width="{w_each-6}" height="20" rx="6" '
                 f'fill="{col}33" stroke="{col}" stroke-width="2"/>')
        if i < pieces - 1:
            cx = x + w_each - 6
            s.append(f'<line x1="{cx}" y1="{y-6}" x2="{cx}" y2="{y+26}" stroke="{BERRY}" '
                     f'stroke-width="2" stroke-dasharray="3 3"/>')
            s.append(f'<text x="{cx}" y="{y-10}" text-anchor="middle" font-size="13">&#9986;</text>')
    return svg("".join(s), x0 + pieces * w_each + 10, y + 40)


def stack2x2x2():
    """An isometric 2x2x2 cube stack (8 unit cubes), outlined in INK so every cube shows."""
    cw, dp, ox, oy = 50, 26, 50, 60
    s = []
    for r in range(2):
        for c in range(2):
            s.append(f'<rect x="{ox+c*cw}" y="{oy+r*cw}" width="{cw}" height="{cw}" '
                     f'fill="{SKY}33" stroke="{INK}" stroke-width="1.8"/>')
    for c in range(2):
        for k in range(2):
            x = ox + c * cw + k * dp / 2
            y = oy - k * dp / 2
            s.append(f'<polygon points="{x},{y} {x+cw},{y} {x+cw+dp/2},{y-dp/2} {x+dp/2},{y-dp/2}" '
                     f'fill="{SKY}55" stroke="{INK}" stroke-width="1.6"/>')
    fx = ox + 2 * cw
    for r in range(2):
        for k in range(2):
            x = fx + k * dp / 2
            y = oy + r * cw - k * dp / 2
            s.append(f'<polygon points="{x},{y} {x+dp/2},{y-dp/2} {x+dp/2},{y+cw-dp/2} {x},{y+cw}" '
                     f'fill="{SKY}22" stroke="{INK}" stroke-width="1.6"/>')
    return svg("".join(s), fx + dp + 30, oy + 2 * cw + 20)


def fold_diagram(folds, holes_positions, W=300):
    """LEFT: a folded stack with 1 punch.  RIGHT: opened sheet with the holes shown."""
    s = []
    # folded stack on the left
    s.append(f'<rect x="20" y="34" width="54" height="80" fill="{GOLD}18" stroke="{INK}" stroke-width="2"/>')
    s.append(f'<text x="47" y="28" text-anchor="middle" font-size="11" fill="{ORANGE}">folded {folds}&#215;</text>')
    s.append(f'<circle cx="47" cy="74" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="47" y="128" text-anchor="middle" font-size="11" fill="{INK}">1 punch</text>')
    s.append(f'<text x="105" y="80" text-anchor="middle" font-size="24" fill="{INK}">&#8594;</text>')
    # opened sheet on the right
    ox, oy, ow, oh = 150, 34, 130, 80
    s.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{GOLD}18" stroke="{INK}" stroke-width="2"/>')
    for fx, fy in holes_positions:
        s.append(f'<circle cx="{ox+fx*ow:.0f}" cy="{oy+fy*oh:.0f}" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="{ox+ow/2:.0f}" y="128" text-anchor="middle" font-size="11" fill="{INK}">'
             f'unfolded &#183; {len(holes_positions)} holes</text>')
    return svg("".join(s), W, 140)


def grid_fig(w, h):
    """A clean w×h grid of cells with marked Start (bottom-left) and End (top-right)."""
    cell, ox, oy = 42, 30, 22
    W, Hh = w * cell + 56, h * cell + 56
    s = []
    for r in range(h + 1):
        s.append(f'<line x1="{ox}" y1="{oy+r*cell}" x2="{ox+w*cell}" y2="{oy+r*cell}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    for c in range(w + 1):
        s.append(f'<line x1="{ox+c*cell}" y1="{oy}" x2="{ox+c*cell}" y2="{oy+h*cell}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    sx, sy = ox, oy + h * cell
    ex, ey = ox + w * cell, oy
    s.append(f'<circle cx="{sx}" cy="{sy}" r="7" fill="{GRASS}"/>')
    s.append(f'<text x="{sx-2}" y="{sy+19}" text-anchor="middle" font-size="11" font-weight="700" fill="{GRASS}">Start</text>')
    s.append(f'<circle cx="{ex}" cy="{ey}" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="{ex}" y="{ey-9}" text-anchor="middle" font-size="11" font-weight="700" fill="{BERRY}">End</text>')
    return svg("".join(s), W, Hh)


def staircase_fig(n):
    """A staircase of unit cubes (heights n, n-1, ... 1)."""
    cw, ox = 28, 28
    cols = list(range(n, 0, -1))
    W, Hh = len(cols) * cw + 50, n * cw + 40
    base = n * cw + 14
    s = []
    for c, hgt in enumerate(cols):
        for r in range(hgt):
            x = ox + c * cw
            y = base - (r + 1) * cw
            s.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{cw}" fill="{GRASS}33" stroke="{GRASS}" stroke-width="1.6"/>')
    return svg("".join(s), W, Hh)


def painted_4cube():
    """A 4x4x4 painted cube (front face shaded orange) to set the 'no painted face' star."""
    cw, dp, ox, oy = 26, 16, 40, 40
    s = []
    for r in range(4):
        for c in range(4):
            s.append(f'<rect x="{ox+c*cw}" y="{oy+r*cw}" width="{cw}" height="{cw}" '
                     f'fill="{ORANGE}33" stroke="{INK}" stroke-width="1.3"/>')
    for c in range(4):
        for k in range(4):
            x = ox + c * cw + k * dp / 4
            y = oy - k * dp / 4
            s.append(f'<polygon points="{x},{y} {x+cw},{y} {x+cw+dp/4},{y-dp/4} {x+dp/4},{y-dp/4}" '
                     f'fill="{ORANGE}44" stroke="{INK}" stroke-width="0.9"/>')
    fx = ox + 4 * cw
    for r in range(4):
        for k in range(4):
            x = fx + k * dp / 4
            y = oy + r * cw - k * dp / 4
            s.append(f'<polygon points="{x},{y} {x+dp/4},{y-dp/4} {x+dp/4},{y+cw-dp/4} {x},{y+cw}" '
                     f'fill="{ORANGE}22" stroke="{INK}" stroke-width="0.9"/>')
    s.append(f'<text x="{ox+2*cw}" y="{oy+4*cw+22}" text-anchor="middle" font-size="13" fill="{INK}">'
             f'a 4 &#215; 4 &#215; 4 cube, painted all over</text>')
    return svg("".join(s), fx + dp + 30, oy + 4 * cw + 32)


def hands_circle(n):
    """n friends in a circle, all pairs joined by a line (handshake figure)."""
    import math
    cx, cy, r = 110, 100, 70
    pts = [(cx + r * math.cos(math.radians(-90 + i * 360 / n)),
            cy + r * math.sin(math.radians(-90 + i * 360 / n))) for i in range(n)]
    s = []
    for i in range(n):
        for j in range(i + 1, n):
            s.append(f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" x2="{pts[j][0]:.0f}" '
                     f'y2="{pts[j][1]:.0f}" stroke="{SKY}" stroke-width="1.6" opacity=".7"/>')
    for (x, y) in pts:
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="11" fill="{ORANGE}"/>')
        s.append(f'<text x="{x:.0f}" y="{y+5:.0f}" text-anchor="middle" font-size="14">&#128100;</text>')
    return svg("".join(s), 220, 200)


def balance_chain():
    """Two balance pictures: melon=3 apples, apple=2 plums."""
    def pan(items_l, items_r, ox):
        ss = [f'<polygon points="{ox+60},96 {ox+44},112 {ox+76},112" fill="{INK}"/>',
              f'<line x1="{ox+60}" y1="34" x2="{ox+60}" y2="98" stroke="{INK}" stroke-width="2.4"/>',
              f'<line x1="{ox+18}" y1="34" x2="{ox+102}" y2="34" stroke="{INK}" stroke-width="2.4"/>',
              f'<path d="M{ox+6} 48 A22 11 0 0 0 {ox+50} 48" fill="{SKY}22" stroke="{SKY}" stroke-width="1.8"/>',
              f'<path d="M{ox+70} 48 A22 11 0 0 0 {ox+114} 48" fill="{BERRY}22" stroke="{BERRY}" stroke-width="1.8"/>']
        for i, em in enumerate(items_l):
            ss.append(f'<text x="{ox+28+i*0}" y="46" text-anchor="middle" font-size="15">{em}</text>')
        for i, em in enumerate(items_r):
            ss.append(f'<text x="{ox+78+i*14}" y="46" text-anchor="middle" font-size="15">{em}</text>')
        ss.append(f'<text x="{ox+60}" y="30" text-anchor="middle" font-size="16" fill="{GRASS}" font-weight="800">=</text>')
        return "".join(ss)
    s = pan(["\U0001F349"], ["\U0001F34E", "\U0001F34E", "\U0001F34E"], 0)
    s += pan(["\U0001F34E"], ["\U0001F7E3", "\U0001F7E3"], 150)
    s += f'<text x="150" y="128" text-anchor="middle" font-size="12" fill="{INK}">1 melon = 3 apples    and    1 apple = 2 plums</text>'
    return svg(s, 300, 138)


# ── the chapter ─────────────────────────────────────────────────────────
def build(chapter):
    b = []
    A = b.append

    A(big_q("You've learned the tricks &mdash; now it's contest day! &#129432; Here is a <b>Kangaroo-style</b> "
            "Challenge Set, written in the style of the Math Kangaroo (&Eacute;colier level). Can you earn "
            "3-point, 4-point and 5-point problems just like the champions in 90+ countries?"))
    A(kiwi("Welcome to the arena, it's <b>Kiwi</b> cheering you on! Quick rules, just like the real "
           "contest: every problem is <b>multiple choice</b> with five answers, <b>(A)</b> to <b>(E)</b>. "
           "Pick the one best answer. <b>No calculator</b> &mdash; use the tricks from the last chapter! "
           "Work each tier in order: the <b>3-point</b> warm-ups build your confidence, the <b>4-point</b> "
           "thinkers make you pause, and the <b>5-point</b> stars are the real brain-benders. Try first, "
           "then open the answer to see the correct <b>letter</b> and how it's done. Ready&hellip; go! &#128640;"))

    A(kiwi("&#128161; <b>Kangaroo strategy:</b> if a problem looks scary, you don't always need the exact "
           "answer first &mdash; you can sometimes <em>knock out</em> answers that are clearly too big or "
           "too small, and pick from what's left. And always re-read the question: many Kangaroo traps "
           "(like cuts-vs-pieces) catch kids who answer too fast!"))

    # ===================== 3-POINT WARM-UPS =====================
    A(H("\U0001F99C 3-Point Warm-ups"))
    A(P("Gentle starters to warm up your thinking. Each is worth <b>3 points</b>."))
    A(figure(rope_seg(3), "Warm-up 1: a rope cut into 3 pieces."))
    A(figure(stack2x2x2(), "Warm-up 3: a cube stack — count the little cubes."))

    A(practice("3-Point Warm-ups", [
        (Q("A 18 m rope is cut into pieces that are each 6 m long. How many <b>cuts</b> are needed? "
           "(See the picture above.)",
           "1", "2", "3", "4", "6"),
         "<b>(B) 2.</b> Pieces = 18 &divide; 6 = 3. Cuts are one fewer than pieces: 3 &minus; 1 = <b>2</b>."),

        (Q("A piece of paper is folded in half <b>once</b>, then one hole is punched through it. How many "
           "holes are there when you unfold the paper?",
           "1", "2", "3", "4", "8"),
         "<b>(B) 2.</b> One fold makes 2 layers, so the single punch goes through both &rarr; <b>2 holes</b>."),

        (Q("How many small cubes are in the stack shown above (it is 2 cubes long, 2 deep and 2 tall)?",
           "4", "6", "8", "9", "12"),
         "<b>(C) 8.</b> Multiply the sides: 2 &times; 2 &times; 2 = <b>8</b> little cubes."),

        (Q("Maya has three digit cards: <b>1</b>, <b>2</b> and <b>3</b>. Using each card exactly once, how "
           "many different 3-digit numbers can she make?",
           "3", "5", "6", "8", "9"),
         "<b>(C) 6.</b> They are 123, 132, 213, 231, 312, 321 &mdash; that's <b>6</b> numbers."),

        (Q("A cinema ticket costs &#8377;40 for an adult and &#8377;20 for a child. What is the total cost "
           "for 2 adults and 3 children?",
           "&#8377;100", "&#8377;120", "&#8377;140", "&#8377;160", "&#8377;200"),
         "<b>(C) &#8377;140.</b> Adults: 2 &times; 40 = 80. Children: 3 &times; 20 = 60. Total = 80 + 60 = <b>140</b>."),

        (Q("The months go January, February, March&hellip; Which month comes <b>right after September</b>?",
           "August", "October", "November", "December", "July"),
         "<b>(B) October.</b> The order is &hellip; September, <b>October</b>, November &hellip;"),

        (Q("Sara is 9 years old, Tom is 12, and Ravi is 7. Who is the <b>youngest</b>?",
           "Sara", "Tom", "Ravi", "They are all the same age", "We cannot tell"),
         "<b>(C) Ravi.</b> Line up the ages 7, 9, 12 &mdash; the smallest is 7, which is <b>Ravi</b>."),

        (Q("A clock shows exactly <b>3 o'clock</b>. What time will it be <b>2 hours</b> later?",
           "4:00", "5:00", "6:00", "2:00", "5:30"),
         "<b>(B) 5:00.</b> 3 o'clock + 2 hours = <b>5 o'clock</b> (5:00)."),
    ]))

    # ===================== 4-POINT THINKERS =====================
    A(H("\U0001F99C 4-Point Thinkers"))
    A(P("Now slow down and <em>think</em>. Each of these is worth <b>4 points</b> &mdash; they reward a "
        "careful plan, not a quick guess."))
    A(figure(fold_diagram(2, [(0.27, 0.30), (0.73, 0.30), (0.27, 0.70), (0.73, 0.70)]),
             "Thinker 2: fold twice, punch once — how many holes?"))
    A(figure(grid_fig(2, 2), "Thinker 5: count the shortest routes from Start to End (right or up only)."))

    A(practice("4-Point Thinkers", [
        (Q("A long rope is cut into <b>6</b> equal pieces. Each cut takes 2 minutes. How long does all the "
           "cutting take?",
           "6 minutes", "8 minutes", "10 minutes", "12 minutes", "5 minutes"),
         "<b>(C) 10 minutes.</b> 6 pieces need 6 &minus; 1 = 5 cuts. Time = 5 &times; 2 = <b>10</b> minutes "
         "(the trap answer 12 forgets that cuts are one fewer than pieces)."),

        (Q("A square paper is folded in half <b>twice</b>, then a single hole is punched. How many holes "
           "appear when you unfold it? (See the picture above.)",
           "2", "3", "4", "6", "8"),
         "<b>(C) 4.</b> Two folds make 2 &times; 2 = 4 layers; one punch through all 4 gives <b>4 holes</b>."),

        (Q("A large cube is built from <b>27</b> little cubes (it is 3 cubes long, 3 deep and 3 tall). How "
           "many little cubes are completely <b>hidden inside</b>, touching no outside face?",
           "0", "1", "3", "6", "9"),
         "<b>(B) 1.</b> Only the very middle cube is buried inside &mdash; every other cube touches a face. "
         "So <b>1</b> is hidden."),

        (Q("Two whole numbers multiply to give <b>24</b> and add to give <b>10</b>. What is the "
           "<b>difference</b> between the two numbers?",
           "2", "4", "6", "8", "10"),
         "<b>(A) 2.</b> The numbers are 4 and 6 (4 &times; 6 = 24, 4 + 6 = 10). Their difference is "
         "6 &minus; 4 = <b>2</b>."),

        (Q("On the grid shown above (2 cells wide, 2 cells tall), how many <b>shortest routes</b> go from "
           "Start to End, moving only right or up?",
           "3", "4", "6", "8", "9"),
         "<b>(C) 6.</b> You take 2 rights and 2 ups in some order; there are exactly <b>6</b> orders "
         "(equivalently, build the corner sums and the top-right corner is 6)."),

        (Q("A classroom has <b>5 rows</b> of <b>6 chairs</b>, but 4 of the chairs are broken. How many "
           "<b>good</b> chairs are there?",
           "24", "25", "26", "30", "34"),
         "<b>(C) 26.</b> All chairs: 5 &times; 6 = 30. Take away the 4 broken ones: 30 &minus; 4 = <b>26</b>."),

        (Q("Today is <b>Wednesday</b>. What day of the week will it be after exactly <b>10 days</b>?",
           "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
         "<b>(D) Saturday.</b> 7 days return to Wednesday; 10 &minus; 7 = 3 more days &rarr; Thu, Fri, "
         "<b>Sat</b>."),

        (Q("Leela thinks of a number. She adds <b>4</b>, then <b>doubles</b> the result, and gets <b>20</b>. "
           "What number did she think of?",
           "4", "5", "6", "7", "8"),
         "<b>(C) 6.</b> Undo backwards: 20 &divide; 2 = 10, then 10 &minus; 4 = <b>6</b>. (Check: 6 + 4 = 10, "
         "10 &times; 2 = 20. &#10003;)"),
    ]))

    # ===================== 5-POINT STARS =====================
    A(H("\U0001F99C 5-Point Stars"))
    A(P("The big ones! Each <b>5-point</b> star may need <em>two</em> tricks working together. Take your "
        "time, draw a picture, and check your answer makes sense."))
    A(figure(staircase_fig(4), "Star 1: a 4-step staircase of cubes — how many cubes in all?"))
    A(figure(painted_4cube(), "Star 3: a 4×4×4 painted cube — how many little cubes have NO painted face?"))
    A(figure(grid_fig(3, 2), "Star 5: count shortest routes across this 3-wide, 2-tall grid."))
    A(figure(hands_circle(5), "Star 6: 5 friends, every pair shakes hands once — how many handshakes?"))
    A(figure(balance_chain(), "Star 7: 1 melon = 3 apples, and 1 apple = 2 plums."))

    A(practice("5-Point Stars", [
        (Q("A staircase is built from cubes (see the picture): the bottom row has 4 cubes, then 3, then 2, "
           "then 1 on top. How many cubes are used altogether?",
           "8", "9", "10", "14", "16"),
         "<b>(C) 10.</b> Add the rows: 4 + 3 + 2 + 1 = <b>10</b> cubes."),

        (Q("A paper is folded in half <b>three</b> times, then a single hole is punched. How many holes "
           "appear when it is fully unfolded?",
           "3", "4", "6", "8", "16"),
         "<b>(D) 8.</b> Three folds make 2 &times; 2 &times; 2 = 8 layers; one punch gives <b>8 holes</b>."),

        (Q("A 4 &times; 4 &times; 4 cube (64 little cubes) is painted all over, then split into the little "
           "cubes. How many little cubes have <b>no painted face at all</b>?",
           "0", "4", "8", "16", "27"),
         "<b>(C) 8.</b> Peel off the painted outer shell; what's left inside is a 2 &times; 2 &times; 2 "
         "block = 2 &times; 2 &times; 2 = <b>8</b> unpainted cubes."),

        (Q("Two whole numbers multiply to <b>18</b> and add to <b>9</b>. What is the <b>smaller</b> of the "
           "two numbers?",
           "2", "3", "4", "6", "9"),
         "<b>(B) 3.</b> The numbers are 3 and 6 (3 &times; 6 = 18, 3 + 6 = 9). The smaller one is <b>3</b>."),

        (Q("On the grid shown above (3 cells wide, 2 cells tall), how many <b>shortest routes</b> go from "
           "Start to End, moving only right or up?",
           "6", "8", "10", "12", "15"),
         "<b>(C) 10.</b> Build the corner sums (1 along each edge, then add neighbours): the top-right "
         "corner comes to <b>10</b> routes."),

        (Q("Five friends meet, and every pair shakes hands exactly once (see the picture). How many "
           "handshakes happen in total?",
           "5", "8", "10", "15", "20"),
         "<b>(C) 10.</b> Count the lines joining every pair: there are <b>10</b> (each of the 5 people "
         "shakes 4 others, 5 &times; 4 = 20, but each handshake is shared by 2 people, so 20 &divide; 2 = 10)."),

        (Q("On a balance, <b>1 melon</b> weighs the same as <b>3 apples</b>, and <b>1 apple</b> weighs the "
           "same as <b>2 plums</b>. How many <b>plums</b> balance <b>1 melon</b>?",
           "3", "5", "6", "8", "9"),
         "<b>(C) 6.</b> Swap step by step: 1 melon = 3 apples, and each apple = 2 plums, so "
         "3 &times; 2 = <b>6 plums</b>."),

        (Q("The <b>1st</b> day of a month falls on a <b>Monday</b>. What day of the week is the <b>15th</b> "
           "of that month?",
           "Monday", "Tuesday", "Wednesday", "Sunday", "Saturday"),
         "<b>(A) Monday.</b> From the 1st to the 15th is 14 days, and 14 = 2 whole weeks, so the 15th is "
         "the same day &mdash; <b>Monday</b>."),
    ]))

    A(kiwi("&#127881; <b>How did you do?</b> If a few stars tripped you up, that's exactly how the Math "
           "Kangaroo is meant to feel &mdash; the 5-point problems are tough on purpose! Go back, re-read "
           "the ones you missed, and try the tricks from Chapter 21. Getting better at these clever "
           "puzzles is the whole adventure. &#129432;"))

    A(challenge(
        P("\U0001F31F <b>Kangaroo Star Challenge &mdash; The Painted Cube.</b> A big cube is built from "
          "little cubes, 3 along each edge (so <b>27</b> little cubes in all). Mr Kangaroo paints the "
          "<em>entire outside</em> orange, then breaks it back into the 27 little cubes and sorts them by "
          "how many faces are painted. Find: "
          "(a) how many little cubes have <b>3</b> painted faces, "
          "(b) how many have exactly <b>2</b> painted faces, "
          "(c) how many have exactly <b>1</b> painted face, "
          "(d) how many have <b>0</b> painted faces. "
          "Then check that your four numbers add up to <b>27</b>!") +
        figure(svg(
            # a 3x3x3 painted cube
            "".join(
                [f'<rect x="{40+c*40}" y="{40+r*40}" width="40" height="40" fill="{ORANGE}33" stroke="{INK}" stroke-width="1.5"/>'
                 for r in range(3) for c in range(3)] +
                [f'<polygon points="{40+c*40+k*16},{40-k*16} {80+c*40+k*16},{40-k*16} {80+c*40+(k+1)*16},{40-(k+1)*16} {40+c*40+(k+1)*16},{40-(k+1)*16}" '
                 f'fill="{ORANGE}44" stroke="{INK}" stroke-width="1.1"/>' for c in range(3) for k in range(3)] +
                [f'<polygon points="{160+k*16},{40+r*40-k*16} {160+(k+1)*16},{40+r*40-(k+1)*16} {160+(k+1)*16},{80+r*40-(k+1)*16} {160+k*16},{80+r*40-k*16}" '
                 f'fill="{ORANGE}22" stroke="{INK}" stroke-width="1.1"/>' for r in range(3) for k in range(3)]),
            260, 210), "A 3 × 3 × 3 cube, painted on every outside face.") +
        tryit("Think about <em>where</em> each little cube sits: corners, edges, face-centres, or buried inside.",
              "<b>(a) Corners = 8.</b> A cube has 8 corners, and each corner shows 3 painted faces. "
              "<b>(b) Edges = 12.</b> Each of the 12 edges has 1 middle cube (between two corners) showing "
              "2 faces. "
              "<b>(c) Face-centres = 6.</b> Each of the 6 flat faces has 1 centre cube showing just 1 face. "
              "<b>(d) Buried = 1.</b> The single cube in the very middle touches no outside face. "
              "Check the total: 8 + 12 + 6 + 1 = <b>27</b>. &#10003; Perfect &mdash; that's the whole cube "
              "accounted for! &#127881;")))

    A(kiwi("You just finished a full Kangaroo-style Challenge Set &mdash; warm-ups, thinkers <em>and</em> "
           "5-point stars &mdash; plus the famous painted-cube puzzle. Working all the way up the tiers and "
           "reasoning through that visual puzzle is exactly the kind of clever thinking these contests reward. "
           "Take a moment to notice how much further you can push now than when you started. &#129432;&#11088;"))

    chapter("Part 7 · 🦘 Kangaroo Corner", 22, "Kangaroo-style Challenge Set (3·4·5 points)",
            "Kangaroo · Brain Benders", "".join(b))
