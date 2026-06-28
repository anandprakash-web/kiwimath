#!/usr/bin/env python3
"""L3 Chapter 6 — Percentages, the % Idea (Algebra · Parts & Wholes). Brand-new
this level, scaffolded gently from Ch5: percent = 'out of 100' (decimal_grid
everywhere), percent<->fraction<->decimal, % of a quantity, what % one number is
of another, simple percentage increase/decrease, with sale-tag/battery/score
surprises."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, decimal_grid, fraction_bar, bar_chart, compare)


def build(chapter):
    b = []; A = b.append

    A(big_q("Two video games are on sale. One shouts <b>“40% OFF!”</b> and costs ₹500 before the cut. The "
            "other says <b>“SAVE ₹150”</b> and costs ₹400 before the cut. Which sale actually saves you more "
            "money? The bigger-looking number isn't always the better deal — and percentages are how you "
            "see through the trick."))
    A(kiwi("Hi explorer! \U0001F95D You already know fractions and decimals are two outfits for the same "
           "parts-of-a-whole idea. Get ready for the <b>third outfit</b>: the <b>percent</b>. It's the one you'll "
           "meet most in real life — sale tags, battery icons, test scores, phone storage, exam results — and "
           "it's secretly the friendliest of all, because it always uses the same whole: <b>100</b>."))

    A(H("Percent just means “out of 100”"))
    A(P("The word <b>per-cent</b> literally means <em>“per hundred”</em> — out of 100. The little sign "
        "<b>%</b> is just a fancy way of writing “/100”. So <b>37%</b> means <b>37 out of 100</b>, the fraction "
        "<b>37/100</b>, the decimal <b>0.37</b>. Same amount, three outfits."))
    A(figure(decimal_grid(37), "37 of the 100 little squares shaded = 37% = 37/100 = 0.37"))
    A(kiwi("This is why percent is so handy: imagine <em>every</em> whole is cut into 100 equal squares, always. "
           "Then a percent is simply “how many squares.” 50% is half the grid, 25% is a quarter, 100% is the "
           "<em>whole</em> grid, and — surprise — you can even go past 100% when you have <em>more</em> than one "
           "whole!"))
    A(figure(decimal_grid(100), "100% = all 100 squares = one whole"))
    A(P("Some you'll just <em>know</em> on sight, like old friends:"))
    A(figure(decimal_grid(50), "50% = 50/100 = 1/2 = 0.5 — half the grid"))
    A(figure(decimal_grid(25), "25% = 25/100 = 1/4 = 0.25 — a quarter of the grid"))
    A(tryit("Shade-in your head: how many squares is <b>10%</b>, and what fraction is that?",
            "10% = <b>10 of 100</b> squares = 10/100 = <b>1/10</b>. (And as a decimal, 0.1.)"))

    A(H("The three outfits: percent ↔ fraction ↔ decimal"))
    A(P("Crossing between the three is fast once you remember <b>% means /100</b>:"))
    A(P("• <b>Percent → fraction:</b> put it over 100 and simplify. 40% = 40/100 = <b>2/5</b>.<br>"
        "• <b>Percent → decimal:</b> divide by 100 — shift the dot <em>two places left</em>. 37% = <b>0.37</b>, "
        "and 8% = <b>0.08</b>.<br>"
        "• <b>Decimal → percent:</b> multiply by 100 — shift the dot <em>two places right</em>. 0.6 = <b>60%</b>.<br>"
        "• <b>Fraction → percent:</b> first make it a decimal (divide top by bottom), then ×100. 3/4 = 0.75 = "
        "<b>75%</b>."))
    A(example("turn 2/5 into a percent", steps([
        "Make it a decimal: 2 ÷ 5 = 0.4.",
        "Multiply by 100 (shift dot two right): 0.4 → <b>40%</b>.",
        "Check with the grid idea: 2/5 of 100 squares = 40 squares = 40%. ✓",
    ])))
    A(figure(fraction_bar(5, 2), "2/5 of a whole is the same shaded amount as 40% of it"))
    A(example("turn 12% into a fraction and a decimal", steps([
        "Fraction: 12/100. Both divide by 4 → <b>3/25</b>.",
        "Decimal: 12 ÷ 100 = <b>0.12</b>.",
        "So 12% = 3/25 = 0.12 — one amount, three names. ✓",
    ])))
    A(figure(decimal_grid(12), "12% = 12 of 100 squares = 12/100 = 3/25 = 0.12 — the same shaded amount"))
    A(kiwi("Watch the surprise hiding in <b>1/8</b>. As a decimal it's 0.125, so as a percent it's "
           "<b>12.5%</b> — percentages are allowed to have a decimal point! And <b>1/3</b> becomes the "
           "never-ending 33.33…%, often written as <b>33⅓%</b>. Percent doesn't have to be a whole number."))
    A(tryit("Write <b>0.09</b> as a percent, and <b>75%</b> as a fraction in simplest form.",
            "0.09 × 100 = <b>9%</b>. And 75% = 75/100 = <b>3/4</b>."))

    A(H("Finding a percent OF a quantity"))
    A(P("Here's the move you'll use most: finding a percent <em>of</em> something — “20% of 50 marbles,” "
        "“15% of ₹200.” Remember from Ch5 that <b>“of” means multiply</b>. So <b>20% of 50</b> = 20/100 × 50. "
        "Two friendly ways to do it:"))
    A(P("• <b>Fraction way:</b> turn the percent into a fraction, then take that fraction of the number. "
        "20% = 1/5, and 1/5 of 50 = 50 ÷ 5 = <b>10</b>.<br>"
        "• <b>Decimal way:</b> turn the percent into a decimal and multiply. 0.20 × 50 = <b>10</b>."))
    A(example("find 15% of ₹200", steps([
        "Decimal way: 15% = 0.15. Then 0.15 × 200 = <b>₹30</b>.",
        "Or the 10%+5% trick: 10% of 200 = 20, and 5% is half of that = 10. Add: 20 + 10 = <b>₹30</b>. ✓",
        "So 15% of ₹200 is ₹30. (And the remaining 85% would be ₹170.)",
    ])))
    A(kiwi("The secret weapon for mental percentages: <b>10% is just “move the dot one place left.”</b> 10% of "
           "350 = 35. Need 5%? Halve the 10%. Need 20%? Double it. Need 30%? Triple it. Almost any everyday "
           "percentage is a few 10%-jumps stacked together — no calculator required."))
    A(figure(bar_chart([("10%", 35), ("20%", 70), ("30%", 105)]),
             "Building percents of 350 by stacking 10%-blocks of 35"))
    A(example("find 8% of 250", steps([
        "Decimal way: 8% = 0.08. Then 0.08 × 250 = <b>20</b>.",
        "Check with 10% − 2%: 10% of 250 = 25; 1% = 2.5, so 2% = 5; 25 − 5 = <b>20</b>. ✓",
    ])))
    A(tryit("A test has 80 marks. You scored 75%. How many marks is that?",
            "75% of 80 = 0.75 × 80 = <b>60 marks</b>. (Or 3/4 of 80 = 60.)"))

    A(trap(P("A trap to dodge: writing <b>“20% of 50 = 20”</b>. The 20 is the <em>percent</em>, not the "
             "answer — you still have to take that share <em>of</em> 50. <b>The right way:</b> “of” means "
             "multiply, so 20% of 50 = 20/100 × 50 = <b>10</b>. (Quick check: 20% is one-fifth, and "
             "one-fifth of 50 is 50 ÷ 5 = 10. ✓) A percent on its own is just a label until you say "
             "<em>percent of what</em>.")))

    A(H("Finding what percent one number is of another"))
    A(P("Sometimes you have the part and the whole, and you want the percentage — “I got 15 out of 60, what "
        "percent is that?” The recipe: <b>part ÷ whole, then × 100</b>. (It's just the part-over-whole "
        "fraction, dressed as a percent.)"))
    A(example("15 out of 60 is what percent?", steps([
        "Make the fraction: part over whole = 15/60.",
        "Simplify if you like: 15/60 = 1/4.",
        "Turn into a percent: 1/4 = 0.25 = <b>25%</b>. (Or straight: 15 ÷ 60 × 100 = 25.) ✓",
    ])))
    A(figure(decimal_grid(25), "15 out of 60 fills the same share as 25 out of 100 → 25%"))
    A(example("a phone is charged from empty to 18 of 24 battery-bars. What % is the battery?", steps([
        "Part over whole: 18/24.",
        "Simplify: 18/24 = 3/4.",
        "As a percent: 3/4 = 75%. The battery icon would read <b>75%</b>. \U0001F50B",
    ])))
    A(tryit("In a class of 20, twelve pupils wear glasses. What percent wear glasses?",
            "12 ÷ 20 × 100 = <b>60%</b>. (12/20 = 3/5 = 0.6 = 60%.)"))

    A(H("Percentage increase &amp; decrease"))
    A(P("Prices rise, prices fall, populations grow, scores improve. To change a number by a percent, "
        "<b>find that percent of it, then add</b> (for an increase) <b>or subtract</b> (for a decrease)."))
    A(example("a ₹200 book goes up by 15%. New price?", steps([
        "Find 15% of 200: 0.15 × 200 = ₹30 (the increase).",
        "Add it on: 200 + 30 = <b>₹230</b>.",
        "Shortcut: an increase of 15% means you pay 115% of the old price → 1.15 × 200 = ₹230. ✓",
    ])))
    A(figure(bar_chart([("old ₹200", 200), ("new ₹230", 230)]),
             "A 15% rise lifts the ₹200 book by ₹30 to ₹230"))
    A(example("an ₹80 toy is 25% off. Sale price?", steps([
        "Find 25% of 80: 1/4 of 80 = ₹20 (the discount).",
        "Take it away: 80 − 20 = <b>₹60</b>.",
        "Shortcut: 25% off means you pay 75% → 0.75 × 80 = ₹60. ✓",
    ])))
    A(figure(compare(80, 60), "₹80 marked price drops to ₹60 after a 25% reduction"))
    A(kiwi("A famous percentage <b>trap</b> to enjoy: a price goes up 10%, then down 10%. Back to the start? "
           "<em>No!</em> Start at 100 → up 10% → 110 → down 10% of 110 (that's 11) → <b>99</b>. You end up "
           "lower! The reason: the second 10% is taken from a <em>bigger</em> number than the first. Percentages "
           "always ask “percent of <em>what</em>?” — and the 'what' can change underneath you. \U0001F62E"))
    A(tryit("A water tank holds 150 litres but is 10% empty. How many litres are in it?",
            "10% of 150 = 15 litres missing, so 150 − 15 = <b>135 litres</b> are in the tank."))

    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What does the symbol % mean?", "“Out of 100” (per hundred) — the same as dividing by 100."),
        ("Write 50% as a fraction.", "50/100 = 1/2."),
        ("Write 25% as a decimal.", "0.25."),
        ("How many squares of a 100-grid is 9%?", "9 squares."),
        ("What percent is the whole grid?", "100%."),
    ]))
    A(practice("Understand", [
        ("Turn 3/4 into a percent.", "3 ÷ 4 = 0.75 → 75%."),
        ("Turn 0.6 into a percent.", "0.6 × 100 = 60%."),
        ("Turn 40% into a fraction in simplest form.", "40/100 = 2/5."),
        ("Turn 1/8 into a percent.", "1 ÷ 8 = 0.125 → 12.5%."),
        ("Turn 8% into a decimal.", "8 ÷ 100 = 0.08."),
    ]))
    A(practice("Apply", [
        ("Find 20% of 50.", "0.20 × 50 = 10."),
        ("Find 15% of 200.", "0.15 × 200 = 30."),
        ("Find 75% of 80.", "3/4 of 80 = 60."),
        ("12 out of 50 is what percent?", "12 ÷ 50 × 100 = 24%."),
        ("A ₹250 shirt rises 8%. New price?", "8% of 250 = 20, so 250 + 20 = ₹270."),
    ]))
    A(practice("Analyze", [
        ("Which is more: 30% of 90, or 25% of 120? Show your working.",
         "30% of 90 = 27; 25% of 120 = 30. So 25% of 120 is more, by 3."),
        ("You scored 18 out of 24 on one test and 21 out of 30 on another. Which percentage is higher?",
         "18/24 = 75%; 21/30 = 70%. The first test (75%) is higher."),
        ("A ₹500 bag is 20% off, then ₹40 is taken off the sale price. What do you pay?",
         "20% of 500 = 100, so sale price is ₹400; minus ₹40 = ₹360."),
        ("A price goes up 20% then down 20%. Is it back to the start? Explain.",
         "No. Start 100 → up to 120 → down 20% of 120 (=24) → 96. The second 20% is of a bigger number, so you end lower."),
    ]))
    A(practice("Create", [
        ("Invent a sale tag (marked price + % off) where the customer ends up paying exactly ₹150.",
         "Many answers — e.g. ‘₹200, 25% off’ (25% of 200 = 50, pay 150) or ‘₹300, 50% off’."),
        ("Write a battery story: a phone’s bars and a percentage that match. Use a fraction that simplifies.",
         "E.g. ‘9 of 12 bars lit’ → 9/12 = 3/4 = 75% charged."),
        ("Make a question whose answer is 12.5% and explain why a fraction is needed.",
         "E.g. ‘1 slice of an 8-slice pizza is what percent?’ → 1/8 = 0.125 = 12.5%; eighths don’t land on a whole percent."),
    ]))

    A(challenge(
        P("Back to the BIG QUESTION! Game A: <b>₹500, 40% off</b>. Game B: <b>₹400, save ₹150</b>. "
          "Work out the actual rupees saved on each — <em>and</em> the percent saved on each — then say which "
          "sale is the better deal and why.") +
        tryit("Find both the money AND the percent for each.",
              "Game A saves 40% of 500 = <b>₹200</b> (that's the full 40%). Game B saves <b>₹150</b>, which is "
              "150 ÷ 400 × 100 = <b>37.5%</b>. So Game A saves more <em>money</em> (₹200 vs ₹150) <em>and</em> a "
              "bigger <em>percent</em> (40% vs 37.5%). The loud “SAVE ₹150” tag looked tempting, but the "
              "percentage reveals Game A is the better deal. That's the power of percent — it lets you compare "
              "two different prices fairly. \U0001F4B0")))

    A(kiwi("Superb! You now read percent as ‘out of 100’, swap freely between percent, fraction and decimal, "
           "find a percent of a quantity, work out what percent one number is of another, and grow or shrink a "
           "number by a percent. Next we put all of this to work where it matters most — <b>real money</b>: "
           "buying, selling, profit, loss and discounts. \U0001F6D2"))

    chapter("Part 2 · Parts & Wholes", 6, "Percentages — the % Idea",
            "Algebra · Parts & Wholes", "".join(b))
