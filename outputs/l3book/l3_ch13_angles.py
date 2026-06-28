#!/usr/bin/env python3
"""L3 Chapter 13 — Lines & Angles (Geometry · Angle Chasers). A from-scratch
scaffold: names of angles, measuring with a protractor, complementary &
supplementary, angles on a line (180°) and at a point (360°), vertically
opposite angles, and parallel lines cut by a transversal. The surprise:
chasing an unknown angle without ever measuring it."""
import math
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg)
from l3_figs import angle, INK, ORANGE, SKY, GRASS, BERRY, PURPLE, GOLD


# ── local inline figures (things the toolkit doesn't have) ──────────────
def straight_line_split(a):
    """A straight line through a point, split into a and (180-a) by one ray."""
    cx, cy, r = 210, 150, 150
    rad = math.radians(a)
    x2, y2 = cx + r * math.cos(rad), cy - r * math.sin(rad)
    s = [f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{INK}" stroke-width="2.6"/>',
         f'<line x1="{cx}" y1="{cy}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{BERRY}" stroke-width="2.6"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>',
         f'<path d="M{cx+44},{cy} A44,44 0 0 0 {cx+44*math.cos(rad):.0f},{cy-44*math.sin(rad):.0f}" fill="none" stroke="{ORANGE}" stroke-width="2.2"/>',
         f'<text x="{cx+58}" y="{cy-18}" text-anchor="start" font-size="15" font-weight="800" fill="{ORANGE}">a</text>',
         f'<path d="M{cx+44*math.cos(rad):.0f},{cy-44*math.sin(rad):.0f} A44,44 0 0 0 {cx-44},{cy}" fill="none" stroke="{SKY}" stroke-width="2.2"/>',
         f'<text x="{cx-62}" y="{cy-20}" text-anchor="start" font-size="15" font-weight="800" fill="{SKY}">b</text>']
    return svg("".join(s), 420, 175)


def point_360(parts):
    """Several rays from one centre splitting the full turn; parts = list of (deg_span,label,color)."""
    cx, cy, r = 150, 150, 120
    s = []
    ang = 0
    for span, lab, col in parts:
        a0 = math.radians(ang)
        x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x0:.0f}" y2="{y0:.0f}" stroke="{INK}" stroke-width="2.4"/>')
        am = math.radians(ang + span / 2)
        s.append(f'<text x="{cx+58*math.cos(am):.0f}" y="{cy-58*math.sin(am):.0f}" text-anchor="middle" font-size="14" font-weight="800" fill="{col}">{lab}</text>')
        ang += span
    s.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>')
    return svg("".join(s), 300, 300)


def vertical_pair(a):
    """Two lines crossing at a point -> vertically opposite angles a & a, b & b."""
    cx, cy, r = 200, 110, 120
    rad = math.radians(a)
    dx, dy = r * math.cos(rad), r * math.sin(rad)
    s = [f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{INK}" stroke-width="2.6"/>',
         f'<line x1="{cx-dx:.0f}" y1="{cy+dy:.0f}" x2="{cx+dx:.0f}" y2="{cy-dy:.0f}" stroke="{INK}" stroke-width="2.6"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>',
         f'<text x="{cx+34}" y="{cy-14}" font-size="15" font-weight="800" fill="{ORANGE}">a</text>',
         f'<text x="{cx-40}" y="{cy+22}" font-size="15" font-weight="800" fill="{ORANGE}">a</text>',
         f'<text x="{cx+8}" y="{cy+30}" font-size="15" font-weight="800" fill="{SKY}">b</text>',
         f'<text x="{cx-20}" y="{cy-16}" font-size="15" font-weight="800" fill="{SKY}">b</text>']
    return svg("".join(s), 400, 220)


def parallel_transversal(show_labels=True):
    s = []
    y1, y2 = 60, 150
    s.append(f'<line x1="20" y1="{y1}" x2="430" y2="{y1}" stroke="{SKY}" stroke-width="2.6"/>')
    s.append(f'<line x1="20" y1="{y2}" x2="430" y2="{y2}" stroke="{SKY}" stroke-width="2.6"/>')
    s.append(f'<text x="420" y="{y1-8}" font-size="13" fill="{SKY}">&#8594;</text>')
    s.append(f'<text x="420" y="{y2-8}" font-size="13" fill="{SKY}">&#8594;</text>')
    s.append(f'<line x1="150" y1="20" x2="320" y2="195" stroke="{BERRY}" stroke-width="2.6"/>')
    if show_labels:
        s.append(f'<text x="178" y="48" font-size="14" font-weight="800" fill="{ORANGE}">x</text>')
        s.append(f'<text x="266" y="138" font-size="14" font-weight="800" fill="{GRASS}">y</text>')
    return svg("".join(s), 450, 210)


