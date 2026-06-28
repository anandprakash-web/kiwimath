#!/usr/bin/env python3
"""Chapter 3 — Number Families: Factors, Multiples & Primes  (Number Theory · Number Families)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, array_dots, factor_tree, venn2, number_line, ORANGE, SKY, GRASS)


def build(chapter):
    b = []
    A = b.append

    A(big_q("You have <b>12</b> chocolates and want to share them into equal rows with none left over. "
            "You could do 1 row of 12, or 2 rows of 6, or 3 rows of 4… How many <em>different</em> "
            "neat rectangles can you make? And why does the number <b>11</b> refuse to make any nice "
            "rectangle at all?"))
    A(kiwi("Hello again — <b>Kiwi</b> here! Every number belongs to families, just like you do. "
           "Some numbers are friendly and split lots of ways; others are loners. By the end of this "
           "chapter you'll know every number's family secrets. Let's meet them!"))

    # ── FACTORS ──────────────────────────────────────────────────
    A(H("Factors — the numbers that divide evenly"))
    A(P("A <b>factor</b> of a number divides into it <em>exactly</em>, leaving no remainder. "
        "For example, 3 is a factor of 12 because 12 ÷ 3 = 4 with nothing left over. But 5 is "
        "<em>not</em> a factor of 12, because 12 ÷ 5 = 2 remainder 2."))
    A(P("The best way to see factors is to build <b>rectangles</b>. Here are 12 dots arranged as "
        "3 rows of 4 — a perfect rectangle, so 3 and 4 are both factors of 12:"))
    A(figure(array_dots(3, 4), "3 × 4 = 12, so 3 and 4 are factors of 12"))
    A(P("We can also stand the same 12 dots up as 2 rows of 6:"))
    A(figure(array_dots(2, 6), "2 × 6 = 12, so 2 and 6 are factors of 12 too"))
    A(P("Each rectangle gives us a <b>factor pair</b> — two numbers that multiply to give 12. "
        "Let's collect them all:"))
    A(example("all the factor pairs of 12", steps([
        "1 × 12 = 12 → the pair (1, 12).",
        "2 × 6 = 12 → the pair (2, 6).",
        "3 × 4 = 12 → the pair (3, 4).",
        "Does 5 work? 12 ÷ 5 has a remainder — no. Does 7, 8…? No.",
        "So the factors of 12 are: <b>1, 2, 3, 4, 6, 12</b> — six factors in all.",
    ])))
    A(kiwi("Two friendly facts: <b>1</b> is a factor of <em>every</em> number, and every number is a "
           "factor of <em>itself</em>. So even a loner number always has at least those two factors."))
    A(tryit("List all the factors of <b>18</b>.",
            "Factor pairs: 1×18, 2×9, 3×6. So the factors are <b>1, 2, 3, 6, 9, 18</b>."))

    # ── MULTIPLES ────────────────────────────────────────────────
    A(H("Multiples — the skip-counting numbers"))
    A(P("A <b>multiple</b> of a number is what you get when you skip-count by it. The multiples of 4 "
        "are 4, 8, 12, 16, 20, … — you can keep going forever! On a number line, the multiples of 4 are "
        "the spots you land on when you hop 4 at a time:"))
    A(figure(number_line(0, 20, 4, [(4, "4", SKY), (8, "8", SKY), (12, "12", SKY),
                                     (16, "16", SKY), (20, "20", SKY)]),
             "Hopping by 4: the multiples of 4 are 4, 8, 12, 16, 20, …"))
    A(kiwi("Watch the difference! <b>Factors</b> of a number are <em>small</em> (they fit inside it) and "
           "there are only a few. <b>Multiples</b> are <em>big</em> (the number fits inside them) and "
           "there are endlessly many. Factors divide in; multiples step out."))
    A(tryit("Write the first five multiples of <b>7</b>.",
            "Skip-count by 7: <b>7, 14, 21, 28, 35</b>."))
    A(tryit("Is <b>45</b> a multiple of 9? Is it a multiple of 4?",
            "9 × 5 = 45, so yes, 45 is a multiple of 9. But 45 ÷ 4 = 11 remainder 1, so 45 is "
            "<b>not</b> a multiple of 4."))

    # ── PRIME vs COMPOSITE ───────────────────────────────────────
    A(H("Prime or composite? Meet the loners and the crowds"))
    A(P("Now back to our puzzle. The number 11 makes <em>no</em> neat rectangle except a single line of "
        "11 (1 × 11). Its only factors are 1 and itself. We call such a number <b>prime</b>."))
    A(P("• A <b>prime number</b> has <em>exactly two</em> factors: 1 and itself. (2, 3, 5, 7, 11, 13, …)<br>"
        "• A <b>composite number</b> has <em>more than two</em> factors — it can be built from smaller "
        "pieces. (4, 6, 8, 9, 12, …)"))
    A(P("Here's 7 dots — try to make a rectangle other than a single row. You can't! That's what makes 7 "
        "prime:"))
    A(figure(array_dots(1, 7), "7 only makes a 1 × 7 line — so 7 is prime"))
    A(P("And here's 9, which happily makes a 3 × 3 square, so 9 is composite:"))
    A(figure(array_dots(3, 3), "9 = 3 × 3, so 9 is composite (extra factor: 3)"))
    A(kiwi("Two facts worth remembering: <b>1 is neither prime nor composite</b> — it has only one "
           "factor (itself), so it fits in neither club. And <b>2 is the only even prime</b> — every "
           "other even number can be split by 2, giving it an extra factor."))
    A(P("The primes below 20 are worth memorising: <b>2, 3, 5, 7, 11, 13, 17, 19</b>."))
    A(tryit("Is <b>21</b> prime or composite? How do you know?",
            "21 = 3 × 7, so it has factors 1, 3, 7 and 21 — more than two. So 21 is <b>composite</b>."))
    A(tryit("Which of these are prime: 15, 17, 19, 25?",
            "15 = 3×5 (composite). 17 has only 1 and 17 → <b>prime</b>. 19 has only 1 and 19 → "
            "<b>prime</b>. 25 = 5×5 (composite). So the primes are <b>17 and 19</b>."))

    # ── PRIME FACTORIZATION ──────────────────────────────────────
    A(H("Breaking a number into its prime building blocks"))
    A(P("Every composite number can be broken down into a multiplication of <em>only primes</em>. "
        "This is called <b>prime factorization</b>, and the <b>factor tree</b> is our favourite tool. "
        "Keep splitting each number into two factors until every branch ends in a prime."))
    A(P("Let's break down <b>24</b>:"))
    A(figure(factor_tree(24, 4, 6, a2=2, b2=2, c2=2, d2=3),
             "24 splits into 4 and 6; 4 → 2×2 and 6 → 2×3"))
    A(example("prime factorization of 24", steps([
        "24 = 4 × 6 (a good first split).",
        "Now split each: 4 = 2 × 2, and 6 = 2 × 3.",
        "The branch-ends are all primes: 2, 2, 2, 3.",
        "So 24 = <b>2 × 2 × 2 × 3</b>.  (Check: 2 × 2 × 2 × 3 = 8 × 3 = 24 ✓)",
    ])))
    A(kiwi("Cool fact: no matter how you split a number first, you always end with the <em>same</em> set "
           "of prime building blocks. Try starting 24 as 2 × 12 instead — you'll still get 2, 2, 2, 3!"))
    A(tryit("Make a factor tree for <b>18</b> and write its prime factorization.",
            "18 = 2 × 9, and 9 = 3 × 3. So 18 = <b>2 × 3 × 3</b>. (Check: 2 × 9 = 18 ✓)"))

    # ── HCF / GCD ────────────────────────────────────────────────
    A(H("HCF — the biggest factor two numbers share"))
    A(P("Sometimes we want the <b>biggest</b> number that divides into two numbers <em>both</em>. "
        "It's called the <b>Highest Common Factor</b> (HCF), also known as the GCD — Greatest Common "
        "Divisor. To find it, list the factors of each number and pick the largest one they share."))
    A(P("Let's find the HCF of <b>12 and 18</b>. We can picture their factors in two overlapping circles "
        "(a Venn diagram). The numbers in the <em>middle</em> are the common factors:"))
    A(figure(venn2(2, 3, 2, "12", "18"),
             "Factors of 12 = {1,2,3,4,6,12}, of 18 = {1,2,3,6,9,18}. Shared: 1, 2, 3, 6"))
    A(example("HCF of 12 and 18", steps([
        "Factors of 12: 1, 2, 3, 4, 6, 12.",
        "Factors of 18: 1, 2, 3, 6, 9, 18.",
        "Common factors (in both lists): 1, 2, 3, 6.",
        "The <b>highest</b> of these is 6.",
        "So HCF(12, 18) = <b>6</b>.",
    ])))
    A(kiwi("Real-life use: HCF answers “what's the biggest equal group I can make from both piles?” "
           "If you have 12 red and 18 blue beads, you can make at most 6 identical little kits "
           "(each with 2 red and 3 blue)."))
    A(tryit("Find the HCF of <b>16 and 24</b>.",
            "Factors of 16: 1, 2, 4, 8, 16. Factors of 24: 1, 2, 3, 4, 6, 8, 12, 24. "
            "Common: 1, 2, 4, 8. Highest = <b>8</b>."))

    # ── LCM ──────────────────────────────────────────────────────
    A(H("LCM — the first multiple two numbers share"))
    A(P("The flip side is the <b>Lowest Common Multiple</b> (LCM): the <em>smallest</em> number that is a "
        "multiple of <em>both</em> numbers. To find it, list the multiples of each and grab the first one "
        "that appears in both lists."))
    A(example("LCM of 4 and 6", steps([
        "Multiples of 4: 4, 8, <b>12</b>, 16, 20, 24, …",
        "Multiples of 6: 6, <b>12</b>, 18, 24, …",
        "The first number in <em>both</em> lists is 12.",
        "So LCM(4, 6) = <b>12</b>.",
    ])))
    A(kiwi("Memory helper: <b>H</b>CF is <b>H</b>igh-but-small (it fits <em>inside</em> both numbers), "
           "and <b>L</b>CM is <b>L</b>ow-but-big (both numbers fit <em>inside</em> it). HCF ≤ each "
           "number ≤ LCM."))
    A(P("Real-life LCM: two lighthouses flash, one every 4 seconds and one every 6 seconds. They flash "
        "<em>together</em> every 12 seconds — that's the LCM!"))
    A(tryit("Find the LCM of <b>3 and 5</b>.",
            "Multiples of 3: 3, 6, 9, 12, <b>15</b>… Multiples of 5: 5, 10, <b>15</b>… First shared "
            "= <b>15</b>."))
    A(tryit("Find the LCM of <b>6 and 8</b>.",
            "Multiples of 6: 6, 12, 18, <b>24</b>… Multiples of 8: 8, 16, <b>24</b>… First shared "
            "= <b>24</b>."))

    # ── PRACTICE LADDER ──────────────────────────────────────────
    A(H("Climb the ladder — practice!"))
    A(P("Work from the bottom rung upward. Try each before peeking."))

    A(practice("Remember", [
        ("Is 1 a factor of 50?", "Yes — 1 is a factor of every number."),
        ("Write the first four multiples of 5.", "5, 10, 15, 20."),
        ("How many factors does a <b>prime</b> number have?", "Exactly two: 1 and itself."),
        ("Is 2 prime or composite?", "Prime (its only factors are 1 and 2). It's the only even prime."),
        ("What does HCF stand for?", "Highest Common Factor."),
    ]))
    A(practice("Understand", [
        ("List all the factors of 20.", "1, 2, 4, 5, 10, 20."),
        ("Is 30 a multiple of 6? Is it a multiple of 7?",
         "6 × 5 = 30, so yes for 6. 30 ÷ 7 = 4 r 2, so <b>not</b> a multiple of 7."),
        ("Sort these into prime or composite: 13, 14, 15, 16.",
         "13 = prime. 14 = 2×7 composite. 15 = 3×5 composite. 16 = 2×8 composite."),
        ("Write the prime factorization of 12.",
         "12 = 2 × 6 = 2 × 2 × 3. So <b>2 × 2 × 3</b>."),
    ]))
    A(practice("Apply", [
        ("Find all factor pairs of 36.",
         "1×36, 2×18, 3×12, 4×9, 6×6. (Factors: 1, 2, 3, 4, 6, 9, 12, 18, 36.)"),
        ("Make a factor tree for 30 and give its prime factorization.",
         "30 = 2 × 15, and 15 = 3 × 5. So 30 = <b>2 × 3 × 5</b>."),
        ("Find the HCF of 18 and 24.",
         "Factors of 18: 1,2,3,6,9,18. Of 24: 1,2,3,4,6,8,12,24. Common: 1,2,3,6 → HCF = <b>6</b>."),
        ("Find the LCM of 4 and 10.",
         "Multiples of 4: 4,8,12,16,<b>20</b>… of 10: 10,<b>20</b>… → LCM = <b>20</b>."),
        ("Two bells ring every 5 minutes and every 8 minutes. After how many minutes do they ring "
         "together?",
         "LCM of 5 and 8: multiples of 5 …,40; of 8 …,40 → <b>40 minutes</b>."),
    ]))
    A(practice("Analyze", [
        ("Which number below 20 has the <em>most</em> factors?",
         "Count them: 12 has 6 factors (1,2,3,4,6,12), 18 has 6 (1,2,3,6,9,18), 16 has 5. "
         "So <b>12 and 18 tie</b> with 6 factors each."),
        ("A number's only factors are 1, 3, 9 and 27. What is the number, and is it prime?",
         "1 × 27 = 27 and 3 × 9 = 27, so the number is <b>27</b>. It has more than two factors, so it is "
         "<b>composite</b>, not prime."),
        ("Is it possible for two different numbers to have an HCF of 1? Give an example.",
         "Yes! 8 and 9 share only the factor 1, so HCF = 1. Such numbers are called <em>co-prime</em>."),
        ("The LCM of two numbers is 12 and one of them is 4. Could the other be 6? Could it be 5?",
         "If the other is 6: LCM(4,6)=12 ✓. If it is 5: LCM(4,5)=20, not 12 ✗. So it could be 6, "
         "not 5."),
    ]))
    A(practice("Create", [
        ("Make up two numbers whose HCF is 5, and check it.",
         "Example: 10 and 15. Factors of 10: 1,2,5,10; of 15: 1,3,5,15. Common highest = 5 ✓."),
        ("Find a number between 20 and 30 that is prime, and explain how you checked.",
         "23 is prime — it isn't even, doesn't end in 5, and isn't divisible by 3 (2+3=5) or 7. "
         "(29 also works.)"),
        ("Build a factor tree of your own for 40 and write the prime factorization.",
         "40 = 4 × 10 = (2×2) × (2×5) → <b>2 × 2 × 2 × 5</b>. (Check: 8 × 5 = 40 ✓)"),
    ]))

    A(challenge(
        P("Two ropes of light blink in a dark room. The red light blinks every <b>6</b> seconds and the "
          "green light every <b>9</b> seconds. They <em>just</em> blinked together. "
          "After how many seconds will they next blink at the same moment? And how many times will the "
          "red light have blinked by then?") +
        tryit("This is an LCM problem — find when both cycles meet.",
              "Multiples of 6: 6, 12, <b>18</b>, … Multiples of 9: 9, <b>18</b>, … First shared = "
              "<b>18 seconds</b>. The red light blinks every 6 seconds, so by 18 seconds it has blinked "
              "18 ÷ 6 = <b>3 times</b>.")))

    A(kiwi("Good work breaking numbers down into their factors. You now know factors, multiples, primes, factor trees, HCF and LCM. These are the "
           "DNA of numbers! In the next chapter we'll learn lightning-fast <b>divisibility tricks</b> so "
           "you can spot factors without doing any division at all. ⚡"))

    chapter("Part 1 · Big Numbers", 3, "Number Families — Factors, Multiples & Primes",
            "Number Theory · Number Families", "".join(b))
