#!/usr/bin/env python3
"""Chapter 11 — Perimeter  (Geometry · Measure Masters)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, rect_fig, polygon)


def build(chapter):
    b = []
    A = b.append

    A(big_q("An ant walks <b>all the way around</b> the edge of a garden and comes back to where it "
            "started. How far did the little ant walk? That total distance has a special name — and "
            "you can always find it just by <em>adding</em>."))
    A(kiwi("Hi again, it's <b>Kiwi</b>! The distance <em>around</em> the outside of a flat shape is called "
           "its <b>perimeter</b>. Think of building a fence around a field, or running once around a "
           "playground — the length of that whole trip is the perimeter. The trick is wonderfully simple: "
           "<b>walk every side and add the side lengths together</b>."))

    A(H("Perimeter means: add up every side"))
    A(P("Perimeter is the total length of the <b>border</b> of a shape. To find it, start at one corner, "
        "travel along each side, and add the lengths as you go — all the way back to the start."))
    A(P("Here is a triangular flag. Walk its three sides one by one:"))
    A(figure(polygon([(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)], labels=["5 cm", "4 cm", "6 cm"]),
             "A triangle with sides 5 cm, 4 cm and 6 cm"))
    A(example("perimeter of the triangle flag", steps([
        "Side 1 = <b>5 cm</b>, side 2 = <b>4 cm</b>, side 3 = <b>6 cm</b>.",
        "Add every side: 5 + 4 + 6 = <b>15 cm</b>.",
        "So the perimeter — the distance all the way around — is <b>15 cm</b>.",
    ]) + P("That's it! No matter how many sides a shape has, perimeter is always just "
           "<em>side + side + side + …</em>")))

    A(kiwi("A quick reminder about <b>units</b>: perimeter is a <em>length</em>, so we measure it in "
           "length units — centimetres (cm), metres (m), and so on. If the sides are in cm, the "
           "perimeter is in cm too. Always write the unit!"))

    A(tryit("A triangle has sides <b>8 cm, 8 cm and 3 cm</b>. What is its perimeter?",
            "Add all three sides: 8 + 8 + 3 = <b>19 cm</b>."))

    A(H("Perimeter of a square — a speedy shortcut"))
    A(P("A <b>square</b> is special: all four sides are exactly the <em>same</em> length. "
        "Look at this square tile whose side is 5 cm."))
    A(figure(rect_fig("5 cm", "5 cm", px=130, py=130, fill="#39A85B"),
             "A square tile — every side is 5 cm"))
    A(P("We could add 5 + 5 + 5 + 5, but adding the same number four times is the same as "
        "<b>multiplying by 4</b>. That gives us a shortcut:"))
    A(example("perimeter of the 5 cm square", steps([
        "All four sides are equal, each <b>5 cm</b>.",
        "Long way: 5 + 5 + 5 + 5 = <b>20 cm</b>.",
        "Shortcut: <b>4 × side</b> = 4 × 5 = <b>20 cm</b>. Same answer, less work!",
    ]) + P("<b>Square rule:</b> Perimeter = <b>4 × side</b>.")))

    A(tryit("A square garden has a side of <b>9 m</b>. What is its perimeter?",
            "Use the square rule: 4 × 9 = <b>36 m</b>."))

    A(H("Perimeter of a rectangle — pair up the sides"))
    A(P("A <b>rectangle</b> has two long sides (the <b>length</b>) and two short sides (the <b>width</b>). "
        "The two lengths match each other, and the two widths match each other."))
    A(figure(rect_fig("8 cm", "3 cm"), "A rectangle: length 8 cm, width 3 cm"))
    A(P("Going around, we pass: length, width, length, width. So we add the length twice and the "
        "width twice. There are two neat ways to write this:"))
    A(example("perimeter of the 8 cm × 3 cm rectangle", steps([
        "Add all four sides: 8 + 3 + 8 + 3 = <b>22 cm</b>.",
        "Smart way: one length + one width = 8 + 3 = 11 cm; there are two of these pairs, "
        "so 2 × 11 = <b>22 cm</b>.",
        "<b>Rectangle rule:</b> Perimeter = <b>2 × (length + width)</b> = 2 × (8 + 3) = 2 × 11 = 22 cm.",
    ])))
    A(kiwi("Why does <b>2 × (length + width)</b> work? Because a rectangle has two lengths and two widths. "
           "Adding one length and one width gives you <em>half</em> the trip around; double it and you've "
           "gone all the way. A square is just a rectangle whose length and width are equal — that's why "
           "<em>its</em> shortcut is 4 × side."))

    A(tryit("A rectangle has length <b>10 m</b> and width <b>6 m</b>. Find its perimeter two ways.",
            "Add the sides: 10 + 6 + 10 + 6 = <b>32 m</b>. Or 2 × (10 + 6) = 2 × 16 = <b>32 m</b>. "
            "Both give 32 m. ✓"))

    A(H("Working backwards — finding a missing side"))
    A(P("Sometimes you know the perimeter but a side is hidden. You can work <em>backwards</em>! "
        "Suppose a square has a perimeter of <b>28 cm</b>. What is one side?"))
    A(figure(rect_fig("? cm", "? cm", px=120, py=120, fill="#8B5CF6"),
             "A square with perimeter 28 cm — but what is one side?"))
    A(example("missing side of a square", steps([
        "A square has 4 equal sides, and 4 × side = perimeter.",
        "So side = perimeter ÷ 4 = 28 ÷ 4 = <b>7 cm</b>.",
        "Check: 4 × 7 = 28 cm. ✓",
    ])))
    A(tryit("A rectangle has a perimeter of <b>20 cm</b> and a length of <b>7 cm</b>. "
            "What is its width?",
            "Two lengths use up 7 + 7 = 14 cm. The two widths must make 20 − 14 = 6 cm, "
            "so one width = 6 ÷ 2 = <b>3 cm</b>. Check: 2 × (7 + 3) = 2 × 10 = 20 cm. ✓"))

    A(H("Tricky shapes? Just keep adding"))
    A(P("Real gardens and rooms aren't always neat rectangles — some have an <b>L-shape</b> or a "
        "zig-zag border. Don't worry: the rule never changes. <b>Walk every side and add.</b> "
        "Here is an L-shaped flower bed (all lengths in metres):"))
    A(figure(polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 0.55), (0.45, 0.55), (0.45, 1.0), (0.0, 1.0)],
                     labels=["8", "3", "4", "3", "4", "6"], fill="#39A85B"),
             "An L-shaped flower bed (sides in metres)"))
    A(example("perimeter of the L-shaped bed", steps([
        "List every side as you go around: 8, 3, 4, 3, 4, 6 (all in metres).",
        "Add them all: 8 + 3 + 4 + 3 + 4 + 6 = <b>28 m</b>.",
        "So you'd need <b>28 m</b> of fencing to go all the way around.",
    ]) + P("The shape has 6 sides, so we added 6 numbers. Easy — just don't miss a side!")))
    A(kiwi("<b>Counting tip:</b> touch each side with your finger as you add it, then put a tiny tick on "
           "it. When every side has a tick, you know you haven't skipped one or counted one twice."))

    A(H("Perimeter in real life — fences and wire"))
    A(P("Perimeter shows up everywhere you go <em>around</em> something: fencing a garden, putting lace "
        "around a tablecloth, a frame around a picture, or wire around a board. These are all "
        "perimeter problems wearing a costume."))
    A(figure(rect_fig("12 m", "12 m", px=130, py=130, fill="#39A85B"),
             "Riya's square vegetable patch — each side is 12 m"))
    A(example("the fencing problem", P("Riya wants to put a fence around her square vegetable patch. "
        "Each side is <b>12 m</b>. Fencing wire costs ₹5 per metre. How much wire does she need, and "
        "how much will it cost?") + steps([
        "Perimeter of the square patch = 4 × 12 = <b>48 m</b> of wire.",
        "Cost = 48 m × ₹5 each = ₹240.",
        "So Riya needs <b>48 m</b> of wire costing <b>₹240</b>.",
    ])))

    A(tryit("A rectangular photo is <b>15 cm</b> long and <b>10 cm</b> wide. How long a frame strip "
            "is needed to go all the way around it?",
            "Perimeter = 2 × (15 + 10) = 2 × 25 = <b>50 cm</b> of frame strip."))

    A(H("Now you try — climb the ladder"))
    A(P("Start gentle and rise step by step. Try each yourself before you peek!"))

    A(practice("Remember", [
        ("What does <b>perimeter</b> mean?",
         "The total distance all the way around the outside of a shape."),
        ("To find a perimeter, do you <b>add</b> the sides or <b>multiply</b> them?",
         "You add the lengths of all the sides."),
        ("What is the shortcut rule for the perimeter of a <b>square</b>?",
         "Perimeter = 4 × side."),
        ("What is the rule for the perimeter of a <b>rectangle</b>?",
         "Perimeter = 2 × (length + width)."),
        ("If a triangle's sides are 6 cm, 7 cm and 9 cm, what do you add to get the perimeter?",
         "6 + 7 + 9 = 22 cm."),
    ]))
    A(practice("Understand", [
        ("Find the perimeter of a triangle with sides <b>3 cm, 5 cm and 7 cm</b>.",
         "3 + 5 + 7 = 15 cm."),
        ("Find the perimeter of a square with side <b>8 cm</b>.",
         "4 × 8 = 32 cm."),
        ("Find the perimeter of a rectangle with length <b>9 m</b> and width <b>4 m</b>.",
         "2 × (9 + 4) = 2 × 13 = 26 m."),
        ("A square has side <b>15 cm</b>. What is its perimeter?",
         "4 × 15 = 60 cm."),
        ("A rectangle is <b>12 cm</b> by <b>5 cm</b>. Find its perimeter.",
         "2 × (12 + 5) = 2 × 17 = 34 cm."),
    ]))
    A(practice("Apply", [
        ("A square park has side <b>25 m</b>. How much fencing goes around it?",
         "4 × 25 = 100 m of fencing."),
        ("A rectangular notebook is <b>24 cm</b> long and <b>18 cm</b> wide. Find the perimeter.",
         "2 × (24 + 18) = 2 × 42 = 84 cm."),
        ("Wire costs ₹3 per metre. How much does it cost to fence a square plot of side <b>20 m</b>?",
         "Perimeter = 4 × 20 = 80 m. Cost = 80 × ₹3 = ₹240."),
        ("An equilateral triangle (all sides equal) has each side <b>14 cm</b>. Find its perimeter.",
         "3 × 14 = 42 cm."),
        ("A rectangular garden is <b>30 m</b> by <b>20 m</b>. A gardener walks around it <b>twice</b>. "
         "How far does she walk?",
         "Once around = 2 × (30 + 20) = 2 × 50 = 100 m. Twice around = 2 × 100 = 200 m."),
    ]))
    A(practice("Analyze", [
        ("A square has a perimeter of <b>36 cm</b>. How long is one side?",
         "Side = 36 ÷ 4 = 9 cm."),
        ("A rectangle has a perimeter of <b>30 cm</b> and a length of <b>9 cm</b>. Find its width.",
         "Two lengths = 9 + 9 = 18 cm; the two widths make 30 − 18 = 12 cm, so width = 12 ÷ 2 = 6 cm."),
        ("Two squares: one has side 6 cm, the other side 8 cm. <b>Which has the larger perimeter, "
         "and by how much?</b>",
         "Perimeters are 4 × 6 = 24 cm and 4 × 8 = 32 cm. The side-8 square is larger by 32 − 24 = 8 cm."),
        ("An L-shaped path has sides <b>10, 4, 6, 3, 4, 7</b> metres. Find its perimeter.",
         "10 + 4 + 6 + 3 + 4 + 7 = 34 m."),
        ("A rectangle and a square both have a perimeter of <b>24 cm</b>. The rectangle is "
         "<b>8 cm</b> long. Find the square's side and the rectangle's width.",
         "Square: side = 24 ÷ 4 = 6 cm. Rectangle: two lengths = 16 cm, two widths = 24 − 16 = 8 cm, "
         "so width = 4 cm."),
    ]))
    A(practice("Create", [
        ("Draw and label a rectangle whose perimeter is exactly <b>20 cm</b>. (Many answers are "
         "possible!)",
         "Any rectangle where length + width = 10 cm works, because 2 × 10 = 20. Examples: 7 cm × 3 cm, "
         "6 cm × 4 cm, or 8 cm × 2 cm."),
        ("Invent a triangle with a perimeter of <b>18 cm</b> using three <em>different</em> side lengths.",
         "Pick three different numbers that add to 18, e.g. 4 cm, 6 cm and 8 cm (4 + 6 + 8 = 18). "
         "(The longest side must be shorter than the other two added together — 8 &lt; 4 + 6 ✓.)"),
        ("Design a square flag and a rectangular flag that use the <b>same length</b> of edging ribbon. "
         "State both perimeters.",
         "Make both perimeters equal, e.g. a square of side 5 cm (perimeter 20 cm) and a rectangle "
         "6 cm × 4 cm (perimeter 2 × 10 = 20 cm). Both use 20 cm of ribbon."),
    ]))

    A(challenge(
        P("A rectangular field is <b>40 m</b> long and <b>25 m</b> wide. The farmer wants to put "
          "<b>3 rows</b> of wire all the way around it to keep the goats in. Wire costs ₹4 per metre. "
          "How many metres of wire are needed, and what is the total cost?") +
        tryit("Find the perimeter first, then handle the 3 rows and the cost.",
              "Perimeter of one row = 2 × (40 + 25) = 2 × 65 = <b>130 m</b>. Three rows = 3 × 130 = "
              "<b>390 m</b> of wire. Cost = 390 × ₹4 = <b>₹1560</b>.")))

    A(kiwi("Nice — you added up every side to go right around the shape, which is exactly what perimeter "
           "means. You can now find the perimeter of triangles, squares, rectangles and even "
           "wiggly L-shapes — and work backwards to find a missing side. Next we'll explore the "
           "<b>space inside</b> a shape, which is called <b>area</b>. Perimeter goes <em>around</em>; "
           "area fills the <em>inside</em>. On to Chapter 12! 🌿"))

    chapter("Part 4 · Measure Masters & Turn & Flip", 11, "Perimeter",
            "Geometry · Measure Masters", "".join(b))
