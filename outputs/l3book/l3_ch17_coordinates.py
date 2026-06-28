#!/usr/bin/env python3
"""L3 Chapter 17 — Maps, Directions & Coordinates (Geometry · Map Makers).
A from-scratch scaffold: compass directions and turns, grid map references, the
coordinate plane — plotting and reading (x, y) points, and simple paths /
distance on a grid. The surprise: you can describe any spot on Earth (or a
treasure!) with just two numbers."""
import math
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, coord_grid)
from l3_figs import INK, ORANGE, SKY, GRASS, BERRY, PURPLE, GOLD


# ── local inline figures ────────────────────────────────────────────────
def compass():
    """An 8-point compass rose: N E S W + NE SE SW NW."""
    cx, cy, r = 130, 120, 92
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SKY}08" stroke="{SKY}" stroke-width="1.6"/>']
    dirs = [("N", -90), ("NE", -45), ("E", 0), ("SE", 45), ("S", 90), ("SW", 135), ("W", 180), ("NW", 225)]
    for lab, deg in dirs:
        a = math.radians(deg)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        major = lab in ("N", "E", "S", "W")
        col = BERRY if lab == "N" else (INK if major else ORANGE)
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{col}" stroke-width="{2.4 if major else 1.4}"/>')
        xl, yl = cx + (r + 12) * math.cos(a), cy + (r + 12) * math.sin(a)
        s.append(f'<text x="{xl:.0f}" y="{yl+4:.0f}" text-anchor="middle" font-size="{15 if major else 12}" font-weight="800" fill="{col}">{lab}</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>')
    return svg("".join(s), 260, 250)


def grid_map():
    """A simple labelled map grid with columns A-D and rows 1-4 and a few icons."""
    c, o = 44, 26
    cols = ["A", "B", "C", "D"]
    n = 4
    s = [f'<rect x="{o}" y="{o}" width="{n*c}" height="{n*c}" fill="none" stroke="{INK}" stroke-width="1.6"/>']
    for k in range(n + 1):
        s.append(f'<line x1="{o+k*c}" y1="{o}" x2="{o+k*c}" y2="{o+n*c}" stroke="{INK}" stroke-width=".6" opacity=".5"/>')
        s.append(f'<line x1="{o}" y1="{o+k*c}" x2="{o+n*c}" y2="{o+k*c}" stroke="{INK}" stroke-width=".6" opacity=".5"/>')
    for i, lab in enumerate(cols):
        s.append(f'<text x="{o+i*c+c/2:.0f}" y="{o-6}" text-anchor="middle" font-size="13" font-weight="800" fill="{SKY}">{lab}</text>')
    for r in range(n):
        s.append(f'<text x="{o-8}" y="{o+r*c+c/2+4:.0f}" text-anchor="end" font-size="13" font-weight="800" fill="{SKY}">{r+1}</text>')
    # icons: school at B2, park at D1, home at A4
    s.append(f'<text x="{o+1*c+c/2:.0f}" y="{o+1*c+c/2+8:.0f}" text-anchor="middle" font-size="22">🏫</text>')   # B2
    s.append(f'<text x="{o+3*c+c/2:.0f}" y="{o+0*c+c/2+8:.0f}" text-anchor="middle" font-size="22">🌳</text>')   # D1
    s.append(f'<text x="{o+0*c+c/2:.0f}" y="{o+3*c+c/2+8:.0f}" text-anchor="middle" font-size="22">🏠</text>')   # A4
    return svg("".join(s), o + n * c + 18, o + n * c + 14)


