#!/usr/bin/env python3
"""Chapter 5 — Fractions, Parts of a Whole  (Fractions · Fair Shares)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, fraction_bar, fraction_circle, frac_on_line, number_line)


def build(chapter):
    b = []
    A = b.append

    A(big_q("One pizza, two hungry friends. You cut it down the middle and each take a piece. "
            "Nobody has a <b>whole</b> pizza any more… so what number tells us how much each friend got?"))
    A(kiwi("Hi again, it's <b>Kiwi</b>! Whole numbers like 1, 2, 3 are great for counting whole things — "
           "whole apples, whole cookies. But the moment we <em>share</em> something fairly, we need a new kind of "
           "number for the <em>pieces</em>. That number is a <b>fraction</b>, and it is one of the friendliest ideas "
           "in all of maths. Let's meet it."))

    A(H("What a fraction really means"))
    A(P("A <b>fraction</b> is a way to name <em>part of a whole</em> — as long as the whole is split into "
        "<b>equal</b> parts. That little word <b>equal</b> is the whole secret. If your pizza pieces are all "
        "different sizes, that's not a fraction, that's just an unfair fight!"))
    A(P("Here is one chocolate bar cut into <b>4 equal pieces</b>, and we have eaten <b>1</b> of them. "
        "The piece we ate is <b>one-quarter</b> of the bar — written <b>1/4</b>:"))
    A(figure(fraction_bar(4, 1), "1 piece eaten out of 4 equal pieces = 1/4 of the bar"))
    A(P("We can show the very same idea with a round pizza. Cut into 4 equal slices, one slice is again <b>1/4</b>:"))
    A(figure(fraction_circle(4, 1), "1 slice out of 4 equal slices = 1/4 of the pizza"))

    A(H("The two numbers in a fraction have names"))
    A(P("Every fraction is built from two numbers, one on top of the other, with a line between them:"))
    A(P("• The number <b>on top</b> is the <b>numerator</b>. It counts <em>how many parts we are talking about</em> "
        "(how many we took, ate, coloured…).<br>"
        "• The number <b>on the bottom</b> is the <b>denominator</b>. It tells us <em>how many equal parts the "
        "whole was cut into</em> altogether."))
    A(kiwi("A memory trick: <b>D</b>enominator is <b>D</b>own at the bottom, and it tells you the size of each "
           "piece. A bigger denominator means the whole was cut into <em>more</em> pieces, so each piece is "
           "<em>smaller</em>. That surprises a lot of people — 1/8 is smaller than 1/4!"))
    A(figure(fraction_bar(8, 3), "Numerator 3, denominator 8 → 3/8 (3 shaded pieces out of 8)"))
    A(P("In the bar above we shaded <b>3</b> pieces out of <b>8</b>, so the fraction is <b>3/8</b>. "
        "Numerator = 3 (the pieces we coloured), denominator = 8 (the pieces in the whole)."))

    A(example("naming a fraction from a picture", steps([
        "First count the total equal parts — that's the <b>denominator</b>.",
        "Then count the shaded (or chosen) parts — that's the <b>numerator</b>.",
        "Write numerator over denominator. For a bar with <b>5</b> equal parts and <b>2</b> shaded → <b>2/5</b>.",
        "Say it out loud: “two-fifths.” You read the top normally and the bottom like a position word.",
    ])))

    A(tryit("A birthday cake is cut into <b>6</b> equal slices and <b>5</b> slices are taken. "
            "What fraction of the cake is gone, and name its numerator and denominator.",
            "5 slices out of 6 → <b>5/6</b>. Numerator = <b>5</b> (slices taken), denominator = <b>6</b> "
            "(total equal slices)."))

    A(H("Special friends: halves, thirds and quarters"))
    A(P("A few fractions show up so often that they have everyday names. When the whole is split into "
        "<b>2</b> equal parts we call each one a <b>half</b> (1/2). Into <b>3</b> equal parts, each is a "
        "<b>third</b> (1/3). Into <b>4</b> equal parts, each is a <b>quarter</b> (1/4)."))
    A(figure(fraction_circle(2, 1), "Cut into 2 → each part is one half = 1/2"))
    A(figure(fraction_circle(3, 1), "Cut into 3 → each part is one third = 1/3"))
    A(P("And look what happens when we shade <em>all</em> the parts. If we shade all 3 thirds, we have "
        "<b>3/3</b> — which is the same as <b>1 whole</b>! Whenever the numerator equals the denominator, "
        "the fraction is exactly <b>1</b>."))
    A(figure(fraction_circle(3, 3), "All 3 thirds shaded = 3/3 = 1 whole pizza"))

    A(H("Fractions live on the number line too"))
    A(P("A fraction isn't only a picture of pizza — it is a real <em>number</em>, so it has its own home on the "
        "number line, sitting <em>between</em> the whole numbers. To place a fraction like <b>3/4</b>, take the "
        "space from 0 to 1, chop it into <b>4</b> equal jumps (the denominator), and hop along <b>3</b> of them "
        "(the numerator):"))
    A(figure(frac_on_line(4, 3), "The orange dot lands on 3/4 — three of four equal jumps from 0 to 1"))
    A(kiwi("See how 3/4 sits a little before 1? That makes sense — three-quarters is <em>almost</em> a whole, "
           "but not quite. The number line lets you <em>see</em> how big a fraction is."))
    A(tryit("On a number line from 0 to 1 split into <b>5</b> equal parts, which fraction does the "
            "<b>2nd</b> mark land on?",
            "Two jumps of one-fifth each → <b>2/5</b>."))

    A(H("Equivalent fractions — different names, same amount"))
    A(P("Here is something magical. Cut a chocolate bar in half and shade one half: that's <b>1/2</b>. Now imagine "
        "cutting <em>each</em> of those halves into two, so the bar has 4 pieces — and the shaded part is now "
        "<b>2</b> pieces out of <b>4</b>. Did the amount of chocolate change? Not one crumb! So <b>1/2 = 2/4</b>. "
        "Fractions that name the <em>same amount</em> are called <b>equivalent fractions</b>."))
    A(figure(fraction_bar(2, 1), "Half a bar shaded = 1/2"))
    A(figure(fraction_bar(4, 2), "Same amount, cut finer = 2/4. So 1/2 = 2/4"))
    A(figure(fraction_bar(8, 4), "Finer still = 4/8. So 1/2 = 2/4 = 4/8 — all the same amount!"))
    A(P("To <b>make</b> an equivalent fraction, multiply (or divide) <em>both</em> the numerator and the "
        "denominator by the <em>same</em> number. Multiplying 1/2 top and bottom by 3 gives 3/6 — still a half."))
    A(example("building equivalent fractions for 2/3", steps([
        "Start with <b>2/3</b>.",
        "Multiply top and bottom by 2: (2×2)/(3×2) = <b>4/6</b>.",
        "Multiply top and bottom by 3: (2×3)/(3×3) = <b>6/9</b>.",
        "So 2/3 = 4/6 = 6/9. They look different but they are all the same slice of pie. ✓",
    ])))
    A(tryit("Fill in the blank to make an equivalent fraction: 3/4 = ?/8.",
            "The bottom went from 4 to 8, that's ×2, so do the same on top: 3×2 = <b>6</b>. So 3/4 = <b>6/8</b>."))

    A(trap(
        P("A super-common slip is to <b>add the bottom numbers</b> when adding fractions. Someone writes "
          "<b>1/3 + 1/3 = 2/6</b>. That looks tidy — but it's wrong!") +
        P("<b>Why it happens:</b> we're so used to adding everything in sight that the two 3s get added too. "
          "But the denominator only tells you the <em>size</em> of each piece — it doesn't get bigger just "
          "because you have more pieces. Two thirds-pieces are still thirds-pieces.") +
        P("<b>The right way:</b> the pieces are the same size, so keep the bottom and add only the tops: "
          "<b>1/3 + 1/3 = 2/3</b>. Picture it — one third plus one third of a pizza is two thirds, which is "
          "<em>more</em> than one third. But 2/6 is smaller than 1/3, so adding the bottoms can't be right. "
          "(You'll practise this properly in the next chapter.)")))

    A(H("Three types of fractions"))
    A(P("Once a fraction can be any size, we sort them into three handy families by comparing the top to the "
        "bottom:"))
    A(P("• A <b>proper fraction</b> has a numerator <em>smaller</em> than its denominator, like 3/4 or 2/5. "
        "It is <em>less than one whole</em>.<br>"
        "• An <b>improper fraction</b> has a numerator <em>bigger than or equal to</em> its denominator, like "
        "5/4 or 7/3. It is <em>one whole or more</em>.<br>"
        "• A <b>mixed number</b> writes a whole number and a proper fraction side by side, like 1¼, meaning "
        "“one whole and one quarter.”"))
    A(P("Picture <b>5/4</b>: that's 5 quarter-pieces. Four of them rebuild one whole bar, and one quarter is "
        "left over. So <b>5/4 = 1¼</b>:"))
    A(figure(fraction_bar(4, 4), "First 4 quarters fill one whole bar = 4/4 = 1"))
    A(figure(fraction_bar(4, 1), "…and 1 more quarter left over. Altogether 5/4 = 1 whole + 1/4 = 1¼"))
    A(example("change the improper fraction 7/3 into a mixed number", steps([
        "Ask: how many whole groups of 3 thirds fit inside 7 thirds? 7 ÷ 3 = 2 remainder 1.",
        "The <b>2</b> is the number of wholes; the remainder <b>1</b> is the leftover thirds.",
        "So 7/3 = <b>2⅓</b> (two wholes and one third).",
        "Check the other way: 2 wholes = 6/3, plus 1/3 = 7/3. ✓",
    ])))
    A(tryit("What whole number does <b>4/4</b> equal, and how would you describe it?",
            "4/4 equals exactly <b>one whole</b>. Because its numerator is not less than its denominator, "
            "many books also call it an <b>improper fraction</b> — both descriptions are fine."))

    A(H("Now you try — climb the ladder"))
    A(P("Start easy and work upward. Try each one before you peek at the answer!"))

    A(practice("Remember", [
        ("In the fraction 3/7, which number is the <b>numerator</b>?", "The top number, 3."),
        ("In the fraction 3/7, which number is the <b>denominator</b>?", "The bottom number, 7."),
        ("What do we call one part when a whole is split into <b>4</b> equal pieces?",
         "A quarter (one-fourth), written 1/4."),
        ("Fill in: a fraction names a part of a whole only when the parts are all ____.", "Equal."),
        ("What fraction means the same as 1 whole when the denominator is 5?", "5/5."),
    ]))
    A(practice("Understand", [
        ("A pizza is cut into 8 equal slices and 3 are eaten. Write the fraction eaten.", "3/8."),
        ("Which is bigger, 1/3 or 1/6? Explain in one line.",
         "1/3 — cutting a whole into fewer pieces makes each piece bigger, so a third beats a sixth."),
        ("Write a fraction equivalent to 1/2 with denominator 10.",
         "Multiply top and bottom by 5: 5/10."),
        ("Is 9/5 a proper fraction, improper fraction, or mixed number?",
         "Improper (the top 9 is bigger than the bottom 5)."),
        ("On a number line from 0 to 1 in fourths, which fraction is at the 1st mark?", "1/4."),
    ]))
    A(practice("Apply", [
        ("Riya has 12 marbles and 7 are blue. What fraction of her marbles are blue?", "7/12."),
        ("Complete the equivalent fraction: 2/5 = ?/15.",
         "Bottom ×3 (5→15), so top ×3: 2×3 = 6. Answer 6/15."),
        ("Change the improper fraction 11/4 into a mixed number.",
         "11 ÷ 4 = 2 remainder 3, so 11/4 = 2¾."),
        ("Change the mixed number 3½ into an improper fraction.",
         "3 wholes = 6/2, plus 1/2 = 7/2."),
        ("Out of 10 birds, 4 flew away. What fraction stayed? Give an equivalent fraction too.",
         "6 stayed out of 10 → 6/10, which is the same as 3/5."),
    ]))
    A(practice("Analyze", [
        ("Are 3/4 and 6/8 the same amount? Show why.",
         "Yes — multiply 3/4 top and bottom by 2 to get 6/8, so they are equivalent (the same amount)."),
        ("Sort these into proper / improper: 2/3, 5/5, 8/3, 1/9, 7/2.",
         "Proper: 2/3, 1/9 (top < bottom). Improper: 5/5, 8/3, 7/2 (top ≥ bottom)."),
        ("Anil says “1/5 is bigger than 1/2 because 5 is bigger than 2.” Is he right?",
         "No. A bigger denominator means smaller pieces, so 1/5 is actually smaller than 1/2."),
        ("Which is closer to a whole pizza, 7/8 or 3/8? Why?",
         "7/8 — it has 7 of the 8 pieces, so only 1 piece is missing, while 3/8 is missing 5 pieces."),
    ]))
    A(practice("Create", [
        ("Draw (in words) and name a fraction that equals exactly one half, but uses the denominator 8.",
         "Shade 4 pieces of an 8-piece bar → 4/8, which equals 1/2."),
        ("Invent a real-life sharing story whose answer is the fraction 2/3.",
         "Many answers! e.g. “3 friends share a sandwich into 3 equal parts and 2 friends each eat their "
         "part” → 2/3 of the sandwich is eaten."),
        ("Write three different fractions that all equal 1 whole.",
         "Any with equal top and bottom, e.g. 2/2, 5/5, 9/9."),
    ]))

    A(challenge(
        P("In the word <b>BANANA</b>, what fraction of the letters are the letter <b>A</b>? Write your answer as "
          "a fraction, then as the <em>simplest</em> equivalent fraction you can.") +
        tryit("Count carefully, then simplify.",
              "BANANA has <b>6</b> letters and <b>3</b> of them are A, so 3/6. Dividing top and bottom by 3 "
              "gives the simplest form <b>1/2</b> — exactly half the letters are A!")))

    A(kiwi("That's solid work with equal parts. You can now read fractions, name the numerator and denominator, place them on a number "
           "line, spot equivalent fractions, and tell proper from improper from mixed. Next chapter we'll "
           "<b>compare, order, add and subtract</b> fractions — sharing maths gets even more fun. 🍕"))

    chapter("Part 2 · Fair Shares", 5, "Fractions — Parts of a Whole",
            "Fractions · Fair Shares", "".join(b))
