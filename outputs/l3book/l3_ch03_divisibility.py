#!/usr/bin/env python3
"""L3 Chapter 3 — Divisibility, Factors & Primes (Number Theory · Prime Hunters).
Builds from Level-2 multiplication facts: divisibility shortcuts (2,3,4,5,6,8,9,
10,11), factors & multiples, prime vs composite, prime factorization with factor
trees, HCF and LCM via shared prime factors / Venn, ending with the wonderful
surprise HCF x LCM = product of the two numbers."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, factor_tree, array_dots, venn2, svg,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


def divis_card(rules):
    """rules = list of (n, rule_html). A neat reference card of divisibility rules."""
    rowh = 34; W = 560; H = 28 + rowh * len(rules) + 10
    s = [f'<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="12" fill="#FFFDF8" stroke="{GOLD}" stroke-width="2"/>',
         f'<text x="{W/2:.0f}" y="26" font-size="14" text-anchor="middle" font-weight="800" fill="{ORANGE}">Divisibility quick-rules</text>']
    y = 40
    for n, rule in rules:
        s.append(f'<circle cx="34" cy="{y+9}" r="15" fill="{SKY}22" stroke="{SKY}" stroke-width="1.8"/>')
        s.append(f'<text x="34" y="{y+14}" font-size="14" text-anchor="middle" font-weight="800" fill="{SKY}">{n}</text>')
        s.append(f'<text x="60" y="{y+14}" font-size="13" fill="{INK}">{rule}</text>')
        y += rowh
    return svg("".join(s), W, H)


def multiples_strip(n, upto=12, hits=None):
    """A 1..upto strip with multiples of n circled."""
    hits = hits or [k for k in range(1, upto + 1) if k % n == 0]
    c = 38; W = upto * c + 16; s = []
    for k in range(1, upto + 1):
        x = 8 + (k - 1) * c
        on = k in hits
        s.append(f'<rect x="{x}" y="14" width="{c-6}" height="{c-6}" rx="7" '
                 f'fill="{GRASS+"22" if on else "#fff"}" stroke="{GRASS if on else "#cfc9bf"}" stroke-width="{2 if on else 1.3}"/>')
        s.append(f'<text x="{x+(c-6)/2:.0f}" y="{14+(c-6)/2+5:.0f}" font-size="13" text-anchor="middle" '
                 f'font-weight="{800 if on else 600}" fill="{GRASS if on else INK}">{k}</text>')
    return svg("".join(s), W, 56)


def prime_grid(upto=30):
    """Sieve-of-Eratosthenes style grid 1..upto: primes green, composites pink, 1 grey."""
    cols = 10; c = 34
    rows = (upto + cols - 1) // cols
    def is_p(x):
        if x < 2: return False
        for d in range(2, int(x ** 0.5) + 1):
            if x % d == 0: return False
        return True
    s = []
    for x in range(1, upto + 1):
        r, cc = divmod(x - 1, cols)
        px, py = 8 + cc * c, 8 + r * c
        if x == 1:
            fill, stroke, tc = "#EFEced", "#bdb7ad", "#8c8377"
        elif is_p(x):
            fill, stroke, tc = GRASS + "33", GRASS, GRASS
        else:
            fill, stroke, tc = BERRY + "22", BERRY, BERRY
        s.append(f'<rect x="{px}" y="{py}" width="{c-5}" height="{c-5}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        s.append(f'<text x="{px+(c-5)/2:.0f}" y="{py+(c-5)/2+5:.0f}" font-size="13" text-anchor="middle" font-weight="800" fill="{tc}">{x}</text>')
    return svg("".join(s), 8 + cols * c, 8 + rows * c + 4)


def build(chapter):
    b = []; A = b.append

    A(big_q("Is <b>91</b> a prime number? It looks like one &#8212; it's odd, it doesn't end in 0 or 5, and "
            "nothing obvious divides it. Most people guess &#8220;prime.&#8221; They're wrong, and by the end of this "
            "chapter you'll spot exactly why in about three seconds. You'll also meet a jaw-dropping rule: "
            "<b>HCF &#215; LCM = the product of the two numbers</b>, every single time."))
    A(kiwi("Hello again, number detective! &#128269; Every whole number is secretly built out of smaller "
           "pieces, the way a wall is built from bricks. Today we learn to <b>x-ray</b> a number: find what "
           "divides it, which numbers are the unbreakable &#8216;atoms&#8217; (primes), and how to compare two numbers' "
           "insides to find what they share. We start from something you already own &#8212; multiplication."))

    # ── factors & multiples ─────────────────────────────
    A(H("Factors and multiples: two sides of one coin"))
    A(P("12 = 3 &#215; 4. We say 3 and 4 are <b>factors</b> of 12 (they divide it with no remainder), and "
        "12 is a <b>multiple</b> of 3 and of 4. A <b>factor</b> fits <em>inside</em> a number exactly; a "
        "<b>multiple</b> is what you get by <em>skip-counting</em> the number. Picture 12 as a perfect "
        "rectangle &#8212; every way to make a full rectangle gives a factor pair:"))
    A(figure(array_dots(3, 4), "3 rows of 4 = 12. So 3 and 4 are a factor pair of 12."))
    A(P("To list <b>all</b> factors of a number, hunt in pairs from the outside in. For 12: 1&#215;12, "
        "2&#215;6, 3&#215;4 &#8212; then 4 already appeared, so stop. Factors of 12: <b>1, 2, 3, 4, 6, 12</b>. "
        "Every number has 1 and itself as factors; the interesting ones live in between."))
    A(figure(multiples_strip(3, 12), "Multiples of 3 up to 12: 3, 6, 9, 12 &#8212; the skip-counting steps."))
    A(example("find all factors of 36", steps([
        "Hunt in pairs: 1&#215;36, 2&#215;18, 3&#215;12, 4&#215;9, 6&#215;6.",
        "After 6&#215;6 the pairs start repeating, so stop.",
        "Factors of 36: <b>1, 2, 3, 4, 6, 9, 12, 18, 36</b> &#8212; nine of them.",
        "Notice 6&#215;6: when a number is a perfect square its middle factor pairs into itself.",
    ])))
    A(tryit("List all factors of 24.",
            "1&#215;24, 2&#215;12, 3&#215;8, 4&#215;6 &#8594; <b>1, 2, 3, 4, 6, 8, 12, 24</b> (eight factors)."))

    # ── divisibility rules ──────────────────────────────
    A(H("Divisibility magic: knowing WITHOUT dividing"))
    A(P("Long division is slow. There are lightning shortcuts that tell you if a number is divisible by "
        "2, 3, 4, 5, 6, 8, 9, 10 or 11 &#8212; just by glancing at its digits. Here's your reference card; "
        "we'll prove the two coolest ones below."))
    A(figure(divis_card([
        (2, "Last digit is even (0,2,4,6,8)."),
        (5, "Last digit is 0 or 5."),
        (10, "Last digit is 0."),
        (4, "Last TWO digits form a multiple of 4."),
        (8, "Last THREE digits form a multiple of 8."),
        (3, "Digit-sum is a multiple of 3."),
        (9, "Digit-sum is a multiple of 9."),
        (6, "Divisible by 2 AND by 3."),
        (11, "Alternating digit-sum (+ &#8722; + &#8722;) is 0 or a multiple of 11."),
    ]), "Divisibility rules at a glance: tests for 2, 3, 4, 5, 6, 8, 9, 10 and 11."))
    A(kiwi("The 3-and-9 rule feels like magic: <em>why</em> should adding the digits tell you anything? "
           "Because 10 = 9 + 1, 100 = 99 + 1, 1000 = 999 + 1 &#8230; and 9, 99, 999 are all multiples of 9. "
           "So a number is &#8216;a pile of 9s&#8217; plus its digit-sum. The pile of 9s is already divisible by 9 (and "
           "by 3), so the leftover &#8212; the digit-sum &#8212; decides it. Beautiful, not magic!"))
    A(example("is 9,724 divisible by 6? (the source-PDF puzzle)", steps([
        "By 6 means by 2 AND by 3.",
        "By 2: last digit 4 is even &#8212; yes. &#10003;",
        "By 3: digit-sum 9+7+2+4 = 22, and 22 is not a multiple of 3 &#8212; no. &#10007;",
        "Since it fails the 3-test, 9,724 is <b>not</b> divisible by 6.",
        "Bonus: to make 9724* divisible by 6, the * must be even AND make the digit-sum a multiple of 3. "
        "Digit-sum so far is 22; +2 gives 24 (a multiple of 3) and 2 is even &#8594; <b>*</b> = 2 works.",
    ])))
    A(example("test 3,4,5,9 on 4,950", steps([
        "By 5: ends in 0 &#8212; yes. By 10: ends in 0 &#8212; yes too.",
        "By 9: digit-sum 4+9+5+0 = 18, a multiple of 9 &#8212; yes (so by 3 as well).",
        "By 4: last two digits 50, and 50 is not a multiple of 4 &#8212; no.",
        "So 4,950 is divisible by 3, 5, 9, 10 but not by 4.",
    ])))
    A(tryit("Is 8,261,955 divisible by 11? (Use the alternating-sum rule, right to left.)",
            "Alternating sum: 5&#8722;5+9&#8722;1+6&#8722;2+8 = 20. 20 is not 0 or a multiple of 11, so <b>no</b>. "
            "(Adding 2 would make it 22 &#8212; a multiple of 11 &#8212; which is why the smallest number to add is 2.)"))

    # ── primes & composites ─────────────────────────────
    A(H("Primes: the unbreakable atoms of arithmetic"))
    A(P("A number with <b>exactly two</b> factors &#8212; 1 and itself &#8212; is <b>prime</b>: 2, 3, 5, 7, 11, 13 &#8230; "
        "A number with <b>more</b> than two factors is <b>composite</b>: 4, 6, 8, 9, 10 &#8230; The number "
        "<b>1 is special</b> &#8212; it has only one factor (itself), so it's <em>neither</em> prime nor composite. "
        "And 2 is the only <em>even</em> prime &#8212; every other even number has 2 as an extra factor."))
    A(figure(prime_grid(30), "Numbers 1&#8211;30: primes (green) are the atoms; composites (pink) are built from them; 1 (grey) stands alone."))
    A(P("Here's the detective trick that cracks our opening puzzle. To test if a number is prime, you only "
        "need to try dividing by primes up to its <b>square root</b> &#8212; because if it had a factor bigger "
        "than its square root, the matching partner would be smaller, and you'd have caught that already."))
    A(example("is 91 prime? (the trap from page 1)", steps([
        "&#8730;91 is a bit less than 10 (since 10&#215;10 = 100), so test primes up to 9: 2, 3, 5, 7.",
        "Not even (so not 2); digit-sum 10 (so not 3); doesn't end in 0/5 (so not 5).",
        "Try 7: 7 &#215; 13 = 91. Found a factor!",
        "So <b>91 = 7 &#215; 13</b> is composite, not prime. The trap is that 91 has no <em>small</em> factor, "
        "so it &#8216;feels&#8217; prime &#8212; but 7 &#215; 13 was hiding in plain sight.",
    ])))
    A(tryit("Is 97 prime? Test primes up to 9.",
            "2,3,5,7 all fail to divide 97 (97 is odd, digit-sum 16, doesn't end in 0/5, and 97/7 isn't whole). "
            "So <b>97 is prime</b>."))

    # ── prime factorization ─────────────────────────────
    A(H("Prime factorization: every number's secret recipe"))
    A(P("The grand theorem of arithmetic: <b>every whole number above 1 is a product of primes in exactly "
        "one way</b> (apart from the order). That unique recipe is its <b>prime factorization</b>. We find it "
        "with a <b>factor tree</b> &#8212; keep splitting until every leaf is prime."))
    A(figure(factor_tree(60, 6, 10, a2=2, b2=3, c2=2, d2=5),
             "60 &#8594; 6 &#215; 10 &#8594; (2&#215;3) &#215; (2&#215;5). Leaves: 2, 3, 2, 5."))
    A(P("Collect the leaves: 60 = 2 &#215; 2 &#215; 3 &#215; 5 = <b>2&#178; &#215; 3 &#215; 5</b>. "
        "Surprise check: it doesn't matter how you start the tree. Split 60 as 4 &#215; 15 instead and you "
        "still land on 2&#178; &#215; 3 &#215; 5. The recipe is destiny."))
    A(example("prime-factorize 72", steps([
        "72 = 8 &#215; 9.",
        "8 = 2 &#215; 2 &#215; 2, and 9 = 3 &#215; 3.",
        "So 72 = 2 &#215; 2 &#215; 2 &#215; 3 &#215; 3 = <b>2&#179; &#215; 3&#178;</b>.",
        "Quick brick-count: that's three 2-bricks and two 3-bricks &#8212; the complete blueprint of 72.",
    ])))
    A(tryit("Write the prime factorization of 84.",
            "84 = 4 &#215; 21 = (2&#215;2) &#215; (3&#215;7) = <b>2&#178; &#215; 3 &#215; 7</b>."))

    # ── HCF & LCM ────────────────────────────────────────
    A(H("HCF and LCM: comparing two numbers' insides"))
    A(P("Lay two numbers' prime recipes side by side and two famous numbers appear:"))
    A(steps([
        "<b>HCF</b> (Highest Common Factor, also called GCD) = the primes they <em>share</em> &#8212; the biggest "
        "number that divides both.",
        "<b>LCM</b> (Lowest Common Multiple) = the smallest number that <em>both</em> divide into &#8212; you take "
        "every prime to its highest power seen.",
    ]))
    A(P("Take 12 = 2&#178; &#215; 3 and 18 = 2 &#215; 3&#178;. A Venn diagram makes the sharing visible &#8212; "
        "shared prime-bricks go in the middle, leftovers go outside:"))
    A(figure(venn2(2, "2&#215;3", 3, "12 = 2&#178;&#215;3", "18 = 2&#215;3&#178;"),
             "Middle (shared) = 2&#215;3 = 6 = HCF. Whole picture = 2&#215;3 &#215; 2 &#215; 3 = 36 = LCM."))
    A(example("find HCF and LCM of 12 and 18", steps([
        "12 = 2 &#215; 2 &#215; 3.   18 = 2 &#215; 3 &#215; 3.",
        "Shared bricks (take the <em>lower</em> power of each common prime): one 2 and one 3 &#8594; HCF = 2 &#215; 3 = <b>6</b>.",
        "For LCM take the <em>higher</em> power of every prime that appears: 2&#178; &#215; 3&#178; = 4 &#215; 9 = <b>36</b>.",
        "Sense-check: 6 divides both 12 and 18 (yes), and 36 is the first number both 12 and 18 march into.",
    ])))
    A(kiwi("Memory hook: <b>H</b>CF is <b>H</b>idden inside &#8212; the part both share. <b>L</b>CM is <b>L</b>arge "
           "enough to hold both. HCF &#8804; either number &#8804; LCM, always."))
    A(tryit("Find the HCF and LCM of 8 and 12.",
            "8 = 2&#179;, 12 = 2&#178;&#215;3. HCF = 2&#178; = <b>4</b>; LCM = 2&#179;&#215;3 = <b>24</b>."))
    A(example("four bells ring every 6, 8 and 9 seconds &#8212; when do all ring together?", steps([
        "&#8220;Together again&#8221; = the LCM of 6, 8, 9.",
        "6 = 2&#215;3, 8 = 2&#179;, 9 = 3&#178;.",
        "Highest power of each prime: 2&#179; &#215; 3&#178; = 8 &#215; 9 = <b>72</b>.",
        "So all three ring together every <b>72 seconds</b> &#8212; LCM is the &#8216;everyone-meets&#8217; number.",
    ])))

    # ── THE SURPRISE: HCF x LCM = product ────────────────
    A(H("&#10024; The surprise: HCF &#215; LCM = the product of the numbers"))
    A(P("Look back at 12 and 18. HCF = 6, LCM = 36. Now multiply them: 6 &#215; 36 = <b>216</b>. "
        "And 12 &#215; 18 = <b>216</b>. The same number! This is no accident:"))
    A(figure(svg(
        '<text x="180" y="30" font-size="17" text-anchor="middle" font-weight="800" fill="#2b2622">HCF &#215; LCM = a &#215; b</text>'
        '<text x="100" y="74" font-size="16" text-anchor="middle" fill="#39A85B" font-weight="800">6 &#215; 36</text>'
        '<text x="180" y="74" font-size="18" text-anchor="middle" fill="#8c8377">=</text>'
        '<text x="262" y="74" font-size="16" text-anchor="middle" fill="#FF6F00" font-weight="800">12 &#215; 18</text>'
        '<text x="100" y="100" font-size="15" text-anchor="middle" fill="#8c8377">= 216</text>'
        '<text x="262" y="100" font-size="15" text-anchor="middle" fill="#8c8377">= 216</text>',
        360, 120), "HCF &#215; LCM always equals the product of the two numbers."))
    A(P("Why must it be true? In the Venn picture, the HCF is the <em>shared</em> bricks and the LCM is "
        "<em>all</em> the bricks. When you multiply HCF &#215; LCM you use the shared bricks <b>twice</b> and "
        "the leftover bricks once &#8212; which is exactly the bricks of the first number times the bricks of the "
        "second. So HCF &#215; LCM = a &#215; b. It can never fail."))
    A(kiwi("This gives a super shortcut: if you know the HCF, you get the LCM for free &#8212; "
           "<b>LCM = (a &#215; b) &#247; HCF</b>. No need to build the LCM brick by brick!"))
    A(example("the LCM of two numbers is 30 and their HCF is 15; one number is 30 &#8212; find the other (source-PDF Q7)", steps([
        "Use HCF &#215; LCM = a &#215; b &#8594; 15 &#215; 30 = 30 &#215; b.",
        "So 450 = 30 &#215; b.",
        "b = 450 &#247; 30 = <b>15</b>.",
        "Check: HCF(30, 15) = 15 &#10003; and LCM(30, 15) = 30 &#10003;. The shortcut nailed it.",
    ])))
    A(tryit("Two numbers multiply to 96 and their HCF is 4. What is their LCM?",
            "LCM = product &#247; HCF = 96 &#247; 4 = <b>24</b>."))

    # ── BLOOM LADDER ─────────────────────────────────────
    A(H("Climb the prime-hunter ladder"))
    A(practice("Remember", [
        ("List the first five prime numbers.", "2, 3, 5, 7, 11."),
        ("Is 1 prime, composite, or neither?", "Neither &#8212; it has only one factor, itself."),
        ("What is the only even prime number?", "2."),
        ("State the divisibility rule for 5.", "The last digit must be 0 or 5."),
        ("How many factors does a prime number have?", "Exactly two: 1 and itself."),
    ]))
    A(practice("Understand", [
        ("Is 372 divisible by 3? Show the digit-sum.", "3+7+2 = 12, a multiple of 3 &#8594; yes."),
        ("Write the prime factorization of 90.", "90 = 2 &#215; 3&#178; &#215; 5."),
        ("Is 51 prime? Explain.", "No: 51 = 3 &#215; 17 (digit-sum 6 is a multiple of 3)."),
        ("Find all factors of 18.", "1, 2, 3, 6, 9, 18."),
        ("Is 7,225 divisible by 5? By 25?", "By 5: ends in 5 &#8594; yes. By 25: last two digits 25 &#8594; yes."),
    ]))
    A(practice("Apply", [
        ("Find the HCF of 24 and 36.", "24 = 2&#179;&#215;3, 36 = 2&#178;&#215;3&#178;. Shared: 2&#178;&#215;3 = 12."),
        ("Find the LCM of 4, 8 and 16.", "Highest power is 2&#8308; = 16. (16 is itself a multiple of 4 and 8.)"),
        ("What least digit at * makes 37*124 divisible by 9?", "Digit-sum 3+7+1+2+4 = 17; need a multiple of 9, "
         "so 17 + * = 18 &#8594; <b>* = 1</b>."),
        ("Three lighthouses flash every 12, 18 and 30 minutes. When do all flash together?",
         "LCM: 12=2&#178;&#215;3, 18=2&#215;3&#178;, 30=2&#215;3&#215;5 &#8594; 2&#178;&#215;3&#178;&#215;5 = 180 minutes (3 hours)."),
        ("HCF of two numbers is 6 and their product is 720. Find the LCM.", "LCM = 720 &#247; 6 = 120."),
    ]))
    A(practice("Analyze", [
        ("The HCF of two co-prime numbers is 1 and their LCM is 117. What could the numbers be?",
         "Co-prime means HCF = 1, so LCM = product = 117 = 9 &#215; 13. The numbers are 9 and 13 (their squares sum to 81+169 = 250)."),
        ("What is the greatest number that divides 37, 50 and 123 leaving remainders 1, 2 and 3?",
         "Subtract the remainders: 36, 48, 120. Take their HCF: 36=2&#178;&#215;3&#178;, 48=2&#8308;&#215;3, 120=2&#179;&#215;3&#215;5 &#8594; shared 2&#178;&#215;3 = 12."),
        ("A number is divisible by both 8 and 11. What is the smallest 3-digit such number?",
         "8 and 11 are co-prime, so it must be a multiple of 88. The smallest 3-digit multiple is 88 itself? "
         "88 is 2-digit; next is 176. So <b>176</b>."),
        ("If a number is divisible by 72, which single-digit numbers must also divide it?",
         "72 = 2&#179;&#215;3&#178;, so 2, 3, 4, 6, 8, 9 all divide it (each is built from those primes)."),
    ]))
    A(practice("Create", [
        ("Invent a number between 100 and 200 that is divisible by 3, 4 and 5 at once. What did you build?",
         "It must be a multiple of LCM(3,4,5) = 60. So 120 or 180."),
        ("Make a 4-digit number divisible by 11 and explain how you forced it.",
         "Choose digits so the alternating sum is 0, e.g. 3,4,3,4 &#8594; 3454? (4&#8722;5+4&#8722;3... ) Easiest: 1,2,1,2 &#8594; 2121 (1&#8722;2+1&#8722;2 = &#8722;2)? "
         "Cleanest is 1,1,0,0 &#8594; 1001 = 7&#215;11&#215;13 &#8212; alternating sum 1&#8722;0+0&#8722;1 = 0. &#10003;"),
        ("Design a &#8216;bell puzzle&#8217; of your own where three bells next ring together after exactly 60 seconds.",
         "Pick three numbers whose LCM is 60, e.g. 4, 6, 15 (LCM = 60) or 5, 12, 20 (LCM = 60)."),
    ]))

    # ── CHALLENGE ────────────────────────────────────────
    A(challenge(
        P("<b>The Locker Mystery.</b> 100 lockers stand in a row, all shut, numbered 1 to 100. Student 1 "
          "walks past and <em>flips</em> every locker (opens them all). Student 2 flips every 2nd locker "
          "(2, 4, 6&#8230;). Student 3 flips every 3rd locker (3, 6, 9&#8230;), and so on up to student 100. "
          "A locker ends up <b>open</b> only if it was flipped an <em>odd</em> number of times. Which lockers are "
          "left open &#8212; and what makes them special?") +
        tryit("Hint: locker n is flipped once by every student whose number is a FACTOR of n.",
              "Locker n is flipped once per factor of n. Factors normally come in pairs (like 12: 1&#215;12, "
              "2&#215;6, 3&#215;4) &#8212; an <em>even</em> count &#8212; so most lockers close. The only numbers with an "
              "<b>odd</b> number of factors are the <b>perfect squares</b>, because their middle factor pairs with "
              "<em>itself</em> (e.g. 36 = 6&#215;6, so 6 is counted once). So the open lockers are "
              "<b>1, 4, 9, 16, 25, 36, 49, 64, 81, 100</b> &#8212; the perfect squares! You just used factor-pairing "
              "to crack a 100-locker puzzle. &#127881;")))

    A(kiwi("Magnificent detective work! You can now x-ray any number into primes, judge divisibility at a "
           "glance, and find HCF and LCM &#8212; plus you proved HCF &#215; LCM = the product. Next we discover a "
           "shorthand that lets us write 2 &#215; 2 &#215; 2 &#215; &#8230; without writer's cramp, and watch numbers "
           "grow at terrifying speed: <b>powers and exponents</b>. &#9889;"))

    chapter("Part 1 · Number Sense & Integers", 3, "Divisibility, Factors & Primes",
            "Number Theory · Prime Hunters", "".join(b))