def axes_only():
    """An empty coordinate grid to introduce the axes."""
    c, o = 30, 28
    n = 5
    s = [f'<rect x="{o}" y="6" width="{n*c}" height="{n*c}" fill="none" stroke="{INK}" stroke-width="1.4"/>']
    for k in range(n + 1):
        s.append(f'<line x1="{o+k*c}" y1="6" x2="{o+k*c}" y2="{6+n*c}" stroke="{INK}" stroke-width=".5" opacity=".4"/>')
        s.append(f'<line x1="{o}" y1="{6+k*c}" x2="{o+n*c}" y2="{6+k*c}" stroke="{INK}" stroke-width=".5" opacity=".4"/>')
        s.append(f'<text x="{o+k*c}" y="{6+n*c+15}" text-anchor="middle" font-size="11" fill="{INK}">{k}</text>')
        if k < n:
            s.append(f'<text x="{o-8}" y="{6+(n-k)*c+4}" text-anchor="end" font-size="11" fill="{INK}">{k}</text>')
    # axis labels
    s.append(f'<text x="{o+n*c+4}" y="{6+n*c+4}" font-size="13" font-weight="800" fill="{SKY}">x</text>')
    s.append(f'<text x="{o-4}" y="2" text-anchor="middle" font-size="13" font-weight="800" fill="{BERRY}">y</text>')
    s.append(f'<text x="{o-8}" y="{6+n*c+15}" text-anchor="end" font-size="11" font-weight="800" fill="{INK}">O</text>')
    return svg("".join(s), o + n * c + 20, 6 + n * c + 24)


def path_grid():
    """A coordinate grid with a path A(1,1)->B(1,4)->C(5,4)."""
    pts = [(1, 1, "A"), (1, 4, "B"), (5, 4, "C")]
    c, o = 28, 26
    n = 6
    s = [f'<rect x="{o}" y="6" width="{n*c}" height="{n*c}" fill="none" stroke="{INK}" stroke-width="1.6"/>']
    for k in range(n + 1):
        s.append(f'<line x1="{o+k*c}" y1="6" x2="{o+k*c}" y2="{6+n*c}" stroke="{INK}" stroke-width=".5" opacity=".4"/>')
        s.append(f'<line x1="{o}" y1="{6+k*c}" x2="{o+n*c}" y2="{6+k*c}" stroke="{INK}" stroke-width=".5" opacity=".4"/>')
        s.append(f'<text x="{o+k*c}" y="{6+n*c+15}" text-anchor="middle" font-size="11" fill="{INK}">{k}</text>')
        if k < n:
            s.append(f'<text x="{o-8}" y="{6+(n-k)*c+4}" text-anchor="end" font-size="11" fill="{INK}">{k}</text>')
    # path lines
    def px(p): return o + p[0] * c
    def py(p): return 6 + (n - p[1]) * c
    s.append(f'<line x1="{px(pts[0])}" y1="{py(pts[0])}" x2="{px(pts[1])}" y2="{py(pts[1])}" stroke="{GRASS}" stroke-width="2.6"/>')
    s.append(f'<line x1="{px(pts[1])}" y1="{py(pts[1])}" x2="{px(pts[2])}" y2="{py(pts[2])}" stroke="{GRASS}" stroke-width="2.6"/>')
    for (x, y, lab) in pts:
        cx, cy = o + x * c, 6 + (n - y) * c
        s.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{ORANGE}"/>')
        s.append(f'<text x="{cx+9}" y="{cy-7}" font-size="12" font-weight="800" fill="{ORANGE}">{lab}</text>')
    return svg("".join(s), o + n * c + 18, 6 + n * c + 24)