def _protractor(reading):
    """A semicircle protractor with a ray at `reading` degrees off the baseline."""
    cx, cy, r = 175, 150, 130
    s = [f'<path d="M{cx-r},{cy} A{r},{r} 0 0 1 {cx+r},{cy} Z" fill="{SKY}10" stroke="{SKY}" stroke-width="2"/>']
    s.append(f'<line x1="{cx-r-12}" y1="{cy}" x2="{cx+r+12}" y2="{cy}" stroke="{INK}" stroke-width="2.4"/>')
    for d in range(0, 181, 10):
        rad = math.radians(d)
        x1, y1 = cx + (r) * math.cos(rad), cy - (r) * math.sin(rad)
        x2, y2 = cx + (r - 12) * math.cos(rad), cy - (r - 12) * math.sin(rad)
        s.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{SKY}" stroke-width="1.3"/>')
        if d % 30 == 0:
            xl, yl = cx + (r - 26) * math.cos(rad), cy - (r - 26) * math.sin(rad)
            s.append(f'<text x="{xl:.0f}" y="{yl+4:.0f}" text-anchor="middle" font-size="11" fill="{INK}">{d}</text>')
    rad = math.radians(reading)
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+r*math.cos(rad):.0f}" y2="{cy-r*math.sin(rad):.0f}" stroke="{BERRY}" stroke-width="2.8"/>')
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{BERRY}" stroke-width="2.8"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>')
    s.append(f'<text x="{cx+(r-50)*math.cos(math.radians(reading/2)):.0f}" y="{cy-(r-50)*math.sin(math.radians(reading/2)):.0f}" text-anchor="middle" font-size="15" font-weight="800" fill="{BERRY}">{reading}&#176;</text>')
    return svg("".join(s), 350, 175)


def _complement(a):
    """Two adjacent angles a and (90-a) sharing a vertex, fitting into a right angle."""
    cx, cy, r = 90, 150, 150
    rad = math.radians(a)
    s = [f'<line x1="{cx}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{INK}" stroke-width="2.6"/>',
         f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r}" stroke="{INK}" stroke-width="2.6"/>',
         f'<line x1="{cx}" y1="{cy}" x2="{cx+r*math.cos(rad):.0f}" y2="{cy-r*math.sin(rad):.0f}" stroke="{BERRY}" stroke-width="2.6"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>',
         f'<polyline points="{cx+16},{cy} {cx+16},{cy-16} {cx},{cy-16}" fill="none" stroke="{INK}" stroke-width="1.4"/>',
         f'<text x="{cx+46}" y="{cy-14}" font-size="14" font-weight="800" fill="{ORANGE}">{a}&#176;</text>',
         f'<text x="{cx+18}" y="{cy-60}" font-size="14" font-weight="800" fill="{SKY}">{90-a}&#176;</text>']
    return svg("".join(s), 260, 175)


def _three_on_line(a, c):
    """Three angles a, c, (180-a-c) sitting on a straight baseline."""
    cx, cy, r = 200, 150, 160
    r1 = math.radians(a); r2 = math.radians(a + c)
    s = [f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{INK}" stroke-width="2.6"/>',
         f'<line x1="{cx}" y1="{cy}" x2="{cx-r*math.cos(r1):.0f}" y2="{cy-r*math.sin(r1):.0f}" stroke="{BERRY}" stroke-width="2.4"/>',
         f'<line x1="{cx}" y1="{cy}" x2="{cx-r*math.cos(r2):.0f}" y2="{cy-r*math.sin(r2):.0f}" stroke="{GRASS}" stroke-width="2.4"/>',
         f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>',
         f'<text x="{cx+58}" y="{cy-14}" font-size="14" font-weight="800" fill="{ORANGE}">{a}&#176;</text>',
         f'<text x="{cx}" y="{cy-60}" text-anchor="middle" font-size="14" font-weight="800" fill="{SKY}">{c}&#176;</text>',
         f'<text x="{cx-66}" y="{cy-14}" font-size="14" font-weight="800" fill="{PURPLE}">?</text>']
    return svg("".join(s), 400, 175)


