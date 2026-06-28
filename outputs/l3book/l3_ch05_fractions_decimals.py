#!/usr/bin/env python3
"""L3 Chapter 5 — Fractions & Decimals (Algebra · Parts & Wholes). Solidifies the
Level-2 fraction & decimal ideas and climbs higher: equivalent fractions, compare,
all four operations (incl. 'of a number'), mixed numbers, decimal place value to
thousandths, decimal +-x/, rounding, and the fraction <-> decimal bridge."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, fraction_bar, fraction_circle,
                        decimal_grid, number_line, compare)


def build(chapter):
    b = []; A = b.append

    A(big_q("Two pizzas, one cut into <b>4</b> slices and one into <b>6</b>. You grab <b>3 slices</b> "
            "from each. Did you take the same amount of pizza both times? And here's the twist — could you "
            "write each amount as a number with a tiny <em>dot</em> in it instead? By the end of this chapter "
            "you'll answer both in your head."))
    A(kiwi("Welcome back, explorer! \U0001F95D In Level 2 you met <b>fractions</b> (parts of a whole) and "
           "<b>decimals</b> (the dot way of writing them). This chapter is your <b>power-up</b>: we'll sharpen "
           "everything you know, then add the grown-up moves — comparing, all four operations, mixed numbers, "
           "rounding, and the secret bridge that turns any fraction into a decimal and back. Nothing new will "
           "appear out of thin air; each move grows from one you already trust."))

    A(H("30-second warm-up: a fraction is two jobs in one"))
    A(P("Every fraction does two jobs at once. The <b>bottom</b> number (the <b>denominator</b>) says how many "
        "<em>equal</em> parts the whole was cut into. The <b>top</b> number (the <b>numerator</b>) counts how "
        "many of those parts you're talking about. Here are <b>3</b> shaded out of <b>8</b> equal pieces:"))
    A(figure(fraction_bar(8, 3), "Numerator 3 (shaded), denominator 8 (total equal parts) → 3/8"))
    A(P("Same idea on a round pizza — <b>5</b> slices out of <b>6</b> is <b>5/6</b>:"))
    A(figure(fraction_circle(6, 5), "5 of 6 equal slices = 5/6"))
    A(kiwi("Remember the surprise from Level 2: a <em>bigger</em> denominator means <em>smaller</em> pieces. "
           "So 1/8 is smaller than 1/4, even though 8 is bigger than 4. Cutting into more pieces makes each "
           "piece tinier."))

    A(H("Equivalent fractions — same amount, different name"))
    A(P("Cut a bar in half and shade one half: <b>1/2</b>. Now slice each half in two so the bar has 4 pieces — "
        "the shaded amount is now <b>2</b> of <b>4</b>. Not one crumb of chocolate moved, so <b>1/2 = 2/4</b>. "
        "Fractions that name the same amount are <b>equivalent</b>."))
    A(figure(fraction_bar(2, 1), "Half shaded = 1/2"))
    A(figure(fraction_bar(4, 2), "Same amount, cut finer = 2/4. So 1/2 = 2/4"))
    A(figure(fraction_bar(8, 4), "Finer still = 4/8 — all the very same amount of chocolate"))
    A(P("<b>The rule:</b> multiply (or divide) the top <em>and</em> the bottom by the <em>same</em> number, and "
        "the fraction keeps its value. Multiplying changes its <em>name</em>, never its <em>amount</em>."))
    A(P("Going the other way — dividing top and bottom — gives the <b>simplest form</b>: the smallest, cleanest "
        "name a fraction can have. You divide both by their biggest common factor until nothing else divides "
        "evenly."))
    A(example("write 18/24 in simplest form", steps([
        "Find a number that divides <b>both</b> 18 and 24. The biggest one is <b>6</b>.",
        "Divide top and bottom by 6: (18÷6)/(24÷6) = <b>3/4</b>.",
        "Can 3/4 be cut down more? 3 and 4 share no factor but 1 — so <b>3/4</b> is simplest. ✓",
        "Check: 3/4 = 6/8 = 9/12 = 18/24, all the same slice of the world.",
    ])))
    A(tryit("Write <b>6/10</b> in simplest form.",
            "Both 6 and 10 divide by 2: (6÷2)/(10÷2) = <b>3/5</b>. (And 3 and 5 share nothing, so we're done.)"))

    A(H("Comparing &amp; ordering fractions"))
    A(P("If two fractions already share the <b>same denominator</b>, just compare the tops: 5/8 beats 3/8 "
        "because 5 pieces beat 3 pieces of the same size. When the denominators are <em>different</em>, give "
        "the fractions a <b>common denominator</b> first — rename them so the pieces are the same size, then "
        "compare."))
    A(example("which is bigger, 2/3 or 3/4?", steps([
        "The denominators are 3 and 4. A size that fits both is <b>12</b>.",
        "Rename: 2/3 = 8/12 (×4 top and bottom). And 3/4 = 9/12 (×3 top and bottom).",
        "Now compare the tops: 9 &gt; 8, so <b>3/4 &gt; 2/3</b>.",
        "Picture-check: three-quarters is closer to a whole than two-thirds. ✓",
    ])))
    A(figure(fraction_bar(12, 8), "2/3 renamed to twelfths = 8/12 (8 of 12 pieces shaded)"))
    A(figure(fraction_bar(12, 9), "3/4 renamed to twelfths = 9/12 — one more piece shaded, so 3/4 is bigger"))
    A(tryit("Order from smallest to biggest: 1/2, 2/5, 7/10.",
            "Use tenths: 1/2 = 5/10, 2/5 = 4/10, 7/10 = 7/10. So <b>2/5 &lt; 1/2 &lt; 7/10</b>."))

    A(H("Adding &amp; subtracting fractions"))
    A(P("You can only add or subtract things that are the <em>same size</em>. Three apples plus two apples is "
        "five apples — but three apples plus two oranges isn't five of anything. Fractions are the same: make "
        "the denominators match, then add (or subtract) just the <b>tops</b>. The denominator names the piece "
        "size, so it stays put."))
    A(example("add 2/3 + 1/4", steps([
        "Common denominator of 3 and 4 is <b>12</b>.",
        "Rename: 2/3 = 8/12 and 1/4 = 3/12.",
        "Add the tops, keep the bottom: 8/12 + 3/12 = <b>11/12</b>.",
        "Is 11/12 simplest? 11 and 12 share no factor — yes. ✓",
    ])))
    A(figure(fraction_bar(12, 11), "8/12 + 3/12 = 11/12 — almost a whole bar"))
    A(example("subtract 3/4 − 5/8", steps([
        "Common denominator of 4 and 8 is <b>8</b>.",
        "Rename only the one that needs it: 3/4 = 6/8.",
        "Subtract the tops: 6/8 − 5/8 = <b>1/8</b>. ✓",
    ])))
    A(tryit("Work out 5/6 − 1/3.",
            "Common bottom 6: 1/3 = 2/6. Then 5/6 − 2/6 = <b>3/6</b> = <b>1/2</b> in simplest form."))

    A(trap(P("A super-common slip: <b>1/3 + 1/3 = 2/6</b>. Here the bottoms got added too — but the "
             "denominator is the <em>piece size</em>, and that doesn't change when you collect pieces! "
             "Worse, 2/6 = 1/3, the <em>same</em> as one of the parts you added — a sum can't equal just "
             "one of its pieces. <b>The right way:</b> the bottoms already match, so add only the tops and "
             "keep the bottom: 1/3 + 1/3 = <b>2/3</b>. (Think: one-third pizza plus one-third pizza is "
             "two-thirds of a pizza.)")))

    A(H("Multiplying fractions — and the magic word “of”"))
    A(P("Multiplying fractions is the <em>easy</em> one — no common denominator needed! Just multiply the tops "
        "together and the bottoms together, then simplify."))
    A(example("multiply 2/3 × 6/7", steps([
        "Tops: 2 × 6 = 12. Bottoms: 3 × 7 = 21. So 12/21.",
        "Simplify: 12 and 21 both divide by 3 → <b>4/7</b>. ✓",
    ])))
    A(kiwi("Here's a surprise that unlocks half of word-problem maths: the word <b>“of”</b> means "
           "<b>multiply</b>. “Two-fifths <em>of</em> 30” is just <b>2/5 × 30</b>. And the quick trick — "
           "<em>divide by the bottom, multiply by the top</em>: 30 ÷ 5 = 6, then 6 × 2 = <b>12</b>."))
    A(figure(fraction_bar(5, 2), "Split 30 into 5 equal groups (6 each), take 2 groups → 2/5 of 30 = 12"))
    A(example("find 3/8 of 64", steps([
        "Divide by the bottom: 64 ÷ 8 = 8 (that's one-eighth).",
        "Multiply by the top: 8 × 3 = <b>24</b>.",
        "So 3/8 of 64 = <b>24</b>. (Check: 5/8 would be the other 40, and 24 + 40 = 64. ✓)",
    ])))
    A(tryit("A class has 48 pupils and 5/6 of them came to the trip. How many came?",
            "48 ÷ 6 = 8, then 8 × 5 = <b>40</b> pupils came. (The 8 who stayed back are the missing 1/6.)"))

    A(H("Dividing fractions — flip and multiply"))
    A(P("Dividing by a fraction asks: “how many of <em>these</em> fit inside?” And here is the famous shortcut: "
        "<b>keep the first, flip the second, then multiply</b>. (The flipped fraction is called its "
        "<b>reciprocal</b> — top and bottom swapped.)"))
    A(example("work out 3/4 ÷ 2/3", steps([
        "Keep the first: 3/4.",
        "Flip the second: 2/3 becomes 3/2.",
        "Multiply: 3/4 × 3/2 = 9/8 = <b>1⅛</b>. ✓",
        "Why flip works: dividing by 2/3 is the same as multiplying by how-many-2/3-make-1, which is 3/2.",
    ])))
    A(tryit("How many 1/4-cups of flour are in 3 cups?",
            "3 ÷ 1/4 = 3 × 4 = <b>12</b> quarter-cups. (Each whole cup holds 4 quarter-cups, and 3 × 4 = 12.)"))

    A(H("Mixed numbers ↔ improper fractions"))
    A(P("A <b>mixed number</b> like 1¾ means “one whole and three quarters.” An <b>improper fraction</b> like "
        "7/4 means “seven quarter-pieces.” They're the same amount wearing different clothes — and you can "
        "switch between them in your head."))
    A(figure(fraction_bar(4, 4), "Four quarters rebuild one whole = 4/4 = 1…"))
    A(figure(fraction_bar(4, 3), "…and 3 more quarters left over. Together 7/4 = 1¾"))
    A(P("• <b>Improper → mixed:</b> divide top by bottom. 7 ÷ 4 = 1 remainder 3, so 7/4 = <b>1¾</b>.<br>"
        "• <b>Mixed → improper:</b> multiply the whole by the bottom, add the top. For 2⅜: 2 × 5 + 3 = 13, "
        "so 2⅜ = <b>13/5</b>."))
    A(example("add the mixed numbers 1½ + 2¾", steps([
        "Turn each into an improper fraction: 1½ = 3/2 and 2¾ = 11/4.",
        "Common denominator 4: 3/2 = 6/4. Add: 6/4 + 11/4 = 17/4.",
        "Back to a mixed number: 17 ÷ 4 = 4 remainder 1 → <b>4¼</b>. ✓",
    ])))
    A(tryit("Change <b>11/4</b> to a mixed number, then change <b>3½</b> to an improper fraction.",
            "11 ÷ 4 = 2 r3 → <b>2¾</b>. And 3½ = (3×2 + 1)/2 = <b>7/2</b>."))

    A(H("Decimals: place value to the thousandths"))
    A(P("A <b>decimal</b> is a fraction whose bottom is always 10, 100, 1000… — a power of ten. The tiny "
        "<b>decimal point</b> separates the wholes (on the left) from the parts (on the right). Each place to "
        "the right is worth <em>ten times less</em> than the one before: <b>tenths</b>, then "
        "<b>hundredths</b>, then <b>thousandths</b>."))
    A(figure(decimal_grid(35), "35 of 100 little squares shaded = 35/100 = 0.35"))
    A(P("Read <b>4.276</b> place by place: <b>4 ones + 2 tenths + 7 hundredths + 6 thousandths</b>, the same as "
        "4 + 2/10 + 7/100 + 6/1000. Out loud it's “four point two seven six.”"))
    A(kiwi("Big idea you'll use forever: extra zeros on the <em>right</em> of a decimal don't change its value. "
           "<b>0.5 = 0.50 = 0.500</b> — five tenths, fifty hundredths, five hundred thousandths are all the same "
           "amount. That trick makes comparing and subtracting decimals painless."))
    A(figure(decimal_grid(50), "0.5 and 0.50 fill exactly the same half of the grid"))
    A(tryit("In <b>3.408</b>, what is the value of the 4, and what is the value of the 8?",
            "The 4 is in the tenths place → <b>4 tenths = 0.4</b>. The 8 is in the thousandths place → "
            "<b>8 thousandths = 0.008</b>."))

    A(H("Comparing decimals"))
    A(P("Line decimals up by their dots and compare from the <em>left</em> (the biggest places first). The "
        "first place that differs decides the winner. Tip: give them the same number of decimal places by "
        "padding with zeros on the right — that never changes the value."))
    A(figure(compare(0.6, 0.06), "0.6 beats 0.06 — six tenths is far more than six hundredths"))
    A(P("The grids prove it — sixty squares versus six:"))
    A(figure(decimal_grid(60), "0.6 = 60 of 100 squares"))
    A(tryit("Which is bigger, <b>0.45</b> or <b>0.5</b>?",
            "Pad to two places: 0.5 = 0.50. Now 50 hundredths beats 45 hundredths, so <b>0.5 &gt; 0.45</b>. "
            "(Don't be fooled by 45 having more digits!)"))

    A(H("Adding &amp; subtracting decimals — line up the dots"))
    A(P("The one golden rule: <b>line up the decimal points</b> (which lines up tenths under tenths, hundredths "
        "under hundredths), pad with zeros so both have the same length, then add or subtract just like whole "
        "numbers and bring the dot straight down."))
    A(example("add 0.7 + 0.45", steps([
        "Pad: 0.7 becomes 0.70 so both have two places.",
        "Line up the dots and add: 0.70 + 0.45 = <b>1.15</b>.",
        "Check it's sensible: 0.7 is a bit over a half, 0.45 a bit under, so just over 1. ✓",
    ])))
    A(example("subtract 3.6 − 1.85", steps([
        "Pad: 3.6 becomes 3.60.",
        "Line up and subtract: 3.60 − 1.85 = <b>1.75</b>. ✓",
    ])))
    A(tryit("A ribbon is 2.5 m long and you cut off 0.8 m. How much is left?",
            "2.5 − 0.8 = <b>1.7 m</b> left."))

    A(H("Multiplying &amp; dividing decimals"))
    A(P("<b>Multiplying:</b> ignore the dots, multiply as whole numbers, then count the total decimal places in "
        "both factors and put that many places in the answer. <b>Dividing:</b> the neat trick is to make the "
        "<em>divider</em> a whole number by shifting <em>both</em> dots the same number of places."))
    A(example("multiply 1.2 × 0.3", steps([
        "Ignore dots: 12 × 3 = 36.",
        "Count decimal places: 1.2 has 1, and 0.3 has 1 → 2 places in total.",
        "Put 2 places in the answer: <b>0.36</b>.",
        "Sanity check: about 1 of 0.3 is 0.3, so a bit more — 0.36 fits. ✓",
    ])))
    A(example("divide 4.5 ÷ 5", steps([
        "Divider 5 is already a whole number, so divide straight: 4.5 ÷ 5.",
        "45 ÷ 5 = 9, and there's 1 decimal place, so the answer is <b>0.9</b>. ✓",
    ])))
    A(tryit("Work out 0.8 ÷ 0.2.",
            "Shift both dots one place to make the divider whole: 8 ÷ 2 = <b>4</b>. (How many 0.2s fit in 0.8? "
            "Four of them.)"))

    A(H("Rounding decimals"))
    A(P("To round to a place, look at the digit just to its <em>right</em>: 5 or more rounds the place "
        "<b>up</b>, 4 or less leaves it the same — then drop the rest. This is how prices, measurements and "
        "scores get tidied up."))
    A(figure(number_line(3, 4, 1, [(3.8, "3.8", "#E0556E")]),
             "3.8 sits closer to 4 than to 3 → rounds to 4 (to the nearest whole)"))
    A(example("round 3.847 to 2 decimal places", steps([
        "We're keeping 2 places: 3.84… The digit to the right is the <b>7</b> in the thousandths.",
        "7 is 5-or-more, so round the hundredths up: 4 becomes 5.",
        "Answer: <b>3.85</b>. ✓",
    ])))
    A(tryit("Round 12.96 to 1 decimal place.",
            "The digit after the tenths is 6 (≥ 5), so the tenths 9 rounds up — it carries: 12.96 → <b>13.0</b>."))

    A(H("The bridge: fraction ↔ decimal"))
    A(P("Fractions and decimals are the <em>same idea</em> in two outfits — and crossing between them is a "
        "superpower. <b>Fraction → decimal:</b> just divide the top by the bottom (or rename the bottom to "
        "10/100/1000). <b>Decimal → fraction:</b> count the places — two places means hundredths — then "
        "simplify."))
    A(figure(fraction_bar(4, 1), "1/4 of a bar…"))
    A(figure(decimal_grid(25), "…is exactly 0.25 of the grid. So 1/4 = 0.25 — the same amount."))
    A(P("A few worth memorising forever: <b>1/2 = 0.5</b>, <b>1/4 = 0.25</b>, <b>3/4 = 0.75</b>, "
        "<b>1/5 = 0.2</b>, <b>1/10 = 0.1</b>, <b>1/8 = 0.125</b>."))
    A(example("write 3/8 as a decimal", steps([
        "Divide top by bottom: 3 ÷ 8.",
        "3.000 ÷ 8 = 0.375 (8 into 30 is 3 with 6 left, into 60 is 7 with 4 left, into 40 is 5 exactly).",
        "So 3/8 = <b>0.375</b>. ✓",
    ])))
    A(example("write 0.375 back as a fraction", steps([
        "It has 3 decimal places → thousandths: 0.375 = 375/1000.",
        "Simplify: both divide by 125 → <b>3/8</b>.",
        "Full circle — 3/8 and 0.375 are the same number. ✓",
    ])))
    A(kiwi("A delicious surprise: not every fraction gives a tidy decimal. Try <b>1/3</b> — divide and you get "
           "0.3333… forever! These never-ending decimals are called <b>recurring decimals</b>, and we write "
           "them with a dot or bar above the repeating digit. The fraction 1/3 is the <em>exact</em> value; the "
           "decimal can only get close. Sometimes a fraction is the more honest number. \U0001F3AF"))
    A(tryit("Write <b>7/20</b> as a decimal.",
            "Rename the bottom to 100: 7/20 = 35/100 (×5 top and bottom) = <b>0.35</b>."))

    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("In 7/9, name the numerator and the denominator.", "Numerator 7 (top), denominator 9 (bottom)."),
        ("Write 4/4 as a whole number.", "1 (top equals bottom)."),
        ("What does the word “of” tell you to do in “1/2 of 20”?", "Multiply: 1/2 × 20 = 10."),
        ("In the decimal 5.62, which place is the 6 in?", "The tenths place (6 tenths = 0.6)."),
        ("Is 0.4 the same number as 0.40?", "Yes — extra zeros on the right don't change the value."),
    ]))
    A(practice("Understand", [
        ("Write 6/10 in simplest form.", "Divide top and bottom by 2 → 3/5."),
        ("Which is bigger, 2/3 or 3/4?", "3/4 (rename to twelfths: 9/12 &gt; 8/12)."),
        ("Change 7/4 to a mixed number.", "7 ÷ 4 = 1 r3 → 1¾."),
        ("Write 1/8 as a decimal.", "1 ÷ 8 = 0.125."),
        ("Round 0.4783 to 3 decimal places.", "The 4th digit is 3 (&lt; 5), so it stays: 0.478."),
    ]))
    A(practice("Apply", [
        ("Add 2/3 + 1/4.", "Common bottom 12: 8/12 + 3/12 = 11/12."),
        ("Find 3/8 of 64.", "64 ÷ 8 = 8, then 8 × 3 = 24."),
        ("Work out 0.7 + 0.45.", "Pad to 0.70 + 0.45 = 1.15."),
        ("A 48-pupil class had 5/6 present. How many were present?", "48 ÷ 6 × 5 = 40."),
        ("Multiply 2.5 × 1.4.", "25 × 14 = 350, with 2 decimal places → 3.50."),
    ]))
    A(practice("Analyze", [
        ("Vani says 0.45 &gt; 0.5 because 45 is bigger than 5. Is she right? Explain.",
         "No. Pad to 0.50; 50 hundredths beats 45 hundredths, so 0.5 &gt; 0.45. Digit count doesn't decide size."),
        ("Order from smallest to biggest: 1/2, 2/5, 7/10.",
         "As tenths: 4/10, 5/10, 7/10 → 2/5 &lt; 1/2 &lt; 7/10."),
        ("Without a calculator, is 5/8 more or less than 0.6? Show how you know.",
         "5/8 = 0.625, and 0.625 &gt; 0.6, so 5/8 is more than 0.6 (by 0.025)."),
        ("How many 1/4-litre cups fill a 3-litre jug?", "3 ÷ 1/4 = 3 × 4 = 12 cups."),
    ]))
    A(practice("Create", [
        ("Invent a sharing story whose answer is exactly 3/4, then write that as a decimal too.",
         "Many answers — e.g. “4 friends split a cake into 4 equal parts and 3 are eaten” → 3/4 = 0.75 eaten."),
        ("Write three different fractions equivalent to 1/2, then one that is recurring as a decimal.",
         "1/2 = 2/4 = 3/6 = 50/100; a recurring one is 1/3 = 0.333…"),
        ("Make a decimal addition that totals exactly 1, using two numbers with different decimal lengths.",
         "Any like 0.6 + 0.40 = 1.00, or 0.85 + 0.15 = 1.00."),
    ]))

    A(challenge(
        P("Back to the BIG QUESTION! You took <b>3 slices from a 4-slice pizza</b> (that's 3/4) and "
          "<b>3 slices from a 6-slice pizza</b> (that's 3/6). Which grab was more pizza — and exactly how much "
          "more? Write both as fractions <em>and</em> decimals to be sure.") +
        tryit("Make the pieces the same size, then compare.",
              "3/4 = 0.75 and 3/6 = 1/2 = 0.5. So the 4-slice pizza gave more! As fractions with a common "
              "bottom: 3/4 = 9/12 and 3/6 = 6/12, so you took <b>3/12 = 1/4 more</b> — which is <b>0.25</b> of "
              "a pizza extra. Same number of slices, very different amounts — because the slices were "
              "different sizes. \U0001F355"))) 

    A(kiwi("Outstanding! You can now simplify, compare, and run all four operations on fractions <em>and</em> "
           "decimals, switch a number freely between the two, round neatly, and even spot a recurring decimal. "
           "Next we meet a brand-new disguise for these same parts-of-a-whole: <b>percentages</b> — the special "
           "'out of 100' that runs every sale tag and battery icon you'll ever see. \U0001F4AF"))

    chapter("Part 2 · Parts & Wholes", 5, "Fractions & Decimals",
            "Algebra · Parts & Wholes", "".join(b))
