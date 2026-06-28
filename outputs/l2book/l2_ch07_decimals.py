#!/usr/bin/env python3
"""Chapter 7 — Decimals, Another Way to Share  (Arithmetic · Decimals)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, decimal_grid, fraction_bar, number_line, compare)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Look at a price tag: <b>₹7.50</b>. There's a tiny dot in the middle of that number. "
            "What is that dot doing there, and what do the digits after it really mean?"))
    A(kiwi("Hello, <b>Kiwi</b> again! That little dot is called a <b>decimal point</b>, and the digits after it "
           "are a brand-new way of writing fractions — one that's perfect for money, measuring, and lining numbers "
           "up neatly. Decimals and fractions are secretly the same idea wearing different clothes. Let's unwrap it!"))

    A(H("Tenths: splitting one whole into 10"))
    A(P("Last chapter we cut wholes into equal parts. A <b>decimal</b> just always cuts into <b>10</b>, or "
        "<b>100</b>, or <b>1000</b> — powers of ten. Split one whole into <b>10</b> equal strips and shade "
        "<b>3</b> of them. As a fraction that's <b>3/10</b>; as a decimal we write <b>0.3</b> and say "
        "“three-tenths.”"))
    A(figure(fraction_bar(10, 3), "3 of 10 equal strips shaded = 3/10 = 0.3"))
    A(P("The dot separates the <b>whole part</b> (on the left) from the <b>fraction part</b> (on the right). "
        "In <b>0.3</b>, the 0 means zero wholes, and the 3 means three-tenths. The very first place after the "
        "dot is always the <b>tenths</b> place."))

    A(H("Hundredths: splitting into 100"))
    A(P("Cut a whole into a <b>10 × 10</b> grid and you get <b>100</b> tiny squares. Each little square is one "
        "<b>hundredth</b> = 1/100 = <b>0.01</b>. Here are <b>35</b> squares shaded — that's <b>35/100</b>, written "
        "<b>0.35</b>:"))
    A(figure(decimal_grid(35), "35 of 100 little squares shaded = 35/100 = 0.35"))
    A(P("The <b>second</b> place after the dot is the <b>hundredths</b> place. So in <b>0.35</b>, the 3 is "
        "3 tenths and the 5 is 5 hundredths. Notice the grid: 35 little squares is the same as 3 full columns "
        "(3 tenths) plus 5 extra squares (5 hundredths). Same picture, two ways to read it."))
    A(figure(decimal_grid(50), "50 squares shaded = 50/100 = 0.50, which is exactly half the grid (also 0.5)"))
    A(kiwi("Big idea: <b>0.5 and 0.50 are the same number.</b> Five tenths is the same amount as fifty hundredths — "
           "the grid shows it's half either way. Extra zeros on the <em>right</em> of a decimal don't change its value."))

    A(H("Decimal place value"))
    A(P("Just like big numbers, decimals have a place-value chart — it simply keeps going to the <em>right</em> "
        "of the dot, with each place worth <b>ten times less</b> than the one before:"))
    A(P("Ones &nbsp;·&nbsp; <b>tenths</b> (1/10) &nbsp; <b>hundredths</b> (1/100) &nbsp; <b>thousandths</b> "
        "(1/1000). So the number <b>4.27</b> means <b>4 ones + 2 tenths + 7 hundredths</b>, the same as "
        "4 + 2/10 + 7/100."))
    A(example("read the value of each digit in 4.27", steps([
        "The <b>4</b> is left of the dot → 4 ones = 4.",
        "The <b>2</b> is in the first place after the dot → 2 tenths = 2/10 = 0.2.",
        "The <b>7</b> is in the second place after the dot → 7 hundredths = 7/100 = 0.07.",
        "Add them up: 4 + 0.2 + 0.07 = <b>4.27</b>. ✓",
    ])))
    A(tryit("In the number <b>6.8</b>, what does the 8 stand for — 8 ones, 8 tenths, or 8 hundredths?",
            "The 8 is in the first place after the dot, so it is <b>8 tenths</b> (0.8)."))

    A(H("Reading decimals out loud"))
    A(P("To read a decimal, say the whole part, say “point,” then read the digits after the dot one by one. "
        "<b>12.5</b> is “twelve point five.” <b>3.09</b> is “three point zero nine.” The “point” keeps the "
        "tenths and hundredths from sneaking into the whole part."))
    A(tryit("How do you read <b>0.07</b> out loud, and what fraction is it?",
            "“Zero point zero seven.” It is 7 hundredths = <b>7/100</b>."))

    A(H("Fractions and decimals are partners"))
    A(P("Some fractions turn into especially friendly decimals — worth memorising, because they pop up "
        "everywhere (especially with money):"))
    A(P("• <b>1/2 = 0.5</b> &nbsp;(half a whole — five tenths)<br>"
        "• <b>1/4 = 0.25</b> &nbsp;(a quarter — twenty-five hundredths)<br>"
        "• <b>3/4 = 0.75</b> &nbsp;(three quarters)<br>"
        "• <b>1/10 = 0.1</b> &nbsp;and&nbsp; <b>1/100 = 0.01</b>"))
    A(figure(fraction_bar(4, 1), "1/4 of a bar… is the same shaded amount as 0.25 of it"))
    A(figure(decimal_grid(25), "…and here is 0.25 as 25 of 100 squares. 1/4 = 0.25, the same amount."))
    A(P("To turn a fraction with denominator 10 or 100 into a decimal, just place the numerator in the right "
        "place after the dot: 7/10 = 0.7, and 7/100 = 0.07. To go back, count the decimal places — two places "
        "means hundredths, so 0.45 = 45/100."))
    A(example("write 1/2 as a decimal two ways", steps([
        "Way 1 — make the bottom 10: 1/2 = 5/10 (multiply top and bottom by 5) → <b>0.5</b>.",
        "Way 2 — make the bottom 100: 1/2 = 50/100 → <b>0.50</b>, which is the same as 0.5.",
        "Both give half a whole. ✓",
    ])))
    A(tryit("Write <b>3/10</b> as a decimal, and write <b>0.9</b> as a fraction.",
            "3/10 = <b>0.3</b>. And 0.9 has one decimal place (tenths), so 0.9 = <b>9/10</b>."))

    A(H("Comparing and ordering decimals"))
    A(P("To compare decimals, line them up by their dots and compare place by place, starting from the "
        "<em>left</em> (the biggest places). Compare <b>0.6</b> and <b>0.06</b>: the tenths digit is 6 versus 0, "
        "and 6 tenths beats 0 tenths, so <b>0.6 &gt; 0.06</b>."))
    A(figure(compare(0.6, 0.06), "0.6 is greater than 0.06 — six tenths beats six hundredths"))
    A(P("The grids prove it. Sixty little squares versus six little squares — 0.6 fills far more of the whole:"))
    A(figure(decimal_grid(60), "0.6 = 60 of 100 squares (six whole columns)"))
    A(figure(decimal_grid(6), "0.06 = just 6 of 100 squares — much less"))
    A(kiwi("Handy trick: give the decimals the <em>same number of places</em> by adding zeros on the right "
           "(remember, that doesn't change the value). Then 0.6 becomes 0.60 and you can compare 60 vs 06 like "
           "whole numbers. 60 &gt; 6, so 0.6 &gt; 0.06."))
    A(example("put 9.2, 26.8, 26.7 and 32.1 in ascending order", steps([
        "Compare the whole parts first: 9, 26, 26, 32.",
        "9 is smallest; 32 is biggest. The two 26s tie, so look at their tenths: 26.7 vs 26.8 → 7 &lt; 8.",
        "Ascending order: <b>9.2 &lt; 26.7 &lt; 26.8 &lt; 32.1</b>. ✓",
    ])))
    A(tryit("Which is larger, <b>0.45</b> or <b>0.5</b>?",
            "Make the places match: 0.5 = 0.50. Now compare 45 vs 50 → 50 is bigger, so <b>0.5 &gt; 0.45</b>."))

    A(H("Adding and subtracting decimals"))
    A(P("Adding decimals is just like adding whole numbers, with one golden rule: <b>line up the decimal "
        "points</b> so tenths sit under tenths and hundredths under hundredths. Then add, and bring the dot "
        "straight down."))
    A(example("add 2.30 + 1.45", steps([
        "Stack them with dots lined up: 2.30 and 1.45.",
        "Add hundredths: 0 + 5 = 5. Add tenths: 3 + 4 = 7. Add ones: 2 + 1 = 3.",
        "Bring the dot straight down: <b>3.75</b>.",
    ])))
    A(P("Subtraction works the same way — line up the dots and subtract. If one number is shorter, fill the "
        "gap with zeros so both have the same number of places."))
    A(example("subtract 5.6 − 2.45", steps([
        "Line up the dots and pad 5.6 to <b>5.60</b> so both have two places.",
        "Hundredths: 0 − 5 needs borrowing → borrow to get 10 − 5 = 5; tenths becomes 5.",
        "Tenths: 5 − 4 = 1. Ones: 5 − 2 = 3.",
        "Answer: <b>3.15</b>.",
    ])))
    A(tryit("Work out <b>3.4 + 0.25</b> by lining up the dots.",
            "Pad to 3.40 + 0.25. Hundredths 0+5=5, tenths 4+2=6, ones 3+0=3 → <b>3.65</b>."))

    A(trap(
        P("The number-one decimal mistake is <b>not lining up the decimal points</b>. When one number has "
          "fewer places, people stack the numbers flush on the <em>right</em> (last digit under last digit) "
          "instead of lining up the dots. Adding <b>2.5 + 0.35</b> that way:") +
        P("&nbsp;&nbsp;&nbsp;&nbsp;<code>&nbsp;2.5_</code> &nbsp;←&nbsp; the “5” (which is 5 <em>tenths</em>) "
          "slides into the wrong column<br>"
          "&nbsp;&nbsp;&nbsp;&nbsp;<code>+0.35</code><br>"
          "…and out pops something like <b>0.60</b> — clearly wrong, since 2.5 alone is already bigger than that!") +
        P("<b>Why it happens:</b> with whole numbers we line up the right-hand ends, so the hand does it "
          "automatically — but decimals must be lined up by <b>place value</b>, not by their ends.") +
        P("<b>The right way:</b> line up the dots and <b>pad with zeros</b> so both have the same number of "
          "places: 2.5 becomes <b>2.50</b>. Then 2.50 + 0.35 = <b>2.85</b>. Tip: writing the dots in a neat "
          "vertical line — and padding the short one — stops this error every time.")))

    A(H("Money is decimals in disguise"))
    A(P("Money is the most common place you'll meet decimals. In rupees, the digits after the dot are "
        "<b>paise</b>: <b>₹7.50</b> means 7 rupees and 50 paise, because 100 paise make 1 rupee (so paise are "
        "hundredths of a rupee). Adding money is just adding decimals — line up the dots!"))
    A(example("a shopping bill: ₹12.50 + ₹3.75", steps([
        "Line up the dots: 12.50 and 3.75.",
        "Paise (hundredths): 0 + 5 = 5. Tenths: 5 + 7 = 12, write 2 carry 1. Ones: 2 + 3 + 1(carry) = 6. Tens: 1.",
        "Total = <b>₹16.25</b> — sixteen rupees and twenty-five paise.",
    ])))
    A(tryit("You pay with ₹20.00 for a snack that costs <b>₹13.50</b>. How much change do you get?",
            "20.00 − 13.50 = <b>₹6.50</b> (six rupees fifty paise)."))

    A(H("Now you try — climb the ladder"))
    A(P("Take it one rung at a time. Try before you check!"))

    A(practice("Remember", [
        ("What is the name of the dot in 3.5?", "The decimal point."),
        ("What is the first place to the right of the decimal point called?", "The tenths place."),
        ("Write three-tenths as a decimal.", "0.3."),
        ("True or false: 0.7 and 0.70 are the same value.", "True (extra zeros on the right don't change it)."),
        ("What is 1/2 as a decimal?", "0.5."),
    ]))
    A(practice("Understand", [
        ("Write 0.25 as a fraction.", "25/100 (which is 1/4)."),
        ("In 8.46, what does the 4 stand for?", "4 tenths (0.4)."),
        ("Read 5.09 out loud (in words).", "“Five point zero nine.”"),
        ("Write 9/100 as a decimal.", "0.09."),
        ("Which is bigger, 0.3 or 0.30?", "They are equal."),
    ]))
    A(practice("Apply", [
        ("Add: 1.5 + 2.3.", "3.8."),
        ("Subtract: 4.75 − 1.25.", "3.50 (= 3.5)."),
        ("A pencil costs ₹6.50 and an eraser ₹3.50. What is the total?", "₹10.00."),
        ("Write 3/4 as a decimal.", "0.75."),
        ("A ribbon 2.40 m long is joined to one 1.35 m long. What is the total length?", "2.40 + 1.35 = 3.75 m."),
    ]))
    A(practice("Analyze", [
        ("Put in ascending order: 0.5, 0.05, 0.55, 0.15.",
         "0.05 < 0.15 < 0.5 < 0.55 (pad to two places: 05, 15, 50, 55)."),
        ("Ravi says 0.4 is less than 0.40. Is he right?",
         "No — they are equal; 0.40 just has an extra zero that adds nothing."),
        ("Which is larger and by how much: 0.7 or 0.65?",
         "0.7 is larger. 0.70 − 0.65 = 0.05, so it is larger by 0.05."),
        ("A ribbon 5.36 m is joined to one 3.69 m, then 2.72 m is used for a gift. How much ribbon is left?",
         "5.36 + 3.69 = 9.05, then 9.05 − 2.72 = 6.33 m left."),
    ]))
    A(practice("Create", [
        ("Write a decimal between 0.3 and 0.4.",
         "Many answers, e.g. 0.35 (it sits halfway between 0.3 and 0.4)."),
        ("Make up a shopping problem whose two prices add to exactly ₹10.00.",
         "Many answers, e.g. a ₹6.25 juice and a ₹3.75 biscuit pack → ₹10.00."),
        ("Write the same amount, one-half, in three forms: a fraction, a tenths-decimal, and a hundredths-decimal.",
         "1/2, 0.5, and 0.50 — all the same amount."),
    ]))

    A(challenge(
        P("Add these four decimals carefully by lining up the dots: "
          "<b>0.123 + 12.3 + 0.0123 + 1.23</b>. (Tip: pad them all to the same number of decimal places first.)") +
        tryit("Pad every number to <b>four</b> decimal places, then add column by column.",
              "Pad them all to four places (because 0.0123 already has four): 0.1230, 12.3000, "
              "0.0123, 1.2300. Add the ten-thousandths, thousandths, hundredths and on up: "
              "<b>13.6653</b>.")))

    A(kiwi("Nicely done — lining up those decimal points is exactly what keeps the place values straight. You now read and write decimals, see how they match fractions, compare and order them, "
           "and add and subtract them — even real money. Next chapter we turn into Conversion Masters: metres to "
           "centimetres, kilograms to grams, hours to minutes, and more. 📏"))

    chapter("Part 2 · Fair Shares", 7, "Decimals — Another Way to Share",
            "Arithmetic · Decimals", "".join(b))
