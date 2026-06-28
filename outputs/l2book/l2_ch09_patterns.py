#!/usr/bin/env python3
"""Chapter 9 — Patterns, Analogies & Classification  (Algebra · Rule Finders)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, pattern_seq, number_line, array_dots,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Look at these numbers: 2, 4, 6, 8, &hellip; What comes next? You probably said <b>10</b> in a flash. "
            "But <em>how</em> did you know? You found a hidden <b>rule</b> &mdash; and rule-finding is one of the "
            "most powerful tricks in all of mathematics."))
    A(kiwi("Hi again, it's <b>Kiwi</b>! A <b>pattern</b> is anything that repeats or grows in a regular way. "
           "If you can spot the rule, you can predict what comes next &mdash; and even jump far ahead without "
           "drawing every step. Detectives find clues; mathematicians find patterns. Let's become "
           "<em>pattern detectives</em>!"))

    # -- 1. Repeating patterns --
    A(H("Repeating patterns: the part that says itself again"))
    A(P("The simplest pattern just repeats a little chunk over and over. That chunk is called the "
        "<b>core</b>. Here the core is <b>orange&ndash;blue</b>, and it keeps repeating:"))
    A(figure(pattern_seq([("O", ORANGE), ("B", SKY), ("O", ORANGE), ("B", SKY), ("O", ORANGE)]),
             "An orange-blue (O, B) bead pattern. Core = O, B. What fills the ? box?"))
    A(P("To find the missing one, just keep the core going. After orange always comes blue, so the "
        "<b>?</b> is <b>blue</b>. Finding the core is the whole secret of a repeating pattern."))
    A(tryit("A bead string goes red-green-green, red-green-green, red-green-green, &hellip; What are the next <b>two</b> beads?",
            "The core is <b>red, green, green</b>. We stopped right after a full core, so the next two "
            "begin a new core: <b>red then green</b>."))

    A(kiwi("Trick for repeating patterns: <b>find where the core starts over</b>, then count along. "
           "You never have to draw the whole thing &mdash; just the core, again and again."))

    # -- 2. Growing number patterns --
    A(H("Growing patterns: count the jump"))
    A(P("Many patterns don't repeat &mdash; they <b>grow</b>. The rule is the size of the jump from one "
        "term to the next. Watch the jumps in <b>3, 6, 9, 12, &hellip;</b>"))
    A(figure(number_line(0, 15, 3, points=[(3, "3", ORANGE), (6, "6", ORANGE), (9, "9", ORANGE),
                                            (12, "12", ORANGE)]),
             "Each hop is +3. The next hop lands on 15."))
    A(P("Every step adds <b>3</b>, so the rule is <em>'+3 each time.'</em> After 12 comes 12 + 3 = "
        "<b>15</b>. These are the same as counting in 3s, or the 3 times-table!"))
    A(example("find the rule, then the next two terms of 5, 9, 13, 17, &hellip;", steps([
        "Find the jump: 9 &minus; 5 = 4, and 13 &minus; 9 = 4. The rule is <b>+4 each time</b>.",
        "Next term: 17 + 4 = <b>21</b>.",
        "And the one after: 21 + 4 = <b>25</b>.",
        "So the sequence continues 5, 9, 13, 17, <b>21, 25</b>.",
    ])))
    A(tryit("What is the rule for <b>40, 35, 30, 25, &hellip;</b> and what comes next?",
            "Each step <b>subtracts 5</b> (40 &minus; 35 = 5). Next: 25 &minus; 5 = <b>20</b>."))

    # -- 3. Patterns that change their jump --
    A(H("Detective level up: when the jump itself changes"))
    A(P("Some sneaky patterns change the jump each time. Look hard at <b>1, 2, 4, 7, 11, &hellip;</b>"))
    A(figure(number_line(0, 16, 1, points=[(1, "1", BERRY), (2, "2", BERRY), (4, "4", BERRY),
                                           (7, "7", BERRY), (11, "11", BERRY)]),
             "Jumps grow: +1, +2, +3, +4, &hellip; so the next jump is +5."))
    A(example("continue 1, 2, 4, 7, 11, &hellip;", steps([
        "Find each jump: 2 &minus; 1 = 1, 4 &minus; 2 = 2, 7 &minus; 4 = 3, 11 &minus; 7 = 4.",
        "The jumps are 1, 2, 3, 4 &mdash; they go up by one each time! Next jump = <b>5</b>.",
        "So the next term is 11 + 5 = <b>16</b>.",
    ]) + P("<b>Watch out!</b> If the jumps aren't equal, don't give up &mdash; check whether the "
           "<em>jumps</em> follow a pattern of their own.")))

    # -- 4. Shape & growing-shape patterns --
    A(H("Shape patterns and growing shapes"))
    A(P("Patterns aren't only numbers &mdash; shapes follow rules too. This one repeats a "
        "<b>triangle&ndash;square&ndash;circle</b> core:"))
    A(figure(pattern_seq([("T", GRASS), ("S", PURPLE), ("C", SKY), ("T", GRASS), ("S", PURPLE)]),
             "Shapes: T=triangle, S=square, C=circle. Core = T, S, C. What is the ?"))
    A(P("After triangle then square, the core says the next shape is <b>circle</b>."))
    A(P("Now a <b>growing</b> shape pattern. Count the dots in each picture below &mdash; it's a "
        "square of dots getting bigger: 1, then 4, then 9 dots. These are the <b>square numbers</b>!"))
    A(figure(array_dots(1, 1, GOLD), "Step 1: 1 dot (1 x 1)"))
    A(figure(array_dots(2, 2, GOLD), "Step 2: 4 dots (2 x 2)"))
    A(figure(array_dots(3, 3, GOLD), "Step 3: 9 dots (3 x 3)"))
    A(example("how many dots in step 4 and step 5?", steps([
        "The dots make a square: step n has n rows and n columns, so n x n dots.",
        "Step 4 = 4 x 4 = <b>16</b> dots.",
        "Step 5 = 5 x 5 = <b>25</b> dots.",
        "Spotting the rule (<b>n x n</b>) let us jump ahead without drawing all the dots!",
    ])))
    A(tryit("A pattern of dots grows 2, 4, 6, 8, &hellip; (each step adds one more row of 2). How many "
            "dots in step 6?",
            "The rule is +2 each step, so step 6 = 2 x 6 = <b>12</b> dots."))

    # -- 5. Analogies --
    A(H("Analogies: 'A is to B as C is to ?'"))
    A(P("An <b>analogy</b> is a matching puzzle. You're shown how the first pair is connected, then "
        "you make a second pair connect the <em>same way</em>. We read it like this:"))
    A(P("&nbsp;&nbsp;&nbsp;<b>2 is to 4 &nbsp;as&nbsp; 3 is to ?</b>"))
    A(P("First find the rule that turns 2 into 4. Here, 2 was <b>doubled</b> (2 x 2 = 4). Apply the "
        "<em>same</em> rule to 3: 3 x 2 = <b>6</b>. So the answer is <b>6</b>."))
    A(example("solve  5 is to 8  as  9 is to ?", steps([
        "How do we get from 5 to 8? We <b>add 3</b> (5 + 3 = 8).",
        "Use the same rule on 9: 9 + 3 = <b>12</b>.",
        "So 5 is to 8 as 9 is to <b>12</b>.",
    ])))
    A(kiwi("In an analogy the rule is <em>shared</em> by both pairs. Find the rule on the pair you "
           "fully know, then copy it onto the other pair. Analogies can use words too: "
           "<b>hand is to glove as foot is to ?</b> &rarr; <b>sock</b> (the thing you wear on it)."))
    A(tryit("Finish the analogy:  <b>10 is to 5  as  16 is to ?</b>",
            "From 10 to 5 we <b>halve</b> it (10 &divide; 2 = 5). So 16 &divide; 2 = <b>8</b>."))

    # -- 6. Odd one out / classification --
    A(H("Odd one out: sorting by a rule"))
    A(P("<b>Classification</b> means sorting things into groups by a shared property &mdash; and spotting the "
        "one that doesn't belong. Look at this set: <b>4, 6, 9, 10</b>. Three of them share something. "
        "Which is the odd one out?"))
    A(example("find the odd one out in 4, 6, 9, 10", steps([
        "Test a property: are they even? 4 even, 6 even, 9 odd, 10 even.",
        "Three numbers are <b>even</b> and only one is odd.",
        "So <b>9</b> is the odd one out &mdash; it's the only odd number.",
    ]) + P("There can be more than one good reason &mdash; what matters is finding a rule that fits "
           "<em>all but one</em>.")))
    A(tryit("Which is the odd one out:  <b>triangle, square, circle, rectangle</b>?",
            "A <b>circle</b> &mdash; it's the only shape with <em>no straight sides and no corners</em>. "
            "The other three are made of straight sides."))

    # -- 7. Secret codes (letter / number coding) --
    A(H("Secret codes: patterns hiding in the alphabet"))
    A(P("Code puzzles use a pattern too. The trick is to remember the <b>alphabet in order</b> and "
        "find how each letter moved. Suppose <b>CAT</b> is written as <b>DBU</b>. What's the rule?"))
    A(example("crack the code: CAT &rarr; DBU, then code the word DOG", steps([
        "Compare letters: C &rarr; D is <b>+1 step</b> (D is the next letter after C).",
        "Check the rest: A &rarr; B is +1, and T &rarr; U is +1. The rule is <b>move each letter forward 1</b>.",
        "Now code DOG: D &rarr; E, O &rarr; P, G &rarr; H. So DOG becomes <b>EPH</b>.",
    ])))
    A(kiwi("For letter codes, lay the alphabet out: A B C D E F G H &hellip; and count the steps. "
           "Forward steps add; backward steps subtract. The <em>same</em> step is used on every letter."))
    A(P("Numbers can be codes too. If A=1, B=2, C=3, &hellip; then each letter is just its position. "
        "<b>BED</b> would be 2-5-4. Spotting the rule (position number) unlocks the whole message."))
    A(tryit("Using A=1, B=2, C=3, &hellip;, what number code spells <b>CAB</b>?",
            "C is the 3rd letter, A is 1st, B is 2nd &rarr; <b>3-1-2</b>."))

    # -- Practice ladder --
    A(H("Now you try - climb the ladder"))
    A(P("Each level is a little harder. Find the rule first, then answer. Peek only after you try!"))

    A(practice("Remember", [
        ("What comes next: 5, 10, 15, 20, ___ ?", "+5 each time &rarr; 25."),
        ("Name the core of the pattern triangle-blue, triangle-blue, triangle-blue, &hellip;", "The core is triangle, blue."),
        ("What is the rule for 2, 4, 6, 8, &hellip; ?", "Add 2 each time (count in 2s)."),
        ("Complete:  7 is to 8  as  9 is to ___ . (rule: add 1)", "9 + 1 = 10."),
    ]))
    A(practice("Understand", [
        ("Find the rule and next term of 100, 90, 80, 70, &hellip; .", "Subtract 10 each time &rarr; 60."),
        ("In the pattern yellow-yellow-green, yellow-yellow-green, &hellip;, what is the 7th shape?",
         "Core (yellow, yellow, green) is 3 long. 7 = 3 + 3 + 1, so the 7th is the 1st of a new core &rarr; yellow."),
        ("Solve the analogy:  3 is to 9  as  4 is to ___ .",
         "From 3 to 9 we multiply by 3 (3 x 3 = 9). So 4 x 3 = 12."),
        ("Which is the odd one out: 11, 13, 15, 16, 17? Why?",
         "16 &mdash; it's the only even number; the rest are odd."),
    ]))
    A(practice("Apply", [
        ("Continue the growing pattern 1, 3, 6, 10, &hellip; (jumps +2, +3, +4, &hellip;). Give the next two terms.",
         "Next jump +5 &rarr; 10 + 5 = 15; then +6 &rarr; 15 + 6 = 21. Next two: 15, 21."),
        ("A bead string repeats red, blue, blue. What colour is the 10th bead?",
         "Core length 3. 10 = 3 + 3 + 3 + 1, so the 10th is the 1st of a core &rarr; red."),
        ("Crack the code: if DOG is written as EPH (each letter +1), what is the code for CAT?",
         "C&rarr;D, A&rarr;B, T&rarr;U &rarr; DBU."),
        ("Solve:  20 is to 10  as  30 is to ___ . (find the rule)",
         "From 20 to 10 we halve (&divide;2). So 30 &divide; 2 = 15."),
    ]))
    A(practice("Analyze", [
        ("Here are four sequences. Which one does NOT have a constant jump? "
         "A) 2,5,8,11  B) 4,8,12,16  C) 1,2,4,8  D) 10,20,30,40.",
         "C) 1,2,4,8 &mdash; its jumps are +1,+2,+4 (doubling, not constant). The others add 3, 4, 10."),
        ("Sort these into EVEN and ODD, then say which group is bigger: 3, 8, 5, 12, 7, 10.",
         "Even: 8, 12, 10 (three). Odd: 3, 5, 7 (three). The groups are the same size."),
        ("Two friends solve  6 is to 36  as  5 is to ? . One says 35, one says 25. "
         "Who is right and why?",
         "The rule 'square it' fits: 6 x 6 = 36, so 5 x 5 = <b>25</b>. The friend who said 25 is right; "
         "35 (just adding 30) doesn't match the squaring rule."),
        ("A pattern goes 2, 6, 18, 54, &hellip; . Is the rule 'add the same number' or 'multiply by the "
         "same number'? Find it.",
         "Multiply by 3 each time (2 x 3 = 6, 6 x 3 = 18, 18 x 3 = 54). It is not a constant add &mdash; "
         "the jumps 4, 12, 36 keep changing, but x3 stays the same."),
    ]))
    A(practice("Create", [
        ("Invent a growing number pattern whose rule is '+7 each time,' and write its first 4 terms.",
         "Any start works, e.g. 1, 8, 15, 22 (each adds 7)."),
        ("Make your own repeating pattern with a core that is 4 items long, then write it out for "
         "8 items.",
         "E.g. core triangle-square-circle-star, written twice (the core repeats exactly twice)."),
        ("Design a secret code (e.g. move each letter +2) and write your name in it.",
         "E.g. with +2: KIWI &rarr; MKYK (K&rarr;M, I&rarr;K, W&rarr;Y, I&rarr;K). Any consistent shift is correct."),
        ("Build an analogy of your own of the form 'A is to B as C is to ?' where the rule is "
         "'multiply by 4'. Give the full puzzle and its answer.",
         "E.g. 2 is to 8 as 5 is to ___ ; rule x4, so the answer is 20 (5 x 4). Any matching pair works."),
    ]))

    A(challenge(
        P("Pattern detective, your final case! A magic number machine takes a number, follows a hidden "
          "rule, and prints a new one. You feed it numbers and watch:") +
        P("&nbsp;&nbsp;3 &rarr; 7 &nbsp;&nbsp;|&nbsp;&nbsp; 5 &rarr; 11 &nbsp;&nbsp;|&nbsp;&nbsp; 10 &rarr; 21") +
        tryit("What is the machine's rule, and what will it print for <b>8</b>?",
              "Test a rule: 3 &rarr; 7 could be (x2)+1 since 3 x 2 + 1 = 7. Check: 5 x 2 + 1 = 11, "
              "10 x 2 + 1 = 21. The rule is <b>double it, then add 1</b>. "
              "For 8: 8 x 2 + 1 = <b>17</b>.")))

    A(kiwi("Nice spotting — you found the rule first and then used it, which is the whole game. You can now find rules in repeating patterns, growing patterns, "
           "analogies, odd-ones-out, and even secret codes. Finding the rule is the doorway to "
           "<b>algebra</b> &mdash; where we use a letter to stand for the mystery number. That's exactly "
           "where we go next."))

    chapter("Part 3 · Rule Finders & Balance the Scale", 9, "Patterns, Analogies & Classification",
            "Algebra · Rule Finders", "".join(b))
