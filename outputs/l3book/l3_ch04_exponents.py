#!/usr/bin/env python3
"""L3 Chapter 4 — Powers & Exponents (Number Theory · Powers). Builds from the
Chapter-3 idea of repeated multiplication: base/exponent, squares & cubes,
square roots of perfect squares, the laws of exponents DISCOVERED by the reader,
a^0 = 1, powers of 10, and the rice-on-a-chessboard explosion."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, array_dots, svg,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


def power_expand(base, exp):
    """Show base^exp = base x base x ... = value, as one tidy figure."""
    chain = " &#215; ".join([str(base)] * exp)
    val = base ** exp
    s = [f'<text x="40" y="46" font-size="30" font-family="Georgia,serif" fill="{ORANGE}" font-weight="800">{base}</text>',
         f'<text x="62" y="32" font-size="18" font-family="Georgia,serif" fill="{BERRY}" font-weight="800">{exp}</text>',
         f'<text x="92" y="46" font-size="20" fill="{INK}">= {chain}</text>',
         f'<text x="92" y="78" font-size="20" fill="{INK}">= <tspan font-weight="800" fill="{GRASS}">{val}</tspan></text>',
         f'<text x="40" y="104" font-size="13" fill="#8c8377">base {base}, exponent {exp} &#8212; &#8220;{base} to the power {exp}&#8221;</text>']
    return svg("".join(s), 460, 120)


def square_fig(n):
    """An n x n square of dots: a visual square number."""
    return array_dots(n, n, col=SKY)


def cube_stack(n):
    """A simple isometric-ish n x n x n cube hint with the value labelled."""
    s = [f'<rect x="40" y="46" width="100" height="100" fill="{PURPLE}22" stroke="{PURPLE}" stroke-width="2"/>',
         f'<polygon points="40,46 70,20 170,20 140,46" fill="{PURPLE}33" stroke="{PURPLE}" stroke-width="2"/>',
         f'<polygon points="140,46 170,20 170,120 140,146" fill="{PURPLE}18" stroke="{PURPLE}" stroke-width="2"/>']
    for k in range(1, n):
        s.append(f'<line x1="{40+k*100/n}" y1="46" x2="{40+k*100/n}" y2="146" stroke="{PURPLE}" stroke-width=".7" opacity=".5"/>')
        s.append(f'<line x1="40" y1="{46+k*100/n}" x2="140" y2="{46+k*100/n}" stroke="{PURPLE}" stroke-width=".7" opacity=".5"/>')
    s.append(f'<text x="200" y="92" font-size="18" fill="{PURPLE}" font-weight="800">{n}&#179; = {n**3}</text>')
    s.append(f'<text x="200" y="116" font-size="13" fill="#8c8377">{n}&#215;{n}&#215;{n} unit cubes</text>')
    return svg("".join(s), 320, 168)


def growth_bars(base, upto):
    """Tiny bar chart of base^1..base^upto to SHOW explosive growth."""
    vals = [base ** k for k in range(1, upto + 1)]
    mx = vals[-1]; bw = 40; gap = 18; x = 36; maxh = 130
    s = [f'<line x1="28" y1="{maxh+16}" x2="{36+upto*(bw+gap)}" y2="{maxh+16}" stroke="{INK}" stroke-width="2"/>']
    for i, v in enumerate(vals):
        h = max(3, v / mx * maxh); c = [SKY, GRASS, ORANGE, BERRY, PURPLE, GOLD][i % 6]
        s.append(f'<rect x="{x}" y="{maxh+16-h:.0f}" width="{bw}" height="{h:.0f}" fill="{c}99" stroke="{c}" stroke-width="1.6" rx="3"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{maxh+16-h-6:.0f}" font-size="11" text-anchor="middle" font-weight="800" fill="{c}">{v}</text>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{maxh+34:.0f}" font-size="12" text-anchor="middle" fill="{INK}">{base}<tspan font-size="9" dy="-6">{i+1}</tspan></text>')
        x += bw + gap
    return svg("".join(s), 36 + upto * (bw + gap) + 10, maxh + 44)


def build(chapter):
    b = []; A = b.append

    A(big_q("Fold a sheet of paper in half, then in half again, and again&#8230; If you could fold it just "
            "<b>42 times</b>, how thick would the stack be? A few centimetres? A metre? The real answer is "
            "<b>past the Moon</b>. That is the secret power of <em>doubling</em> &#8212; and by the end of this "
            "chapter you'll command it with a tiny raised number called an <b>exponent</b>."))
    A(kiwi("Hi again, explorer! &#9889; In Chapter 3 we multiplied the same prime again and again &#8212; like "
           "2 &#215; 2 &#215; 2. Writing all those is tiring. Mathematicians invented a beautiful shorthand: the "
           "<b>exponent</b>. It looks small but it is mighty. Let's build it from what you already know &#8212; "
           "plain multiplication."))

    # ── what is an exponent ──────────────────────────────
    A(H("Exponents: a shortcut for repeated multiplication"))
    A(P("Just as 4 &#215; 3 is shorthand for &#8216;add 4 three times,&#8217; an <b>exponent</b> is shorthand for "
        "&#8216;multiply the same number several times.&#8217; We write 2 &#215; 2 &#215; 2 as <b>2&#179;</b>. The big number "
        "is the <b>base</b> (what we multiply), the little raised number is the <b>exponent</b> or <b>power</b> "
        "(how many copies)."))
    A(figure(power_expand(2, 3), "2&#179; means three 2's multiplied: 2&#215;2&#215;2 = 8."))
    A(P("Careful &#8212; an exponent is <em>not</em> multiplication of the two numbers. 2&#179; is 8, <b>not</b> "
        "2 &#215; 3 = 6. The exponent only counts how many copies of the base to multiply."))
    A(figure(power_expand(3, 4), "3&#8308; = 3&#215;3&#215;3&#215;3 = 81 &#8212; four 3's, not 3&#215;4!"))
    A(example("write and evaluate &#8216;five to the power 3&#8217; and &#8216;ten to the power 4&#8217;", steps([
        "Five to the power 3 = 5&#179; = 5 &#215; 5 &#215; 5 = <b>125</b>.",
        "Ten to the power 4 = 10&#8308; = 10 &#215; 10 &#215; 10 &#215; 10 = <b>10,000</b>.",
        "Notice 10&#8308; is 1 followed by 4 zeros &#8212; powers of ten are wonderfully tidy. More on that soon.",
    ])))
    A(tryit("Write 7 &#215; 7 &#215; 7 &#215; 7 in exponent form and find its value.",
            "7&#8308; = <b>2,401</b>."))

    # ── squares & cubes ──────────────────────────────────
    A(H("Squares and cubes: powers you can SEE"))
    A(P("Two powers are so common they earned nicknames. <b>n&#178;</b> is read &#8216;n squared&#8217; &#8212; because "
        "n&#215;n is the number of dots in a real square. <b>n&#179;</b> is &#8216;n cubed&#8217; &#8212; the number of "
        "little cubes that fill a real cube."))
    A(figure(square_fig(5), "5&#178; = 5 rows of 5 = 25. A square number is literally a square!"))
    A(figure(cube_stack(3), "3&#179; = 3 layers of a 3&#215;3 square = 27 unit cubes."))
    A(P("The first few <b>perfect squares</b> are worth knowing by heart: 1, 4, 9, 16, 25, 36, 49, 64, 81, "
        "100. The first few <b>perfect cubes</b>: 1, 8, 27, 64, 125. (Did you spot that 64 is in <em>both</em> "
        "lists? 64 = 8&#178; = 4&#179; &#8212; a number can be a square and a cube at once!)"))
    A(tryit("What is 6&#178;, and what is 4&#179;? Which is bigger?",
            "6&#178; = 36, 4&#179; = 64. <b>4&#179; is bigger</b> &#8212; cubing grows faster than squaring."))

    # ── square roots ─────────────────────────────────────
    A(H("Square roots: undoing the square"))
    A(P("If squaring takes 7 to 49, the <b>square root</b> goes back: it asks &#8216;what number, squared, gives "
        "this?&#8217; We write it &#8730;49 = 7, because 7&#178; = 49. Square-rooting is the <em>opposite</em> of "
        "squaring, the way subtraction undoes addition."))
    A(figure(svg(
        '<text x="60" y="50" font-size="22" font-family="Georgia,serif" fill="#3B9CE6" font-weight="800">7</text>'
        '<path d="M90,40 C140,18 200,18 250,40" fill="none" stroke="#FF6F00" stroke-width="2.2" marker-end="url(#ar)"/>'
        '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L7,3 L0,6 Z" fill="#FF6F00"/></marker></defs>'
        '<text x="170" y="22" font-size="13" text-anchor="middle" fill="#FF6F00">square (&#215;7)</text>'
        '<text x="270" y="50" font-size="22" font-family="Georgia,serif" fill="#E0556E" font-weight="800">49</text>'
        '<path d="M250,70 C200,92 140,92 92,70" fill="none" stroke="#39A85B" stroke-width="2.2" marker-end="url(#ar2)"/>'
        '<defs><marker id="ar2" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L7,3 L0,6 Z" fill="#39A85B"/></marker></defs>'
        '<text x="170" y="96" font-size="13" text-anchor="middle" fill="#39A85B">&#8730; (square root)</text>',
        340, 110), "Squaring and square-rooting are a there-and-back-again pair."))
    A(P("To find a square root of a <b>perfect square</b>, hunt for the number that makes it. Knowing your "
        "squares makes this instant: &#8730;81 = 9, &#8730;144 = 12. A neat trick uses prime factorization: pair "
        "up the primes and take one from each pair."))
    A(example("find &#8730;324 using prime factorization", steps([
        "324 = 4 &#215; 81 = 2&#178; &#215; 3&#8308;.",
        "Make pairs: (2&#215;2) and (3&#215;3) and (3&#215;3).",
        "Take one number from each pair: 2 &#215; 3 &#215; 3 = 18.",
        "So &#8730;324 = <b>18</b>. Check: 18&#178; = 324. &#10003;",
    ])))
    A(tryit("Find &#8730;196.",
            "196 = 14 &#215; 14, so &#8730;196 = <b>14</b>. (Or 196 = 2&#178;&#215;7&#178;, take 2&#215;7 = 14.)"))

    # ── DISCOVER the laws ────────────────────────────────
    A(H("&#128270; Discover the laws of exponents yourself"))
    A(kiwi("I won't hand you the rules &#8212; let's <em>discover</em> them. Whenever a power puzzle looks hard, "
           "blow it up into its copies, count, and the rule reveals itself. Watch."))
    A(P("<b>Discovery 1 &#8212; multiplying powers of the same base.</b> What is 2&#179; &#215; 2&#178;? Expand both:"))
    A(figure(svg(
        '<text x="20" y="38" font-size="18" font-family="Georgia,serif" fill="#2b2622">2&#179; &#215; 2&#178; = (2&#215;2&#215;2) &#215; (2&#215;2)</text>'
        '<text x="20" y="68" font-size="18" font-family="Georgia,serif" fill="#2b2622">= 2&#215;2&#215;2&#215;2&#215;2 = 2<tspan font-size="12" dy="-7">5</tspan></text>'
        '<text x="300" y="68" font-size="14" fill="#E0556E" font-weight="800">3 + 2 = 5!</text>',
        460, 90), "Three 2's times two 2's = five 2's. The exponents ADD."))
    A(P("You just discovered the <b>product rule</b>: <b>a<sup>m</sup> &#215; a<sup>n</sup> = a<sup>m+n</sup></b> "
        "&#8212; same base, add the exponents. It <em>has</em> to work, because you're just counting copies."))
    A(P("<b>Discovery 2 &#8212; a power of a power.</b> What is (2&#179;)&#178;? That means 2&#179; multiplied by "
        "itself, twice:"))
    A(figure(svg(
        '<text x="20" y="38" font-size="18" font-family="Georgia,serif" fill="#2b2622">(2&#179;)&#178; = 2&#179; &#215; 2&#179; = (2&#215;2&#215;2)&#215;(2&#215;2&#215;2)</text>'
        '<text x="20" y="68" font-size="18" font-family="Georgia,serif" fill="#2b2622">= 2<tspan font-size="12" dy="-7">6</tspan></text>'
        '<text x="120" y="68" font-size="14" fill="#E0556E" font-weight="800">3 &#215; 2 = 6!</text>',
        470, 90), "Two groups of three 2's = six 2's. The exponents MULTIPLY."))
    A(P("That's the <b>power-of-a-power rule</b>: <b>(a<sup>m</sup>)<sup>n</sup> = a<sup>m&#215;n</sup></b>. "
        "Multiplying powers adds; powering a power multiplies. Count copies and you can never mix them up."))
    A(P("<b>Discovery 3 &#8212; dividing powers.</b> What is 2&#8309; &#247; 2&#178;? Cross out the matching 2's:"))
    A(figure(svg(
        '<text x="20" y="40" font-size="18" font-family="Georgia,serif" fill="#2b2622">2<tspan font-size="12" dy="-7">5</tspan><tspan dy="7"> &#247; 2&#178; = </tspan></text>'
        '<text x="150" y="30" font-size="15" font-family="Georgia,serif" fill="#2b2622">2&#215;2&#215;2&#215;2&#215;2</text>'
        '<line x1="150" y1="46" x2="270" y2="46" stroke="#2b2622" stroke-width="1.4"/>'
        '<text x="186" y="62" font-size="15" font-family="Georgia,serif" fill="#2b2622">2&#215;2</text>'
        '<text x="290" y="44" font-size="18" font-family="Georgia,serif" fill="#39A85B" font-weight="800">= 2&#179;</text>'
        '<text x="290" y="66" font-size="13" fill="#E0556E" font-weight="800">5 &#8722; 2 = 3</text>',
        420, 84), "Two 2's on top and bottom cancel, leaving three. The exponents SUBTRACT."))
    A(P("So the <b>quotient rule</b>: <b>a<sup>m</sup> &#247; a<sup>n</sup> = a<sup>m&#8722;n</sup></b>. "
        "Now a real surprise pops out for free. What is 2&#179; &#247; 2&#179;? By the rule it's 2<sup>3&#8722;3</sup> "
        "= 2&#8304;. But any number divided by itself is <b>1</b>. So 2&#8304; must equal 1!"))
    A(figure(svg(
        '<text x="30" y="40" font-size="18" font-family="Georgia,serif" fill="#2b2622">2&#179; &#247; 2&#179; = 2<tspan font-size="12" dy="-7">3&#8722;3</tspan><tspan dy="7"> = 2&#8304;</tspan></text>'
        '<text x="30" y="72" font-size="18" font-family="Georgia,serif" fill="#2b2622">but 8 &#247; 8 = 1, so&#8230;</text>'
        '<text x="260" y="58" font-size="22" font-family="Georgia,serif" fill="#FF6F00" font-weight="800">2&#8304; = 1</text>',
        420, 96), "Anything (except 0) to the power 0 equals 1 &#8212; forced by the division rule."))
    A(kiwi("Mind-bending but true: <b>a&#8304; = 1</b> for every non-zero number a. So 5&#8304; = 1, 99&#8304; = 1, "
           "even 2,450&#8304; = 1. It isn't a random rule someone made up &#8212; the division law <em>forces</em> it. "
           "(That's why a tricky exam option &#8216;2450&#8304;&#8217; equals 1, not 0!)"))
    A(example("evaluate 1&#8304; + 2&#8304; + 3&#8304; + 4&#8304; + 5&#8304; (source-PDF puzzle)", steps([
        "Each term is a non-zero number to the power 0, so each equals 1.",
        "1 + 1 + 1 + 1 + 1 = <b>5</b>.",
        "Surprise: the bases 1,2,3,4,5 don't matter at all once the exponent is 0!",
    ])))
    A(example("simplify (3&#178;)&#179; &#247; 3&#8308;", steps([
        "Power of a power: (3&#178;)&#179; = 3<sup>2&#215;3</sup> = 3&#8310;.",
        "Now divide: 3&#8310; &#247; 3&#8308; = 3<sup>6&#8722;4</sup> = 3&#178;.",
        "3&#178; = <b>9</b>. (We never had to compute 729 &#247; 81 &#8212; the laws did the heavy lifting.)",
    ])))
    A(tryit("Use the laws: 4&#178; &#215; 4&#179; = ? and (10&#178;)&#178; = ?",
            "4&#178;&#215;4&#179; = 4&#8309; = <b>1024</b>. (10&#178;)&#178; = 10&#8308; = <b>10,000</b>."))

    # ── powers of 10 ─────────────────────────────────────
    A(H("Powers of 10: the tidiest powers of all"))
    A(P("Our whole number system is built on tens, so powers of 10 are the friendliest. The exponent simply "
        "counts the zeros:"))
    A(figure(svg(
        '<text x="20" y="30" font-size="15" font-family="Georgia,serif" fill="#2b2622">10&#185; = 10</text>'
        '<text x="20" y="56" font-size="15" font-family="Georgia,serif" fill="#2b2622">10&#178; = 100</text>'
        '<text x="20" y="82" font-size="15" font-family="Georgia,serif" fill="#2b2622">10&#179; = 1,000</text>'
        '<text x="20" y="108" font-size="15" font-family="Georgia,serif" fill="#2b2622">10&#8308; = 10,000</text>'
        '<text x="220" y="56" font-size="14" fill="#FF6F00" font-weight="800">exponent = number</text>'
        '<text x="220" y="76" font-size="14" fill="#FF6F00" font-weight="800">of zeros!</text>',
        420, 124), "10 raised to n is just 1 followed by n zeros."))
    A(P("This lets us write giant (or tiny) numbers compactly &#8212; called <b>standard form</b>. The Sun is "
        "about 150,000,000 km away; we write that as 1.5 &#215; 10&#8312;. Each step up the power of ten makes the "
        "number <em>ten times</em> bigger &#8212; which is exactly why the next section is so explosive."))
    A(tryit("Write 1,000,000 as a power of 10. How many zeros?",
            "1,000,000 = 10&#8310; (one million = 6 zeros)."))

    # ── THE SURPRISE: rice on a chessboard ───────────────
    A(H("&#127881; The surprise: rice on a chessboard"))
    A(P("Legend says a clever inventor showed a king a new game on a 64-square board. The king offered any "
        "reward. The inventor asked for something that sounded humble: <b>1 grain of rice on the first square, "
        "2 on the next, 4 on the next, doubling each square</b> to the 64th. The king laughed and agreed. "
        "Big mistake. Each square is a power of 2:"))
    A(figure(growth_bars(2, 6), "Squares 1&#8211;6 hold 2&#8304;..2&#8309; = 1, 2, 4, 8, 16, 32 grains. Already racing upward."))
    A(P("By square 11 you owe 1,024 grains; by square 21, over a million; by square 41, over a trillion. The "
        "final square alone, 2&#8310;&#179;, is more than nine <em>quintillion</em> grains. The whole board totals "
        "about <b>18,446,744,073,709,551,615</b> grains &#8212; more rice than the planet has ever grown. The king "
        "could never pay."))
    A(figure(svg(
        '<text x="190" y="28" font-size="14" text-anchor="middle" font-weight="800" fill="#FF6F00">Doubling is a rocket</text>'
        '<text x="20" y="56" font-size="13" font-family="Georgia,serif" fill="#2b2622">square 10: 2&#8313; = 512</text>'
        '<text x="20" y="80" font-size="13" font-family="Georgia,serif" fill="#2b2622">square 21: 2&#178;&#8304; &#8776; 1 million</text>'
        '<text x="20" y="104" font-size="13" font-family="Georgia,serif" fill="#2b2622">square 41: 2&#8308;&#8304; &#8776; 1 trillion</text>'
        '<text x="20" y="128" font-size="13" font-family="Georgia,serif" fill="#E0556E" font-weight="800">square 64: 2&#8310;&#179; &#8776; 9.2 quintillion</text>',
        380, 144), "A tiny base (2) with a growing exponent leaves any ordinary number in the dust."))
    A(kiwi("This is why exponents matter so much: they grow <b>impossibly fast</b>. The paper folded 42 times "
           "is 2&#8308;&#178; sheets thick &#8212; past the Moon &#8212; for the same reason. When you see a small base with "
           "a climbing exponent, expect an explosion. That instinct is a real mathematician's superpower. "
           "&#128640;"))

    # ── BLOOM LADDER ─────────────────────────────────────
    A(H("Climb the powers ladder"))
    A(practice("Remember", [
        ("In 5&#8308;, name the base and the exponent.", "Base 5, exponent 4."),
        ("What is 2&#179;?", "8."),
        ("What does any non-zero number to the power 0 equal?", "1."),
        ("What is &#8730;64?", "8 (because 8&#178; = 64)."),
        ("Write 10&#179; as an ordinary number.", "1,000."),
    ]))
    A(practice("Understand", [
        ("Is 3&#178; the same as 2&#179;? Show both.", "No: 3&#178; = 9 but 2&#179; = 8 &#8212; order matters."),
        ("Write 6 &#215; 6 &#215; 6 &#215; 6 &#215; 6 in exponent form.", "6&#8309;."),
        ("Evaluate 4&#178; + 3&#179;.", "16 + 27 = 43."),
        ("Find &#8730;121.", "11."),
        ("Which is greater: 2&#8308; or 4&#178;?", "Equal &#8212; both are 16."),
    ]))
    A(practice("Apply", [
        ("Use the product rule: 5&#179; &#215; 5&#178;.", "5&#8309; = 3,125."),
        ("Use the power rule: (2&#178;)&#8308;.", "2&#8312; = 256."),
        ("Simplify 7&#8309; &#247; 7&#179;.", "7&#178; = 49."),
        ("Evaluate 10 + 2&#8304; + 3&#8304;.", "10 + 1 + 1 = 12."),
        ("A bacterium splits in two every hour. Starting from 1, how many after 6 hours?", "2&#8310; = 64."),
    ]))
    A(practice("Analyze", [
        ("Which power of 8 equals 2&#8310;? (Hint: 8 = 2&#179;.)", "8 = 2&#179;, so 8&#178; = 2&#8310;. The answer is 2 (8&#178; = 64 = 2&#8310;)."),
        ("Is 3&#185;&#178; greater than 6&#8310;? Explain using powers of small primes.",
         "6&#8310; = (2&#215;3)&#8310; = 2&#8310;&#215;3&#8310;. Compare to 3&#185;&#178; = 3&#8310;&#215;3&#8310;. Since 3&#8310; &gt; 2&#8310;, 3&#185;&#178; &gt; 6&#8310;."),
        ("Find the smallest whole number n with 2&#8319; greater than 1000.", "2&#185;&#8304; = 1024 &gt; 1000, and 2&#8313; = 512 &lt; 1000, so n = 10."),
        ("64 is both a perfect square and a perfect cube. Write it as a square and as a cube.", "64 = 8&#178; = 4&#179;."),
    ]))
    A(practice("Create", [
        ("Invent a doubling story (like the rice) where day 1 starts at 1 and you want it to pass 1,000. On which day does it happen?",
         "Doubling 1,2,4,...: 2&#185;&#8304; = 1024 on day 11 (since you start at 2&#8304;=1 on day 1, day n holds 2<sup>n&#8722;1</sup>)."),
        ("Write three different powers that all equal 64.", "8&#178;, 4&#179;, 2&#8310; (and 64&#185;)."),
        ("Make a true equation using the product rule with base 3 whose answer is 3&#8311;.",
         "Many: 3&#179;&#215;3&#8308;, or 3&#178;&#215;3&#8309;, or 3&#185;&#215;3&#8310; (exponents add to 7)."),
    ]))

    # ── CHALLENGE ────────────────────────────────────────
    A(challenge(
        P("<b>The Last Digit Detective.</b> Powers of 3 march like this: 3&#185; = 3, 3&#178; = 9, 3&#179; = 27, "
          "3&#8308; = 81, 3&#8309; = 243, 3&#8310; = 729&#8230; Stare only at the <em>last digit</em> of each: 3, 9, 7, 1, 3, 9, 7, 1, "
          "&#8230; Without computing the gigantic number, can you find the <b>last digit of 3&#178;&#8304;</b>?") +
        tryit("Hint: the last digits repeat in a cycle. How long is the cycle?",
              "The last digits cycle through <b>3, 9, 7, 1</b> &#8212; a pattern of length 4 &#8212; and then repeat forever. "
              "So to find the last digit of 3&#178;&#8304;, divide the exponent by 4: 20 &#247; 4 = 5 with remainder <b>0</b>. "
              "A remainder of 0 means we're at the <em>end</em> of a cycle &#8212; the 4th position &#8212; whose last digit is "
              "<b>1</b>. (Check the pattern: 3&#8308; ends in 1, 3&#8312; ends in 1, &#8230; every multiple of 4 does.) "
              "So 3&#178;&#8304; ends in <b>1</b>, found without ever writing the 10-digit monster. You just used cycles &#8212; a "
              "true olympiad trick! &#127881;")))

    A(kiwi("Phenomenal! You can now read and write powers, square and cube and un-square numbers, wield the "
           "exponent laws by counting copies, and you've felt how explosively powers grow. That completes "
           "Part 1 &#8212; you've mastered the building blocks of number. Next we turn to <b>parts of a whole</b>: "
           "fractions, decimals and the powerful percent. See you there! &#127809;"))

    chapter("Part 1 · Number Sense & Integers", 4, "Powers & Exponents",
            "Number Theory · Powers", "".join(b))
