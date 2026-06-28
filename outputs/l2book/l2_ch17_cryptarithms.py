#!/usr/bin/env python3
"""Chapter 17 — Cryptarithms & Magic Squares  (Combinatorics · Brain Benders)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, magic_square, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# ── local figure: a vertical letter-sum (cryptarithm) ───────────────────────
def crypto_sum(rows, result, note=""):
    """rows = list of strings (top addends), result = string (bottom).
    Draws a column-addition with a '+' and an underline, big friendly glyphs."""
    width = max(len(r) for r in rows + [result])
    cw = 40
    x_right = 60 + width * cw
    Hh = 50 + len(rows) * 46 + 60
    s = []
    y = 46
    for ri, r in enumerate(rows):
        padded = r.rjust(width)
        for ci, ch in enumerate(padded):
            if ch == " ":
                continue
            x = x_right - (width - ci) * cw + cw / 2
            col = INK if ch.isdigit() else ORANGE
            s.append(f'<text x="{x:.0f}" y="{y}" text-anchor="middle" font-size="30" '
                     f'font-weight="800" font-family="Georgia,serif" fill="{col}">{ch}</text>')
        if ri == len(rows) - 1:
            s.append(f'<text x="22" y="{y}" font-size="28" font-weight="800" fill="{GRASS}">+</text>')
        y += 46
    # underline
    s.append(f'<line x1="14" y1="{y-30}" x2="{x_right}" y2="{y-30}" stroke="{INK}" '
             f'stroke-width="2.6"/>')
    padded = result.rjust(width)
    for ci, ch in enumerate(padded):
        if ch == " ":
            continue
        x = x_right - (width - ci) * cw + cw / 2
        col = INK if ch.isdigit() else BERRY
        s.append(f'<text x="{x:.0f}" y="{y}" text-anchor="middle" font-size="30" '
                 f'font-weight="800" font-family="Georgia,serif" fill="{col}">{ch}</text>')
    if note:
        s.append(f'<text x="{x_right/2:.0f}" y="{Hh-8}" text-anchor="middle" font-size="12.5" '
                 f'fill="{INK}">{note}</text>')
    return svg("".join(s), x_right + 16, Hh)


def build(chapter):
    b = []
    A = b.append

    A(big_q("In the sum below, each <b>letter</b> stands for a secret <b>digit</b> — and the "
            "same letter is always the same digit. Can you crack the code so the sum is true?"))
    A(figure(crypto_sum(["A B", "  B"], "B A"), "Each letter = one hidden digit. What are A and B?"))
    A(kiwi("Hello, detective — <b>Kiwi</b> here! This chapter is pure puzzle fun. First we'll "
           "be code-breakers, finding which digit each letter hides. Then we'll build "
           "<b>magic squares</b>, where every row, column and diagonal adds to the same magic "
           "number. No new formulas — just clever thinking. 🔍"))

    # ── single-letter warm-up ───────────────────────────────────────────────
    A(H("Warm-up: one letter, one digit"))
    A(P("The simplest code uses a single letter. If a letter always means the same digit, we "
        "can solve a little equation. Look:"))
    A(figure(crypto_sum(["A", "A", "A"], "9"),
             "A + A + A = 9 — what digit is A?"))
    A(example("finding A", steps([
        "A added to itself three times makes 9, so A + A + A = 9.",
        "That means 3 × A = 9.",
        "So A = 9 ÷ 3 = <b>3</b>. Check: 3 + 3 + 3 = 9. ✓",
    ])))
    A(tryit("In the code <b>B + B = 14</b>, what digit is B?",
            "B + B = 14 means 2 × B = 14, so B = 7. Check: 7 + 7 = 14. ✓"))

    # ── the even/odd insight ────────────────────────────────────────────────
    A(H("A detective's shortcut: even or odd?"))
    A(P("Here's a trick clever solvers use. <b>Any digit added to itself is even</b> — because "
        "doubling always lands on an even number: 0, 2, 4, 6, 8, 10, 12… So in <b>A + A</b>, "
        "the answer's last digit can only be <b>0, 2, 4, 6 or 8</b>."))
    A(kiwi("This is a <em>clue-finder</em>, not the whole answer. Knowing the result must be "
           "even lets you throw away lots of wrong guesses before you even start. Detectives love "
           "a clue that shrinks the search!"))
    A(tryit("Could <b>A + A = 7</b> ever be true for a single digit A? Why or why not?",
            "No — A + A is always <b>even</b>, but 7 is odd. So it's impossible."))

    # ── the real two-letter cryptarithm ─────────────────────────────────────
    A(H("The big one: AB + B = BA"))
    A(P("Now back to our opening puzzle. <b>A B</b> is a 2-digit number (A tens, B ones), and we "
        "add the single digit <b>B</b> to it. The answer is <b>B A</b> — the <em>same two "
        "digits, swapped</em>. Let's reason it out like detectives, column by column."))
    A(figure(crypto_sum(["A B", "  B"], "B A"),
             "A tens + B ones, plus B ones, equals B tens + A ones"))
    A(example("cracking AB + B = BA", steps([
        "<b>Write the place values.</b> AB means 10A + B (A tens, B ones), and the single B is "
        "just B. So the left side is 10A + B + B = 10A + 2B. The answer BA means 10B + A.",
        "<b>Set them equal:</b> 10A + 2B = 10B + A.",
        "<b>Tidy up:</b> move the A's together and the B's together → 10A − A = 10B − 2B, "
        "which is 9A = 8B.",
        "<b>Read off the only answer.</b> 9A = 8B with A and B single digits: 9 and 8 share no "
        "common factor, so A must be 8 and B must be 9 (then 9 × 8 = 72 = 8 × 9 ✓).",
        "<b>Check the whole sum:</b> AB = 89, plus B = 9, gives 89 + 9 = <b>98</b> = BA. "
        "It works — A = 8 and B = 9. 🎉",
    ])))
    A(kiwi("Notice we didn't guess at all — we turned the puzzle into the tidy equation 9A = 8B "
           "and it handed us the only answer. Writing letters as place values (10A + B) is a "
           "code-breaker's sharpest tool."))

    A(tryit("In the code <b>ME + ME = WE</b> with E = 0, find one set of digits that works "
            "(M, W are different digits, and no number starts with 0).",
            "With E = 0: ME = M0 and WE = W0, so M0 + M0 = W0 means 2 × M = W. "
            "For example M = 3, W = 6: 30 + 30 = 60. ✓ (M = 1,W = 2 or M = 4,W = 8 also work.)"))

    # ── MAGIC SQUARES ───────────────────────────────────────────────────────
    A(H("Magic squares: every line, the same total"))
    A(P("Now for a 4,000-year-old puzzle. A <b>magic square</b> is a grid of numbers where every "
        "<b>row</b>, every <b>column</b>, and both <b>diagonals</b> add up to the <em>same</em> "
        "total — the <b>magic number</b>. Here is the most famous one of all, using the digits "
        "1 to 9 exactly once each:"))
    A(figure(magic_square([[2, 7, 6], [9, 5, 1], [4, 3, 8]]),
             "Every row, column and diagonal adds to 15 — the magic number"))
    A(example("checking the magic number", steps([
        "<b>Top row:</b> 2 + 7 + 6 = <b>15</b>.",
        "<b>Middle column:</b> 7 + 5 + 3 = <b>15</b>.",
        "<b>Main diagonal:</b> 2 + 5 + 8 = <b>15</b>.",
        "Try any other row, column or diagonal — they <em>all</em> make 15. That's the magic! "
        "And notice the <b>5</b> sits right in the middle.",
    ])))
    A(kiwi("Why 15? The digits 1 to 9 add up to 45. Sharing that fairly across 3 rows gives "
           "45 ÷ 3 = <b>15</b> per row. That's the magic number for the 1-to-9 square — and the "
           "middle cell is always the total ÷ 3, which is 5."))

    # ── filling missing cells ───────────────────────────────────────────────
    A(H("Filling in the blanks"))
    A(P("The real fun is completing a half-finished magic square. You don't guess — you use the "
        "magic number to <em>work out</em> each missing cell. Here the magic number is "
        "<b>15</b>. Find the three blanks marked “?”:"))
    A(figure(magic_square([[2, 7, 6], ["", 5, 1], [4, "", 8]]),
             "Magic number = 15. Find the three missing numbers."))
    A(example("solving the blanks one at a time", steps([
        "<b>Left column</b> (2, ?, 4) must total 15: 2 + ? + 4 = 15, so ? = 15 − 6 = <b>9</b>.",
        "<b>Bottom row</b> (4, ?, 8) must total 15: 4 + ? + 8 = 15, so ? = 15 − 12 = <b>3</b>.",
        "<b>Middle row</b> is now (9, 5, ?)… but we already know the last cell is 1 from the "
        "grid; check it: 9 + 5 + 1 = 15. ✓",
        "The finished square is 2 7 6 / 9 5 1 / 4 3 8 — exactly the famous one!",
    ])))
    A(figure(magic_square([[2, 7, 6], [9, 5, 1], [4, 3, 8]]),
             "Completed! Every line totals 15."))
    A(kiwi("The secret to magic squares: hunt for a row, column or diagonal that has only "
           "<b>one</b> blank. With one unknown, you can always find it — total minus the known "
           "numbers. Fill that, and a new “one-blank” line usually opens up."))

    A(tryit("A row of a magic square reads <b>6, ?, 8</b> and the magic number is 21. "
            "What is the missing number?",
            "6 + ? + 8 = 21, so ? = 21 − 14 = <b>7</b>."))

    # ── Bloom ladder ────────────────────────────────────────────────────────
    A(H("Now you try — climb the ladder"))
    A(P("For cryptarithms, find clues (even/odd, size). For magic squares, find a line with one "
        "blank. Peek only after a real try!"))

    A(practice("Remember", [
        ("In a cryptarithm, can the same letter stand for two different digits?",
         "No — the same letter is always the same digit."),
        ("In a magic square, what is special about every row, column and diagonal?",
         "They all add up to the same total — the magic number."),
        ("Is A + A always even or always odd?", "Always even."),
        ("In the famous 1-to-9 magic square, what number sits in the centre?", "5."),
    ]))
    A(practice("Understand", [
        ("Solve the code: A + A + A + A = 8. What is A?",
         "4 × A = 8, so A = 2."),
        ("A magic square has magic number 15. A row reads 8, 1, ?. Find the missing number.",
         "8 + 1 + ? = 15, so ? = 6."),
        ("Why can't C + C = 9 be true for a single digit C?",
         "C + C is always even, but 9 is odd, so it's impossible."),
        ("The digits 1 to 9 add to 45. If they fill a 3×3 magic square, what is the magic "
         "number?",
         "45 ÷ 3 = 15."),
    ]))
    A(practice("Apply", [
        ("In a magic square with magic number 18, a column reads 7, ?, 4. Find the missing "
         "number.",
         "7 + ? + 4 = 18, so ? = 7."),
        ("Solve: T + T = 16. What digit is T? Then what is T + T + T?",
         "2 × T = 16, so T = 8. Then T + T + T = 24."),
        ("A diagonal of a magic square reads ?, 5, 9 and the magic number is 18. Find the "
         "missing corner.",
         "? + 5 + 9 = 18, so ? = 4."),
        ("In the code D D + D = ? , with D = 2, what is the answer? (D D means the 2-digit "
         "number with both digits D.)",
         "DD = 22, plus D = 2, so 22 + 2 = 24."),
    ]))
    A(practice("Analyze", [
        ("Here is part of a magic square (magic number 15):<br>"
         "top row 4, 9, 2 &nbsp;|&nbsp; middle row ?, 5, ? &nbsp;|&nbsp; bottom row 8, 1, ?. "
         "Find all three blanks.",
         "Left column 4, ?, 8 → ? = 3. Right column 2, ?, ? with middle-right and bottom-right "
         "both unknown — use the middle row: 3 + 5 + ? = 15 → middle-right = 7. Bottom row "
         "8 + 1 + ? = 15 → bottom-right = 6. So the square is 4 9 2 / 3 5 7 / 8 1 6."),
        ("In the code A B + B A, both A and B are digits. Pip says the answer is <em>always</em> a "
         "2-digit number with the same digit in both places (like 99 or 77). Is Pip right? "
         "Test with A = 2, B = 5, and then with A = 5, B = 8.",
         "AB = 25, BA = 52, sum = 77 — two same digits, so it looks true at first. But try "
         "A = 5, B = 8: 58 + 85 = <b>143</b> — that's a <em>3-digit</em> number! So Pip is wrong. "
         "The real rule is <b>AB + BA = 11 × (A + B)</b>: the answer is always a multiple of 11. "
         "It is a 2-digit “repeated” number (like 77) <em>only when</em> A + B is less than 10; "
         "when A + B is 10 or more it becomes a 3-digit multiple of 11 (such as 143)."),
        ("Could a 3×3 magic square made from 1-to-9 have a magic number of 12? Explain.",
         "No. The only magic number for 1-to-9 is 45 ÷ 3 = 15. A different total would mean the "
         "nine numbers don't add to 45, but 1 + 2 + … + 9 is always 45."),
        ("Show that the code S O + S O = O O is impossible. Explain why (use the place values).",
         "Write the values: SO = 10S + O, so SO + SO = 2 × (10S + O) = 20S + 2O. And OO = 11 × O. "
         "Setting them equal: 20S + 2O = 11O, which tidies up to <b>20S = 9O</b>. For S and O to "
         "be single digits with S ≠ 0, we'd need 20S to be a multiple of 9 between 0 and 81 — but "
         "20 × 1 = 20, 20 × 2 = 40, 20 × 3 = 60, 20 × 4 = 80 are none of them multiples of 9. "
         "The only whole-number solution is S = 0, O = 0, which isn't a real 2-digit code. So no "
         "solution exists."),
    ]))
    A(practice("Create", [
        ("Invent your own one-letter code (like “?+?+?=12”) and write its answer.",
         "Many answers, e.g. K + K + K = 12 → K = 4; or P + P = 18 → P = 9."),
        ("Take the famous square 2 7 6 / 9 5 1 / 4 3 8 and rub out any two numbers to make a "
         "puzzle for a friend. Write which two you erased and how they'd find them.",
         "Example: erase the 7 (top middle) and the 3 (bottom middle). Friend uses the middle "
         "column 7 + 5 + 3 = 15: top-middle from top row 2 + ? + 6 = 15 → 7; bottom-middle "
         "from bottom row 4 + ? + 8 = 15 → 3."),
    ]))

    A(challenge(
        P("Complete this magic square. The <b>magic number is 15</b>, and the only numbers used "
          "are 1 to 9, each once. You are given just the diagonal and one corner:") +
        figure(magic_square([[2, "", ""], ["", 5, ""], ["", "", 8]]),
               "Given: 2 (top-left), 5 (centre), 8 (bottom-right). Magic number 15.") +
        tryit("Use the lines through the numbers you already have, one blank at a time.",
              "The main diagonal 2 + 5 + 8 = 15 already checks out. The other diagonal is "
              "?, 5, ? totalling 15, so those two corners add to 10 → they are 6 and 4. Place "
              "6 (top-right) and 4 (bottom-left) so each edge works: top row 2 + ? + 6 = 15 → 7; "
              "left column 2 + ? + 4 = 15 → 9; then 9, 5, ? = 15 → 1; bottom 4, ?, 8 = 15 → 3. "
              "The completed square is <b>2 7 6 / 9 5 1 / 4 3 8</b>.")))

    A(kiwi("Case closed, detective! You can crack letter-codes using even/odd and size clues, "
           "and you can complete any magic square by hunting for a line with a single blank. "
           "Next we'll sort things into overlapping circles — the wonderful world of "
           "<b>Venn diagrams</b>. 🎯"))

    chapter("Part 5 · Brain Benders", 17, "Cryptarithms & Magic Squares",
            "Combinatorics · Brain Benders", "".join(b))
