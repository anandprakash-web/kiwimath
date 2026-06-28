#!/usr/bin/env python3
"""Chapter 8 — Useful Conversions  (Arithmetic · Useful Conversions)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, number_line, clock, bar_chart, compare)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Your friend is <b>1 metre 40 centimetres</b> tall. You are <b>135 centimetres</b> tall. "
            "Who is taller? The numbers 1, 40 and 135 don't line up at all… so how do we even compare them?"))
    A(kiwi("Hi, <b>Kiwi</b> here! The trick is to put both heights into the <em>same unit</em> first. "
           "Once they're both in centimetres (or both in metres), comparing is easy. Learning to "
           "<b>convert</b> between units — and to add, subtract and compare measurements — is a real-life "
           "superpower. Let's collect it!"))

    A(H("Why we need conversions"))
    A(P("We measure the world with <b>units</b>: <em>length</em> in kilometres, metres and centimetres; "
        "<em>mass</em> (how heavy) in kilograms and grams; <em>capacity</em> (how much liquid) in litres and "
        "millilitres; <em>time</em> in hours and minutes; and <em>money</em> in rupees and paise. "
        "The same amount can be written in a big unit or a small unit, and a <b>conversion</b> swaps between them."))
    A(P("Here are the friendships you'll use most. Each big unit is worth a fixed number of small units:"))
    A(P("• <b>Length:</b> 1 km = 1000 m &nbsp;·&nbsp; 1 m = 100 cm &nbsp;·&nbsp; 1 cm = 10 mm<br>"
        "• <b>Mass:</b> 1 kg = 1000 g<br>"
        "• <b>Capacity:</b> 1 L = 1000 mL<br>"
        "• <b>Time:</b> 1 hour = 60 minutes &nbsp;·&nbsp; 1 minute = 60 seconds &nbsp;·&nbsp; 1 day = 24 hours<br>"
        "• <b>Money:</b> 1 rupee = 100 paise"))

    A(H("The two golden moves: big→small and small→big"))
    A(P("Every conversion is one of two moves, and it helps to picture a number line. Going from a <b>big</b> "
        "unit to a <b>small</b> unit, you'll need <em>more</em> of the small ones, so you <b>multiply</b>. "
        "Going from a <b>small</b> unit to a <b>big</b> unit, you bundle them up, so you <b>divide</b>."))
    A(figure(number_line(0, 5, 1, points=[(3, "3 m", "#FF6F00")]),
             "3 m sits at 3 on the metre line. To get centimetres, multiply by 100 → 300 cm"))
    A(kiwi("A memory hook: <b>B</b>ig to small, you get <b>m</b>ore (multiply). Small to big, fewer (divide). "
           "If your answer has way too few of the small units, you probably multiplied the wrong way!"))
    A(example("convert 3 m into centimetres", steps([
        "Metre is the big unit, centimetre is the small unit → we'll get more, so <b>multiply</b>.",
        "1 m = 100 cm, so 3 m = 3 × 100 = <b>300 cm</b>.",
        "Check: 300 cm is a lot more than 3 — that's right, centimetres are small. ✓",
    ])))
    A(figure(number_line(0, 5, 1, points=[(2, "2 kg", "#39A85B")]),
             "2000 g bundles back to 2 on the kilogram line — small to big, so divide by 1000"))
    A(example("convert 2500 g into kilograms", steps([
        "Gram is the small unit, kilogram is the big unit → we'll get fewer, so <b>divide</b>.",
        "1000 g = 1 kg, so 2500 ÷ 1000 = <b>2.5 kg</b> (two and a half kilograms).",
        "Check: 2.5 is much smaller than 2500 — correct, kilograms are big. ✓",
    ])))
    A(tryit("Convert <b>4 km</b> into metres.",
            "Big to small, so multiply: 4 × 1000 = <b>4000 m</b>."))
    A(tryit("Convert <b>3000 mL</b> into litres.",
            "Small to big, so divide: 3000 ÷ 1000 = <b>3 L</b>."))

    A(H("Mixed units: like 1 m 40 cm"))
    A(P("Often a measurement comes in <em>two</em> units at once, like <b>1 m 40 cm</b> or <b>2 kg 250 g</b>. "
        "To work with it, change the big part into the small unit and add. <b>1 m 40 cm</b> = (1 × 100) + 40 = "
        "<b>140 cm</b>. Now we can finally answer the BIG QUESTION:"))
    A(figure(compare(140, 135), "Your friend is 140 cm, you are 135 cm → 140 &gt; 135, your friend is taller"))
    A(P("So your friend (140 cm) is taller than you (135 cm) — by 140 − 135 = <b>5 cm</b>. Same unit, easy "
        "comparison!"))
    A(example("write 2 kg 250 g as grams, and as kilograms", steps([
        "As grams: (2 × 1000) + 250 = 2000 + 250 = <b>2250 g</b>.",
        "As kilograms: 2250 ÷ 1000 = <b>2.25 kg</b>.",
        "Both describe the very same weight. ✓",
    ])))
    A(tryit("Write <b>3 L 500 mL</b> as a number of millilitres.",
            "(3 × 1000) + 500 = 3000 + 500 = <b>3500 mL</b>."))

    A(H("Telling time and converting it"))
    A(P("Time has its own friendly numbers: <b>60</b> minutes in an hour, <b>60</b> seconds in a minute. To turn "
        "hours into minutes, multiply by 60. The clock below shows <b>2:30</b> — half past two:"))
    A(figure(clock(2, 30), "Half past 2. The half-hour means 30 minutes — and 2½ hours = 150 minutes"))
    A(example("convert 2 hours 30 minutes into minutes", steps([
        "Change the hours into minutes: 2 × 60 = 120 minutes.",
        "Add the extra minutes: 120 + 30 = <b>150 minutes</b>.",
        "Check: 150 minutes is two-and-a-half hours — that matches 2:30. ✓",
    ])))
    A(P("Here's another: the clock below reads <b>3:15</b> — a quarter past three. A quarter of an hour is "
        "15 minutes (because 60 ÷ 4 = 15)."))
    A(figure(clock(3, 15), "Quarter past 3 = 3:15. A quarter-hour is 60 ÷ 4 = 15 minutes"))
    A(tryit("How many minutes are there in <b>3 hours</b>?",
            "3 × 60 = <b>180 minutes</b>."))

    A(H("Money: rupees and paise"))
    A(P("Money converts just like the others: <b>100 paise = 1 rupee</b>, so paise are small and rupees are big. "
        "<b>₹5 and 75 paise</b> = (5 × 100) + 75 = <b>575 paise</b>. To go back, divide by 100: 575 paise = ₹5.75."))
    A(tryit("How many paise are there in <b>₹2 and 50 paise</b>?",
            "(2 × 100) + 50 = 200 + 50 = <b>250 paise</b>."))

    A(H("Conversion word problems"))
    A(P("Now let's use conversions in real stories — exactly the kind you meet on a road trip, in a kitchen, or "
        "at the shop. The plan is always: <em>get everything into one unit, then add or subtract.</em>"))
    A(P("Take the school van's diesel tank: it <em>holds</em> <b>75 L</b> but only has <b>18 L</b> in it now. "
        "The bar chart makes the gap easy to see — the empty space is what we need to fill:"))
    A(figure(bar_chart([("Has now", 18), ("Tank full", 75)]),
             "The tank holds 75 L but has only 18 L — the difference is what's still needed"))
    A(example("the school van tank", steps([
        "A school van's diesel tank holds <b>75 L</b>. Right now there are <b>18 L</b> inside.",
        "How many more litres are needed to fill it? Same unit already (litres), so just subtract.",
        "75 − 18 = <b>57 L</b> more are needed. ✓",
    ])))
    A(example("how heavy can the box still hold?", steps([
        "A box can carry <b>250 kg</b>. It already holds <b>55 kg</b>.",
        "Space left = 250 − 55 = <b>195 kg</b> more can be put in. ✓",
    ])))
    A(example("joining two ribbons in mixed units", steps([
        "One ribbon is <b>1 m 50 cm</b>, another is <b>1 m 30 cm</b>. Put both in centimetres.",
        "1 m 50 cm = 150 cm; 1 m 30 cm = 130 cm.",
        "Total = 150 + 130 = 280 cm = <b>2 m 80 cm</b> (since 280 ÷ 100 = 2 remainder 80). ✓",
    ])))
    A(tryit("Ammu's mum had <b>1 L</b> of oil and was left with <b>250 mL</b> after cooking. How much oil did "
            "she use?",
            "Put both in mL: 1 L = 1000 mL. Used = 1000 − 250 = <b>750 mL</b>."))

    A(H("Now you try — climb the ladder"))
    A(P("Work up the rungs. Try each one before you peek!"))

    A(practice("Remember", [
        ("How many centimetres are in 1 metre?", "100 cm."),
        ("How many grams are in 1 kilogram?", "1000 g."),
        ("How many minutes are in 1 hour?", "60 minutes."),
        ("How many millilitres are in 1 litre?", "1000 mL."),
        ("How many paise are in 1 rupee?", "100 paise."),
    ]))
    A(practice("Understand", [
        ("Convert 2 m into centimetres.", "2 × 100 = 200 cm."),
        ("Convert 5000 g into kilograms.", "5000 ÷ 1000 = 5 kg."),
        ("Convert 2 hours into minutes.", "2 × 60 = 120 minutes."),
        ("Going from litres to millilitres, do you multiply or divide?",
         "Multiply (big unit → small unit means more)."),
        ("Write 1 m 25 cm as centimetres.", "100 + 25 = 125 cm."),
    ]))
    A(practice("Apply", [
        ("A tank holds 60 L of water and has 22 L in it. How much more is needed to fill it?",
         "60 − 22 = 38 L."),
        ("Convert 3 kg 400 g into grams.", "(3 × 1000) + 400 = 3400 g."),
        ("How many minutes are in 4 hours 15 minutes?", "(4 × 60) + 15 = 255 minutes."),
        ("A jug holds 2 L. You pour out 750 mL. How much is left (in mL)?",
         "2 L = 2000 mL; 2000 − 750 = 1250 mL."),
        ("How many paise are in ₹7 and 25 paise?", "(7 × 100) + 25 = 725 paise."),
    ]))
    A(practice("Analyze", [
        ("Who is taller: a girl 1 m 38 cm tall, or a boy 142 cm tall? By how much?",
         "1 m 38 cm = 138 cm. The boy at 142 cm is taller, by 142 − 138 = 4 cm."),
        ("Which is heavier: 2 kg 500 g, or 2300 g?",
         "2 kg 500 g = 2500 g, which is heavier than 2300 g (by 200 g)."),
        ("A flagpole stood 1 m 50 cm above the ground, then a 12 m 65 cm extension pole was fixed on "
         "top. How tall is it now?",
         "150 cm + 1265 cm = 1415 cm = 14 m 15 cm."),
        ("A box can carry 250 kg; it holds 55 kg. Can you still add a 200 kg load?",
         "Space left is 250 − 55 = 195 kg, which is less than 200 kg, so no — it would be 5 kg too much."),
    ]))
    A(practice("Create", [
        ("Write a length equal to 250 cm using metres and centimetres.",
         "250 cm = 2 m 50 cm (since 250 ÷ 100 = 2 remainder 50)."),
        ("Make up a tank-filling problem whose answer is 'needs 40 more litres'.",
         "Many answers, e.g. “A 100 L tank has 60 L in it — it needs 100 − 60 = 40 L more.”"),
        ("Invent a recipe problem that uses converting litres to millilitres.",
         "e.g. “A recipe needs 1 L 200 mL = 1200 mL of milk; you have 800 mL, so you need 400 mL more.”"),
    ]))

    A(challenge(
        P("Four chains are joined end to end: <b>24 m 66 cm</b>, <b>9 m 36 cm</b>, <b>20 m 45 cm</b> and "
          "<b>18 m 30 cm</b>. What is the total length of the long chain, in metres and centimetres?") +
        tryit("Add the centimetres together and the metres together, then bundle every 100 cm into 1 m.",
              "Centimetres: 66 + 36 + 45 + 30 = 177 cm = 1 m 77 cm. Metres: 24 + 9 + 20 + 18 = 71 m. "
              "Total = 71 m + 1 m 77 cm = <b>72 m 77 cm</b>.")))

    A(kiwi("Well done — you put both measurements into the same unit first, which is the whole secret to "
           "getting conversions right. You can now switch between km/m/cm, kg/g, L/mL, hours/minutes "
           "and rupees/paise, handle mixed units, and solve real measuring problems. That wraps up Part 2, "
           "Fair Shares. 🏆"))

    chapter("Part 2 · Fair Shares", 8, "Useful Conversions",
            "Arithmetic · Useful Conversions", "".join(b))
