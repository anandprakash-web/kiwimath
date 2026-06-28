#!/usr/bin/env python3
"""Chapter 14 — Symmetry  (Geometry · Turn & Flip)."""
import math
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, symmetry_fig, polygon, svg, ORANGE, SKY, BERRY, INK, GRASS)


def _circle_sym():
    """A circle with several mirror lines through its centre."""
    cx, cy, r = 100, 95, 70
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SKY}22" stroke="{SKY}" stroke-width="2.4"/>']
    for ang in (0, 45, 90, 135):
        a = math.radians(ang)
        dx, dy = (r + 12) * math.cos(a), (r + 12) * math.sin(a)
        s.append(f'<line x1="{cx-dx:.0f}" y1="{cy-dy:.0f}" x2="{cx+dx:.0f}" y2="{cy+dy:.0f}" '
                 f'stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>')
    return svg("".join(s), 200, 190)


def _reflect_demo():
    """Half a flag (an arrow) on the left of a vertical mirror line, with its reflection ghosted."""
    s = [f'<line x1="150" y1="14" x2="150" y2="186" stroke="{ORANGE}" stroke-width="2.5" '
         f'stroke-dasharray="7 5"/>']
    # solid left half — a simple flag triangle pointing at the line
    s.append(f'<polygon points="60,50 150,80 60,110" fill="{GRASS}33" stroke="{GRASS}" stroke-width="2.4"/>')
    s.append(f'<rect x="56" y="50" width="6" height="100" fill="{GRASS}" />')
    # ghosted mirror copy on the right (the answer)
    s.append(f'<polygon points="240,50 150,80 240,110" fill="{GRASS}12" stroke="{GRASS}" '
             f'stroke-width="2" stroke-dasharray="5 4"/>')
    s.append(f'<rect x="238" y="50" width="6" height="100" fill="{GRASS}" opacity=".45"/>')
    s.append(f'<text x="80" y="170" font-size="13" fill="{INK}" text-anchor="middle">given half</text>')
    s.append(f'<text x="222" y="170" font-size="13" fill="{INK}" text-anchor="middle">mirror copy</text>')
    return svg("".join(s), 300, 190)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Fold a paper butterfly exactly in half and the two wings land <b>perfectly on top of each "
            "other</b>. What is the secret rule that makes the two halves match? "
            "It's a beautiful idea called <em>symmetry</em>."))
    A(kiwi("Hi! When a shape can be folded so that one half lands <em>exactly</em> on the other half, we "
           "say it has <b>line symmetry</b>. The fold line — the line that splits it into matching halves "
           "— is called a <b>line of symmetry</b> (or <em>mirror line</em>). Think of it as a magic "
           "mirror: one side is the reflection of the other."))

    A(H("A line of symmetry makes two matching halves"))
    A(P("Picture a <b>heart</b>. Run a straight line down its middle and fold. The left half lands right "
        "on top of the right half — they match perfectly. That middle line is a <b>line of symmetry</b>."))
    A(figure(symmetry_fig("heart", 1), "A heart with its line of symmetry (the dashed line)"))
    A(P("The dashed orange line is the mirror line. Everything on the left is a mirror copy of "
        "everything on the right. That's what makes the heart look balanced."))
    A(kiwi("Here's a real test you can do with any picture: imagine folding along the line. If the two "
           "halves match <em>exactly</em> — every edge on top of an edge — it's a true line of symmetry. "
           "If they don't quite line up, it isn't one!"))
    A(tryit("If you fold a shape along a line of symmetry, what happens to the two halves?",
            "They land <b>exactly</b> on top of each other — the halves match perfectly, like a "
            "mirror reflection."))

    A(H("Some shapes have more than one line of symmetry"))
    A(P("A heart has just <em>one</em> mirror line. But many shapes have <b>several</b>! Let's count "
        "them, starting with a triangle whose two sides are equal (an <b>isosceles</b> triangle):"))
    A(figure(symmetry_fig("tri", 1), "An isosceles triangle — 1 line of symmetry"))
    A(P("Fold it down the middle and the two slanted sides match. That's its <em>one</em> line of "
        "symmetry. Now look at a <b>square</b>:"))
    A(figure(symmetry_fig("square", 2), "A square — two of its lines of symmetry are shown; a square has four in all"))
    A(example("how many lines of symmetry does a square have?", steps([
        "Fold top-to-bottom: the halves match — that's <b>1</b> line (the horizontal one shown).",
        "Fold left-to-right: the halves match — that's a <b>2nd</b> line (the vertical one shown).",
        "You can also fold along each <b>diagonal</b> (corner to corner) and the halves still match — "
        "that's <b>2 more</b> lines.",
        "Total: 2 straight + 2 diagonal = <b>4 lines of symmetry</b> for a square!",
    ]) + P("The picture shows the two straight ones; remember the two diagonals are there too.")))
    A(P("Here is a count of lines of symmetry for common shapes:"))
    A('<table class="pv"><tr><th>Shape</th><th>Lines of symmetry</th></tr>'
      '<tr><td>Square</td><td>4</td></tr>'
      '<tr><td>Rectangle (not a square)</td><td>2</td></tr>'
      '<tr><td>Equilateral triangle (all sides equal)</td><td>3</td></tr>'
      '<tr><td>Isosceles triangle (two sides equal)</td><td>1</td></tr>'
      '<tr><td>Circle</td><td>Very many! (a line through the centre any way you turn)</td></tr></table>')
    A(kiwi("A <b>circle</b> is the symmetry champion. <em>Any</em> straight line through its centre folds "
           "it into matching halves — so it has more lines of symmetry than you could ever count. A "
           "rectangle (that isn't a square) has only 2: across the middle the long way and the short way. "
           "Its diagonals do <em>not</em> work — try folding a long rectangle corner-to-corner and the "
           "halves won't match!"))
    A(figure(_circle_sym(), "A circle — every line through its centre is a line of symmetry (here are 4)"))
    A(tryit("How many lines of symmetry does a <b>rectangle</b> (that is not a square) have?",
            "<b>2</b> — one across the middle the long way, and one across the middle the short way. "
            "(The diagonals do not work for a rectangle.)"))

    A(H("Symmetry in letters and the world"))
    A(P("Symmetry is hiding in plain sight — in capital letters, road signs, flowers, faces and "
        "butterflies. Take capital letters. Some have a <b>vertical</b> mirror line, some a "
        "<b>horizontal</b> one, some have both, and some have none."))
    A('<table class="pv"><tr><th>Mirror line</th><th>Example letters</th></tr>'
      '<tr><td>Vertical (down the middle)</td><td>A, M, T, U, V, W, Y</td></tr>'
      '<tr><td>Horizontal (across the middle)</td><td>B, C, D, E, K</td></tr>'
      '<tr><td>Both vertical and horizontal</td><td>H, I, O, X</td></tr>'
      '<tr><td>No line of symmetry</td><td>F, G, J, L, P, Q, R, S, Z</td></tr></table>')
    A(tryit("Does the letter <b>H</b> have a line of symmetry? How many, and which way?",
            "Yes — <b>2</b> lines. A vertical one down the middle <em>and</em> a horizontal one across "
            "the middle both split H into matching halves."))

    A(H("Complete the symmetric picture"))
    A(P("A favourite puzzle: you're given <em>half</em> a picture and a mirror line, and you must draw "
        "the other half so the whole thing is symmetric. The trick is to <b>reflect every point</b> "
        "across the line — each point's mirror copy is the same distance on the other side."))
    A(figure(_reflect_demo(), "Given the solid half on the left, the dashed half on the right completes it"))
    A(example("completing a symmetric flag", P("Half of a flag is drawn to the left of a vertical mirror "
        "line. A red dot sits <b>3 squares</b> to the left of the line. Where does its mirror copy go?")
        + steps([
        "A line of symmetry makes one side a mirror of the other.",
        "The dot is 3 squares <em>left</em> of the line, so its mirror copy is 3 squares <em>right</em> "
        "of the line — the <b>same distance</b>, opposite side.",
        "Do this for every point of the half-picture and you've completed the symmetric flag!",
    ])))
    A(kiwi("Golden rule for completing symmetry: <b>same distance from the line, opposite side</b>. "
           "A point 2 squares above goes 2 squares above on the other side; a point touching the line "
           "stays put. Reflect point by point and the picture finishes itself."))
    A(tryit("In a symmetric drawing with a vertical mirror line, a star is <b>4 squares to the right</b> "
            "of the line. Where is its mirror copy?",
            "<b>4 squares to the left</b> of the line — the same distance, on the opposite side."))

    A(H("Turning symmetry — rotational symmetry"))
    A(P("There's a second kind of symmetry that's about <em>turning</em> instead of folding. A shape has "
        "<b>rotational symmetry</b> if you can spin it part-way around its centre and it looks "
        "<em>exactly the same</em> as before — before you've gone all the way around."))
    A(figure(polygon([(0.5, 0.0), (1.0, 0.66), (0.79, 1.0), (0.21, 1.0), (0.0, 0.66)],
                     labels=["", "", "", "", ""], fill="#8B5CF6"),
             "A regular pentagon looks the same as you turn it around its centre"))
    A(P("Think of a square lying flat. Turn it a quarter-turn (90°) and it looks identical — you can't "
        "tell it moved! Turn it again, and again — it matches in <b>4</b> positions as it spins all the "
        "way round. We say the square has rotational symmetry of <b>order 4</b>."))
    A(example("rotational symmetry of a square", steps([
        "Start with a square. Slowly turn it around its centre.",
        "After a quarter-turn (90°) it looks exactly the same. ✓",
        "It matches again at a half-turn, a three-quarter-turn, and a full turn.",
        "It looks the same in <b>4</b> positions during one full spin → <b>order 4</b>.",
    ])))
    A(kiwi("A neat fact: a shape always looks the same after a <em>full</em> turn (360°) — that doesn't "
           "count as special. Rotational symmetry is about matching <em>before</em> a full turn. A "
           "square matches 4 times, an equilateral triangle matches 3 times, and a circle matches at "
           "<em>every</em> tiny turn!"))
    A(tryit("Turn a rectangle (not a square) a half-turn (180°) around its centre. Does it look the "
            "same?",
            "Yes! A rectangle looks the same after a half-turn, so it has rotational symmetry of "
            "<b>order 2</b> (it matches twice in a full spin)."))

    A(H("Now you try — climb the ladder"))
    A(P("Fold, flip and turn your way up the ladder. Picture each shape before you peek!"))

    A(practice("Remember", [
        ("What is a <b>line of symmetry</b>?",
         "A line that folds a shape into two matching halves (a mirror line)."),
        ("If you fold a shape on its line of symmetry, what do the two halves do?",
         "They match exactly, one on top of the other."),
        ("How many lines of symmetry does a <b>square</b> have?",
         "4 lines of symmetry."),
        ("How many lines of symmetry does a <b>heart</b> have?",
         "1 (a vertical line down the middle)."),
        ("What is <b>rotational symmetry</b>?",
         "When a shape looks the same after being turned part-way around its centre."),
    ]))
    A(practice("Understand", [
        ("How many lines of symmetry does a <b>rectangle</b> (not a square) have?",
         "2 lines."),
        ("How many lines of symmetry does an <b>equilateral triangle</b> have?",
         "3 lines."),
        ("Does the letter <b>A</b> have a line of symmetry? Which way?",
         "Yes — 1 vertical line down the middle."),
        ("Does the letter <b>O</b> have lines of symmetry? How many?",
         "In this block-letter font, O has vertical AND horizontal symmetry — that's <b>2</b> lines. "
         "(A perfect circle, on the other hand, has infinitely many lines through its centre.)"),
        ("A shape matches itself 3 times in a full turn. What is its order of rotational symmetry?",
         "Order 3."),
    ]))
    A(practice("Apply", [
        ("Which of these letters have a <b>vertical</b> line of symmetry: A, B, M, F, T?",
         "A, M and T have a vertical line. (B has a horizontal one; F has none.)"),
        ("A point is 5 squares to the left of a vertical mirror line. Where is its mirror copy?",
         "5 squares to the right of the line (same distance, opposite side)."),
        ("How many lines of symmetry does a <b>circle</b> have?",
         "Very many — any line through its centre is a line of symmetry."),
        ("Sort these by number of lines of symmetry: square, rectangle, equilateral triangle.",
         "Equilateral triangle = 3, rectangle = 2, square = 4. (So square > triangle > rectangle.)"),
        ("Turn an equilateral triangle around its centre. After what turn does it first look the same?",
         "After a one-third turn (120°). It matches 3 times in a full spin (order 3)."),
    ]))
    A(practice("Analyze", [
        ("Which has <b>more</b> lines of symmetry, a square or an equilateral triangle? By how many?",
         "A square has 4 and a triangle has 3, so the square has 1 more."),
        ("Ved says a rectangle has 4 lines of symmetry, like a square. Is he right? Explain.",
         "No — a rectangle (not a square) has only 2 lines. Its diagonals are NOT lines of symmetry, "
         "because folding a long rectangle corner-to-corner does not make the halves match."),
        ("How many capital letters in the word <b>MATH</b> have at least one line of symmetry?",
         "M (vertical), A (vertical), T (vertical) and H (both) all do — that's all <b>4</b> letters."),
        ("A regular hexagon (6 equal sides) — how many lines of symmetry would you expect, and why?",
         "6 lines. For a regular shape, the number of lines of symmetry equals the number of sides."),
        ("Does a parallelogram (a slanted, pushed-over rectangle) that is not a rectangle have any "
         "lines of symmetry?",
         "No lines of symmetry — but it does have rotational symmetry of order 2 (a half-turn looks "
         "the same)."),
    ]))
    A(practice("Create", [
        ("Write <b>three</b> capital letters that each have a vertical line of symmetry.",
         "Any from A, M, T, U, V, W, Y. For example: A, T, W."),
        ("Draw a shape with exactly <b>2</b> lines of symmetry, and name it.",
         "A rectangle (not a square) has exactly 2 lines of symmetry. (A non-square rhombus also "
         "has exactly 2.)"),
        ("Fold a piece of paper in half, cut a shape along the fold, then open it. Explain why the "
         "result is always symmetric.",
         "Because the fold becomes the line of symmetry: whatever you cut on one side is mirrored "
         "exactly on the other side when you unfold. (This is how paper snowflakes get their symmetry!)"),
    ]))

    A(challenge(
        P("Kiwi is making an alphabet poster and wants to group the capital letters by their symmetry. "
          "From the letters <b>H, A, S, X, N, T, O</b>, find: "
          "(a) the letters with a <b>vertical</b> line of symmetry, "
          "(b) the letters with <b>two</b> lines of symmetry, and "
          "(c) the letters with <b>no</b> line of symmetry.") +
        tryit("Test each letter by imagining a mirror down the middle and across the middle.",
              "(a) <b>Vertical line:</b> H, A, T, O, X. "
              "(b) <b>Two lines:</b> H, O, X (each has both a vertical and a horizontal mirror line). "
              "(c) <b>No line of symmetry:</b> S and N (they have rotational symmetry of order 2 "
              "instead, but no mirror line).")))

    A(kiwi("You've reached the end of our geometry adventure! You can now spot lines of symmetry, count "
           "how many a shape has, complete symmetric pictures by reflecting point-for-point, and even "
           "recognise rotational symmetry by turning shapes. From butterflies to letters to spinning "
           "squares, you'll start noticing this hidden balance everywhere. That's a lot of careful "
           "seeing — nicely done. 🌟"))

    chapter("Part 4 · Measure Masters & Turn & Flip", 14, "Symmetry",
            "Geometry · Turn & Flip", "".join(b))
