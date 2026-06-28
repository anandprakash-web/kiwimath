#!/usr/bin/env python3
"""L3 Chapter 10 — Vedic Speed Maths (Arithmetic · Speed Magic). The showpiece
"surprise" chapter: ×11, squaring numbers ending in 5, same-tens/units-add-to-10,
Nikhilam near a base of 100, all-from-9 subtraction, ×5/×25/×9/×99, the 9-check
for catching mistakes, and a peek at vertically-&-crosswise. Each trick is a
"watch this magic" hook, then the SECRET (why it works via place value / algebra).
Every single number is Python-verified before it was written down."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


# ── tiny inline SVG figures, hand-built for this chapter ─────────────────────
def _t(x, y, s, size=14, col=INK, anchor="middle", w=700):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{w}" fill="{col}">{s}</text>'


def fig_eleven(t, s):
    """×11 'drop the digits apart, put their SUM in the middle'."""
    mid = t + s
    defs = (f'<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="6" refY="3" '
            f'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{GRASS}"/></marker></defs>')
    inner = [
        _t(58, 58, str(t), 48, SKY, w=800),
        _t(402, 58, str(s), 48, BERRY, w=800),
        f'<rect x="176" y="22" width="108" height="58" rx="12" fill="{ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
        _t(230, 62, str(mid), 38, "#ffffff", w=800),
        f'<path d="M100,46 C140,24 168,24 196,38" fill="none" stroke="{GRASS}" stroke-width="2.4" marker-end="url(#ar)"/>',
        f'<path d="M360,46 C320,24 292,24 264,38" fill="none" stroke="{GRASS}" stroke-width="2.4" marker-end="url(#ar)"/>',
        _t(230, 102, f'the SUM&#160; {t}+{s}={mid}', 13, GRASS),
    ]
    return svg(defs + "".join(inner), 460, 116)


def fig_twobox(label, lcol, ltxt, rtxt, lsub, rsub, result):
    """Generic 'front | back' two-chip figure (used for the same-tens trick)."""
    inner = [
        _t(70, 50, label, 30, lcol, anchor="start", w=800),
        f'<rect x="210" y="20" width="78" height="48" rx="10" fill="{GRASS}" stroke="{GRASS}" stroke-width="2"/>',
        _t(249, 53, ltxt, 26, "#ffffff", w=800),
        f'<rect x="296" y="20" width="78" height="48" rx="10" fill="{ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
        _t(335, 53, rtxt, 26, "#ffffff", w=800),
        _t(249, 88, lsub, 12, GRASS),
        _t(335, 88, rsub, 12, ORANGE),
        _t(392, 50, result, 20, INK, anchor="start", w=800),
    ]
    return svg("".join(inner), 470, 102)


def fig_base100(a, b):
    """Nikhilam base-100 deficit diagram."""
    da, db = 100 - a, 100 - b
    cross = a - db                      # = 100 − da − db
    prod = da * db
    prodtxt = f'{prod:02d}' if prod < 100 else str(prod)
    inner = [
        _t(95, 24, "BASE&#160;&#160;100", 13, GOLD, w=800),
        _t(70, 66, str(a), 32, SKY, w=800),
        _t(70, 98, f'&#8722;{da}', 22, BERRY, w=800),
        _t(150, 66, str(b), 32, SKY, w=800),
        _t(150, 98, f'&#8722;{db}', 22, BERRY, w=800),
        f'<line x1="98" y1="78" x2="138" y2="94" stroke="{PURPLE}" stroke-width="2.2"/>',
        f'<line x1="138" y1="78" x2="98" y2="94" stroke="{PURPLE}" stroke-width="2.2"/>',
        _t(212, 72, "&#8594;", 30, INK, w=800),
        f'<rect x="250" y="46" width="60" height="46" rx="10" fill="{GRASS}" stroke="{GRASS}" stroke-width="2"/>',
        f'<rect x="320" y="46" width="72" height="46" rx="10" fill="{ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
        _t(280, 79, str(cross), 26, "#ffffff", w=800),
        _t(356, 79, prodtxt, 24, "#ffffff", w=800),
        _t(280, 110, "cross &#8722;", 12, GRASS),
        _t(356, 110, f'{da}&#215;{db}', 12, ORANGE),
    ]
    return svg("".join(inner), 404, 122)


def fig_allfrom9(big, sub):
    """All-from-9, last-from-10 subtraction strip for big - sub."""
    ds = str(sub)
    n = len(ds)
    res = str(big - sub).rjust(n, "0")
    inner = [_t(60, 40, f"{big} &#8722; {sub}", 24, SKY, anchor="start", w=800)]
    x0 = 60
    for i, d in enumerate(ds):
        x = x0 + i * 92
        last = (i == n - 1)
        sub_lbl = f'10&#8722;{d}' if last else f'9&#8722;{d}'
        inner.append(_t(x, 96, sub_lbl, 16, BERRY if last else INK, anchor="start"))
        inner.append(_t(x + 18, 70, res[i], 26, GOLD if last else GRASS, w=800))
    inner.append(_t(x0 + n * 92 + 10, 70, f"&#8594; {big - sub}", 20, INK, anchor="start", w=800))
    return svg("".join(inner), x0 + n * 92 + 130, 112)


def fig_ninecheck(num):
    """Digit-sum 'funnel' down to a single check digit."""
    f = abs(num)
    chain = [f]
    while f >= 10:
        f = sum(int(x) for x in str(f))
        chain.append(f)
    x = 44
    inner = [_t(x, 42, str(num), 26, SKY, anchor="start", w=800)]
    span = len(str(num)) * 16
    inner.append(_t(x + span / 2, 66, "add digits", 11, INK))
    px = x + span + 40
    for i, v in enumerate(chain[1:], 1):
        last = (i == len(chain) - 1)
        col = GOLD if last else GRASS
        inner.append(_t(px - 20, 42, "&#8594;", 22, INK, w=800))
        inner.append(_t(px + 22, 42, str(v), 26, col, w=800))
        inner.append(_t(px + 22, 66, "check digit" if last else "add again", 11, GOLD if last else INK))
        px += 92
    return svg("".join(inner), max(px, 360), 84)


def fig_cross(a, b, c, d):
    """Vertically-&-crosswise cross diagram for (10a+b)(10c+d)."""
    y1, y2 = 58, 116
    xa, xb = 160, 290
    inner = [
        _t(225, 24, "&#215; = cross-multiply, then ADD the two crosses", 12, ORANGE, w=700),
        _t(xa, y1, str(a), 34, SKY, w=800),
        _t(xb, y1, str(b), 34, SKY, w=800),
        _t(xa, y2, str(c), 34, BERRY, w=800),
        _t(xb, y2, str(d), 34, BERRY, w=800),
        f'<line x1="{xb}" y1="{y1+10}" x2="{xb}" y2="{y2-26}" stroke="{GRASS}" stroke-width="2.6"/>',
        f'<line x1="{xa}" y1="{y1+10}" x2="{xa}" y2="{y2-26}" stroke="{GRASS}" stroke-width="2.6"/>',
        f'<line x1="{xa+12}" y1="{y1+10}" x2="{xb-12}" y2="{y2-26}" stroke="{ORANGE}" stroke-width="2.6"/>',
        f'<line x1="{xb-12}" y1="{y1+10}" x2="{xa+12}" y2="{y2-26}" stroke="{ORANGE}" stroke-width="2.6"/>',
        _t(xb + 58, 88, "units", 13, GRASS),
        _t(xa - 52, 88, "left", 13, GRASS),
    ]
    return svg("".join(inner), 440, 140)


# ───────────────────────────────────────────────────────────────────────────
def build(chapter):
    b = []
    A = b.append

    A(big_q("Pick any two-digit number and multiply it by 11 — in your head, in <em>one second</em>, "
            "before a calculator could even switch on. Impossible? By the end of this page you'll do it. "
            "By the end of this chapter you'll square numbers, multiply near-100s, and subtract from a "
            "thousand faster than anyone in the room — and you'll know the <b>secret</b> behind every "
            "trick, so it's real maths, not memorised hocus-pocus."))
    A(kiwi("Ta-da! 🎩✨ Today I'm <b>Kiwi the Math Magician</b>. Long ago in India, mathematicians found "
           "lightning-fast ways to calculate — collected into a system people call <b>Vedic Maths</b>. "
           "Here's my promise: every trick looks like magic, but underneath it is something you already "
           "know — <b>place value</b> and a little <b>algebra</b>. A real magician knows how the trick "
           "works. So for each one we'll do the magic… <em>then</em> I'll show you the secret. Roll up "
           "your sleeves!"))

    # ── TRICK 1: ×11 ────────────────────────────────────────────────────────
    A(H("🔮 Trick 1 — Times eleven, in one second"))
    A(P("Watch this magic: <b>35 × 11</b>. I split the digits 3 and 5 apart, add them to get the "
        "middle, and… <b>385</b>. Done."))
    A(figure(fig_eleven(3, 5), "35 × 11 → 3, then (3+5), then 5 → 385"))
    A(example("35 × 11", steps([
        "Pull the two digits apart and leave a gap: &#160;3 &#160;_&#160; 5.",
        "Add the two digits and drop the answer into the gap: 3 + 5 = <b>8</b>.",
        "Read it straight off: 3&#160;<b>8</b>&#160;5 = <b>385</b>. (Check: 35 × 11 = 385. ✓)",
    ])))
    A(P("But what if the middle sum is <b>10 or more</b>? Then we just <b>carry</b>, exactly like normal "
        "adding. Try <b>76 × 11</b>:"))
    A(figure(fig_eleven(7, 6), "76 × 11 → 7, (7+6)=13, 6 → carry the 1 → 836"))
    A(example("76 × 11 (with a carry)", steps([
        "Outer digits: 7 _ 6.",
        "Middle: 7 + 6 = <b>13</b> — that's two digits, too big for one slot.",
        "Keep the 3, <b>carry the 1</b> left onto the 7: 7 + 1 = 8.",
        "Read it: <b>8</b>&#160;3&#160;6 = <b>836</b>. (Check: 76 × 11 = 836. ✓)",
    ])))
    A(kiwi("🔑 <b>The secret.</b> Eleven is just <b>10 + 1</b>. So 35 × 11 = 35 × 10 + 35 × 1 = "
           "350 + 35. Stack those and add:<br>&#160;&#160;&#160;3 5 0<br>+&#160;&#160;&#160;&#160;3 5<br>"
           "The ones place is the last digit (5). The hundreds place is the first digit (3). And the "
           "tens place gets <b>both</b> digits added together — that's why the middle is the SUM! Place "
           "value did the magic; I just skipped the writing."))
    A(P("It even works on <b>3-digit</b> numbers — add each <em>neighbouring pair</em>. Try "
        "<b>352 × 11</b>: write 3, then (3+5), then (5+2), then 2 → 3&#160;8&#160;7&#160;2 = "
        "<b>3872</b>. (Check ✓)"))
    A(tryit("Do 23 × 11 and 52 × 11 in your head.",
            "23 × 11 = 2&#160;(2+3)&#160;3 = <b>253</b>. &#160; 52 × 11 = 5&#160;(5+2)&#160;2 = <b>572</b>."))
    A(tryit("A carry one: 48 × 11.",
            "4 _ 8, middle 4+8 = 12 → keep 2, carry 1 → 5&#160;2&#160;8 = <b>528</b>."))
    A(tryit("🎂 Try it on YOUR birth year! e.g. 2014 × 11.",
            "2, (2+0), (0+1), (1+4), 4 = 2&#160;2&#160;1&#160;5&#160;4 = <b>22,154</b>. "
            "(Carry whenever a pair adds to 10 or more.)"))

    # ── TRICK 2: squaring numbers ending in 5 ───────────────────────────────
    A(H("🔮 Trick 2 — Square any number ending in 5"))
    A(P("Magic: I can square <b>65</b> instantly. <b>4225</b>. Watch <b>how</b>: take the part before "
        "the 5 (that's 6), multiply it by the <em>next</em> number up (7), and just stick <b>25</b> on "
        "the end. 6 × 7 = 42, then 25 → <b>4225</b>."))
    A(example("65² ", steps([
        "Front part = 6. Next number up = 7.",
        "Multiply them: 6 × 7 = <b>42</b>.",
        "Write <b>25</b> after it: 42 | 25 = <b>4225</b>. (Check: 65 × 65 = 4225. ✓)",
    ])))
    A(example("115² (works for big ones too)", steps([
        "Front part = 11. Next up = 12.",
        "11 × 12 = <b>132</b>.",
        "Tack on 25: 132 | 25 = <b>13225</b>. (Check: 115² = 13225. ✓)",
    ])))
    A(kiwi("🔑 <b>The secret (a touch of algebra).</b> Any number ending in 5 is "
           "<b>10n + 5</b> (for 65, n = 6). Square it:<br>"
           "(10n + 5)² = 100n² + 100n + 25 = <b>100 × n × (n+1) + 25</b>.<br>"
           "The “× 100” pushes n(n+1) into the hundreds — so n(n+1) becomes the <em>front</em> of the "
           "answer, and the lonely <b>+25</b> is always the last two digits. That's the whole trick, "
           "hiding inside one line of algebra!"))
    A(tryit("Square 25 and 45 with the trick.",
            "25² = (2×3)|25 = 6|25 = <b>625</b>. &#160; 45² = (4×5)|25 = 20|25 = <b>2025</b>."))
    A(tryit("Square 85.",
            "8 × 9 = 72, then 25 → <b>7225</b>."))
    A(tryit("Square 95 — then peek ahead and square 105.",
            "95² = (9×10)|25 = <b>9025</b>. &#160; 105² = (10×11)|25 = 110|25 = <b>11025</b>."))

    # ── TRICK 3: same tens, units add to 10 ─────────────────────────────────
    A(H("🔮 Trick 3 — Same tens, and the ones add to 10"))
    A(P("This one feels like mind-reading. <b>43 × 47</b>. Both start with 4, and the ones (3 and 7) "
        "add up to 10. So: 4 × (4+1) = 20 for the front, 3 × 7 = 21 for the back → <b>2021</b>."))
    A(figure(fig_twobox("43 &#215; 47", SKY, "20", "21", "4&#215;5", "3&#215;7", "= 2021"),
             "43 × 47 → (4×5) | (3×7) → 20 | 21 → 2021"))
    A(example("62 × 68", steps([
        "Same tens (6 and 6). Ones: 2 + 8 = 10. ✓ Trick applies.",
        "Front: 6 × (6+1) = 6 × 7 = <b>42</b>.",
        "Back: 2 × 8 = <b>16</b> (keep two digits!).",
        "Join: 42 | 16 = <b>4216</b>. (Check: 62 × 68 = 4216. ✓)",
    ])))
    A(P("Careful: the back part is always <b>two digits</b>. For 21 × 29 the back is 1 × 9 = 9, written "
        "as <b>09</b>: front 2 × 3 = 6, so 6 | 09 = <b>609</b>. (Check ✓)"))
    A(kiwi("🔑 <b>The secret.</b> Write the numbers as 10a + b and 10a + c, where the tens match (both a) "
           "and the ones add to ten (b + c = 10). Multiply out:<br>"
           "(10a + b)(10a + c) = 100a² + 10a(b + c) + bc.<br>"
           "Since b + c = 10, the middle term is 10a × 10 = 100a. So the first two terms are "
           "100a² + 100a = <b>100 × a × (a+1)</b> — that's the front part, a(a+1), pushed into the "
           "hundreds. And <b>bc</b> is the back. Same shape as Trick 2 — in fact Trick 2 is just this "
           "trick when b = c = 5!"))
    A(tryit("Try 84 × 86 and 91 × 99.",
            "84 × 86 = (8×9)|(4×6) = 72|24 = <b>7224</b>. &#160; 91 × 99 = (9×10)|(1×9) = 90|09 = <b>9009</b>."))
    A(tryit("Which of these fits the trick: 33 × 37, &#160;33 × 36, &#160;76 × 74?",
            "33 × 37 fits (3=3, 3+7=10) → 12|21 = <b>1221</b>. &#160; 76 × 74 fits (7=7, 6+4=10) → "
            "56|24 = <b>5624</b>. &#160; 33 × 36 does <em>not</em> (3+6 = 9, not 10)."))

    # ── TRICK 4: Nikhilam near a base of 100 ────────────────────────────────
    A(H("🔮 Trick 4 — Multiplying near 100 (the deficit trick)"))
    A(P("Now for numbers hugging 100. <b>97 × 96</b>. Each one is a little <em>short</em> of 100: 97 is "
        "3 short, 96 is 4 short. Cross-subtract a deficit (97 − 4 = 93, or the same 96 − 3 = 93) for the "
        "front, multiply the deficits (3 × 4 = 12) for the back → <b>9312</b>."))
    A(figure(fig_base100(97, 96), "97 × 96 → front 97−4 = 93, back 3 × 4 = 12 → 9312"))
    A(example("97 × 96", steps([
        "Deficits from 100: &#160;100 − 97 = 3, &#160;100 − 96 = 4.",
        "Front = either number minus the <em>other's</em> deficit (cross): 97 − 4 = <b>93</b> "
        "(and 96 − 3 = 93 too — they always agree!).",
        "Back = deficits multiplied: 3 × 4 = <b>12</b> (two digits).",
        "Join: 93 | 12 = <b>9312</b>. (Check: 97 × 96 = 9312. ✓)",
    ])))
    A(P("When the back product spills past two digits, you <b>carry</b> into the front, like always. "
        "<b>88 × 97</b>: deficits 12 and 3 → front 88 − 3 = 85, back 12 × 3 = 36 → <b>8536</b>:"))
    A(figure(fig_base100(88, 97), "88 × 97 → front 88−3 = 85, back 12 × 3 = 36 → 8536"))
    A(kiwi("🔑 <b>The secret.</b> Near 100, write the numbers as (100 − x) and (100 − y), where x, y are "
           "the deficits. Multiply:<br>"
           "(100 − x)(100 − y) = 100(100 − x − y) + xy = 100 × <b>[(100 − x) − y]</b> + <b>xy</b>.<br>"
           "The bracket is exactly the cross-subtraction (one number minus the other's deficit), sitting "
           "in the hundreds; and xy is the product of the deficits in the back. Magic explained — it's "
           "just clever place value around a friendly base."))
    A(tryit("Try 98 × 97 and 94 × 92.",
            "98 × 97: deficits 2, 3 → 98−3 = 95, 2×3 = 06 → <b>9506</b>. &#160; 94 × 92: deficits 6, 8 → "
            "94−8 = 86, 6×8 = 48 → <b>8648</b>."))
    A(tryit("A spicy carry: 89 × 89.",
            "Deficits 11, 11 → front 89 − 11 = 78, back 11 × 11 = 121. The 121 is three digits, so carry "
            "the 1: 78 + 1 = 79, keep 21 → <b>7921</b>. (Check: 89² = 7921. ✓)"))

    # ── TRICK 5: all-from-9, last-from-10 ───────────────────────────────────
    A(H("🔮 Trick 5 — Instant subtraction from 1000, 10000, …"))
    A(P("Subtracting from a big round number usually means messy borrowing. Not any more. "
        "<b>10000 − 4767</b>. The rule is a little chant: <b>“all from 9, and the last from 10.”</b> "
        "Take every digit of 4767 from 9, except the final digit which you take from 10:"))
    A(figure(fig_allfrom9(10000, 4767),
             "9−4=5, 9−7=2, 9−6=3, and the LAST 10−7=3 → 5233"))
    A(example("10000 − 4767", steps([
        "First digit: 9 − 4 = <b>5</b>.",
        "Next: 9 − 7 = <b>2</b>. &#160; Next: 9 − 6 = <b>3</b>.",
        "Last digit only: 10 − 7 = <b>3</b>.",
        "Read it off: <b>5233</b>. No borrowing, no crossing-out. (Check: 10000 − 4767 = 5233. ✓)",
    ])))
    A(kiwi("🔑 <b>The secret.</b> 10000 = 9999 + 1. Subtracting from <b>9999</b> never needs borrowing "
           "(every digit of 9999 is already a 9, so 9 − each digit is easy). That handles “all from 9.” "
           "Then the spare <b>+1</b> bumps the very last digit up by one — which is the same as taking "
           "the last digit from <b>10</b> instead of 9. Two tiny ideas, zero borrowing."))
    A(tryit("Do 1000 − 586.",
            "9−5 = 4, 9−8 = 1, last 10−6 = 4 → <b>414</b>."))
    A(tryit("Do 10000 − 2358.",
            "9−2 = 7, 9−3 = 6, 9−5 = 4, last 10−8 = 2 → <b>7642</b>."))

    # ── TRICK 6: ×5, ×25, ×9, ×99 ───────────────────────────────────────────
    A(H("🔮 Trick 6 — The friendly-number shortcuts (×5, ×25, ×9, ×99)"))
    A(P("Some numbers have a secret twin that's easier to use:"))
    A(P("• <b>× 5</b> = <b>× 10 ÷ 2</b> (because 5 is half of 10). So 468 × 5 → 4680 ÷ 2 = <b>2340</b>.<br>"
        "• <b>× 25</b> = <b>× 100 ÷ 4</b> (25 is a quarter of 100). So 32 × 25 → 3200 ÷ 4 = <b>800</b>.<br>"
        "• <b>× 9</b> = <b>× 10 − itself</b>. So 68 × 9 → 680 − 68 = <b>612</b>.<br>"
        "• <b>× 99</b> = <b>× 100 − itself</b>. So 46 × 99 → 4600 − 46 = <b>4554</b>."))
    A(example("1234 × 5 in two seconds", steps([
        "Stick a 0 on: 1234 → 12340 (that's × 10).",
        "Halve it: 12340 ÷ 2 = <b>6170</b>. (Check: 1234 × 5 = 6170. ✓)",
    ])))
    A(example("88 × 25", steps([
        "× 100: 88 → 8800.",
        "÷ 4: 8800 ÷ 4 = <b>2200</b>. (Check: 88 × 25 = 2200. ✓)",
    ])))
    A(kiwi("🔑 <b>The secret.</b> It's just <b>rewriting the number you multiply by</b> as something "
           "round. 5 = 10 ÷ 2, &#160;25 = 100 ÷ 4, &#160;9 = 10 − 1, &#160;99 = 100 − 1. Multiplying by "
           "10 or 100 is free (you only add zeros), and halving, quartering, or one subtraction is easy. "
           "Choose the easy twin and let place value carry the load."))
    A(tryit("Do 246 × 5 and 36 × 25.",
            "246 × 5 = 2460 ÷ 2 = <b>1230</b>. &#160; 36 × 25 = 3600 ÷ 4 = <b>900</b>."))
    A(tryit("Do 47 × 9 and 83 × 99.",
            "47 × 9 = 470 − 47 = <b>423</b>. &#160; 83 × 99 = 8300 − 83 = <b>8217</b>."))

    # ── TRICK 7: the 9-check ────────────────────────────────────────────────
    A(H("🔮 Trick 7 — The 9-check: catch a wrong answer red-handed"))
    A(P("Here's the most useful magic of all — a <b>mistake detector</b>. Take any number and keep "
        "adding its digits until just one digit is left (this one-digit squeeze is called its "
        "<b>digit sum</b>). For 1161: 1+1+6+1 = 9. For 27: 2+7 = 9."))
    A(figure(fig_ninecheck(1161), "1161 → 1+1+6+1 = 9. Squeeze any number down to one digit."))
    A(P("The surprise: when you do a multiplication, the digit sums obey the <em>same</em> "
        "multiplication. Test <b>27 × 43 = 1161</b>: digit-sum of 27 is 9, of 43 is 7. Now 9 × 7 = 63, "
        "and its digit sum is 6 + 3 = 9. The answer 1161 also squeezes to 9. <b>They match — so the "
        "answer passes the check.</b>"))
    A(P("Now watch it <b>catch a liar.</b> Suppose someone claims <b>68 × 47 = 3186</b>:"))
    A(example("the 9-check catches an error", steps([
        "Left side check: digit sum of 68 = 6+8 = 14 → 1+4 = <b>5</b>; of 47 = 4+7 = 11 → <b>2</b>.",
        "Multiply the checks: 5 × 2 = 10 → 1+0 = <b>1</b>. So a correct answer MUST squeeze to 1.",
        "Their answer 3186 squeezes to 3+1+8+6 = 18 → <b>9</b>.",
        "9 ≠ 1 — <b>caught!</b> The real answer is 68 × 47 = <b>3196</b> (which squeezes to "
        "3+1+9+6 = 19 → 1 ✓).",
    ])))
    A(figure(fig_ninecheck(6201), "Addition works too: 6201 → 6+2+0+1 = 9."))
    A(P("It checks <b>addition</b> as well. For 4825 + 1376: digit sums 1 and 8 → 1 + 8 = 9; the true "
        "total 6201 squeezes to 9 ✓. A claimed total of 6101 would squeeze to 8 — instantly wrong."))
    A(kiwi("🔑 <b>The secret.</b> Squeezing the digits is really finding the <b>remainder after dividing "
           "by 9</b> (mathematicians call it “casting out nines”). Remainders survive multiplication and "
           "addition, so the check digit of the answer must equal the check digit you get from the parts. "
           "⚠️ Honest warning: it can <em>miss</em> some errors (if a mistake is an exact multiple of 9, "
           "or two digits get swapped, the check digit doesn't change). It never gives a <b>false alarm</b> "
           "though — if the check fails, the answer is <em>definitely</em> wrong. A free 5-second safety "
           "net for every calculation you do."))
    A(tryit("Use the 9-check on “53 × 11 = 583.” Does it pass?",
            "53 → 8, 11 → 2; 8 × 2 = 16 → 7. Answer 583 → 5+8+3 = 16 → 7. <b>7 = 7, it passes.</b> "
            "(And 53 × 11 really is 583.)"))
    A(tryit("A friend writes “51 × 48 = 2438.” Catch it with the 9-check.",
            "51 → 6, 48 → 12 → 3; 6 × 3 = 18 → 9. So the answer must squeeze to 9. But 2438 → "
            "2+4+3+8 = 17 → 8. <b>8 ≠ 9 — wrong!</b> The real answer is 2448 (→ 9 ✓)."))

    # ── TRICK 8: vertically & crosswise (peek) ──────────────────────────────
    A(H("🔮 Trick 8 (a peek) — Vertically &amp; crosswise: ANY 2-digit × 2-digit"))
    A(P("The tricks so far need a special number (an 11, a 5, a near-100). This last one — "
        "<b>Urdhva-Tiryak</b>, “vertically and crosswise” — works for <em>every</em> 2-digit × 2-digit "
        "product in one line. Three little steps: <b>right</b>, <b>cross</b>, <b>left</b>."))
    A(figure(fig_cross(2, 3, 4, 1), "23 × 41 → right (3×1), cross (2×1 + 3×4), left (2×4)"))
    A(example("23 × 41", steps([
        "<b>Right</b> (straight down the ones): 3 × 1 = <b>3</b> → that's the ones digit.",
        "<b>Cross</b> (multiply the two diagonals and add): (2 × 1) + (3 × 4) = 2 + 12 = <b>14</b> → "
        "write 4, carry 1.",
        "<b>Left</b> (straight down the tens): 2 × 4 = 8, plus the carried 1 = <b>9</b>.",
        "Read it: 9&#160;4&#160;3 = <b>943</b>. (Check: 23 × 41 = 943. ✓)",
    ])))
    A(kiwi("🔑 <b>The secret.</b> (10a + b)(10c + d) = <b>100·ac</b> + 10·<b>(ad + bc)</b> + <b>bd</b>. "
           "Look at the three pieces: bd lands in the ones (that's “right”), ad + bc lands in the tens "
           "(the two “crosses” added), and ac lands in the hundreds (“left”). The cross diagram is "
           "literally a picture of this expansion — every Vedic trick in this chapter is one of these "
           "little algebra identities wearing a costume."))
    A(tryit("Try 12 × 34 with right–cross–left.",
            "Right 2×4 = 8. Cross (1×4)+(2×3) = 4+6 = 10 → 0 carry 1. Left 1×3 = 3, +1 = 4 → <b>408</b>."))
    A(tryit("Try 31 × 27.",
            "Right 1×7 = 7. Cross (3×7)+(1×2) = 21+2 = 23 → 3 carry 2. Left 3×2 = 6, +2 = 8 → <b>837</b>."))

    # ── PRACTICE LADDER ─────────────────────────────────────────────────────
    A(H("🪄 Practise your magic — climb the ladder"))
    A(P("Use the tricks (no long multiplication!). The last questions ask you to explain <em>why</em> a "
        "trick works — that's what turns a magician into a mathematician."))
    A(practice("Remember", [
        ("Which trick squares 65 fastest, and what's the rule?",
         "Trick 2: front × next-number, then write 25. 6×7 = 42 → <b>4225</b>."),
        ("42 × 11 = ?", "4 | (4+2) | 2 = <b>462</b>."),
        ("In “same tens, ones add to 10,” what must the ONES digits add to?",
         "Exactly <b>10</b> (and the tens digits must be the same)."),
        ("What is the digit sum (9-check value) of 1161?", "1+1+6+1 = <b>9</b>."),
        ("× 25 is the same as × 100 then ÷ ___ ?", "÷ <b>4</b> (since 25 is a quarter of 100)."),
    ]))
    A(practice("Understand", [
        ("73 × 11 — careful, there's a carry.",
         "7 | (7+3)=10 | 3 → carry the 1 → 8 | 0 | 3 = <b>803</b>."),
        ("Square 85 with the trick.", "8 × 9 = 72, then 25 → <b>7225</b>."),
        ("64 × 66 (same tens, ones add to 10).", "(6×7) | (4×6) = 42 | 24 = <b>4224</b>."),
        ("Explain in one sentence why 23 × 27 uses the same-tens trick.",
         "Both have tens digit 2 and the ones add to 10 (3+7), so it's 2×3 | 3×7 = 6 | 21 = <b>621</b>."),
        ("246 × 5 using the ×10÷2 shortcut.", "2460 ÷ 2 = <b>1230</b>."),
    ]))
    A(practice("Apply", [
        ("88 × 11.", "8 | 16 | 8 → carry → 9 | 6 | 8 = <b>968</b>."),
        ("Square 135.", "13 × 14 = 182, then 25 → <b>18225</b>."),
        ("41 × 49 (ones add to 10).", "(4×5) | (1×9) = 20 | 09 = <b>2009</b>."),
        ("98 × 91 with the near-100 deficit trick.",
         "Deficits 2 and 9 → front 98−9 = 89, back 2×9 = 18 → <b>8918</b>."),
        ("10000 − 3489 with all-from-9, last-from-10.",
         "9−3, 9−4, 9−8, 10−9 = 6, 5, 1, 1 → <b>6511</b>."),
        ("72 × 25 and 67 × 99.", "72 × 25 = 7200 ÷ 4 = <b>1800</b>. &#160; 67 × 99 = 6700 − 67 = <b>6633</b>."),
    ]))
    A(practice("Analyze", [
        ("45² = 2025 and 55² = 3025. Both end in 25 — explain why every number ending in 5 must end its "
         "square in 25.",
         "Because (10n+5)² = 100·n(n+1) + 25: the +25 is always there and the 100×… part never reaches "
         "the last two places, so the square ALWAYS ends in <b>25</b>."),
        ("35 × 11 = 385 and 53 × 11 = 583. Why do they share the same middle digit 8?",
         "The middle is the SUM of the two digits, and 3+5 = 5+3 = 8. Swapping the digits doesn't change "
         "their sum, so the middle stays 8 (only the outer digits swap)."),
        ("A friend says 76 × 74 = 5604. Use the 9-check to test it, then give the right answer.",
         "76 → 4, 74 → 2; 4×2 = 8. Answer must squeeze to 8. But 5604 → 5+6+0+4 = 15 → 6 ≠ 8, so it's "
         "<b>wrong</b>. Correct: same-tens trick (7×8)|(6×4) = 56|24 = <b>5624</b> (→ 8 ✓)."),
        ("Why does 97 × 96 = 9312 give the SAME front whether you do 97−4 or 96−3?",
         "Both equal 100 − 3 − 4 = 93. The cross-subtraction is really “100 minus both deficits,” so "
         "either route lands on the same number."),
    ]))
    A(practice("Create", [
        ("Invent your OWN “ones-add-to-10” multiplication (pick a tens digit and two ones that add to 10) "
         "and show the one-line answer.",
         "Example: 72 × 78 → both tens 7, ones 2+8 = 10 → (7×8)|(2×8) = 56|16 = <b>5616</b>. "
         "(Any valid pair works — check it!)"),
        ("Make up a wrong multiplication answer that the 9-check would FAIL to catch, and explain the "
         "loophole.",
         "Take a true answer and change it by a multiple of 9 (e.g. claim 23 × 11 = 394 instead of the "
         "real 385 — they differ by 9). Both squeeze to the same check digit, so the 9-check can't tell — "
         "that's the multiple-of-9 blind spot."),
        ("Design a 10-second mental-maths challenge for a friend using exactly two different tricks, and "
         "write the answers.",
         "E.g. “95² then 99 × 99”: 95² = (9×10)|25 = <b>9025</b>; 99 × 99 deficits 1,1 → 98|01 = "
         "<b>9801</b>."),
    ]))

    # ── FINALE: the Magic Show ──────────────────────────────────────────────
    A(challenge(
        P("🔮 <b>THE GRAND MAGIC SHOW.</b> Stand in front of your family and say: “Give me any two-digit "
          "number — I'll square it if it ends in 5, multiply it by 11, and check my answer is right, all "
          "without writing!” Here's your secret rehearsal with the number <b>85</b>:") +
        steps([
            "<b>85 × 11</b>: 8 | (8+5)=13 | 5 → carry → 9 | 3 | 5 = <b>935</b>.",
            "<b>85²</b>: 8 × 9 = 72, then 25 → <b>7225</b>.",
            "<b>Prove 85² is right with the 9-check</b>: 85 → 8+5 = 13 → 4; so 85² must squeeze to "
            "4 × 4 = 16 → <b>7</b>. And 7225 → 7+2+2+5 = 16 → <b>7</b>. Match — take a bow! 🎩",
        ]) +
        tryit("Your real challenge: do the WHOLE show for the number 75 (75 × 11, then 75², then "
              "9-check your 75²). Show every step.",
              "75 × 11 = 7 | (7+5)=12 | 5 → carry → 8 | 2 | 5 = <b>825</b>. &#160; "
              "75² = 7×8 = 56, then 25 → <b>5625</b>. &#160; 9-check: 75 → 12 → 3, so 75² must squeeze to "
              "3 × 3 = <b>9</b>; and 5625 → 5+6+2+5 = 18 → <b>9</b>. ✓ Perfect — you're a real "
              "math magician now!") +
        P("Take it further: ask for a number near 100 (like 96 or 98) and dazzle them with the deficit "
          "trick too. Every single move you make is built on place value and a sliver of algebra — that's "
          "the deepest magic of all: <em>you understand exactly why it works.</em>")))

    A(kiwi("Spectacular! 🎉 You now wield eight pieces of Vedic speed-magic — and you've seen the secret "
           "behind each: ×11 hides 10 + 1, squaring-in-5 and same-tens hide (10n+5)² and 100·a(a+1), "
           "the near-100 trick hides (100−x)(100−y), and crosswise hides the full ab × cd expansion. "
           "Real maths, real speed, real wonder. Next stop on our expedition: hunting for hidden "
           "<b>patterns and rules</b> in sequences. 🔭"))

    chapter("Part 3 · 🔮 Vedic Maths Magic", 10, "Vedic Speed Maths",
            "Arithmetic · Speed Magic", "".join(b))
