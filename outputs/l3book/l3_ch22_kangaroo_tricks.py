#!/usr/bin/env python3
"""L3 Chapter 22 — Kangaroo Thinking Tricks  (Kangaroo · Brain Benders).

Teaches Kangaroo-STYLE thinking strategies (in the style of the Math Kangaroo Benjamin
tier, Grades 5-6) Socratically, pitched well above the L2 set: PARITY arguments,
INVARIANTS, the PIGEONHOLE principle, working BACKWARDS, clever COUNTING BY COMPLEMENT,
3D / painted-cube visualisation, GRID PATHS via C(m+n,n) (incl. an obstacle), LOGICAL
ELIMINATION with clues, and DIGIT / divisibility / last-digit tricks. These are
practice problems written in the style of the contest, not official Math Kangaroo
questions.
EVERY numeric answer was brute-forced/enumerated in Python before writing (see
/tmp/verify_l3kangaroo.py etc.).
"""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)
from math import comb


# ── custom figures, built just for this chapter ─────────────────────────
def cup_row(states, flip_pairs=None):
    """A row of glasses. states: list of 'U'(up) / 'D'(down). Optionally show a flip bracket."""
    x0, gw, y = 26, 56, 66   # y = glass top, lowered to leave a clear band for title + flip arc
    s = [f'<text x="{x0}" y="16" text-anchor="start" font-size="13" fill="{INK}">'
         f'Glasses in a row (U = up, D = down):</text>']
    for i, st in enumerate(states):
        x = x0 + i * gw
        up = (st == 'U')
        col = SKY if up else BERRY
        # a simple glass: trapezoid; flip vertically if 'down'
        if up:
            s.append(f'<polygon points="{x+8},{y} {x+38},{y} {x+33},{y+42} {x+13},{y+42}" '
                     f'fill="{col}22" stroke="{col}" stroke-width="2.2"/>')
        else:
            s.append(f'<polygon points="{x+13},{y} {x+33},{y} {x+38},{y+42} {x+8},{y+42}" '
                     f'fill="{col}22" stroke="{col}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+23:.0f}" y="{y+60}" text-anchor="middle" font-size="13" '
                 f'font-weight="700" fill="{col}">{st}</text>')
    if flip_pairs:
        for (i, j) in flip_pairs:
            xa = x0 + i * gw + 23; xb = x0 + j * gw + 23
            s.append(f'<path d="M{xa},{y-8} q {(xb-xa)/2},-16 {xb-xa},0" fill="none" '
                     f'stroke="{ORANGE}" stroke-width="2.4"/>')
            s.append(f'<text x="{(xa+xb)/2:.0f}" y="42" text-anchor="middle" '
                     f'font-size="12" fill="{ORANGE}">flip these 2</text>')
    return svg("".join(s), x0 + len(states) * gw + 12, y + 76)


def board_numbers(nums, op_label):
    """A 'board' of numbers with an operation note (for invariant games)."""
    x0, bw, y = 24, 50, 40
    s = [f'<text x="{x0}" y="24" text-anchor="start" font-size="13" fill="{INK}">'
         f'Numbers on the board:</text>']
    for i, n in enumerate(nums):
        x = x0 + i * (bw + 8)
        s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="40" rx="9" '
                 f'fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{y+27:.0f}" text-anchor="middle" '
                 f'font-size="19" font-weight="800" fill="{GRASS}">{n}</text>')
    s.append(f'<text x="{x0}" y="{y+62}" text-anchor="start" font-size="13" '
             f'font-weight="700" fill="{BERRY}">{op_label}</text>')
    return svg("".join(s), x0 + len(nums) * (bw + 8) + 12, y + 76)


def pigeon_holes(pigeons, holes):
    """Draw `pigeons` birds dropping into `holes` boxes (one overflow shown)."""
    bw, x0, y = 60, 24, 70
    s = [f'<text x="{x0}" y="26" text-anchor="start" font-size="13" fill="{INK}">'
         f'{pigeons} pigeons, only {holes} holes:</text>']
    # holes
    for h in range(holes):
        x = x0 + h * (bw + 12)
        s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="46" rx="8" '
                 f'fill="{SKY}18" stroke="{SKY}" stroke-width="2"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{y+62}" text-anchor="middle" '
                 f'font-size="11" fill="{SKY}">hole {h+1}</text>')
    # place pigeons: one per hole, then extras pile into hole 1
    placed = 0
    for h in range(holes):
        if placed >= pigeons:
            break
        x = x0 + h * (bw + 12) + bw / 2
        s.append(f'<text x="{x:.0f}" y="{y+30}" text-anchor="middle" font-size="20">&#128038;</text>')
        placed += 1
    extra = pigeons - placed
    if extra > 0:
        x = x0 + bw / 2
        s.append(f'<text x="{x:.0f}" y="{y-8}" text-anchor="middle" font-size="20">&#128038;</text>')
        s.append(f'<text x="{x0 + holes*(bw+12)}" y="{y+30}" text-anchor="start" '
                 f'font-size="12" font-weight="700" fill="{BERRY}">&#8592; this hole must get 2!</text>')
    return svg("".join(s), x0 + holes * (bw + 12) + 150, y + 76)


def back_chain(steps_list, result):
    """A left->right chain '?' -> step -> step -> result, for working backwards."""
    boxes = [("?", BERRY)] + [(t, SKY if k % 2 == 0 else GRASS) for k, t in enumerate(steps_list)] + [(str(result), ORANGE)]
    x = 14
    s = []
    for i, (t, c) in enumerate(boxes):
        bw = 74
        s.append(f'<rect x="{x}" y="34" width="{bw}" height="44" rx="10" '
                 f'fill="{c}1f" stroke="{c}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{62}" text-anchor="middle" '
                 f'font-size="17" font-weight="800" fill="{c}">{t}</text>')
        if i < len(boxes) - 1:
            ax = x + bw
            s.append(f'<line x1="{ax}" y1="56" x2="{ax+22}" y2="56" stroke="{INK}" stroke-width="2.4"/>')
            s.append(f'<polygon points="{ax+22},56 {ax+14},51 {ax+14},61" fill="{INK}"/>')
        x += bw + 22
    s.append(f'<text x="{x/2:.0f}" y="22" text-anchor="middle" font-size="13" fill="{INK}">'
             f'Forwards &#8594;</text>')
    s.append(f'<text x="{x/2:.0f}" y="96" text-anchor="middle" font-size="13" '
             f'font-weight="700" fill="{BERRY}">&#8592; To find ?, walk back and UNDO every step</text>')
    return svg("".join(s), x + 8, 110)