def _transversal_chase(a):
    s = []
    y1, y2 = 55, 150
    s.append(f'<line x1="20" y1="{y1}" x2="430" y2="{y1}" stroke="{SKY}" stroke-width="2.6"/>')
    s.append(f'<line x1="20" y1="{y2}" x2="430" y2="{y2}" stroke="{SKY}" stroke-width="2.6"/>')
    s.append(f'<text x="420" y="{y1-8}" font-size="13" fill="{SKY}">&#8594;</text>')
    s.append(f'<text x="420" y="{y2-8}" font-size="13" fill="{SKY}">&#8594;</text>')
    s.append(f'<line x1="150" y1="20" x2="320" y2="195" stroke="{BERRY}" stroke-width="2.6"/>')
    s.append(f'<text x="205" y="46" font-size="14" font-weight="800" fill="{ORANGE}">{a}&#176;</text>')
    s.append(f'<text x="292" y="142" font-size="14" font-weight="800" fill="{GRASS}">{a}&#176;</text>')
    return svg("".join(s), 450, 210)


def build(chapter):
    b = []; A = b.append

    # ── HOOK ────────────────────────────────────────────────────────────
    A(big_q("Two straight roads cross. A signpost tells you just <em>one</em> of the four angles they "
            "make is <b>50°</b>. Without a protractor — without measuring anything — can you find the "
            "other three? By the end of this chapter you'll do it in your head, and feel like a "
            "detective who reads angles the way you read words."))
    A(kiwi("Hi explorer, it's <b>Kiwi</b>! 🧭 In Level 2 you flipped and turned shapes. Now we zoom right "
           "in on the <b>corners</b> — the angles. An angle is just the amount of <b>turn</b> between two "
           "lines that meet. We'll learn to name angles, measure them, and best of all — to <em>chase</em> "
           "an unknown angle using rules instead of a ruler. That's the superpower of this whole part of "
           "the book."))

    # ── WHAT IS AN ANGLE ────────────────────────────────────────────────
    A(H("An angle is an amount of turn"))
    A(P("Picture the hands of a clock, or a door swinging open. When two straight lines (we call them "
        "<b>rays</b>) share a starting point — the <b>vertex</b> — the gap between them is the <b>angle</b>. "
        "We measure that turn in <b>degrees</b> (°). A full spin all the way around is <b>360°</b>; a "
        "quarter-turn is <b>90°</b>."))
    A(figure(angle(40), "Two rays meet at a vertex. The orange mark shows the angle — here, 40°."))
    A(P("Why 360 for a full turn? It's an ancient choice (the Babylonians liked 360 because it divides "
        "so neatly), and it stuck because 360 splits cleanly into halves, thirds, quarters, sixths and "
        "more. Keep that in your pocket: <b>full turn = 360°</b>, <b>half turn = 180°</b>, "
        "<b>quarter turn = 90°</b>."))

    # ── TYPES OF ANGLES ─────────────────────────────────────────────────
    A(H("The five kinds of angles"))
    A(P("Angles get names based on their size. Meet the whole family:"))
    A(figure(angle(45), "An ACUTE angle: smaller than 90°. (Tip: acute = a-'cute' little angle.)"))
    A(figure(angle(90, "90&#176;"), "A RIGHT angle: exactly 90° — a perfect square corner. We mark it with a tiny box in geometry."))
    A(figure(angle(130, "130&#176;"), "An OBTUSE angle: bigger than 90° but smaller than 180°."))
    A(figure(angle(180, "180&#176;"), "A STRAIGHT angle: exactly 180° — the two rays make a straight line."))
    A(figure(angle(210, "210&#176;"), "A REFLEX angle: bigger than 180° (more than half a turn). Here the turn we mean is the BIG way round — 210°."))
    A(kiwi("Quick check, no measuring needed — just compare to 90° and 180°:<br>"
           "• smaller than 90° → <b>acute</b><br>"
           "• exactly 90° → <b>right</b><br>"
           "• between 90° and 180° → <b>obtuse</b><br>"
           "• exactly 180° → <b>straight</b><br>"
           "• between 180° and 360° → <b>reflex</b>"))
    A(tryit("Sort these by name: 12°, 90°, 175°, 200°, 180°.",
            "12° acute · 90° right · 175° obtuse · 200° reflex · 180° straight."))

    # ── PROTRACTOR ──────────────────────────────────────────────────────
    A(H("Measuring with a protractor"))
    A(P("A <b>protractor</b> is a half-circle ruler marked from 0° to 180°. To measure an angle:"))
    A(figure(_protractor(60), "A protractor reading 60°. The centre sits on the vertex; one ray lines up with 0°."))
    A(example("measure an angle with a protractor", steps([
        "Place the protractor's <b>centre dot</b> exactly on the <b>vertex</b> (the corner).",
        "Turn it so one ray runs along the <b>0° line</b> (the baseline).",
        "Read where the <em>other</em> ray crosses the scale. Use the scale that starts at 0° on your "
        "baseline — a protractor has two scales so you don't read the wrong one!",
        "Here the second ray points to <b>60°</b>, so the angle is 60°.",
    ])))
    A(kiwi("The two-scale trap is the #1 mistake. Easy fix: first <em>guess</em> whether the angle is acute "
           "or obtuse. If it looks acute, your answer must be under 90°. If your reading says 120° but the "
           "angle is clearly a tiny acute one, you read the wrong scale — flip to the other."))
    A(tryit("Your ray starts on the 0° baseline and the other crosses the scale at the 110° mark. "
            "Is the angle acute or obtuse, and what is its size?",
            "110° is between 90° and 180°, so it's <b>obtuse</b>, measuring <b>110°</b>."))

    # ── COMPLEMENTARY & SUPPLEMENTARY ───────────────────────────────────
    A(H("Two angles that team up: complementary & supplementary"))
    A(P("Some angle pairs add to special totals — and that's where angle-chasing begins."))
    A(P("<b>Complementary</b> angles add up to <b>90°</b> (think: they make a right angle together). "
        "<b>Supplementary</b> angles add up to <b>180°</b> (they make a straight line together)."))
    A(figure(_complement(35), "Two complementary angles: 35° + 55° = 90°. They fit together into a right angle."))
    A(figure(straight_line_split(125), "Two supplementary angles on a straight line: a + b = 180°."))
    A(example("find the missing partner", steps([
        "An angle is 35°. Its <b>complement</b> = 90 − 35 = <b>55°</b>.",
        "The same 35° angle's <b>supplement</b> = 180 − 35 = <b>145°</b>.",
        "No guessing, no measuring — just subtract from 90 or from 180!",
    ])))
    A(kiwi("A memory hook some students love: <b>C</b> comes before <b>S</b> in the alphabet, and "
           "<b>9</b>0 comes before <b>18</b>0. So <b>C</b>omplementary → 90°, <b>S</b>upplementary → 180°."))
    A(tryit("Two angles are supplementary. One is 72°. What is the other?",
            "180 − 72 = <b>108°</b>."))
    A(tryit("An angle and its complement are equal. What is each angle?",
            "If both are equal and add to 90°, each is 90 ÷ 2 = <b>45°</b>."))

    # ── ANGLES ON A LINE ────────────────────────────────────────────────
    A(H("Angles on a straight line add to 180°"))
    A(P("Here is the first big chasing rule. If several angles sit in a row along one side of a "
        "<b>straight line</b>, they always add up to <b>180°</b> — because a straight line <em>is</em> a "
        "half-turn."))
    A(figure(_three_on_line(50, 70), "Three angles on a straight line: 50° + 70° + ? = 180°."))
    A(example("chase the unknown on a line", steps([
        "The three angles share a straight line, so they total <b>180°</b>.",
        "Known so far: 50° + 70° = 120°.",
        "Missing angle = 180 − 120 = <b>60°</b>. Detective work, not a ruler!",
    ])))
    A(tryit("On a straight line, two angles are 90° and x. Find x.",
            "x = 180 − 90 = <b>90°</b>. (Two right angles make a straight line.)"))

    # ── ANGLES AT A POINT ───────────────────────────────────────────────
    A(H("Angles around a point add to 360°"))
    A(P("Go all the way around a single point and you've made a <b>full turn</b>. So all the angles "
        "meeting at a point must total <b>360°</b>."))
    A(figure(point_360([(90, "90°", BERRY), (120, "120°", GRASS), (60, "60°", SKY), (90, "?", ORANGE)]),
             "Four angles meet at a point: 90° + 120° + 60° + ? = 360°."))
    A(example("chase the unknown around a point", steps([
        "Angles around the point add to <b>360°</b>.",
        "Known: 90 + 120 + 60 = 270°.",
        "Missing angle = 360 − 270 = <b>90°</b>.",
    ])))
    A(tryit("Three equal angles meet at a point. What is each one?",
            "360 ÷ 3 = <b>120°</b> each."))

    # ── VERTICALLY OPPOSITE ─────────────────────────────────────────────
    A(H("The crossing surprise: vertically opposite angles"))
    A(P("When two straight lines cross, they make four angles. The two angles that are "
        "<b>directly across</b> from each other (sharing only the vertex) are called "
        "<b>vertically opposite</b> — and here's the surprise: they are always <b>equal</b>."))
    A(figure(vertical_pair(35), "Two crossing lines. The two 'a' angles are equal; the two 'b' angles are equal."))
    A(P("Why must they be equal? Watch the chase: <b>a + b = 180°</b> (they sit on a straight line), and "
        "the angle next to b on the <em>other</em> side <b>also</b> makes 180° with b. Two things that "
        "both fill the gap left by b must be the same size. So the opposite angles match — proved, not "
        "measured!"))
    A(example("one angle unlocks all four", steps([
        "Two roads cross; one angle is <b>50°</b>.",
        "Its vertically opposite angle is also <b>50°</b>.",
        "Each of the other two angles is supplementary to 50°: 180 − 50 = <b>130°</b>.",
        "So the four angles are <b>50°, 130°, 50°, 130°</b> — and they add to 360° ✓. There's the "
        "answer to our Big Question!",
    ])))
    A(tryit("Two lines cross. One angle is 110°. Give all four angles.",
            "110°, and its opposite 110°; the other pair are 180 − 110 = <b>70°</b> each. "
            "So <b>110°, 70°, 110°, 70°</b>."))

    # ── PARALLEL LINES + TRANSVERSAL ────────────────────────────────────
    A(H("Parallel lines cut by a transversal"))
    A(P("<b>Parallel</b> lines are two straight lines that run in the same direction and never meet — like "
        "rails of a train track. We mark them with little arrows. Now draw a third line crossing both of "
        "them; that crossing line is a <b>transversal</b>."))
    A(figure(parallel_transversal(), "Two parallel lines (blue arrows) cut by a transversal (red). Equal angles appear!"))
    A(P("Because the parallel lines have the <em>same slant</em>, the transversal makes the <b>same set "
        "of angles</b> at each crossing. Two beautiful patterns pop out:"))
    A(P("• <b>Corresponding angles</b> (matching position at each crossing — like x and y in the figure, "
        "both in the 'top-left' spot) are <b>equal</b>.<br>"
        "• <b>Alternate angles</b> (on opposite sides of the transversal, tucked <em>between</em> the "
        "parallels) are also <b>equal</b>."))
    A(kiwi("Picture sliding the top crossing straight down the transversal until it lands on the bottom "
           "crossing. Because the lines are parallel, everything lines up <em>perfectly</em> — that's the "
           "real reason corresponding angles match. Alternate angles then follow, because they're "
           "vertically opposite to corresponding ones."))
    A(figure(_transversal_chase(70), "If one angle is 70°, the equal-position angle below is also 70°."))
    A(example("chase across parallel lines", steps([
        "The transversal makes a <b>70°</b> angle with the top parallel line.",
        "The <b>corresponding</b> angle at the bottom line is also <b>70°</b>.",
        "The angle next to it (on the straight bottom line) is its supplement: 180 − 70 = <b>110°</b>.",
        "So once you know one angle in a parallel-lines picture, you can fill in <em>every</em> angle "
        "as 70° or 110°. ✨",
    ])))
    A(tryit("A transversal crosses two parallel lines. One angle is 65°. Its alternate angle (between the "
            "parallels, other side) is what?",
            "Alternate angles are equal, so it's also <b>65°</b>."))

    # ── BLOOM LADDER ────────────────────────────────────────────────────
    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("Name the angle that is exactly 90°.", "A right angle."),
        ("Complementary angles add up to what?", "90°."),
        ("Supplementary angles add up to what?", "180°."),
        ("How many degrees are in a full turn around a point?", "360°."),
        ("What do we call a line that crosses two other lines?", "A transversal."),
    ]))
    A(practice("Understand", [
        ("Is a 200° angle acute, obtuse, straight or reflex?", "Reflex (it is more than 180°)."),
        ("Two lines cross. Are the two angles directly opposite each other equal or supplementary?",
         "Equal — they are vertically opposite."),
        ("An angle measures 90°. What is special about its complement?",
         "Its complement is 0° — a right angle uses up the whole 90°, so there's nothing left to add."),
        ("Why do angles on a straight line add to 180°?",
         "A straight line is a half-turn, and a half-turn is 180°."),
        ("Corresponding angles at parallel lines are equal. True or false?", "True."),
    ]))
    A(practice("Apply", [
        ("Find the complement of 28°.", "90 − 28 = 62°."),
        ("Find the supplement of 95°.", "180 − 95 = 85°."),
        ("On a straight line, three angles are 40°, x and 75°. Find x.", "180 − 40 − 75 = 65°."),
        ("Around a point, angles are 130°, 80°, 70° and x. Find x.", "360 − 130 − 80 − 70 = 80°."),
        ("Two lines cross; one angle is 47°. Find the other three angles.",
         "47° (opposite), 133° and 133° (each = 180 − 47)."),
        ("A transversal makes a 118° angle with one of two parallel lines. Find the corresponding angle.",
         "118° (corresponding angles are equal)."),
    ]))
    A(practice("Analyze", [
        ("An angle is three times its complement. Find both angles.",
         "Let the angle be x; its complement is (90 − x). 'Three times its complement' means "
         "x = 3(90 − x) → x = 270 − 3x → 4x = 270 → x = 67.5°, complement = 22.5°. "
         "Check: 67.5 = 3 × 22.5 ✓."),
        ("Two supplementary angles are in the ratio 2 : 3. Find them.",
         "The 5 parts make 180°, so one part = 36°. Angles are 2 × 36 = 72° and 3 × 36 = 108°."),
        ("Two lines cross. One angle is x and the angle next to it is (x + 40)°. Find x.",
         "They are on a straight line: x + (x + 40) = 180 → 2x = 140 → x = 70°."),
        ("A transversal cuts two parallel lines. Two alternate angles are 2x and (x + 30). Find x.",
         "Alternate angles are equal: 2x = x + 30 → x = 30."),
    ]))
    A(practice("Create", [
        ("Draw two crossing lines and label all four angles with real numbers that obey the rules. "
         "What numbers did you pick?",
         "Any opposite-equal, supplementary-neighbour set — e.g. 35°, 145°, 35°, 145°. They must add to 360°."),
        ("Invent a complementary-angle riddle whose answer is 25°, and write its solution.",
         "E.g. 'I am an acute angle. My complement is 65°. Who am I?' → 90 − 65 = 25°."),
        ("Design a road junction where four roads meet at a point and every angle is a multiple of 30°. "
         "List your four angles.",
         "Any four multiples of 30° that total 360°, e.g. 60° + 90° + 120° + 90° = 360°."),
    ]))

    # ── CHALLENGE ───────────────────────────────────────────────────────
    A(challenge(
        P("Two parallel lines are crossed by a transversal. At the top crossing, one angle is "
          "<b>(3x + 10)°</b>. At the bottom crossing, the <em>co-interior</em> angle (the one on the "
          "<b>same side</b> of the transversal, also between the parallels) is <b>(2x + 30)°</b>. "
          "Co-interior angles always add to 180°. Find x — and then find both angles.") +
        tryit("Set up the equation and chase it down.",
              "Same-side interior (co-interior) angles add to 180°: (3x + 10) + (2x + 30) = 180 → "
              "5x + 40 = 180 → 5x = 140 → <b>x = 28</b>. The angles are 3(28) + 10 = <b>94°</b> and "
              "2(28) + 30 = <b>86°</b>, and 94 + 86 = 180 ✓. You just chased an unknown across two "
              "parallel lines with pure logic — no protractor in sight! 🕵️")))

    A(kiwi("Outstanding. You can name and measure angles, and — the real prize — <b>chase</b> a hidden "
           "angle using straight-line, around-a-point, vertically-opposite and parallel-line rules. "
           "Next we point these tools at <b>triangles and polygons</b>, where a single stunning fact "
           "(the angles of every triangle add to 180°) unlocks the whole world of shapes. 🔺"))

    chapter("Part 5 · Shapes, Space & Maps", 13, "Lines & Angles",
            "Geometry · Angle Chasers", "".join(b))
