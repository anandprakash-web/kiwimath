#!/usr/bin/env python3
"""Chapter 10 - Letters for Numbers (Algebra)  (Algebra - Balance the Scale)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, balance, number_line, array_dots,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE, INK)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Imagine a closed box with some marbles inside &mdash; you can't see how many. "
            "How can we do maths with a number we don't even know yet? The amazing answer: give it a "
            "<b>name</b>, like the letter <em>x</em>, and work with the name. That idea is called "
            "<b>algebra</b>."))
    A(kiwi("Kiwi here! Don't let the word 'algebra' scare you &mdash; you already do it. When you think "
           "'3 plus <em>something</em> makes 10, so the something is 7,' you just solved algebra. "
           "All we add is a tidy way to write 'something': a letter. Let's meet it properly."))

    # -- 1. Variables and constants --
    A(H("Letters that hold mystery numbers"))
    A(P("A <b>variable</b> is a letter that stands for a number we don't know yet, or a number that can "
        "change. We often use <em>x</em>, <em>y</em> or <em>n</em>. A <b>constant</b> is a number that "
        "stays fixed &mdash; it never changes, like 5 or 12."))
    A(P("Think of a variable as a <b>mystery box</b> and a constant as a <b>price tag</b> you can already "
        "read. In <b>x + 4</b>, the <em>x</em> is the mystery box and the <b>4</b> is a known constant."))
    A(kiwi("Quick check: a <b>variable</b> wears a letter and can change. A <b>constant</b> is a plain "
           "number and stays put. In <em>m + 7</em>: variable = <b>m</b>, constant = <b>7</b>."))
    A(tryit("In the expression <b>b + 12</b>, which part is the <b>variable</b> and which is the "
            "<b>constant</b>?",
            "Variable = <b>b</b> (the letter, our mystery number). Constant = <b>12</b> (a fixed number)."))

    # -- 2. Terms, coefficient, constant term --
    A(H("The parts of an expression: terms, coefficient, constant"))
    A(P("An <b>expression</b> is a little math phrase, like <b>12 + 5x</b>. It has no equals sign &mdash; "
        "it's a phrase, not a full sentence. The pieces joined by + or &minus; signs are called "
        "<b>terms</b>. In <b>12 + 5x</b> the terms are <b>12</b> and <b>5x</b>."))
    A(P("Look closely at the term <b>5x</b>. The number stuck to the front, <b>5</b>, is the "
        "<b>numerical coefficient</b> &mdash; it tells you <em>how many x's</em> you have. So 5x means "
        "<b>x + x + x + x + x</b> (five mystery boxes). The lonely number <b>12</b>, with no letter, is the "
        "<b>constant term</b>."))
    A(example("name every part of  12 + 5x", steps([
        "Terms (pieces joined by +): <b>12</b> and <b>5x</b>.",
        "Variable: <b>x</b> (the only letter).",
        "Numerical coefficient: <b>5</b> (the number in front of x &mdash; how many x's).",
        "Constant term: <b>12</b> (the number with no letter, fixed forever).",
    ])))
    A(kiwi("Careful: 5x means 5 <em>times</em> x. In algebra we don't write the times sign &mdash; a number "
           "snuggled next to a letter <em>always</em> means multiply. And '<em>x</em>' all alone secretly "
           "has a coefficient of <b>1</b>, because x means 1x."))
    A(tryit("In the expression <b>7y + 3</b>, name the coefficient and the constant term.",
            "Coefficient = <b>7</b> (the number in front of y). Constant term = <b>3</b>."))

    # -- 3. Building expressions from words --
    A(H("Turning words into expressions"))
    A(P("The real magic of algebra is writing a sentence as a short expression. The trick is to let a "
        "letter stand for the unknown, then translate the words into + &minus; x or &divide;."))
    A(P("'<em>5 more than a number</em>' &rarr; let the number be n, so it's <b>n + 5</b>.<br>"
        "'<em>double a number</em>' &rarr; <b>2n</b>.<br>"
        "'<em>3 less than a number</em>' &rarr; <b>n &minus; 3</b>.<br>"
        "'<em>a number shared into 4 equal parts</em>' &rarr; <b>n &divide; 4</b>."))
    A(example("write an expression: 'Riya has some stickers, then gets 6 more'", steps([
        "Let the stickers she started with be <b>s</b> (the mystery number).",
        "'Gets 6 more' means we add 6.",
        "So the expression is <b>s + 6</b>. If we later learn s = 10, she has 10 + 6 = 16.",
    ])))
    A(tryit("Write an expression for: 'A number of apples, <b>doubled</b>, then <b>1 taken away</b>.' "
            "Use the letter a.",
            "Double the apples: 2a. Then take 1 away: <b>2a &minus; 1</b>."))

    # -- 4. Evaluating by substitution --
    A(H("Opening the box: evaluating by substitution"))
    A(P("When someone finally tells us the value of the variable, we <b>substitute</b> &mdash; that just "
        "means swap the letter for its number &mdash; and work it out. Watch what 5x becomes when x = 3, "
        "using dots to show the five groups:"))
    A(figure(array_dots(1, 5, ORANGE), "x = 3? Then 5x = five 3s. (Here 5 boxes; fill each with 3.)"))
    A(example("evaluate  12 + 5x  when x = 3", steps([
        "Swap x for 3: the term 5x becomes 5 x 3 = <b>15</b>.",
        "Now add the constant term: 12 + 15 = <b>27</b>.",
        "So when x = 3, the expression 12 + 5x equals <b>27</b>.",
    ])))
    A(kiwi("Order matters! Do the multiplying (the 5x part) <em>before</em> the adding. "
           "Multiply first, then add the constant. We'll always keep that order."))
    A(tryit("Evaluate <b>2n + 4</b> when <b>n = 6</b>.",
            "2n = 2 x 6 = 12, then add 4: 12 + 4 = <b>16</b>."))
    A(tryit("Evaluate <b>20 &minus; 3y</b> when <b>y = 4</b>.",
            "3y = 3 x 4 = 12, then 20 &minus; 12 = <b>8</b>."))

    # -- 5. Equations and the balance idea --
    A(H("Equations: a balance that must stay level"))
    A(P("Put an <b>equals sign</b> between two things and you have an <b>equation</b> &mdash; a full math "
        "sentence saying 'the left side weighs exactly the same as the right side.' Picture a "
        "<b>balance scale</b>: if both pans hold the same amount, it stays perfectly level."))
    A(figure(balance(5, 5, "5", "5"), "5 = 5: the scale is balanced and level."))
    A(P("Now hide part of the left pan inside a mystery box. The equation <b>x + 3 = 7</b> says: "
        "'a mystery box plus 3 weighs the same as 7.' Our job is to find the weight of the box, x."))
    A(figure(balance(7, 7, "x + 3", "7"), "x + 3 = 7: still balanced, but the left pan hides x."))
    A(P("Golden rule of the scale: <b>whatever you do to one pan, you must do to the other</b>, or it "
        "tips over. To get the box alone, take 3 off the left &mdash; so take 3 off the right too:"))
    A(example("solve  x + 3 = 7  with the balance rule", steps([
        "We want x by itself. The left pan has an extra +3, so remove 3 from the <b>left</b>.",
        "To keep it balanced, remove 3 from the <b>right</b> as well: 7 &minus; 3 = 4.",
        "Now the left pan is just x, and the right is 4. So <b>x = 4</b>.",
        "Check: put 4 back in &mdash; 4 + 3 = 7. The scale balances!",
    ])))
    A(figure(balance(4, 4, "x", "4"), "After taking 3 off both pans: x = 4. Balanced!"))
    A(kiwi("The whole secret of solving simple equations: <b>keep the scale balanced</b>. Add the same "
           "amount to both sides, or take the same amount off both sides, until the mystery box stands "
           "alone. Then read its weight."))

    A(example("solve  x &minus; 2 = 5", steps([
        "The box has 2 taken away from it. To undo that, <b>add 2</b> to the left.",
        "Keep it balanced: add 2 to the right too &rarr; 5 + 2 = 7.",
        "So <b>x = 7</b>. Check: 7 &minus; 2 = 5. ",
    ])))
    A(tryit("Solve <b>x + 6 = 10</b> using the balance rule.",
            "Take 6 off both sides: 10 &minus; 6 = 4. So <b>x = 4</b>. Check: 4 + 6 = 10. "))

    A(P("Multiplication equations work the same way, but we <em>undo</em> times with divide. "
        "<b>3x = 12</b> means 'three boxes weigh 12,' so one box is 12 shared into 3:"))
    A(figure(balance(12, 12, "3x", "12"), "3x = 12: three equal boxes balance 12."))
    A(example("solve  3x = 12", steps([
        "Three equal boxes weigh 12, so one box is 12 &divide; 3.",
        "Divide both sides by 3: 12 &divide; 3 = 4.",
        "So <b>x = 4</b>. Check: 3 x 4 = 12. ",
    ])))
    A(tryit("Solve <b>2x = 14</b>.",
            "Two equal boxes weigh 14, so x = 14 &divide; 2 = <b>7</b>. Check: 2 x 7 = 14."))

    # -- Practice ladder --
    A(H("Now you try - climb the ladder"))
    A(P("Find the variable, then do the math. Always check your answer fits the scale. Peek only after "
        "you've tried!"))

    A(practice("Remember", [
        ("In algebra, a letter like x or y is called a ___ .", "A variable."),
        ("In <b>n + 8</b>, what is the constant?", "8."),
        ("What does <b>4x</b> mean in words?", "4 times x (four x's: x + x + x + x)."),
        ("True or false: an equation has an equals sign.", "True. (An expression does not; an equation does.)"),
    ]))
    A(practice("Understand", [
        ("In <b>6p + 9</b>, name the coefficient and the constant term.",
         "Coefficient = 6 (in front of p); constant term = 9."),
        ("List the terms in <b>8 + 3y</b>.", "The terms are 8 and 3y."),
        ("Write an expression for '7 more than a number m'.", "m + 7."),
        ("What is the coefficient of x in the term <b>x</b> (just x alone)?",
         "1 &mdash; because x means 1x."),
    ]))
    A(practice("Apply", [
        ("Evaluate <b>3n + 2</b> when n = 5.", "3 x 5 = 15, then + 2 = 17."),
        ("Evaluate <b>15 &minus; 2y</b> when y = 4.", "2 x 4 = 8, then 15 &minus; 8 = 7."),
        ("Solve <b>x + 5 = 12</b>.", "Take 5 off both sides: 12 &minus; 5 = 7. So x = 7."),
        ("Solve <b>4x = 20</b>.", "Divide both sides by 4: 20 &divide; 4 = 5. So x = 5."),
    ]))
    A(practice("Analyze", [
        ("Without solving fully, is the x in <b>x + 8 = 5</b> a normal counting number? Explain.",
         "No &mdash; we'd need 5 &minus; 8, which is less than zero. There's no whole number of marbles that works, "
         "so x can't be a counting number here."),
        ("Maya says the coefficient in <b>9 + y</b> is 9. Is she right?",
         "No. 9 is the constant term. The term y has coefficient 1, not 9."),
        ("Two expressions: <b>2n + 3</b> and <b>n + n + 3</b>. Are they the same? Check with n = 4.",
         "Yes, the same. n = 4: 2(4) + 3 = 11, and 4 + 4 + 3 = 11. 2n is just n + n."),
        ("Solve and check: <b>x &minus; 4 = 9</b>.",
         "Add 4 to both sides: 9 + 4 = 13. So x = 13. Check: 13 &minus; 4 = 9. "),
    ]))
    A(practice("Create", [
        ("Write a word story whose equation is <b>x + 4 = 11</b>, then solve it.",
         "E.g. 'I have x marbles, then win 4 more, and now have 11.' Solve: x = 11 &minus; 4 = 7."),
        ("Make an expression with a coefficient of 6 and a constant term of 2.",
         "For example 6x + 2 (or 6n + 2). Any letter works."),
        ("Invent an equation of the form ax = b that has the answer x = 3, and check it.",
         "E.g. 5x = 15 &rarr; x = 15 &divide; 5 = 3. Check: 5 x 3 = 15. (Any a, b with b = 3a works.)"),
    ]))

    A(challenge(
        P("The Mystery Box Riddle! A sealed box of marbles is placed on a scale. Beside it sit 2 loose "
          "marbles. The other pan holds 9 marbles, and the scale balances perfectly.") +
        figure(balance(9, 9, "x + 2", "9"), "x + 2 = 9. How many marbles are in the box?") +
        tryit("Find x, the number of marbles in the box.",
              "The equation is x + 2 = 9. Take 2 off both pans: 9 &minus; 2 = 7. So the box holds "
              "<b>x = 7</b> marbles. Check: 7 + 2 = 9 &mdash; balanced!") +
        P("<b>Bonus:</b> if instead <em>three identical</em> boxes balanced 9 marbles (3x = 9), how "
          "many would be in <em>one</em> box?") +
        tryit("Solve 3x = 9.",
              "Share 9 among the 3 equal boxes: 9 &divide; 3 = <b>3</b> marbles in each box.")))

    A(kiwi("You're an algebra explorer now! You can name variables, constants, terms, coefficients and "
           "constant terms; build expressions from words; open the box by substituting; and solve simple "
           "equations by keeping the scale balanced. From a single mystery letter, a whole new kind of "
           "math opened up &mdash; well done!"))

    chapter("Part 3 · Rule Finders & Balance the Scale", 10, "Letters for Numbers (Algebra)",
            "Algebra · Balance the Scale", "".join(b))
