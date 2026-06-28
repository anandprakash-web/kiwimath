#!/usr/bin/env python3
"""L3 Chapter 11 — Patterns & Sequences (Algebra · What Comes Next). Bridges the
Level-2 'find the rule' habit into real sequences: arithmetic sequences, the nth
term, triangular & square numbers, growing shape patterns, and the surprise of
summing 1+2+...+n (Gauss). Uses pattern_seq, number_line, array_dots."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, pattern_seq, number_line, array_dots,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE)


def build(chapter):
    b = []; A = b.append

    A(big_q("Your teacher says: 'Add up every whole number from 1 to 100 — by hand.' Groan! "
            "But a 7-year-old named Carl Gauss did it in <em>seconds</em> and wrote a single number: "
            "<b>5050</b>. He didn't add 100 things — he spotted a <b>pattern</b>. By the end of this "
            "chapter, you'll do the very same trick, and many more, by hunting the hidden rule inside a "
            "sequence."))
    A(kiwi("Welcome back, explorer! 🥝 In Level 2 you became a pattern detective — finding the rule and "
           "predicting 'what comes next.' Now we go further: we'll <b>jump far ahead</b> in a pattern "
           "without listing every step, give patterns proper names, and meet numbers that grow in the shape "
           "of triangles and squares. Same detective skill — bigger cases."))

    # ── 1. Sequences and terms ──────────────────────────
    A(H("Sequences and their terms"))
    A(P("A <b>sequence</b> is just a list of numbers in a set order, made by a rule. Each number is a "
        "<b>term</b>. We talk about the 1st term, 2nd term, 3rd term, and so on. Here's the sequence of "
        "even numbers, with the rule '+2 each time':"))
    A(figure(number_line(0, 12, 2, [(2, "1st", ORANGE), (4, "2nd", ORANGE),
                                     (6, "3rd", ORANGE), (8, "4th", ORANGE)]),
             "The sequence 2, 4, 6, 8, … Each term is one hop of +2 along the line."))
    A(kiwi("Two words to keep: a <b>sequence</b> is the whole list; a <b>term</b> is one number in it. "
           "The <em>position</em> (1st, 2nd, 10th…) is just as important as the value."))

    # ── 2. Arithmetic sequences ─────────────────────────
    A(H("Arithmetic sequences: the same jump every time"))
    A(P("The friendliest sequences add the <em>same</em> number at every step. That fixed jump is called "
        "the <b>common difference</b>, and such a list is an <b>arithmetic sequence</b>. Watch "
        "<b>3, 7, 11, 15, …</b>"))
    A(figure(number_line(0, 24, 4, [(3, "3", BERRY), (7, "7", BERRY), (11, "11", BERRY),
                                     (15, "15", BERRY)]),
             "Equal hops of +4: the common difference is 4. Next terms: 19, 23."))
    A(example("find the common difference and the next two terms of 5, 12, 19, 26, …", steps([
        "Find the jump: 12 − 5 = 7, and 19 − 12 = 7. The common difference is <b>+7</b>.",
        "Next term: 26 + 7 = <b>33</b>.",
        "And the one after: 33 + 7 = <b>40</b>. So it continues 5, 12, 19, 26, <b>33, 40</b>.",
    ])))
    A(tryit("Find the common difference and the next term of <b>100, 90, 80, 70, …</b>",
            "Each step subtracts 10, so the common difference is <b>−10</b>. Next term: 70 − 10 = <b>60</b>."))

    # ── 3. The nth-term jump ────────────────────────────
    A(H("Jumping ahead: the nth term"))
    A(P("Here's the real power. Suppose you want the <b>20th term</b> of 2, 5, 8, 11, … Listing all 20 is "
        "slow. Instead, notice you start at 2 and then add the common difference <em>one fewer time</em> "
        "than the position — because the 1st term hasn't jumped yet."))
    A(example("find the 10th term of 2, 5, 8, 11, …", steps([
        "First term = 2; common difference = 3.",
        "To reach the 10th term you add the jump (10 − 1) = 9 times: 9 × 3 = 27.",
        "10th term = first term + 27 = 2 + 27 = <b>29</b>.",
        "Rule in words: <b>nth term = first term + (n − 1) × common difference</b>. No listing needed!",
    ])))
    A(kiwi("The nth-term rule is your teleporter: <b>start value + (position − 1) × jump</b>. It lets you "
           "land on the 100th term as easily as the 3rd. We use (n − 1) because the very first term hasn't "
           "jumped yet."))
    A(tryit("Use the rule to find the 8th term of <b>4, 9, 14, 19, …</b>",
            "First term 4, jump 5. 8th term = 4 + (8 − 1) × 5 = 4 + 35 = <b>39</b>."))

    # ── 4. Growing shape patterns & the nth shape ──────
    A(H("Growing shapes: counting without drawing"))
    A(P("Patterns live in shapes too. Picture rows of square tiles, each new figure adding a tile. Better "
        "still, picture matchstick squares in a row — but where neighbours <em>share</em> a side:"))
    A(figure(pattern_seq([("4", GRASS), ("7", PURPLE), ("10", SKY)], q=True),
             "Matchsticks needed: 1 square = 4, 2 squares = 7, 3 squares = 10. What about 4 squares?"))
    A(example("how many matchsticks for 4 squares, and for the nth?", steps([
        "Look at the jumps: 4 → 7 → 10 adds <b>3</b> each time (each new square shares one side, so it only "
        "needs 3 fresh sticks).",
        "So 4 squares = 10 + 3 = <b>13</b> matchsticks.",
        "The nth figure: start at 4 and add 3 a total of (n − 1) times → 4 + 3(n − 1) = <b>3n + 1</b>.",
        "Check: n = 3 gives 3 × 3 + 1 = 10. ✓ Now you can find 100 squares instantly: 3 × 100 + 1 = 301.",
    ])))
    A(tryit("A pattern of dots grows 2, 4, 6, 8, … (each step adds a row of 2). How many dots in the 6th "
            "figure?",
            "It's +2 each time starting at 2, so the nth figure has 2n dots. 6th = 2 × 6 = <b>12 dots</b>."))

    # ── 5. Triangular numbers ───────────────────────────
    A(H("Triangular numbers: stacking like bowling pins"))
    A(P("Stack dots like bowling pins — 1, then a row of 2 under it, then 3, then 4. The running totals "
        "<b>1, 3, 6, 10, 15, …</b> are the <b>triangular numbers</b>, because each makes a neat triangle."))
    A(figure(array_dots(1, 1, GOLD), "T₁ = 1 dot."))
    A(figure(array_dots(2, 2, GOLD), "Add a row → T₂ = 1 + 2 = 3 dots (shown in a 2×2 frame)."))
    A(figure(array_dots(3, 3, GOLD), "Add another → T₃ = 1 + 2 + 3 = 6 dots."))
    A(P("To get the next triangular number you just add the next counting number: "
        "T₄ = T₃ + 4 = 6 + 4 = <b>10</b>; T₅ = 10 + 5 = <b>15</b>. So the 6th triangular number is "
        "15 + 6 = <b>21</b>."))
    A(kiwi("Triangular numbers ARE the running sums 1, 1+2, 1+2+3, … So the nth triangular number is exactly "
           "'add up everything from 1 to n.' Hold that thought — it's about to give us Gauss's trick."))
    A(tryit("What is the 7th triangular number?",
            "Keep adding: …, T₅ = 15, T₆ = 21, T₇ = 21 + 7 = <b>28</b>."))

    # ── 6. Square numbers + the odd-number surprise ─────
    A(H("Square numbers and a hidden surprise"))
    A(P("Now arrange dots in full <b>square</b> grids: 1×1, 2×2, 3×3, … The counts <b>1, 4, 9, 16, 25, …</b> "
        "are the <b>square numbers</b> (the nth one is simply n × n)."))
    A(figure(array_dots(2, 2, SKY), "2 × 2 = 4 dots — the 2nd square number."))
    A(figure(array_dots(4, 4, SKY), "4 × 4 = 16 dots — the 4th square number."))
    A(P("Here's a jaw-dropper. Add up the <b>odd numbers</b> in order: 1, then 1+3, then 1+3+5, …"))
    A(example("add the odd numbers: 1, 1+3, 1+3+5, 1+3+5+7", steps([
        "1 = <b>1</b> = 1².",
        "1 + 3 = <b>4</b> = 2².",
        "1 + 3 + 5 = <b>9</b> = 3².",
        "1 + 3 + 5 + 7 = <b>16</b> = 4².",
        "Surprise! The sum of the first n odd numbers is always n² — a perfect square. The odd numbers "
        "are secretly square-number builders. 🤯",
    ])))
    A(tryit("Without adding one by one, what is 1 + 3 + 5 + 7 + 9 + 11?",
            "That's the first 6 odd numbers, so the sum is 6² = <b>36</b>."))

    # ── 7. Gauss's summing trick ────────────────────────
    A(H("Gauss's lightning trick: summing 1 + 2 + … + n"))
    A(P("Back to the big question. To add 1 + 2 + 3 + … + 100, Gauss paired the <b>first with the last</b>: "
        "1 + 100 = 101. Then 2 + 99 = 101. Then 3 + 98 = 101… every pair makes <b>101</b>!"))
    A(P("There are 100 numbers, so they form <b>50 pairs</b>, each adding to 101. The grand total is "
        "50 × 101 = <b>5050</b>. No long addition — just one clever pairing."))
    A(example("add 1 + 2 + 3 + … + 10 the Gauss way", steps([
        "Pair first + last: 1 + 10 = 11. Next pair: 2 + 9 = 11. Then 3 + 8 = 11, 4 + 7 = 11, 5 + 6 = 11.",
        "That's <b>5 pairs</b>, each summing to 11.",
        "Total = 5 × 11 = <b>55</b>. (And 55 is exactly the 10th triangular number — the same idea!)",
        "General rule: the sum 1 + 2 + … + n = <b>n × (n + 1) ÷ 2</b>. Check n = 10: 10 × 11 ÷ 2 = 55. ✓",
    ])))
    A(kiwi("So 'add 1 to n' = <b>n × (n + 1) ÷ 2</b> — and that's the nth triangular number too! "
           "Patterns connect: odd-number sums make squares, counting-number sums make triangles. "
           "Spotting structure beats brute force every single time."))
    A(tryit("Use Gauss's rule to add 1 + 2 + 3 + … + 50.",
            "Sum = 50 × 51 ÷ 2 = 2550 ÷ 2 = <b>1275</b>."))

    # ── Practice ladder ─────────────────────────────────
    A(H("Now climb the ladder"))
    A(P("Find the rule first — the jump, the nth-term, or the pairing — then answer. Peek only after you try!"))

    A(practice("Remember", [
        ("What comes next: 6, 11, 16, 21, ___ ?", "+5 each time → <b>26</b>."),
        ("Name the common difference of 4, 8, 12, 16, …", "<b>+4</b>."),
        ("List the first five triangular numbers.", "1, 3, 6, 10, 15."),
        ("What is the 4th square number?", "4 × 4 = <b>16</b>."),
    ]))
    A(practice("Understand", [
        ("Find the common difference and next term of 50, 44, 38, 32, …",
         "Each step −6, so next term = 32 − 6 = <b>26</b>."),
        ("What is the sum 1 + 2 + 3 + … + 5? Use the rule n(n+1)/2.",
         "5 × 6 ÷ 2 = <b>15</b> (also the 5th triangular number)."),
        ("The sum of the first n odd numbers equals what?", "n² — a perfect square."),
        ("Is 2, 4, 8, 16, … an arithmetic sequence? Why or why not?",
         "No — the jumps are +2, +4, +8 (not constant). It doubles each time instead."),
    ]))
    A(practice("Apply", [
        ("Find the 10th term of 3, 7, 11, 15, … using the nth-term rule.",
         "First 3, jump 4. 10th = 3 + (10 − 1) × 4 = 3 + 36 = <b>39</b>."),
        ("A matchstick pattern needs 3n + 1 sticks for n squares. How many for 20 squares?",
         "3 × 20 + 1 = <b>61</b> matchsticks."),
        ("What is the 8th triangular number?",
         "Keep adding to 7: T₇ = 28, T₈ = 28 + 8 = <b>36</b> (or 8 × 9 ÷ 2 = 36)."),
        ("Add 1 + 3 + 5 + 7 + 9 quickly.",
         "First 5 odd numbers, so the sum is 5² = <b>25</b>."),
    ]))
    A(practice("Analyze", [
        ("Find the missing term: 4, 9, ___, 19, 24 (arithmetic).",
         "Common difference is +5, so the missing term is 9 + 5 = <b>14</b>."),
        ("Carl claims the 100th term of 1, 4, 7, 10, … is 298. Check him with the nth-term rule.",
         "First 1, jump 3. 100th = 1 + (100 − 1) × 3 = 1 + 297 = <b>298</b>. He's right!"),
        ("Show that the 5th triangular number plus the 4th triangular number equals a square number.",
         "T₅ = 15 and T₄ = 10, so 15 + 10 = 25 = 5². (Two stacked triangles make a square — every time!)"),
        ("A sequence goes 2, 6, 12, 20, 30, … Find the rule for the jumps, then the next term.",
         "Jumps are +4, +6, +8, +10 (going up by 2). Next jump +12, so next term = 30 + 12 = <b>42</b>. "
         "(These are the 'rectangular' numbers n(n+1).)"),
    ]))
    A(practice("Create", [
        ("Invent an arithmetic sequence with common difference 9, and write its first four terms and its "
         "10th term.",
         "e.g. 5, 14, 23, 32, …; 10th = 5 + 9 × 9 = <b>86</b>. Any start works."),
        ("Draw (in your head) a growing dot pattern and write a rule for the nth figure.",
         "e.g. an L-shape adding 3 dots each time starting at 3 → nth figure has 3n dots. Any consistent "
         "rule is fine."),
        ("Use Gauss's pairing idea to add 1 + 2 + … + 20, and explain your pairing.",
         "Pair 1 + 20 = 21, and there are 10 such pairs → 10 × 21 = <b>210</b> (= 20 × 21 ÷ 2)."),
    ]))

    A(challenge(
        P("The grand theatre puzzle! A theatre has <b>30 rows</b>. The front row has <b>20 seats</b>, and "
          "each row behind has <b>2 more seats</b> than the one in front. How many seats are in the "
          "<em>back</em> row — and how many seats does the whole theatre hold? (Use the nth-term rule, then "
          "Gauss's summing idea.)") +
        tryit("Find the last row first, then sum all the rows.",
              "<b>Back row (30th term):</b> first row 20, common difference 2, so 30th = 20 + (30 − 1) × 2 = "
              "20 + 58 = <b>78 seats</b>. <b>Whole theatre:</b> we add an arithmetic sequence from 20 up to 78. "
              "Pair first + last: 20 + 78 = 98, and 30 rows make 15 pairs, so total = 15 × 98 = "
              "<b>1470 seats</b>. (Two ideas, one puzzle — the nth-term teleporter to find the back row, then "
              "Gauss's pairing to add them all. That's the power of patterns! 🎉)")))

    A(kiwi("Brilliant climb! You can now name sequences and terms, find the common difference, teleport to "
           "the nth term, count growing shapes, recognise triangular and square numbers, and sum a long run "
           "the Gauss way. Finding rules with words and pictures leads straight to writing them with "
           "<b>letters</b> — the language of algebra, where we go next. ➡️"))

    chapter("Part 4 · Rule Finders & Letter Maths", 11, "Patterns & Sequences",
            "Algebra · What Comes Next", "".join(b))
