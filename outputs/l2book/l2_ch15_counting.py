#!/usr/bin/env python3
"""Chapter 15 — Counting & Combinations  (Combinatorics · Brain Benders)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, array_dots, pattern_seq, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# ── a little local figure: a simple "choice tree" ───────────────────────────
def choice_tree(trunk, branches, leaves):
    """trunk = root label; branches = list of (label,color); leaves = list of
    lists, one per branch, each a list of (label,color). Draws a left-to-right tree."""
    rowh = 44
    total_leaves = sum(len(lv) for lv in leaves)
    H_ = max(total_leaves * rowh + 20, 120)
    x_root, x_b, x_l = 24, 150, 300
    cy_root = H_ / 2
    s = [f'<circle cx="{x_root}" cy="{cy_root:.0f}" r="16" fill="{INK}" />',
         f'<text x="{x_root}" y="{cy_root+5:.0f}" text-anchor="middle" font-size="13" '
         f'font-weight="800" fill="#fff">{trunk}</text>']
    # walk leaves top-to-bottom, grouping by branch
    leaf_ys = []
    y = 30
    for lv in leaves:
        ys = []
        for _ in lv:
            ys.append(y)
            y += rowh
        leaf_ys.append(ys)
    for bi, (blab, bcol) in enumerate(branches):
        ys = leaf_ys[bi]
        cyb = sum(ys) / len(ys)
        s.append(f'<line x1="{x_root+16}" y1="{cy_root:.0f}" x2="{x_b-18}" y2="{cyb:.0f}" '
                 f'stroke="{bcol}" stroke-width="2.2"/>')
        s.append(f'<rect x="{x_b-18}" y="{cyb-15:.0f}" width="36" height="30" rx="8" '
                 f'fill="{bcol}22" stroke="{bcol}" stroke-width="2"/>')
        s.append(f'<text x="{x_b}" y="{cyb+5:.0f}" text-anchor="middle" font-size="13" '
                 f'font-weight="800" fill="{bcol}">{blab}</text>')
        for li, (llab, lcol) in enumerate(leaves[bi]):
            ly = ys[li]
            s.append(f'<line x1="{x_b+18}" y1="{cyb:.0f}" x2="{x_l-6}" y2="{ly:.0f}" '
                     f'stroke="{lcol}" stroke-width="1.8"/>')
            s.append(f'<rect x="{x_l-6}" y="{ly-14:.0f}" width="120" height="28" rx="8" '
                     f'fill="{lcol}18" stroke="{lcol}" stroke-width="1.6"/>')
            s.append(f'<text x="{x_l+54}" y="{ly+5:.0f}" text-anchor="middle" font-size="12.5" '
                     f'font-weight="700" fill="{INK}">{llab}</text>')
    return svg("".join(s), 430, H_)


def two_digit_grid(tens, ones, made):
    """Tens digits down the side, ones across the top; fill cells with the 2-digit
    number formed. `made` = set of (t,o) that are allowed (for no-repeat)."""
    c = 52
    W = 40 + len(ones) * c + 20
    Hh = 40 + len(tens) * c + 20
    s = [f'<text x="{40+len(ones)*c/2:.0f}" y="16" text-anchor="middle" font-size="12.5" '
         f'font-weight="800" fill="{SKY}">ONES digit →</text>']
    for j, o in enumerate(ones):
        s.append(f'<text x="{40+j*c+c/2:.0f}" y="38" text-anchor="middle" font-size="16" '
                 f'font-weight="800" fill="{SKY}">{o}</text>')
    s.append(f'<text x="14" y="{40+len(tens)*c/2:.0f}" text-anchor="middle" font-size="12.5" '
             f'font-weight="800" fill="{BERRY}" transform="rotate(-90 14 {40+len(tens)*c/2:.0f})">'
             f'TENS digit ↓</text>')
    for i, t in enumerate(tens):
        s.append(f'<text x="34" y="{40+i*c+c/2+6:.0f}" text-anchor="middle" font-size="16" '
                 f'font-weight="800" fill="{BERRY}">{t}</text>')
        for j, o in enumerate(ones):
            x = 40 + j * c
            yv = 40 + i * c
            ok = (t, o) in made
            fill = f"{GRASS}22" if ok else "#f0eee9"
            stroke = GRASS if ok else "#cfc9bf"
            s.append(f'<rect x="{x}" y="{yv}" width="{c}" height="{c}" rx="6" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="1.8"/>')
            if ok:
                s.append(f'<text x="{x+c/2:.0f}" y="{yv+c/2+6:.0f}" text-anchor="middle" '
                         f'font-size="16" font-weight="800" fill="{INK}">{t*10+o}</text>')
            else:
                s.append(f'<text x="{x+c/2:.0f}" y="{yv+c/2+7:.0f}" text-anchor="middle" '
                         f'font-size="20" fill="#cfc9bf">✗</text>')
    return svg("".join(s), W, Hh)


def build(chapter):
    b = []
    A = b.append

    A(big_q("You have <b>3 T-shirts</b> and <b>2 pairs of shorts</b>. How many different "
            "outfits can you make? Could you list <em>every single one</em> without missing any "
            "— or accidentally counting one twice?"))
    A(kiwi("Hi again, it's <b>Kiwi</b>! Counting sounds like the easiest thing in maths — 1, 2, 3… "
           "But counting <em>without seeing the things</em> is a real superpower. The trick is to be "
           "<b>organised</b>: make a neat list or table so nothing escapes. Let's learn the secret."))

    # ── outfits / counting principle ────────────────────────────────────────
    A(H("Outfits: the counting trick"))
    A(P("Say your shirts are <b>Red</b>, <b>Blue</b> and <b>Green</b>, and your shorts are "
        "<b>White</b> and <b>Black</b>. Let's draw a <b>choice tree</b>. First we pick a shirt "
        "(3 ways). Then, from <em>each</em> shirt, we branch out to pick shorts (2 ways)."))
    A(figure(choice_tree("Start",
                         [("R", BERRY), ("B", SKY), ("G", GRASS)],
                         [[("Red + White", BERRY), ("Red + Black", BERRY)],
                          [("Blue + White", SKY), ("Blue + Black", SKY)],
                          [("Green + White", GRASS), ("Green + Black", GRASS)]]),
             "3 shirts, each splitting into 2 shorts → 6 leaves = 6 outfits"))
    A(P("Count the endings (we call them <b>leaves</b>): there are <b>6</b>. Notice we didn't "
        "have to draw to know this — there are <b>3</b> shirts, and each one gives <b>2</b> outfits, "
        "so 3 + 3 = 6… which is just <b>3 × 2</b>."))
    A(kiwi("Here is the golden rule, the <b>Counting Principle</b>: if you make one choice in "
           "<em>a</em> ways and then another choice in <em>b</em> ways, the number of ways to do "
           "<b>both</b> is <b>a × b</b>. Choices that follow one another get <b>multiplied</b>."))
    A(P("We can also lay the 6 outfits out as a neat <b>grid</b> — 3 rows for shirts, 2 columns "
        "for shorts. Each little dot is one outfit:"))
    A(figure(array_dots(3, 2), "3 rows × 2 columns = 6 dots = 6 outfits"))

    A(example("ice-cream cones", steps([
        "An ice-cream shop has <b>4 flavours</b> (vanilla, mango, choco, strawberry) and "
        "<b>3 toppings</b> (sprinkles, nuts, cherry). One scoop + one topping = one cone.",
        "First choice: pick a flavour → <b>4</b> ways.",
        "Second choice: pick a topping → <b>3</b> ways.",
        "By the Counting Principle, multiply: 4 × 3 = <b>12</b> different cones. 🍦",
    ])))

    A(tryit("A breakfast has <b>2 drinks</b> (milk or juice) and <b>5 fruits</b>. "
            "How many drink-and-fruit breakfasts are possible?",
            "Multiply the choices: 2 × 5 = <b>10</b> breakfasts."))

    # ── making two-digit numbers ────────────────────────────────────────────
    A(H("How many 2-digit numbers can we build?"))
    A(P("Here's a favourite olympiad question. Using the digits <b>2, 4, 7</b>, how many "
        "<b>2-digit numbers</b> can we make if a digit is <em>allowed to repeat</em> "
        "(so 22 and 44 are fine)?"))
    A(P("A 2-digit number has a <b>tens</b> place and a <b>ones</b> place. We choose a digit "
        "for each place:"))
    A(figure(two_digit_grid([2, 4, 7], [2, 4, 7],
                           {(t, o) for t in (2, 4, 7) for o in (2, 4, 7)}),
             "Tens digit: 3 choices · Ones digit: 3 choices → 3 × 3 = 9 numbers"))
    A(example("counting the 2-digit numbers (repeats allowed)", steps([
        "<b>Tens</b> place: we may use 2, 4 or 7 → <b>3</b> choices.",
        "<b>Ones</b> place: again any of 2, 4, 7 (repeats allowed) → <b>3</b> choices.",
        "Multiply: 3 × 3 = <b>9</b> numbers.",
        "Let's list them to be sure: 22, 24, 27, 42, 44, 47, 72, 74, 77. "
        "Count them — exactly <b>9</b>! ✓",
    ])))
    A(P("Now a twist: what if a digit <b>cannot</b> repeat (no number like 22)? Then once a "
        "digit is used in the tens place, the ones place has <em>one fewer</em> choice."))
    A(figure(two_digit_grid([2, 4, 7], [2, 4, 7],
                           {(t, o) for t in (2, 4, 7) for o in (2, 4, 7) if t != o}),
             "Repeats not allowed: the diagonal (22, 44, 77) is crossed out → 9 − 3 = 6"))
    A(example("counting with NO repeats", steps([
        "<b>Tens</b> place: any of 2, 4, 7 → <b>3</b> choices.",
        "<b>Ones</b> place: must be <em>different</em> from the tens digit → only <b>2</b> left.",
        "Multiply: 3 × 2 = <b>6</b> numbers.",
        "List to check: 24, 27, 42, 47, 72, 74. That's <b>6</b>. ✓",
    ])))
    A(kiwi("Spot the difference! <b>Repeats allowed</b> → 3 × 3 = 9. <b>No repeats</b> → 3 × 2 = 6. "
           "Always ask yourself: <em>“Can I use the same thing twice?”</em> It changes the answer."))

    A(tryit("Using the digits <b>1, 5, 8</b>, how many 2-digit numbers can you make if "
            "repeats <b>are</b> allowed?",
            "Tens: 3 choices, Ones: 3 choices → 3 × 3 = <b>9</b> numbers "
            "(11, 15, 18, 51, 55, 58, 81, 85, 88)."))

    # ── systematic listing (pairs) ──────────────────────────────────────────
    A(H("Pairs that don't care about order: choosing 2 friends"))
    A(P("Sometimes order doesn't matter. From <b>4 friends</b> — <b>Asha, Bina, Cara, Dev</b> — "
        "we want to pick a <b>team of 2</b> to play. Asha-with-Bina is the <em>same team</em> as "
        "Bina-with-Asha, so we must <b>not</b> count it twice."))
    A(P("The safe way is to <b>list in order</b> and never go backwards. Start every pair with "
        "Asha, then every <em>new</em> pair with Bina, and so on:"))
    A(figure(pattern_seq([("AB", BERRY), ("AC", BERRY), ("AD", BERRY),
                         ("BC", SKY), ("BD", SKY), ("CD", GRASS)], q=False),
             "Listed alphabetically, never repeating — exactly 6 teams of 2"))
    A(example("counting the teams of 2", steps([
        "Pairs that start with <b>A</b>: AB, AC, AD → <b>3</b> teams.",
        "New pairs that start with <b>B</b> (B with someone later): BC, BD → <b>2</b> teams.",
        "New pair that starts with <b>C</b>: CD → <b>1</b> team.",
        "We stop at D (no one comes after D to pair with). Total: 3 + 2 + 1 = <b>6</b> teams.",
    ])))
    A(kiwi("This neat countdown <b>3 + 2 + 1</b> is the secret to picking 2 from a group when "
           "order doesn't matter. It makes sure you never miss a pair or count one twice."))

    A(tryit("A pizza shop lets you choose <b>2 different toppings</b> from "
            "<b>mushroom, olives, corn</b>. How many topping-pairs are there?",
            "List them: mushroom-olives, mushroom-corn, olives-corn → 2 + 1 = <b>3</b> pairs."))

    # ── handshakes (a classic) ──────────────────────────────────────────────
    A(H("The handshake puzzle"))
    A(P("At a small party, <b>4 children</b> each shake hands with <b>every other</b> child "
        "exactly once. How many handshakes happen altogether?"))
    A(P("A handshake is just a <b>pair</b> of children — and Asha shaking Bina is the same "
        "handshake as Bina shaking Asha! So this is the <em>same</em> as picking teams of 2: "
        "3 + 2 + 1 = <b>6</b> handshakes."))
    A(challenge(
        P("Picture 5 children at the party instead. <b>How many handshakes</b> now? "
          "(Hint: use the countdown trick.)") +
        tryit("Count down from 4.",
              "The first child shakes 4 others, the next adds 3 new, then 2, then 1: "
              "4 + 3 + 2 + 1 = <b>10</b> handshakes.")))

    # ── Bloom ladder ────────────────────────────────────────────────────────
    A(H("Now you try — climb the ladder"))
    A(P("Be <b>organised</b>: draw a tree, a grid, or list in order. Peek only after a real try!"))

    A(practice("Remember", [
        ("If you choose one thing in 4 ways and then another in 5 ways, you find the total "
         "number of ways by adding or multiplying?",
         "Multiplying: 4 × 5 = 20."),
        ("A coin has how many sides it can land on?", "2 (Heads or Tails)."),
        ("To pick a <b>pair</b> of 2 friends, does the <em>order</em> matter — is "
         "“Sam &amp; Pat” different from “Pat &amp; Sam”?",
         "No — it's the same pair, so order does not matter."),
        ("Using digits 3 and 8 (repeats allowed), name all the 2-digit numbers.",
         "33, 38, 83, 88 — that's 4 numbers (2 × 2)."),
    ]))
    A(practice("Understand", [
        ("A sandwich shop has 3 breads and 4 fillings. How many different sandwiches "
         "(1 bread + 1 filling)?",
         "Multiply: 3 × 4 = 12 sandwiches."),
        ("Using digits 1, 2, 3, 4, how many 2-digit numbers can be made if repeats are "
         "allowed?",
         "Tens: 4 choices, Ones: 4 choices → 4 × 4 = 16 numbers."),
        ("From friends P, Q, R, list every team of 2.",
         "PQ, PR, QR → 3 teams (2 + 1)."),
        ("You have 2 hats and 3 scarves. How many hat-and-scarf combos?",
         "2 × 3 = 6 combos."),
    ]))
    A(practice("Apply", [
        ("A girl has 3 skirts, 2 tops and 2 pairs of shoes. How many complete outfits "
         "(skirt + top + shoes)?",
         "Three choices in a row, so multiply all: 3 × 2 × 2 = 12 outfits."),
        ("Using digits 2, 5, 9, how many 2-digit numbers can be made with <b>no repeats</b>?",
         "Tens: 3 choices, Ones: 2 left → 3 × 2 = 6 (25, 29, 52, 59, 92, 95)."),
        ("6 people at a meeting all shake hands once with each other. How many handshakes?",
         "Countdown: 5 + 4 + 3 + 2 + 1 = 15 handshakes."),
        ("An ice-cream has 5 flavours and a choice of cone or cup. How many ways to order one "
         "scoop?",
         "5 flavours × 2 holders = 10 ways."),
    ]))
    A(practice("Analyze", [
        ("Using digits 0, 4, 7 with repeats allowed, how many 2-digit numbers can be made? "
         "(Careful — a 2-digit number can't <em>start</em> with 0!)",
         "Tens place can't be 0, so only 4 or 7 → 2 choices. Ones place: 0, 4 or 7 → 3 choices. "
         "2 × 3 = 6 numbers (40, 44, 47, 70, 74, 77)."),
        ("Maya says “3 friends make 3 teams of 2.” Is she right? Explain.",
         "The count is right (AB, AC, BC = 3), but her reason should be the countdown 2 + 1 = 3, "
         "not “same as the number of friends.” With 4 friends it would be 6, not 4."),
        ("Which gives MORE 2-digit numbers from the digits 1, 2, 3, 4, 5 — allowing repeats, "
         "or not allowing them? By how many?",
         "Repeats: 5 × 5 = 25. No repeats: 5 × 4 = 20. Allowing repeats gives 5 more."),
        ("A lunch combo is 1 main + 1 drink. There are 12 possible combos and 4 drinks. "
         "How many mains are there?",
         "Mains × 4 = 12, so mains = 12 ÷ 4 = 3 mains."),
    ]))
    A(practice("Create", [
        ("Invent a “build-your-own pizza” menu with some bases and some toppings so that "
         "there are exactly <b>6</b> different pizzas. Show your numbers.",
         "Many answers, e.g. 2 bases × 3 toppings = 6, or 3 bases × 2 toppings = 6, or "
         "6 bases × 1 topping = 6."),
        ("Choose 4 digits and ask a friend how many 2-digit numbers can be made with no "
         "repeats. Write the question AND its answer.",
         "Example: digits 2, 3, 5, 8 → 4 × 3 = 12 two-digit numbers (no repeats)."),
    ]))

    A(challenge(
        P("A restaurant offers a <b>3-course meal</b>: <b>2 starters</b>, then <b>3 mains</b>, "
          "then <b>2 desserts</b>. <b>How many different 3-course meals</b> can a diner choose? "
          "And if they skip dessert, how many <b>2-course</b> meals (starter + main) are there?") +
        tryit("Multiply the choices for the courses you keep.",
              "Full 3-course meal: 2 × 3 × 2 = <b>12</b> meals. Skipping dessert leaves "
              "starter × main = 2 × 3 = <b>6</b> meals.")))

    A(kiwi("Nice — multiplying the choices in a row is exactly the Counting Principle at work. You've learned the <b>Counting Principle</b> (multiply choices in a row), "
           "the <b>countdown trick</b> for pairs and handshakes (3 + 2 + 1…), and how to "
           "<b>list in order</b> so nothing slips away. Next we'll ask not just “how many ways?” "
           "but “how <em>likely</em>?” — welcome to <b>Probability</b>. 🎲"))

    chapter("Part 5 · Brain Benders", 15, "Counting & Combinations",
            "Combinatorics · Brain Benders", "".join(b))
