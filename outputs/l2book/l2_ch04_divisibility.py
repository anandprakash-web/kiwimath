#!/usr/bin/env python3
"""Chapter 4 — Divisibility Magic Tricks  (Number Theory · Last-Digit Detective)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, number_line, array_dots, pattern_seq,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Your friend writes a giant number — <b>3,756,924</b> — and asks: “Can this be split evenly "
            "by 3? By 4? By 9?” You have no calculator… yet you answer in <em>seconds</em>. "
            "How? Magic? No — <b>divisibility tricks</b>! Let's learn them."))
    A(kiwi("Hi, it's <b>Kiwi</b>! A number is <b>divisible</b> by another when it divides exactly, with "
           "<em>no remainder</em>. Instead of doing long division every time, mathematicians spotted "
           "clever shortcuts hidden in the digits. Once you know them, you can check a huge number in "
           "seconds. 🪄"))

    # ── EVEN / ODD ───────────────────────────────────────────────
    A(H("First, the simplest split of all — even and odd"))
    A(P("Numbers come in two great tribes. <b>Even</b> numbers can be split into two equal groups with "
        "nothing left over — they are exactly the numbers divisible by <b>2</b>. <b>Odd</b> numbers "
        "always have one left over. Look how even numbers pair up perfectly, but odd numbers leave a "
        "lonely dot:"))
    A(figure(array_dots(2, 4), "8 dots make two equal rows — 8 is EVEN (divisible by 2)"))
    A(figure(array_dots(1, 7) + array_dots(1, 0), "7 dots can't pair up evenly — one is always left over, so 7 is ODD"))
    A(P("The secret is in the <b>last digit</b>. If a number ends in <b>0, 2, 4, 6 or 8</b>, it's even. "
        "If it ends in <b>1, 3, 5, 7 or 9</b>, it's odd. You only ever look at the final digit!"))
    A(figure(number_line(0, 10, 1, [(0, "E", GRASS), (2, "E", GRASS), (4, "E", GRASS), (6, "E", GRASS),
                                     (8, "E", GRASS), (10, "E", GRASS)]),
             "Even numbers (E) land on every second step: 0, 2, 4, 6, 8, 10, …"))
    A(kiwi("This is your first <b>last-digit detective</b> rule — and the easiest one. The whole number "
           "could be a million digits long, but only its <em>last</em> digit decides even or odd!"))
    A(tryit("Is <b>4,873</b> even or odd? Is <b>21,560</b> even or odd?",
            "4,873 ends in 3 → <b>odd</b>. 21,560 ends in 0 → <b>even</b>."))

    # ── DIVISIBLE BY 2, 5, 10 ────────────────────────────────────
    A(H("The last-digit detectives: tricks for 2, 5 and 10"))
    A(P("These three rules all live in the very last digit — quick as a blink:"))
    A(P("• <b>Divisible by 2</b> → last digit is even (0, 2, 4, 6, 8).<br>"
        "• <b>Divisible by 5</b> → last digit is <b>0 or 5</b>.<br>"
        "• <b>Divisible by 10</b> → last digit is <b>0</b>."))
    A(figure(pattern_seq([("5", GRASS), ("10", GRASS), ("15", GRASS), ("20", GRASS)], q=False),
             "Multiples of 5 always end in 5 or 0 — that's the whole trick!"))
    A(example("a quick triple-check on 90", steps([
        "Ends in 0, which is even → 90 is divisible by <b>2</b> ✓ (90 ÷ 2 = 45).",
        "Ends in 0 → divisible by <b>5</b> ✓ (90 ÷ 5 = 18).",
        "Ends in 0 → divisible by <b>10</b> ✓ (90 ÷ 10 = 9).",
        "A number ending in 0 is always divisible by all three!",
    ])))
    A(kiwi("Notice: if a number ends in 0, it passes the 2-test, the 5-test <em>and</em> the 10-test at "
           "once. Zero is the super-friendly ending!"))
    A(tryit("Which of 2, 5, 10 divide <b>365</b>?",
            "365 ends in 5: not even (so not 2), ends in 5 (so yes 5), not 0 (so not 10). "
            "Only <b>5</b> divides it. (365 ÷ 5 = 73.)"))

    # ── DIVISIBLE BY 3 and 9 ─────────────────────────────────────
    A(H("The digit-sum detectives: tricks for 3 and 9"))
    A(P("Here's where it gets really clever. For 3 and 9 the last digit won't help — instead you "
        "<b>add up all the digits</b> and check that sum:"))
    A(P("• <b>Divisible by 3</b> → the <em>sum of the digits</em> is divisible by 3.<br>"
        "• <b>Divisible by 9</b> → the <em>sum of the digits</em> is divisible by 9."))
    A(example("is 4,521 divisible by 3?", steps([
        "Add the digits: 4 + 5 + 2 + 1 = <b>12</b>.",
        "Is 12 divisible by 3? Yes (12 ÷ 3 = 4).",
        "So 4,521 <b>is</b> divisible by 3. ✓  (Check: 4521 ÷ 3 = 1507.)",
    ])))
    A(example("is 6,138 divisible by 9?", steps([
        "Add the digits: 6 + 1 + 3 + 8 = <b>18</b>.",
        "Is 18 divisible by 9? Yes (18 ÷ 9 = 2).",
        "So 6,138 <b>is</b> divisible by 9. ✓  (Check: 6138 ÷ 9 = 682.)",
    ])))
    A(kiwi("Super shortcut: if a number passes the <b>9</b>-test, it automatically passes the "
           "<b>3</b>-test too (because 9 is itself divisible by 3). But not the other way round — "
           "6 passes the 3-test but not the 9-test."))
    A(P("If the digit sum is still big, just add <em>its</em> digits again! For 9: a number like 9,999 "
        "has digit sum 36, and 3 + 6 = 9 — divisible by 9. ✓"))
    A(tryit("Use the digit-sum trick: is <b>738</b> divisible by 3? By 9?",
            "Digit sum = 7 + 3 + 8 = 18. 18 ÷ 3 = 6 → divisible by 3 ✓. 18 ÷ 9 = 2 → divisible by 9 "
            "✓. So 738 passes <b>both</b>."))

    # ── DIVISIBLE BY 4 ───────────────────────────────────────────
    A(H("The last-TWO-digits detective: the trick for 4"))
    A(P("For <b>4</b>, you don't need the whole number — just look at the number made by the "
        "<b>last two digits</b>. If that little 2-digit number is divisible by 4, the whole number is "
        "too. (Why? Because 100 is divisible by 4, so the hundreds and beyond never affect it.)"))
    A(example("is 7,316 divisible by 4?", steps([
        "Look only at the last two digits: <b>16</b>.",
        "Is 16 divisible by 4? Yes (16 ÷ 4 = 4).",
        "So 7,316 is divisible by 4. ✓  (Check: 7316 ÷ 4 = 1829.)",
    ])))
    A(example("is 5,250 divisible by 4?", steps([
        "Last two digits: <b>50</b>.",
        "Is 50 divisible by 4? 4 × 12 = 48 and 4 × 13 = 52, so 50 leaves a remainder of 2 — no.",
        "So 5,250 is <b>not</b> divisible by 4. ✗",
    ])))
    A(kiwi("Handy: any number ending in <b>00</b> is divisible by 4 (since 100 is). So 300, 1,700 and "
           "8,000 all sail through the 4-test."))
    A(tryit("Is <b>2,932</b> divisible by 4?",
            "Last two digits = 32, and 32 ÷ 4 = 8. So <b>yes</b>, 2,932 is divisible by 4."))

    # ── SUMMARY TABLE FIGURE (inline) ────────────────────────────
    A(H("Your magic-trick cheat sheet"))
    A(P("Here are all the rules in one place. Pin this in your brain!"))
    A(figure(_rules_table(),
             "Six divisibility detectives — last digit, last two digits, or digit sum."))

    # ── BIG-NUMBER FINALE ────────────────────────────────────────
    A(H("Back to the giant number"))
    A(P("Remember <b>3,756,924</b> from the start? Let's dazzle your friend:"))
    A(example("testing 3,756,924", steps([
        "By <b>2</b>? Last digit is 4 (even) → <b>yes</b>.",
        "By <b>5</b>? Last digit is 4 (not 0 or 5) → <b>no</b>.",
        "By <b>4</b>? Last two digits are 24, and 24 ÷ 4 = 6 → <b>yes</b>.",
        "By <b>3</b>? Digit sum = 3+7+5+6+9+2+4 = 36, and 36 ÷ 3 = 12 → <b>yes</b>.",
        "By <b>9</b>? Same digit sum 36, and 36 ÷ 9 = 4 → <b>yes</b>.",
        "All in your head, no long division. That's the magic! ✨",
    ])))
    A(kiwi("Mental-maths bonus: to test divisibility by <b>6</b>, just check 2 <em>and</em> 3 together "
           "(6 = 2 × 3). 3,756,924 passed both, so it's divisible by 6 as well!"))

    # ── PRACTICE LADDER ──────────────────────────────────────────
    A(H("Climb the ladder — practice!"))
    A(P("Try each one with the tricks — no long division allowed!"))

    A(practice("Remember", [
        ("A number ending in 0, 2, 4, 6 or 8 is divisible by which number?", "2 (these are the even digits)."),
        ("To test divisibility by 5, which digit do you check?", "The last digit — it must be 0 or 5."),
        ("To test divisibility by 9, what do you add up?", "All the digits, then check if the sum is divisible by 9."),
        ("Is 8 even or odd?", "Even."),
        ("Which last digit means divisible by 10?", "0."),
    ]))
    A(practice("Understand", [
        ("Is 4,560 divisible by 2, by 5 and by 10?",
         "Ends in 0: even → yes by 2; 0 → yes by 5; 0 → yes by 10. All three!"),
        ("Find the digit sum of 7,254 and say if it's divisible by 3.",
         "7+2+5+4 = 18, and 18 ÷ 3 = 6 → <b>yes</b>, divisible by 3."),
        ("Is 1,000 divisible by 4? Explain using the trick.",
         "Last two digits = 00, which is divisible by 4 → <b>yes</b>."),
        ("Which is odd: 3,330 or 3,331?",
         "3,331 ends in 1 → odd. (3,330 ends in 0 → even.)"),
    ]))
    A(practice("Apply", [
        ("Test 5,832 for divisibility by 3, 4 and 9.",
         "Digit sum 5+8+3+2 = 18 → divisible by 3 ✓ and 9 ✓. Last two digits 32 ÷ 4 = 8 → divisible "
         "by 4 ✓. (Passes all three.)"),
        ("Is 2,475 divisible by 5? By 9?",
         "Ends in 5 → divisible by 5 ✓. Digit sum 2+4+7+5 = 18 → divisible by 9 ✓."),
        ("Is 6,074 divisible by 4?",
         "Last two digits = 74; 4 × 18 = 72, so 74 leaves remainder 2 → <b>no</b>."),
        ("Which of 2, 3, 5, 9 divide 9,000?",
         "Ends in 0 → by 2 ✓ and by 5 ✓. Digit sum 9 → by 3 ✓ and by 9 ✓. All four divide it!"),
        ("A number is divisible by both 2 and 3. Is it divisible by 6? Test it on 4,512.",
         "4,512 is even (ends in 2) ✓ and digit sum 4+5+1+2 = 12 is divisible by 3 ✓, so it's "
         "divisible by 6 (4,512 ÷ 6 = 752)."),
    ]))
    A(practice("Analyze", [
        ("Find the missing digit so that 3<b>?</b>2 is divisible by 3. Give all answers.",
         "Digit sum = 3 + ? + 2 = 5 + ?. We need 5 + ? divisible by 3, so ? = 1 (6), 4 (9) or 7 (12). "
         "Answers: <b>1, 4, 7</b> → 312, 342, 372."),
        ("Can a number be divisible by 9 but NOT by 3? Explain.",
         "No — every multiple of 9 is also a multiple of 3 (since 9 = 3 × 3). Passing the 9-test "
         "guarantees the 3-test."),
        ("The number 4,__0 is divisible by 4 and ends in 0. What could the tens digit be?",
         "Last two digits are __0; we need that divisible by 4. The even tens make 20, 40, 60, 80, 00 "
         "(all ÷ 4) — so the tens digit can be <b>0, 2, 4, 6 or 8</b>."),
        ("Is 1,111,111 divisible by 3? (Use the digit-sum trick.)",
         "Digit sum = seven 1s = 7, and 7 is not divisible by 3 → <b>no</b>."),
    ]))
    A(practice("Create", [
        ("Write a 4-digit number that is divisible by 2, 3 and 5 all at once, and show why.",
         "It must end in 0 (for 2 and 5) and have a digit sum divisible by 3. Example: 1,230 — ends in "
         "0 ✓, digit sum 1+2+3+0 = 6 divisible by 3 ✓."),
        ("Make the largest 3-digit number divisible by 9 using only digits 4, 5 and a 0.",
         "Arrange big→small for largest: 540. Digit sum 5+4+0 = 9 → divisible by 9 ✓. Answer: <b>540</b>."),
        ("Invent a number that passes the 4-test but fails the 3-test, and check both.",
         "Example: 1,016. Last two digits 16 ÷ 4 = 4 → passes 4 ✓. Digit sum 1+0+1+6 = 8, not "
         "divisible by 3 → fails 3 ✓."),
    ]))

    A(challenge(
        P("Detective puzzle! I am a 3-digit number. I am divisible by <b>5</b> AND <em>even</em>, so I "
          "must end in <b>0</b>. I am also divisible by <b>9</b>. The smallest such number "
          "is… who am I?") +
        tryit("Combine the rules step by step.",
              "Even <b>and</b> divisible by 5 means I must end in <b>0</b>. Divisible by 9 means my "
              "digit sum is a multiple of 9. The smallest 3-digit number ending in 0 with digit sum "
              "divisible by 9: try 1_0 → need first+0+0 part… 180 has digit sum 1+8+0 = 9 ✓ and ends in "
              "0 ✓. So the answer is <b>180</b>. (Check: 180 ÷ 5 = 36, 180 ÷ 9 = 20, and 180 is even.)")))

    A(kiwi("Nicely done — you used the digit-sum and last-digit rules just as a real <b>last-digit "
           "detective</b> would, testing 2, 3, 4, 5, 9 and 10 faster than any calculator can power on. "
           "That's all of Part 1, Big Numbers. The world of fractions and shapes awaits! 🎉"))

    chapter("Part 1 · Big Numbers", 4, "Divisibility Magic Tricks",
            "Number Theory · Last-Digit Detective", "".join(b))


def _rules_table():
    """A small inline SVG cheat-sheet table of the divisibility rules."""
    rows = [
        ("÷ 2", "Last digit is 0, 2, 4, 6 or 8", GRASS),
        ("÷ 3", "Digit sum is divisible by 3", SKY),
        ("÷ 4", "Last two digits divisible by 4", PURPLE),
        ("÷ 5", "Last digit is 0 or 5", ORANGE),
        ("÷ 9", "Digit sum is divisible by 9", BERRY),
        ("÷ 10", "Last digit is 0", GOLD),
    ]
    W, rh, top, bw, bh = 440, 42, 18, 60, 30
    H = top * 2 + len(rows) * rh
    s = [f'<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="14" '
         f'fill="#fff" stroke="#00000018" stroke-width="1.5"/>']
    for i, (k, txt, col) in enumerate(rows):
        yc = top + rh // 2 + i * rh                       # vertical centre of this row
        s.append(f'<rect x="20" y="{yc-bh//2}" width="{bw}" height="{bh}" rx="9" '
                 f'fill="{col}" fill-opacity="0.16" stroke="{col}" stroke-width="1.8"/>')
        s.append(f'<text x="{20+bw//2}" y="{yc+6}" text-anchor="middle" font-size="17" '
                 f'font-weight="800" fill="{col}">{k}</text>')
        s.append(f'<text x="98" y="{yc+5}" text-anchor="start" font-size="14.5" '
                 f'fill="#2b2622">{txt}</text>')
        if i < len(rows) - 1:
            s.append(f'<line x1="20" y1="{top+(i+1)*rh}" x2="{W-20}" y2="{top+(i+1)*rh}" '
                     f'stroke="#00000010" stroke-width="1"/>')
    return f'<svg class="fig" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">{"".join(s)}</svg>'
