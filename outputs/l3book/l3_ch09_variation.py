#!/usr/bin/env python3
"""L3 Chapter 9 — Direct & Inverse Variation (Algebra · In Proportion). Builds on
Chapter 8's ratios: when one quantity changes, does the other grow with it
(direct) or shrink (inverse)? Spotting which is which; solving with the
constant-ratio and constant-product ideas; the 'more is not always more' surprise."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, bar_chart, balance, ratio_bar, number_line)


def build(chapter):
    b = []; A = b.append

    A(big_q("One painter takes 12 days to paint a long wall. So how long would 2 painters take? "
            "6 days, you'd guess. And 4 painters? 3 days. <em>More painters, fewer days.</em> "
            "But buying more paint cans does the opposite — more cans, more cost. Two quantities, "
            "two completely different behaviours. Today we learn to tell them apart on sight — and meet a "
            "surprise: in maths, <b>more is not always more</b>."))
    A(kiwi("Kiwi again! 🥝 You just mastered ratios. Now we watch what happens when one amount "
           "<em>changes</em>. Sometimes its partner rises with it; sometimes its partner falls. "
           "These two opposite stories are called <b>direct variation</b> and <b>inverse variation</b>, "
           "and almost every real-world 'rate' question is one of them. Let's meet them both."))

    # ── 1. Direct variation ─────────────────────────────
    A(H("Direct variation: they rise together"))
    A(P("Pens cost <b>₹8</b> each. Buy more pens and you pay more — the cost <b>grows in step</b> with the "
        "number of pens. When two quantities go up together (and down together) so that their "
        "<b>ratio stays the same</b>, we say one <b>varies directly</b> with the other."))
    A(figure(bar_chart([("1 pen", 8), ("3 pens", 24), ("6 pens", 48)], unit="₹"),
             "Cost grows in step with pens: 1→₹8, 3→₹24, 6→₹48. Twice the pens, twice the cost."))
    A(P("Here's the fingerprint of direct variation: <b>cost ÷ pens is always the same</b>. "
        "8 ÷ 1 = 8, 24 ÷ 3 = 8, 48 ÷ 6 = 8. That fixed value (₹8 per pen) is called the "
        "<b>constant</b> — it never changes, and it's exactly the 'one part' / unitary value from "
        "Chapter 8."))
    A(figure(ratio_bar([1, 1, 1, 1, 1, 1], ["8", "8", "8", "8", "8", "8"]),
             "Six pens = six equal \u20b98 blocks. Each extra pen adds the same \u20b98 \u2014 that is the constant at work."))
    A(example("4 books cost ₹200. What do 7 books cost?", steps([
        "Spot the type: more books → more cost. That's <b>direct variation</b>.",
        "Find the constant (cost of one book): ₹200 ÷ 4 = <b>₹50</b> per book.",
        "Scale up to 7 books: 7 × ₹50 = <b>₹350</b>.",
        "Check the ratio held: 200 ÷ 4 = 50 and 350 ÷ 7 = 50 — same constant. ✓",
    ])))
    A(kiwi("Test for direct variation: <b>does the ratio (one ÷ other) stay constant?</b> If yes, "
           "they vary directly — double one and the other doubles, halve one and the other halves."))
    A(tryit("2 kg of apples cost ₹90. What do 5 kg cost?",
            "Direct: more kg → more cost. One kg = ₹90 ÷ 2 = ₹45. Five kg = 5 × ₹45 = <b>₹225</b>. "
            "(Check: 225 ÷ 5 = 45 = the constant.)"))

    # ── 2. Inverse variation ────────────────────────────
    A(H("Inverse variation: as one rises, the other falls"))
    A(P("Back to the wall. <b>4 painters</b> finish in <b>6 days</b>. Add painters and the job finishes "
        "<em>sooner</em> — one quantity goes <b>up</b> while the other goes <b>down</b>. When that happens "
        "so that their <b>product stays the same</b>, one quantity <b>varies inversely</b> with the other."))
    A(figure(bar_chart([("4 painters", 6), ("6 painters", 4), ("8 painters", 3)], unit=" days"),
             "More painters, fewer days: 4→6 days, 6→4 days, 8→3 days. The bars shrink as the crew grows."))
    A(P("The fingerprint of inverse variation: <b>painters × days is always the same</b>. "
        "4 × 6 = 24, 6 × 4 = 24, 8 × 3 = 24. That constant <b>24</b> is the total amount of work — call it "
        "<b>'24 painter-days.'</b> The wall always needs 24 painter-days; you can spread that work across "
        "many painters and few days, or few painters and many days."))
    A(figure(balance(24, 24, "8 × 3", "4 × 6"),
             "Inverse variation keeps the PRODUCT balanced: 8 × 3 = 4 × 6 = 24."))
    A(example("6 workers dig a trench in 10 days. How long would 5 workers take?", steps([
        "Spot the type: fewer workers → MORE days. That's <b>inverse variation</b>.",
        "Find the constant (total work): 6 × 10 = <b>60 worker-days</b>.",
        "Now share 60 across 5 workers: 60 ÷ 5 = <b>12 days</b>.",
        "Check: 5 × 12 = 60 — same product. ✓ Fewer hands, more time, same total job.",
    ])))
    A(kiwi("Test for inverse variation: <b>does the product (one × other) stay constant?</b> If yes, they "
           "vary inversely — double one and the other halves. Direct uses <em>÷ stays same</em>; "
           "inverse uses <em>× stays same</em>. That one swap is the whole difference!"))
    A(tryit("A car covers a fixed road in 4 hours at 60 km/h. How long at 80 km/h?",
            "Faster speed → less time = inverse. Constant = distance = 60 × 4 = 240 km. "
            "Time at 80 = 240 ÷ 80 = <b>3 hours</b>. (Check: 80 × 3 = 240.) ✓"))

    # ── 3. Spotting which is which ──────────────────────
    A(H("The big question: which kind is it?"))
    A(P("Before you compute <em>anything</em>, ask one question: <b>when the first quantity goes UP, does "
        "the second go up or down?</b> That single answer tells you the method."))
    A(P("• Goes <b>up together</b> (more → more) → <b>direct</b> → use the <em>constant ratio</em> "
        "(÷ stays same); find one, then multiply.<br>"
        "• Goes <b>opposite</b> (more → less) → <b>inverse</b> → use the <em>constant product</em> "
        "(× stays same); multiply to get the total, then divide."))
    A(kiwi("Quick reflex drill — say 'same way' or 'opposite way':<br>"
           "• More petrol → more distance? <b>same way → direct.</b><br>"
           "• More taps filling a tank → less time? <b>opposite → inverse.</b><br>"
           "• More speed → less time for a trip? <b>opposite → inverse.</b><br>"
           "• More hours worked → more pay? <b>same way → direct.</b>"))
    A(figure(number_line(0, 24, 4, [(24, "24 painter-days", "#E0556E")]),
             "The wall is always 24 painter-days. Spread that fixed total over many painters and few "
             "days, or few painters and many days \u2014 the product never moves off 24."))
    A(example("decide and solve: 3 pipes fill a tank in 8 hours; how long with 4 pipes?", steps([
        "More pipes → less time. Opposite way, so <b>inverse</b> variation.",
        "Constant product = 3 × 8 = <b>24 pipe-hours</b>.",
        "With 4 pipes: 24 ÷ 4 = <b>6 hours</b>.",
        "Check: 4 × 6 = 24. ✓",
    ])))
    A(tryit("Decide the type, then solve: 3 metres of cloth cost ₹150. What do 8 metres cost?",
            "More cloth → more cost = <b>direct</b>. One metre = 150 ÷ 3 = ₹50. Eight metres = 8 × 50 = "
            "<b>₹400</b>."))

    # ── 4. The surprise: more is not always more ────────
    A(H("Surprise: 'more is not always more'"))
    A(P("Most people's gut feeling is <em>'more always means more.'</em> Inverse variation proves that wrong "
        "in everyday life — and it can save you from real mistakes. Picture food on a long trek."))
    A(figure(bar_chart([("12 people", 20), ("16 people", 15), ("24 people", 10)], unit=" days"),
             "Same food box: MORE people means the food lasts FEWER days. 12→20, 16→15, 24→10 days."))
    A(example("food lasts 12 hikers for 20 days. How long will it last 16 hikers?", steps([
        "More mouths → food runs out SOONER. Opposite way → <b>inverse</b> variation.",
        "Constant = total food = 12 × 20 = <b>240 person-days</b> of food.",
        "Share among 16 people: 240 ÷ 16 = <b>15 days</b>.",
        "Surprise check: more people (16 &gt; 12) gave fewer days (15 &lt; 20). 'More' made the answer "
        "<em>smaller</em> — exactly because it's inverse!",
    ])))
    A(kiwi("Whenever a problem feels like 'more should give more' but the answer comes out smaller — pause. "
           "You've spotted inverse variation. Trust the <b>product stays constant</b>, not your gut. "
           "(And if you ever multiply when you should divide, your answer will be wildly too big — a free "
           "mistake-detector!)"))

    # ── Practice ladder ─────────────────────────────────
    A(H("Now climb the ladder"))
    A(P("First decide direct or inverse, then solve. Peek only after you try!"))

    A(practice("Remember", [
        ("In direct variation, when one quantity doubles, the other ___ .", "also doubles."),
        ("In inverse variation, when one quantity doubles, the other ___ .", "halves."),
        ("In direct variation, what stays constant: the ratio or the product?", "The <b>ratio</b> (one ÷ other)."),
        ("In inverse variation, what stays constant: the ratio or the product?", "The <b>product</b> (one × other)."),
    ]))
    A(practice("Understand", [
        ("More workers on a job means fewer days. Is this direct or inverse?", "<b>Inverse</b> (opposite way)."),
        ("More litres of petrol means more distance driven. Direct or inverse?", "<b>Direct</b> (same way)."),
        ("Cost of 1 toy is ₹15. Find the constant and the cost of 4 toys.",
         "Constant = ₹15 per toy (direct). Four toys = 4 × 15 = <b>₹60</b>."),
        ("5 machines pack boxes in 12 days. Find the constant amount of work.",
         "Inverse; constant = 5 × 12 = <b>60 machine-days</b>."),
    ]))
    A(practice("Apply", [
        ("8 identical chocolates cost ₹96. What do 5 chocolates cost? (direct)",
         "One = 96 ÷ 8 = ₹12. Five = 5 × 12 = <b>₹60</b>."),
        ("10 machines finish an order in 12 days. How long would 8 machines take? (inverse)",
         "Constant = 10 × 12 = 120. With 8: 120 ÷ 8 = <b>15 days</b>."),
        ("2 taps fill a tank in 6 hours. How long would 3 taps take?",
         "Inverse; constant = 2 × 6 = 12. With 3 taps: 12 ÷ 3 = <b>4 hours</b>."),
        ("5 cups of flour make 20 cookies. How many cookies from 8 cups? (direct)",
         "Per cup = 20 ÷ 5 = 4 cookies. Eight cups = 8 × 4 = <b>32 cookies</b>."),
    ]))
    A(practice("Analyze", [
        ("A student says: 'If 6 workers take 10 days, then 12 workers take 20 days — double the workers, "
         "double the days.' What's the mistake, and what's the right answer?",
         "It's inverse, not direct! More workers → FEWER days. Constant = 6 × 10 = 60, so 12 workers take "
         "60 ÷ 12 = <b>5 days</b>, not 20."),
        ("Decide the type with reasoning: the number of slices you cut a fixed cake into, versus the size "
         "of each slice.",
         "More slices → each slice is SMALLER. Opposite way → <b>inverse</b> (slices × size = whole cake, "
         "a constant)."),
        ("3 kg of rice feeds a family for 9 days. They cook the same amount daily. How long does 5 kg last?",
         "More rice → more days = <b>direct</b>. Per kg = 9 ÷ 3 = 3 days. Five kg = 5 × 3 = <b>15 days</b>."),
        ("Is this direct or inverse: at a fixed speed, the time taken versus the distance travelled? Solve "
         "for 2 hours if 1 hour covers 50 km.",
         "More time → more distance = <b>direct</b>. Per hour = 50 km. Two hours = 2 × 50 = <b>100 km</b>."),
    ]))
    A(practice("Create", [
        ("Invent a real-life example of DIRECT variation and explain why the ratio stays constant.",
         "e.g. 'apples at ₹40/kg' — cost ÷ kg is always 40, so cost rises in step with weight."),
        ("Invent a real-life example of INVERSE variation and explain why the product stays constant.",
         "e.g. 'a fixed pizza shared among friends' — slices × size-per-friend = whole pizza, a constant; "
         "more friends → smaller slices."),
        ("Write your own problem where '12 of something takes 6 days' and ask about 9 of them, then solve it "
         "as inverse variation.",
         "e.g. '12 workers take 6 days; how long for 9?' Constant = 12 × 6 = 72; 72 ÷ 9 = <b>8 days</b>."),
    ]))

    A(challenge(
        P("The builder's puzzle. A team of <b>15 workers</b> builds a boundary wall in <b>8 days</b>. The "
          "owner suddenly needs it finished in just <b>5 days</b>. How many <em>extra</em> workers must be "
          "hired? (Assume every worker works at the same steady pace.)") +
        tryit("Find the total work first, then work backwards.",
              "This is inverse variation: more workers → fewer days. Total work = 15 × 8 = <b>120 worker-days</b> "
              "— that amount never changes. To finish in 5 days we need 120 ÷ 5 = <b>24 workers</b>. The team "
              "already has 15, so hire 24 − 15 = <b>9 extra workers</b>. (Notice how the constant product "
              "did all the heavy lifting — no guessing!) 🎉")))

    A(kiwi("Superb! You can now tell direct from inverse variation just by asking 'same way or opposite "
           "way?', solve each with its constant (ratio for direct, product for inverse), and you've seen "
           "why 'more is not always more.' Next we hunt for hidden rules in <b>patterns &amp; sequences</b> — "
           "where numbers grow in shapes you can predict. ➡️"))

    chapter("Part 2 · Parts & Wholes", 9, "Direct & Inverse Variation",
            "Algebra · In Proportion", "".join(b))
