#!/usr/bin/env python3
"""L3 Chapter 20 — Logic & Reasoning (Combinatorics · Sock Drawer Logic).
The PIGEONHOLE surprise (sock drawer), logic-grid deduction, ranking & position,
clocks (angles, gently) & calendars (day-of-week by counting), blood relations
(inline family tree), and working backwards. Every count, angle and day is
computed/verified in Python."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, clock, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# -- local figure: a sock drawer with mixed coloured socks ----------------
def sock_drawer(colors):
    """colors = list of hex; draws a drawer of socks in those colours."""
    n = len(colors); perrow = 6
    rows = (n + perrow - 1) // perrow
    W = 60 + perrow * 44
    Hh = 54 + rows * 60
    s = [f'<rect x="14" y="30" width="{W-28}" height="{Hh-44}" rx="12" '
         f'fill="{GOLD}10" stroke="{INK}" stroke-width="2.4"/>',
         f'<rect x="{W/2-26:.0f}" y="22" width="52" height="14" rx="6" '
         f'fill="{INK}" opacity=".7"/>']
    for i, c in enumerate(colors):
        r, col = divmod(i, perrow)
        x = 40 + col * 44; y = 56 + r * 60
        # a simple sock shape
        s.append(f'<path d="M{x},{y} l16,0 l0,30 q0,8 -8,10 l-18,5 q-9,2 -10,-7 '
                 f'q0,-6 7,-9 l11,-5 Z" fill="{c}cc" stroke="{c}" stroke-width="2"/>')
    return svg("".join(s), W, Hh)


# -- local figure: a 3x3 logic grid (deduction table) ---------------------
def logic_grid(rows, cols, marks):
    """rows, cols = lists of labels. marks = dict {(r,c): 'O'|'X'} (O = yes, X = no)."""
    cw = 56; rh = 40; x0 = 96; y0 = 44
    W = x0 + len(cols) * cw + 12
    Hh = y0 + len(rows) * rh + 12
    s = []
    for j, c in enumerate(cols):
        s.append(f'<text x="{x0+j*cw+cw/2:.0f}" y="{y0-12}" text-anchor="middle" '
                 f'font-size="12.5" font-weight="800" fill="{SKY}">{c}</text>')
    for i, r in enumerate(rows):
        s.append(f'<text x="{x0-10}" y="{y0+i*rh+rh/2+5:.0f}" text-anchor="end" '
                 f'font-size="12.5" font-weight="800" fill="{BERRY}">{r}</text>')
    for i in range(len(rows)):
        for j in range(len(cols)):
            x = x0 + j * cw; y = y0 + i * rh
            s.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{rh}" fill="#fff" '
                     f'stroke="#cfc9bf" stroke-width="1.4"/>')
            mk = marks.get((i, j))
            if mk == "O":
                s.append(f'<circle cx="{x+cw/2:.0f}" cy="{y+rh/2:.0f}" r="11" '
                         f'fill="none" stroke="{GRASS}" stroke-width="3"/>')
            elif mk == "X":
                s.append(f'<text x="{x+cw/2:.0f}" y="{y+rh/2+7:.0f}" text-anchor="middle" '
                         f'font-size="20" font-weight="800" fill="{BERRY}">&#215;</text>')
    return svg("".join(s), W, Hh)


# -- local figure: a ranking line (positions in a row) --------------------
def rank_line(n, top_pos=None, bot_pos=None, target_label="?"):
    """A row of n people; optionally mark a target at top_pos from left."""
    bw = 38; gap = 8; x0 = 24
    W = x0 + n * (bw + gap) + 60
    s = [f'<text x="14" y="30" font-size="12" font-weight="800" fill="{SKY}">front</text>',
         f'<text x="{W-50}" y="30" font-size="12" font-weight="800" fill="{BERRY}">back</text>']
    for i in range(n):
        x = x0 + i * (bw + gap)
        is_t = (top_pos is not None and i == top_pos - 1)
        col = ORANGE if is_t else "#cfc9bf"
        fill = f"{ORANGE}22" if is_t else "#f3f1ec"
        s.append(f'<rect x="{x}" y="40" width="{bw}" height="{bw}" rx="8" fill="{fill}" '
                 f'stroke="{col}" stroke-width="2.2"/>')
        lab = str(i + 1)
        s.append(f'<text x="{x+bw/2:.0f}" y="{40+bw/2+5:.0f}" text-anchor="middle" '
                 f'font-size="13" font-weight="700" fill="{INK if not is_t else ORANGE}">{lab}</text>')
        if is_t:
            s.append(f'<text x="{x+bw/2:.0f}" y="34" text-anchor="middle" font-size="12" '
                     f'font-weight="800" fill="{ORANGE}">{target_label}</text>')
    return svg("".join(s), W, 96)


# -- local figure: a small family tree (inline) ---------------------------
def family_tree():
    def box(x, y, name, col, w=92):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="32" rx="9" '
                f'fill="{col}1f" stroke="{col}" stroke-width="2"/>'
                f'<text x="{x+w/2}" y="{y+21}" text-anchor="middle" font-size="13" '
                f'font-weight="700" fill="{col}">{name}</text>')
    L = INK; s = []
    s.append(box(78, 12, "Grandpa", SKY))
    s.append(box(196, 12, "Grandma", BERRY))
    s.append(f'<line x1="170" y1="28" x2="196" y2="28" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="183" y1="28" x2="183" y2="58" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="104" y1="58" x2="300" y2="58" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="104" y1="58" x2="104" y2="72" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="300" y1="58" x2="300" y2="72" stroke="{L}" stroke-width="2"/>')
    s.append(box(58, 72, "Dad", GRASS))
    s.append(box(172, 72, "Mom", ORANGE))
    s.append(box(266, 72, "Aunt", PURPLE, 84))
    s.append(f'<line x1="150" y1="88" x2="172" y2="88" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="161" y1="88" x2="161" y2="118" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="98" y1="118" x2="224" y2="118" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="98" y1="118" x2="98" y2="132" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="224" y1="118" x2="224" y2="132" stroke="{L}" stroke-width="2"/>')
    s.append(box(52, 132, "Me", BERRY))
    s.append(box(176, 132, "Sister", SKY, 92))
    return svg("".join(s), 380, 178)


# -- local figure: a working-backwards "machine" chain --------------------
def machine_chain(start_label, ops, end_label):
    """ops = list of strings like 'x2', '+6'. Draws start -> [op] -> ... -> end."""
    bw = 70; x = 12; s = []
    s.append(f'<rect x="{x}" y="22" width="{bw}" height="44" rx="11" fill="{SKY}18" '
             f'stroke="{SKY}" stroke-width="2"/>')
    s.append(f'<text x="{x+bw/2}" y="49" text-anchor="middle" font-size="16" '
             f'font-weight="800" fill="{INK}">{start_label}</text>')
    x += bw
    for op in ops:
        s.append(f'<text x="{x+18}" y="49" text-anchor="middle" font-size="20" '
                 f'fill="{GRASS}">&#8594;</text>')
        x += 36
        s.append(f'<rect x="{x}" y="26" width="56" height="36" rx="9" fill="{ORANGE}18" '
                 f'stroke="{ORANGE}" stroke-width="2"/>')
        s.append(f'<text x="{x+28}" y="49" text-anchor="middle" font-size="15" '
                 f'font-weight="800" fill="{ORANGE}">{op}</text>')
        x += 56
    s.append(f'<text x="{x+18}" y="49" text-anchor="middle" font-size="20" '
             f'fill="{GRASS}">&#8594;</text>')
    x += 36
    s.append(f'<rect x="{x}" y="22" width="{bw}" height="44" rx="11" fill="{BERRY}18" '
             f'stroke="{BERRY}" stroke-width="2"/>')
    s.append(f'<text x="{x+bw/2}" y="49" text-anchor="middle" font-size="16" '
             f'font-weight="800" fill="{INK}">{end_label}</text>')
    return svg("".join(s), x + bw + 12, 88)


def build(chapter):
    b = []; A = b.append

    A(big_q("Your sock drawer is a jumble of <b>black</b> and <b>white</b> socks, and the room is "
            "<b>pitch dark</b>. You can't see a thing. What is the <em>smallest</em> number of "
            "socks you must grab to be <b>100% sure</b> you're holding a matching pair? The answer "
            "is wonderfully small &mdash; and it reveals one of the most powerful ideas in all of "
            "mathematics."))
    A(kiwi("Hello, super-sleuth &mdash; <b>Kiwi</b> here! &#128373; This is the reasoning chapter, "
           "and it's pure thinking joy: no formulas to memorise, just careful logic. We'll meet a "
           "surprising guarantee called the <b>Pigeonhole Principle</b>, solve deduction grids, "
           "untangle who-ranks-where, read clocks and calendars, sort out families, and learn to "
           "work <em>backwards</em>. Go slowly, one clue at a time, and write down what you know."))

    # ===================== A . PIGEONHOLE =====================
    A(H("Part A &middot; The sock-drawer surprise (Pigeonhole)"))
    A(P("Back to the dark room. There are only <b>2 colours</b> of sock. Let's think about the "
        "<em>worst</em> possible luck. You pull one sock &mdash; say black. You pull another "
        "&mdash; the meanest luck gives you white. Now you hold one of each, still no pair. But "
        "the <b>third</b> sock <em>must</em> be black or white &mdash; either way it matches one "
        "you already hold!"))
    A(figure(sock_drawer([INK, "#cfcfcf", INK, "#cfcfcf", INK, "#cfcfcf", INK, "#cfcfcf"]),
             "Only 2 colours. Grab 3 socks and a matching pair is GUARANTEED."))
    A(example("why 3 socks guarantee a pair", steps([
        "There are only <b>2</b> colours (think of them as 2 &ldquo;boxes&rdquo;).",
        "Each sock you grab must go into one of those 2 boxes.",
        "Grab <b>3</b> socks for 2 boxes &mdash; by sheer force, some box gets <b>2</b> socks. "
        "Those 2 are the same colour: a pair!",
        "So <b>3</b> is the magic number. Not 2 (you might get one of each), but 3 makes a pair "
        "<em>certain</em>. &#10003;",
    ])))
    A(kiwi("That's the <b>Pigeonhole Principle</b>, and it's beautifully simple: <em>if you put "
           "more items than boxes, some box must hold at least two items.</em> "
           "More pigeons than holes &rarr; some hole is shared. It <b>guarantees</b> a result "
           "without you knowing anything about which sock is which &mdash; that's the surprise!"))
    A(P("Change the numbers and the idea still works. With <b>3</b> colours of sock, the worst "
        "luck gives one of each (3 socks, no pair), so the <b>4th</b> sock guarantees a pair. The "
        "rule: <b>(number of colours) + 1</b> socks always guarantees a matching pair."))
    A(example("a trickier pigeonhole: sharing a birth month", steps([
        "There are <b>12</b> months &mdash; think of them as 12 boxes.",
        "Put <b>13</b> people into those 12 month-boxes (by their birth month).",
        "13 people, 12 boxes &rarr; some month-box holds at least 2 people.",
        "So in <em>any</em> group of <b>13</b> people, at least two share a birth month &mdash; "
        "guaranteed, every time. &#127881;",
    ])))
    A(tryit("A drawer has socks of <b>4</b> colours, all mixed up in the dark. How many socks must "
            "you grab to be sure of a matching pair?",
            "Worst luck = one of each colour (4 socks, no pair), so the next one matches: "
            "<b>5</b> socks. (Rule: colours + 1.)"))

    # ===================== B . LOGIC GRIDS =====================
    A(H("Part B &middot; Logic-grid deduction"))
    A(P("A <b>logic puzzle</b> gives you clues and asks you to match things up &mdash; like "
        "&ldquo;who owns which pet?&rdquo; A <b>grid</b> keeps your thinking tidy: mark "
        "&#9711; for a definite YES and &#215; for a definite NO. Each clue lets you fill in some "
        "marks, and YES in one cell forces NO across the rest of that row and column."))
    A(P("Three friends &mdash; <b>Amy, Ben, Cara</b> &mdash; each own one pet: a <b>cat</b>, a "
        "<b>dog</b>, or a <b>fish</b>. Clues: <b>(1)</b> Ben owns the dog. <b>(2)</b> Amy does not "
        "own the cat."))
    A(figure(logic_grid(["Amy", "Ben", "Cara"], ["Cat", "Dog", "Fish"],
                       {(1, 1): "O", (1, 0): "X", (1, 2): "X",  # Ben dog
                        (0, 0): "X",                              # Amy not cat
                        (0, 1): "X", (2, 1): "X"}),               # nobody else has dog
             "Clue 1 fixes Ben=Dog (X out the rest of his row/column). Clue 2: Amy is not Cat."))
    A(example("finishing the deduction", steps([
        "<b>Clue 1:</b> Ben owns the Dog &rarr; &#9711; at Ben/Dog. So Ben is not Cat or Fish, "
        "and nobody else owns the Dog (&#215; down the Dog column).",
        "<b>Clue 2:</b> Amy is not the Cat (&#215; at Amy/Cat). The only pets left for Amy are Dog "
        "or Fish &mdash; but Dog is taken, so <b>Amy owns the Fish</b>.",
        "<b>What's left:</b> the Cat must belong to <b>Cara</b> (the last person, the last pet).",
        "Answer: Ben&ndash;Dog, Amy&ndash;Fish, Cara&ndash;Cat. Every clue fits, and it's the "
        "only solution. &#10003;",
    ])))
    A(kiwi("The grid's secret: once you write &#9711; (YES) in a cell, immediately put &#215; "
           "across the rest of that <em>row</em> and that <em>column</em> &mdash; one person, one "
           "pet. Then re-read the clues; new YESes appear, and the puzzle unravels itself."))
    A(tryit("Three children &mdash; Raj, Sam, Tia &mdash; like one fruit each: apple, banana, "
            "cherry. Sam likes the banana, and Raj does not like the apple. Who likes what?",
            "Sam = banana. Raj is not apple and banana is taken, so Raj = cherry. That leaves "
            "Tia = apple."))

    # ===================== C . RANKING & POSITION =====================
    A(H("Part C &middot; Ranking & position"))
    A(P("A queue puzzle: <b>Sam is 9th from the front</b> and <b>38th from the back</b> of a line. "
        "How many people are in the line? The trap is to add 9 + 38 = 47 &mdash; but that counts "
        "<b>Sam twice</b> (once from each end)."))
    A(figure(rank_line(12, top_pos=4, target_label="Sam"),
             "Counting from front AND back both include the marked person -- so subtract 1."))
    A(example("the ranking rule", steps([
        "Sam is counted in the &ldquo;9 from the front&rdquo; <em>and</em> in the &ldquo;38 from "
        "the back&rdquo; &mdash; that's Sam double-counted.",
        "Total = (position from front) + (position from back) &minus; 1.",
        "Total = 9 + 38 &minus; 1 = <b>46</b> people. The &ldquo;&minus;1&rdquo; removes the "
        "double count. &#10003;",
    ])))
    A(kiwi("Position rule: <b>front-rank + back-rank &minus; 1 = total</b>. The &minus;1 is "
           "because the person themselves is counted from both directions. The same idea fixes "
           "&ldquo;how many between?&rdquo; puzzles &mdash; always check who's being counted "
           "twice."))
    A(tryit("In a row, Meena is 7th from the left and 12th from the right. How many children are "
            "in the row?",
            "7 + 12 &minus; 1 = <b>18</b> children."))

    # ===================== D . CLOCKS & ANGLES =====================
    A(H("Part D &middot; Clocks, angles & calendars"))
    A(P("A clock face is a circle, so all the way round is <b>360&deg;</b>. There are 12 hour "
        "marks, so the gap between two neighbouring numbers is 360 &divide; 12 = <b>30&deg;</b>. "
        "That single fact lets us measure the angle between the hands."))
    A(figure(clock(3, 0), "At 3:00 the hands are 3 gaps apart: 3 x 30 = 90 degrees."))
    A(example("the angle between the hands at 3:00", steps([
        "The hour hand is on 3, the minute hand on 12 &mdash; that's <b>3 gaps</b> apart.",
        "Each gap is 30&deg;, so the angle = 3 &times; 30 = <b>90&deg;</b> (a perfect right "
        "angle!).",
    ])))
    A(figure(clock(6, 0), "At 6:00 the hands point opposite ways: 6 x 30 = 180 degrees (a straight line)."))
    A(kiwi("Quick angle facts: 12:00 &rarr; the hands overlap, <b>0&deg;</b>. 3:00 and 9:00 "
           "&rarr; <b>90&deg;</b> (right angle). 6:00 &rarr; <b>180&deg;</b> (straight line). "
           "Between numbers the hour hand creeps along too &mdash; it moves a little every minute "
           "&mdash; which is why 3:30 isn't exactly 90&deg;."))
    A(tryit("What is the angle between the clock hands at <b>9:00</b>?",
            "9 and 12 are 3 gaps apart, so 3 &times; 30 = <b>90&deg;</b> (a right angle)."))

    A(H("Day-of-the-week jumps"))
    A(P("The 7 days repeat forever, so jumping exactly <b>7</b> days (or 14, or 21&hellip;) lands "
        "you on the <em>same</em> day. To find a future day, divide the jump by 7 and only the "
        "<b>remainder</b> matters."))
    A(example("what day is 10 days after Monday?", steps([
        "10 = 7 + 3. The 7 brings us right back to <b>Monday</b>.",
        "Then count on the remainder, 3: Monday &rarr; Tue (1) &rarr; Wed (2) &rarr; <b>Thu</b> "
        "(3).",
        "So 10 days after Monday is a <b>Thursday</b>. &#10003;",
    ])))
    A(kiwi("Calendar trick: only the <b>remainder after dividing by 7</b> changes the day. "
           "15 days ahead? 15 = 7 + 7 + 1, remainder 1, so just <b>1 day</b> later than today. "
           "Months vary in length (30 or 31 days; February has 28, or 29 in a leap year)."))
    A(tryit("Today is Friday. Your birthday is in exactly <b>15</b> days. On which day of the "
            "week is it?",
            "15 = 7 + 7 + 1, remainder 1, so 1 day after Friday &rarr; <b>Saturday</b>."))

    # ===================== E . BLOOD RELATIONS =====================
    A(H("Part E &middot; Family puzzles (who is who?)"))
    A(P("A <b>relationship</b> puzzle describes people and asks how two are related. The best tool "
        "is a little <b>family tree</b> &mdash; a line going <em>down</em> means &ldquo;parent "
        "of&rdquo;, and a line <em>across</em> between two boxes means &ldquo;married to&rdquo;."))
    A(figure(family_tree(),
             "Down = parent of. Across = married to. Read relationships straight off the picture."))
    A(kiwi("Handy word-list: parent's <b>brother</b> = <b>uncle</b>, parent's <b>sister</b> = "
           "<b>aunt</b>, aunt/uncle's child = <b>cousin</b>, your brother's or sister's child = "
           "your <b>nephew</b> (boy) / <b>niece</b> (girl), and your parent's parent = "
           "<b>grandparent</b>."))
    A(example("&ldquo;The man's mother is the only daughter of my mother.&rdquo; (a woman is speaking)", steps([
        "Find <b>the only daughter of my mother</b>. The speaker is the woman, so her mother's "
        "only daughter is the <b>woman herself</b>.",
        "The sentence says the man's mother <em>is</em> that person &mdash; so the man's mother is "
        "the <b>woman</b>.",
        "If the woman is the man's mother, she is his <b>mother</b>. &#10003; (Tip: phrases like "
        "&ldquo;the only daughter of my mother&rdquo; often point straight back at the speaker.)",
    ])))
    A(tryit("Pointing to a boy, Mr Suresh says, &ldquo;He is the son of the <b>only son</b> of my "
            "mother.&rdquo; How is Suresh related to the boy?",
            "The only son of Suresh's mother is <b>Suresh himself</b>, so the boy is Suresh's son "
            "&mdash; Suresh is the boy's <b>father</b>."))

    # ===================== F . WORKING BACKWARDS =====================
    A(H("Part F &middot; Working backwards"))
    A(P("Some puzzles tell you the <em>end</em> and ask for the <em>start</em>. The trick is to "
        "<b>run the steps in reverse</b>, turning each operation into its opposite: undo "
        "<b>&times;</b> with <b>&divide;</b>, and undo <b>+</b> with <b>&minus;</b> &mdash; in the "
        "<em>backwards</em> order."))
    A(figure(machine_chain("?", ["x2", "+6"], "20"),
             "Forwards: think of a number, double it, add 6, get 20. Work backwards to find it."))
    A(example("number machine: double, then add 6, gives 20", steps([
        "Run it <em>backwards</em>, last step first. The last thing done was <b>+6</b>; undo it: "
        "20 &minus; 6 = <b>14</b>.",
        "The step before was <b>&times;2</b>; undo it: 14 &divide; 2 = <b>7</b>.",
        "So the starting number was <b>7</b>. Check forwards: 7 &times; 2 = 14, + 6 = 20. "
        "&#10003;",
    ])))
    A(kiwi("Working backwards is a real problem-solving superpower &mdash; the same one champions "
           "use. Whenever you know the finish and want the start, <em>reverse the journey</em> and "
           "flip every operation to its opposite."))
    A(tryit("I think of a number, <b>add 5</b>, then <b>multiply by 3</b>, and get <b>36</b>. "
            "What was my number?",
            "Backwards: undo &times;3 first &rarr; 36 &divide; 3 = 12; undo +5 &rarr; 12 &minus; 5 "
            "= <b>7</b>. (Check: 7 + 5 = 12, &times; 3 = 36. &#10003;)"))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now climb the detective ladder"))
    A(P("Match each puzzle to its tool: pigeonhole, a grid, the position rule, a clock fact, a "
        "day-jump, a family tree, or working backwards. Peek only after a real try!"))

    A(practice("Remember", [
        ("Socks come in 2 colours, mixed in the dark. How many must you grab to be sure of a "
         "pair?", "3 socks."),
        ("In a clock face, how many degrees is the gap between two neighbouring numbers?",
         "30 degrees (360 / 12)."),
        ("Your parent's sister is called your ____.", "Aunt."),
        ("To undo &ldquo;multiply by 4&rdquo; when working backwards, what do you do?",
         "Divide by 4."),
        ("How many days in a week make you land on the same day again?", "7 days."),
    ]))
    A(practice("Understand", [
        ("A drawer has socks of 3 colours, mixed in the dark. How many must you grab to be sure "
         "of a matching pair?", "Colours + 1 = 3 + 1 = 4 socks."),
        ("What is the angle between the clock hands at 6:00?",
         "6 gaps apart, 6 &times; 30 = 180&deg; (a straight line)."),
        ("Three friends Ann, Bob, Cy each pick one drink: tea, milk, juice. Bob picks milk and "
         "Ann does not pick tea. Who picks what?",
         "Bob = milk; Ann is not tea so Ann = juice; that leaves Cy = tea."),
        ("Today is Wednesday. What day is it after exactly 7 days?",
         "The same day &mdash; Wednesday."),
        ("A number, doubled, gives 18. Working backwards, what was the number?",
         "Undo &times;2: 18 &divide; 2 = 9."),
    ]))
    A(practice("Apply", [
        ("In a class of 13 children, must at least two share the same birth month? Explain.",
         "Yes &mdash; 13 children into 12 month-boxes means some month has at least 2 "
         "(pigeonhole)."),
        ("Riya is 8th from the front and 15th from the back of a queue. How many people are in "
         "the queue?", "8 + 15 &minus; 1 = 22 people."),
        ("What is the angle between the clock hands at 9:00?",
         "3 gaps apart, 3 &times; 30 = 90&deg; (a right angle)."),
        ("Today is Monday. What day is it after 9 days?",
         "9 = 7 + 2, remainder 2: Monday &rarr; Tue &rarr; Wed. It is a Wednesday."),
        ("I think of a number, multiply by 5, then subtract 4, and get 31. What is the number?",
         "Backwards: 31 + 4 = 35, then 35 &divide; 5 = 7."),
    ]))
    A(practice("Analyze", [
        ("A box holds many red, blue and green balls mixed in the dark. What is the smallest "
         "number you must take to be sure of <b>two of the same colour</b>?",
         "3 colours, so worst luck is one of each (3 balls); the 4th must repeat a colour &rarr; "
         "4 balls."),
        ("Pointing to a woman in a photo, a man says &ldquo;She is the daughter of my "
         "grandfather's only son.&rdquo; The man has no brothers. How is the woman related to him?",
         "His grandfather's only son is the man's father; the father's daughter (the man has no "
         "brothers, but could have a sister) is the man's <b>sister</b>."),
        ("In a row of children, Dev is 10th from the left. After he swaps places with Bina, who "
         "was 9th from the right, Dev is now 15th from the left. How many children are in the row?",
         "Dev moved into Bina's spot, which is 15th from the left AND 9th from the right. "
         "Total = 15 + 9 &minus; 1 = 23 children."),
        ("Megha will be 53 in the year 2019. How old was she in 1998?",
         "From 1998 to 2019 is 21 years, so she was 53 &minus; 21 = 32 in 1998."),
        ("A girl spent <b>half</b> her pocket money on a book, then &#8377;10 on a pen, and had "
         "&#8377;5 left. How much did she start with? (Work backwards.)",
         "Before the pen she had 5 + 10 = &#8377;15, which was half her money, so she started "
         "with 15 &times; 2 = &#8377;30."),
    ]))
    A(practice("Create", [
        ("Invent your own pigeonhole question whose answer is &ldquo;5 socks&rdquo;. (Hint: how "
         "many colours?)",
         "Use 4 colours: worst luck is one of each (4), so the 5th guarantees a pair &mdash; "
         "4 + 1 = 5."),
        ("Make a working-backwards riddle whose answer is the number 10. Write the riddle and the "
         "answer.",
         "Example: &ldquo;I think of a number, multiply by 3, add 2, and get 32.&rdquo; "
         "Backwards: 32 &minus; 2 = 30, &divide; 3 = 10. Any reversible chain works."),
        ("Draw a logic grid for 3 people and 3 hobbies, write 2 clues, and give the unique "
         "answer.",
         "Example: Pia/Quin/Rio like reading/drawing/dancing; clue 1 Quin dances, clue 2 Pia "
         "doesn't read &rarr; Pia draws, Rio reads."),
        ("Write a &ldquo;day-of-the-week&rdquo; puzzle whose answer is <b>Sunday</b>. "
         "(Hint: pick a start day and a number of days to jump.)",
         "Example: &ldquo;Today is Thursday; what day is it in 10 days?&rdquo; 10 = 7 + 3, "
         "remainder 3: Thu &rarr; Fri &rarr; Sat &rarr; Sun. Any jump that lands on Sunday "
         "works."),
    ]))

    A(challenge(
        P("&#11088; <b>The Pigeonhole Party.</b> At a birthday party there are <b>13 children</b>. "
          "(a) Explain why at least <b>two</b> of them must share the same birth month. (b) The "
          "party started at <b>4:30</b> and lasted <b>2 hours 45 minutes</b>. What time did it "
          "end, and what is the angle between the clock hands at the <em>start</em> time of "
          "4:30 &mdash; well, let's keep it friendly: what is the angle at exactly <b>3:00</b>, "
          "which the clock passed earlier that afternoon?") +
        tryit("Use pigeonhole for (a); add the time and use the 30&deg;-per-gap fact for (b).",
              "(a) 13 children into only 12 possible birth months &mdash; by the Pigeonhole "
              "Principle some month must hold at least 2 children, so two share a birth month. "
              "(b) End time: 4:30 + 2 h = 6:30, + 45 min = <b>7:15</b>. Angle at 3:00: the hands "
              "are 3 gaps apart, 3 &times; 30 = <b>90&deg;</b> (a right angle). &#10003;")))

    A(kiwi("Brilliant detective work! &#127881; You now wield the <b>Pigeonhole Principle</b> "
           "(more pigeons than holes &rarr; a guaranteed pair), logic grids, the position rule, "
           "clock angles, day-jumps, family trees, and working backwards &mdash; the very "
           "reasoning toolkit Olympiad champions use. Last stop on our climb: becoming "
           "<b>data detectives</b>, finding the stories hidden inside averages and graphs. "
           "&#128202;"))

    chapter("Part 6 · Counting, Chance & Logic", 20, "Logic & Reasoning",
            "Combinatorics · Sock Drawer Logic", "".join(b))