def venn_complement(total, inside, in_label, out_label):
    """A box (total) with a circle (inside) — to picture counting by complement."""
    s = [f'<rect x="14" y="14" width="280" height="150" fill="{GRASS}0c" '
         f'stroke="{GRASS}" stroke-width="2"/>',
         f'<text x="24" y="34" text-anchor="start" font-size="13" fill="{GRASS}" '
         f'font-weight="700">all {total}</text>',
         f'<circle cx="120" cy="92" r="58" fill="{BERRY}1f" stroke="{BERRY}" stroke-width="2.2"/>',
         f'<text x="120" y="84" text-anchor="middle" font-size="13" fill="{BERRY}" '
         f'font-weight="700">{in_label}</text>',
         f'<text x="120" y="104" text-anchor="middle" font-size="18" fill="{BERRY}" '
         f'font-weight="800">{inside}</text>',
         f'<text x="246" y="120" text-anchor="middle" font-size="13" fill="{GRASS}" '
         f'font-weight="700">{out_label}</text>',
         f'<text x="246" y="142" text-anchor="middle" font-size="18" fill="{GRASS}" '
         f'font-weight="800">{total-inside}</text>']
    return svg("".join(s), 308, 178)


def painted_cube(n, label=None):
    """An n×n×n painted cube drawn isometrically (front shaded), every unit cube outlined."""
    cw = max(18, 90 // n); dp = max(10, cw * 0.6); ox, oy = 40, 30 + n * dp
    s = []
    # front face n×n
    for r in range(n):
        for c in range(n):
            s.append(f'<rect x="{ox+c*cw}" y="{oy+r*cw}" width="{cw}" height="{cw}" '
                     f'fill="{ORANGE}33" stroke="{INK}" stroke-width="1.1"/>')
    # top face
    for c in range(n):
        for k in range(n):
            x = ox + c * cw + k * dp
            y = oy - k * dp
            s.append(f'<polygon points="{x:.1f},{y:.1f} {x+cw:.1f},{y:.1f} '
                     f'{x+cw+dp:.1f},{y-dp:.1f} {x+dp:.1f},{y-dp:.1f}" '
                     f'fill="{ORANGE}44" stroke="{INK}" stroke-width="0.8"/>')
    # right face
    fx = ox + n * cw
    for r in range(n):
        for k in range(n):
            x = fx + k * dp
            y = oy + r * cw - k * dp
            s.append(f'<polygon points="{x:.1f},{y:.1f} {x+dp:.1f},{y-dp:.1f} '
                     f'{x+dp:.1f},{y+cw-dp:.1f} {x:.1f},{y+cw:.1f}" '
                     f'fill="{ORANGE}22" stroke="{INK}" stroke-width="0.8"/>')
    W = fx + n * dp + 30
    lab = label or f"a {n} &#215; {n} &#215; {n} cube, painted on every outside face"
    s.append(f'<text x="{W/2:.0f}" y="{oy+n*cw+24}" text-anchor="middle" font-size="13" '
             f'fill="{INK}">{lab}</text>')
    return svg("".join(s), W, oy + n * cw + 36)


def grid_obstacle(W, H, block=None, sample=True):
    """A W×H lattice (corner-to-corner, right/up). Optional blocked node (bx,by) marked X."""
    cell, ox, oy = 46, 32, 24
    Wd, Hd = W * cell + 64, H * cell + 56
    s = []
    for r in range(H + 1):
        s.append(f'<line x1="{ox}" y1="{oy+r*cell}" x2="{ox+W*cell}" y2="{oy+r*cell}" '
                 f'stroke="{SKY}" stroke-width="1.4" opacity=".55"/>')
    for c in range(W + 1):
        s.append(f'<line x1="{ox+c*cell}" y1="{oy}" x2="{ox+c*cell}" y2="{oy+H*cell}" '
                 f'stroke="{SKY}" stroke-width="1.4" opacity=".55"/>')
    sx, sy = ox, oy + H * cell
    ex, ey = ox + W * cell, oy
    if sample and not block:
        path = [(sx, sy)]
        for c in range(W):
            path.append((ox + (c + 1) * cell, sy))
        for r in range(H):
            path.append((ex, sy - (r + 1) * cell))
        pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in path)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{ORANGE}" stroke-width="4" '
                 f'stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>')
    if block:
        bx, by = block
        cx = ox + bx * cell
        cy = oy + (H - by) * cell
        s.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="#fff" stroke="{BERRY}" stroke-width="2.6"/>')
        s.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="18" '
                 f'font-weight="800" fill="{BERRY}">&#10006;</text>')
        s.append(f'<text x="{cx}" y="{cy-18}" text-anchor="middle" font-size="11" '
                 f'fill="{BERRY}">road closed</text>')
    s.append(f'<circle cx="{sx}" cy="{sy}" r="7" fill="{GRASS}"/>')
    s.append(f'<text x="{sx-2}" y="{sy+20}" text-anchor="middle" font-size="12" '
             f'font-weight="700" fill="{GRASS}">Start</text>')
    s.append(f'<circle cx="{ex}" cy="{ey}" r="7" fill="{BERRY}"/>')
    s.append(f'<text x="{ex}" y="{ey-10}" text-anchor="middle" font-size="12" '
             f'font-weight="700" fill="{BERRY}">End</text>')
    return svg("".join(s), Wd, Hd)


