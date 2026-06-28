#!/usr/bin/env python3
"""L3 Chapter 23 — Kangaroo Challenge Set (3·4·5 points)  (Kangaroo · Brain Benders).

A GRADED problem set in Kangaroo-STYLE (in the style of the Math Kangaroo Benjamin
tier, Grades 5-6), pitched above the L2 set. Three tiers via practice(): 3-Point
Warm-ups, 4-Point Thinkers, 5-Point Stars (8 problems each = 24 five-option MCQs).
These are original practice problems written in the style of the contest, NOT official
Math Kangaroo questions. Each reveal gives the correct LETTER plus a short worked
solution.
EVERY answer was enumerated/brute-forced in Python and each correct letter was
checked against its option list (see /tmp/setcheck.py, /tmp/optcheck.py).
"""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)
from math import comb


# ── 5-option MCQ layout ─────────────────────────────────────────────────
def opts(a, b, c, d, e):
    items = [("A", a), ("B", b), ("C", c), ("D", d), ("E", e)]
    inner = " &nbsp; ".join(f"<b>({L})</b>&nbsp;{v}" for L, v in items)
    return f'<div class="kopts" style="margin-top:6px;font-size:15px">{inner}</div>'


def Q(text, a, b, c, d, e):
    return text + opts(a, b, c, d, e)


# ── figures for the visual problems (reused / fresh for Benjamin) ────────
def cup_line(states):
    x0, gw, y = 26, 50, 40
    s = []
    for i, st in enumerate(states):
        x = x0 + i * gw
        up = (st == 'U')
        col = SKY if up else BERRY
        if up:
            s.append(f'<polygon points="{x+7},{y} {x+34},{y} {x+30},{y+38} {x+11},{y+38}" '
                     f'fill="{col}22" stroke="{col}" stroke-width="2.2"/>')
        else:
            s.append(f'<polygon points="{x+11},{y} {x+30},{y} {x+34},{y+38} {x+7},{y+38}" '
                     f'fill="{col}22" stroke="{col}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+20:.0f}" y="{y+54}" text-anchor="middle" font-size="12" '
                 f'font-weight="700" fill="{col}">{st}</text>')
    return svg("".join(s), x0 + len(states) * gw + 10, y + 66)


def painted_iso(n, label=None):
    cw = max(18, 88 // n); dp = max(10, cw * 0.6); ox, oy = 38, 28 + n * dp
    s = []
    for r in range(n):
        for c in range(n):
            s.append(f'<rect x="{ox+c*cw}" y="{oy+r*cw}" width="{cw}" height="{cw}" '
                     f'fill="{ORANGE}33" stroke="{INK}" stroke-width="1.1"/>')
    for c in range(n):
        for k in range(n):
            x = ox + c * cw + k * dp; y = oy - k * dp
            s.append(f'<polygon points="{x:.1f},{y:.1f} {x+cw:.1f},{y:.1f} '
                     f'{x+cw+dp:.1f},{y-dp:.1f} {x+dp:.1f},{y-dp:.1f}" '
                     f'fill="{ORANGE}44" stroke="{INK}" stroke-width="0.8"/>')
    fx = ox + n * cw
    for r in range(n):
        for k in range(n):
            x = fx + k * dp; y = oy + r * cw - k * dp
            s.append(f'<polygon points="{x:.1f},{y:.1f} {x+dp:.1f},{y-dp:.1f} '
                     f'{x+dp:.1f},{y+cw-dp:.1f} {x:.1f},{y+cw:.1f}" '
                     f'fill="{ORANGE}22" stroke="{INK}" stroke-width="0.8"/>')
    W = fx + n * dp + 28
    lab = label or f"a {n} &#215; {n} &#215; {n} cube, painted all over"
    s.append(f'<text x="{W/2:.0f}" y="{oy+n*cw+22}" text-anchor="middle" font-size="13" '
             f'fill="{INK}">{lab}</text>')
    return svg("".join(s), W, oy + n * cw + 34)


def grid_plain(W, H, block=None):
    cell, ox, oy = 44, 30, 22
    Wd, Hd = W * cell + 60, H * cell + 54
    s = []
    for r in range(H + 1):
        s.append(f'<line x1="{ox}" y1="{oy+r*cell}" x2="{ox+W*cell}" y2="{oy+r*cell}" '
                 f'stroke="{SKY}" stroke-width="1.4" opacity=".6"/>')
    for c in range(W + 1):
        s.append(f'<line x1="{ox+c*cell}" y1="{oy}" x2="{ox+c*cell}" y2="{oy+H*cell}" '
                 f'stroke="{SKY}" stroke-width="1.4" opacity=".6"/>')
    sx, sy = ox, oy + H * cell
    ex, ey = ox + W * cell, oy
    if block:
        bx, by = block
        cx = ox + bx * cell; cy = oy + (H - by) * cell
        s.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="#fff" stroke="{BERRY}" stroke-width="2.4"/>')
        s.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="16" '
                 f'font-weight="800" fill="{BERRY}">&#10006;</text>')
    s.append(f'<circle cx="{sx}" cy="{sy}" r="7" fill="{GRASS}"/>')
    s.append(f'<text x="{sx-2}" y="{sy+19}" text-anchor="middle" font-size="11" '
             f'font-weight="700" fill="{GRASS}">Start</text>')
    s.append(f'<circle cx="{ex}" cy="{ey}" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="{ex}" y="{ey-9}" text-anchor="middle" font-size="11" '
             f'font-weight="700" fill="{BERRY}">End</text>')
    return svg("".join(s), Wd, Hd)


