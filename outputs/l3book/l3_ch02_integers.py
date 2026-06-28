#!/usr/bin/env python3
"""L3 Chapter 2 — Meet the Integers (Number Theory · Integers). Bridges from the
Level-2 whole-number line into the world LEFT of zero: negatives in real life,
the integer number line, ordering, absolute value, and adding & subtracting
integers — built entirely from pictures, ending with the two-minuses surprise."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, number_line, compare, svg,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


# -- a couple of tiny bespoke figures, drawn exact-vector ---------------
def thermometer(temp, lo=-10, hi=10):
    """A vertical thermometer showing `temp` degrees, scale lo..hi."""
    x, y0, y1 = 70, 24, 224          # y0 = top (hi), y1 = bulb top (lo)
    span = hi - lo
    def yv(v): return y1 - (v - lo) / span * (y1 - y0)
    s = [f'<rect x="{x-9}" y="{y0}" width="18" height="{y1-y0}" rx="9" fill="#fff" stroke="{INK}" stroke-width="2"/>',
         f'<circle cx="{x}" cy="{y1+22}" r="20" fill="{BERRY if temp>=0 else SKY}" stroke="{INK}" stroke-width="2"/>']
    yt = yv(temp)
    col = BERRY if temp >= 0 else SKY
    s.append(f'<rect x="{x-5}" y="{yt:.0f}" width="10" height="{y1+22-yt:.0f}" fill="{col}"/>')
    s.append(f'<circle cx="{x}" cy="{y1+22}" r="13" fill="{col}"/>')
    for v in range(lo, hi + 1, 5):
        yy = yv(v)
        s.append(f'<line x1="{x+9}" y1="{yy:.0f}" x2="{x+17}" y2="{yy:.0f}" stroke="{INK}" stroke-width="1.6"/>')
        s.append(f'<text x="{x+22}" y="{yy+4:.0f}" font-size="13" fill="{INK}">{v}&#176;</text>')
    yz = yv(0)
    s.append(f'<line x1="{x-16}" y1="{yz:.0f}" x2="{x-9}" y2="{yz:.0f}" stroke="{GOLD}" stroke-width="3"/>')
    s.append(f'<text x="{x-20}" y="{yz+4:.0f}" font-size="12" fill="{GOLD}" text-anchor="end" font-weight="800">0</text>')
    s.append(f'<text x="{x}" y="{y0-6}" font-size="15" font-weight="800" fill="{col}" text-anchor="middle">{temp}&#176;C</text>')
    return svg("".join(s), 150, 270)


def elevation(value, deep=-40, high=40):
    """A sea-level picture: a marker at `value` metres (negative = below sea)."""
    W, H = 380, 200
    midy = 96
    s = [f'<rect x="0" y="0" width="{W}" height="{midy}" fill="{SKY}11"/>',
         f'<rect x="0" y="{midy}" width="{W}" height="{H-midy}" fill="{SKY}33"/>',
         f'<line x1="0" y1="{midy}" x2="{W}" y2="{midy}" stroke="{SKY}" stroke-width="2.5"/>',
         f'<text x="8" y="{midy-6}" font-size="12" fill="{SKY}" font-weight="800">sea level = 0 m</text>']
    span = high - deep
    yy = midy - (value) / span * (H - 20)
    yy = max(12, min(H - 12, yy))
    col = GRASS if value >= 0 else BERRY
    s.append(f'<line x1="190" y1="{midy}" x2="190" y2="{yy:.0f}" stroke="{col}" stroke-width="2" stroke-dasharray="4 4"/>')
    s.append(f'<circle cx="190" cy="{yy:.0f}" r="9" fill="{col}" stroke="#fff" stroke-width="2"/>')
    s.append(f'<text x="206" y="{yy+5:.0f}" font-size="15" font-weight="800" fill="{col}">{value:+d} m</text>')
    return svg("".join(s), W, H)


def signed_chips(pos, neg):
    """Draw `pos` orange (+) chips and `neg` blue (-) chips."""
    s = []; x = 14
    for _ in range(pos):
        s.append(f'<circle cx="{x+15}" cy="34" r="15" fill="{ORANGE}33" stroke="{ORANGE}" stroke-width="2"/>')
        s.append(f'<text x="{x+15}" y="40" font-size="20" text-anchor="middle" font-weight="800" fill="{ORANGE}">+</text>')
        x += 38
    x += 16
    for _ in range(neg):
        s.append(f'<circle cx="{x+15}" cy="34" r="15" fill="{SKY}33" stroke="{SKY}" stroke-width="2"/>')
        s.append(f'<text x="{x+15}" y="41" font-size="22" text-anchor="middle" font-weight="800" fill="{SKY}">&#8722;</text>')
        x += 38
    return svg("".join(s), max(x + 14, 200), 64)


def build(chapter):
    b = []; A = b.append

    A(big_q("The coldest natural place on Earth once hit about <b>89 degrees below zero</b>. "
            "A submarine can dive to <b>240 metres below the sea</b>. You might <b>owe a friend 5 rupees</b>. "
            "Plain whole numbers can't say any of these &#8212; they all need a number that is <em>less than "
            "nothing</em>. Do such numbers even exist? By the end of this chapter you'll add and subtract "
            "them in your head &#8212; and uncover why <b>two minuses make a plus</b>."))
    A(kiwi("Welcome back, explorer! &#129517; In Chapter 1 our number line started at 0 and marched right: "
           "0, 1, 2, 3 &#8230; But what lives to the <b>left</b> of zero? Today we extend the line in the other "
           "direction and meet the <b>integers</b>. Nothing here is hard &#8212; we'll build every step from a "
           "picture you can see."))

    A(H("Why zero can't be the end of the line"))
    A(P("Think about a lift (elevator) in a tall building. The ground floor is <b>0</b>. Going up gives "
        "floors 1, 2, 3 &#8230; But many buildings have a basement <em>below</em> the ground floor &#8212; a car park, "
        "maybe two levels down. What number should those floors get? We can't reuse 1 and 2 (those are "
        "<em>up</em>). We need new numbers below zero: <b>&#8722;1, &#8722;2, &#8722;3</b> &#8212; read &#8220;negative one, negative two&#8221;."))
    A(figure(thermometer(-5), "&#8722;5&#176;C: five degrees below zero. The 0 is just a landmark on the way down."))
    A(P("Negatives show up everywhere two opposite directions meet a starting point:"))
    A(P("&#8226; <b>Temperature:</b> above 0&#176; is +, below 0&#176; is &#8722;.<br>"
        "&#8226; <b>Sea level:</b> a mountain top is +2,000 m, the sea floor is &#8722;800 m.<br>"
        "&#8226; <b>Money:</b> &#8377;50 saved is +50; &#8377;20 owed is &#8722;20.<br>"
        "&#8226; <b>Time:</b> 3 years from now is +3, 3 years ago is &#8722;3."))
    A(figure(elevation(-30), "A diver 30 m below the sea is at &#8722;30 m. Sea level is the 0."))
    A(kiwi("The <b>integers</b> are the whole numbers together with their negatives, plus zero:<br>"
           "&#8230; &#8722;3, &#8722;2, &#8722;1, <b>0</b>, 1, 2, 3 &#8230; Zero is the only integer that is neither positive nor "
           "negative &#8212; it's the perfect middle, the hinge of the whole line."))

    A(H("The integer number line: zero gets a mirror"))
    A(P("Take Chapter 1's number line and reflect it through 0. Every positive number now has a "
        "<b>twin</b> the same distance to the left. These twins are called <b>opposites</b>: the opposite "
        "of 3 is &#8722;3, and the opposite of &#8722;3 is 3. Zero is its own opposite."))
    A(figure(number_line(-5, 5, 1, [(-3, "-3", SKY), (0, "0", GOLD), (3, "3", ORANGE)]),
             "&#8722;3 and 3 are opposites &#8212; both sit 3 steps from 0, on opposite sides."))
    A(P("Two rock-solid rules you can read straight off the line:"))
    A(steps([
        "<b>Bigger is to the right, smaller is to the left.</b> Always. So &#8722;2 &gt; &#8722;5, because &#8722;2 is "
        "farther right.",
        "<b>Every negative number is less than every positive number</b>, and both are arranged around 0.",
    ]))
    A(P("This fixes a famous trap. Which is colder, &#8722;2&#176; or &#8722;5&#176;? On the line, &#8722;5 is farther "
        "<em>left</em> than &#8722;2, so <b>&#8722;5 &lt; &#8722;2</b>: &#8722;5&#176; is the colder day, even though &#8220;5 looks "
        "bigger than 2&#8221;. The minus sign flips your intuition &#8212; the line never lies."))
    A(figure(number_line(-8, 0, 1, [(-5, "-5", SKY), (-2, "-2", BERRY)]),
             "&#8722;5 is to the LEFT of &#8722;2, so &#8722;5 &lt; &#8722;2."))
    A(tryit("Put in order, smallest first: 3, &#8722;7, 0, &#8722;1, 5.",
            "Smallest is the farthest left: <b>&#8722;7 &lt; &#8722;1 &lt; 0 &lt; 3 &lt; 5</b>."))

    A(H("Absolute value: how FAR from zero (forget the direction)"))
    A(P("Sometimes we only care <em>how far</em> a number is from 0, not which side. That distance is its "
        "<b>absolute value</b>, written with two straight bars: |&#8722;5| means &#8220;the distance of &#8722;5 from 0&#8221;, "
        "which is <b>5</b>. Distance is never negative, so an absolute value is never negative."))
    A(figure(number_line(-6, 6, 1, [(-4, "-4", SKY), (4, "4", ORANGE)]),
             "|&#8722;4| = 4 and |4| = 4: both are 4 steps from 0."))
    A(example("compute |&#8722;7|, |3|, |0|, and the opposite of &#8722;9", steps([
        "|&#8722;7| = 7  (it's 7 steps from 0).",
        "|3| = 3   (3 steps from 0).",
        "|0| = 0   (0 is sitting right on 0).",
        "The opposite of &#8722;9 is +9 &#8212; same distance, other side. (Don't confuse: |&#8722;9| = 9 is a "
        "<em>distance</em>; the opposite of &#8722;9 is the number 9.)",
    ])))
    A(kiwi("Picture absolute value as a footstep-counter: stand on the number, walk to 0, count steps. "
           "&#8722;6 and 6 give the same count, 6. It throws away the sign and keeps only the size."))
    A(tryit("Which is greater: |&#8722;8| or |5|? And which number is greater, &#8722;8 or 5?",
            "|&#8722;8| = 8 &gt; |5| = 5, so |&#8722;8| is greater. But as numbers, &#8722;8 &lt; 5 (&#8722;8 is far left). "
            "Size and position are different questions!"))

    A(H("Adding integers &#8212; just keep walking on the line"))
    A(P("Adding is moving along the line. <b>Adding a positive</b> walks you <em>right</em>; "
        "<b>adding a negative</b> walks you <em>left</em>. Start where the first number says, then take "
        "the second number's walk."))
    A(example("(+3) + (&#8722;5)", steps([
        "Start at +3.",
        "Add &#8722;5 &#8594; walk 5 steps LEFT.",
        "3 &#8594; 2 &#8594; 1 &#8594; 0 &#8594; &#8722;1 &#8594; &#8722;2. You land on <b>&#8722;2</b>.",
    ])))
    A(figure(number_line(-4, 5, 1, [(3, "start", ORANGE), (-2, "end", BERRY)]),
             "(+3) + (&#8722;5): begin at 3, step 5 left, finish at &#8722;2."))
    A(P("Here's a second way to picture it &#8212; the <b>chip model</b>. Let an orange <b>+</b> chip and a blue "
        "<b>&#8722;</b> chip cancel to <em>nothing</em> (a &#8220;zero pair&#8221;). To compute 3 + (&#8722;5), put out 3 plus-chips "
        "and 5 minus-chips and remove every pair that cancels:"))
    A(figure(signed_chips(3, 5), "3 plus-chips and 5 minus-chips. Three pairs cancel; two minus-chips remain &#8594; &#8722;2."))
    A(P("Both pictures agree: <b>(+3) + (&#8722;5) = &#8722;2</b>. Use whichever you like &#8212; the number line for "
        "movement, the chips for cancelling."))
    A(P("Two quick patterns fall out for free:"))
    A(steps([
        "<b>Same signs:</b> add the sizes, keep the sign. (&#8722;4) + (&#8722;3): four left then three more left = "
        "<b>&#8722;7</b>.",
        "<b>Different signs:</b> subtract the smaller size from the bigger, keep the sign of the bigger. "
        "(+8) + (&#8722;3): 8 beats 3 by 5, and 8 is positive &#8594; <b>+5</b>.",
    ]))
    A(figure(number_line(-8, 0, 1, [(-4, "+(-3)", SKY), (-7, "end", BERRY)]),
             "(&#8722;4) + (&#8722;3): start at &#8722;4, three more steps left &#8594; &#8722;7."))
    A(tryit("Compute (&#8722;6) + (+10) and (&#8722;2) + (&#8722;9).",
            "(&#8722;6) + (+10): different signs, 10 beats 6 by 4, positive wins &#8594; <b>+4</b>. "
            "(&#8722;2) + (&#8722;9): same sign, 2 + 9 = 11, both negative &#8594; <b>&#8722;11</b>."))

    A(H("Subtracting integers &#8212; the &#8220;add the opposite&#8221; secret"))
    A(P("Subtraction has a beautiful shortcut. <b>Subtracting a number is the same as adding its "
        "opposite.</b> In symbols: a &#8722; b = a + (&#8722;b). Why? Because &#8220;take away 5&#8221; and &#8220;add &#8722;5&#8221; move you the "
        "same way on the line &#8212; both walk 5 steps left."))
    A(example("(+4) &#8722; (+9) using add-the-opposite", steps([
        "Rewrite: (+4) &#8722; (+9) = (+4) + (&#8722;9).",
        "Now it's an addition. Different signs: 9 beats 4 by 5, and 9 is the negative one.",
        "So the answer is <b>&#8722;5</b>. (Check on the line: start at 4, walk 9 left, land on &#8722;5. &#10003;)",
    ])))
    A(figure(number_line(-6, 5, 1, [(4, "start", ORANGE), (-5, "end", BERRY)]),
             "(+4) &#8722; (+9) = (+4)+(&#8722;9): from 4, step 9 left, land on &#8722;5."))
    A(P("This is exactly why a thermometer dropping from 4&#176; by 9 degrees reads &#8722;5&#176;. The "
        "everyday word &#8220;drop&#8221; <em>is</em> subtraction, and the integer machine handles it without blinking."))
    A(tryit("Compute (&#8722;3) &#8722; (+7) and 6 &#8722; (&#8722;2). (Add the opposite each time.)",
            "(&#8722;3) &#8722; (+7) = (&#8722;3) + (&#8722;7) = <b>&#8722;10</b>.  6 &#8722; (&#8722;2) = 6 + (+2) = <b>+8</b> "
            "(subtracting a negative adds &#8212; that's the next big surprise!)."))

    A(H("&#129327; The big surprise: why two minuses make a plus"))
    A(kiwi("Everyone is <em>told</em> &#8220;minus times minus is plus&#8221; and &#8220;subtracting a negative adds.&#8221; "
           "But <em>why</em>? Let me show you, not just tell you. Two little stories, no memorising."))
    A(P("<b>Story 1 &#8212; the debt eraser.</b> Subtracting means &#8220;take away.&#8221; A negative number is a debt &#8212; "
        "something you <em>owe</em>. So <b>&#8722;(&#8722;2)</b> means &#8220;take away a &#8377;2 debt.&#8221; If I erase &#8377;2 of debt "
        "you owe, you are &#8377;2 <b>richer</b> &#8212; that's the same as <em>giving</em> you &#8377;2. So removing a "
        "negative is the same as adding a positive: 6 &#8722; (&#8722;2) = 6 + 2 = <b>8</b>."))
    A(figure(signed_chips(0, 2), "Two minus-chips = a debt of 2. Take them away and you've GAINED 2 &#8212; like adding +2."))
    A(P("<b>Story 2 &#8212; let the pattern force the answer.</b> Watch a staircase of subtractions where the "
        "second number drops by 1 each line. The answers must keep climbing by 1 &#8212; patterns don't suddenly "
        "break:"))
    A(figure(svg(
        '<text x="20" y="28" font-size="17" font-family="Georgia,serif" fill="#2b2622">5 &#8722; (&#43;2) = 3</text>'
        '<text x="20" y="54" font-size="17" font-family="Georgia,serif" fill="#2b2622">5 &#8722; (&#43;1) = 4</text>'
        '<text x="20" y="80" font-size="17" font-family="Georgia,serif" fill="#2b2622">5 &#8722; (&#160;&#160;0) = 5</text>'
        '<text x="20" y="106" font-size="17" font-family="Georgia,serif" fill="#E0556E" font-weight="800">5 &#8722; (&#8722;1) = 6</text>'
        '<text x="20" y="132" font-size="17" font-family="Georgia,serif" fill="#E0556E" font-weight="800">5 &#8722; (&#8722;2) = 7</text>'
        '<text x="220" y="40" font-size="13" fill="#8c8377">right side</text>'
        '<text x="220" y="58" font-size="13" fill="#8c8377">climbs by 1</text>'
        '<text x="220" y="76" font-size="13" fill="#8c8377">each step&#8230;</text>'
        '<text x="220" y="104" font-size="13" fill="#E0556E">so it MUST</text>'
        '<text x="220" y="122" font-size="13" fill="#E0556E">keep climbing!</text>',
        360, 150), "As the number being subtracted drops by 1, the answer rises by 1. The pattern forces 5&#8722;(&#8722;1)=6."))
    A(P("The pattern <em>forces</em> 5 &#8722; (&#8722;1) = 6 and 5 &#8722; (&#8722;2) = 7. Subtracting a negative adds. Both "
        "stories land in the same place: <b>two minus signs sitting together turn into a plus</b>."))
    A(kiwi("Keep this jingle: <b>&#8220;minus a minus is a plus.&#8221;</b> a &#8722; (&#8722;b) = a + b. You didn't memorise it &#8212; "
           "you watched it <em>have</em> to be true. That's real maths power. &#127881;"))
    A(example("simplify &#8722;12 + (&#8722;98) &#8722; (&#8722;84) + (&#8722;7)", steps([
        "Turn every subtraction into add-the-opposite: &#8722;12 + (&#8722;98) + (+84) + (&#8722;7).",
        "Gather the negatives: (&#8722;12) + (&#8722;98) + (&#8722;7) = &#8722;117.",
        "Add the positive: &#8722;117 + 84.",
        "Different signs: 117 beats 84 by 33, negative wins &#8594; <b>&#8722;33</b>.",
    ])))

    A(H("Climb the integer ladder"))
    A(practice("Remember", [
        ("Write the opposite of &#8722;15.", "+15."),
        ("What is |&#8722;23|?", "23 (distance from 0 is never negative)."),
        ("Is 0 positive, negative, or neither?", "Neither &#8212; it's the hinge in the middle."),
        ("On the number line, which is farther right: &#8722;9 or &#8722;2?", "&#8722;2 (bigger numbers sit farther right)."),
        ("Fill in &lt; or &gt;:  &#8722;6 ___ &#8722;1.", "&#8722;6 &lt; &#8722;1."),
    ]))
    A(practice("Understand", [
        ("Why is &#8722;5 less than &#8722;2 even though 5 &gt; 2?", "Because &#8722;5 is farther LEFT on the number line; "
         "the minus flips the order."),
        ("Rewrite 8 &#8722; (&#8722;3) as an addition, then solve.", "8 + (+3) = 11."),
        ("Rewrite (&#8722;4) &#8722; (+6) as an addition, then solve.", "(&#8722;4) + (&#8722;6) = &#8722;10."),
        ("Order from least to greatest: &#8722;3, 4, &#8722;10, 0, 2.", "&#8722;10 &lt; &#8722;3 &lt; 0 &lt; 2 &lt; 4."),
        ("True or false: |&#8722;7| &gt; |4|.", "True (7 &gt; 4)."),
    ]))
    A(practice("Apply", [
        ("A diver at &#8722;18 m rises 25 m. What's her new depth?", "&#8722;18 + 25 = +7 m (7 m ABOVE sea level &#8212; "
         "she has surfaced)."),
        ("The temperature is &#8722;3&#176;C and falls 6&#176;. Now what?", "&#8722;3 + (&#8722;6) = &#8722;9&#176;C."),
        ("Compute (&#8722;7) + (&#8722;8) + 20.", "(&#8722;15) + 20 = +5."),
        ("You owe &#8377;40 (that's &#8722;40) and pay back &#8377;25. What's your balance?", "&#8722;40 + 25 = &#8722;15 (you still owe &#8377;15)."),
        ("Evaluate 12 &#8722; 19 &#8722; (&#8722;4).", "12 + (&#8722;19) + (+4) = &#8722;3."),
    ]))
    A(practice("Analyze", [
        ("From the sum of 6 and 12, subtract the difference of &#8722;15 and &#8722;7. What's the result?",
         "Sum 6 + 12 = 18. Difference (&#8722;15) &#8722; (&#8722;7) = &#8722;15 + 7 = &#8722;8. Then 18 &#8722; (&#8722;8) = 18 + 8 = 26."),
        ("Two integers are opposites and their absolute values are 9. What could they be, and what's their sum?",
         "9 and &#8722;9; opposites always add to 0."),
        ("Find an integer x with |x| = 6 and x &lt; 0.", "x = &#8722;6."),
        ("Which is greater and by how much: (&#8722;5) + (&#8722;6) or (&#8722;2) &#8722; (+9)?",
         "(&#8722;5)+(&#8722;6) = &#8722;11. (&#8722;2)&#8722;(+9) = &#8722;11. They're EQUAL &#8212; neither is greater."),
    ]))
    A(practice("Create", [
        ("Invent a real-life story that ends at exactly &#8722;4 using one rise and one fall.",
         "E.g. start at +5&#176;, drop 9&#176; &#8594; &#8722;4&#176;. Or: in a lift, go up 2 then down 6 from floor 0 &#8594; &#8722;4."),
        ("Write three different integer additions that all equal &#8722;7.",
         "Many work: (&#8722;3)+(&#8722;4); (&#8722;10)+(+3); 0+(&#8722;7); (&#8722;12)+(+5)."),
        ("Build a subtraction of two negatives whose answer is positive, and check it on the line.",
         "E.g. (&#8722;2) &#8722; (&#8722;9) = &#8722;2 + 9 = +7. &#10003;"),
    ]))

    A(challenge(
        P("<b>The Magic Cross.</b> Place the five integers &#8722;2, &#8722;1, 0, 1, 2 into the five circles of a plus-"
          "shaped cross &#8212; one in the centre, four on the arms &#8212; so that the three numbers going "
          "<em>across</em> add to the <em>same</em> total as the three going <em>down</em>. "
          "What must the centre number be, and what is that equal total?") +
        figure(svg(
            '<circle cx="120" cy="40" r="22" fill="#FFF" stroke="#FF6F00" stroke-width="2"/>'
            '<circle cx="120" cy="100" r="22" fill="#FFF3E0" stroke="#FF6F00" stroke-width="2.6"/>'
            '<circle cx="120" cy="160" r="22" fill="#FFF" stroke="#FF6F00" stroke-width="2"/>'
            '<circle cx="60" cy="100" r="22" fill="#FFF" stroke="#FF6F00" stroke-width="2"/>'
            '<circle cx="180" cy="100" r="22" fill="#FFF" stroke="#FF6F00" stroke-width="2"/>'
            '<text x="120" y="106" font-size="20" text-anchor="middle" fill="#8c8377">?</text>',
            240, 200), "One centre, two arms across, two arms down &#8212; both lines share the centre.") +
        tryit("Think: what total can BOTH lines reach, using each number once?",
              "Put <b>0 in the centre</b>. Then the across pair and the down pair are {&#8722;2, 2} and {&#8722;1, 1} &#8212; "
              "each pair sums to 0 &#8212; so each whole line totals <b>0</b>. Beautiful: the opposites cancel and "
              "the magic total is 0. (Centre 0 is the only choice that lets both lines match, because the "
              "four arm-numbers split perfectly into two opposite pairs.) &#127881;")))

    A(kiwi("Outstanding! You now live on the <em>whole</em> number line &#8212; left of zero included. You can "
           "order integers, measure their distance from 0, and add &amp; subtract them by walking, by "
           "cancelling chips, or by add-the-opposite. Next we hunt for the hidden building blocks of "
           "numbers: <b>factors, primes, and the divisibility magic tricks</b>. &#128269;"))

    chapter("Part 1 · Number Sense & Integers", 2, "Meet the Integers",
            "Number Theory · Integers", "".join(b))
