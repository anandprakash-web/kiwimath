#!/usr/bin/env python3
"""L3 Chapter 21 — Averages, Graphs & Data Handling (Data Handling · Data Detectives).
Mean (the fair-share average), median & mode, reading & drawing bar charts,
pictographs (with a key), and pie charts; totals, differences, how-many-more,
most/least, and what an average really tells you. Every average is recomputed and
every chart answer matches the figure data exactly (verified in Python)."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, bar_chart, pictograph, pie, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# -- local figure: "levelling" towers to show the mean as a fair share ----
def level_towers(values, mean_val, labels=None):
    """Draw towers of cubes for each value, with a dashed line at the mean to show
    'levelling out'. mean_val may be a float."""
    cube = 22; bw = 40; gap = 20; x0 = 30
    base = 30 + max(values) * cube
    W = x0 + len(values) * (bw + gap) + 40
    Hh = base + 36
    cols = [SKY, GRASS, BERRY, ORANGE, PURPLE, GOLD]
    s = []
    for i, v in enumerate(values):
        x = x0 + i * (bw + gap)
        for k in range(v):
            y = base - (k + 1) * cube
            s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{cube-3}" rx="4" '
                     f'fill="{cols[i%6]}99" stroke="{cols[i%6]}" stroke-width="1.6"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{base+18}" text-anchor="middle" font-size="12" '
                 f'fill="{INK}">{labels[i] if labels else v}</text>')
    ymean = base - mean_val * cube
    s.append(f'<line x1="20" y1="{ymean:.0f}" x2="{W-20}" y2="{ymean:.0f}" stroke="{ORANGE}" '
             f'stroke-width="2.4" stroke-dasharray="7 5"/>')
    s.append(f'<text x="{W-18}" y="{ymean-5:.0f}" text-anchor="end" font-size="12" '
             f'font-weight="800" fill="{ORANGE}">mean = {mean_val:g}</text>')
    return svg("".join(s), W, Hh)


# -- local figure: a sorted row of numbers with the median highlighted -----
def sorted_row(values, median_idx=None, pair=None):
    """values already sorted; highlight the middle one (median_idx) or the pair."""
    bw = 46; gap = 12; x0 = 16
    W = x0 + len(values) * (bw + gap) + 6
    s = []
    for i, v in enumerate(values):
        x = x0 + i * (bw + gap)
        hot = (median_idx is not None and i == median_idx) or (pair is not None and i in pair)
        col = ORANGE if hot else "#cfc9bf"
        fill = f"{ORANGE}1f" if hot else "#f3f1ec"
        s.append(f'<rect x="{x}" y="14" width="{bw}" height="44" rx="9" fill="{fill}" '
                 f'stroke="{col}" stroke-width="2.2"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="42" text-anchor="middle" font-size="18" '
                 f'font-weight="800" fill="{INK}">{v}</text>')
    return svg("".join(s), W, 70)


def build(chapter):
    b = []; A = b.append

    A(big_q("Five friends compare pocket money: &#8377;10, &#8377;30, &#8377;20, &#8377;40, "
            "&#8377;0. &ldquo;That's not fair!&rdquo; cries the one with nothing. If they pooled "
            "it all and split it <b>equally</b>, how much would each get? That single &ldquo;fair "
            "share&rdquo; number is one of the most useful ideas in maths &mdash; and by the end "
            "of this chapter you'll read it straight out of charts and graphs."))
    A(kiwi("Hello, data detective &mdash; <b>Kiwi</b> here! &#128202; Numbers are clues, and the "
           "right <b>picture</b> makes the clues leap out. In this final chapter you'll learn the "
           "three kinds of <b>average</b> (mean, median, mode), then <em>read and draw</em> bar "
           "charts, pictographs and pie charts &mdash; finding the most, the least, the total, "
           "and the story the data is trying to tell."))

    # ===================== A . MEAN =====================
    A(H("Part A &middot; The mean: a fair share"))
    A(P("The <b>mean</b> (the everyday &ldquo;average&rdquo;) is what each one would get if you "
        "<b>shared everything equally</b>. Imagine three towers of blocks &mdash; 3, 5 and 1 "
        "&mdash; and you slide blocks across until all towers are the <em>same</em> height:"))
    A(figure(level_towers([3, 5, 1], 3),
             "Total 9 blocks shared into 3 equal towers of 3 -- the mean is 3."))
    A(example("the recipe for the mean", steps([
        "<b>Add</b> all the values: 3 + 5 + 1 = <b>9</b> blocks altogether.",
        "<b>Divide</b> by how many there are: 9 &divide; 3 = <b>3</b>.",
        "So the mean is <b>3</b> &mdash; the fair, level share. Rule: <b>mean = total &divide; "
        "(how many)</b>.",
    ])))
    A(P("Back to the pocket money: &#8377;10 + &#8377;30 + &#8377;20 + &#8377;40 + &#8377;0 = "
        "&#8377;100 shared among 5 friends = <b>&#8377;20 each</b>. Notice the mean (&#8377;20) "
        "isn't anyone's actual amount &mdash; it's the <em>balancing point</em> of them all."))
    A(kiwi("Two things the mean loves to do: (1) it lands <em>between</em> the smallest and "
           "biggest value, never outside; (2) it's the size every value <em>would</em> be if they "
           "were all equal. A great check: if your mean is bigger than every number, you've "
           "slipped somewhere!"))
    A(example("a useful twist: finding a missing value", steps([
        "Over 5 days a runner's steps (in thousands) were 12, 15, 9, 8, and one more day that's "
        "smudged. The <b>mean was 12</b>.",
        "If the mean of 5 numbers is 12, their <b>total</b> must be 12 &times; 5 = <b>60</b>.",
        "The four known days add to 12 + 15 + 9 + 8 = <b>44</b>.",
        "So the smudged day = 60 &minus; 44 = <b>16</b> (thousand steps). Working from the mean "
        "back to a total is a real detective move! &#10003;",
    ])))
    A(tryit("Find the mean of <b>6, 10, 8</b>.",
            "Total = 6 + 10 + 8 = 24; there are 3 numbers; mean = 24 &divide; 3 = <b>8</b>."))

    # ===================== B . MEDIAN & MODE =====================
    A(H("Part B &middot; Median & mode (two more averages)"))
    A(P("The <b>median</b> is the <b>middle</b> value when the numbers are lined up in order. "
        "Line up 3, 7, 2, 9, 5 from smallest to biggest and look at the one in the centre:"))
    A(figure(sorted_row([2, 3, 5, 7, 9], median_idx=2),
             "Sorted: 2, 3, 5, 7, 9. The middle value is 5 -- that's the median."))
    A(example("finding the median (an odd-sized list)", steps([
        "<b>Sort</b> the numbers: 2, 3, 5, 7, 9.",
        "There are 5 numbers, so the <b>middle</b> one is the 3rd: <b>5</b>.",
        "The median is <b>5</b> &mdash; half the numbers are below it, half above.",
    ])))
    A(P("If there's an <b>even</b> number of values there are <em>two</em> in the middle &mdash; "
        "the median is their mean (halfway between). For 2, 4, 6, 8 the two middles are 4 and 6, "
        "so the median is (4 + 6) &divide; 2 = <b>5</b>."))
    A(figure(sorted_row([2, 4, 6, 8], pair=(1, 2)),
             "Sorted: 2, 4, 6, 8. Two middles (4 and 6) -> median = (4 + 6) / 2 = 5."))
    A(P("The <b>mode</b> is the value that appears <b>most often</b> &mdash; the most "
        "&ldquo;popular&rdquo; number. In 3, 5, 5, 2, 5, 1 the number <b>5</b> shows up three "
        "times, more than any other, so the mode is 5."))
    A(kiwi("Three averages, three jobs: the <b>mean</b> is the fair share (add then divide); the "
           "<b>median</b> is the middle in order; the <b>mode</b> is the most common. A shoe shop "
           "cares about the <em>mode</em> (which size sells most!), while a teacher sharing sweets "
           "cares about the <em>mean</em>."))
    A(tryit("Find the <b>mode</b> and the <b>median</b> of the shoe sizes 6, 7, 7, 8, 7, 9.",
            "Mode = <b>7</b> (it appears three times). Sorted: 6, 7, 7, 7, 8, 9 &mdash; six "
            "numbers, two middles (7 and 7), so median = (7 + 7) &divide; 2 = <b>7</b>."))

    # ===================== C . BAR CHARTS =====================
    A(H("Part C &middot; Bar charts: taller means more"))
    A(P("A <b>bar chart</b> shows amounts as bars &mdash; taller bar, bigger number. Read a "
        "value from the number at the bar's top. Here is a class's favourite-fruit survey:"))
    A(figure(bar_chart([("Apple", 8), ("Banana", 5), ("Mango", 10), ("Grapes", 3)]),
             "Favourite fruit. Mango reaches 10, Apple 8, Banana 5, Grapes 3."))
    A(kiwi("Four detective questions work on <em>every</em> chart: (1) Which is the <b>most</b>? "
           "(tallest bar) (2) Which is the <b>least</b>? (shortest bar) (3) What is the "
           "<b>total</b>? (add all bars) (4) <b>How many more</b>? (subtract one bar from "
           "another)."))
    A(example("reading the fruit bar chart", steps([
        "<b>Most popular?</b> The tallest bar is <b>Mango</b> at 10.",
        "<b>Least popular?</b> The shortest is <b>Grapes</b> at 3.",
        "<b>Total children?</b> 8 + 5 + 10 + 3 = <b>26</b>.",
        "<b>How many more chose mango than grapes?</b> 10 &minus; 3 = <b>7</b> more.",
    ])))
    A(tryit("From the fruit chart, how many more children chose <b>apple</b> than <b>banana</b>, "
            "and how many chose <b>apple or grapes</b> altogether?",
            "Apple 8 &minus; banana 5 = <b>3</b> more. Apple (8) + grapes (3) = <b>11</b> "
            "children."))
    A(P("Bar charts also show change over time. Here are a cricketer's runs in 5 matches &mdash; "
        "and this time we'll also find the <b>mean</b>:"))
    A(figure(bar_chart([("M1", 45), ("M2", 60), ("M3", 30), ("M4", 75), ("M5", 40)]),
             "Runs per match: 45, 60, 30, 75, 40. Total 250, mean 50."))
    A(example("combining a chart with the mean", steps([
        "<b>Best match?</b> The tallest bar is <b>M4</b> with 75 runs; the lowest is M3 with 30.",
        "<b>Total runs?</b> 45 + 60 + 30 + 75 + 40 = <b>250</b>.",
        "<b>Mean (average) runs?</b> 250 &divide; 5 = <b>50</b> runs per match.",
        "<b>How many more in M4 than M3?</b> 75 &minus; 30 = <b>45</b> runs. &#10003;",
    ])))

    # ===================== D . PICTOGRAPHS =====================
    A(H("Part D &middot; Pictographs: counting with pictures"))
    A(P("A <b>pictograph</b> uses a little picture to stand for an amount. The most important "
        "thing is the <b>key</b> &mdash; it tells you how much <em>one</em> picture is worth. Here "
        "each star is worth <b>5</b> reward points:"))
    A(figure(pictograph([("Aarav", 4), ("Diya", 6), ("Kabir", 3), ("Mira", 5)], icon="&#11088;", per=5),
             "Reward stars. Read the key: each star = 5 points."))
    A(kiwi("Golden rule for pictographs: <b>count the pictures, then multiply by the key.</b> "
           "Never just count pictures &mdash; always check what one is worth first!"))
    A(example("reading the star pictograph (each star = 5)", steps([
        "Diya has 6 stars &rarr; 6 &times; 5 = <b>30</b> points.",
        "Aarav: 4 &times; 5 = <b>20</b>; Kabir: 3 &times; 5 = <b>15</b>; Mira: 5 &times; 5 = "
        "<b>25</b>.",
        "<b>Who earned the most?</b> Diya (30 points).",
        "<b>How many more has Diya than Kabir?</b> 30 &minus; 15 = <b>15</b> points. &#10003;",
    ])))
    A(tryit("In the star pictograph (each star = 5), how many points did <b>Aarav and Kabir "
            "together</b> earn? And if a new friend earned <b>20</b> points, how many stars would "
            "they draw?",
            "Aarav 20 + Kabir 15 = <b>35</b> points. A new friend with 20 points draws "
            "20 &divide; 5 = <b>4</b> stars."))

    # ===================== E . PIE CHARTS =====================
    A(H("Part E &middot; Pie charts: slices of the whole"))
    A(P("A <b>pie chart</b> (circle graph) shows how one whole is split into parts. The whole "
        "circle is everything; each slice is one part, and a bigger slice means a bigger share. "
        "Here is how a class of <b>24</b> children spend their free time:"))
    A(figure(pie([("Reading", 6), ("Sports", 8), ("Drawing", 4), ("Music", 6)]),
             "Free-time of 24 children. Biggest slice = most popular."))
    A(example("reading the free-time pie chart", steps([
        "<b>Most popular?</b> The largest slice is <b>Sports</b> (8 children).",
        "<b>Least popular?</b> The smallest is <b>Drawing</b> (4 children).",
        "<b>Do all slices add to the whole?</b> 6 + 8 + 4 + 6 = <b>24</b>. &#10003;",
        "<b>Do reading and music make half the class?</b> 6 + 6 = 12, and half of 24 is 12 "
        "&mdash; yes, exactly half!",
    ])))
    A(kiwi("Detective check for pie charts: the slices must <em>always add up to the whole</em>. "
           "And you can read slices as fractions: Sports is 8 of 24 = <b>1/3</b> of the class, "
           "Drawing is 4 of 24 = <b>1/6</b>. The pie shows fractions at a glance."))
    A(tryit("From the free-time pie chart, how many children chose <b>reading or drawing</b> "
            "altogether, and how many <b>more</b> chose sports than drawing?",
            "Reading 6 + drawing 4 = <b>10</b> children. Sports 8 &minus; drawing 4 = <b>4</b> "
            "more."))

    # ===================== F . DRAW YOUR OWN =====================
    A(H("Part F &middot; Draw your own graph"))
    A(P("Real detectives also <b>make</b> graphs. A team scored these goals over four weeks: "
        "<b>Week 1: 3, Week 2: 5, Week 3: 2, Week 4: 6</b>. To draw a bar chart: draw a baseline, "
        "mark numbers up the side, draw each bar as tall as its value, label it, and add a title."))
    A(figure(bar_chart([("Wk 1", 3), ("Wk 2", 5), ("Wk 3", 2), ("Wk 4", 6)]),
             "Goals each week -- the bar chart you would draw. Total 16, mean 4."))
    A(tryit("From your goals chart, in which week were the <b>most</b> goals scored, what was the "
            "<b>total</b>, and what was the <b>mean</b> per week?",
            "Most: <b>Week 4</b> (6 goals). Total = 3 + 5 + 2 + 6 = <b>16</b>. Mean = 16 &divide; "
            "4 = <b>4</b> goals per week."))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now climb the data ladder"))
    A(P("Pick the right tool: mean (add then divide), median (middle in order), mode (most "
        "common), or read a chart. Peek only after a real try!"))

    A(practice("Remember", [
        ("To find the <b>mean</b>, you add the values and then do what?",
         "Divide by how many values there are."),
        ("What do we call the <b>middle</b> value of a sorted list?", "The median."),
        ("What do we call the value that appears <b>most often</b>?", "The mode."),
        ("On a bar chart, does a taller bar mean more or less?", "More."),
        ("In a pictograph, what tells you how much one picture is worth?", "The key."),
    ]))
    A(practice("Understand", [
        ("Find the mean of 4, 8, 6.", "Total 18 &divide; 3 = 6."),
        ("Find the median of 7, 3, 9 (sort them first).", "Sorted 3, 7, 9; the middle is 7."),
        ("Find the mode of 2, 4, 4, 6, 4.", "4 (it appears three times)."),
        ("In the fruit chart, how many children chose mango?", "10 children."),
        ("In the star pictograph (each star = 5), how many points does Mira have?",
         "5 stars &times; 5 = 25 points."),
    ]))
    A(practice("Apply", [
        ("Find the mean of 12, 15, 9, 8, 16.", "Total 60 &divide; 5 = 12."),
        ("In the runs chart, how many runs were scored in all 5 matches, and what is the mean?",
         "Total 45 + 60 + 30 + 75 + 40 = 250; mean = 250 &divide; 5 = 50 runs."),
        ("In the star pictograph (each star = 5), how many points did Aarav and Diya together "
         "earn?", "Aarav 20 + Diya 30 = 50 points."),
        ("In the free-time pie chart, how many more children chose sports than drawing?",
         "8 &minus; 4 = 4 more children."),
        ("Find the median of 4, 2, 8, 6 (an even-sized list).",
         "Sorted 2, 4, 6, 8; two middles 4 and 6, so median = (4 + 6) &divide; 2 = 5."),
    ]))
    A(practice("Analyze", [
        ("The mean of five numbers is 12. Four of them are 12, 15, 9 and 8. What is the fifth?",
         "Total must be 12 &times; 5 = 60; the four add to 44, so the fifth is 60 &minus; 44 = "
         "16."),
        ("In the fruit chart, is it true that more children chose mango than apple and grapes "
         "put together?",
         "Apple + grapes = 8 + 3 = 11, but mango is 10. So no &mdash; mango (10) is actually 1 "
         "fewer than apple-and-grapes (11)."),
        ("A child scored 8, 6, 10 and 8 on four tests. Find the mean and the mode.",
         "Mean = (8 + 6 + 10 + 8) &divide; 4 = 32 &divide; 4 = 8. Mode = 8 (it appears twice)."),
        ("In the free-time pie chart, write Sports and Drawing as fractions of the class of 24, "
         "in simplest form.",
         "Sports = 8/24 = 1/3; Drawing = 4/24 = 1/6."),
        ("Five friends have a mean of 20 sweets each. If four of them have 18, 22, 25 and 15, "
         "how many does the fifth have?",
         "Total = 20 &times; 5 = 100; the four add to 80, so the fifth has 100 &minus; 80 = 20."),
    ]))
    A(practice("Create", [
        ("Make up five test scores whose <b>mean</b> is exactly 10. Show they work.",
         "Many answers, e.g. 10, 10, 10, 10, 10 (total 50 &divide; 5 = 10), or 8, 12, 9, 11, 10 "
         "(total 50 &divide; 5 = 10)."),
        ("Invent a small data set (5 numbers) whose <b>mode</b> is 7 and whose <b>median</b> is "
         "also 7. Write the numbers.",
         "Example: 5, 7, 7, 7, 9 &mdash; sorted, the middle is 7 (median) and 7 appears most "
         "(mode)."),
        ("Draw a bar chart for goals over 4 weeks that totals 20, then write one how-many-more "
         "question about it.",
         "Any 4 bars adding to 20, e.g. 3, 7, 4, 6, with a question like &ldquo;How many more in "
         "week 2 than week 1?&rdquo; (answer 4)."),
        ("Make up four numbers whose <b>mean</b> is 6 but whose <b>mode</b> is 8. Write them "
         "and check.",
         "Example: 2, 8, 8, 6 has mean (2+8+8+6)&divide;4 = 24&divide;4 = 6, and mode = 8 (it "
         "appears most often). &#10003;"),
    ]))

    A(challenge(
        P("&#11088; <b>The Sports Day Mystery.</b> A pictograph shows medals won by four houses, "
          "where each medal-picture = <b>3 medals</b>. Red drew 4 pictures, Blue drew 5, Green "
          "drew 2, Yellow drew 3. (a) How many medals did each house win? (b) Which house won the "
          "most, and how many <b>more</b> than the last-place house? (c) What was the <b>mean</b> "
          "number of medals per house?") +
        figure(pictograph([("Red", 4), ("Blue", 5), ("Green", 2), ("Yellow", 3)],
                          icon="&#127941;", per=3),
               "Each medal-picture = 3 medals.") +
        tryit("Multiply each picture-count by 3; then compare, and use mean = total / 4.",
              "(a) Red 4&times;3 = <b>12</b>, Blue 5&times;3 = <b>15</b>, Green 2&times;3 = "
              "<b>6</b>, Yellow 3&times;3 = <b>9</b>. (b) <b>Blue</b> won most (15); last is "
              "<b>Green</b> (6); Blue won 15 &minus; 6 = <b>9</b> more. (c) Total = 12 + 15 + 6 + "
              "9 = 42, so mean = 42 &divide; 4 = <b>10.5</b> medals per house. (The mean can be a "
              "&ldquo;half&rdquo; even though no house won 10.5 &mdash; it's the balancing point, "
              "not a real medal count!) &#10003;")))

    A(kiwi("You're a true data detective now! &#127881; You can find the <b>mean</b> (fair "
           "share), <b>median</b> (middle) and <b>mode</b> (most common), and read or draw bar "
           "charts, pictographs and pie charts &mdash; finding the most, the least, the total, "
           "and how many more. That's the summit of our expedition, brilliant mathematician. Keep "
           "your detective eyes open: numbers, patterns and surprises are hiding everywhere, just "
           "waiting for you. &#128075;"))

    chapter("Part 7 · Data Detectives", 21, "Averages, Graphs & Data Handling",
            "Data Handling · Data Detectives", "".join(b))