def pigeons_fig(pigeons, holes, note):
    bw, x0, y = 54, 24, 64
    s = [f'<text x="{x0}" y="24" text-anchor="start" font-size="13" fill="{INK}">'
         f'{pigeons} into {holes}:</text>']
    for h in range(holes):
        x = x0 + h * (bw + 10)
        s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="42" rx="8" '
                 f'fill="{SKY}18" stroke="{SKY}" stroke-width="2"/>')
    placed = 0
    for h in range(holes):
        if placed >= pigeons:
            break
        x = x0 + h * (bw + 10) + bw / 2
        s.append(f'<text x="{x:.0f}" y="{y+28}" text-anchor="middle" font-size="18">&#9899;</text>')
        placed += 1
    if pigeons > placed:
        x = x0 + bw / 2
        s.append(f'<text x="{x:.0f}" y="{y-6}" text-anchor="middle" font-size="18">&#9899;</text>')
    s.append(f'<text x="{x0}" y="{y+62}" text-anchor="start" font-size="12" '
             f'font-weight="700" fill="{BERRY}">{note}</text>')
    return svg("".join(s), x0 + holes * (bw + 10) + 20, y + 76)


def detective(title, clues):
    s = [f'<rect x="10" y="10" width="320" height="{34+len(clues)*25}" rx="12" '
         f'fill="{PURPLE}0d" stroke="{PURPLE}" stroke-width="2"/>',
         f'<text x="24" y="33" text-anchor="start" font-size="14" font-weight="800" '
         f'fill="{PURPLE}">{title}</text>']
    for i, c in enumerate(clues):
        s.append(f'<text x="24" y="{56+i*25}" text-anchor="start" font-size="13" '
                 f'fill="{INK}">&#8226; {c}</text>')
    return svg("".join(s), 340, 44 + len(clues) * 25)


def handshake_party(n, deg):
    """n people in a circle, each joined to `deg` neighbours (a regular handshake graph)."""
    import math
    cx, cy, r = 115, 100, 74
    pts = [(cx + r * math.cos(math.radians(-90 + i * 360 / n)),
            cy + r * math.sin(math.radians(-90 + i * 360 / n))) for i in range(n)]
    s = []
    for i in range(n):
        for off in range(1, deg // 2 + 1):
            j = (i + off) % n
            s.append(f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" '
                     f'x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" stroke="{SKY}" '
                     f'stroke-width="1.5" opacity=".7"/>')
    for (x, y) in pts:
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="{ORANGE}"/>')
    s.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" '
             f'fill="{INK}">{n} people,<tspan x="{cx}" dy="15">{deg} each</tspan></text>')
    return svg("".join(s), 230, 200)


def repdigit_card(A):
    s = [f'<rect x="40" y="30" width="160" height="64" rx="12" fill="{GOLD}1f" '
         f'stroke="{GOLD}" stroke-width="2.4"/>',
         f'<text x="120" y="76" text-anchor="middle" font-size="34" font-weight="800" '
         f'fill="{ORANGE}" font-family="Georgia,serif">{A}{A}{A}</text>',
         f'<text x="120" y="110" text-anchor="middle" font-size="13" fill="{INK}">'
         f'a 3-digit number with all the same digit</text>']
    return svg("".join(s), 240, 124)


