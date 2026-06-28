#!/usr/bin/env python3
"""Chapter 12 — Area  (Geometry · Measure Masters)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, area_grid, rect_fig)


def build(chapter):
    b = []
    A = b.append

    A(big_q("You want to cover a floor with square tiles, with no gaps and no overlaps. "
            "<b>How many tiles will it take?</b> The answer is a number called <em>area</em> — "
            "and counting little squares is the secret to finding it."))
    A(kiwi("Welcome back! In the last chapter, perimeter measured the trip <em>around</em> a shape. "
           "<b>Area</b> is different — it measures the <em>space inside</em>, like how much carpet covers "
           "a floor or how much paint covers a wall. We measure area by counting how many <b>unit "
           "squares</b> fit inside. Let's see what that means."))

    A(H("Area is counted in unit squares"))
    A(P("Imagine covering a shape with little squares that are each <b>1 cm by 1 cm</b>. We call each one "
        "a <b>square centimetre</b>, written <b>cm²</b>. The area is simply <em>how many of those little "
        "squares fit inside</em>. Here is a rectangle covered in unit squares:"))
    A(figure(area_grid(5, 3), "A 5 × 3 rectangle, covered in 1 cm unit squares"))
    A(example("count the squares", steps([
        "Count along one row: there are <b>5</b> squares in a row.",
        "Count the rows: there are <b>3</b> rows.",
        "Total squares = 5 + 5 + 5 = 15, which is the same as 5 × 3 = <b>15</b>.",
        "So the area is <b>15 cm²</b> — fifteen little squares fill the inside.",
    ])))
    A(kiwi("Did you spot the shortcut? Instead of counting every single square, we <b>multiplied the "
           "number in a row by the number of rows</b>. That's the big idea of area — and it leads "
           "straight to a rule."))

    A(P("Area is always measured in <b>square units</b>: square centimetres (cm²), square metres (m²), "
        "and so on. The little <b>²</b> reminds us we're counting <em>squares</em>, not just lengths."))

    A(tryit("How many unit squares are in a rectangle that is <b>4</b> squares across and <b>2</b> "
            "rows tall? What is its area?",
            "4 in each row × 2 rows = 8 squares, so the area is <b>8 square units</b>."))

    A(H("Area of a rectangle — length × width"))
    A(P("Because a rectangle is just rows of equal squares, we never need to draw and count every time. "
        "We can use a rule:"))
    A(figure(rect_fig("6 cm", "4 cm"), "A rectangle: length 6 cm, width 4 cm"))
    A(example("area of the 6 cm × 4 cm rectangle", steps([
        "Each row has <b>6</b> unit squares (the length).",
        "There are <b>4</b> rows (the width).",
        "Area = length × width = 6 × 4 = <b>24 cm²</b>.",
    ]) + P("<b>Rectangle rule:</b> Area = <b>length × width</b>.")))

    A(tryit("A rectangle is <b>8 cm</b> long and <b>5 cm</b> wide. What is its area?",
            "Area = length × width = 8 × 5 = <b>40 cm²</b>."))

    A(H("Area of a square — side × side"))
    A(P("A <b>square</b> has equal sides, so its length and width are the same number. The rule becomes "
        "even simpler — just multiply the side by itself."))
    A(figure(area_grid(4, 4), "A square that is 4 squares on each side"))
    A(example("area of a 4 cm square", steps([
        "The side is <b>4 cm</b>, so each row has 4 squares and there are 4 rows.",
        "Area = side × side = 4 × 4 = <b>16 cm²</b>.",
    ]) + P("<b>Square rule:</b> Area = <b>side × side</b>.")))

    A(tryit("A square has a side of <b>7 cm</b>. What is its area?",
            "Area = side × side = 7 × 7 = <b>49 cm²</b>."))

    A(H("Area and perimeter are NOT the same thing"))
    A(P("This is where many people get muddled, so let's be crystal clear. <b>Perimeter</b> is the "
        "distance <em>around</em> (add the sides). <b>Area</b> is the space <em>inside</em> (count the "
        "squares). They answer different questions and even have different units!"))
    A(figure(area_grid(4, 2), "A 4 × 2 rectangle — let's measure it both ways"))
    A(example("compare area and perimeter of the 4 × 2 rectangle", steps([
        "<b>Perimeter</b> (the trip around) = 4 + 2 + 4 + 2 = <b>12 cm</b>.",
        "<b>Area</b> (the squares inside) = 4 × 2 = <b>8 cm²</b>.",
        "Notice: perimeter is in <b>cm</b>, but area is in <b>cm²</b>. Different idea, different unit!",
    ])))
    A(kiwi("A way to remember: <b>P</b>erimeter is the <b>P</b>ath around the edge. <b>A</b>rea is the "
           "<b>A</b>mount of space inside. If you're buying a fence, you want perimeter. If you're "
           "buying carpet, you want area."))
    A(tryit("A square has a side of <b>5 cm</b>. Find <em>both</em> its perimeter and its area, "
            "with the right units.",
            "Perimeter = 4 × 5 = <b>20 cm</b>. Area = 5 × 5 = <b>25 cm²</b>. "
            "Same square, two different measurements!"))

    A(H("Working backwards — finding a missing side"))
    A(P("If you know the area and one side, you can find the other side by <em>dividing</em>. "
        "Suppose a rectangle has an area of <b>30 cm²</b> and a length of <b>6 cm</b>. How wide is it?"))
    A(figure(area_grid(6, 5), "30 unit squares fit in: 6 in each row, but how many rows?"))
    A(example("missing width from area", steps([
        "Area = length × width, so width = area ÷ length.",
        "Width = 30 ÷ 6 = <b>5 cm</b>.",
        "Check: 6 × 5 = 30 cm². ✓",
    ])))
    A(tryit("A square has an area of <b>36 cm²</b>. How long is one side?",
            "We need a number that times itself makes 36. Since 6 × 6 = 36, the side is <b>6 cm</b>."))

    A(H("Area in real life — tiles and carpet"))
    A(P("Whenever you <em>cover</em> a flat space, you're using area: tiling a floor, laying carpet, "
        "painting a wall, or planting grass in a field."))
    A(figure(area_grid(8, 5, unit="1 m"), "A kitchen floor tiled with 1 m² square tiles"))
    A(example("the floor tiles problem", P("A kitchen floor is a rectangle <b>8 m</b> long and "
        "<b>5 m</b> wide. Square tiles each cover <b>1 m²</b>. How many tiles are needed to cover the "
        "whole floor?") + steps([
        "Floor area = length × width = 8 × 5 = <b>40 m²</b>.",
        "Each tile covers 1 m², so the number of tiles = 40 ÷ 1 = <b>40 tiles</b>.",
    ])))
    A(tryit("A rug is <b>3 m</b> by <b>2 m</b>. It is laid on a floor that is <b>5 m</b> by <b>4 m</b>. "
            "How much floor area is <em>left uncovered</em>?",
            "Floor area = 5 × 4 = 20 m². Rug area = 3 × 2 = 6 m². "
            "Uncovered = 20 − 6 = <b>14 m²</b>."))

    A(H("Now you try — climb the ladder"))
    A(P("Take it step by step, and always check your <b>units</b> — area uses square units (²)!"))

    A(practice("Remember", [
        ("What does <b>area</b> measure?",
         "The amount of space inside a flat shape (how many unit squares fit)."),
        ("What is the rule for the area of a <b>rectangle</b>?",
         "Area = length × width."),
        ("What is the rule for the area of a <b>square</b>?",
         "Area = side × side."),
        ("What unit do we use for area: cm or cm²?",
         "cm² (square centimetres) — area is measured in square units."),
        ("Do we <b>add</b> or <b>multiply</b> to find the area of a rectangle?",
         "We multiply length × width."),
    ]))
    A(practice("Understand", [
        ("A rectangle is <b>7 cm</b> by <b>3 cm</b>. Find its area.",
         "7 × 3 = 21 cm²."),
        ("A square has side <b>6 cm</b>. Find its area.",
         "6 × 6 = 36 cm²."),
        ("How many unit squares are in a rectangle that is 9 across and 2 down?",
         "9 × 2 = 18 unit squares."),
        ("A rectangle is <b>10 m</b> long and <b>4 m</b> wide. What is its area?",
         "10 × 4 = 40 m²."),
        ("A square garden has side <b>8 m</b>. Find its area.",
         "8 × 8 = 64 m²."),
    ]))
    A(practice("Apply", [
        ("A floor is <b>6 m</b> by <b>5 m</b>. Tiles cover <b>1 m²</b> each. How many tiles are needed?",
         "Area = 6 × 5 = 30 m², so 30 tiles."),
        ("A rectangular field is <b>20 m</b> by <b>15 m</b>. What is its area?",
         "20 × 15 = 300 m²."),
        ("A square sheet of paper has side <b>12 cm</b>. Find its area.",
         "12 × 12 = 144 cm²."),
        ("Carpet costs ₹50 per square metre. How much does it cost to carpet a room "
         "<b>4 m</b> by <b>3 m</b>?",
         "Area = 4 × 3 = 12 m². Cost = 12 × ₹50 = ₹600."),
        ("A wall is <b>9 m</b> long and <b>3 m</b> high. How much paint area must be covered?",
         "9 × 3 = 27 m²."),
    ]))
    A(practice("Analyze", [
        ("A rectangle has an area of <b>24 cm²</b> and a length of <b>8 cm</b>. Find its width.",
         "Width = 24 ÷ 8 = 3 cm."),
        ("A square has an area of <b>81 cm²</b>. How long is one side?",
         "We need a number times itself = 81. Since 9 × 9 = 81, the side is 9 cm."),
        ("Rectangle A is 6 cm × 4 cm; rectangle B is 5 cm × 5 cm. <b>Which has the larger area, "
         "and by how much?</b>",
         "A = 6 × 4 = 24 cm²; B = 5 × 5 = 25 cm². B is larger by 25 − 24 = 1 cm²."),
        ("A rectangle is 8 cm long and 3 cm wide. Find its <b>area</b> and its <b>perimeter</b>.",
         "Area = 8 × 3 = 24 cm². Perimeter = 2 × (8 + 3) = 2 × 11 = 22 cm. (Different units!)"),
        ("A big square of side 6 cm has a small square of side 2 cm cut out of a corner. "
         "What area is <b>left</b>?",
         "Big area = 6 × 6 = 36 cm². Small cut-out = 2 × 2 = 4 cm². Left = 36 − 4 = 32 cm²."),
    ]))
    A(practice("Create", [
        ("Find <b>two different</b> rectangles that each have an area of <b>12 cm²</b>. Give the "
         "length and width of each.",
         "Any two whose length × width = 12 work, e.g. 6 cm × 2 cm and 4 cm × 3 cm "
         "(both give 12 cm²); 12 cm × 1 cm also works."),
        ("Draw a rectangle and a square that have the <b>same area</b> of <b>16 cm²</b>. State both.",
         "Square: side 4 cm (4 × 4 = 16). Rectangle: 8 cm × 2 cm (8 × 2 = 16). Same area, "
         "different shapes."),
        ("Invent a tiling problem of your own: pick a room size and a tile size, then say how many "
         "tiles are needed.",
         "Example: a room 6 m × 4 m has area 24 m². With 1 m² tiles that's 24 tiles. "
         "(Any consistent room and tile sizes work.)"),
    ]))

    A(challenge(
        P("A rectangular garden is <b>10 m</b> long and <b>6 m</b> wide. A square pond of side "
          "<b>3 m</b> sits inside it. The rest of the garden is covered with grass. "
          "<b>What area of grass is there?</b> If grass turf costs ₹20 per square metre, what is "
          "the total cost of the grass?") +
        tryit("Find the whole area, subtract the pond, then work out the cost.",
              "Garden area = 10 × 6 = <b>60 m²</b>. Pond area = 3 × 3 = <b>9 m²</b>. "
              "Grass area = 60 − 9 = <b>51 m²</b>. Cost = 51 × ₹20 = <b>₹1020</b>.")))

    A(kiwi("Good work — you used length × width to fill the inside with squares, exactly as area should. You can now count squares, use <b>length × width</b> and <b>side × side</b>, tell "
           "area apart from perimeter, and even handle cut-out shapes! Next we leave flat shapes behind "
           "and meet <b>3D solids</b> like cubes and cones — and discover how flat <b>nets</b> fold up "
           "into them. See you in Chapter 13! 📦"))

    chapter("Part 4 · Measure Masters & Turn & Flip", 12, "Area",
            "Geometry · Measure Masters", "".join(b))
