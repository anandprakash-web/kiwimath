#!/usr/bin/env python3
"""Chapter 16 — Probability  (Combinatorics · Probability)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, spinner, svg,
                        INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE)


# ── local figure: the likelihood line (impossible → certain) ────────────────
def likelihood_line(marks=None):
    """A 0→1 chance line labelled Impossible / Unlikely / Even / Likely / Certain.
    marks = list of (frac0to1, label, color) dots."""
    marks = marks or []
    x0, x1, y = 40, 600, 60
    s = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{INK}" stroke-width="3"/>']
    stops = [(0.0, "Impossible", BERRY), (0.25, "Unlikely", ORANGE),
             (0.5, "Even chance", GOLD), (0.75, "Likely", SKY), (1.0, "Certain", GRASS)]
    for f, lab, col in stops:
        x = x0 + f * (x1 - x0)
        s.append(f'<line x1="{x:.0f}" y1="{y-9}" x2="{x:.0f}" y2="{y+9}" stroke="{INK}" '
                 f'stroke-width="2.5"/>')
        s.append(f'<text x="{x:.0f}" y="{y+30}" text-anchor="middle" font-size="12.5" '
                 f'font-weight="800" fill="{col}">{lab}</text>')
        frac = {0.0: "0", 0.25: "¼", 0.5: "½", 0.75: "¾", 1.0: "1"}[f]
        s.append(f'<text x="{x:.0f}" y="{y-16}" text-anchor="middle" font-size="12" '
                 f'fill="{INK}">{frac}</text>')
    for f, lab, col in marks:
        x = x0 + f * (x1 - x0)
        s.append(f'<circle cx="{x:.0f}" cy="{y}" r="9" fill="{col}"/>')
        s.append(f'<text x="{x:.0f}" y="{y-26}" text-anchor="middle" font-size="12.5" '
                 f'font-weight="800" fill="{col}">{lab}</text>')
    return svg("".join(s), 640, 96)


def die_face(n):
    """A single die face showing n pips (1..6)."""
    s = [f'<rect x="6" y="6" width="80" height="80" rx="14" fill="#fff" stroke="{INK}" '
         f'stroke-width="2.6"/>']
    P_ = {  # pip positions for each face
        1: [(46, 46)],
        2: [(26, 26), (66, 66)],
        3: [(26, 26), (46, 46), (66, 66)],
        4: [(26, 26), (66, 26), (26, 66), (66, 66)],
        5: [(26, 26), (66, 26), (46, 46), (26, 66), (66, 66)],
        6: [(26, 24), (66, 24), (26, 46), (66, 46), (26, 68), (66, 68)],
    }[n]
    for (px, py) in P_:
        s.append(f'<circle cx="{px}" cy="{py}" r="8" fill="{INK}"/>')
    return "".join(s)


def dice_row(faces):
    """A row of die faces, faces = list of ints."""
    s = []
    for i, n in enumerate(faces):
        s.append(f'<g transform="translate({i*100},0)">{die_face(n)}</g>')
    return svg("".join(s), len(faces) * 100, 96)


def marble_bag(colors):
    """colors = list of color hex; draws that many marbles in a bag outline."""
    n = len(colors)
    perrow = 5
    rows = (n + perrow - 1) // perrow
    W = 280
    Hh = 90 + rows * 38
    s = [  # bag
        f'<path d="M70,70 Q140,30 210,70 L230,{Hh-14} Q140,{Hh+6} 50,{Hh-14} Z" '
        f'fill="{GOLD}11" stroke="{GOLD}" stroke-width="2.6"/>',
        f'<rect x="96" y="40" width="88" height="22" rx="8" fill="{GOLD}22" '
        f'stroke="{GOLD}" stroke-width="2.2"/>',
    ]
    x0, y0 = 86, 92
    for i, c in enumerate(colors):
        r, col = divmod(i, perrow)
        cx = x0 + col * 30 + (r % 2) * 12
        cy = y0 + r * 38
        s.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="{c}99" stroke="{c}" '
                 f'stroke-width="2"/>')
    return svg("".join(s), W, Hh)


def build(chapter):
    b = []
    A = b.append

    A(big_q("If you toss a coin, will it land on <b>Heads</b>? You can't be <em>sure</em> — "
            "but you're not totally in the dark either. How do mathematicians measure "
            "<b>how likely</b> something is to happen?"))
    A(kiwi("It's <b>Kiwi</b> here! Maths can even handle <em>luck</em>. We can't promise what one "
           "coin toss will do, but we can say exactly <b>how likely</b> each result is. That "
           "measure is called <b>probability</b> — and it's the language of games, weather, and "
           "every “what are the chances?” you've ever asked."))

    # ── likelihood words ────────────────────────────────────────────────────
    A(H("Five chance words"))
    A(P("Before numbers, let's use words. Every event sits somewhere on a <b>chance line</b>:"))
    A(figure(likelihood_line(),
             "Impossible (0) · Unlikely · Even chance (½) · Likely · Certain (1)"))
    A(P("• <b>Impossible</b> — it can never happen (rolling a 7 on a normal die).<br>"
        "• <b>Unlikely</b> — it might, but probably won't.<br>"
        "• <b>Even chance</b> — just as likely to happen as not (a coin landing Heads).<br>"
        "• <b>Likely</b> — it will probably happen.<br>"
        "• <b>Certain</b> — it must happen (the sun rising tomorrow)."))
    A(P("The ends are fixed: <b>0</b> always means impossible and <b>1</b> always means certain, "
        "with <b>½</b> exactly in the middle for an even chance. The <b>¼</b> and <b>¾</b> marks on "
        "the line are just <em>example points</em> for “unlikely” and “likely” — these two words "
        "cover a whole stretch of the line, not one single fraction."))
    A(figure(likelihood_line([(0.0, "roll a 7", BERRY), (0.5, "coin = Heads", GOLD),
                             (1.0, "a day has a night", GRASS)]),
             "Placing three events on the chance line"))
    A(tryit("Where does “it will rain frogs at lunchtime” go on the chance line — "
            "impossible, unlikely, even, likely, or certain?",
            "<b>Impossible</b> — frogs don't fall as rain, so its chance is 0."))

    # ── equally likely + the fraction ───────────────────────────────────────
    A(H("Turning chance into a number"))
    A(P("To get a number, we count two things:"))
    A(P("&nbsp;&nbsp;&nbsp;&nbsp;<b>probability = (number of ways we WANT) ÷ (number of ways "
        "ALTOGETHER)</b>"))
    A(P("We write it as a <b>fraction</b>. It only works tidily when every result is "
        "<b>equally likely</b> — like a fair coin or a fair die, where no side is special."))
    A(example("tossing a fair coin", steps([
        "A coin has <b>2</b> equally likely results: Heads or Tails. That's the “altogether”. "
        "(In our fair-coin model we ignore the tiny chance it lands on its edge.)",
        "We want <b>Heads</b> — that's <b>1</b> of those results.",
        "Probability of Heads = 1 out of 2 = <b>½</b>.",
        "So Heads has an <b>even chance</b> — it lands right in the middle of our line. 🪙",
    ])))
    A(kiwi("A probability is always a fraction between <b>0</b> and <b>1</b>. 0 means impossible, "
           "1 means certain, and ½ means even. It can never be bigger than 1 — you can't be "
           "<em>more</em> than certain!"))

    # ── dice ────────────────────────────────────────────────────────────────
    A(H("Rolling a die"))
    A(P("A normal die has <b>6</b> faces, numbered 1 to 6, all equally likely:"))
    A(figure(dice_row([1, 2, 3, 4, 5, 6]),
             "The 6 faces of a fair die — each has the same chance"))
    A(example("the chance of rolling a 4", steps([
        "Faces altogether: <b>6</b> (the numbers 1, 2, 3, 4, 5, 6).",
        "Faces we want (a 4): just <b>1</b>.",
        "Probability = 1 out of 6 = <b>1/6</b>.",
    ])))
    A(example("the chance of rolling an EVEN number", steps([
        "Even faces are 2, 4 and 6 → that's <b>3</b> faces we want.",
        "Faces altogether: <b>6</b>.",
        "Probability = 3 out of 6 = 3/6 = <b>½</b>. An even chance — same as a coin!",
    ])))
    A(tryit("What is the probability of rolling a number <b>greater than 4</b> "
            "(that is, a 5 or a 6) on a fair die?",
            "We want 5 or 6 → 2 faces, out of 6 altogether. Probability = 2/6 = <b>1/3</b>."))

    # ── spinner ─────────────────────────────────────────────────────────────
    A(H("Spinning a spinner"))
    A(P("This spinner has <b>4 equal sectors</b>: two are <b>Red</b>, one is <b>Blue</b>, one "
        "is <b>Green</b>. Where the arrow stops is the result."))
    A(figure(spinner(["Red", "Blue", "Red", "Green"]),
             "4 equal slices: 2 Red, 1 Blue, 1 Green"))
    A(example("chance the spinner lands on Red", steps([
        "Equal slices altogether: <b>4</b>.",
        "Slices that are Red: <b>2</b>.",
        "Probability of Red = 2 out of 4 = 2/4 = <b>½</b>.",
    ])))
    A(example("chance the spinner lands on Blue", steps([
        "Slices altogether: <b>4</b>. Blue slices: just <b>1</b>.",
        "Probability of Blue = <b>1/4</b>. So Blue is <em>less</em> likely than Red.",
    ])))
    A(kiwi("Bigger share of the slices → bigger probability. Red fills half the spinner, so it's "
           "the most likely colour. Blue and Green each get a quarter."))
    A(tryit("On the same spinner, what is the probability the arrow lands on <b>Green</b>? "
            "And on a colour that is <b>NOT</b> Red?",
            "Green = 1 slice of 4 = <b>1/4</b>. Not Red means Blue or Green = 2 slices of 4 = "
            "2/4 = <b>½</b>."))

    # ── marbles ─────────────────────────────────────────────────────────────
    A(H("Marbles in a bag"))
    A(P("A bag holds <b>3 red</b> and <b>2 blue</b> marbles. You reach in without looking and "
        "pull one out. Each marble is equally likely to be grabbed."))
    A(figure(marble_bag([BERRY, BERRY, BERRY, SKY, SKY]),
             "3 red + 2 blue = 5 marbles altogether"))
    A(example("chance of pulling a red marble", steps([
        "Marbles altogether: 3 + 2 = <b>5</b>.",
        "Red marbles we want: <b>3</b>.",
        "Probability of red = <b>3/5</b>.",
    ])))
    A(example("chance of pulling a blue marble", steps([
        "Blue marbles: <b>2</b>, out of <b>5</b> altogether.",
        "Probability of blue = <b>2/5</b>.",
        "Check: red + blue chances = 3/5 + 2/5 = 5/5 = <b>1</b>. The two cover everything "
        "that can happen — that's certain! ✓",
    ])))
    A(kiwi("Lovely check: the probabilities of <em>all</em> the possible results always add up "
           "to <b>1</b>. If they don't, something has been miscounted."))

    A(tryit("A bag has <b>4 red</b>, <b>1 green</b> and <b>1 yellow</b> marble. "
            "What is the probability of pulling a <b>red</b> marble?",
            "Altogether: 4 + 1 + 1 = 6 marbles. Red = 4. Probability = 4/6 = <b>2/3</b>."))

    # ── Bloom ladder ────────────────────────────────────────────────────────
    A(H("Now you try — climb the ladder"))
    A(P("For each chance, count <b>how many you want</b> and <b>how many altogether</b>, then "
        "write the fraction. Peek only after a real try!"))

    A(practice("Remember", [
        ("What is the probability of something that is <b>certain</b>?", "1."),
        ("What is the probability of something <b>impossible</b>?", "0."),
        ("How many faces does a normal die have?", "6."),
        ("A coin landing on Heads is an example of which chance word — impossible, even, or "
         "certain?",
         "Even chance (probability ½)."),
    ]))
    A(practice("Understand", [
        ("On a fair die, what is the probability of rolling a <b>2</b>?",
         "1 face out of 6 = 1/6."),
        ("A spinner has 3 equal slices: red, yellow, blue. What is the chance of red?",
         "1 of 3 slices = 1/3."),
        ("A bag has 1 red and 1 blue marble. What is the probability of red?",
         "1 of 2 = 1/2."),
        ("On a fair die, what is the probability of rolling an <b>odd</b> number?",
         "Odd faces 1, 3, 5 → 3 of 6 = 3/6 = 1/2."),
    ]))
    A(practice("Apply", [
        ("A spinner has 4 equal slices: 3 green and 1 red. What is the probability of green? "
         "Of red?",
         "Green = 3/4. Red = 1/4."),
        ("A bag holds 2 red, 3 blue and 5 yellow marbles. What is the probability of yellow?",
         "Altogether 2 + 3 + 5 = 10. Yellow = 5. Probability = 5/10 = 1/2."),
        ("On a fair die, what is the probability of rolling a number <b>less than 3</b> "
         "(a 1 or a 2)?",
         "2 faces of 6 = 2/6 = 1/3."),
        ("A spinner is half red, a quarter blue and a quarter green. Which colour is the "
         "spinner most likely to land on, and what is its probability?",
         "Red is most likely; it covers half, so the probability is 1/2."),
    ]))
    A(practice("Analyze", [
        ("A bag has 6 red and 4 blue marbles. Aria says “there are 10 marbles, so the chance of "
         "red is 1/10.” What did she do wrong, and what is the right answer?",
         "She used 1 instead of the number of RED marbles. Red = 6 of 10 = 6/10 = 3/5."),
        ("On a fair die, what is the probability of rolling a number from <b>1 to 6</b>? "
         "Why does that answer make sense?",
         "All 6 faces work → 6/6 = 1. It's certain, because every roll is a number from 1 to 6."),
        ("A spinner lands on red with probability 1/4. If red and blue are the only colours, "
         "what is the probability of blue?",
         "All chances add to 1, so blue = 1 − 1/4 = 3/4."),
        ("Which is more likely: rolling a 6 on a fair die, or pulling a red marble from a bag of "
         "2 red and 1 blue? Explain.",
         "Die: 1/6. Marbles: 2/3. Since 2/3 is much bigger than 1/6, the red marble is more "
         "likely."),
    ]))
    A(practice("Create", [
        ("Design a spinner (say how many slices and their colours) so that the chance of blue "
         "is exactly <b>½</b>. Describe it.",
         "Many answers, e.g. 4 slices with 2 blue (2/4 = ½), or 2 slices, 1 blue (1/2), or "
         "6 slices with 3 blue (3/6 = ½)."),
        ("Fill a bag with red and green marbles so that pulling a green is <b>more likely</b> "
         "than pulling a red. Give the numbers and both probabilities.",
         "Example: 5 green + 2 red (7 total) → green = 5/7, red = 2/7; green is more likely."),
    ]))

    A(challenge(
        P("A spinner has <b>6 equal slices</b>: 3 are <b>Sun ☀</b>, 2 are <b>Cloud ☁</b>, "
          "1 is <b>Rain 🌧</b>. (a) What is the probability of <b>Sun</b>? (b) What is the "
          "probability of <b>NOT Rain</b>? (c) Show your three chances add up to 1.") +
        tryit("Count the slices for each, out of 6.",
              "(a) Sun = 3/6 = <b>½</b>. (b) Not Rain means Sun or Cloud = 3 + 2 = 5 slices = "
              "<b>5/6</b>. (c) Sun + Cloud + Rain = 3/6 + 2/6 + 1/6 = 6/6 = <b>1</b>. ✓")))

    A(kiwi("Nicely done — counting the wanted outcomes over the total is the heart of probability. You can now describe chance in <b>words</b> (impossible → certain) and as a "
           "<b>fraction</b> (ways wanted ÷ ways altogether), and you know all the chances add to "
           "<b>1</b>. Next we'll crack secret-code sums and magic squares — pure puzzle joy. 🔢"))

    chapter("Part 5 · Brain Benders", 16, "Probability",
            "Combinatorics · Probability", "".join(b))
