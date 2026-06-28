#!/usr/bin/env python3
"""L3 Chapter 8 — Ratio & Proportion (Algebra · In Proportion). Bridges from the
Level-2 'fair shares' idea into comparing quantities, equivalent ratios, simplest
form, dividing a quantity in a ratio, proportion (a:b = c:d) and the unitary
method. Recipe / mixing / sharing stories throughout."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, ratio_bar, number_line, compare)


def build(chapter):
    b = []; A = b.append

    A(big_q("Two friends mix orange squash. Aarohi pours <b>2</b> cups of syrup into <b>6</b> cups of water; "
            "Ved pours <b>3</b> cups of syrup into <b>9</b> cups of water. Their cups are different sizes and "
            "the totals are different… yet the drinks taste <em>exactly the same</em>. How can two different "
            "mixes taste identical? By the end of this chapter you'll see why — and it's the secret behind "
            "every recipe, map and mixture on Earth."))
    A(kiwi("Hi explorer, Kiwi here! 🥝 In Level 2 you shared things into <em>fair, equal parts</em>. "
           "A <b>ratio</b> is the grown-up of that idea: it compares two amounts by asking "
           "<em>'how many of these for each of those?'</em> Ratios power cooking, mixing paint, reading maps "
           "and money. We'll build the whole idea from sharing — one careful step at a time."))

    # ── 1. What a ratio is ──────────────────────────────
    A(H("A ratio compares two amounts"))
    A(P("Suppose a fruit bowl has <b>3 mangoes</b> and <b>4 apples</b>. The <b>ratio</b> of mangoes to apples "
        "is written <b>3 : 4</b> and read <em>'three to four.'</em> It does not say there are 7 fruits — it "
        "tells you the <b>comparison</b>: for every 3 mangoes there are 4 apples."))
    A(figure(ratio_bar([3, 4], ["3 mangoes", "4 apples"]),
             "The bar split into 3 + 4 = 7 equal parts. Mangoes : apples = 3 : 4."))
    A(P("<b>Order matters!</b> 3 : 4 (mangoes to apples) is <em>not</em> the same as 4 : 3 (apples to mangoes). "
        "Always say the ratio in the order the words are given. The two numbers are called the "
        "<b>terms</b> of the ratio."))
    A(kiwi("A ratio is a comparison, not a total. <b>3 : 4</b> could mean 3 and 4, or 6 and 8, or 30 and 40 — "
           "what stays fixed is the <em>relationship</em>: 'a bit fewer mangoes than apples, in 3-to-4 steps.'"))
    A(tryit("In a class there are 10 girls and 15 boys. Write the ratio of girls to boys, "
            "and then boys to girls.",
            "Girls : boys = <b>10 : 15</b>. Boys : girls = <b>15 : 10</b>. The order flips the numbers!"))

    # ── 2. Equivalent ratios ────────────────────────────
    A(H("Equivalent ratios: many names for one comparison"))
    A(P("Here's the squash surprise unwrapped. Look at Aarohi's mix <b>2 : 6</b> and Ved's mix <b>3 : 9</b>. "
        "If you <em>multiply or divide BOTH terms by the same number</em>, the comparison doesn't change — "
        "you just get another name for it. These are <b>equivalent ratios</b>."))
    A(figure(ratio_bar([2, 6], ["syrup 2", "water 6"]), "Aarohi: 2 : 6 syrup to water."))
    A(figure(ratio_bar([3, 9], ["syrup 3", "water 9"]), "Ved: 3 : 9 syrup to water — same shape!"))
    A(P("Why do they taste the same? Divide both of Aarohi's terms by 2 → <b>1 : 3</b>. Divide both of Ved's "
        "by 3 → <b>1 : 3</b>. Underneath, <em>both</em> drinks are 1 part syrup to 3 parts water. Same "
        "recipe, just scaled up or down."))
    A(example("build three ratios equivalent to 2 : 3", steps([
        "Multiply both terms by 2: 2×2 : 3×2 = <b>4 : 6</b>.",
        "Multiply both terms by 5: 2×5 : 3×5 = <b>10 : 15</b>.",
        "Multiply both terms by 10: <b>20 : 30</b>.",
        "All of 2:3, 4:6, 10:15, 20:30 are the <em>same comparison</em> wearing different clothes.",
    ])))
    A(kiwi("Golden rule of ratios: <b>do the same thing to BOTH terms</b> — multiply both, or divide both, "
           "by the same number. (Never just one!) That keeps the comparison true."))
    A(tryit("Are <b>4 : 5</b> and <b>12 : 15</b> equivalent?",
            "Multiply 4:5 by 3 → 12 : 15. <b>Yes</b>, they're equivalent. (Or check by cross-multiplying: "
            "4 × 15 = 60 and 5 × 12 = 60 — equal, so they match.)"))

    # ── 3. Simplest form ────────────────────────────────
    A(H("Simplest form: the smallest, neatest name"))
    A(P("Just like fractions, every ratio has a <b>simplest form</b> — the smallest whole numbers that still "
        "give the same comparison. You reach it by dividing both terms by their biggest common factor (the "
        "<b>HCF</b>)."))
    A(example("write 18 : 24 in simplest form", steps([
        "Find the biggest number that divides both 18 and 24. That's <b>6</b>.",
        "Divide both terms by 6: 18 ÷ 6 = 3 and 24 ÷ 6 = 4.",
        "So 18 : 24 = <b>3 : 4</b> in simplest form. You can't go smaller — 3 and 4 share no common factor "
        "except 1.",
    ])))
    A(figure(compare(18 * 4, 24 * 3),
             "A quick equivalence check by cross-product: 18×4 = 24×3 = 72, so 18:24 really is 3:4."))
    A(tryit("Write <b>40 : 50</b> in simplest form.",
            "The HCF of 40 and 50 is 10. Divide both by 10 → <b>4 : 5</b>."))
    A(kiwi("Simplest form is the ratio's 'home address.' To test whether two ratios are equal, simplify "
           "both — if they land on the same simplest form, they're equivalent."))

    # ── 4. Dividing a quantity in a given ratio ─────────
    A(H("Sharing in a ratio: the 'parts' trick"))
    A(P("Now the most useful skill of all. Two friends share <b>₹35</b> in the ratio <b>3 : 4</b> (the older one "
        "did a little more work). How much does each get? The secret: count the <b>parts</b>."))
    A(figure(ratio_bar([3, 4], ["3 parts", "4 parts"]),
             "Split ₹35 into 3 + 4 = 7 equal parts, then hand out 3 and 4."))
    A(example("share ₹35 in the ratio 3 : 4", steps([
        "Add the terms to get the total number of parts: 3 + 4 = <b>7 parts</b>.",
        "Find the value of <em>one</em> part: ₹35 ÷ 7 = <b>₹5</b> per part.",
        "First share = 3 parts = 3 × ₹5 = <b>₹15</b>. Second share = 4 parts = 4 × ₹5 = <b>₹20</b>.",
        "Check: ₹15 + ₹20 = ₹35. ✓ And 15 : 20 simplifies back to 3 : 4. ✓",
    ])))
    A(kiwi("The recipe never changes: <b>(1)</b> add the ratio numbers to get total parts, <b>(2)</b> divide "
           "the quantity by total parts to get 'one part,' <b>(3)</b> multiply each ratio number by one part. "
           "Always check your two answers add back to the whole."))
    A(tryit("Share 24 sweets between two children in the ratio <b>5 : 3</b>.",
            "Total parts = 5 + 3 = 8. One part = 24 ÷ 8 = 3 sweets. Shares = 5×3 = <b>15</b> and 3×3 = <b>9</b>. "
            "Check: 15 + 9 = 24. ✓"))

    # ── 5. Proportion ───────────────────────────────────
    A(H("Proportion: when two ratios are equal"))
    A(P("A <b>proportion</b> is simply a statement that two ratios are equal, like <b>2 : 5 = 8 : 20</b>. "
        "We read it <em>'2 is to 5 as 8 is to 20.'</em> The squash mixes from the start were a proportion: "
        "2 : 6 = 3 : 9."))
    A(P("There's a beautiful test. In a true proportion, the <b>cross-products</b> match: multiply the "
        "outer pair and the inner pair, and they're equal."))
    A(example("is 2 : 5 = 8 : 20 a true proportion?", steps([
        "Cross-multiply: outer × outer = 2 × 20 = <b>40</b>.",
        "Inner × inner = 5 × 8 = <b>40</b>.",
        "The cross-products are equal (40 = 40), so <b>yes</b>, it's a true proportion.",
    ])))
    A(figure(compare(2 * 20, 5 * 8), "The cross-product check: 2×20 and 5×8 both equal 40 → true proportion."))
    A(P("Cross-products do more than check — they let you <b>find a missing term</b>. Suppose a proportion has "
        "a gap: <b>3 : 4 = 9 : ?</b>"))
    A(example("find the missing term in 3 : 4 = 9 : ?", steps([
        "Notice 3 became 9 — that's ×3. Do the same to the other side: 4 × 3 = <b>12</b>.",
        "So 3 : 4 = 9 : <b>12</b>.",
        "Check with cross-products: 3 × 12 = 36 and 4 × 9 = 36. Equal! ✓",
    ])))
    A(tryit("Find the missing term: <b>2 : 7 = ? : 21</b>.",
            "7 became 21, that's ×3, so 2 × 3 = <b>6</b>. Thus 2 : 7 = <b>6</b> : 21. "
            "Check: 2 × 21 = 42 and 7 × 6 = 42. ✓"))

    # ── 6. The unitary method ───────────────────────────
    A(H("The unitary method: go through ONE"))
    A(P("Here's a power-move that solves a huge family of problems: first find the value of <b>one</b> unit, "
        "then scale up to however many you want. It's called the <b>unitary method</b> — and it's secretly "
        "the 'one part' idea again."))
    A(example("5 identical pens cost ₹60. What do 8 pens cost?", steps([
        "Find the cost of <b>one</b> pen: ₹60 ÷ 5 = <b>₹12</b> each.",
        "Now scale up to 8 pens: 8 × ₹12 = <b>₹96</b>.",
        "Through-one thinking turned a tricky question into two easy steps.",
    ])))
    A(kiwi("Unitary method in a sentence: <b>divide to reach one, then multiply to reach many</b>. "
           "Whenever quantities scale together (more pens → more cost), this trick works."))
    A(P("It shines in recipes. A recipe uses <b>2 cups of flour for every 3 cups of sugar</b>. You're "
        "doubling the cake and now have <b>9 cups of sugar</b> — how much flour?"))
    A(example("flour needed for 9 cups of sugar (recipe is 2 flour : 3 sugar)", steps([
        "Per <em>one</em> cup of sugar: flour = 2 ÷ 3 cup… but let's keep it whole by using parts.",
        "9 cups of sugar is 9 ÷ 3 = <b>3 batches</b> of the '3 sugar' unit.",
        "Each batch needs 2 cups of flour, so flour = 3 × 2 = <b>6 cups</b>.",
        "Check the ratio: 6 flour : 9 sugar = 2 : 3. ✓ Same recipe, bigger cake.",
    ])))
    A(tryit("4 apples cost ₹100. How much do 10 apples cost? (unitary method)",
            "One apple = ₹100 ÷ 4 = ₹25. Ten apples = 10 × ₹25 = <b>₹250</b>."))

    # ── Practice ladder ─────────────────────────────────
    A(H("Now climb the ladder"))
    A(P("Find the simplest form or set up the parts first, then answer. Peek only after you try!"))

    A(practice("Remember", [
        ("Write the ratio of vowels to consonants in the word <b>MATHS</b>.",
         "Vowels: A (1). Consonants: M, T, H, S (4). Ratio = <b>1 : 4</b>."),
        ("Write 6 : 9 in simplest form.", "Divide both by 3 → <b>2 : 3</b>."),
        ("How many equal parts is a quantity split into for the ratio 4 : 5?", "4 + 5 = <b>9 parts</b>."),
        ("True or false: the ratio 3 : 4 is the same as 4 : 3.",
         "<b>False</b> — order matters; 3 : 4 ≠ 4 : 3."),
    ]))
    A(practice("Understand", [
        ("Write two ratios equivalent to 5 : 2.", "e.g. 10 : 4 (×2) and 15 : 6 (×3). Any '×same number' pair works."),
        ("Is 4 : 6 equivalent to 6 : 9?", "Simplify both: 4:6 → 2:3 and 6:9 → 2:3. Same → <b>yes</b>, equivalent."),
        ("Write 24 : 36 in simplest form.", "HCF is 12; divide both → <b>2 : 3</b>."),
        ("Find the missing term: 5 : 8 = 15 : ?", "5 became 15 (×3), so 8 × 3 = <b>24</b>."),
    ]))
    A(practice("Apply", [
        ("Share ₹40 between two friends in the ratio 3 : 5.",
         "Parts = 8; one part = 40 ÷ 8 = ₹5. Shares = 3×5 = <b>₹15</b> and 5×5 = <b>₹25</b>."),
        ("Divide 150 marbles in the ratio 2 : 3.",
         "Parts = 5; one part = 150 ÷ 5 = 30. Shares = 2×30 = <b>60</b> and 3×30 = <b>90</b>."),
        ("7 books cost ₹210. What do 4 books cost? (unitary method)",
         "One book = 210 ÷ 7 = ₹30. Four books = 4 × ₹30 = <b>₹120</b>."),
        ("A paint mix is 3 parts blue to 1 part white. To make 12 litres, how much of each colour?",
         "Parts = 4; one part = 12 ÷ 4 = 3 L. Blue = 3×3 = <b>9 L</b>, white = 1×3 = <b>3 L</b>."),
    ]))
    A(practice("Analyze", [
        ("Two ratios, 6 : 8 and 9 : 12, are claimed to be equal. Are they? Prove it two ways.",
         "Simplify: 6:8 → 3:4 and 9:12 → 3:4, same. Cross-products: 6×12 = 72 and 8×9 = 72, equal. "
         "So <b>yes</b>, equal."),
        ("Money is shared in the ratio 4 : 5 and the smaller share is ₹20. Find the total amount.",
         "The '4' part is ₹20, so one part = 20 ÷ 4 = ₹5. Larger share = 5 × 5 = ₹25. Total = 20 + 25 = <b>₹45</b>."),
        ("In a proportion a : 6 = 10 : 12, find a.",
         "Cross-products must match: a × 12 = 6 × 10 = 60, so a = 60 ÷ 12 = <b>5</b>. Check: 5:6 = 10:12. ✓"),
        ("A recipe uses 2 cups flour : 3 cups sugar. Riya used 8 cups flour but only 9 cups sugar. "
         "Did she keep the recipe's taste?",
         "Correct flour for 9 sugar is 6 cups (9 ÷ 3 × 2). She used 8 — too much flour, so 8 : 9 is NOT 2 : 3. "
         "<b>The taste changed.</b>"),
    ]))
    A(practice("Create", [
        ("Invent a real-life situation that uses the ratio 1 : 4, and explain what the two numbers mean.",
         "e.g. 'orange squash mixed 1 part syrup to 4 parts water' — for every 1 cup syrup, 4 cups water."),
        ("Make a proportion of your own that is TRUE, and prove it with cross-products.",
         "e.g. 3 : 5 = 12 : 20; check 3 × 20 = 60 and 5 × 12 = 60. ✓ Any equal pair works."),
        ("Write a sharing problem where ₹60 is split in the ratio 1 : 2 : 3, and solve it. "
         "(Hint: three terms — add all three for total parts.)",
         "Parts = 1 + 2 + 3 = 6; one part = 60 ÷ 6 = ₹10. Shares = <b>₹10, ₹20, ₹30</b>. "
         "Check: 10 + 20 + 30 = 60. ✓"),
    ]))

    A(challenge(
        P("A mixing mystery! A jug holds 12 litres of fruit punch, mixed <b>water : juice = 3 : 1</b>. "
          "You taste it and decide it's too strong — you want the new mix to be <b>water : juice = 5 : 1</b>. "
          "How much extra <b>water</b> must you stir in? (Tip: the amount of <em>juice</em> doesn't change — "
          "only water is added.)") +
        tryit("Track the juice, then rebuild the water.",
              "First mix: 3 + 1 = 4 parts in 12 L, so one part = 3 L. Juice = 1 part = <b>3 L</b>, "
              "water = 3 parts = 9 L. We keep the 3 L of juice fixed. For the new ratio 5 : 1, juice (the '1') "
              "is 3 L, so water (the '5') must be 5 × 3 = <b>15 L</b>. We already have 9 L of water, so add "
              "15 − 9 = <b>6 litres</b> of water. (Surprise: you fix a mixture not by removing juice, but by "
              "adding water — the ratio does the thinking for you!) 🎉")))

    A(kiwi("Outstanding! You can now read and write ratios, find equivalent ratios and simplest form, "
           "share a quantity in any ratio, test and complete a proportion, and solve through-one with the "
           "unitary method. Next we ask a deeper question: when one amount grows, does the other grow with it "
           "or shrink? That's <b>direct &amp; inverse variation</b>. ➡️"))

    chapter("Part 2 · Parts & Wholes", 8, "Ratio & Proportion",
            "Algebra · In Proportion", "".join(b))