def path_sums(W, H):
    """The 'write the number on each corner' method: Pascal-style additions on a W×H lattice."""
    cell, ox, oy = 50, 40, 24
    # ways to reach (i,j) = C(i+j, i)
    s = []
    for r in range(H + 1):
        s.append(f'<line x1="{ox}" y1="{oy+r*cell}" x2="{ox+W*cell}" y2="{oy+r*cell}" '
                 f'stroke="{SKY}" stroke-width="1.2" opacity=".4"/>')
    for c in range(W + 1):
        s.append(f'<line x1="{ox+c*cell}" y1="{oy}" x2="{ox+c*cell}" y2="{oy+H*cell}" '
                 f'stroke="{SKY}" stroke-width="1.2" opacity=".4"/>')
    for i in range(W + 1):
        for j in range(H + 1):
            ways = comb(i + j, i)
            cx = ox + i * cell
            cy = oy + (H - j) * cell
            top = (i == W and j == H)
            col = BERRY if top else INK
            s.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="#fff" '
                     f'stroke="{col}" stroke-width="{2.4 if top else 1.4}"/>')
            s.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" '
                     f'font-weight="{800 if top else 700}" fill="{col}">{ways}</text>')
    s.append(f'<text x="{ox-10}" y="{oy+H*cell+6}" text-anchor="end" font-size="12" '
             f'fill="{GRASS}">Start=1</text>')
    return svg("".join(s), ox + W * cell + 30, oy + H * cell + 24)


def clue_list(title, clues):
    """A tidy 'detective board' of clues."""
    s = [f'<rect x="10" y="10" width="320" height="{34+len(clues)*26}" rx="12" '
         f'fill="{PURPLE}0d" stroke="{PURPLE}" stroke-width="2"/>',
         f'<text x="24" y="34" text-anchor="start" font-size="14" font-weight="800" '
         f'fill="{PURPLE}">{title}</text>']
    for i, c in enumerate(clues):
        s.append(f'<text x="24" y="{58+i*26}" text-anchor="start" font-size="13" '
                 f'fill="{INK}">&#8226; {c}</text>')
    return svg("".join(s), 340, 44 + len(clues) * 26)


def last_digit_wheel(base, cycle):
    """A wheel showing the repeating last-digit cycle of powers of `base`."""
    import math
    cx, cy, r, n = 110, 100, 66, len(cycle)
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r+18}" fill="{SKY}0c" stroke="{SKY}" stroke-width="1.6"/>']
    for i, d in enumerate(cycle):
        a = math.radians(-90 + i * 360 / n)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="17" fill="#fff" stroke="{ORANGE}" stroke-width="2.2"/>')
        s.append(f'<text x="{x:.0f}" y="{y+6:.0f}" text-anchor="middle" font-size="16" '
                 f'font-weight="800" fill="{ORANGE}">{d}</text>')
        # power label
        x2 = cx + (r + 30) * math.cos(a)
        y2 = cy + (r + 30) * math.sin(a)
        s.append(f'<text x="{x2:.0f}" y="{y2+4:.0f}" text-anchor="middle" font-size="11" '
                 f'fill="{INK}">{base}^{i+1}</text>')
    s.append(f'<text x="{cx}" y="{cy+1}" text-anchor="middle" font-size="13" '
             f'font-weight="800" fill="{INK}">last digit</text>')
    s.append(f'<text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="13" '
             f'font-weight="800" fill="{INK}">cycles!</text>')
    return svg("".join(s), 220, 200)


