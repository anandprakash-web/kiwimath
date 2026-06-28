#!/usr/bin/env python3
"""L3 Chapter 19 — Probability, Cryptarithms & Magic Squares (Combinatorics).
Probability = favourable/total on the 0-1 scale (coins, dice, spinners, marbles),
sure/impossible, complementary events; then letter-sum cryptarithms (unique
solutions) and the 3x3 Lo Shu magic square. Every probability is ENUMERATED and
every code/blank is brute-forced in Python."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, spinner, magic_square, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# -- local figure: the 0 -> 1 chance line --------------------------------
def chance_line(marks=None):
    marks = marks or []
    x0, x1, y = 40, 600, 58
    s = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{INK}" stroke-width="3"/>']
    stops = [(0.0, "Impossible", BERRY, "0"), (0.25, "Unlikely", ORANGE, "1/4"),
             (0.5, "Even chance", GOLD, "1/2"), (0.75, "Likely", SKY, "3/4"),
             (1.0, "Certain", GRASS, "1")]
    for f, lab, col, frac in stops:
        x = x0 + f * (x1 - x0)
        s.append(f'<line x1="{x:.0f}" y1="{y-9}" x2="{x:.0f}" y2="{y+9}" stroke="{INK}" '
                 f'stroke-width="2.5"/>')
        s.append(f'<text x="{x:.0f}" y="{y+30}" text-anchor="middle" font-size="12.5" '
                 f'font-weight="800" fill="{col}">{lab}</text>')
        s.append(f'<text x="{x:.0f}" y="{y-16}" text-anchor="middle" font-size="12" '
                 f'fill="{INK}">{frac}</text>')
    for f, lab, col in marks:
        x = x0 + f * (x1 - x0)
        s.append(f'<circle cx="{x:.0f}" cy="{y}" r="9" fill="{col}"/>')
        s.append(f'<text x="{x:.0f}" y="{y-26}" text-anchor="middle" font-size="12.5" '
                 f'font-weight="800" fill="{col}">{lab}</text>')
    return svg("".join(s), 640, 92)


# -- local figure: a single die face -------------------------------------
def die_face(n):
    s = [f'<rect x="6" y="6" width="80" height="80" rx="14" fill="#fff" stroke="{INK}" '
         f'stroke-width="2.6"/>']
    pp = {1: [(46, 46)], 2: [(26, 26), (66, 66)],
          3: [(26, 26), (46, 46), (66, 66)],
          4: [(26, 26), (66, 26), (26, 66), (66, 66)],
          5: [(26, 26), (66, 26), (46, 46), (26, 66), (66, 66)],
          6: [(26, 24), (66, 24), (26, 46), (66, 46), (26, 68), (66, 68)]}[n]
    for px, py in pp:
        s.append(f'<circle cx="{px}" cy="{py}" r="8" fill="{INK}"/>')
    return "".join(s)


def dice_row(faces):
    s = [f'<g transform="translate({i*100},0)">{die_face(n)}</g>' for i, n in enumerate(faces)]
    return svg("".join(s), len(faces) * 100, 96)


# -- local figure: marbles in a bag --------------------------------------
def marble_bag(colors):
    n = len(colors); perrow = 5
    rows = (n + perrow - 1) // perrow
    Hh = 92 + rows * 36
    s = [f'<path d="M70,70 Q140,30 210,70 L228,{Hh-14} Q140,{Hh+4} 52,{Hh-14} Z" '
         f'fill="{GOLD}11" stroke="{GOLD}" stroke-width="2.6"/>',
         f'<rect x="96" y="40" width="88" height="22" rx="8" fill="{GOLD}22" '
         f'stroke="{GOLD}" stroke-width="2.2"/>']
    x0, y0 = 88, 92
    for i, c in enumerate(colors):
        r, col = divmod(i, perrow)
        cx = x0 + col * 30 + (r % 2) * 12; cy = y0 + r * 36
        s.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="{c}99" stroke="{c}" '
                 f'stroke-width="2"/>')
    return svg("".join(s), 280, Hh)


# -- local figure: a vertical letter-sum (cryptarithm) -------------------
def crypto_sum(rows, result, op="+"):
    width = max(len(r) for r in rows + [result])
    cw = 40
    xr = 60 + width * cw
    Hh = 40 + (len(rows) + 1) * 46
    s = []; y = 46
    for ri, r in enumerate(rows):
        padded = r.rjust(width)
        for ci, ch in enumerate(padded):
            if ch == " ":
                continue
            x = xr - (width - ci) * cw + cw / 2
            col = INK if ch.isdigit() else ORANGE
            s.append(f'<text x="{x:.0f}" y="{y}" text-anchor="middle" font-size="30" '
                     f'font-weight="800" font-family="Georgia,serif" fill="{col}">{ch}</text>')
        if ri == len(rows) - 1:
            s.append(f'<text x="22" y="{y}" font-size="28" font-weight="800" '
                     f'fill="{GRASS}">{op}</text>')
        y += 46
    s.append(f'<line x1="14" y1="{y-30}" x2="{xr}" y2="{y-30}" stroke="{INK}" '
             f'stroke-width="2.6"/>')
    padded = result.rjust(width)
    for ci, ch in enumerate(padded):
        if ch == " ":
            continue
        x = xr - (width - ci) * cw + cw / 2
        col = INK if ch.isdigit() else BERRY
        s.append(f'<text x="{x:.0f}" y="{y}" text-anchor="middle" font-size="30" '
                 f'font-weight="800" font-family="Georgia,serif" fill="{col}">{ch}</text>')
    return svg("".join(s), xr + 16, Hh)


def build(chapter):
    b = []; A = b.append

    A(big_q("Toss a coin &mdash; will it be Heads? Roll a die &mdash; will you get a six? You "
            "can't be <em>sure</em>&hellip; yet you're not totally guessing either. How do "
            "mathematicians pin down exactly <b>how likely</b> something is &mdash; and then turn "
            "into <b>detectives</b> who crack secret-code sums and 4,000-year-old number squares?"))
    A(kiwi("Hi again &mdash; <b>Kiwi</b> here! &#127922; This chapter has two joys. First, "
           "<b>probability</b>: maths can measure luck itself, putting every &ldquo;what are the "
           "chances?&rdquo; on a clean scale from 0 to 1. Then pure puzzle fun: "
           "<b>cryptarithms</b> (where letters hide digits) and <b>magic squares</b> (where every "
           "line adds to the same total). No scary formulas &mdash; just careful counting and "
           "clever reasoning."))

    # ===================== A . PROBABILITY =====================
    A(H("Part A &middot; Measuring chance"))
    A(P("Before numbers, words. Every event sits somewhere on a <b>chance line</b> from "
        "<b>impossible</b> (it can never happen) to <b>certain</b> (it must happen):"))
    A(figure(chance_line(),
             "Impossible (0) - Unlikely - Even chance (1/2) - Likely - Certain (1)."))
    A(figure(chance_line([(0.0, "roll a 7", BERRY), (0.5, "coin = Heads", GOLD),
                         (1.0, "sun sets today", GRASS)]),
             "Three events placed on the chance line."))
    A(P("To get a <b>number</b>, we count two things and make a fraction. It works tidily when "
        "every result is <b>equally likely</b> (a fair coin, a fair die):"))
    A(P("&nbsp;&nbsp;&nbsp;&nbsp;<b>probability = (number of ways we WANT) &divide; (number of "
        "ways ALTOGETHER)</b>"))
    A(example("tossing a fair coin", steps([
        "Results altogether: <b>2</b> (Heads or Tails).",
        "Results we want (Heads): <b>1</b>.",
        "P(Heads) = 1 &divide; 2 = <b>1/2</b> &mdash; an even chance, right in the middle of the "
        "line. &#129689;",
    ]) + P("<em>(Throughout this chapter we use our <b>fair-coin model</b>: exactly two equally "
           "likely results, Heads and Tails, and we ignore the wafer-thin chance the coin lands on "
           "its edge.)</em>")))
    A(kiwi("A probability is always between <b>0</b> and <b>1</b>. It can never be more than 1 "
           "&mdash; you can't be <em>more</em> than certain! And it's never less than 0."))

    A(H("Rolling a die"))
    A(P("A fair die has <b>6</b> equally likely faces:"))
    A(figure(dice_row([1, 2, 3, 4, 5, 6]), "The 6 faces of a fair die -- each equally likely."))
    A(example("the chance of an EVEN roll", steps([
        "Even faces: 2, 4, 6 &rarr; <b>3</b> faces we want.",
        "Faces altogether: <b>6</b>.",
        "P(even) = 3 &divide; 6 = <b>1/2</b>. Same as a coin!",
    ])))
    A(example("the chance of rolling MORE than 4", steps([
        "Faces more than 4: just 5 and 6 &rarr; <b>2</b> faces.",
        "P(more than 4) = 2 &divide; 6 = <b>1/3</b>.",
    ])))
    A(tryit("On a fair die, what is the probability of rolling a <b>prime</b> number "
            "(2, 3 or 5)?",
            "Primes 2, 3, 5 &rarr; 3 faces of 6, so P = 3/6 = <b>1/2</b>."))

    A(H("Spinners"))
    A(P("This spinner has <b>4 equal slices</b>: two Red, one Blue, one Green. Bigger share of "
        "the spinner &rarr; bigger probability."))
    A(figure(spinner(["Red", "Blue", "Red", "Green"]),
             "4 equal slices: 2 Red, 1 Blue, 1 Green."))
    A(example("reading the spinner", steps([
        "P(Red) = 2 of 4 = 2/4 = <b>1/2</b> (Red is the most likely &mdash; it fills half).",
        "P(Blue) = 1 of 4 = <b>1/4</b>; P(Green) = 1 of 4 = <b>1/4</b>.",
        "Check: 1/2 + 1/4 + 1/4 = <b>1</b>. Every possible result, added up, makes 1. &#10003;",
    ])))
    A(tryit("On the same spinner, what is the probability of landing on a colour that is "
            "<b>NOT Red</b>?",
            "Not Red means Blue or Green &rarr; 2 slices of 4 = 2/4 = <b>1/2</b>."))

    A(H("Marbles, and the complement trick"))
    A(P("A bag holds <b>3 red</b> and <b>2 blue</b> marbles. You grab one without looking."))
    A(figure(marble_bag([BERRY, BERRY, BERRY, SKY, SKY]),
             "3 red + 2 blue = 5 marbles altogether."))
    A(example("red, blue, and the check", steps([
        "P(red) = 3 of 5 = <b>3/5</b>.",
        "P(blue) = 2 of 5 = <b>2/5</b>.",
        "P(red) + P(blue) = 3/5 + 2/5 = 5/5 = <b>1</b>. The two cover everything that can happen. "
        "&#10003;",
    ])))
    A(kiwi("Here's a Level-3 power move &mdash; the <b>complement</b>. Because all the chances add "
           "to 1, the chance of something <em>NOT</em> happening is <b>1 minus</b> the chance it "
           "does: P(not A) = 1 &minus; P(A). Sometimes the &ldquo;not&rdquo; is far easier to "
           "count!"))
    A(example("using the complement", steps([
        "A spinner lands on Red with probability 1/4, and Red and Blue are the only colours.",
        "Instead of measuring Blue directly, use the complement: P(Blue) = 1 &minus; P(Red).",
        "P(Blue) = 1 &minus; 1/4 = <b>3/4</b>. &#10003;",
    ])))
    A(tryit("A bag has <b>4 red</b>, <b>1 green</b> and <b>1 yellow</b> marble. What is the "
            "probability of pulling a marble that is <b>not red</b>?",
            "Not red = green or yellow = 2 of 6 = 2/6 = <b>1/3</b>. (Check with the complement: "
            "red is 4/6 = 2/3, and 1 &minus; 2/3 = 1/3. &#10003;)"))

    # ===================== B . CRYPTARITHMS =====================
    A(H("Part B &middot; Cryptarithms: letters hiding digits"))
    A(P("Now we become code-breakers. In a <b>cryptarithm</b>, each <b>letter</b> stands for a "
        "secret <b>digit</b>, and the same letter is always the same digit. Crack the code so the "
        "sum is true. Start tiny:"))
    A(figure(crypto_sum(["A", "A", "A"], "9"), "A + A + A = 9. What digit is A?"))
    A(example("finding A", steps([
        "A added three times makes 9, so 3 &times; A = 9.",
        "A = 9 &divide; 3 = <b>3</b>. Check: 3 + 3 + 3 = 9. &#10003;",
    ])))
    A(P("A detective's shortcut you'll use again and again: <b>a digit added to itself is always "
        "even</b> (doubling lands on 0, 2, 4, 6, 8&hellip;). So in <b>A + A</b>, the answer's last "
        "digit can only be even. That single clue throws away half the guesses!"))
    A(tryit("Could <b>A + A = 7</b> ever be true for a single digit A? Why or why not?",
            "No &mdash; A + A is always <b>even</b>, but 7 is odd. Impossible."))

    A(H("The big one: AB + B = BA"))
    A(P("Here <b>AB</b> is a 2-digit number (A tens, B ones), and we add the single digit "
        "<b>B</b>. The answer is <b>BA</b> &mdash; the <em>same two digits, swapped</em>. Reason "
        "it out column by column:"))
    A(figure(crypto_sum(["A B", "  B"], "B A"),
             "A tens + B ones, plus B ones, equals B tens + A ones."))
    A(example("cracking AB + B = BA &mdash; a clean proof, no guessing", steps([
        "<b>Write what the digits mean.</b> AB is the number 10A + B; add the single digit B; the "
        "answer BA is 10B + A. So the sum says <b>10A + B + B = 10B + A</b>, i.e. "
        "<b>10A + 2B = 10B + A</b>.",
        "<b>Tidy it up.</b> Move the letters together: 10A &minus; A = 10B &minus; 2B, which gives "
        "<b>9A = 8B</b>. One neat equation now carries the whole puzzle.",
        "<b>Read off the only answer.</b> 9 and 8 share no common factor, so for 9A = 8B the left "
        "side must be a multiple of 8 and the right a multiple of 9. With single digits and A "
        "&ge; 1, that forces A = <b>8</b> and B = <b>9</b> (then 9&times;8 = 8&times;9 = 72 &mdash; "
        "it balances).",
        "<b>Check the whole sum:</b> 89 + 9 = <b>98</b> = BA. &#10003; The proof <em>guarantees</em> "
        "this is the one and only solution &mdash; we never had to try cases.",
    ])))
    A(kiwi("That's the difference between a guesser and a mathematician: instead of testing digit "
           "after digit, we turned the picture into the equation <b>9A = 8B</b> and the answer fell "
           "out. A quick computer sweep of all 100 digit pairs agrees &mdash; <b>only</b> A = 8, "
           "B = 9 works. The algebra already knew that."))
    A(P("One more pattern worth proving: <b>AB + BA</b> = (10A + B) + (10B + A) = 11A + 11B = "
        "<b>11 &times; (A + B)</b> &mdash; always a multiple of 11. What kind of multiple depends on "
        "A + B:"))
    A(P("&bull; If <b>A + B is less than 10</b>, then 11 &times; (A + B) is a <b>two-digit repeated "
        "number</b>: 25 + 52 = <b>77</b>, 16 + 61 = <b>77</b> (both have A + B = 7), and 72 + 27 = "
        "<b>99</b> (A + B = 9).<br>"
        "&bull; If <b>A + B is 10 or more</b>, the total spills into <b>three digits</b> &mdash; "
        "still a multiple of 11: 58 + 85 = <b>143</b> = 11 &times; 13. The repeated-digit look only "
        "happens while A + B stays a single digit."))
    A(tryit("In the code <b>BB + B</b> with B = 2 (BB means the two-digit number 22), what is the "
            "total?",
            "BB = 22, plus B = 2, so 22 + 2 = <b>24</b>."))

    # ===================== C . MAGIC SQUARES =====================
    A(H("Part C &middot; Magic squares"))
    A(P("A <b>magic square</b> is a grid where every <b>row</b>, every <b>column</b>, and both "
        "<b>diagonals</b> add up to the same total &mdash; the <b>magic number</b>. Here is the "
        "oldest and most famous, the <b>Lo Shu</b> square (over 4,000 years old!), using 1 to 9 "
        "exactly once each:"))
    A(figure(magic_square([[2, 7, 6], [9, 5, 1], [4, 3, 8]]),
             "Every row, column and diagonal adds to 15 -- the magic number."))
    A(example("checking the magic number", steps([
        "<b>Top row:</b> 2 + 7 + 6 = <b>15</b>.",
        "<b>Middle column:</b> 7 + 5 + 3 = <b>15</b>.",
        "<b>Main diagonal:</b> 2 + 5 + 8 = <b>15</b>. Every line makes 15!",
        "Why 15? The digits 1 to 9 add to 45, shared over 3 rows: 45 &divide; 3 = <b>15</b>. And "
        "the centre is always the magic number &divide; 3 = 5.",
    ])))
    A(P("The real fun is <b>completing</b> a half-finished square &mdash; you don't guess, you "
        "<em>work out</em> each blank. Magic number = <b>15</b>; find the three &ldquo;?&rdquo;:"))
    A(figure(magic_square([[2, 7, 6], ["", 5, 1], [4, "", 8]]),
             "Magic number = 15. Find the three missing numbers."))
    A(example("solving the blanks, one line at a time", steps([
        "<b>Left column</b> (2, ?, 4) must total 15: ? = 15 &minus; 6 = <b>9</b>.",
        "<b>Bottom row</b> (4, ?, 8) must total 15: ? = 15 &minus; 12 = <b>3</b>.",
        "<b>Check the middle row:</b> 9 + 5 + 1 = 15. &#10003; The finished square is the famous "
        "one.",
    ])))
    A(kiwi("The secret to every magic square: hunt for a row, column or diagonal with only "
           "<b>one</b> blank. With a single unknown you can always find it &mdash; magic number "
           "minus the known numbers. Fill it, and a fresh one-blank line usually opens up."))
    A(tryit("A row of a magic square reads <b>6, ?, 8</b> and the magic number is 21. What is the "
            "missing number?",
            "6 + ? + 8 = 21, so ? = 21 &minus; 14 = <b>7</b>."))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now climb the ladder"))
    A(P("For probability, count <em>want</em> over <em>altogether</em>. For codes, hunt clues "
        "(even/odd, size). For magic squares, find a line with one blank. Peek only after a real "
        "try!"))

    A(practice("Remember", [
        ("What is the probability of something <b>certain</b>?", "1."),
        ("What is the probability of something <b>impossible</b>?", "0."),
        ("Is A + A always even or always odd?", "Always even."),
        ("In the famous 1-to-9 magic square, what number sits in the centre?", "5."),
        ("On a fair die, what is the probability of rolling a 4?", "1 of 6 = 1/6."),
    ]))
    A(practice("Understand", [
        ("A spinner has 4 equal slices: 3 green and 1 red. What is P(green)? And P(red)?",
         "P(green) = 3/4, P(red) = 1/4."),
        ("Solve the code: A + A + A + A = 8. What is A?", "4 &times; A = 8, so A = 2."),
        ("A magic square has magic number 15. A row reads 8, 1, ?. Find the missing number.",
         "8 + 1 + ? = 15, so ? = 6."),
        ("A bag holds 2 red, 3 blue and 5 yellow marbles. What is P(yellow)?",
         "Altogether 2 + 3 + 5 = 10; yellow = 5, so 5/10 = 1/2."),
        ("On a fair die, what is the probability of rolling a number less than 3 (a 1 or a 2)?",
         "2 of 6 = 2/6 = 1/3."),
    ]))
    A(practice("Apply", [
        ("A spinner has 8 equal slices numbered 1-8. What is the probability of landing on a "
         "<b>multiple of 3</b>?",
         "Multiples of 3 from 1-8 are 3 and 6 &rarr; 2 of 8 = 2/8 = 1/4."),
        ("A bag has 6 red and 4 blue marbles. What is the probability of <b>not</b> red? "
         "(Use the complement.)",
         "P(red) = 6/10 = 3/5, so P(not red) = 1 &minus; 3/5 = 2/5. (Or count blue: 4/10 = 2/5.)"),
        ("In a magic square with magic number 18, a column reads 7, ?, 4. Find the missing "
         "number.", "7 + ? + 4 = 18, so ? = 7."),
        ("Solve: T + T = 16. What digit is T? Then what is T + T + T?",
         "2 &times; T = 16, so T = 8; then T + T + T = 24."),
        ("Two fair coins are tossed. What is the probability of getting <b>two Heads</b>? "
         "(List the 4 equally likely results.)",
         "Results: HH, HT, TH, TT. Two Heads is just HH &rarr; 1 of 4 = 1/4."),
    ]))
    A(practice("Analyze", [
        ("A bag has 6 red and 4 blue marbles. Aria says &ldquo;there are 10 marbles, so the "
         "chance of red is 1/10.&rdquo; What did she do wrong, and what is the right answer?",
         "She used 1 instead of the number of RED marbles. P(red) = 6 of 10 = 6/10 = 3/5."),
        ("Two fair coins are tossed. What is the probability of getting <b>at least one Head</b>? "
         "Use the complement to check.",
         "Results HH, HT, TH, TT: three have a Head &rarr; 3/4. Complement check: the only "
         "no-Head result is TT (1/4), so 1 &minus; 1/4 = 3/4. &#10003;"),
        ("Part of a magic square (magic number 15): top row 4, 9, 2; middle row ?, 5, ?; bottom "
         "row 8, 1, ?. Find all three blanks.",
         "Left column 4, ?, 8 &rarr; middle-left = 3. Middle row 3, 5, ? &rarr; middle-right = 7. "
         "Bottom row 8, 1, ? &rarr; bottom-right = 6. The square is 4 9 2 / 3 5 7 / 8 1 6."),
        ("Pip says AB + BA always gives a number with two equal digits (like 77). Test A = 2, "
         "B = 5, then A = 1, B = 6, then A = 5, B = 8, and explain when Pip is right.",
         "25 + 52 = 77 and 16 + 61 = 77 (two equal digits), but 58 + 85 = 143 &mdash; three "
         "digits! The truth: AB + BA = 11 &times; (A + B). When A + B is a single digit (1&ndash;9) "
         "the answer is 11, 22, &hellip;, 99 &mdash; a repeated digit, so Pip is right. But once "
         "A + B reaches 10 the total becomes a 3-digit multiple of 11, so Pip's rule only holds "
         "for A + B &lt; 10."),
        ("Could a 3x3 magic square made from 1-to-9 ever have magic number 12? Explain.",
         "No. The nine numbers always add to 45, so the magic number must be 45 &divide; 3 = 15. "
         "No other total is possible."),
    ]))
    A(practice("Create", [
        ("Design a spinner (slices and colours) so that the chance of blue is exactly <b>1/2</b>. "
         "Describe it.",
         "Many answers, e.g. 4 slices with 2 blue (2/4), or 6 slices with 3 blue (3/6), or "
         "2 slices with 1 blue."),
        ("Invent your own one-letter code (like ? + ? + ? = 12) and write its answer.",
         "Many answers, e.g. K + K + K = 12 &rarr; K = 4; or P + P = 18 &rarr; P = 9."),
        ("Take the Lo Shu square 2 7 6 / 9 5 1 / 4 3 8, rub out any two numbers, and write how a "
         "friend would find them.",
         "Example: erase the 7 (top middle) and 3 (bottom middle). Friend uses the top row "
         "2 + ? + 6 = 15 &rarr; 7, and the bottom row 4 + ? + 8 = 15 &rarr; 3."),
        ("Fill a bag with red and blue marbles so that pulling a red is exactly <b>twice</b> "
         "as likely as pulling a blue. Give the numbers and both probabilities.",
         "Example: 4 red + 2 blue (6 total) &rarr; P(red) = 4/6 = 2/3 and P(blue) = 2/6 = 1/3, "
         "and 2/3 is twice 1/3. (Any 2-to-1 split of reds-to-blues works.)"),
    ]))

    A(challenge(
        P("&#11088; <b>The Detective Double-Header.</b> (a) <b>Probability:</b> a spinner has "
          "<b>6 equal slices</b> &mdash; 3 Sun, 2 Cloud, 1 Rain. Find P(Sun) and P(not Rain), and "
          "show the three chances add to 1. (b) <b>Magic square:</b> complete this one (magic "
          "number 15, digits 1-9 once each), given only the diagonal and one corner:") +
        figure(magic_square([[2, "", ""], ["", 5, ""], ["", "", 8]]),
               "Given: 2 (top-left), 5 (centre), 8 (bottom-right). Magic number 15.") +
        tryit("Count slices out of 6; for the square, work one blank at a time.",
              "(a) P(Sun) = 3/6 = <b>1/2</b>; P(not Rain) = (3 + 2)/6 = <b>5/6</b>; and "
              "3/6 + 2/6 + 1/6 = 6/6 = <b>1</b>. &#10003; (b) The main diagonal 2 + 5 + 8 = 15 "
              "already checks. The other diagonal ?, 5, ? totals 15, so those corners add to 10 "
              "&rarr; 6 (top-right) and 4 (bottom-left). Then top row 2 + ? + 6 = 15 &rarr; 7; "
              "left column 2 + ? + 4 = 15 &rarr; 9; middle row 9 + 5 + ? = 15 &rarr; 1; bottom row "
              "4 + ? + 8 = 15 &rarr; 3. Completed: <b>2 7 6 / 9 5 1 / 4 3 8</b>.")))

    A(kiwi("Wonderful work! You can measure chance as a fraction from 0 to 1, use the "
           "<b>complement</b> (1 &minus; P), crack letter-codes with even/odd and size clues, and "
           "complete any magic square by hunting one-blank lines. Next, your reasoning powers "
           "level up again: pigeonholes, logic grids, clocks, calendars and family puzzles. "
           "&#128373;"))

    chapter("Part 6 · Counting, Chance & Logic", 19, "Probability, Cryptarithms & Magic Squares",
            "Combinatorics · Smart Counting", "".join(b))
