#!/usr/bin/env python3
"""Chapter 13 — 2D & 3D Shapes & Nets  (Geometry · Shapes & Solids)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, polygon, solid, cube_net)


def build(chapter):
    b = []
    A = b.append

    A(big_q("A sheet of paper is <b>flat</b>, but a dice is <b>solid</b> — you can hold it. "
            "What makes a shape flat or solid? And here's the magic question: "
            "<em>could you fold a flat sheet to make a solid box?</em>"))
    A(kiwi("Hello again! Shapes come in two families. <b>Flat shapes</b> — like a drawing on paper — are "
           "called <b>2D shapes</b> (two-dimensional). <b>Solid shapes</b> you can pick up — like a ball "
           "or a box — are called <b>3D shapes</b> (three-dimensional). Let's get to know both, then "
           "watch a flat shape fold into a solid one!"))

    A(H("2D shapes — sides and corners"))
    A(P("A <b>2D shape</b> is flat. We describe it by counting its <b>sides</b> (the straight edges) and "
        "its <b>corners</b> (also called <b>vertices</b> — the points where two sides meet). Let's meet "
        "the famous ones."))
    A(figure(polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], labels=["", "", "", ""],
                     fill="#3B9CE6"), "A square — 4 equal sides, 4 corners"))
    A(figure(polygon([(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)], labels=["", "", ""], fill="#39A85B"),
             "A triangle — 3 sides, 3 corners"))
    A(figure(polygon([(0.5, 0.0), (1.0, 0.4), (0.8, 1.0), (0.2, 1.0), (0.0, 0.4)],
                     labels=["", "", "", "", ""], fill="#E0556E"),
             "A pentagon — 5 sides, 5 corners"))
    A(P("Here is a handy table of common flat shapes:"))
    A('<table class="pv"><tr><th>Shape</th><th>Sides</th><th>Corners</th></tr>'
      '<tr><td>Triangle</td><td>3</td><td>3</td></tr>'
      '<tr><td>Square / Rectangle</td><td>4</td><td>4</td></tr>'
      '<tr><td>Pentagon</td><td>5</td><td>5</td></tr>'
      '<tr><td>Hexagon</td><td>6</td><td>6</td></tr>'
      '<tr><td>Circle</td><td>0 (1 curved side)</td><td>0</td></tr></table>')
    A(kiwi("Spot the pattern? For shapes with straight sides, the number of <b>sides</b> always equals the "
           "number of <b>corners</b>! A triangle has 3 of each, a pentagon has 5 of each. A circle is the "
           "odd one out — one smooth curved side and no corners at all."))
    A(tryit("A shape has <b>6</b> straight sides. What is it called, and how many corners does it have?",
            "Six sides makes it a <b>hexagon</b>, and it has <b>6</b> corners (sides = corners)."))

    A(H("3D shapes — faces, edges and vertices"))
    A(P("Solid shapes are described with three special words. Picture a building block:"))
    A(P("• A <b>face</b> is a flat (or curved) surface — like one side of a box.<br>"
        "• An <b>edge</b> is a line where two faces meet.<br>"
        "• A <b>vertex</b> is a corner point where edges meet (the plural is <b>vertices</b>)."))
    A(figure(solid("cube"), "A cube — count its faces, edges and vertices"))
    A(example("counting on a cube", steps([
        "<b>Faces:</b> a cube has a top, a bottom, and 4 sides → <b>6 faces</b> (all squares).",
        "<b>Edges:</b> 4 around the top, 4 around the bottom, and 4 standing up → <b>12 edges</b>.",
        "<b>Vertices:</b> 4 corners on top and 4 on the bottom → <b>8 vertices</b>.",
    ])))
    A(P("A <b>cuboid</b> (a box shape, like a brick or a cereal packet) has the <em>same</em> counts as a "
        "cube — its faces are just rectangles instead of squares:"))
    A(figure(solid("cuboid"), "A cuboid (box) — 6 faces, 12 edges, 8 vertices"))

    A(H("Solids with curves — cones, cylinders and spheres"))
    A(P("Not all solids are made of flat squares and rectangles. Some have <b>curved</b> surfaces. "
        "Let's meet three of them."))
    A(figure(solid("cone"), "A cone — like an ice-cream cone or a party hat"))
    A(figure(solid("cylinder"), "A cylinder — like a tin can or a drum"))
    A(figure(solid("sphere"), "A sphere — like a ball or a globe"))
    A(P("Here is a count of all five solids. The curved ones surprise people, so look closely!"))
    A('<table class="pv"><tr><th>Solid</th><th>Faces</th><th>Edges</th><th>Vertices</th></tr>'
      '<tr><td>Cube</td><td>6</td><td>12</td><td>8</td></tr>'
      '<tr><td>Cuboid</td><td>6</td><td>12</td><td>8</td></tr>'
      '<tr><td>Cone</td><td>2</td><td>1</td><td>1</td></tr>'
      '<tr><td>Cylinder</td><td>3</td><td>2</td><td>0</td></tr>'
      '<tr><td>Sphere</td><td>1</td><td>0</td><td>0</td></tr></table>')
    A(kiwi("Let's make sense of the curvy ones. A <b>cone</b> has a flat circle on the bottom plus one "
           "curved surface = 2 faces; they meet at one circular <b>edge</b>, and the pointy tip is its "
           "single <b>vertex</b>. A <b>cylinder</b> has two flat circles (top and bottom) plus the "
           "curved tube = 3 faces, two circular edges, and <em>no</em> vertices — it has no points! "
           "A <b>sphere</b> is one smooth curved surface: 1 face, 0 edges, 0 vertices."))
    A(P("<b>A note on counting curved surfaces:</b> in this book a curved surface counts as a face "
        "(so a cylinder has 3 faces and a sphere has 1). Your school may instead call a curved "
        "surface a “curved surface” and count only the flat ones as faces — so these counts can "
        "differ. Either way of saying it is fine; just match whichever your teacher uses."))
    A(tryit("Which solid has <b>no vertices and no edges</b> at all — just one smooth curved surface?",
            "A <b>sphere</b> (like a ball). It is perfectly round, with no corners and no edges."))
    A(tryit("How many <b>edges</b> does a cylinder have, and where are they?",
            "A cylinder has <b>2 edges</b> — the two circles, one around the top and one around "
            "the bottom, where the flat faces meet the curved surface."))

    A(H("Nets — flat shapes that fold into solids"))
    A(P("Here is the magic from our Big Question. If you carefully <b>unfold</b> a cardboard box and lay "
        "it flat, you get a special flat pattern called a <b>net</b>. Fold the net back up and you get the "
        "solid again! A net for a <b>cube</b> is made of <b>6 squares</b> (one for each face). This "
        "cross-shaped net folds into a cube:"))
    A(figure(cube_net(), "A net of 6 squares that folds up into a cube"))
    A(example("does this net fold into a cube?", steps([
        "Count the squares: a cube has 6 faces, so its net must have exactly <b>6</b> squares.",
        "This net has 6 squares — good so far. ✓",
        "Imagine folding the four arms up around the middle square, then the top square folds over to "
        "close the box. It works — this net makes a cube!",
    ]) + P("<b>Watch out!</b> Not every arrangement of 6 squares folds into a cube. If two squares would "
           "have to land on the <em>same</em> face when you fold, the net won't close up properly.")))
    A(kiwi("Try it for real! Trace this net onto card, cut it out, and fold along the lines. Seeing a flat "
           "shape become a solid box with your own hands is one of the most satisfying things in maths. "
           "A net for a <b>cuboid</b> uses 6 rectangles, and a net for a <b>cylinder</b> is two circles "
           "plus one rectangle (the rectangle rolls into the tube)."))
    A(tryit("A net is made of <b>2 circles and 1 rectangle</b>. Which solid does it fold into?",
            "A <b>cylinder</b> — the two circles become the top and bottom, and the rectangle rolls "
            "around to make the curved tube (like the label on a tin can)."))

    A(H("Solids all around us"))
    A(P("Once you know these shapes, you'll see them everywhere. Matching real objects to solids is a "
        "great way to remember them:"))
    A('<table class="pv"><tr><th>Everyday object</th><th>Solid shape</th></tr>'
      '<tr><td>Dice, sugar cube</td><td>Cube</td></tr>'
      '<tr><td>Cereal box, brick</td><td>Cuboid</td></tr>'
      '<tr><td>Ice-cream cone, party hat</td><td>Cone</td></tr>'
      '<tr><td>Tin can, drum, candle</td><td>Cylinder</td></tr>'
      '<tr><td>Football, globe, orange</td><td>Sphere</td></tr></table>')

    A(H("Now you try — climb the ladder"))
    A(P("Move up one rung at a time. Picture each shape in your head before you check!"))

    A(practice("Remember", [
        ("How many sides and corners does a <b>triangle</b> have?",
         "3 sides and 3 corners."),
        ("What do we call the flat surfaces of a solid?",
         "Faces."),
        ("How many faces, edges and vertices does a <b>cube</b> have?",
         "6 faces, 12 edges, 8 vertices."),
        ("What is a <b>net</b>?",
         "A flat pattern that folds up to make a solid (3D) shape."),
        ("What is a <b>2D</b> shape? What is a <b>3D</b> shape?",
         "A 2D shape is flat (like a drawing); a 3D shape is solid (you can hold it)."),
    ]))
    A(practice("Understand", [
        ("How many corners does a <b>pentagon</b> have?",
         "5 corners (a pentagon has 5 sides and 5 corners)."),
        ("How many vertices does a <b>cuboid</b> have?",
         "8 vertices."),
        ("How many flat faces does a <b>cone</b> have, and what shape is the flat one?",
         "1 flat face, which is a circle (plus 1 curved face)."),
        ("Which solid is shaped like a tin can?",
         "A cylinder."),
        ("How many squares are in the net of a cube?",
         "6 squares (one for each face)."),
    ]))
    A(practice("Apply", [
        ("A shape has <b>8</b> straight sides. What is it called?",
         "An octagon (8 sides, 8 corners)."),
        ("Name the solid: it has 2 circular flat faces and 1 curved face. ",
         "A cylinder."),
        ("Sort these as 2D or 3D: square, cube, circle, sphere, triangle, cone.",
         "2D: square, circle, triangle. 3D: cube, sphere, cone."),
        ("A party hat is shaped like which solid? How many vertices does it have?",
         "A cone; it has 1 vertex (the pointy tip)."),
        ("A net is 6 rectangles. Which solid does it fold into?",
         "A cuboid (a box)."),
    ]))
    A(practice("Analyze", [
        ("Which has <b>more edges</b>, a cube or a cone? By how many?",
         "A cube has 12 edges and a cone has 1 edge, so the cube has 11 more."),
        ("Riya says a sphere has 1 vertex. Is she right? Explain.",
         "No — a sphere has 0 vertices (and 0 edges). It is perfectly smooth with no corners at all."),
        ("Add together the number of faces of a cube and a cylinder.",
         "Cube has 6 faces, cylinder has 3 faces, so 6 + 3 = 9 faces."),
        ("A solid has 6 faces, 12 edges and 8 vertices, but its faces are rectangles, not squares. "
         "What is it?",
         "A cuboid (a box). Same counts as a cube, but with rectangular faces."),
        ("Which 3D shapes have <b>no vertices</b>? Name them and say why.",
         "A cylinder (0 vertices) and a sphere (0 vertices) — they have curved surfaces with no "
         "corner points."),
    ]))
    A(practice("Create", [
        ("List <b>three</b> objects in your home for each solid: cube, cylinder and sphere.",
         "Examples — Cube: dice, Rubik's cube, sugar cube. Cylinder: tin can, candle, drinking glass. "
         "Sphere: ball, orange, marble. (Any sensible objects count.)"),
        ("Sketch a net that you think folds into a cube, then check it has 6 squares.",
         "Any 6-square net that closes into a box works, e.g. the cross shape: a row of 4 squares with "
         "1 square above and 1 below the second square. Count: 4 + 1 + 1 = 6 squares. ✓"),
        ("Invent a riddle for a classmate: describe a solid by its faces, edges and vertices without "
         "naming it.",
         "Example riddle: \"I have 6 square faces, 12 edges and 8 vertices. What am I?\" Answer: a cube. "
         "(Any correct set of counts works.)"),
    ]))

    A(challenge(
        P("Kiwi is building shapes out of straws (for edges) and clay balls (for vertices). "
          "Kiwi wants to build <b>one cube</b> and <b>one cuboid</b>. "
          "How many straws and how many clay balls are needed <em>in total</em>?") +
        tryit("Work out the edges and vertices of each solid, then add.",
              "A cube has 12 edges and 8 vertices; a cuboid also has 12 edges and 8 vertices. "
              "Total straws (edges) = 12 + 12 = <b>24</b>. Total clay balls (vertices) = 8 + 8 = "
              "<b>16</b>. So Kiwi needs <b>24 straws and 16 clay balls</b>.")))

    A(kiwi("Good work counting faces, edges and vertices carefully. You now know 2D shapes by their sides and corners, 3D solids by their faces, edges "
           "and vertices, and the clever idea of nets that fold flat shapes into solids. In our last "
           "geometry chapter we'll discover <b>symmetry</b> — the secret balance hidden in butterflies, "
           "letters and shapes. Turn the page to Chapter 14! 🦋"))

    chapter("Part 4 · Measure Masters & Turn & Flip", 13, "2D & 3D Shapes & Nets",
            "Geometry · Shapes & Solids", "".join(b))