# ── the chapter ─────────────────────────────────────────────────────────
def build(chapter):
    b = []
    A = b.append

    A(big_q("Here is a puzzle that looks impossible. <b>Five glasses</b> stand on a table, all the right "
            "way <b>up</b>. Each move, you must turn over <em>exactly two</em> of them. Can you ever get "
            "<b>all five upside-down</b>? Try it&hellip; you'll fail every time. But a champion doesn't just "
            "try harder &mdash; they <em>prove</em> it's impossible in one line. By the end of this chapter "
            "you'll see exactly why &mdash; and you'll think like a Kangaroo. &#129432;"))
    A(kiwi("Hello again, explorer &mdash; it's <b>Kiwi</b>! You've climbed a long way since the Level 2 "
           "Kangaroo Corner. That was pitched at the younger <b>&Eacute;colier</b> stage (Grades "
           "3&ndash;4). Now we step up to <b>Benjamin</b>-style thinking &mdash; the kind of reasoning "
           "the Math Kangaroo contest sets for <b>Grades 5&ndash;6</b>, taken by students across many "
           "countries. We'll keep that friendly format: every problem is <b>multiple choice with five "
           "answers</b>, (A) to (E), grouped into <b>3-point</b> warm-ups, <b>4-point</b> thinkers and "
           "<b>5-point</b> stars, and no calculators. But the <em>thinking</em> goes deeper. These nine "
           "strategies are the real tools that crack these puzzles. Let's collect them. &#128640;"))

    # ===================== TRICK 1 . PARITY =====================
    A(H("Trick 1 \U0001F99C — Parity: the odd/even superpower"))
    A(P("<b>Parity</b> just means whether a number is <b>odd</b> or <b>even</b>. The Kangaroo secret is "
        "this: in many puzzles, <em>some quantity can only change in a way that keeps its parity the "
        "same</em>. If the start and the goal have <b>different</b> parities, the goal is "
        "<b>impossible</b> &mdash; no matter how hard you try!"))
    A(P("Back to our five glasses. Count how many are <b>upside-down</b>. At the start, that count is "
        "<b>0</b> (even). Each move flips <em>exactly two</em> glasses, so the down-count changes by "
        "&minus;2, 0, or +2 &mdash; it always stays <b>even</b>. But &ldquo;all five down&rdquo; needs the "
        "down-count to be <b>5</b>, which is <b>odd</b>. Even can never become odd by adding 2s. "
        "<b>Impossible!</b>"))
    A(figure(cup_row(['U', 'U', 'U', 'U', 'U'], flip_pairs=[(1, 3)]),
             "Start: 0 glasses down (even). Flipping 2 keeps the down-count even — 5 (odd) is unreachable."))
    A(example("why 5 glasses can never all go down (flipping 2 at a time)", steps([
        "Track one thing: <b>how many glasses are upside-down</b>. Start = <b>0</b>, which is even.",
        "Every legal move turns over exactly 2 glasses, changing the down-count by an <b>even</b> amount.",
        "An even number plus or minus even numbers is <em>always</em> even &mdash; the parity is "
        "<b>locked</b>.",
        "The target &ldquo;all 5 down&rdquo; needs down-count = <b>5</b> (odd). Locked-even can never reach "
        "odd. So it is <b>impossible</b>. &#10003;",
    ]) + P("With an <b>even</b> number of glasses (say 6), the goal <em>is</em> reachable &mdash; because "
           "now 6 is even, matching the locked parity.")))
    A(kiwi("Parity also cracks the classic &ldquo;put + and &minus; signs in front of "
           "1, 2, 3, &hellip;, 10 to make 0&rdquo; puzzle. The total 1+2+&hellip;+10 = <b>55</b> is "
           "<b>odd</b>. Flipping any &lsquo;+&rsquo; to a &lsquo;&minus;&rsquo; changes the sum by an "
           "<em>even</em> amount, so every result stays <b>odd</b> &mdash; and 0 is even. Impossible! "
           "(With 1&hellip;7 the total is 28, even, so <em>there</em> it can be done.)"))
    A(tryit("Seven lamps are all OFF. Each move you must switch <em>exactly two</em> of them. Can you ever "
            "get all seven ON? Explain in one line.",
            "<b>No.</b> The number of ON lamps starts at 0 (even) and each move changes it by an even "
            "amount, so it stays even &mdash; but &ldquo;all 7 on&rdquo; is odd. Parity forbids it."))

    # ===================== TRICK 2 . INVARIANTS =====================
    A(H("Trick 2 \U0001F99C — Invariants: find what never changes"))
    A(P("Parity is really one example of a bigger idea: an <b>invariant</b> &mdash; some quantity that "
        "<em>stays the same</em> (or changes in a totally predictable way) no matter what moves you make. "
        "Spot the invariant and a wild-looking puzzle becomes easy."))
    A(P("Here's a number game. The numbers <b>1, 2, 3, &hellip;, 10</b> are written on a board. Each move, "
        "you <b>rub out two</b> of them, say <em>a</em> and <em>b</em>, and write the single number "
        "<b><em>a</em> + <em>b</em> &minus; 1</b> instead. You repeat until just <b>one</b> number is "
        "left. What is it?"))
    A(figure(board_numbers([1, 2, 3, 4, 5, '…', 10],
                           "Move: erase a, b → write (a + b − 1).  What is the final number?"),
             "Ten numbers; each move removes two and writes (a+b−1), shrinking the count by 1."))
    A(example("the disappearing-numbers game", steps([
        "Don't simulate &mdash; hunt for what's <b>invariant</b>. Watch the <b>sum of all numbers</b> on the "
        "board.",
        "When you replace <em>a, b</em> with <em>a+b&minus;1</em>, the sum changes from (&hellip;+a+b) to "
        "(&hellip;+a+b&minus;1) &mdash; it goes <b>down by exactly 1</b> every move.",
        "Start sum = 1+2+&hellip;+10 = <b>55</b>. You make moves until one number remains: that's "
        "10 &minus; 1 = <b>9</b> moves, each dropping the sum by 1.",
        "Final number = 55 &minus; 9 = <b>46</b>. The order you pick the numbers <em>never matters</em>. "
        "&#10003;",
    ])))
    A(kiwi("The magic of an invariant: you get the answer <b>without doing the steps</b>. You found a "
           "quantity (the sum) that obeys a simple rule (drops by 1 each move), so you could leap straight "
           "to the end. Champions always ask: <em>&ldquo;What stays the same here?&rdquo;</em>"))
    A(tryit("Same game, but on the board are <b>1, 2, 3, 4, 5, 6</b>, and each move you write "
            "<em>a + b &minus; 1</em>. What single number is left at the end?",
            "Sum starts at 21; there are 6 &minus; 1 = 5 moves, each dropping the sum by 1. "
            "Final = 21 &minus; 5 = <b>16</b>."))

    # ===================== TRICK 3 . PIGEONHOLE =====================
    A(H("Trick 3 \U0001F99C — The Pigeonhole Principle"))
    A(P("Possibly the most beautiful idea in this whole chapter, and it sounds almost silly: <b>if you put "
        "more pigeons than holes, some hole must hold at least two pigeons.</b> Put 5 pigeons into 4 "
        "holes &mdash; one hole is guaranteed to get 2 or more. You can't avoid it!"))
    A(figure(pigeon_holes(5, 4), "5 pigeons, 4 holes — at least one hole must hold two."))
    A(P("The power is choosing the right &ldquo;pigeons&rdquo; and &ldquo;holes&rdquo;. Socks in a drawer "
        "are a favourite. If a drawer has socks of <b>3 colours</b>, how many must you grab <em>in the "
        "dark</em> to be <b>certain</b> of a matching pair?"))
    A(example("guaranteeing a matching pair of socks (3 colours)", steps([
        "Let the <b>holes</b> be the 3 colours. Each sock you pull is a <b>pigeon</b> dropped into its "
        "colour-hole.",
        "With 3 socks you might be unlucky: one of each colour, no pair yet.",
        "Pull <b>one more</b> &mdash; the 4th sock <em>must</em> match a colour you already have (only 3 "
        "colours exist). Pigeonhole!",
        "So <b>4</b> socks guarantee a pair. The rule: <em>(number of holes) + 1</em>. &#10003;",
    ])))
    A(kiwi("&#128161; Always ask <b>worst case</b>: imagine an enemy handing you the <em>unluckiest</em> "
           "socks possible. Pigeonhole says even the enemy must eventually give you a repeat. A sharper "
           "version: <b>if you put more than 2&times;(holes) pigeons in, some hole gets at least 3</b>, and "
           "so on."))
    A(P("A number version: choose any <b>5</b> numbers from <b>1, 2, 3, 4, 5, 6, 7, 8</b>. Must two of "
        "them add up to <b>9</b>? Pair the numbers by what makes 9: {1,8}, {2,7}, {3,6}, {4,5} &mdash; "
        "that's <b>4 pairs</b> (the holes). Picking 5 numbers means two land in the same pair &mdash; and "
        "those two sum to 9. <b>Yes, guaranteed.</b>"))
    A(tryit("A box has red, green, blue and yellow balls all mixed up. Reaching in without looking, how "
            "many balls must you take to be <b>sure</b> of two the same colour?",
            "4 colours = 4 holes, so 4 + 1 = <b>5 balls</b> guarantee a matching pair."))

    # ===================== TRICK 4 . WORKING BACKWARDS =====================
    A(H("Trick 4 \U0001F99C — Working backwards (undo the whole story)"))
    A(P("Some problems tell a story <em>forwards</em> and ask for the <b>start</b>. The trick is to begin "
        "at the <b>end</b> and <b>undo</b> each step in reverse: + becomes &minus;, &times; becomes "
        "&divide;, &lsquo;half of&rsquo; becomes &lsquo;double&rsquo;. Benjamin loves multi-step ones."))
    A(figure(back_chain(["&#215; 3", "+ 7", "&#247; 2", "&#8722; 4"], 10),
             "A four-step machine ends at 10. Walk back and undo each step to find the start."))
    A(example("a number is ×3, then +7, then ÷2, then −4, and the result is 10", steps([
        "Start at the <b>end</b>, 10, and reverse the <em>last</em> step first. Last was &minus;4, so undo "
        "with +4: 10 + 4 = <b>14</b>.",
        "Before that was &divide;2; undo with &times;2: 14 &times; 2 = <b>28</b>.",
        "Before that was +7; undo with &minus;7: 28 &minus; 7 = <b>21</b>.",
        "Before that was &times;3; undo with &divide;3: 21 &divide; 3 = <b>7</b>.",
        "The secret start was <b>7</b>. Check forwards: 7&times;3=21, +7=28, &divide;2=14, &minus;4=10. "
        "&#10003;",
    ])))
    A(kiwi("Working backwards shines in &ldquo;giving away half&rdquo; puzzles too. <em>I had some "
           "marbles. I gave away half plus one to Ami, then half of what was left plus one to Bo, and "
           "ended with 3.</em> Reverse it: before Bo, (3+1)&times;2 = 8; before Ami, (8+1)&times;2 = "
           "<b>18</b>. I started with 18 marbles!"))
    A(tryit("Mira thinks of a number, <b>doubles</b> it, then <b>adds 3</b>, and the result is <b>16</b>. "
            "Wait &mdash; can her number be a whole number? If yes, what is it?",
            "Undo: 16 &minus; 3 = 13, then 13 &divide; 2 = 6.5. That's <b>not a whole number</b>, so if she "
            "meant a whole number she made a slip. (If instead the result were 17: 17&minus;3=14, "
            "14&divide;2 = <b>7</b>.) Working backwards even catches impossible stories!"))

    # ===================== TRICK 5 . COUNTING BY COMPLEMENT =====================
    A(H("Trick 5 \U0001F99C — Clever counting: count the opposite"))
    A(P("When something is hard to count directly, count the <b>opposite</b> (the &ldquo;complement&rdquo;) "
        "and <b>subtract from the total</b>. It's often far easier &mdash; this is one of the most useful "
        "shortcuts in all of Kangaroo."))
    A(P("How many whole numbers from <b>1 to 100</b> are <b>not</b> divisible by 3 <em>or</em> 5? Counting "
        "them one by one is painful. Instead, count the ones that <b>are</b> divisible by 3 or 5, then "
        "take that away from 100."))
    A(figure(venn_complement(100, 47, "divisible by 3 or 5", "neither"),
             "Count the easy group (multiples of 3 or 5), then subtract from 100."))
    A(example("how many of 1–100 are NOT divisible by 3 or 5", steps([
        "Multiples of <b>3</b> up to 100: 100 &divide; 3 = 33 (ignore the remainder) &rarr; <b>33</b>.",
        "Multiples of <b>5</b>: 100 &divide; 5 = <b>20</b>.",
        "But multiples of <b>15</b> got counted twice (they're in both), so subtract them once: "
        "100 &divide; 15 = <b>6</b>.",
        "Divisible by 3 or 5 = 33 + 20 &minus; 6 = <b>47</b> (this is the &lsquo;add the two, take back the "
        "overlap&rsquo; rule).",
        "So <b>not</b> divisible by 3 or 5 = 100 &minus; 47 = <b>53</b>. &#10003;",
    ])))
    A(kiwi("That &ldquo;add the two, then subtract the overlap&rdquo; move has a fancy name &mdash; "
           "<b>inclusion&ndash;exclusion</b> &mdash; but you just used it like a pro. Another complement "
           "gem: to count numbers <em>with</em> a certain digit, it's usually easier to count the ones "
           "<em>without</em> it and subtract."))
    A(P("Geometry has a complement trick too. The number of <b>diagonals</b> of a shape with <em>n</em> "
        "corners is <b><em>n</em>(<em>n</em>&minus;3) &divide; 2</b> &mdash; because each corner joins to "
        "all others <em>except</em> itself and its 2 neighbours. An <b>octagon</b> (8 corners) has "
        "8&times;5&divide;2 = <b>20</b> diagonals."))
    A(tryit("How many whole numbers from <b>1 to 20</b> are <b>not</b> multiples of 4?",
            "Multiples of 4 up to 20: 20 &divide; 4 = 5 of them. So not multiples of 4 = 20 &minus; 5 = "
            "<b>15</b>."))

    # ===================== TRICK 6 . 3D / PAINTED CUBES =====================
    A(H("Trick 6 \U0001F99C — Seeing in 3D: the painted cube"))
    A(P("Kangaroo loves cubes you must picture in your head. The champion move is to sort the little cubes "
        "by <b>where they live</b>: <b>corners</b> (3 faces showing), <b>edges</b> (2 faces), "
        "<b>face-centres</b> (1 face), and <b>buried inside</b> (0 faces). For an <em>n</em>&times;<em>n</em>"
        "&times;<em>n</em> cube this never changes its pattern."))
    A(figure(painted_cube(4), "A 4×4×4 cube, painted on every outside face, then split into 64 little cubes."))
    A(example("a 4×4×4 cube is painted all over — how many little cubes have 0, 1, 2, 3 painted faces?",
              steps([
        "<b>Corners</b> always show <b>3</b> faces. A cube has <b>8</b> corners &rarr; <b>8</b> cubes with 3 "
        "painted faces (true for <em>any</em> n).",
        "<b>Edges</b> show <b>2</b> faces. Each of the 12 edges has (n&minus;2) middle cubes &rarr; "
        "12&times;(4&minus;2) = <b>24</b> cubes with 2 faces.",
        "<b>Face-centres</b> show <b>1</b> face. Each of the 6 faces has (n&minus;2)&sup2; centre cubes "
        "&rarr; 6&times;2&sup2; = <b>24</b> cubes with 1 face.",
        "<b>Buried</b> cubes show <b>0</b> faces &mdash; they form a smaller (n&minus;2)&sup3; cube inside: "
        "2&sup3; = <b>8</b> with no paint.",
        "Check the total: 8 + 24 + 24 + 8 = <b>64</b> = 4&sup3;. &#10003; Every cube accounted for!",
    ])))
    A(kiwi("Memorise the four formulas &mdash; they unlock <em>every</em> painted-cube question:<br>"
           "&bull; <b>3 faces:</b> always <b>8</b> (the corners).<br>"
           "&bull; <b>2 faces:</b> <b>12&times;(n&minus;2)</b> (the edges).<br>"
           "&bull; <b>1 face:</b> <b>6&times;(n&minus;2)&sup2;</b> (the face-centres).<br>"
           "&bull; <b>0 faces:</b> <b>(n&minus;2)&sup3;</b> (buried inside)."))
    A(tryit("A <b>5&times;5&times;5</b> cube is painted all over and cut into 125 little cubes. How many "
            "have <b>exactly one</b> painted face? And how many have <b>none</b>?",
            "One face = 6&times;(5&minus;2)&sup2; = 6&times;9 = <b>54</b>. None = (5&minus;2)&sup3; = "
            "3&sup3; = <b>27</b>."))

    # ===================== TRICK 7 . GRID PATHS =====================
    A(H("Trick 7 \U0001F99C — Counting routes on a grid"))
    A(P("A town is a grid; you start bottom-left and walk to top-right, only ever going <b>right</b> or "
        "<b>up</b>. How many shortest routes are there? In Level 2 you added corner-by-corner. Benjamin "
        "gives you a faster engine &mdash; and asks you to handle <b>closed roads</b> too."))
    A(figure(path_sums(3, 3),
             "Write the number of ways to reach each corner: each = (corner below) + (corner to the left)."))
    A(example("how many shortest routes cross a 3×3 grid of blocks?", steps([
        "Label every corner with the number of ways to reach it. Edges are all <b>1</b> (one straight way).",
        "Each inside corner = (ways from below) + (ways from the left), exactly like building Pascal's "
        "triangle.",
        "Add your way up; the top-right corner reads <b>20</b>.",
        "<b>The fast formula:</b> a route is just 3 R's and 3 U's in some order &mdash; choose which 3 of "
        "the 6 steps are R's. That count is <b>&ldquo;6 choose 3&rdquo; = 20</b>. Same answer, instantly. "
        "&#10003;",
    ])))
    A(kiwi("The engine: on a grid that is <em>m</em> wide and <em>n</em> tall, the number of shortest "
           "right/up routes is <b>&ldquo;(m+n) choose m&rdquo;</b> &mdash; the number of ways to arrange "
           "<em>m</em> rights among <em>m</em>+<em>n</em> steps. (m+n choose m means "
           "(m+n)! &divide; (m! &times; n!).) For a 4&times;4 grid that's &ldquo;8 choose 4&rdquo; = "
           "<b>70</b> routes."))
    A(P("Now the Benjamin twist: a <b>road is closed</b> at one corner. Count routes through the bad "
        "corner and <b>subtract</b> them (complement again!). Routes <em>avoiding</em> it = (all routes) "
        "&minus; (routes forced through it)."))
    A(figure(grid_obstacle(3, 3, block=(1, 1)),
             "Same 3×3 grid, but the marked corner is closed. How many routes still reach the End?"))
    A(example("routes across the 3×3 grid that avoid the closed corner", steps([
        "All routes with no closure = <b>20</b> (from above).",
        "Routes <em>forced</em> through the closed corner = (ways to reach it) &times; (ways from it to the "
        "End). To that corner: &ldquo;2 choose 1&rdquo; = 2. From it onward: &ldquo;4 choose 2&rdquo; = 6.",
        "So routes through the bad corner = 2 &times; 6 = <b>12</b>.",
        "Routes that <b>avoid</b> it = 20 &minus; 12 = <b>8</b>. &#10003;",
    ])))
    A(tryit("On a grid <b>4 wide and 2 tall</b>, how many shortest right/up routes are there (no closures)?",
            "&ldquo;(4+2) choose 4&rdquo; = &ldquo;6 choose 4&rdquo; = <b>15</b> routes."))

    # ===================== TRICK 8 . LOGICAL ELIMINATION =====================
    A(H("Trick 8 \U0001F99C — Logical elimination with clues"))
    A(P("Detective problems give you clues; your job is to <b>cross out the impossible</b> until one "
        "answer survives. Two master techniques: <b>line things up in order</b>, and <b>test the cases "
        "one by one</b>."))
    A(P("<b>Ordering.</b> Five children take a test, all with different scores. Mira scored higher than "
        "Ravi, Ravi higher than Tia, Sam higher than Mira, and Ela scored the lowest. Who came "
        "<b>third</b>?"))
    A(figure(clue_list("Detective board — who came 3rd?", [
        "Mira scored higher than Ravi", "Ravi scored higher than Tia",
        "Sam scored higher than Mira", "Ela scored the lowest"]),
             "Chain the comparisons into a single line from highest to lowest."))
    A(example("ordering the five scores", steps([
        "Chain the &lsquo;higher than&rsquo; clues: Sam &gt; Mira &gt; Ravi &gt; Tia.",
        "Ela is the lowest, so she sits at the very bottom, below Tia.",
        "The full order, highest to lowest: <b>Sam, Mira, Ravi, Tia, Ela</b>.",
        "Third place is <b>Ravi</b>. &#10003;",
    ])))
    A(P("<b>Testing cases.</b> A cookie vanished. Four friends each speak, but <em>exactly one</em> of "
        "them is telling the <b>truth</b>. Tom: &ldquo;Sam took it.&rdquo; Sam: &ldquo;I did not.&rdquo; "
        "Pia: &ldquo;I did not.&rdquo; Ron: &ldquo;Tom took it.&rdquo; Who took the cookie?"))
    A(example("the cookie thief (exactly one statement is true)", steps([
        "Try each suspect as the thief and count how many statements come out <b>true</b>; we need exactly "
        "<b>one</b> true.",
        "If <b>Tom</b> took it: Tom F, Sam T, Pia T, Ron T &rarr; 3 true. &#10007;",
        "If <b>Sam</b> took it: Tom T, Sam F, Pia T, Ron F &rarr; 2 true. &#10007;",
        "If <b>Pia</b> took it: Tom F, Sam T, Pia F, Ron F &rarr; <b>1 true</b>. &#10003;",
        "If <b>Ron</b> took it: Tom F, Sam T, Pia T, Ron F &rarr; 2 true. &#10007;",
        "Only the case &ldquo;<b>Pia</b> took it&rdquo; gives exactly one true statement. The thief is "
        "<b>Pia</b>!",
    ])))
    A(kiwi("Two golden detective habits: <b>(1)</b> turn comparison clues into one long chain &mdash; the "
           "answer reads straight off an end; <b>(2)</b> when statements are tangled, just <em>test every "
           "possibility</em> and keep the one that fits all the clues. Slow and sure beats clever guessing."))
    A(tryit("Ana, Ben and Com each play one sport: chess, tennis or swimming. Ana does <em>not</em> play "
            "chess. Ben plays tennis. Com does <em>not</em> swim. Who plays what?",
            "Ben = tennis. Com isn't swimming and tennis is taken, so Com = chess. That leaves Ana = "
            "<b>swimming</b>. (Ana=swim, Ben=tennis, Com=chess.)"))

    # ===================== TRICK 9 . DIGITS / DIVISIBILITY / LAST DIGIT =====================
    A(H("Trick 9 \U0001F99C — Digit sense: divisibility & last digits"))
    A(P("Number-sense tricks turn scary-looking numbers into easy ones. Two you must own:"))
    A(P("<b>Divisibility by 9 (and 3):</b> a number is divisible by 9 exactly when its <b>digit sum</b> is "
        "divisible by 9 (for 3, when the digit sum is divisible by 3). So you can fill in a missing digit "
        "without long division."))
    A(example("the 3-digit number 4 ⬚ 2 is divisible by 9 — what is the missing digit?", steps([
        "Divisible by 9 means the <b>digit sum</b> is a multiple of 9.",
        "Digit sum = 4 + ? + 2 = 6 + ?.",
        "The next multiple of 9 at or above 6 is 9, so 6 + ? = 9 &rarr; ? = <b>3</b>.",
        "Check: 4<b>3</b>2 &divide; 9 = 48 exactly. &#10003;",
    ])))
    A(P("<b>Last-digit cycles:</b> the units digit of the powers of a number <b>repeats in a short "
        "loop</b>. For powers of 7 the last digits cycle <b>7, 9, 3, 1</b> and then repeat &mdash; a loop "
        "of length 4. To find the last digit of a big power, you only need its position in the loop."))
    A(figure(last_digit_wheel(7, [7, 9, 3, 1]),
             "Powers of 7 end in 7, 9, 3, 1, 7, 9, 3, 1, … — a loop of length 4."))
    A(example("what is the last digit of 7¹⁰⁰?", steps([
        "List the last-digit loop for 7: 7&sup1;&rarr;7, 7&sup2;&rarr;9, 7&sup3;&rarr;3, 7&#8308;&rarr;1, "
        "then it repeats. Loop length = <b>4</b>.",
        "Find where exponent 100 lands: 100 &divide; 4 = 25 remainder <b>0</b>. A remainder of 0 means we "
        "are at the <em>end</em> of a loop &mdash; the 4th position.",
        "The 4th last-digit in the loop is <b>1</b>.",
        "So 7&#185;&#8304;&#8304; ends in <b>1</b>. (No need to compute the giant number!) &#10003;",
    ])))
    A(kiwi("Handy loops to recognise: powers of <b>2</b> &rarr; 2, 4, 8, 6 (length 4); powers of <b>3</b> "
           "&rarr; 3, 9, 7, 1 (length 4); powers of <b>9</b> &rarr; 9, 1 (length 2); powers of <b>5</b> "
           "always end in 5; powers of <b>6</b> always end in 6. Match the exponent to its spot in the "
           "loop using the <em>remainder</em>."))
    A(tryit("What is the last digit of <b>3&#8313;&#8313;</b> (3 to the power 99)?",
            "Loop for 3 is 3, 9, 7, 1 (length 4). 99 &divide; 4 = 24 remainder 3 &rarr; the 3rd spot &rarr; "
            "<b>7</b>."))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now climb the Benjamin ladder \U0001F99C"))
    A(P("Time to use your nine tools. These rise from gentle to genuinely tricky &mdash; the same spirit "
        "as a Kangaroo-style round. Try each before you peek, and always ask: <em>which trick fits "
        "here?</em>"))

    A(practice("Remember", [
        ("In the painted-cube method, how many little cubes <em>always</em> have exactly 3 painted faces?",
         "Always <b>8</b> &mdash; the corners."),
        ("Pigeonhole: 7 pigeons go into 6 holes. At least one hole holds how many?",
         "At least <b>2</b> (7 &gt; 6)."),
        ("What is the last-digit loop for powers of 2?",
         "<b>2, 4, 8, 6</b>, then it repeats (length 4)."),
        ("A number's digit sum is 18. Is it divisible by 9?",
         "<b>Yes</b> &mdash; 18 is a multiple of 9, so the number is too."),
        ("To count shortest right/up routes on an m&times;n grid, which count do you use?",
         "&ldquo;(m+n) choose m&rdquo; &mdash; arrange m rights among m+n steps."),
    ]))
    A(practice("Understand", [
        ("Why can 5 glasses (all up) never all be turned down if you must flip exactly 2 each time?",
         "The number of down glasses starts even (0) and changes by an even amount each move, so it stays "
         "even; 5 is odd &mdash; <b>impossible</b> (parity)."),
        ("Socks come in 4 colours. How many must you grab in the dark to be sure of a matching pair?",
         "4 + 1 = <b>5</b> socks."),
        ("Numbers 1&hellip;6 are on a board; each move erase a, b and write a+b&minus;1. Final number?",
         "Sum 21, five moves dropping 1 each &rarr; 21 &minus; 5 = <b>16</b>."),
        ("How many whole numbers from 1 to 100 are NOT divisible by 3 or 5?",
         "Div by 3 or 5 = 33 + 20 &minus; 6 = 47, so not = 100 &minus; 47 = <b>53</b>."),
        ("Last digit of 2&#8309;&#8304; (2 to the 50)?",
         "Loop 2,4,8,6; 50 &divide; 4 = 12 r 2 &rarr; 2nd spot &rarr; <b>4</b>."),
    ]))
    A(practice("Apply", [
        ("A 4&times;4&times;4 cube is painted and split into 64 little cubes. How many have exactly 2 "
         "painted faces?",
         "Edges: 12 &times; (4 &minus; 2) = <b>24</b> cubes."),
        ("On a 3&times;3 grid of blocks, how many shortest right/up routes are there?",
         "&ldquo;6 choose 3&rdquo; = <b>20</b>."),
        ("A number is &times;3, then +7, then &divide;2, then &minus;4, ending at 10. What was it?",
         "Undo backwards: 10+4=14, &times;2=28, &minus;7=21, &divide;3=<b>7</b>."),
        ("The 3-digit number 5 &#9723; 4 is divisible by 9. Find the missing digit.",
         "5 + ? + 4 = 9 + ? must be a multiple of 9 &rarr; ? = <b>0</b> (giving 504 = 9&times;56)."),
        ("Choose any 5 numbers from 1&hellip;8. Must two of them add to 9? Why?",
         "<b>Yes.</b> The pairs {1,8},{2,7},{3,6},{4,5} are 4 holes; 5 numbers force two into one pair, "
         "which sums to 9."),
    ]))
    A(practice("Analyze", [
        ("Can you put + and &minus; signs in front of 1, 2, 3, &hellip;, 10 so the total is exactly 0? "
         "Explain.",
         "<b>No.</b> The plain sum 55 is odd; flipping a + to &minus; changes the total by an even amount, "
         "so every result stays odd &mdash; but 0 is even. Parity forbids it."),
        ("A 5&times;5&times;5 cube is painted all over. How many of the 125 little cubes have <b>no</b> "
         "paint?",
         "(5 &minus; 2)&sup3; = 3&sup3; = <b>27</b>."),
        ("On a 3&times;3 grid of blocks, one corner is closed (the corner 1 right and 1 up from Start). "
         "How many shortest routes still reach the End?",
         "All 20, minus those through the bad corner: (2 choose 1)&times;(4 choose 2) = 2&times;6 = 12, so "
         "20 &minus; 12 = <b>8</b>."),
        ("Five kids scored differently. Sam &gt; Mira &gt; Ravi &gt; Tia, and Ela is lowest. Who is "
         "<b>4th</b>?",
         "Order: Sam, Mira, Ravi, Tia, Ela. Fourth is <b>Tia</b>."),
        ("Last digit of 7&#8311;&#8311; (7 to the 77)?",
         "Loop 7,9,3,1; 77 &divide; 4 = 19 r 1 &rarr; 1st spot &rarr; <b>7</b>."),
    ]))
    A(practice("Create", [
        ("Invent your own &ldquo;impossible by parity&rdquo; puzzle with coins or switches, and say the "
         "one-line reason it can't be done.",
         "E.g. &ldquo;9 cards face-down; each move flip exactly 2; can all face up?&rdquo; No &mdash; "
         "face-up count stays even, but 9 is odd."),
        ("Design a painted-cube question whose answer is <b>8 unpainted cubes</b>. What size cube did you "
         "use?",
         "A <b>4&times;4&times;4</b> cube: (4&minus;2)&sup3; = 8 buried cubes have no paint."),
        ("Make up a working-backwards puzzle whose secret start is <b>5</b>. Give the forward steps and the "
         "final result.",
         "E.g. start 5: &times;4 = 20, &minus;3 = 17, so &ldquo;a number is &times;4 then &minus;3 to give "
         "17 &mdash; find it.&rdquo; Undo: 17+3=20, &divide;4 = 5. &#10003;"),
    ]))

    A(challenge(
        P("\U0001F99C <b>The Kangaroo Toolkit Triple.</b> Use three different tricks, then combine the "
          "answers. "
          "(a) <b>Painted cube:</b> a 4&times;4&times;4 cube is painted all over &mdash; how many little "
          "cubes have <em>no</em> paint at all? "
          "(b) <b>Grid paths:</b> how many shortest right/up routes cross a 3&times;3 grid of blocks? "
          "(c) <b>Last digit:</b> what is the last digit of 3&#178;&#8304;&#178;&#8308; (3 to the 2024)? "
          "Now compute <em>(a)</em> &times; <em>(c)</em>, then add <em>(b)</em>. What total do you get?") +
        tryit("Work each part with the matching trick, then combine.",
              "(a) Buried cubes = (4&minus;2)&sup3; = 2&sup3; = <b>8</b>. "
              "(b) Routes = &ldquo;6 choose 3&rdquo; = <b>20</b>. "
              "(c) Loop for 3 is 3,9,7,1 (length 4); 2024 &divide; 4 = 506 remainder 0 &rarr; the 4th spot "
              "&rarr; last digit <b>1</b>. "
              "Combine: (a)&times;(c) = 8 &times; 1 = 8, then + (b) = 8 + 20 = <b>28</b>. &#127881;")))

    A(kiwi("That's a real toolkit now &mdash; you carry all nine Benjamin-style tools: <b>parity</b>, "
           "<b>invariants</b>, <b>pigeonhole</b>, <b>working backwards</b>, <b>counting by "
           "complement</b>, the <b>painted cube</b>, <b>grid routes</b>, <b>logical elimination</b>, and "
           "<b>digit sense</b>. In the next chapter you'll put every one to work in a <b>Kangaroo-style "
           "Challenge Set</b> &mdash; 3-point, 4-point and 5-point problems, set up just like contest "
           "day. Pencils up! &#129432;&#10024;"))

    chapter("Part 8 · 🦘 Kangaroo Corner", 22, "Kangaroo Thinking Tricks",
            "Kangaroo · Brain Benders", "".join(b))
