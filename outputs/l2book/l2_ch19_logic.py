#!/usr/bin/env python3
"""Chapter 19 — Logic: Relations, Codes, Clocks & Folding  (Logic & Puzzles · Brain Benders)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, svg, clock, INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# -- little custom figures just for this chapter --------------------------
def family_tree():
    """A simple, friendly 3-generation family tree."""
    def box(x, y, name, col, w=92):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="9" '
                f'fill="{col}1f" stroke="{col}" stroke-width="2"/>'
                f'<text x="{x+w/2}" y="{y+22}" text-anchor="middle" font-size="14" '
                f'font-weight="700" fill="{col}">{name}</text>')
    L = INK
    s = []
    s.append(box(70, 14, "Grandpa", SKY))
    s.append(box(190, 14, "Grandma", BERRY))
    s.append(f'<line x1="162" y1="31" x2="190" y2="31" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="176" y1="31" x2="176" y2="64" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="100" y1="64" x2="300" y2="64" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="100" y1="64" x2="100" y2="78" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="300" y1="64" x2="300" y2="78" stroke="{L}" stroke-width="2"/>')
    s.append(box(54, 78, "Dad", GRASS))
    s.append(box(168, 78, "Mom", ORANGE))
    s.append(box(266, 78, "Aunt", PURPLE, 86))
    s.append(f'<line x1="146" y1="95" x2="168" y2="95" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="157" y1="95" x2="157" y2="128" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="95" y1="128" x2="219" y2="128" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="95" y1="128" x2="95" y2="142" stroke="{L}" stroke-width="2"/>')
    s.append(f'<line x1="219" y1="128" x2="219" y2="142" stroke="{L}" stroke-width="2"/>')
    s.append(box(48, 142, "Me", BERRY))
    s.append(box(172, 142, "Brother", SKY, 96))
    return svg("".join(s), 380, 190)


def code_strip(plain, coded, shift_lbl="+1"):
    """Show PLAIN letters above CODED letters with little arrows = a shift code."""
    s = []
    n = max(len(plain), len(coded))
    x0 = 200 - n * 33
    for i in range(n):
        x = x0 + i * 66
        p = plain[i] if i < len(plain) else ""
        c = coded[i] if i < len(coded) else ""
        s.append(f'<rect x="{x}" y="12" width="42" height="40" rx="8" fill="{SKY}1f" stroke="{SKY}" stroke-width="2"/>')
        s.append(f'<text x="{x+21}" y="40" text-anchor="middle" font-size="22" font-weight="800" fill="{SKY}">{p}</text>')
        s.append(f'<line x1="{x+21}" y1="56" x2="{x+21}" y2="74" stroke="{ORANGE}" stroke-width="2.4"/>')
        s.append(f'<polygon points="{x+21},78 {x+16},70 {x+26},70" fill="{ORANGE}"/>')
        s.append(f'<rect x="{x}" y="82" width="42" height="40" rx="8" fill="{GRASS}1f" stroke="{GRASS}" stroke-width="2"/>')
        s.append(f'<text x="{x+21}" y="110" text-anchor="middle" font-size="22" font-weight="800" fill="{GRASS}">{c}</text>')
    s.append(f'<text x="{x0+n*66+4}" y="68" text-anchor="start" font-size="15" font-weight="800" fill="{ORANGE}">move each {shift_lbl}</text>')
    return svg("".join(s), max(x0 * 2 + n * 66, 360), 132)


def fold_punch():
    """A square folded in half, one hole punched, then unfolded showing TWO holes."""
    s = []
    s.append(f'<rect x="20" y="30" width="70" height="100" fill="{GOLD}14" stroke="{INK}" stroke-width="2"/>')
    s.append(f'<line x1="90" y1="26" x2="90" y2="134" stroke="{ORANGE}" stroke-width="2.5" stroke-dasharray="6 4"/>')
    s.append(f'<circle cx="50" cy="70" r="9" fill="{BERRY}"/>')
    s.append(f'<text x="55" y="150" text-anchor="middle" font-size="12" fill="{INK}">folded &#183; 1 punch</text>')
    s.append(f'<text x="90" y="20" text-anchor="middle" font-size="11" fill="{ORANGE}">fold</text>')
    s.append(f'<text x="150" y="85" text-anchor="middle" font-size="26" fill="{INK}">&#8594;</text>')
    s.append(f'<rect x="195" y="30" width="140" height="100" fill="{GOLD}14" stroke="{INK}" stroke-width="2"/>')
    s.append(f'<line x1="265" y1="26" x2="265" y2="134" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="4 4"/>')
    s.append(f'<circle cx="225" cy="70" r="9" fill="{BERRY}"/>')
    s.append(f'<circle cx="305" cy="70" r="9" fill="{BERRY}"/>')
    s.append(f'<text x="265" y="150" text-anchor="middle" font-size="12" fill="{INK}">unfolded &#183; 2 holes</text>')
    return svg("".join(s), 360, 160)


def build(chapter):
    b = []
    A = b.append

    A(big_q("A detective doesn't need magic &mdash; just careful <b>thinking</b>. "
            "Can you read a secret code, untangle a family, tell the time on a clock, "
            "and picture a folded paper before it's even opened? Let's train your brain like a super-sleuth!"))
    A(kiwi("Hi again, it's <b>Kiwi</b>! This is my favourite chapter. There are no scary formulas here &mdash; "
           "just puzzles you crack with logic. The trick is always the same: <em>go slowly, one clue at a time, "
           "and write down what you know.</em> Ready, detective? &#128269;"))

    # ===================== A . BLOOD RELATIONS =====================
    A(H("Part A . Family puzzles (who is who?)"))
    A(P("A <b>family relationship</b> puzzle gives you a sentence about people and asks how two of them "
        "are related. The best tool is a little <b>family tree</b> &mdash; a picture that shows who is whose "
        "parent, child, brother or sister. Here is one for Kiwi's family:"))
    A(figure(family_tree(), "A family tree. A line down means parent of; a line across between two boxes means married to."))
    A(P("From the tree you can read off lots of relationships:"))
    A(P("&bull; <b>Mom</b> and <b>Dad</b> are my <b>parents</b>.<br>"
        "&bull; <b>Brother</b> and I are <b>siblings</b> (we share the same parents).<br>"
        "&bull; <b>Grandpa</b> and <b>Grandma</b> are my <b>grandparents</b> &mdash; they are my parents' parents.<br>"
        "&bull; <b>Aunt</b> is Dad's sister, so she is my <b>aunt</b>; if she had a child, that child would be my <b>cousin</b>.<br>"
        "&bull; My father's <b>brother</b> would be my <b>uncle</b>; my father's <b>sister</b> is my <b>aunt</b>."))
    A(kiwi("Quick word-list: your parent's <b>brother</b> = <b>uncle</b>, parent's <b>sister</b> = <b>aunt</b>, "
           "aunt/uncle's child = <b>cousin</b>, your brother's child = your <b>nephew</b> (boy) or <b>niece</b> (girl), "
           "and your parent's parent = <b>grandparent</b>."))

    A(example("The woman on the road is my father's wife. How is she related to me?", steps([
        "Read it slowly: the woman is <b>my father's wife</b>.",
        "Who is your father's wife? That's your <b>mother</b>!",
        "So the woman is my <b>mother</b>. &#10003;",
    ])))
    A(example("Mr Arun points to a girl: She is the daughter of my brother. Who is she to Arun?", steps([
        "She is <b>the daughter of Arun's brother</b>.",
        "Your brother's daughter is your <b>niece</b> (a girl) &mdash; a nephew if it were a boy.",
        "So the girl is Arun's <b>niece</b>. &#10003;",
    ])))
    A(example("A woman says about a man: His mother is the only daughter of my mother. Who is the woman to him?",
              steps([
        "Find <b>the only daughter of my mother.</b> The woman is speaking, so the only daughter of her mother is the <b>woman herself</b>.",
        "The sentence says the man's mother <em>is</em> that only daughter &mdash; so the man's mother is the <b>woman</b>.",
        "If the woman is the man's mother, then she is his <b>mother</b>. &#10003;",
    ]) + P("<b>Detective tip:</b> phrases like the only daughter of my mother often point straight back at the speaker. "
           "Replace them with the simpler word before you finish.")))

    A(tryit("Pointing to a photo, Mr Suresh says, He is the son of the <b>only son</b> of my mother. "
            "How is Suresh related to the boy?",
            "The only son of Suresh's mother is <b>Suresh himself</b>. So the boy is the son of Suresh &mdash; "
            "Suresh is the boy's <b>father</b>."))

    # ===================== B . CODING-DECODING =====================
    A(H("Part B . Secret agent codes (coding &amp; decoding)"))
    A(P("Spies hide messages with a <b>code</b>: a secret <em>rule</em> that changes each letter into another one. "
        "If you know the rule, you can <b>encode</b> (lock) or <b>decode</b> (unlock) any word. The most famous "
        "rule is a <b>letter shift</b>: slide every letter forward by the same number of steps in the alphabet."))
    A(P("Here is the rule move each letter <b>1 step forward</b> turning the word <b>CAT</b> into a code:"))
    A(figure(code_strip("CAT", "DBU", "+1"), "C to D, A to B, T to U. The codeword for CAT is DBU."))
    A(P("Watch carefully: every letter moves the <em>same</em> number of steps. C becomes D, A becomes B, "
        "T becomes U. To <b>decode</b>, just move the other way (backwards)."))
    A(example("Encode the word DOG with the rule +1 (one step forward)", steps([
        "D moves forward 1 &rarr; <b>E</b>.",
        "O moves forward 1 &rarr; <b>P</b>.",
        "G moves forward 1 &rarr; <b>H</b>.",
        "So DOG is written as the code <b>EPH</b>. &#10003;",
    ])))
    A(kiwi("What happens at the end of the alphabet? If you must move <b>Z</b> forward by 1, you loop back to the "
           "start: <b>Z &rarr; A</b>. The alphabet is like a circle! So ZOO with +1 becomes <b>APP</b>."))
    A(example("Decode the secret word EPH (the rule was +1)", steps([
        "To decode, move each letter <em>backward</em> 1 step instead.",
        "E &rarr; <b>D</b>, P &rarr; <b>O</b>, H &rarr; <b>G</b>.",
        "The hidden word is <b>DOG</b>. &#10003;",
    ])))
    A(P("Another kind of code uses <b>position numbers</b>: A = 1, B = 2, C = 3, &hellip; all the way to Z = 26. "
        "Then a word becomes a string of numbers."))
    A(example("Write CAB using position numbers (A=1, B=2, &hellip;)", steps([
        "C is the 3rd letter &rarr; <b>3</b>.",
        "A is the 1st letter &rarr; <b>1</b>.",
        "B is the 2nd letter &rarr; <b>2</b>.",
        "So CAB is coded <b>3-1-2</b>. &#10003;",
    ])))
    A(tryit("Using the rule +2 (two steps forward), what is the codeword for <b>FROG</b>?",
            "F&rarr;H, R&rarr;T, O&rarr;Q, G&rarr;I. The code is <b>HTQI</b>."))
    A(tryit("Decode the numbers <b>2-15-25</b> using A=1, B=2, &hellip; What word is it?",
            "2 = B, 15 = O, 25 = Y &rarr; the word is <b>BOY</b>."))

    # ===================== C . CLOCKS & CALENDARS =====================
    A(H("Part C . Clocks, calendars &amp; ages"))
    A(P("A clock has two main hands. The <b>short, fat hand</b> is the <b>hour hand</b>; the <b>long, thin hand</b> "
        "(shown in orange) is the <b>minute hand</b>. The minute hand sweeps all the way around &mdash; 60 minutes "
        "&mdash; while the hour hand creeps from one number to the next. This clock reads <b>3 o'clock</b>:"))
    A(figure(clock(3, 0), "Hour hand on 3, minute hand on 12 gives 3:00."))
    A(P("To read a time, check the <b>hour hand</b> first (which number has it just passed?), then count the "
        "<b>minutes</b> by the minute hand: each number it points to is <em>5 minutes</em> (1 is 5, 2 is 10, 3 is 15&hellip;). "
        "Here the minute hand is on 6, which is <b>30 minutes</b>:"))
    A(figure(clock(7, 30), "Hour hand between 7 and 8, minute hand on 6 gives 7:30 (half past seven)."))

    A(H("Elapsed time &mdash; how long did it take?"))
    A(P("<b>Elapsed time</b> means how much time passed from a start time to an end time. The safe way is to "
        "<b>count up</b>: jump to the next whole hour, then add the leftover minutes."))
    A(example("A film starts at 7:45 and lasts 2 hours 30 minutes. When does it end?", steps([
        "Start at <b>7:45</b>. Add the 2 hours first &rarr; <b>9:45</b>.",
        "Now add 30 minutes. From 9:45, 15 more minutes reaches 10:00&hellip;",
        "&hellip;and 15 minutes after that is <b>10:15</b>.",
        "The film ends at <b>10:15</b>. &#10003;",
    ])))
    A(figure(clock(10, 15), "The film ends at 10:15."))
    A(kiwi("Going backwards works the same way. If Mr Sharma <b>arrives</b> at 4:45 and the drive took 2 hours "
           "15 minutes, count <em>back</em>: 4:45 &minus; 2 hours = 2:45, then &minus; 15 minutes = <b>2:30</b>. He set off at 2:30."))

    A(H("Days of the week &amp; the calendar"))
    A(P("The 7 days repeat forever: <b>Mon, Tue, Wed, Thu, Fri, Sat, Sun,</b> then Monday again. Because there "
        "are <em>7</em> days in a week, jumping exactly <b>7 days</b> (or 14, or 21&hellip;) lands you on the <em>same</em> day!"))
    A(example("Today is Monday. What day will it be after 10 days?", steps([
        "7 of those days bring us right back to <b>Monday</b> (one full week).",
        "That leaves 10 &minus; 7 = <b>3</b> more days to count.",
        "Monday &rarr; Tue (1) &rarr; Wed (2) &rarr; <b>Thu</b> (3).",
        "So 10 days after Monday is a <b>Thursday</b>. &#10003;",
    ])))
    A(kiwi("Months have different lengths: 31 days for Jan, Mar, May, Jul, Aug, Oct, Dec; 30 days for Apr, Jun, "
           "Sep, Nov; and February has 28 (29 in a leap year). A handy rhyme: Thirty days has September, April, "
           "June and November&hellip;."))

    A(H("Age problems"))
    A(P("Ages change by the <em>same</em> amount as the years. If 6 years pass, <b>everyone</b> gets 6 years older, "
        "so the <b>difference</b> between two people's ages never changes."))
    A(example("Megha will be 53 years old in 2019. What was her age in 1998?", steps([
        "From 1998 to 2019 is 2019 &minus; 1998 = <b>21 years</b>.",
        "She was 21 years younger back then: 53 &minus; 21 = <b>32</b>.",
        "So Megha was <b>32 years old</b> in 1998. &#10003;",
    ])))
    A(tryit("A clock shows the hour hand a little past 4 and the minute hand on 4. What time is it? "
            "(Remember: the minute hand on 4 means 4 &times; 5 minutes.)",
            "The minute hand on 4 is 4 &times; 5 = 20 minutes, and the hour hand is just past 4, so it is <b>4:20</b>."))
    A(tryit("Riya's swimming class starts at 8:30 and finishes at 10:15. How long is the class?",
            "From 8:30, add 1 hour &rarr; 9:30; another 30 min &rarr; 10:00; 15 more min &rarr; 10:15. "
            "That's 1 hour + 45 minutes = <b>1 hour 45 minutes</b>."))

    # ===================== D . PAPER FOLDING & CUTTING =====================
    A(H("Part D . Paper folding &amp; cutting (see it before you open it!)"))
    A(P("Here is a puzzle that feels like magic: fold a piece of paper, punch a hole or snip a shape, then "
        "<b>imagine</b> what it looks like when you open it back up. The big idea is <b>symmetry</b>: whatever you "
        "do on one side of a <b>fold line</b> appears <em>mirrored</em> on the other side when you unfold."))
    A(figure(fold_punch(), "Fold the square in half, punch ONE hole, unfold: the hole appears on BOTH sides of the fold."))
    A(P("Why does one punch make two holes? Because folding <b>stacked the paper into 2 layers</b>, so the punch "
        "went through both at once. When you open it, each layer shows its own hole &mdash; and they sit as mirror "
        "images across the fold line."))
    A(kiwi("Counting rule: each fold <b>doubles</b> the layers. Fold once &rarr; 2 layers &rarr; 1 punch makes <b>2</b> holes. "
           "Fold twice &rarr; 4 layers &rarr; 1 punch makes <b>4</b> holes. Fold three times &rarr; 8 layers &rarr; <b>8</b> holes! "
           "(This works as long as the punch is <em>away from the fold lines</em> and the holes don't overlap &mdash; "
           "a hole punched right on a fold can land on top of its mirror and count as one.)"))
    A(example("You fold a paper in half TWICE, then punch one hole. How many holes after unfolding?", steps([
        "First fold &rarr; 2 layers.",
        "Second fold &rarr; 2 &times; 2 = <b>4 layers</b> stacked together.",
        "One punch goes through all 4 layers, so unfolding shows <b>4 holes</b>. &#10003;",
    ])))
    A(P("Cutting works by the same mirror rule. If you fold a paper in half and cut a little <b>triangle out of "
        "the fold</b>, unfolding gives a <b>full diamond</b> &mdash; the triangle and its mirror image join up. Snowflakes "
        "are made exactly this way: fold, snip, and the pattern repeats around the folds."))
    A(tryit("A strip of paper is folded in half, in half again (so it's folded twice), and one round hole is "
            "punched through. How many holes when you open it flat?",
            "Two folds make 2 &times; 2 = <b>4 layers</b>, so the single punch becomes <b>4 holes</b>."))

    # ===================== THE BLOOM LADDER =====================
    A(H("Now you try &mdash; climb the detective ladder"))
    A(P("These get trickier as you go up. Try first, then peek!"))

    A(practice("Remember", [
        ("Your parent's sister is called your ____.", "Aunt."),
        ("In the code rule +1, what does the letter A become?", "B (one step forward)."),
        ("How many minutes does the minute hand show when it points to the number 3?",
         "3 &times; 5 = 15 minutes."),
        ("How many days are there in one week?", "7 days."),
        ("Fold a paper in half once and punch 1 hole. How many holes when unfolded?", "2 holes."),
    ]))
    A(practice("Understand", [
        ("Mr Verma says, He is the son of my mother's only son. He is pointing at a boy. "
         "Who is the boy to Mr Verma?",
         "The only son of his mother is Mr Verma himself, so the boy is his <b>son</b>."),
        ("Using the rule +1, write the codeword for <b>SUN</b>.", "S&rarr;T, U&rarr;V, N&rarr;O &rarr; <b>TVO</b>."),
        ("Write the time shown when the hour hand is between 9 and 10 and the minute hand points to 6.",
         "9:30 (half past nine)."),
        ("Today is Wednesday. What day will it be after exactly 7 days?",
         "The same day &mdash; Wednesday (7 days = one full week)."),
        ("Decode the numbers <b>3-1-20</b> with A=1, B=2, &hellip; What word is it?", "3=C, 1=A, 20=T &rarr; <b>CAT</b>."),
    ]))
    A(practice("Apply", [
        ("Pointing to a girl, Reena said, She is the daughter of my mother. But Reena has no sisters. "
         "Who is the girl?",
         "If the girl is the daughter of Reena's mother and Reena has no sisters, the girl must be <b>Reena herself</b>."),
        ("A cartoon starts at 4:20 and lasts 1 hour 15 minutes. What time does it end?",
         "4:20 + 1 hour = 5:20; + 15 minutes = <b>5:35</b>."),
        ("Decode the secret word <b>NJML</b> if the rule was +1. (Move each letter back 1.)",
         "N&rarr;M, J&rarr;I, M&rarr;L, L&rarr;K &rarr; <b>MILK</b>."),
        ("Aarav is 7 years old now. How old will he be in the year that is 9 years from now?",
         "7 + 9 = <b>16 years old</b>."),
        ("A paper is folded in half three times, then one hole is punched. How many holes appear when unfolded?",
         "Three folds &rarr; 2 &times; 2 &times; 2 = 8 layers &rarr; <b>8 holes</b>."),
    ]))
    A(practice("Analyze", [
        ("A woman, pointing to a man, says, His mother is the only daughter of my mother. "
         "How is the woman related to the man?",
         "The only daughter of her mother is the woman herself, and that person is the man's mother, so the woman "
         "is the man's <b>mother</b>."),
        ("Two codes are shown: BIRD becomes CJSE, and FISH becomes GJTI. What is the secret rule, "
         "and what would CAT become?",
         "Each letter moved <b>forward 1 step</b> (B&rarr;C, I&rarr;J, R&rarr;S, D&rarr;E &#10003;). So CAT &rarr; <b>DBU</b>."),
        ("Today is Friday. Your birthday is in exactly 15 days. On which day of the week is your birthday?",
         "15 = 7 + 7 + 1, so it's 1 day after Friday &rarr; <b>Saturday</b>."),
        ("Dad is 35 and his daughter is 7. In 10 years, what will the difference between their ages be?",
         "The age difference never changes: 35 &minus; 7 = <b>28 years</b> (it's still 28 in 10 years)."),
        ("A square paper is folded in half, and a small triangle is cut <em>out of the folded edge</em> (the fold). "
         "What single shape appears in the middle when you unfold it?",
         "The triangle and its mirror join across the fold to make one <b>diamond</b> (a four-sided shape)."),
    ]))
    A(practice("Create", [
        ("Invent your own +3 secret code and use it to write the word <b>KIWI</b>. (Move each letter forward 3.)",
         "K&rarr;N, I&rarr;L, W&rarr;Z, I&rarr;L &rarr; <b>NLZL</b>."),
        ("Draw a family tree for yourself with you, your two parents, and one grandparent. Then label which person "
         "is your parent's parent.",
         "Any correct tree where the top person (your parent's parent) is the <b>grandparent</b>."),
        ("Make up an age riddle where the answer is 12. (Example answer given.)",
         "I am 8 now. How old will I be in 4 years? &rarr; 8 + 4 = <b>12</b>. Any riddle that works is great!"),
    ]))

    A(challenge(
        P("&#128373; <b>The Birthday Mystery.</b> Detective, put it all together &mdash; but watch out: "
          "<em>one clue may be wrong</em>. Trust the method that is most reliable, and explain the conflict. "
          "Today is <b>Monday</b>. Maya's birthday party is in exactly <b>9 days</b>. On the invitation she also "
          "wrote the day as a code using the rule move each letter back 1 step, and it read <b>UVFTEBZ</b>. "
          "(a) Use day-counting to find the party day. (b) Decode UVFTEBZ. (c) The two clues disagree &mdash; "
          "which do you trust, and why?") +
        tryit("Work part by part, then compare the two answers.",
              "(a) 9 days after Monday: 7 days returns to Monday, plus 2 more &rarr; Tue (1), <b>Wed</b> (2). "
              "Counting gives <b>Wednesday</b>. "
              "(b) Decode UVFTEBZ by moving each letter <em>back</em> 1: U&rarr;T, V&rarr;U, F&rarr;E, T&rarr;S, E&rarr;D, B&rarr;A, Z&rarr;Y &rarr; "
              "<b>TUESDAY</b>. "
              "(c) The two clues <b>conflict</b>: counting says Wednesday, the codeword says Tuesday. Day-counting "
              "is the <em>more reliable</em> method here &mdash; it follows a fixed rule (7 days = one week) with no "
              "room for a slip, while a handwritten codeword is easy to mistype. So Maya most likely made an error "
              "writing the code, and the trustworthy answer is <b>Wednesday</b>. (A good detective says <em>why</em> "
              "one clue wins, not just which.)")))

    A(kiwi("Good reasoning — going one clue at a time is what cracked every one of these. &#127881; You can now untangle families, crack letter codes, read clocks, count "
           "days, work out ages, and picture folded paper. These are real reasoning superpowers &mdash; the same kind "
           "olympiad champions use. In our last chapter, we'll become <b>data detectives</b> and read secrets "
           "hidden inside charts and graphs!"))

    chapter("Part 5 · Brain Benders", 19, "Logic: Relations, Codes, Clocks & Folding",
            "Logic & Puzzles · Brain Benders", "".join(b))
