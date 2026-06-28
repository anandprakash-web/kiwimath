#!/usr/bin/env python3
"""L3 Chapter 1 — Knowing Your Numbers (Number Theory · Number Sense). Bridges
from Level 2 place value and climbs into lakhs/millions, comparing, rounding &
estimation."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, pv_table, place_arrows, number_line, compare)


def build(chapter):
    b = []; A = b.append

    A(big_q("Roughly how many <em>heartbeats</em> have you had since you were born? "
            "Take a guess… then let's find out together. The answer is a number so big it "
            "barely fits on the page — and by the end of this chapter you'll read it, write it, "
            "and round it like an expert."))
    A(kiwi("Hi explorer, I'm <b>Kiwi</b>! 🧭 Welcome to Level 3. You already met numbers in Level 2 — "
           "now we go <b>bigger</b>, meet brand-new kinds of numbers, and learn the secret tricks the "
           "experts use. We'll never jump ahead; every new idea grows out of one you already know. "
           "Let's warm up where you're strong: <b>place value</b>."))

    A(H("A 30-second warm-up: place value still rules"))
    A(P("Every digit's worth depends on its <b>place</b>. Pull the number 6,408 apart and you can see "
        "exactly what each digit is really worth — this is its <b>expanded form</b>:"))
    A(figure(place_arrows(6408), "6408 = 6000 + 400 + 0 + 8"))
    A(P("Notice the <b>0</b> in the tens place. It's not 'nothing' — it's a <em>placeholder</em> that keeps "
        "the 4 in the hundreds and the 6 in the thousands. Remove it and 6408 collapses into 648. "
        "Zeros are the quiet heroes of our number system."))

    A(H("Going bigger: thousands, lakhs, millions"))
    A(P("Past the thousands, the places keep growing ten times each step. Two naming systems share the "
        "very same number — they just group the digits differently:"))
    A(figure(pv_table(254178, cols=("Lakhs", "Ten-Th", "Thousands", "Hundreds", "Tens", "Ones")),
             "2,54,178 — the Indian way of grouping"))
    A(P("• <b>Indian system:</b> group from the right as 2,54,178 and read “two <b>lakh</b> fifty-four "
        "thousand one hundred seventy-eight”.<br>"
        "• <b>International system:</b> group in threes — 254,178 — and read “two hundred fifty-four "
        "<b>thousand</b>, one hundred seventy-eight”."))
    A(P("The <em>same digits</em> are just <b>grouped differently</b>. After the thousands the two "
        "systems part ways — see them side by side:"))
    A(_grouping_table())
    A(kiwi("Same number, two outfits. In the <b>Indian</b> system the big jumps are "
           "<b>lakh</b> and <b>crore</b>: a <b>lakh</b> is 1,00,000 = one hundred thousand, and a "
           "<b>crore</b> is 1,00,00,000 = one hundred lakh (that's <b>ten million</b>). In the "
           "<b>international</b> system the jumps are <b>thousand</b> and <b>million</b>: a "
           "<b>million</b> is 1,000,000 = ten lakh. So <b>1 crore = 10 million</b>. The grouping commas "
           "even land in different spots — Indian numbers go 2-2-3 from the right (12,34,567) while "
           "international numbers go in threes (1,234,567). Keep both in your toolkit — Olympiads use "
           "both."))
    A(example("read 70,05,302 (Indian system)", steps([
        "Group from the right: 70,05,302.",
        "Places: 7 ten-lakhs, 0 lakhs, 0 ten-thousands, 5 thousands, 3 hundreds, 0 tens, 2 ones.",
        "Read it: “seventy lakh five thousand three hundred two.”",
        "The two zeros in the lakhs and ten-thousands places are placeholders — they keep the 7 way up "
        "in the ten-lakhs seat.",
    ])))
    A(tryit("Write “three lakh forty thousand twenty” in digits.",
            "3,40,020. (Careful with the placeholders: nothing in the hundreds, and a 2 in the tens.)"))

    A(H("Comparing & ordering big numbers"))
    A(P("To compare, first count digits — more digits wins. Same digit-count? Line them up and compare "
        "<b>from the left</b>; the first place that differs decides it."))
    A(figure(compare(58213, 58320), "Tie at 5, 8, 2… then 1 &lt; 3, so 58,213 is smaller."))
    A(tryit("Put these in ascending order: 90,899 · 9,899 · 90,999 · 9,999.",
            "Count digits first: 9,899 and 9,999 are 4-digit (smaller). Order: "
            "<b>9,899 &lt; 9,999 &lt; 90,899 &lt; 90,999</b>."))

    A(H("The expert move: rounding & estimating"))
    A(P("Experts rarely compute the exact answer first — they <b>estimate</b> to know what to expect, "
        "then check. To <b>round</b>, look at the digit just to the <em>right</em> of the place you're "
        "rounding to: 5 or more rounds <b>up</b>, 4 or less stays the same."))
    A(figure(number_line(40, 50, 1, [(47, "47", "#E0556E")]),
             "47 is closer to 50 than to 40 → rounds to 50."))
    A(example("estimate 612 × 39 in your head", steps([
        "Round each number to something friendly: 612 ≈ 600, 39 ≈ 40.",
        "Multiply the easy numbers: 600 × 40 = <b>24,000</b>.",
        "So the real answer should be <em>near</em> 24,000. (It's exactly 23,868 — our estimate nailed "
        "the size!)",
        "Surprise power: in two seconds you knew the answer wasn't 2,400 or 240,000. Estimation is your "
        "built-in mistake-detector.",
    ])))
    A(kiwi("Golden habit: <b>estimate first, compute second, then compare</b>. If your exact answer is "
           "far from your estimate, you probably slipped — go back and check."))

    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What is the place value of 7 in 4,73,160?", "7 is in the ten-thousands place → 70,000."),
        ("How many zeros are in one lakh?", "Five: 1,00,000."),
        ("Round 384 to the nearest hundred.", "400 (the tens digit 8 is ≥ 5, so round up)."),
        ("Which is greater: 6,05,000 or 60,50,000?", "60,50,000 (it has more digits — 7 vs 6)."),
    ]))
    A(practice("Understand", [
        ("Write 5,06,090 in expanded form.", "500000 + 6000 + 90 = 5,00,000 + 6,000 + 90."),
        ("Write “forty lakh seven thousand five” in digits.", "40,07,005."),
        ("Round 7,649 to the nearest thousand.", "8,000 (hundreds digit 6 ≥ 5)."),
        ("Is 1 million bigger or smaller than 1 lakh? By how many times?", "Bigger — 1 million = 10 lakh, so 10 times bigger."),
        ("How many millions make 1 crore? (1 crore = 1,00,00,000.)", "Ten — 1 crore = 10 million (both are 10,000,000)."),
    ]))
    A(practice("Apply", [
        ("Estimate 297 + 488 + 612 by rounding each to the nearest hundred.", "300 + 500 + 600 = 1,400 (exact is 1,397)."),
        ("Estimate 81 × 49.", "80 × 50 = 4,000 (exact 3,969)."),
        ("Arrange in descending order: 2,34,567 · 2,43,567 · 2,34,765.",
         "Compare from the left: 2,43,567 &gt; 2,34,765 &gt; 2,34,567."),
        ("A stadium holds 48,750 fans. Round it to the nearest thousand for a headline.", "About 49,000 fans."),
    ]))
    A(practice("Analyze", [
        ("I rounded a number to the nearest ten and got 80. What is the largest whole number it could have been?",
         "84 (anything 85 or more would round to 90)."),
        ("Without computing exactly, which is bigger: 503 × 198 or 99,000? Use estimation.",
         "503 × 198 ≈ 500 × 200 = 1,00,000, which is more than 99,000. So 503 × 198 is bigger (it's 99,594)."),
        ("Using digits 0, 2, 5, 7, 9 once each, make the largest and smallest 5-digit numbers.",
         "Largest: 97,520. Smallest can't start with 0, so 20,579."),
    ]))
    A(practice("Create", [
        ("Make a 6-digit number that reads the same forwards and backwards (a palindrome) and is bigger "
         "than 5 lakh. What did you make?", "Any like 5,23,325 or 9,08,809 — first and last digits match, "
         "second and fifth match, third and fourth match, and it's &gt; 5,00,000."),
        ("Invent a real-life headline where rounding makes the number friendlier, and write both the exact "
         "and the rounded number.", "E.g. “City library lends 1,98,742 books a year” → headline "
         "“Nearly 2,00,000 books a year!”"),
    ]))

    A(challenge(
        P("A number machine does this: it takes a 3-digit number, <b>reverses</b> its digits, and "
          "subtracts the smaller from the larger. Try 742 → 742 − 247 = 495. Now try 631, then 805, then "
          "any 3-digit number whose first and last digits differ. What surprising thing do you notice "
          "about the answer's <em>middle digit</em> — and the sum of its outer digits?") +
        tryit("Test a few and look hard.",
              "The middle digit is always <b>9</b>, and the first and last digits always add up to <b>9</b> "
              "too! (631 → 631−136 = 495; 805 → 805−508 = 297; 9+5+... the outer digits 4 and 5 sum to 9.) "
              "Every such difference is a multiple of 99, and that's the hidden reason. You just discovered "
              "a number-theory secret — welcome to Level 3! 🎉")))

    A(kiwi("Brilliant start. You can now read giant numbers in two systems, compare and order them, and "
           "round &amp; estimate like an expert. Next stop: a whole new kind of number that lives to the "
           "<em>left</em> of zero — the <b>integers</b>. 🧊"))

    chapter("Part 1 · Number Sense & Integers", 1, "Knowing Your Numbers",
            "Number Theory · Number Sense", "".join(b))


def _grouping_table():
    """Side-by-side: the same place columns named the Indian way vs the international way."""
    rows = [
        ("1", "One", "One"),
        ("10", "Ten", "Ten"),
        ("100", "Hundred", "Hundred"),
        ("1,000", "Thousand", "Thousand"),
        ("10,000", "Ten thousand", "Ten thousand"),
        ("1,00,000", "<b>Lakh</b>", "Hundred thousand"),
        ("10,00,000", "Ten lakh", "<b>Million</b>"),
        ("1,00,00,000", "<b>Crore</b>", "Ten million"),
        ("10,00,00,000", "Ten crore", "Hundred million"),
    ]
    head = ("<tr><th>Value</th><th>Indian name</th><th>International name</th></tr>")
    body = "".join(
        f"<tr><td>{v}</td><td>{ind}</td><td>{intl}</td></tr>" for v, ind, intl in rows)
    return ('<table class="pv" style="font-size:13px">'
            '<caption style="caption-side:top;font-size:12px;color:#6b6b6b;padding-bottom:4px">'
            'Indian vs International grouping — same place, two names</caption>'
            f"{head}{body}</table>")