def build(chapter):
    b = []; A = b.append

    # ── HOOK ────────────────────────────────────────────────────────────
    A(big_q("A pirate's note says: \"From the old oak, walk to the spot <b>3 steps East and 2 steps "
            "North</b>. Dig.\" Just two numbers — and X marks the exact spot. How can only two numbers "
            "pin down <em>any</em> place on a whole island, a city, or even the Earth? That's the power "
            "of <b>coordinates</b>, and you're about to become a master map-maker."))
    A(kiwi("Hi explorer, it's <b>Kiwi</b>! 🗺️ This is the most adventurous geometry chapter. We'll learn "
           "to point in any <b>direction</b>, read a <b>map grid</b>, and then meet the brilliant "
           "<b>coordinate plane</b> — the idea that links shapes to numbers and runs every video game map, "
           "GPS, and graph in the world. Two numbers, infinite places. Let's explore!"))

    # ── DIRECTIONS ──────────────────────────────────────────────────────
    A(H("Directions: the compass and turns"))
    A(P("A <b>compass</b> shows the four main directions: <b>N</b>orth, <b>E</b>ast, <b>S</b>outh, "
        "<b>W</b>est. Going clockwise from North: N → E → S → W. Between them sit NE, SE, SW, NW."))
    A(figure(compass(), "The 8-point compass rose. North is up; East is right. Clockwise: N, E, S, W."))
    A(P("A handy memory phrase for the order clockwise from the top is "
        "<b>N</b>ever <b>E</b>at <b>S</b>oggy <b>W</b>eetabix (N, E, S, W). Turns are measured like "
        "angles: a <b>quarter-turn</b> is 90°, a <b>half-turn</b> is 180°, a <b>full turn</b> is 360°."))
    A(example("which way after turning?", steps([
        "You are facing <b>North</b>. You turn <b>90° clockwise</b> (to the right).",
        "Clockwise from N is E, so you now face <b>East</b>.",
        "Turn another 90° clockwise → <b>South</b>. So 180° from North is South — a half-turn faces you "
        "the opposite way!",
    ])))
    A(kiwi("Clockwise means turning the way clock hands move (N→E→S→W). Anticlockwise is the reverse "
           "(N→W→S→E). Every 90° turn hops you one direction along; 180° is always straight behind you; "
           "360° brings you right back where you started."))
    A(tryit("You face West and make a 90° turn clockwise. Which direction do you face now?",
            "Clockwise from West is North, so you now face <b>North</b>."))
    A(tryit("You face South. You turn 180°. Which way now?",
            "A half-turn flips you to the opposite direction → <b>North</b>."))

    # ── MAP GRID REFERENCES ─────────────────────────────────────────────
    A(H("Map grids: finding a place by its square"))
    A(P("Maps are covered with a <b>grid</b> of squares, with letters along the top and numbers down the "
        "side. To name a square, give its <b>column letter then row number</b> — like B3. (Letter first, "
        "always.)"))
    A(figure(grid_map(), "A map grid. The school 🏫 is in B2, the park 🌳 in D1, home 🏠 in A4."))
    A(example("read map references", steps([
        "Find the column letter first (across the top), then the row number (down the side).",
        "The school 🏫 sits in column <b>B</b>, row <b>2</b> → its reference is <b>B2</b>.",
        "The park 🌳 is column D, row 1 → <b>D1</b>. Home 🏠 is column A, row 4 → <b>A4</b>.",
    ])))
    A(tryit("On the map above, what is at reference A4?",
            "Home 🏠 (column A, row 4)."))

    # ── COORDINATE PLANE INTRO ──────────────────────────────────────────
    A(H("The big idea: the coordinate plane"))
    A(P("Map letters and numbers are good, but mathematicians use <b>numbers for both</b> directions — "
        "and that unlocks everything. We draw two number lines that cross at right angles:"))
    A(P("• The <b>x-axis</b> runs <em>across</em> (left-right), like East on a compass.<br>"
        "• The <b>y-axis</b> runs <em>up-down</em>, like North.<br>"
        "• They cross at the <b>origin</b>, the point (0, 0), marked <b>O</b>."))
    A(figure(axes_only(), "The coordinate plane: x-axis across, y-axis up, meeting at the origin O (0, 0)."))
    A(P("Any point is named by an <b>ordered pair (x, y)</b>: the x-number tells how far to go "
        "<b>across</b> first, then the y-number tells how far <b>up</b>. The order matters — that's why "
        "it's called an <em>ordered</em> pair!"))
    A(kiwi("Golden rule, never forget it: <b>x before y, across before up</b> — go along the corridor "
           "before you climb the stairs. The point (3, 2) means 'across 3, up 2', which is a totally "
           "different spot from (2, 3) ('across 2, up 3'). Order is everything."))

    # ── PLOTTING ────────────────────────────────────────────────────────
    A(H("Plotting points — across, then up"))
    A(P("To plot (4, 3): start at the origin, move <b>4 across</b> (along the x-axis), then "
        "<b>3 up</b>, and mark the spot. Let's place a few points:"))
    A(figure(coord_grid([(4, 3, "P(4,3)"), (2, 5, "Q(2,5)"), (6, 1, "R(6,1)")]),
             "Three plotted points. P is 4 across and 3 up; Q is 2 across, 5 up; R is 6 across, 1 up."))
    A(example("plot the point (4, 3)", steps([
        "Start at the origin O (0, 0).",
        "The first number is x = 4: move <b>4 units across</b> (to the right).",
        "The second number is y = 3: from there move <b>3 units up</b>.",
        "Mark the point — that's P(4, 3). Across first, up second, every time.",
    ])))
    A(tryit("Where do you end up if you plot (0, 4)?",
            "x = 0 means don't move across at all; y = 4 means go up 4. So you land <b>on the y-axis, 4 "
            "units up</b>."))

    # ── READING COORDINATES ─────────────────────────────────────────────
    A(H("Reading coordinates — what point is that?"))
    A(P("Going the other way is just as easy. To read a point's coordinates: see how far <b>across</b> "
        "it is (that's x), then how far <b>up</b> (that's y), and write (x, y)."))
    A(figure(coord_grid([(2, 3, "A"), (4, 1, "B"), (5, 5, "C")]),
             "Read each point: A is at (2, 3), B at (4, 1), C at (5, 5)."))
    A(example("read the coordinates of point A", steps([
        "Look at point A. How far across is it? <b>2</b> → x = 2.",
        "How far up is it? <b>3</b> → y = 3.",
        "So A = <b>(2, 3)</b>. Always write across-number first.",
    ])))
    A(tryit("From the figure above, what are the coordinates of point C?",
            "C is 5 across and 5 up → <b>(5, 5)</b>."))

    # ── PATHS & DISTANCE ────────────────────────────────────────────────
    A(H("Paths & distance on a grid"))
    A(P("Coordinates let us measure journeys. To find the distance along a <b>straight horizontal</b> "
        "line, subtract the x-values; along a <b>straight vertical</b> line, subtract the y-values."))
    A(figure(path_grid(), "A path from A(1,1) up to B(1,4), then across to C(5,4)."))
    A(example("how far is the path A → B → C?", steps([
        "A(1, 1) to B(1, 4): the x stays 1, so it's vertical. Distance = 4 − 1 = <b>3 units up</b>.",
        "B(1, 4) to C(5, 4): the y stays 4, so it's horizontal. Distance = 5 − 1 = <b>4 units across</b>.",
        "Total path length = 3 + 4 = <b>7 units</b>. (Like walking 3 blocks up then 4 blocks over.)",
    ])))
    A(kiwi("A surprise peek ahead: A and C are 3 up and 4 across apart. The <em>straight-line</em> "
           "shortcut from A to C (the diagonal) turns out to be exactly <b>5 units</b> — because 3, 4, 5 "
           "make a special right-triangle trio you'll meet again. The path is 7, but the crow-flies "
           "distance is 5. Geometry is full of these hidden gems! ✨"))
    A(tryit("What is the distance from (2, 1) to (2, 7) along the grid?",
            "Same x (vertical line): 7 − 1 = <b>6 units</b>."))

    # ── BLOOM LADDER ────────────────────────────────────────────────────
    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What are the four main compass directions, clockwise from North?", "North, East, South, West."),
        ("Which axis runs across (left-right)?", "The x-axis."),
        ("What is the point where the axes cross called?", "The origin, (0, 0)."),
        ("In the pair (x, y), which number do you use first?", "x — go across before up."),
        ("How many degrees is a quarter-turn?", "90°."),
    ]))
    A(practice("Understand", [
        ("You face North and turn 90° clockwise. Which way now?", "East."),
        ("Plot order: for (5, 2), do you move across 5 then up 2, or up 5 then across 2?",
         "Across 5, then up 2 (x first)."),
        ("On a map grid, is the reference written as letter-then-number or number-then-letter?",
         "Letter then number (e.g. C3)."),
        ("Where is the point (0, 0)?", "At the origin, where the two axes meet."),
        ("Is (3, 5) the same point as (5, 3)? Why?",
         "No — (3, 5) is across 3, up 5; (5, 3) is across 5, up 3. Order matters."),
    ]))
    A(practice("Apply", [
        ("You face East and turn 180°. Which direction do you face?", "West (a half-turn is the opposite way)."),
        ("Plot (3, 4): describe where it lands.", "3 across and 4 up from the origin."),
        ("Read the point that is 6 across and 0 up.", "(6, 0) — it sits on the x-axis."),
        ("Find the distance from (1, 2) to (1, 9) along the grid.", "Same x, vertical: 9 − 2 = 7 units."),
        ("Find the distance from (2, 5) to (8, 5) along the grid.", "Same y, horizontal: 8 − 2 = 6 units."),
        ("You face South and turn 90° anticlockwise. Which way now?",
         "Anticlockwise from South is East… check: clockwise S→W, so anticlockwise S→E. You face East."),
    ]))
    A(practice("Analyze", [
        ("A square has corners at (1, 1), (4, 1) and (4, 4). What is the fourth corner?",
         "(1, 4) — it completes the square (same left x as the first, same top y as the third)."),
        ("Start at (2, 3). Move 3 right and 2 up. Where do you end?",
         "x: 2 + 3 = 5; y: 3 + 2 = 5 → (5, 5)."),
        ("A rectangle has corners (0, 0), (5, 0), (5, 3). Find the fourth corner and its perimeter.",
         "Fourth corner (0, 3). It's 5 wide and 3 tall → perimeter = 2 × (5 + 3) = 16 units."),
        ("You face North, turn 90° clockwise three times. Which way do you face?",
         "N→E→S→W. After three 90° clockwise turns you face West."),
    ]))
    A(practice("Create", [
        ("Plot any 3 points that form a triangle and list their coordinates.",
         "Any three non-line points, e.g. (1, 1), (5, 1), (3, 4)."),
        ("Write treasure-hunt directions using a start point and compass turns that lead to (4, 2). "
         "What are your directions?",
         "E.g. 'Start at origin, walk 4 steps East, then 2 steps North.' (Many correct routes.)"),
        ("Design a small square on the grid (give all four corners) and find its area.",
         "E.g. (2, 2), (5, 2), (5, 5), (2, 5): side = 3 → area = 3 × 3 = 9 square units."),
    ]))

    # ── CHALLENGE ───────────────────────────────────────────────────────
    A(challenge(
        P("A robot starts at the origin <b>(0, 0)</b> facing <b>East</b>. It follows this program: "
          "<b>move 3, turn left (90° anticlockwise), move 3, turn left, move 1, turn left, move 1</b>. "
          "Track it step by step. Where does the robot finish, and which direction is it facing? "
          "(Hint: facing East, 'forward' adds to x; after a left turn it faces North and 'forward' adds "
          "to y; the next left faces West, then South.)") +
        tryit("Walk the robot through, updating its position and heading at each step.",
              "Start (0,0) facing E. Move 3 → (3,0), still E. Turn left → faces N. Move 3 → (3,3). "
              "Turn left → faces W. Move 1 → (2,3). Turn left → faces S. Move 1 → (2,2). "
              "<b>The robot finishes at (2, 2), facing South.</b> You just ran a coordinate-geometry "
              "program — the same idea behind every game character and drawing robot! 🤖")))

    A(kiwi("Fantastic — you can read a compass, navigate a map grid, and plot, read and travel between "
           "points on the coordinate plane with confidence. That completes our geometry expedition: "
           "angles, triangles, polygons, area, circles, solids, symmetry, and now maps & coordinates. "
           "You see shapes and space the way a mathematician does now. Onward, explorer! 🧭"))

    chapter("Part 5 · Shapes, Space & Maps", 17, "Maps, Directions & Coordinates",
            "Geometry · Map Makers", "".join(b))