def board_seq(nums, op):
    x0, bw, y = 24, 46, 36
    s = [f'<text x="{x0}" y="22" text-anchor="start" font-size="13" fill="{INK}">On the board:</text>']
    for i, n in enumerate(nums):
        x = x0 + i * (bw + 7)
        s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="38" rx="9" '
                 f'fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{y+25:.0f}" text-anchor="middle" '
                 f'font-size="18" font-weight="800" fill="{GRASS}">{n}</text>')
    s.append(f'<text x="{x0}" y="{y+58}" text-anchor="start" font-size="13" '
             f'font-weight="700" fill="{BERRY}">{op}</text>')
    return svg("".join(s), x0 + len(nums) * (bw + 7) + 12, y + 72)


# ── the chapter ─────────────────────────────────────────────────────────
def build(chapter):
    b = []
    A = b.append

    A(big_q("You've gathered the nine tools &mdash; now it's <b>contest day</b>! &#129432; Here is a "
            "Kangaroo-<b>style</b> Challenge Set in the <b>Benjamin</b> spirit (Grades 5&ndash;6). Can "
            "you earn the 3-point, 4-point and 5-point problems, the way students do in the Math "
            "Kangaroo around the world?"))
    A(kiwi("Welcome to the arena &mdash; it's <b>Kiwi</b>, cheering you on! Quick rules, set up just like "
           "the real contest: every problem is <b>multiple choice</b> with five answers, <b>(A)</b> to "
           "<b>(E)</b>; pick the one best answer. <b>No calculator</b> &mdash; reach for the tricks from "
           "Chapter 22! Work each tier in order: <b>3-point</b> warm-ups build confidence, <b>4-point</b> "
           "thinkers make you pause, and <b>5-point</b> stars are real brain-benders. (These are our own "
           "practice problems written in the contest's style, not the official Kangaroo paper.) Try "
           "first, then open the answer to see the correct <b>letter</b> and how it's done. Ready&hellip; "
           "go! &#128640;"))
    A(kiwi("&#128161; <b>Kangaroo strategy:</b> if a problem looks scary, you don't always need the exact "
           "answer first &mdash; you can <em>knock out</em> options that are clearly too big or too small, "
           "then choose from what's left. And always re-read: many Benjamin traps catch students who "
           "answer too fast (especially the parity and painted-cube ones)!"))

    # ===================== 3-POINT WARM-UPS =====================
    A(H("\U0001F99C 3-Point Warm-ups"))
    A(P("Gentle starters to warm up your thinking. Each is worth <b>3 points</b>."))
    A(figure(cup_line(['U', 'U', 'U', 'U', 'U']), "Warm-up 1: five glasses, all up — flip exactly two each move."))
    A(figure(painted_iso(3), "Warm-up 5: a 3×3×3 painted cube."))

    A(practice("3-Point Warm-ups", [
        (Q("Five glasses stand on a table, all the right way <b>up</b>. Each move you must turn over "
           "<b>exactly two</b> of them. Can you ever make <b>all five</b> upside-down?",
           "Yes, in 3 moves", "Yes, in 5 moves", "No, it is impossible", "Yes, in 10 moves",
           "Only with luck"),
         "<b>(C) No, it is impossible.</b> The number of down glasses starts at 0 (even) and each move "
         "changes it by an even amount, so it stays even &mdash; but &ldquo;all 5 down&rdquo; is odd. "
         "Parity forbids it."),

        (Q("What is the <b>last digit</b> of 2&#185;&#8304; (that is, 2 to the power 10)?",
           "2", "4", "6", "8", "0"),
         "<b>(B) 4.</b> The last digits of powers of 2 loop 2, 4, 8, 6. Since 10 &divide; 4 = 2 remainder "
         "2, we want the 2nd in the loop &rarr; <b>4</b>. (Indeed 2&#185;&#8304; = 1024.)"),

        (Q("How many <b>diagonals</b> does a <b>pentagon</b> (a 5-sided shape) have?",
           "2", "3", "5", "8", "10"),
         "<b>(C) 5.</b> Diagonals = n(n&minus;3)&divide;2 = 5&times;2&divide;2 = <b>5</b>. (Each corner "
         "joins the 2 non-neighbouring corners.)"),

        (Q("A town is a grid <b>2 blocks wide and 3 blocks tall</b>. Going only <b>right</b> or <b>up</b>, "
           "how many shortest routes lead from the bottom-left to the top-right corner?",
           "5", "6", "8", "10", "12"),
         "<b>(D) 10.</b> A route is 2 rights and 3 ups in some order: &ldquo;5 choose 2&rdquo; = <b>10</b>."),

        (Q("A 3 &times; 3 &times; 3 cube is painted all over, then split into 27 little cubes. How many "
           "little cubes have <b>exactly two</b> painted faces?",
           "6", "8", "9", "12", "18"),
         "<b>(D) 12.</b> The two-face cubes sit on the edges: each of the 12 edges has 1 middle cube &rarr; "
         "<b>12</b>."),

        (Q("How many whole numbers from <b>1 to 20</b> are <b>not</b> multiples of 4?",
           "4", "5", "10", "15", "16"),
         "<b>(D) 15.</b> Multiples of 4 up to 20 are 4, 8, 12, 16, 20 &mdash; that's 5. So 20 &minus; 5 = "
         "<b>15</b> are not (counting by complement)."),

        (Q("A number is <b>increased by 3</b>, then the result is <b>doubled</b>, giving <b>16</b>. What "
           "was the original number?",
           "3", "4", "5", "6", "8"),
         "<b>(C) 5.</b> Work backwards: undo the doubling (16 &divide; 2 = 8), then undo the +3 "
         "(8 &minus; 3 = <b>5</b>). Check: 5 + 3 = 8, 8 &times; 2 = 16. &#10003;"),

        (Q("Socks of <b>4 colours</b> are jumbled in a drawer. Reaching in <em>in the dark</em>, how many "
           "socks must you take to be <b>certain</b> of a matching pair?",
           "2", "3", "4", "5", "6"),
         "<b>(D) 5.</b> Pigeonhole: 4 colours are 4 &lsquo;holes&rsquo;; 4 socks could be all different, "
         "but a 5th must repeat a colour &mdash; <b>5</b>."),
    ]))

    # ===================== 4-POINT THINKERS =====================
    A(H("\U0001F99C 4-Point Thinkers"))
    A(P("Now slow down and <em>think</em>. Each is worth <b>4 points</b> &mdash; they reward a careful "
        "plan, not a quick guess."))
    A(figure(board_seq([1, 2, 3, 4, 5, 6], "Move: erase a, b → write (a + b − 1). Repeat to one number."),
             "Thinker 1: the disappearing-numbers game — find what's invariant."))
    A(figure(painted_iso(4), "Thinker 3: a 4×4×4 painted cube — how many little cubes have NO paint?"))
    A(figure(grid_plain(4, 2), "Thinker 5: shortest right/up routes across a 4-wide, 2-tall grid."))

    A(practice("4-Point Thinkers", [
        (Q("The numbers <b>1, 2, 3, 4, 5, 6</b> are written on a board. Each move, erase two of them, "
           "<em>a</em> and <em>b</em>, and write <b><em>a</em> + <em>b</em> &minus; 1</b> in their place. "
           "After repeating until one number is left, what is that number?",
           "6", "11", "15", "16", "21"),
         "<b>(D) 16.</b> The <em>sum</em> on the board drops by exactly 1 each move (invariant!). Start sum "
         "= 21; with 5 moves it falls to 21 &minus; 5 = <b>16</b>."),

        (Q("What is the <b>last digit</b> of 3&#8313;&#8313; (3 to the power 99)?",
           "1", "3", "7", "9", "27"),
         "<b>(C) 7.</b> Powers of 3 end in 3, 9, 7, 1 (loop of 4). 99 &divide; 4 = 24 remainder 3 &rarr; "
         "the 3rd spot &rarr; <b>7</b>."),

        (Q("A 4 &times; 4 &times; 4 cube (64 little cubes) is painted all over, then split apart. How many "
           "little cubes have <b>no painted face at all</b>?",
           "0", "4", "8", "16", "27"),
         "<b>(C) 8.</b> Peel off the painted shell; what remains is a (4&minus;2)&sup3; = 2&times;2&times;2 "
         "block = <b>8</b> unpainted cubes."),

        (Q("How many whole numbers from <b>1 to 100</b> are divisible by <b>3 or 5</b>?",
           "33", "40", "47", "53", "60"),
         "<b>(C) 47.</b> Multiples of 3: 33. Of 5: 20. Of 15 (counted twice): 6. So 33 + 20 &minus; 6 = "
         "<b>47</b>."),

        (Q("A town is a grid <b>4 blocks wide and 2 blocks tall</b>. Moving only right or up, how many "
           "shortest routes go from corner to corner?",
           "6", "10", "12", "15", "20"),
         "<b>(D) 15.</b> A route is 4 rights and 2 ups in some order: &ldquo;6 choose 4&rdquo; = "
         "&ldquo;6 choose 2&rdquo; = <b>15</b>."),

        (Q("In a class of <b>25 students</b>, each has a birthday in one of the 12 months. The teacher "
           "says: &lsquo;Some month is shared by at least ___ students.&rsquo; What is the largest number "
           "that <em>must</em> be true?",
           "1", "2", "3", "4", "12"),
         "<b>(C) 3.</b> Pigeonhole: 25 students in 12 month-&lsquo;holes&rsquo;. Even spread is 2 each "
         "(24), so the 25th forces some month to <b>3</b>. (You can't guarantee 4.)"),

        (Q("The numbers <b>1, 2, 3, &hellip;, 10</b> are on a board. Each move, erase two, <em>a</em> and "
           "<em>b</em>, and write <b><em>a</em> + <em>b</em> &minus; 1</b>. What single number remains at "
           "the end?",
           "10", "45", "46", "55", "100"),
         "<b>(C) 46.</b> The sum drops by 1 per move (invariant). Start 1+&hellip;+10 = 55; there are 9 "
         "moves &rarr; 55 &minus; 9 = <b>46</b>."),

        (Q("How many <b>two-digit numbers</b> have digits that add up to exactly <b>9</b>?",
           "7", "8", "9", "10", "11"),
         "<b>(C) 9.</b> They are 18, 27, 36, 45, 54, 63, 72, 81, 90 &mdash; <b>9</b> numbers (the tens "
         "digit runs 1&hellip;9, and the units digit is whatever makes 9)."),
    ]))

    # ===================== 5-POINT STARS =====================
    A(H("\U0001F99C 5-Point Stars"))
    A(P("The big ones! Each <b>5-point</b> star may need <em>two</em> tricks working together. Take your "
        "time, draw a picture, and check your answer makes sense."))
    A(figure(painted_iso(5), "Star 1: a 5×5×5 painted cube — how many little cubes show exactly one face?"))
    A(figure(grid_plain(4, 4, block=(2, 2)),
             "Star 3: shortest right/up routes on a 4×4 grid, but the marked corner is closed."))
    A(figure(detective("Star 6 — who came 3rd?", [
        "Mira scored higher than Ravi", "Ravi higher than Tia",
        "Sam higher than Mira", "Ela scored the lowest"]),
             "Star 6: chain the clues into one order, then read off 3rd place."))
    A(figure(handshake_party(10, 3), "Star 7: 10 people, each shakes hands with exactly 3 others."))
    A(figure(repdigit_card("A"), "Star 8: a 3-digit number with one repeated digit, divisible by 7."))

    A(practice("5-Point Stars", [
        (Q("A 5 &times; 5 &times; 5 cube (125 little cubes) is painted on every outside face, then split "
           "apart. How many little cubes have <b>exactly one</b> painted face?",
           "27", "36", "48", "54", "96"),
         "<b>(D) 54.</b> One-face cubes sit at face centres: 6 faces &times; (5&minus;2)&sup2; = "
         "6 &times; 9 = <b>54</b>."),

        (Q("What is the <b>last digit</b> of 7&#8311;&#8311; (7 to the power 77)?",
           "1", "3", "7", "9", "49"),
         "<b>(C) 7.</b> Powers of 7 end in 7, 9, 3, 1 (loop of 4). 77 &divide; 4 = 19 remainder 1 &rarr; "
         "the 1st spot &rarr; <b>7</b>."),

        (Q("A town is a 4 &times; 4 grid of blocks. Going only right or up, how many shortest routes go "
           "from Start to End if the <b>centre corner is closed</b> (see the &#10006; in the picture)?",
           "8", "16", "34", "36", "70"),
         "<b>(C) 34.</b> All routes = &ldquo;8 choose 4&rdquo; = 70. Routes <em>through</em> the closed "
         "centre = (4 choose 2)&times;(4 choose 2) = 6&times;6 = 36. So 70 &minus; 36 = <b>34</b> avoid "
         "it."),

        (Q("How many whole numbers from <b>1 to 200</b> are divisible by <b>none</b> of 2, 3 and 5?",
           "27", "45", "53", "54", "80"),
         "<b>(D) 54.</b> By complement: divisible by 2, 3 or 5 = 100 + 66 + 40 &minus; 33 &minus; 20 "
         "&minus; 13 + 6 = 146. So 200 &minus; 146 = <b>54</b>."),

        (Q("A cookie vanished. Four friends speak, and <b>exactly one</b> of them is telling the truth. "
           "Tom: &lsquo;Sam took it.&rsquo; Sam: &lsquo;I did not.&rsquo; Pia: &lsquo;I did not.&rsquo; "
           "Ron: &lsquo;Tom took it.&rsquo; Who took the cookie?",
           "Tom", "Sam", "Pia", "Ron", "Cannot tell"),
         "<b>(C) Pia.</b> Test each thief and count true statements; only &lsquo;Pia took it&rsquo; gives "
         "exactly one true (Sam's &lsquo;I did not&rsquo;). Tom&rarr;3 true, Sam&rarr;2, Ron&rarr;2."),

        (Q("Five children scored differently on a test. Mira scored higher than Ravi, Ravi higher than "
           "Tia, and Sam higher than Mira; Ela scored the lowest. Who finished <b>third</b>?",
           "Sam", "Mira", "Ravi", "Tia", "Ela"),
         "<b>(C) Ravi.</b> Chain the clues: Sam &gt; Mira &gt; Ravi &gt; Tia, with Ela last. The order is "
         "Sam, Mira, <b>Ravi</b>, Tia, Ela &mdash; third is <b>Ravi</b>."),

        (Q("At a party, <b>10 people</b> are seated in a circle and each person shakes hands with exactly "
           "<b>3</b> others. How many handshakes happen in total?",
           "10", "13", "15", "20", "30"),
         "<b>(C) 15.</b> Count hand-ends: 10 people &times; 3 = 30, but each handshake is shared by 2 "
         "people, so 30 &divide; 2 = <b>15</b> handshakes."),

        (Q("A 3-digit number is written with the <b>same digit three times</b> (like 222 or 888). For "
           "which digit <b>A</b> is the number <b>AAA</b> divisible by <b>7</b>?",
           "1", "3", "6", "7", "9"),
         "<b>(D) 7.</b> AAA = 111 &times; A, and 111 = 3 &times; 37 shares no factor of 7, so 7 must divide "
         "A &mdash; only A = <b>7</b> works. (777 &divide; 7 = 111. &#10003;)"),
    ]))

    A(kiwi("&#127881; <b>How did you do?</b> If a few stars tripped you up, that's exactly how the "
           "Benjamin level is meant to feel &mdash; the 5-point problems are tough on purpose! Go back, "
           "re-read the ones you missed, and try the matching trick from Chapter 22 again. Working out a "
           "puzzle you were stuck on is the part that actually builds the skill. &#129432;"))

    A(challenge(
        P("\U0001F31F <b>Kangaroo Star Challenge &mdash; The Grand Combo.</b> Three tools, one final "
          "number. "
          "(a) A <b>4 &times; 4 &times; 4</b> cube is painted all over &mdash; how many little cubes have "
          "<b>3</b> painted faces? "
          "(b) The <em>same</em> cube &mdash; how many little cubes have <b>0</b> painted faces? "
          "(c) What is the <b>last digit</b> of 2&#8308;&#8304; (2 to the power 40)? "
          "Now compute <em>(a)</em> + <em>(b)</em> + <em>(c)</em>. What is the grand total?") +
        figure(painted_iso(4, "the 4 × 4 × 4 cube for parts (a) and (b)"),
               "A 4 × 4 × 4 painted cube — sort the little cubes by how many faces are painted.") +
        tryit("Solve each part with its tool, then add the three numbers.",
              "(a) <b>3-face cubes are the corners &mdash; always 8.</b> "
              "(b) <b>0-face (buried) cubes = (4&minus;2)&sup3; = 2&sup3; = 8.</b> "
              "(c) Last digit of 2&#8308;&#8304;: powers of 2 loop 2, 4, 8, 6; 40 &divide; 4 = 10 "
              "remainder 0 &rarr; the 4th spot &rarr; <b>6</b>. "
              "Grand total: 8 + 8 + 6 = <b>22</b>. &#127881;")))

    A(kiwi("You just finished a full Kangaroo-<b>style</b> Challenge Set &mdash; warm-ups, thinkers "
           "<em>and</em> 5-point stars &mdash; plus the Grand Combo. That's exactly the clever, visual, "
           "insight-over-calculation thinking the Math Kangaroo rewards around the world. Notice what you "
           "did here: you picked the right tool for each problem instead of just calculating. That habit "
           "&mdash; choosing a method before you start &mdash; is what carries you through the toughest "
           "puzzles. &#129432;&#11088;"))

    chapter("Part 8 · 🦘 Kangaroo Corner", 23, "Kangaroo Challenge Set (3·4·5 points)",
            "Kangaroo · Brain Benders", "".join(b))
