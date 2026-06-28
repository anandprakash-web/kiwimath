#!/usr/bin/env python3
"""L3 Chapter 7 — Profit, Loss & Discounts (Arithmetic · Money Maths). Builds on
Ch6 percentages: cost price, selling price, profit, loss, profit%/loss% (ALWAYS on
cost price), marked price & discount (on marked price), and real shopping stories."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, trap, compare, bar_chart, ratio_bar, decimal_grid)


def build(chapter):
    b = []; A = b.append

    A(big_q("A shopkeeper buys a cricket bat for <b>₹400</b> and sells it for <b>₹500</b>. Easy — she made "
            "₹100. But now two bats: she sells one for a ₹100 gain and the other for a ₹100 gain too… yet she "
            "tells you one sale was a <em>better deal</em> than the other. How can the same ₹100 profit be "
            "better on one bat than the other? The answer is hiding in a percentage."))
    A(kiwi("Hello again! \U0001F95D Last chapter you mastered percentages. Now we spend them in the real world — "
           "the world of <b>buying and selling</b>. Every shop runs on a few simple words, and once you know "
           "them, you'll never be fooled by a price tag again. Let's set up our shop."))

    A(H("The shopkeeper's three words"))
    A(P("Almost every money problem uses just three quantities. Meet them:"))
    A(P("• <b>Cost Price (CP)</b> — what the seller <em>paid</em> to get the item.<br>"
        "• <b>Selling Price (SP)</b> — what the seller <em>sold</em> it for.<br>"
        "• <b>Profit</b> or <b>Loss</b> — the difference between them."))
    A(P("The rule writes itself. If you sell for <em>more</em> than you paid, you made a <b>profit</b>; if you "
        "sell for <em>less</em>, you took a <b>loss</b>:"))
    A(P("<b>Profit = SP − CP</b> &nbsp;(when SP &gt; CP) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Loss = CP − SP</b> "
        "&nbsp;(when CP &gt; SP)"))
    A(example("buy at ₹400, sell at ₹500", steps([
        "CP = ₹400 (what she paid). SP = ₹500 (what she sold for).",
        "SP &gt; CP, so it's a profit: Profit = 500 − 400 = <b>₹100</b>. ✓",
    ])))
    A(figure(compare(500, 400), "SP ₹500 is greater than CP ₹400, so there's a ₹100 profit"))
    A(tryit("A toy is bought for ₹250 and sold for ₹200. Profit or loss, and how much?",
            "SP &lt; CP, so it's a <b>loss</b>: 250 − 200 = <b>₹50</b> loss."))

    A(H("The golden rule: profit% and loss% are ALWAYS on the cost price"))
    A(P("Money profit alone can fool you (as our two-bats puzzle showed). To compare deals fairly, we ask: the "
        "profit is what <em>percent of what it cost</em>? This is <b>profit%</b>, and there is one rule you "
        "must never break:"))
    A(kiwi("⭐ <b>THE GOLDEN RULE.</b> Profit% and loss% are <em>always</em> worked out on the "
           "<b>Cost Price</b> — never the selling price. The cost price is the shopkeeper's “starting money,” "
           "so it's the fair thing to measure the gain against. Burn this in: <b>% is on CP</b>."))
    A(P("<b>Profit% = (Profit ÷ CP) × 100</b> &nbsp;&nbsp;and&nbsp;&nbsp; <b>Loss% = (Loss ÷ CP) × 100</b>"))
    A(example("CP ₹400, SP ₹500 — find the profit%", steps([
        "Profit = 500 − 400 = ₹100.",
        "Divide by the COST price (not 500!): 100 ÷ 400 = 0.25.",
        "Times 100: 0.25 × 100 = <b>25%</b> profit. ✓",
    ])))
    A(figure(decimal_grid(25), "₹100 profit on a ₹400 cost = 25 out of every 100 rupees of cost → 25%"))
    A(figure(ratio_bar([400, 100], ["cost 400", "profit 100"]),
             "SP ₹500 = cost ₹400 + profit ₹100. The profit is one-quarter of the cost → 25%"))
    A(example("CP ₹500, SP ₹400 — find the loss%", steps([
        "Loss = 500 − 400 = ₹100.",
        "Divide by CP: 100 ÷ 500 = 0.20.",
        "Times 100: <b>20%</b> loss. ✓",
        "Notice: the SAME ₹100 gap is 25% on a ₹400 cost but only 20% on a ₹500 cost — the cost price "
        "decides the percent.",
    ])))
    A(tryit("A pen costs ₹50 and is sold for ₹65. Find the profit%.",
            "Profit = 65 − 50 = ₹15. Profit% = 15 ÷ 50 × 100 = <b>30%</b>."))

    A(trap(P("The most common profit% mistake: dividing the profit by the <b>selling price</b> instead of "
             "the cost. For CP ₹400, SP ₹500, profit ₹100, that wrongly gives 100 ÷ 500 = <b>20%</b>. "
             "<b>The right way:</b> profit% is <em>always</em> on the <b>cost price</b> — 100 ÷ 400 = "
             "<b>25%</b>. Why? Profit% measures the gain against the shopkeeper's <em>starting</em> money "
             "(what she paid), not against the price she ended at. Same numbers, but ₹100 is a bigger "
             "slice of ₹400 than of ₹500 — so the base you choose changes the answer. Always: <b>% on "
             "CP</b>.")))

    A(H("Going the other way: find the selling price from a target profit%"))
    A(P("Shopkeepers usually <em>decide</em> the profit% they want, then work out the selling price. To add a "
        "profit% onto the cost: find that percent of CP and add it on (exactly the percentage-increase move "
        "from Ch6). For a loss%, subtract instead."))
    A(example("she wants 20% profit on a ₹200 item — what's the SP?", steps([
        "Find 20% of the cost: 0.20 × 200 = ₹40 (the profit she wants).",
        "Add it to the cost: 200 + 40 = <b>₹240</b>.",
        "Shortcut: 20% profit means SP is 120% of CP → 1.20 × 200 = ₹240. ✓",
    ])))
    A(figure(bar_chart([("CP", 200), ("Profit", 40), ("SP", 240)]),
             "SP = CP + profit. ₹200 cost + ₹40 (20%) profit = ₹240 selling price"))
    A(example("a shirt costs ₹800 but is sold at a 10% loss — what's the SP?", steps([
        "Find 10% of cost: 0.10 × 800 = ₹80 (the loss).",
        "Take it off the cost: 800 − 80 = <b>₹720</b>.",
        "Shortcut: 10% loss means SP is 90% of CP → 0.90 × 800 = ₹720. ✓",
    ])))
    A(tryit("A baker’s cake costs ₹150 to make. She wants a 30% profit. What price should she sell it at?",
            "30% of 150 = ₹45 profit, so SP = 150 + 45 = <b>₹195</b>."))

    A(H("Marked price &amp; discount — the sale-tag maths"))
    A(P("Walk into any shop and you'll see a <b>Marked Price (MP)</b> — the price printed on the tag (also "
        "called the list price). A <b>discount</b> is a cut <em>off the marked price</em> to tempt you to buy. "
        "And here's the partner to the golden rule:"))
    A(kiwi("⭐ <b>Discount is always on the MARKED price</b> (the tag), while profit/loss is always on the "
           "<b>COST price</b>. Don't mix them up! A “20% off” sticker means 20% off the tag — it says nothing "
           "about what the shop paid."))
    A(P("<b>Discount = MP − SP</b>, &nbsp; and &nbsp; <b>Sale Price (SP) = MP − discount</b>. The discount "
        "percent is on the marked price: <b>Discount% = (Discount ÷ MP) × 100</b>."))
    A(example("a ₹500 jacket has “20% OFF” — what do you pay?", steps([
        "Discount = 20% of the MARKED price: 0.20 × 500 = ₹100.",
        "Sale price = MP − discount: 500 − 100 = <b>₹400</b>.",
        "Shortcut: paying after 20% off means paying 80% → 0.80 × 500 = ₹400. ✓",
    ])))
    A(figure(compare(500, 400), "Marked ₹500, pay ₹400 after a 20% discount — you save ₹100"))
    A(example("a tag says MP ₹400, you pay ₹300 — what's the discount %?", steps([
        "Discount = MP − SP = 400 − 300 = ₹100.",
        "Discount% on the MARKED price: 100 ÷ 400 × 100 = <b>25%</b>. ✓",
    ])))
    A(figure(decimal_grid(25), "₹100 off a ₹400 tag = 25 out of every 100 rupees of the marked price → 25% off"))
    A(tryit("A ₹250 toy is on “10% off”. What is the sale price?",
            "10% of 250 = ₹25 off, so you pay 250 − 25 = <b>₹225</b>."))

    A(H("Putting it together: cost, tag, discount AND profit"))
    A(P("Real shops do all of it at once. A clever shopkeeper buys cheaply (CP), marks the price <em>up</em> on "
        "the tag (MP), then offers a discount off the tag — and <em>still</em> makes a profit, because the sale "
        "price stays above her cost. The trick is to track which price each percentage is measured against."))
    A(example("CP ₹400, marked at ₹500, with a 10% discount — does she profit?", steps([
        "Discount is on the MARKED price: 10% of 500 = ₹50.",
        "Sale price = 500 − 50 = ₹450 (this is the SP).",
        "Now profit on the COST price: profit = 450 − 400 = ₹50.",
        "Profit% = 50 ÷ 400 × 100 = <b>12.5%</b>. She gives ‘10% off’ AND keeps a 12.5% profit. \U0001F60E",
    ])))
    A(figure(ratio_bar([400, 50, 50], ["cost ₹400", "+50", "−50"]),
             "The ₹500 tag = ₹400 cost + ₹50 profit kept, with ₹50 sliced off as the discount"))
    A(kiwi("See the magician's secret? ‘10% off ₹500’ sounds generous to <em>you</em>, but it's measured on the "
           "<b>inflated tag</b>, while her profit is measured on the <b>real cost</b>. Two different ‘wholes’, "
           "two different percentages — and she wins on both counts. Now you can read straight through any sale."))
    A(tryit("CP ₹200, marked ₹300, 20% discount. Find the sale price and the profit.",
            "20% of 300 = ₹60 off → SP = 300 − 60 = <b>₹240</b>. Profit = 240 − 200 = <b>₹40</b> "
            "(a 20% profit on the ₹200 cost)."))

    A(H("Now climb the ladder"))
    A(practice("Remember", [
        ("What does CP stand for?", "Cost Price — what the seller paid."),
        ("What does SP stand for?", "Selling Price — what the seller sold it for."),
        ("Write the formula for profit.", "Profit = SP − CP (when SP is bigger)."),
        ("Profit% is always worked out on which price?", "The Cost Price (CP)."),
        ("A discount is always taken off which price?", "The Marked Price (MP)."),
    ]))
    A(practice("Understand", [
        ("CP ₹120, SP ₹150. Profit or loss, and how much?", "Profit of ₹30 (150 − 120)."),
        ("CP ₹250, SP ₹200. Profit or loss, and how much?", "Loss of ₹50 (250 − 200)."),
        ("MP ₹500, discount ₹50. What is the sale price?", "₹450 (500 − 50)."),
        ("Why don’t we use the selling price to find profit%?", "Profit% is a share of the seller’s starting money — the cost — so it must be on CP, the fair base."),
        ("MP ₹800, you pay ₹680. How big was the discount in rupees?", "₹120 (800 − 680)."),
    ]))
    A(practice("Apply", [
        ("CP ₹400, SP ₹500. Find the profit%.", "Profit 100; 100 ÷ 400 × 100 = 25%."),
        ("CP ₹150, SP ₹120. Find the loss%.", "Loss 30; 30 ÷ 150 × 100 = 20%."),
        ("A ₹200 item is sold at 20% profit. Find the SP.", "20% of 200 = 40; SP = 200 + 40 = ₹240."),
        ("A ₹500 jacket has 20% off. Find the sale price.", "20% of 500 = 100; pay 500 − 100 = ₹400."),
        ("MP ₹400, SP ₹300. Find the discount%.", "Discount 100; 100 ÷ 400 × 100 = 25%."),
    ]))
    A(practice("Analyze", [
        ("Bat A: CP ₹400, profit ₹100. Bat B: CP ₹500, profit ₹100. Which is the better deal (higher profit%)?",
         "Bat A: 100 ÷ 400 = 25%. Bat B: 100 ÷ 500 = 20%. Same ₹100, but Bat A is the better deal at 25%."),
        ("A ₹360 item is sold for ₹480. Find the profit%.",
         "Profit 120; 120 ÷ 360 × 100 = 33⅓% (the answer is a recurring percent)."),
        ("CP ₹400, marked ₹500, then 10% discount. What is the final profit% on cost?",
         "10% of 500 = 50 off → SP ₹450; profit 450 − 400 = 50; 50 ÷ 400 × 100 = 12.5%."),
        ("Shop X: ‘50% off ₹400’. Shop Y: ‘₹250 flat’ for the same toy. Which is cheaper, and by how much?",
         "Shop X: 50% of 400 = 200 off → pay ₹200. Shop Y: ₹250. Shop X is cheaper by ₹50."),
    ]))
    A(practice("Create", [
        ("Invent a buy-and-sell story that gives exactly a 25% profit. State CP and SP.",
         "Many answers — e.g. CP ₹80, SP ₹100 (profit 20 = 25% of 80), or CP ₹200, SP ₹250."),
        ("Design a sale tag (marked price + discount %) where the customer pays exactly ₹360.",
         "E.g. ‘₹400, 10% off’ (40 off → ₹360) or ‘₹720, 50% off’."),
        ("Make a shop puzzle where the seller gives a discount and STILL profits. Give CP, MP and the discount.",
         "E.g. CP ₹200, MP ₹300, 20% off → SP ₹240 → ₹40 profit. The discount is off the tag, profit is on cost."),
    ]))

    A(challenge(
        P("Back to the BIG QUESTION! Both bats earned a <b>₹100 profit</b>. Bat 1 cost the shopkeeper "
          "<b>₹400</b>; bat 2 cost her <b>₹500</b>. Work out the <b>profit% on each</b> and explain, in one "
          "sentence, why the same ₹100 is a better deal on one bat than the other.") +
        tryit("Find each profit% on its own cost price.",
              "Bat 1: 100 ÷ 400 × 100 = <b>25%</b>. Bat 2: 100 ÷ 500 × 100 = <b>20%</b>. Same ₹100 profit, but "
              "bat 1 is the better deal because that ₹100 is a <em>bigger slice of a smaller cost</em> — 25% of "
              "₹400 beats 20% of ₹500. Money profit hides the truth; <b>profit% on cost</b> reveals it. That's "
              "why every smart trader thinks in percentages. \U0001F3CF")))

    A(kiwi("Fantastic — you can now run a whole shop! You know CP, SP, marked price and sale price; you can "
           "find profit, loss, profit%, loss% and discount%, always measuring on the right ‘whole’ (% on CP, "
           "discount on MP). Coming up next, we follow these comparisons further into the elegant world of "
           "<b>ratio &amp; proportion</b> — the maths of sharing, mixing and scaling. \U0001F9EE"))

    chapter("Part 2 · Parts & Wholes", 7, "Profit, Loss & Discounts",
            "Arithmetic · Money Maths", "".join(b))
