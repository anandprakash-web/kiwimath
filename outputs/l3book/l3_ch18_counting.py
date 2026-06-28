#!/usr/bin/env python3
"""L3 Chapter 18 — Smart Counting & Combinations (Combinatorics · Smart Counting).
Bridges from Level 2 counting (multiply choices, list pairs) and climbs into the
counting principle for many stages, systematic listing, arrangements (order matters)
vs selections (order doesn't), the handshake / n-choose-2 countdown, and forming
numbers from digit cards. Every count is ENUMERATED in Python to be sure."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, array_dots, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# -- local figure: a left-to-right choice tree ------------------------------
def choice_tree(trunk, branches, leaves):
    """trunk = root label; branches = list of (label,color); leaves = list of lists,
    one per branch, each a list of (label,color). Draws a tidy left-right tree."""
    rowh = 40
    total = sum(len(lv) for lv in leaves)
    Hh = max(total * rowh + 18, 110)
    xr, xb, xl = 22, 132, 250
    cyr = Hh / 2
    s = [f'<circle cx="{xr}" cy="{cyr:.0f}" r="15" fill="{INK}"/>',
         f'<text x="{xr}" y="{cyr+5:.0f}" text-anchor="middle" font-size="12" '
         f'font-weight="800" fill="#fff">{trunk}</text>']
    ys_all, y = [], 26
    for lv in leaves:
        ys = []
        for _ in lv:
            ys.append(y); y += rowh
        ys_all.append(ys)
    for bi, (blab, bcol) in enumerate(branches):
        ys = ys_all[bi]; cyb = sum(ys) / len(ys)
        s.append(f'<line x1="{xr+15}" y1="{cyr:.0f}" x2="{xb-16}" y2="{cyb:.0f}" '
                 f'stroke="{bcol}" stroke-width="2.2"/>')
        s.append(f'<rect x="{xb-16}" y="{cyb-14:.0f}" width="32" height="28" rx="7" '
                 f'fill="{bcol}22" stroke="{bcol}" stroke-width="2"/>')
        s.append(f'<text x="{xb}" y="{cyb+5:.0f}" text-anchor="middle" font-size="13" '
                 f'font-weight="800" fill="{bcol}">{blab}</text>')
        for li, (llab, lcol) in enumerate(leaves[bi]):
            ly = ys[li]
            s.append(f'<line x1="{xb+16}" y1="{cyb:.0f}" x2="{xl-6}" y2="{ly:.0f}" '
                     f'stroke="{lcol}" stroke-width="1.7"/>')
            s.append(f'<rect x="{xl-6}" y="{ly-13:.0f}" width="150" height="26" rx="7" '
                     f'fill="{lcol}18" stroke="{lcol}" stroke-width="1.5"/>')
            s.append(f'<text x="{xl+69}" y="{ly+5:.0f}" text-anchor="middle" font-size="12" '
                     f'font-weight="700" fill="{INK}">{llab}</text>')
    return svg("".join(s), 410, Hh)


# -- local figure: a row of "slots" with the number of choices in each ------
def slot_row(slots, caption_cols=True):
    """slots = list of (label, count, color). Draws boxes with the count inside
    and x signs between, then the product."""
    bw, gap, x = 96, 46, 12
    s = []
    prod = 1
    for i, (lab, cnt, col) in enumerate(slots):
        prod *= cnt
        s.append(f'<rect x="{x}" y="22" width="{bw}" height="58" rx="11" '
                 f'fill="{col}14" stroke="{col}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+bw/2}" y="14" text-anchor="middle" font-size="12" '
                 f'font-weight="800" fill="{col}">{lab}</text>')
        s.append(f'<text x="{x+bw/2}" y="60" text-anchor="middle" font-size="30" '
                 f'font-weight="800" fill="{INK}">{cnt}</text>')
        if caption_cols:
            s.append(f'<text x="{x+bw/2}" y="96" text-anchor="middle" font-size="11" '
                     f'fill="{INK}">choices</text>')
        x += bw
        if i < len(slots) - 1:
            s.append(f'<text x="{x+gap/2}" y="60" text-anchor="middle" font-size="26" '
                     f'font-weight="800" fill="{GRASS}">&#215;</text>')
            x += gap
    s.append(f'<text x="{x+18}" y="60" text-anchor="middle" font-size="26" '
             f'font-weight="800" fill="{GRASS}">=</text>')
    s.append(f'<text x="{x+72}" y="62" text-anchor="middle" font-size="32" '
             f'font-weight="800" fill="{ORANGE}">{prod}</text>')
    return svg("".join(s), x + 120, 104)


# -- local figure: the handshake / pairs polygon with connecting chords -----
def pair_chords(n, names=None):
    """n people on a circle, every pair joined -> counts n-choose-2 chords."""
    import math
    cx, cy, r = 130, 110, 78
    pts = []
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    s = []
    cols = [SKY, BERRY, GRASS, ORANGE, PURPLE, GOLD]
    for i in range(n):
        for j in range(i + 1, n):
            s.append(f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" '
                     f'x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" '
                     f'stroke="{ORANGE}" stroke-width="1.7" opacity=".75"/>')
    for i, (x, y) in enumerate(pts):
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="{cols[i%6]}" />')
        lab = names[i] if names else chr(65 + i)
        s.append(f'<text x="{x:.0f}" y="{y+5:.0f}" text-anchor="middle" font-size="14" '
                 f'font-weight="800" fill="#fff">{lab}</text>')
    return svg("".join(s), 260, 220)


# -- local figure: a tidy row of result chips -------------------------------
def chip_row(items, col):
    bw = 94
    s = []
    for i, p in enumerate(items):
        s.append(f'<rect x="{12+i*bw}" y="14" width="{bw-10}" height="40" rx="9" '
                 f'fill="{col}14" stroke="{col}" stroke-width="1.8"/>')
        s.append(f'<text x="{12+i*bw+(bw-10)/2:.0f}" y="40" text-anchor="middle" '
                 f'font-size="16" font-weight="800" fill="{INK}">{p}</text>')
    return svg("".join(s), 12 + len(items) * bw, 70)


def build(chapter):
    b = []; A = b.append

    A(big_q("A cafe offers <b>5 milkshake flavours</b> and <b>4 toppings</b>. You happily think "
            "&ldquo;I'll try a different shake-and-topping every day.&rdquo; How many days can you "
            "go before you <em>must</em> repeat? And here's the shocker: with just a few more "
            "choices you'd be busy for <b>years</b>. By the end of this chapter you'll count "
            "enormous possibilities <em>without listing a single one</em>."))
    A(kiwi("Welcome back, explorer! It's <b>Kiwi</b>. &#129518; In Level 2 you learned to count "
           "outfits by multiplying choices, and to list pairs without missing any. Now we go "
           "<b>much</b> further: counting across <em>many</em> stages, telling apart when "
           "<b>order matters</b> from when it doesn't, and meeting the famous <b>handshake "
           "puzzle</b>. The golden idea stays simple &mdash; be <b>organised</b>, and let "
           "multiplication do the heavy lifting."))

    # -- recap + the counting principle, generalised -------------------------
    A(H("Quick recap: choices that follow each other get multiplied"))
    A(P("Remember the rule from Level 2 &mdash; the <b>Counting Principle</b>: if one choice can be "
        "made in <em>a</em> ways and a second in <em>b</em> ways, then making <b>both</b> can "
        "happen in <b>a &times; b</b> ways. Let's see it with our cafe: 5 flavours, then for each "
        "flavour 4 toppings."))
    A(figure(slot_row([("flavour", 5, SKY), ("topping", 4, BERRY)]),
             "5 x 4 = 20 different shakes -- so 20 days before you must repeat."))
    A(P("A small <b>choice tree</b> makes it visible &mdash; but notice we already knew the answer "
        "was <b>20</b> from 5 &times; 4, with no drawing needed:"))
    A(figure(choice_tree("Start",
                         [("V", BERRY), ("M", SKY), ("C", GRASS)],
                         [[("Vanilla + sprinkles", BERRY), ("Vanilla + nuts", BERRY),
                           ("Vanilla + fruit", BERRY), ("Vanilla + sauce", BERRY)],
                          [("Mango + sprinkles", SKY), ("Mango + nuts", SKY),
                           ("Mango + fruit", SKY), ("Mango + sauce", SKY)],
                          [("Choco + (4 toppings)", GRASS)]]),
             "Each of the 5 flavours fans into 4 toppings -> 5 groups of 4 = 20."))
    A(tryit("A pizza has 3 sizes and 6 toppings (one of each). How many "
            "different one-topping pizzas are there?",
            "Multiply the two stages: 3 &times; 6 = <b>18</b> pizzas."))

    # -- many stages ----------------------------------------------------------
    A(H("The big leap: more than two stages"))
    A(P("Here is what's new in Level 3. The principle doesn't stop at two choices &mdash; it keeps "
        "going for <em>every</em> stage. Just keep multiplying. Imagine getting dressed: "
        "<b>3 shirts</b>, <b>2 trousers</b>, <b>4 caps</b>."))
    A(figure(slot_row([("shirt", 3, SKY), ("trouser", 2, BERRY), ("cap", 4, GRASS)]),
             "3 x 2 x 4 = 24 complete outfits."))
    A(example("a 4-digit PIN lock", steps([
        "A lock has 4 wheels, each able to show any digit 0-9. Each wheel is a stage.",
        "Stage 1: <b>10</b> choices. Stage 2: <b>10</b>. Stage 3: <b>10</b>. Stage 4: <b>10</b>.",
        "Multiply: 10 &times; 10 &times; 10 &times; 10 = <b>10,000</b> possible PINs (0000 up to "
        "9999).",
        "Surprise! That's why a 4-digit PIN feels safe &mdash; a thief would have to try ten "
        "<em>thousand</em> codes. Add one more wheel and it jumps to 1,00,000. Each extra stage "
        "<b>multiplies</b> the danger away. &#128274;",
    ])))
    A(kiwi("Big idea: <b>more stages -> multiply more numbers</b>. Counting grows "
           "<em>explosively</em> fast &mdash; that's the secret power (and surprise) of the "
           "Counting Principle. A handful of choices can make millions of possibilities."))
    A(tryit("A meal deal is 1 starter (2 options) + 1 main (3 options) + 1 drink "
            "(4 options) + 1 dessert (2 options). How many different meal deals?",
            "Multiply every stage: 2 &times; 3 &times; 4 &times; 2 = <b>48</b> meal deals."))

    # -- forming numbers from digit cards ------------------------------------
    A(H("Forming numbers from digit cards"))
    A(P("A classic Olympiad question: you hold the digit cards <b>3, 5, 7, 8</b>. How many "
        "<b>3-digit numbers</b> can you arrange if <em>no card repeats</em> (you only have one of "
        "each)? Think of three empty slots &mdash; hundreds, tens, ones &mdash; and fill them one "
        "at a time."))
    A(figure(slot_row([("hundreds", 4, SKY), ("tens", 3, BERRY), ("ones", 2, GRASS)]),
             "First slot: 4 cards. Next: 3 left. Last: 2 left -> 4 x 3 x 2 = 24."))
    A(example("counting the 3-digit numbers (no repeats)", steps([
        "<b>Hundreds slot:</b> any of the 4 cards &rarr; <b>4</b> choices.",
        "<b>Tens slot:</b> one card is now used, so <b>3</b> cards remain.",
        "<b>Ones slot:</b> two cards used, so <b>2</b> remain.",
        "Multiply: 4 &times; 3 &times; 2 = <b>24</b> different numbers. (We'll trust the principle "
        "rather than write all 24!)",
    ])))
    A(P("Now a famous twist that trips people up: what if a <b>0</b> is among the cards? A number "
        "<em>cannot start</em> with 0 (0 5 7 would just be 57). Suppose the cards are "
        "<b>0, 4, 7</b> and we want 3-digit numbers, no repeats."))
    A(figure(slot_row([("hundreds", 2, BERRY), ("tens", 2, SKY), ("ones", 1, GRASS)]),
             "Hundreds can't be 0 -> only 2 choices; then 2 left; then 1 -> 2 x 2 x 1 = 4."))
    A(example("when 0 is a card -- fill the fussy slot first", steps([
        "<b>Hundreds slot first</b> (it's the picky one &mdash; no 0 allowed): only 4 or 7 &rarr; "
        "<b>2</b> choices.",
        "<b>Tens slot:</b> 0 is now allowed here, and one card is used, so of the remaining 2 "
        "cards (including 0) &rarr; <b>2</b> choices.",
        "<b>Ones slot:</b> just <b>1</b> card left.",
        "Multiply: 2 &times; 2 &times; 1 = <b>4</b> numbers. List to be sure: 407, 470, 704, 740. "
        "Exactly <b>4</b>! &#10003;",
    ])))
    A(kiwi("Golden habit: when one slot has a special rule (like &ldquo;no leading zero&rdquo;), "
           "<b>fill that fussy slot first</b>. Decide the hard thing while you still can, then the "
           "easy slots fall into place."))
    A(tryit("Using cards 2, 4, 6, 8 (no repeats), how many <b>2-digit</b> numbers can you make?",
            "Tens slot: 4 cards; ones slot: 3 left &rarr; 4 &times; 3 = <b>12</b> numbers. (They "
            "happen to all be even, since every card is an even digit.)"))

    # -- order matters vs order doesn't --------------------------------------
    A(H("The big distinction: does ORDER matter?"))
    A(P("Here is the most important idea in counting, and it decides everything. Sometimes "
        "<b>order matters</b> (we call these <b>arrangements</b>), and sometimes it doesn't (we "
        "call these <b>selections</b>). Watch the difference with three friends &mdash; "
        "<b>A</b>sha, <b>B</b>ina, <b>C</b>ara."))
    A(P("<b>Arrangement (order matters):</b> giving out a <em>gold</em> and a <em>silver</em> "
        "medal to 2 of them. Asha-gold/Bina-silver is a <em>different</em> result from "
        "Bina-gold/Asha-silver."))
    A(figure(slot_row([("gold", 3, GOLD), ("silver", 2, SKY)], caption_cols=False),
             "Gold: 3 choices, then silver: 2 left -> 3 x 2 = 6 different medal results."))
    A(P("Let's list those <b>6</b> ordered results (first = gold, second = silver):"))
    A(figure(chip_row(["A&#8594;B", "A&#8594;C", "B&#8594;A", "B&#8594;C", "C&#8594;A", "C&#8594;B"], ORANGE),
             "6 ordered medal results -- A->B (Asha gold, Bina silver) is not B->A."))
    A(P("<b>Selection (order doesn't matter):</b> instead just <em>choosing 2 friends</em> for a "
        "team (no medals). Now Asha-with-Bina is the <b>same team</b> as Bina-with-Asha. So we "
        "must <em>not</em> count both. The teams are only:"))
    A(figure(chip_row(["A &amp; B", "A &amp; C", "B &amp; C"], GRASS),
             "Only 3 teams -- each pair counted once."))
    A(example("why selections are HALF the arrangements (here)", steps([
        "Ordered medal results: <b>6</b> (we counted them).",
        "But each <em>team</em> of 2 was counted <b>twice</b> in that list &mdash; once as "
        "A&rarr;B and once as B&rarr;A. A pair of people can be lined up in 2 orders.",
        "So the number of teams = 6 &divide; 2 = <b>3</b>. We divide away the repeats.",
        "Rule of thumb: <b>arrangements</b> count orderings; <b>selections</b> = arrangements "
        "&divide; (the number of ways the chosen group can be reordered).",
    ])))
    A(kiwi("The one question to always ask: <em>&ldquo;If I swap the order, is it a new "
           "result?&rdquo;</em> <b>Yes</b> &rarr; it's an arrangement (order matters). "
           "<b>No</b> &rarr; it's a selection (order doesn't), so beware of double-counting."))
    A(tryit("From 4 runners, a 1st place and a 2nd place are awarded. Is this order-matters or "
            "order-doesn't? How many results?",
            "Order <b>matters</b> (1st vs 2nd are different). 4 &times; 3 = <b>12</b> ordered "
            "results."))

    # -- n-choose-2: handshakes ----------------------------------------------
    A(H("Choosing 2 from a group: the handshake countdown"))
    A(P("Choosing a team of <b>2</b> (order doesn't matter) comes up so often it deserves its own "
        "trick. At a party, <b>5 friends</b> each shake hands with <b>every other</b> friend "
        "exactly once. A handshake is just a <em>pair</em> of friends. How many handshakes?"))
    A(figure(pair_chords(5),
             "5 people, every pair joined by a line. Count the lines = count the handshakes."))
    A(P("Two ways to count, and they agree:"))
    A(example("counting the handshakes two ways", steps([
        "<b>Countdown way:</b> the 1st person shakes the other 4. The next person adds 3 "
        "<em>new</em> handshakes (their shake with #1 is already counted). Then 2, then 1, then "
        "0. So 4 + 3 + 2 + 1 = <b>10</b>.",
        "<b>Divide-the-double way:</b> each of the 5 people shakes 4 others = 5 &times; 4 = 20 "
        "&ldquo;ends&rdquo;, but every handshake has 2 ends, so 20 &divide; 2 = <b>10</b>.",
        "Both give <b>10</b> handshakes. The lines in the picture? Count them &mdash; exactly "
        "10. &#10003;",
    ])))
    A(kiwi("The handshake count for <b>n</b> people is the countdown "
           "<b>(n&minus;1) + (n&minus;2) + &hellip; + 1</b>, which is the same as "
           "<b>n &times; (n&minus;1) &divide; 2</b>. It answers ALL &ldquo;choose 2 from "
           "n&rdquo; questions: handshakes, lines between dots, games in a round-robin, teams "
           "of 2."))
    A(tryit("8 chess players each play every other player once. How many games are played?",
            "Choose 2 from 8: 8 &times; 7 &divide; 2 = 56 &divide; 2 = <b>28</b> games."))

    # -- dots and diagonals ---------------------------------------------------
    A(H("Same trick, new disguise: dots and diagonals"))
    A(P("Because a straight line is fixed by <b>2 points</b>, &ldquo;how many lines through these "
        "dots?&rdquo; is secretly a choose-2 question. With <b>6</b> dots (no 3 in a line), the "
        "number of lines joining them is 6 &times; 5 &divide; 2 = <b>15</b>."))
    A(figure(pair_chords(6), "6 dots, every pair joined -> 6 x 5 / 2 = 15 lines."))
    A(P("A neat cousin: a polygon's <b>diagonals</b>. A hexagon (6 corners) has 15 joining lines, "
        "but 6 of them are the <em>sides</em>, so the diagonals number 15 &minus; 6 = <b>9</b>."))
    A(tryit("How many lines join 7 dots, no three in a line?",
            "Choose 2 from 7: 7 &times; 6 &divide; 2 = <b>21</b> lines."))

    # -- Bloom ladder ---------------------------------------------------------
    A(H("Now climb the ladder"))
    A(P("Decide first: <em>do I multiply stages, or choose-2?</em> And always ask whether "
        "<b>order matters</b>. Peek only after a real try!"))

    A(practice("Remember", [
        ("If a choice has 6 ways and a following choice has 3 ways, the total is found by "
         "adding or multiplying?", "Multiplying: 6 &times; 3 = 18."),
        ("In a team of 2 chosen from a group, does the <b>order</b> of the two people matter?",
         "No -- a team is a selection, so order doesn't matter."),
        ("Write the handshake formula for n people.", "n &times; (n &minus; 1) &divide; 2."),
        ("Can a 3-digit number start with the digit 0?",
         "No -- then it wouldn't really be a 3-digit number."),
        ("Giving a gold and a silver medal to 2 of 5 people -- does order matter?",
         "Yes -- gold and silver are different, so it's an arrangement."),
    ]))
    A(practice("Understand", [
        ("A breakfast is 1 cereal (4 kinds) + 1 fruit (3 kinds) + 1 drink (2 kinds). "
         "How many breakfasts?", "Multiply all stages: 4 &times; 3 &times; 2 = 24 breakfasts."),
        ("Using cards 1, 2, 3, 4, 5 (no repeats), how many 2-digit numbers can be made?",
         "Tens: 5 choices, ones: 4 left &rarr; 5 &times; 4 = 20 numbers."),
        ("6 people at a meeting all shake hands once. How many handshakes?",
         "6 &times; 5 &divide; 2 = 15 handshakes."),
        ("From friends P, Q, R, S, list every team of 2 (order doesn't matter).",
         "PQ, PR, PS, QR, QS, RS &rarr; 6 teams (which is 4 &times; 3 &divide; 2)."),
        ("How many lines join 5 dots, no three in a line?", "5 &times; 4 &divide; 2 = 10 lines."),
    ]))
    A(practice("Apply", [
        ("A number plate has 2 letters (each A-Z, repeats allowed) followed by 3 digits "
         "(each 0-9, repeats allowed). How many plates are possible?",
         "26 &times; 26 &times; 10 &times; 10 &times; 10 = 676 &times; 1000 = 6,76,000 plates."),
        ("Using cards 0, 3, 5 (no repeats), how many 3-digit numbers can be made?",
         "Hundreds can't be 0 &rarr; 2 choices; then 2 left; then 1: 2 &times; 2 &times; 1 = 4 "
         "(305, 350, 503, 530)."),
        ("10 football teams play a round-robin (each pair plays once). How many matches?",
         "10 &times; 9 &divide; 2 = 45 matches."),
        ("From 6 runners, a 1st, 2nd and 3rd place are given. How many ways (order matters)?",
         "6 &times; 5 &times; 4 = 120 ways."),
        ("How many diagonals does a pentagon (5 corners) have?",
         "Lines joining 5 corners: 5 &times; 4 &divide; 2 = 10; minus the 5 sides = 5 diagonals."),
    ]))
    A(practice("Analyze", [
        ("Which gives MORE results from 5 people: choosing a team of 2, or awarding a gold "
         "and silver to 2 of them? By how many?",
         "Team (order doesn't matter): 5 &times; 4 &divide; 2 = 10. Medals (order matters): "
         "5 &times; 4 = 20. The medals give 10 more, because each team can be ordered 2 ways."),
        ("Using digits 1, 2, 3, 4 (no repeats), how many 3-digit numbers are EVEN? "
         "(Even means the ones digit is 2 or 4.)",
         "Fill the fussy ones-slot first: ones = 2 or 4 &rarr; 2 choices. Then hundreds: 3 of the "
         "remaining &rarr; 3. Then tens: 2 left &rarr; 2. So 2 &times; 3 &times; 2 = 12 even "
         "numbers."),
        ("Maya says &ldquo;7 friends make 7 handshakes.&rdquo; Is she right? Explain and give the "
         "correct number.",
         "No. Handshakes for 7 = 7 &times; 6 &divide; 2 = 21, not 7. She confused &ldquo;number "
         "of people&rdquo; with &ldquo;number of pairs.&rdquo;"),
        ("A 4-digit code uses digits 0-9 but the first digit can't be 0. How many codes?",
         "First digit: 9 choices (1-9); the other three: 10 each &rarr; "
         "9 &times; 10 &times; 10 &times; 10 = 9,000 codes."),
        ("In a class everyone shook hands once and there were 28 handshakes in total. How many "
         "students are in the class?",
         "We need n &times; (n &minus; 1) &divide; 2 = 28, so n &times; (n &minus; 1) = 56 = "
         "8 &times; 7. Thus n = 8 students."),
    ]))
    A(practice("Create", [
        ("Design an ice-cream menu (scoops and toppings) that gives exactly <b>12</b> different "
         "one-scoop one-topping cones. Show your numbers.",
         "Many answers, e.g. 4 scoops &times; 3 toppings = 12, or 6 scoops &times; 2 toppings = "
         "12, or 2 scoops &times; 6 toppings = 12."),
        ("Invent a &ldquo;how many handshakes?&rdquo; question whose answer is exactly <b>6</b>. "
         "Give the number of people.",
         "4 people: 4 &times; 3 &divide; 2 = 6 handshakes. (Any setup that is choose-2 from 4 "
         "works.)"),
        ("Choose 4 digit-cards (none of them 0) and ask how many 3-digit numbers can be made "
         "with no repeats. Write the question AND the answer.",
         "Example: cards 2, 5, 7, 9 &rarr; 4 &times; 3 &times; 2 = 24 three-digit numbers (no "
         "repeats)."),
        ("Invent a small &ldquo;menu&rdquo; with three stages (like bread, filling, drink) so "
         "that there are exactly <b>24</b> different meals. List your three numbers.",
         "Many answers whose three numbers multiply to 24, e.g. 4 &times; 3 &times; 2 = 24, or "
         "2 &times; 6 &times; 2 = 24, or 3 &times; 4 &times; 2 = 24."),
    ]))

    A(challenge(
        P("&#11088; <b>The Tournament Puzzle.</b> A chess club runs a tournament where every "
          "player plays every other player exactly <b>once</b>. The organiser counts "
          "<b>45 games</b> in total. (a) How many players are in the club? (b) The club then "
          "admits <b>2 more</b> players (same every-pair-once rule). How many <em>extra</em> "
          "games does that add?") +
        tryit("Use the choose-2 formula, and solve n &times; (n&minus;1) &divide; 2 = 45.",
              "(a) n &times; (n &minus; 1) &divide; 2 = 45 &rarr; n &times; (n &minus; 1) = 90 = "
              "10 &times; 9, so <b>10 players</b>. (b) With 12 players: 12 &times; 11 &divide; 2 = "
              "<b>66</b> games. Extra games = 66 &minus; 45 = <b>21</b>. (The 2 newcomers each "
              "play the 10 old players, that's 20 games, plus the 1 game between themselves = "
              "21. &#10003;)")))

    A(kiwi("Outstanding! You can now multiply across <em>many</em> stages, form numbers from "
           "digit cards (mind the leading zero!), tell <b>arrangements</b> from <b>selections</b>, "
           "and crack any &ldquo;choose 2&rdquo; question with the handshake countdown. Next we "
           "ask not just <em>how many</em>, but <em>how likely</em> &mdash; and then crack "
           "secret-code sums and ancient magic squares. &#127922;"))

    chapter("Part 6 · Counting, Chance & Logic", 18, "Smart Counting & Combinations",
            "Combinatorics · Smart Counting", "".join(b))
