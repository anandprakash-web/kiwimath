#!/usr/bin/env python3
"""Chapter 20 — Bar Charts, Pictographs & Circle Graphs  (Data Handling · Data Detectives)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, bar_chart, pictograph, pie)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Imagine you asked everyone in your class, What is your favourite fruit? "
            "You'd get a big messy pile of answers. How can you turn that pile into one neat picture "
            "that tells the whole story at a single glance?"))
    A(kiwi("Hello, data detective! It's <b>Kiwi</b> again. Numbers are clues, and a <b>graph</b> is the picture "
           "that makes the clues easy to read. In this chapter you'll learn to <em>read</em> three kinds of graphs "
           "&mdash; and even <em>draw</em> your own. Let's go hunting for what the data is hiding! &#128202;"))

    # ===================== BAR CHARTS =====================
    A(H("Bar charts &mdash; taller means more"))
    A(P("A <b>bar chart</b> (or bar graph) uses <b>bars</b> to show amounts. The taller the bar, the bigger the "
        "number. Each bar has a <b>label</b> at the bottom telling you what it stands for, and you read its value "
        "from the number at its top. Here is the favourite-fruit survey for one class:"))
    A(figure(bar_chart([("Apple", 8), ("Banana", 5), ("Mango", 10), ("Grapes", 3)]),
             "Favourite fruit of the class. Each bar's height is the number of children who chose it."))
    A(P("To <b>read a value</b>, find the bar's label, then look at the number at the top of that bar. "
        "Mango's bar reaches <b>10</b>, so 10 children chose mango. Apple's reaches 8, banana's 5, grapes' 3."))
    A(kiwi("Four detective questions work on <em>every</em> chart: "
           "(1) Which is the <b>most</b>? (the tallest bar) "
           "(2) Which is the <b>least</b>? (the shortest bar) "
           "(3) What is the <b>total</b>? (add all the bars) "
           "(4) <b>How many more</b>? (subtract one bar from another)."))

    A(example("Reading the fruit bar chart", steps([
        "<b>Most popular?</b> The tallest bar is <b>Mango</b> at 10 &mdash; that's the favourite. &#10003;",
        "<b>Least popular?</b> The shortest bar is <b>Grapes</b> at 3.",
        "<b>Total children?</b> Add every bar: 8 + 5 + 10 + 3 = <b>26</b> children.",
        "<b>How many more chose mango than grapes?</b> 10 &minus; 3 = <b>7</b> more.",
    ])))
    A(P("That last kind &mdash; <b>how many more</b> (or fewer) &mdash; is just a subtraction between two bars. "
        "Always take the <em>bigger</em> bar minus the <em>smaller</em> one."))
    A(tryit("Using the fruit chart, how many more children chose <b>apple</b> than <b>banana</b>?",
            "Apple is 8 and banana is 5, so 8 &minus; 5 = <b>3</b> more children chose apple."))
    A(tryit("Using the fruit chart, how many children chose <b>apple or grapes</b> altogether?",
            "Apple (8) + grapes (3) = <b>11</b> children."))

    A(P("Bar charts are perfect for comparing things <em>over time</em> too. Here is how many books one reader "
        "finished on each school day:"))
    A(figure(bar_chart([("Mon", 4), ("Tue", 6), ("Wed", 2), ("Thu", 8), ("Fri", 5)]),
             "Books read each day. The bars rise and fall, showing busy days and slow days."))
    A(example("Reading the books-per-day chart", steps([
        "<b>Best reading day?</b> The tallest bar is <b>Thursday</b> at 8 books.",
        "<b>Slowest day?</b> The shortest bar is <b>Wednesday</b> at 2 books.",
        "<b>Books all week?</b> 4 + 6 + 2 + 8 + 5 = <b>25</b> books.",
        "<b>How many more on Thursday than Wednesday?</b> 8 &minus; 2 = <b>6</b> more books. &#10003;",
    ])))

    # ===================== PICTOGRAPHS =====================
    A(H("Pictographs &mdash; counting with pictures"))
    A(P("A <b>pictograph</b> uses a little <b>picture</b> (an icon) to stand for an amount. The most important "
        "thing to spot is the <b>key</b> at the bottom &mdash; it tells you how much <em>one</em> picture is worth. "
        "If each star means 2, then 3 stars means 3 &times; 2 = 6!"))
    A(figure(pictograph([("Aarav", 4), ("Diya", 6), ("Kabir", 3), ("Mira", 5)], icon="&#11088;", per=2),
             "Reward stars earned this week. Read the key: each star is worth 2 points."))
    A(kiwi("Golden rule for pictographs: <b>count the pictures, then multiply by the key.</b> "
           "Never just count pictures &mdash; always check what one picture is worth first!"))
    A(example("Reading the star pictograph (each star = 2)", steps([
        "Diya has <b>6 stars</b>. Each star is worth 2, so Diya's points = 6 &times; 2 = <b>12</b>.",
        "Aarav has 4 stars &rarr; 4 &times; 2 = <b>8</b> points.",
        "Kabir has 3 stars &rarr; 3 &times; 2 = <b>6</b> points; Mira has 5 stars &rarr; 5 &times; 2 = <b>10</b> points.",
        "<b>Who earned the most?</b> Diya (12 points) &mdash; she has the most stars. &#10003;",
        "<b>How many more points has Diya than Kabir?</b> 12 &minus; 6 = <b>6</b> points.",
    ])))
    A(tryit("In the star pictograph (each star = 2), how many points did <b>Aarav and Kabir together</b> earn?",
            "Aarav = 4 &times; 2 = 8 and Kabir = 3 &times; 2 = 6, so together 8 + 6 = <b>14</b> points."))
    A(tryit("If a new friend earned <b>16</b> points, how many stars would they draw (each star = 2)?",
            "Work backwards: 16 &divide; 2 = <b>8</b> stars."))

    # ===================== CIRCLE / PIE GRAPHS =====================
    A(H("Circle graphs &mdash; slices of the whole"))
    A(P("A <b>circle graph</b> (also called a <b>pie graph</b>) shows how one whole thing is split into parts. "
        "The <b>whole circle</b> is everything together, and each coloured <b>slice</b> is one part. A bigger slice "
        "means a bigger share. Here's how a class of 24 children spend their free time:"))
    A(figure(pie([("Reading", 6), ("Sports", 8), ("Drawing", 4), ("Music", 6)]),
             "Free-time choices of 24 children. The biggest slice is the most popular activity."))
    A(P("Read a circle graph by its slices and the <b>legend</b> (the little colour key on the side). "
        "The biggest slice is <b>Sports</b> (8 children), and the smallest is <b>Drawing</b> (4 children). "
        "All the slices together make the whole class: 6 + 8 + 4 + 6 = <b>24</b>. &#10003;"))
    A(example("Reading the free-time circle graph", steps([
        "<b>Most popular activity?</b> The largest slice is <b>Sports</b>, chosen by 8 children.",
        "<b>Least popular?</b> The smallest slice is <b>Drawing</b>, chosen by 4 children.",
        "<b>How many more chose sports than drawing?</b> 8 &minus; 4 = <b>4</b> more children.",
        "<b>Do reading and music together make half the class?</b> 6 + 6 = 12, and half of 24 is 12 &mdash; "
        "yes, exactly <b>half</b>! &#10003;",
    ])))
    A(kiwi("Detective check for circle graphs: the slices must <em>always add up to the whole</em>. If you add "
           "every slice and don't get the total, a clue has gone missing &mdash; look again!"))
    A(tryit("In the free-time circle graph, how many children chose <b>reading or drawing</b> altogether?",
            "Reading (6) + drawing (4) = <b>10</b> children."))

    # ===================== DRAW YOUR OWN =====================
    A(H("Draw your own graph"))
    A(P("Reading graphs is great &mdash; but real detectives also <b>make</b> them. Here's a tiny survey: a "
        "football team scored these goals over four weeks: <b>Week 1: 3, Week 2: 5, Week 3: 2, Week 4: 6</b>."))
    A(P("To draw a <b>bar chart</b>, follow these steps:"))
    A(steps([
        "Draw a flat line along the bottom (this holds your labels) and mark numbers going up the side.",
        "For each week, draw a <b>bar</b> as tall as its number of goals.",
        "Write the week's name under its bar and the number at its top.",
        "Give your chart a <b>title</b>, like Goals Scored Each Week.",
    ]))
    A(P("Here is what your finished chart would look like:"))
    A(figure(bar_chart([("Wk 1", 3), ("Wk 2", 5), ("Wk 3", 2), ("Wk 4", 6)]),
             "Goals scored each week &mdash; the bar chart you would draw."))
    A(tryit("From your goals chart, in which week were the <b>most</b> goals scored, and how many goals "
            "were scored in <b>all four weeks</b>?",
            "The tallest bar is <b>Week 4</b> with 6 goals. Total = 3 + 5 + 2 + 6 = <b>16</b> goals."))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now you try &mdash; climb the data ladder"))
    A(P("Each question uses one of the charts above &mdash; read carefully, then check your answer!"))

    A(practice("Remember", [
        ("On a bar chart, does a <b>taller</b> bar mean more or less?", "More."),
        ("In a pictograph, what do we call the note that says how much one picture is worth?", "The key."),
        ("In the fruit chart, how many children chose <b>mango</b>?", "10 children."),
        ("In a circle graph, what do all the slices added together make?", "The whole (the total)."),
        ("In the star pictograph, how many stars does <b>Diya</b> have drawn?", "6 stars."),
    ]))
    A(practice("Understand", [
        ("In the books-per-day chart, which day had the <b>fewest</b> books read?", "Wednesday (2 books)."),
        ("In the star pictograph, each star = 2. How many points does <b>Mira</b> have?",
         "5 stars &times; 2 = <b>10</b> points."),
        ("In the free-time circle graph, which activity is the <b>most</b> popular?", "Sports (8 children)."),
        ("In the fruit chart, how many children chose <b>banana</b>?", "5 children."),
        ("In the goals chart, how many goals were scored in <b>Week 3</b>?", "2 goals."),
    ]))
    A(practice("Apply", [
        ("In the fruit chart, what is the <b>total</b> number of children surveyed?",
         "8 + 5 + 10 + 3 = <b>26</b> children."),
        ("In the books-per-day chart, how many <b>more</b> books were read on <b>Thursday</b> than on <b>Tuesday</b>?",
         "Thursday 8 &minus; Tuesday 6 = <b>2</b> more books."),
        ("In the star pictograph (each star = 2), how many points did <b>Aarav and Diya together</b> earn?",
         "Aarav 4&times;2 = 8 and Diya 6&times;2 = 12, so 8 + 12 = <b>20</b> points."),
        ("In the free-time circle graph, how many more children chose <b>sports</b> than <b>drawing</b>?",
         "8 &minus; 4 = <b>4</b> more children."),
        ("In the goals chart, what was the total number of goals across all four weeks?",
         "3 + 5 + 2 + 6 = <b>16</b> goals."),
    ]))
    A(practice("Analyze", [
        ("In the fruit chart, is it true that <b>more</b> children chose mango than apple and grapes "
         "<em>put together</em>?",
         "Apple + grapes = 8 + 3 = 11, but mango is only 10. So <b>no</b> &mdash; mango (10) is actually 1 <em>fewer</em> "
         "than apple-and-grapes together (11)."),
        ("In the star pictograph (each star = 2), what is the <b>total</b> number of points earned by all four "
         "children?",
         "8 + 12 + 6 + 10 = <b>36</b> points (or count all 18 stars &times; 2 = 36)."),
        ("In the free-time circle graph, do <b>reading and music together</b> make up half the class? Explain.",
         "Reading 6 + music 6 = 12, and half of the 24 children is 12, so <b>yes</b> &mdash; together they are exactly half."),
        ("In the books-per-day chart, on how many days were <b>more than 4</b> books read?",
         "Tuesday (6) and Thursday (8) are above 4, and Friday (5) is too, so <b>3 days</b>."),
        ("Looking at the fruit chart, if 4 more children joined and all chose <b>grapes</b>, would grapes still be "
         "the least popular?",
         "Grapes would become 3 + 4 = 7, while banana stays 5. So <b>no</b> &mdash; banana (5) would then be the least."),
    ]))
    A(practice("Create", [
        ("Survey 5 friends about their favourite colour and <b>draw a bar chart</b> of the results. Then write "
         "one how-many-more question about it.",
         "Any neat bar chart with a title, labels, and bar heights matching your tallies &mdash; plus a question like "
         "How many more chose blue than red?"),
        ("Make a pictograph for 'cups of water drunk' where each cup-picture = 5, and Sam drinks 20. How many "
         "cup-pictures would Sam's row have?",
         "20 &divide; 5 = <b>4</b> cup-pictures."),
        ("Invent a circle-graph story for a class of 20 where reading is the biggest slice. Give numbers that "
         "add to 20.",
         "Any set that totals 20 with reading largest, e.g. Reading 9, Sports 6, Games 5 (9 + 6 + 5 = 20)."),
    ]))

    A(challenge(
        P("&#127942; <b>The Sports Day Mystery.</b> A pictograph shows medals won by four houses, where each "
          "medal-picture = <b>3 medals</b>. Red drew 4 pictures, Blue drew 5, Green drew 2, and Yellow drew 3. "
          "(a) How many medals did each house win? (b) Which house won the most, and how many <b>more</b> did they "
          "win than the house that came last?") +
        tryit("Multiply each picture-count by 3, then compare.",
              "(a) Red 4&times;3 = <b>12</b>, Blue 5&times;3 = <b>15</b>, Green 2&times;3 = <b>6</b>, Yellow 3&times;3 = <b>9</b>. "
              "(b) <b>Blue</b> won the most with 15 medals; the last-place house is <b>Green</b> with 6. "
              "Blue won 15 &minus; 6 = <b>9</b> more medals than Green.")))

    A(kiwi("You're a true data detective now! &#127881; You can read bar charts, pictographs and circle graphs &mdash; "
           "finding the most, the least, the total, and how many more &mdash; and you can even draw your own. "
           "That's the end of our grand adventure, brilliant mathematician. Keep your detective eyes open: "
           "numbers and patterns are hiding everywhere, just waiting for you to solve them. &#128075;"))

    chapter("Part 6 · Data Detectives", 20, "Bar Charts, Pictographs & Circle Graphs",
            "Data Handling · Data Detectives", "".join(b))
