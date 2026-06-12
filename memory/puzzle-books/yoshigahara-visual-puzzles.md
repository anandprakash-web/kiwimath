# Puzzles of Nobuyuki Yoshigahara: Visual/Spatial Puzzle Patterns

## Book Stats
- ~200 puzzles across 10 chapters
- ~160 figures (very heavily illustrated)
- Chapters 1-3 tested with children ages 8-13
- Perfect for mobile touch interface

---

## Chapter-by-Chapter Visual Summary

### Ch1: Introductory (10 puzzles)
Pure logic/verbal — bookmark paradox, cats-mice, liars, seating, deduction. Low visual.

### Ch2: Matchstick Puzzles (10 puzzles) — ALL VISUAL
- Hourglass flip, chair flip, horse direction change, grid squares, triangle area
- Every puzzle has figures. Perfect for drag-to-move touch interaction.

### Ch3: Maze Puzzles (15 puzzles) — VERY HIGH VISUAL
- Art museum heist, library navigation, trade fair, hexagonal garden, castle paths, catacomb routing
- Rich narrative framing (heist stories, exploration adventures)
- Perfect for trace-path touch interaction

### Ch4: Algorithmic (15 puzzles) — MIXED
- Tower escape (pulley), bridge crossing, wine jugs, rail yard shunting, zoo cage swaps, peg solitaire
- Sequential step-by-step solutions

### Ch5: Combinatorial (20 puzzles) — MEDIUM VISUAL
- Langford pairing, graph coloring, necklace labeling, pentomino coloring, string puzzles
- Pattern-matching and arrangement

### Ch6: Digital (25 puzzles) — MEDIUM VISUAL
- Cubes/powers, age reversal, calculator displays, equation box templates
- Number-based with visual templates

### Ch7: Number (25 puzzles) — HIGH VISUAL
- Magic graph sums, cube vertex placement, number chains, triangle arrays, grid partitioning
- Place-numbers-in-circles format (perfect for drag-and-drop)

### Ch8: Geometric (25 puzzles) — VERY HIGH VISUAL
- Paper folding, Steiner trees, triangle comparisons, circle packing, cube nets, coin stacking, die tipping
- Spatial reasoning, transformation

### Ch9: Dissection (30 puzzles) — VERY HIGH VISUAL, LARGEST CHAPTER
- Tetromino/triomino/pentomino dissections, shape transformations, rectangle packing, jigsaw assembly
- Perfect for drag-and-drop piece placement

### Ch10: Other (30 puzzles) — MIXED
- PULL/PUSH door dots, LOVE cards, ambigrams, matchstick equations, balanced mobiles, word puzzles
- Creative/lateral thinking

---

## Mobile Touch Interaction Patterns

| Interaction | Puzzle Types | Example |
|-------------|-------------|---------|
| **Drag matchsticks** | Ch2 matchstick | Move 2 matches to flip hourglass |
| **Trace paths** | Ch3 mazes | Finger-trace through art museum |
| **Drag-and-drop pieces** | Ch9 dissection | Fit tetrominos into rectangle |
| **Drag numbers to circles** | Ch7 number placement | Place 1-8 on cube vertices |
| **Tap to place digits** | Ch6 digital | Fill in equation template |
| **Swipe to tip die** | Ch8 geometric | Roll die across grid |
| **Tap to flip/rotate** | Ch8 geometric | Fold paper along dotted lines |

---

## Top 50 K-6 Mobile App Puzzles

### Section 1: Matchstick Magic (8 puzzles from Ch2)
All 10 Ch2 puzzles adaptable. Drag-and-drop matchstick interface.

### Section 2: Maze Adventures (5 puzzles from Ch3)
Art museum heist, library navigation, hexagonal garden, castle paths, catacomb routing.

### Section 3: Shape Shifters (9 puzzles from Ch9)
Tetromino dissections, shape-to-shape transformations, jigsaw assembly.

### Section 4: Number Circles (8 puzzles from Ch7)
Place numbers in circles so edges/rows sum to target. Magic graphs.

### Section 5: Coin & Object Puzzles (5 puzzles from Ch8)
Coin stacking, die tipping across grid, circle packing.

### Section 6: Digit Detective (7 puzzles from Ch6)
Calculator displays, equation templates, age reversal.

### Section 7: Bridge & Balance (8 puzzles from Ch4+Ch10)
Bridge crossing, balanced mobiles, pulley systems.

---

## SVG Element Types Needed

| Puzzle Type | SVG Elements |
|-------------|-------------|
| Matchstick | `<line>` with rounded `<circle>` heads |
| Maze | `<path>` walls, `<rect>` rooms, `<circle>` nodes |
| Dissection | `<polygon>` pieces with `<pattern>` fills |
| Number circle | `<circle>` nodes, `<line>` edges, `<text>` labels |
| Grid | `<rect>` cells, `<text>` numbers |
| Die | `<rect>` with rounded corners, `<circle>` dots |
| Coin | `<circle>` with metallic gradient |
