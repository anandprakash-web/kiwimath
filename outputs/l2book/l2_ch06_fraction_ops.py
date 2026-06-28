#!/usr/bin/env python3
"""Chapter 6 — Comparing & Adding Fractions  (Fractions · Fair Shares)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, fraction_bar, fraction_circle, frac_on_line, compare)


def build(chapter):
    b = []
    A = b.append

    A(big_q("You and your friend each grab a slice of the <em>same</em> cake. Yours is <b>3/8</b> of the cake, "
            "theirs is <b>5/8</b>. Without weighing anything, who got more — and exactly how much more? "
            "And if you put both slices on one plate, how much cake is on the plate?"))
    A(kiwi("Hi, <b>Kiwi</b> here! In the last chapter we met fractions. Now we'll learn to <b>compare</b> them "
           "(which is bigger?), <b>order</b> them (line them up), and <b>add and subtract</b> them. The good news: "
           "if the pieces are the same size, it's as easy as counting. Let's start there."))

    A(H("Comparing fractions with the same denominator"))
    A(P("When two fractions have the <b>same denominator</b>, the pieces are exactly the same size — so you just "
        "count how many pieces each has. <em>More pieces wins.</em> Compare <b>3/8</b> and <b>5/8</b>:"))
    A(figure(fraction_bar(8, 3), "3/8 — three pieces shaded"))
    A(figure(fraction_bar(8, 5), "5/8 — five pieces shaded (clearly more!)"))
    A(P("Both bars are cut into eighths, so each piece is the same. 5 pieces beat 3 pieces, so <b>5/8 &gt; 3/8</b>. "
        "When denominators match, the bigger numerator is the bigger fraction."))
    A(figure(compare(5, 3), "Same denominator: just compare the numerators, 5 &gt; 3"))
    A(tryit("Which is greater, <b>4/9</b> or <b>7/9</b>?",
            "Same denominator (ninths), so compare numerators: 7 &gt; 4, therefore <b>7/9 &gt; 4/9</b>."))

    A(H("Comparing fractions with the same numerator"))
    A(P("What if the <em>tops</em> match instead? Like <b>1/3</b> versus <b>1/6</b>. Here's the surprising rule: "
        "with the same numerator, the fraction with the <b>smaller denominator</b> is <em>bigger</em>. Why? A smaller "
        "denominator means fewer, <em>larger</em> pieces. One big piece beats one small piece."))
    A(figure(fraction_circle(3, 1), "1/3 — one piece of a pizza cut into 3 (a big piece)"))
    A(figure(fraction_circle(6, 1), "1/6 — one piece of a pizza cut into 6 (a small piece)"))
    A(P("Same one piece each, but the thirds-pizza has bigger slices. So <b>1/3 &gt; 1/6</b>."))
    A(kiwi("Careful! This is the trap that fools everyone: with fractions, a <em>bigger bottom number</em> can mean "
           "a <em>smaller</em> fraction. Think pizza slices, not whole numbers, and you'll never be fooled."))
    A(tryit("Which is greater, <b>2/5</b> or <b>2/9</b>?",
            "Same numerator (2), so the smaller denominator wins: <b>2/5 &gt; 2/9</b> (fifths are bigger pieces "
            "than ninths)."))

    A(H("Ordering fractions"))
    A(P("To <b>order</b> several fractions (smallest to largest, or largest to smallest), use the rules above. "
        "If they all share a denominator, just sort by numerator. Order <b>2/7, 6/7, 1/7, 4/7</b> from smallest "
        "to largest:"))
    A(example("ordering same-denominator fractions", steps([
        "All have denominator 7, so only the numerators matter: 2, 6, 1, 4.",
        "Sort the numerators smallest → largest: 1, 2, 4, 6.",
        "Re-attach the denominator: <b>1/7, 2/7, 4/7, 6/7</b>. Done!",
    ])))
    A(tryit("Put these in order, smallest first: <b>5/10, 2/10, 9/10, 1/10</b>.",
            "Same denominator, so sort the tops: 1, 2, 5, 9 → <b>1/10, 2/10, 5/10, 9/10</b>."))

    A(H("Adding fractions with the same denominator"))
    A(P("Now the fun part. To <b>add</b> fractions whose denominators are the same, you keep the denominator and "
        "just <em>add the numerators</em> — because you're counting same-sized pieces. Back to our cake: "
        "<b>3/8 + 5/8</b>:"))
    A(figure(fraction_bar(8, 3), "Start with 3/8 on the plate…"))
    A(figure(fraction_bar(8, 8), "…add 5/8 more, and the plate is full: 3 + 5 = 8 pieces = 8/8 = 1 whole cake!"))
    A(P("So <b>3/8 + 5/8 = 8/8 = 1</b>. The denominator stayed 8 (the pieces didn't change size); we only added "
        "how many pieces: 3 + 5 = 8."))
    A(kiwi("Golden rule: <b>add the tops, keep the bottom</b>. Never add the bottoms! 1/4 + 1/4 is 2/4, "
           "not 2/8. (Two quarter-slices make a half-slice, not a smaller slice.)"))
    A(example("add 2/9 + 4/9", steps([
        "The denominators are the same (9), so keep 9 on the bottom.",
        "Add the numerators: 2 + 4 = 6.",
        "Answer: <b>6/9</b>. (We could also simplify it to 2/3 by dividing top and bottom by 3.)",
    ])))
    A(tryit("Add <b>1/5 + 3/5</b>.",
            "Keep the bottom (5), add the tops: 1 + 3 = 4 → <b>4/5</b>."))

    A(H("Subtracting fractions with the same denominator"))
    A(P("Subtracting is the mirror image: keep the denominator, and <em>subtract the numerators</em>. If a pizza "
        "has <b>7/8</b> left and you eat <b>3/8</b>, how much is left? Count the pieces that remain:"))
    A(figure(fraction_bar(8, 7), "7/8 of the pizza is there to start"))
    A(figure(fraction_bar(8, 4), "Eat 3 pieces (7 − 3 = 4) and 4/8 is left = half a pizza"))
    A(P("So <b>7/8 − 3/8 = 4/8</b>, which is the same as <b>1/2</b>. We answered the BIG QUESTION too: "
        "the 5/8 slice beats the 3/8 slice by <b>5/8 − 3/8 = 2/8 = 1/4</b> of the cake."))
    A(tryit("Work out <b>6/7 − 2/7</b>.",
            "Keep the bottom (7), subtract the tops: 6 − 2 = 4 → <b>4/7</b>."))

    A(H("A peek at unlike denominators — make them match first"))
    A(P("What about adding fractions whose bottoms are <em>different</em>, like <b>1/2 + 1/4</b>? You can't add "
        "halves and quarters directly — the pieces are different sizes. The trick is to <b>rename one fraction</b> "
        "so both have the same denominator, using equivalent fractions from last chapter."))
    A(P("We know <b>1/2 = 2/4</b>. So rewrite the problem with quarters everywhere, and now it's easy:"))
    A(figure(fraction_bar(4, 2), "1/2 is the same as 2/4…"))
    A(figure(fraction_bar(4, 3), "…so 1/2 + 1/4 = 2/4 + 1/4 = 3/4"))
    A(example("add the unlike fractions 1/3 + 1/6", steps([
        "The denominators 3 and 6 are different. Make them match.",
        "6 works for both: 1/3 = 2/6 (multiply top and bottom by 2). 1/6 stays as 1/6.",
        "Now add same-sized pieces: 2/6 + 1/6 = <b>3/6</b>.",
        "Simplify: 3/6 = <b>1/2</b>. ✓",
    ])))
    A(tryit("Add <b>1/2 + 1/6</b> by first changing 1/2 into sixths.",
            "1/2 = 3/6, so 3/6 + 1/6 = <b>4/6</b>, which simplifies to <b>2/3</b>."))

    A(trap(
        P("The biggest trap with <em>unlike</em> fractions is to add (or compare) them <b>without making the "
          "pieces match first</b>. Someone sees <b>1/2 + 1/4</b> and writes <b>2/6</b> — adding tops together "
          "and bottoms together. Both parts are wrong!") +
        P("<b>Why it happens:</b> when the denominators are different, it's tempting to just smash the numbers "
          "together: 1+1 on top, 2+4 on the bottom. But you can't add halves and quarters directly any more "
          "than you can add 1 apple and 1 orange and call it “2 appleoranges” — the pieces are different sizes.") +
        P("<b>The right way:</b> rename one fraction so both share a denominator, then add only the tops. "
          "1/2 = 2/4, so <b>1/2 + 1/4 = 2/4 + 1/4 = 3/4</b>. Sanity check: 3/4 is more than a half, which is "
          "right — but the wrong answer 2/6 is <em>less</em> than a half, so it can't be correct. The same "
          "“make the pieces match” rule is what lets you <b>compare</b> unlike fractions safely too.")))

    A(H("Mixed numbers in a sum"))
    A(P("Sometimes an answer is bigger than one whole, and we tidy it into a <b>mixed number</b>. Add "
        "<b>4/5 + 3/5</b>: keep the bottom, add the tops, 4 + 3 = 7, giving <b>7/5</b>. That's improper, so we "
        "rename it: 7 ÷ 5 = 1 remainder 2, so <b>7/5 = 1⅖</b> — one whole and two-fifths."))
    A(example("add 5/6 + 5/6 and write it as a mixed number", steps([
        "Same denominator (6): add the tops, 5 + 5 = 10 → 10/6.",
        "10/6 is improper. How many sixes in ten? 10 ÷ 6 = 1 remainder 4.",
        "So 10/6 = <b>1 and 4/6</b>, and 4/6 simplifies to 2/3 → <b>1⅔</b>.",
    ])))
    A(tryit("Add <b>3/4 + 3/4</b> and give the answer as a mixed number.",
            "3 + 3 = 6, so 6/4. Then 6 ÷ 4 = 1 remainder 2 → 1 and 2/4 = <b>1½</b>."))

    A(H("Now you try — climb the ladder"))
    A(P("Work upward, one rung at a time. Try first, then check!"))

    A(practice("Remember", [
        ("To add fractions with the same denominator, do you add the tops or the bottoms?", "Add the tops."),
        ("Fill in: 3/10 + 4/10 = __/10.", "7 (so 7/10)."),
        ("Which is bigger when denominators are the same — the one with the bigger top or smaller top?",
         "The one with the bigger top (numerator)."),
        ("What is 5/5 as a whole number?", "1."),
    ]))
    A(practice("Understand", [
        ("Compare using > or <: 4/7 ___ 6/7.", "4/7 < 6/7 (same bottom, smaller top is smaller)."),
        ("Compare using > or <: 1/4 ___ 1/8.", "1/4 > 1/8 (same top, smaller bottom is bigger)."),
        ("Add: 2/6 + 3/6.", "5/6."),
        ("Subtract: 5/9 − 1/9.", "4/9."),
        ("Why can't we add 1/2 + 1/3 straight away?",
         "The pieces are different sizes (halves vs thirds); we must rename them to a common denominator first."),
    ]))
    A(practice("Apply", [
        ("A jug is 3/8 full, then 2/8 more juice is poured in. How full is it now?", "3/8 + 2/8 = 5/8 full."),
        ("Order from largest to smallest: 3/7, 1/7, 6/7, 4/7.", "6/7, 4/7, 3/7, 1/7."),
        ("Eat 4/9 of a pie, then 2/9 more. What fraction is eaten in total?", "4/9 + 2/9 = 6/9 (= 2/3)."),
        ("A ribbon is 7/10 m long; 3/10 m is cut off. How much is left?", "7/10 − 3/10 = 4/10 m (= 2/5 m)."),
        ("Add the unlike fractions 1/4 + 1/2 (change 1/2 to quarters first).", "2/4 + 1/4 = 3/4."),
    ]))
    A(practice("Analyze", [
        ("Without drawing, which is bigger: 2/3 or 2/5? Give the reason.",
         "2/3 — same numerator, and thirds are bigger pieces than fifths."),
        ("Meera adds 1/3 + 1/3 and writes 2/6. What did she do wrong?",
         "She added the bottoms too. Keep the bottom: 1/3 + 1/3 = 2/3, not 2/6."),
        ("Is 3/8 + 5/8 more than, less than, or equal to one whole?",
         "Equal to one whole — 3 + 5 = 8, so 8/8 = 1."),
        ("Two slices, 5/12 and 4/12 of a cake, go on one plate. Is that more or less than half the cake?",
         "5/12 + 4/12 = 9/12 = 3/4, which is more than half (1/2 = 6/12)."),
    ]))
    A(practice("Create", [
        ("Write two different fractions with denominator 6 that add up to exactly 1.",
         "Any pair of sixths that sum to 6/6, e.g. 2/6 + 4/6, or 1/6 + 5/6."),
        ("Make up a subtraction of like fractions whose answer is 1/2.",
         "Many answers, e.g. 3/4 − 1/4 = 2/4 = 1/2, or 5/8 − 1/8 = 4/8 = 1/2."),
        ("Invent a story where 1/5 + 2/5 of something is used and 2/5 is left.",
         "e.g. “A water bottle: I drink 1/5 in the morning and 2/5 at lunch (3/5 gone), so 2/5 is left.”"),
    ]))

    A(challenge(
        P("A chocolate bar has <b>12</b> equal squares. Aarav eats <b>1/4</b> of the bar and Bela eats "
          "<b>1/3</b> of the bar. What fraction of the bar is <em>left</em> — and how many squares is that?") +
        tryit("Hint: change 1/4 and 1/3 into twelfths so all the pieces match.",
              "1/4 = 3/12 and 1/3 = 4/12. Eaten = 3/12 + 4/12 = 7/12. Left = 12/12 − 7/12 = <b>5/12</b>. "
              "Since the bar has 12 squares, 5/12 means <b>5 squares</b> are left.")))

    A(kiwi("Nice — you kept the bottom and worked only with the tops, just as the rule says. You can compare, order, add and subtract fractions, handle mixed numbers, and even "
           "tackle unlike denominators by renaming them. Next we meet decimals — a slick new way to write those "
           "same fair shares. ✨"))

    chapter("Part 2 · Fair Shares", 6, "Comparing & Adding Fractions",
            "Fractions · Fair Shares", "".join(b))
