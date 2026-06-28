#!/usr/bin/env python3
"""Chapter 18 — Venn Diagrams  (Combinatorics · Brain Benders)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, venn2, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# ── local figure: a 2-set Venn drawn inside a labelled "everyone" box ────────
def _rtext(x, y, val, col):
    """Render a region value as SVG text. If it contains '<br>', split into
    stacked <tspan> word-lines (smaller font); otherwise a big number."""
    val = str(val)
    if "<br>" in val:
        lines = val.split("<br>")
        n = len(lines)
        size = 13
        y0 = y - (n - 1) * (size + 2) / 2
        spans = "".join(
            f'<tspan x="{x}" y="{y0 + i * (size + 2):.0f}">{ln}</tspan>'
            for i, ln in enumerate(lines))
        return (f'<text text-anchor="middle" font-size="{size}" font-weight="800" '
                f'fill="{col}">{spans}</text>')
    return (f'<text x="{x}" y="{y}" text-anchor="middle" font-size="24" '
            f'font-weight="800" fill="{col}">{val}</text>')


def venn2_box(only_l, both, only_r, neither, la, lb, total=None):
    """Two overlapping circles inside a rectangle (the universal set / 'everyone').
    Shows the four region counts + a 'neither' count in the corner."""
    s = [f'<rect x="6" y="6" width="388" height="234" rx="12" fill="none" '
         f'stroke="{INK}" stroke-width="2" stroke-dasharray="2 0"/>',
         f'<text x="20" y="26" font-size="12.5" font-weight="800" fill="{INK}">Everyone</text>',
         f'<circle cx="150" cy="138" r="76" fill="{SKY}1c" stroke="{SKY}" stroke-width="2.4"/>',
         f'<circle cx="250" cy="138" r="76" fill="{BERRY}1c" stroke="{BERRY}" stroke-width="2.4"/>',
         f'<text x="96" y="50" text-anchor="middle" font-size="14" font-weight="800" '
         f'fill="{SKY}">{la}</text>',
         f'<text x="304" y="50" text-anchor="middle" font-size="14" font-weight="800" '
         f'fill="{BERRY}">{lb}</text>',
         _rtext(108, 144, only_l, INK),
         _rtext(200, 144, both, PURPLE),
         _rtext(292, 144, only_r, INK),
         f'<text x="372" y="228" text-anchor="end" font-size="20" font-weight="800" '
         f'fill="{GRASS}">{neither}</text>',
         f'<text x="372" y="208" text-anchor="end" font-size="11" font-weight="700" '
         f'fill="{GRASS}">neither</text>']
    return svg("".join(s), 400, 246)


# ── local figure: a 3-set Venn (just a gentle taste) ────────────────────────
def venn3(regions):
    """regions: dict with keys A,B,C,AB,AC,BC,ABC -> counts. Three circles."""
    g = lambda k: regions.get(k, "")
    s = [f'<circle cx="150" cy="110" r="82" fill="{SKY}18" stroke="{SKY}" stroke-width="2.4"/>',
         f'<circle cx="230" cy="110" r="82" fill="{BERRY}18" stroke="{BERRY}" stroke-width="2.4"/>',
         f'<circle cx="190" cy="178" r="82" fill="{GRASS}18" stroke="{GRASS}" stroke-width="2.4"/>',
         f'<text x="86" y="48" text-anchor="middle" font-size="13.5" font-weight="800" fill="{SKY}">A</text>',
         f'<text x="294" y="48" text-anchor="middle" font-size="13.5" font-weight="800" fill="{BERRY}">B</text>',
         f'<text x="190" y="276" text-anchor="middle" font-size="13.5" font-weight="800" fill="{GRASS}">C</text>',
         # region centres
         f'<text x="112" y="96" text-anchor="middle" font-size="18" font-weight="800" fill="{INK}">{g("A")}</text>',
         f'<text x="268" y="96" text-anchor="middle" font-size="18" font-weight="800" fill="{INK}">{g("B")}</text>',
         f'<text x="190" y="210" text-anchor="middle" font-size="18" font-weight="800" fill="{INK}">{g("C")}</text>',
         f'<text x="190" y="92" text-anchor="middle" font-size="17" font-weight="800" fill="{PURPLE}">{g("AB")}</text>',
         f'<text x="146" y="166" text-anchor="middle" font-size="17" font-weight="800" fill="{PURPLE}">{g("AC")}</text>',
         f'<text x="234" y="166" text-anchor="middle" font-size="17" font-weight="800" fill="{PURPLE}">{g("BC")}</text>',
         f'<text x="190" y="138" text-anchor="middle" font-size="17" font-weight="800" fill="{ORANGE}">{g("ABC")}</text>']
    return svg("".join(s), 380, 296)


def build(chapter):
    b = []
    A = b.append

    A(big_q("In a class, some children like <b>cricket</b>, some like <b>football</b>, and a few "
            "like <b>both</b>. If you just add the cricket-lovers and the football-lovers, you "
            "count the “both” children <em>twice</em>! How can a picture sort this out for us?"))
    A(kiwi("Hi, it's <b>Kiwi</b>! When things can belong to <em>more than one group</em>, a plain "
           "list gets confusing. The cure is a clever picture called a <b>Venn diagram</b> — two "
           "overlapping circles that give every child exactly one home. Let's see how it works."))

    # ── the picture ─────────────────────────────────────────────────────────
    A(H("Two circles that overlap"))
    A(P("Draw one circle for <b>Cricket</b> fans and another for <b>Football</b> fans, and let "
        "them <b>overlap</b> in the middle. Now every child fits in exactly one place:"))
    A(figure(venn2_box("only<br>cricket", "both", "only<br>football", "neither",
                       "Cricket", "Football"),
             "Four homes: only cricket · both · only football · and (outside) neither"))
    A(P("• The <b>left-only</b> part: children who like cricket <em>but not</em> football.<br>"
        "• The <b>middle (overlap)</b>: children who like <em>both</em> sports.<br>"
        "• The <b>right-only</b> part: children who like football <em>but not</em> cricket.<br>"
        "• <b>Outside</b> the circles: children who like <em>neither</em>."))
    A(kiwi("The big idea: the <b>overlap</b> is for things that belong to <em>both</em> groups. "
           "That's how a Venn diagram stops us from double-counting. Each person stands in just "
           "one region."))

    # ── reading region counts ───────────────────────────────────────────────
    A(H("Reading the numbers"))
    A(P("Usually the diagram comes with <b>numbers</b> in each region. Here's our class. Read it "
        "carefully — the <b>6</b> in the middle means 6 children like <em>both</em>:"))
    A(figure(venn2(12, 6, 8, "Cricket", "Football"),
             "12 only cricket · 6 both · 8 only football"))
    A(example("answering questions from the picture", steps([
        "<b>How many like only cricket?</b> Read the left-only region: <b>12</b>.",
        "<b>How many like both?</b> Read the overlap: <b>6</b>.",
        "<b>How many like cricket altogether?</b> That's only-cricket PLUS both = 12 + 6 = "
        "<b>18</b>. (The cricket circle holds both regions!)",
        "<b>How many like football altogether?</b> only-football + both = 8 + 6 = <b>14</b>.",
        "<b>How many children in total are in the circles?</b> 12 + 6 + 8 = <b>26</b>. "
        "(Add each region once — the overlap just once!)",
    ])))
    A(kiwi("Watch the trap! “How many like cricket” means the <em>whole</em> cricket circle "
           "(only-cricket + both), not just the left-only slice. The overlap belongs to "
           "<b>both</b> circles at once."))

    A(tryit("From the same picture, how many children like <b>exactly one</b> of the two sports "
            "(only cricket or only football, but not both)?",
            "Add the two outer slices, leaving out the overlap: 12 + 8 = <b>20</b> children."))

    # ── 'neither' and the total ─────────────────────────────────────────────
    A(H("Where do the 'neither' children go?"))
    A(P("Some children like <em>neither</em> sport. They don't belong in either circle, so they "
        "sit <b>outside</b> both — but still inside the box marked “Everyone”. Suppose the whole "
        "class has <b>30</b> children:"))
    A(figure(venn2_box(12, 6, 8, 4, "Cricket", "Football"),
             "Class of 30: 26 inside the circles, so 4 sit outside (neither)"))
    A(example("finding the 'neither' count", steps([
        "Children inside the circles = 12 + 6 + 8 = <b>26</b>.",
        "The whole class = <b>30</b>.",
        "So children who like neither = 30 − 26 = <b>4</b>. They go outside both circles.",
        "Check: 12 + 6 + 8 + 4 = 30. ✓ Every child is counted exactly once.",
    ])))
    A(kiwi("Golden rule for totals: add the <b>four regions</b> (only-left, both, only-right, "
           "neither) and you get <em>everyone</em>, with nobody counted twice. If your regions "
           "don't add to the total, hunt for the mistake!"))

    A(tryit("A club of <b>20</b> kids: 9 only swim, 4 do both swimming and dancing, 5 only "
            "dance. How many do <b>neither</b>?",
            "Inside the circles: 9 + 4 + 5 = 18. Neither = 20 − 18 = <b>2</b>."))

    # ── building a Venn from a story ────────────────────────────────────────
    A(H("Filling in a Venn from clues"))
    A(P("Often you're <em>told</em> the totals and must work out each region. The trick: "
        "<b>start with the overlap</b>, then subtract. Here's a tasty one."))
    A(example("ice-cream and cake at a party", steps([
        "At a party of <b>25</b> children: <b>15</b> had ice-cream, <b>12</b> had cake, and "
        "<b>7</b> had <em>both</em>.",
        "<b>Both</b> goes in the middle: <b>7</b>.",
        "<b>Only ice-cream</b> = ice-cream total − both = 15 − 7 = <b>8</b>.",
        "<b>Only cake</b> = cake total − both = 12 − 7 = <b>5</b>.",
        "<b>Neither</b> = 25 − (8 + 7 + 5) = 25 − 20 = <b>5</b>.",
    ])))
    A(figure(venn2_box(8, 7, 5, 5, "Ice-cream", "Cake"),
             "Filled in: 8 only ice-cream · 7 both · 5 only cake · 5 neither (party of 25)"))
    A(kiwi("Always subtract the <b>both</b> number from each total to get the “only” parts — "
           "otherwise you double-count the children who had two treats. Overlap first, then "
           "subtract: that's the recipe."))

    A(tryit("In a group of 18: 10 read comics, 8 read storybooks, 3 read both. "
            "How many read <b>only comics</b>?",
            "Only comics = comics total − both = 10 − 3 = <b>7</b>."))

    # ── Bloom ladder ────────────────────────────────────────────────────────
    A(H("Now you try — climb the ladder"))
    A(P("Picture the circles. Put <b>both</b> in the middle first, then subtract for the “only” "
        "parts, then find “neither” from the total. Peek only after a real try!"))

    A(practice("Remember", [
        ("In a Venn diagram, which part is for things that belong to <b>both</b> groups?",
         "The overlap — the middle, where the circles cross."),
        ("Where do you put items that belong to <b>neither</b> group?",
         "Outside both circles (but inside the 'everyone' box)."),
        ("If 5 children are in the overlap, how many like <em>both</em> things?", "5."),
        ("True or false: the overlap counts as part of <em>both</em> circles.", "True."),
    ]))
    A(practice("Understand", [
        ("A Venn shows: only dogs = 7, both = 3, only cats = 5. How many like dogs <b>in "
         "total</b>?",
         "Only dogs + both = 7 + 3 = 10."),
        ("Same picture: how many like cats in total?", "Only cats + both = 5 + 3 = 8."),
        ("Same picture: how many children are inside the circles altogether?",
         "7 + 3 + 5 = 15."),
        ("Same picture: how many like <b>only one</b> of the two animals?",
         "Only dogs + only cats = 7 + 5 = 12 (leave out the overlap)."),
    ]))
    A(practice("Apply", [
        ("In a class of 24: 9 only play guitar, 5 play both guitar and drums, 6 only play "
         "drums. How many play <b>neither</b>?",
         "Inside circles = 9 + 5 + 6 = 20. Neither = 24 − 20 = 4."),
        ("18 children like apples, 6 like both apples and bananas. How many like <b>only</b> "
         "apples?",
         "Only apples = 18 − 6 = 12."),
        ("At a fair, 20 rode the swing, 14 rode the slide, 8 rode both. How many rode the "
         "swing only?",
         "Swing only = 20 − 8 = 12."),
        ("A group of 30: 16 like maths, 19 like art, 9 like both. How many like at least one "
         "of the two subjects?",
         "Only maths 16 − 9 = 7; only art 19 − 9 = 10; both 9 → 7 + 10 + 9 = 26."),
    ]))
    A(practice("Analyze", [
        ("In a class of 28: 17 like pizza, 13 like burgers, 4 like neither. How many like "
         "<b>both</b>? (Hint: first find how many are inside the circles.)",
         "Inside the circles = 28 − 4 = 24. If both = x, then (17 − x) + x + (13 − x) = 24, so "
         "30 − x = 24, giving x = 6. Six children like both."),
        ("Rohan adds “18 like cricket” and “14 like football” and says 32 children like a sport. "
         "But the class has only 30. What did he forget?",
         "He double-counted the children who like BOTH. The real count of sport-likers is "
         "18 + 14 − both, never 32. The 6 'both' children were counted in each total."),
        ("A Venn shows only-X = 11, both = 4, only-Y = 9, and the total group is 30. "
         "Are there any 'neither' children? How many?",
         "Inside circles = 11 + 4 + 9 = 24, so neither = 30 − 24 = 6 children."),
        ("Two clubs: 12 kids are in Chess, 12 are in Music, and 20 kids in total are in at least "
         "one club. How many are in both clubs?",
         "If both = x: (12 − x) + x + (12 − x) = 20 → 24 − x = 20 → x = 4. Four kids are in "
         "both."),
    ]))
    A(practice("Create", [
        ("Make up a Venn-diagram story about two hobbies where exactly <b>3</b> people do both. "
         "Give a number for every region and the total.",
         "Many answers, e.g. 8 only paint, 3 both, 5 only sing, 2 neither → total 18."),
        ("Design a Venn where the same number of people like 'only tea' as like 'only coffee', "
         "and 4 like both. Fill in numbers and the total.",
         "Example: 6 only tea, 4 both, 6 only coffee, 1 neither → total 17 (only-tea = "
         "only-coffee = 6)."),
    ]))

    # ── a taste of 3 sets ───────────────────────────────────────────────────
    A(H("A taste of three circles"))
    A(P("Once you're comfortable with two circles, you can use <b>three</b>! Now there are even "
        "more regions, including a tiny middle bit for things in <em>all three</em> groups. "
        "Here, A = likes <b>art</b>, B = likes <b>ball games</b>, C = likes <b>coding</b>:"))
    A(figure(venn3({"A": 5, "B": 6, "C": 4, "AB": 2, "AC": 3, "BC": 1, "ABC": 2}),
             "The orange centre (2) = children who like ALL THREE; the purple petals = exactly two"))
    A(example("reading the three-circle picture", steps([
        "<b>Like all three</b> (art, ball games AND coding) = the very centre = <b>2</b>.",
        "<b>Like art and coding but not ball games</b> = the A-and-C petal (not touching B) = "
        "<b>3</b>.",
        "<b>Like only art</b> (and nothing else) = the part of A on its own = <b>5</b>.",
        "It's the same idea as before — every child stands in exactly one region.",
    ])))
    A(kiwi("Three circles look busy, but the rule never changes: the deeper the overlap, the "
           "<em>more</em> groups that thing belongs to. The very middle belongs to <b>all "
           "three</b>. You've got this!"))

    A(challenge(
        P("In a class of <b>32</b> children: <b>20</b> like <b>chocolate</b>, <b>15</b> like "
          "<b>vanilla</b>, and <b>8</b> like <b>both</b>. Find: (a) how many like only "
          "chocolate, (b) how many like only vanilla, (c) how many like <b>neither</b>.") +
        tryit("Put 'both' in the middle first, then subtract from each total; finally use the "
              "class size for 'neither'.",
              "(a) Only chocolate = 20 − 8 = <b>12</b>. (b) Only vanilla = 15 − 8 = <b>7</b>. "
              "(c) Inside the circles = 12 + 8 + 7 = 27, so neither = 32 − 27 = <b>5</b>. "
              "Check: 12 + 8 + 7 + 5 = 32. ✓")))

    A(kiwi("Good thinking — counting the overlap just once is the move most people miss. You can read "
           "every region of a Venn diagram, handle the “both” overlap without double-counting, find the "
           "“neither” group, and you've even peeked at three circles. That's the end of our Brain "
           "Benders on counting and sets. 🎉"))

    chapter("Part 5 · Brain Benders", 18, "Venn Diagrams",
            "Combinatorics · Brain Benders", "".join(b))
