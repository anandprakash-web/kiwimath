#!/usr/bin/env python3
"""L3 Chapter 12 — The Language of Algebra (Algebra · Letter Maths). Bridges the
Level-2 'letter for a mystery number' idea into a full first algebra: variables,
expressions, terms, coefficients, like terms & simplifying, forming expressions
from words, evaluating by substitution, and solving one-step & two-step equations
with the balance() 'do the same to both sides' idea."""
from l3_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, balance, array_dots, number_line,
                        ORANGE, SKY, GRASS, BERRY, GOLD, PURPLE)


def build(chapter):
    b = []; A = b.append

    A(big_q("I'm thinking of a number. I double it, add 5, and get 17. What was my number? "
            "You could guess… or you could write the whole riddle as one short line — "
            "<b>2x + 5 = 17</b> — and <em>solve</em> it like unlocking a safe. That short line is "
            "<b>algebra</b>: the language that lets you do maths with numbers you don't know yet."))
    A(kiwi("Kiwi here! 🥝 In Level 2 you let a letter stand for a 'mystery number' and solved simple "
           "balances. Now we turn that into a real language — with its own grammar: variables, terms, "
           "coefficients, and rules for tidying expressions and solving equations. Don't worry, every new "
           "word names something you already understand. Let's build the language piece by piece."))

    # ── 1. Variables and constants ─────────────────────
    A(H("Variables: letters that hold a number"))
    A(P("A <b>variable</b> is a letter that stands for a number we don't know yet, or one that can change. "
        "We usually use <em>x</em>, <em>y</em>, <em>n</em> or <em>a</em>. A <b>constant</b> is a fixed number "
        "that never changes, like 5 or 12. Think of a variable as a sealed box and a constant as a price tag "
        "you can already read."))
    A(kiwi("Two quick words: a <b>variable</b> wears a letter and can change; a <b>constant</b> is a plain "
           "number and stays put. In <em>n + 7</em>: variable = <b>n</b>, constant = <b>7</b>."))
    A(tryit("In the expression <b>b + 12</b>, name the variable and the constant.",
            "Variable = <b>b</b> (the letter — our unknown). Constant = <b>12</b> (a fixed number)."))

    # ── 2. Expressions: terms, coefficients ────────────
    A(H("Inside an expression: terms and coefficients"))
    A(P("An <b>expression</b> is a short math phrase with no equals sign, like <b>3x + 5</b>. The pieces "
        "joined by + or − signs are the <b>terms</b> — here <b>3x</b> and <b>5</b>. In the term 3x, the "
        "number in front, <b>3</b>, is the <b>coefficient</b> — it tells you how many x's there are, so "
        "3x means x + x + x. The lonely number <b>5</b>, with no letter, is the <b>constant term</b>."))
    A(example("name every part of  3x + 5", steps([
        "Terms (joined by +): <b>3x</b> and <b>5</b>.",
        "Variable: <b>x</b>.",
        "Coefficient: <b>3</b> (how many x's).",
        "Constant term: <b>5</b> (a fixed number, no letter).",
    ])))
    A(kiwi("In algebra we drop the times sign: <b>3x means 3 × x</b>. A number snuggled next to a letter "
           "always means multiply. And a lonely <em>x</em> secretly has coefficient <b>1</b>, because x = 1x."))
    A(tryit("In <b>7y + 3</b>, name the coefficient and the constant term.",
            "Coefficient = <b>7</b>; constant term = <b>3</b>."))

    # ── 3. Like terms and simplifying ──────────────────
    A(H("Like terms: tidying an expression"))
    A(P("Terms that use the <em>same letter</em> are <b>like terms</b>, and they can be combined — just add "
        "or subtract their coefficients. Terms with different letters, or a letter versus a plain number, "
        "are <b>unlike</b> and must stay apart. (You can add 3 apples + 2 apples = 5 apples, but you "
        "can't add 3 apples + 2 oranges into one kind of fruit.)"))
    A(figure(array_dots(1, 8, ORANGE),
             "5x and 3x are like terms: 5 boxes plus 3 boxes makes 8 boxes → 5x + 3x = 8x."))
    A(example("simplify  4x + 3 + 2x + 5", steps([
        "Group the like terms. The x-terms: 4x and 2x. The constants: 3 and 5.",
        "Add the x-terms: 4x + 2x = <b>6x</b>.",
        "Add the constants: 3 + 5 = <b>8</b>.",
        "Put it back together: <b>6x + 8</b>. We can't combine 6x with 8 — different kinds.",
    ])))
    A(kiwi("Rule for simplifying: <b>collect like with like</b>. Add the coefficients of matching letters; "
           "add the plain numbers. Never mix an x-term with a number — they're different 'fruits.'"))
    A(tryit("Simplify <b>7a + 2a − a</b>.",
            "All like terms (all 'a'): 7 + 2 − 1 = 8, so the answer is <b>8a</b>. (Remember the lonely a "
            "counts as 1a.)"))

    # ── 4. Words into expressions ──────────────────────
    A(H("Turning words into expressions"))
    A(P("The magic of algebra is writing a whole sentence as one short expression. Let a letter stand for "
        "the unknown, then translate the words into + − × or ÷."))
    A(P("'<em>6 more than a number</em>' → <b>n + 6</b>.<br>"
        "'<em>double a number</em>' → <b>2n</b>.<br>"
        "'<em>5 less than a number</em>' → <b>n − 5</b>.<br>"
        "'<em>a number shared into 4 equal parts</em>' → <b>n ÷ 4</b>.<br>"
        "'<em>double a number, then add 3</em>' → <b>2n + 3</b>."))
    A(example("write an expression: 'Ved has some coins, then finds 4 times as many more'", steps([
        "Let Ved's coins be <b>c</b> (the unknown).",
        "'4 times as many more' adds 4c to what he had.",
        "So the total is <b>c + 4c = 5c</b>. (Like terms combine!) If later c = 3, he has 5 × 3 = 15 coins.",
    ])))
    A(tryit("Write an expression for: 'A number of apples, <b>tripled</b>, then <b>2 taken away</b>.' "
            "Use the letter a.",
            "Triple the apples: 3a. Then take 2 away: <b>3a − 2</b>."))

    # ── 5. Evaluating by substitution ──────────────────
    A(H("Opening the box: evaluating by substitution"))
    A(P("When someone tells us the value of the variable, we <b>substitute</b> — swap the letter for its "
        "number — and work it out. Watch out for the order: do the multiplying first, then the adding."))
    A(example("evaluate  3x + 5  when x = 4", steps([
        "Swap x for 4: the term 3x becomes 3 × 4 = <b>12</b>.",
        "Now add the constant: 12 + 5 = <b>17</b>.",
        "So when x = 4, the expression 3x + 5 equals <b>17</b>. (That's our opening riddle, almost solved!)",
    ])))
    A(figure(number_line(0, 20, 5, [(12, "3x = 12", "#3B9CE6"), (17, "+5 \u2192 17", "#E0556E")]),
             "Substituting x = 4: the 3x part lands on 12, then adding the constant 5 reaches 17."))
    A(kiwi("Substitution = 'open the box and put the real number in.' Always multiply the letter-terms "
           "before adding the constant — same order-of-operations rule you already know."))
    A(tryit("Evaluate <b>2n + 7</b> when <b>n = 6</b>.",
            "2n = 2 × 6 = 12, then 12 + 7 = <b>19</b>."))
    A(tryit("Evaluate <b>20 − 3y</b> when <b>y = 4</b>.",
            "3y = 3 × 4 = 12, then 20 − 12 = <b>8</b>."))

    # ── 6. One-step equations: the balance ─────────────
    A(H("Equations: keep the balance level"))
    A(P("Put an <b>equals sign</b> between two things and you get an <b>equation</b> — a full sentence "
        "saying 'the left side weighs the same as the right.' Picture a <b>balance scale</b>: equal pans "
        "stay perfectly level."))
    A(figure(balance(7, 7, "x + 3", "7"),
             "x + 3 = 7: balanced, but the left pan hides x inside a box."))
    A(P("Golden rule of the scale: <b>whatever you do to one pan, do to the other</b>, or it tips. "
        "To free the box, take 3 off the left — so take 3 off the right too:"))
    A(example("solve  x + 3 = 7", steps([
        "The left pan has an extra +3. Remove 3 from the left.",
        "To stay balanced, remove 3 from the right as well: 7 − 3 = 4.",
        "Now the left is just x and the right is 4, so <b>x = 4</b>.",
        "Check: 4 + 3 = 7. ✓",
    ])))
    A(figure(balance(4, 4, "x", "4"), "After taking 3 off both pans: x = 4. Still balanced!"))
    A(P("Subtraction undoes with addition; multiplication undoes with division. <b>3x = 12</b> means "
        "'three boxes weigh 12,' so one box is 12 shared into 3:"))
    A(example("solve  3x = 12", steps([
        "Three identical boxes weigh 12 together. Share equally: divide both sides by 3.",
        "12 ÷ 3 = 4, so one box weighs 4 → <b>x = 4</b>.",
        "Check: 3 × 4 = 12. ✓",
    ])))
    A(figure(balance(4, 4, "x", "4"),
             "Sharing 3x = 12 into three equal boxes: each box is 4, so x = 4. Balanced!"))
    A(tryit("Solve <b>x − 4 = 9</b> using the balance rule.",
            "Add 4 to both sides: 9 + 4 = 13, so <b>x = 13</b>. Check: 13 − 4 = 9. ✓"))
    A(tryit("Solve <b>x ÷ 5 = 4</b>.",
            "Multiply both sides by 5: 4 × 5 = 20, so <b>x = 20</b>. Check: 20 ÷ 5 = 4. ✓"))

    # ── 7. Two-step equations ──────────────────────────
    A(H("Two-step equations: undo in reverse order"))
    A(P("Now we solve our opening riddle, <b>2x + 5 = 17</b>. It was built by <em>first</em> multiplying "
        "by 2, <em>then</em> adding 5. To unlock it, we undo in the <b>reverse order</b>: peel off the "
        "+5 first, then undo the ×2 — like taking off your shoes before your socks."))
    A(figure(balance(17, 17, "2x + 5", "17"),
             "2x + 5 = 17: two boxes plus 5 weigh 17. Peel the +5 first."))
    A(example("solve  2x + 5 = 17", steps([
        "Undo the +5: subtract 5 from both sides. 17 − 5 = 12, leaving <b>2x = 12</b>.",
        "Undo the ×2: divide both sides by 2. 12 ÷ 2 = 6, so <b>x = 6</b>.",
        "Check: 2 × 6 + 5 = 12 + 5 = 17. ✓ Riddle solved — my number was 6!",
    ])))
    A(kiwi("Two-step recipe: <b>first undo the + or − (move the constant), then undo the × or ÷ "
           "(the coefficient)</b>. Always do the same to both sides, and always check by putting your "
           "answer back in."))
    A(example("solve  3x − 5 = 16", steps([
        "Undo the −5: add 5 to both sides. 16 + 5 = 21, so <b>3x = 21</b>.",
        "Undo the ×3: divide both sides by 3. 21 ÷ 3 = 7, so <b>x = 7</b>.",
        "Check: 3 × 7 − 5 = 21 − 5 = 16. ✓",
    ])))
    A(tryit("Solve <b>5x + 2 = 17</b>.",
            "Subtract 2: 5x = 15. Divide by 5: <b>x = 3</b>. Check: 5 × 3 + 2 = 17. ✓"))
    A(tryit("Solve <b>4x − 7 = 13</b>.",
            "Add 7: 4x = 20. Divide by 4: <b>x = 5</b>. Check: 4 × 5 − 7 = 13. ✓"))

    # ── Practice ladder ─────────────────────────────────
    A(H("Now climb the ladder"))
    A(P("Read each phrase or equation carefully — name the parts, simplify, substitute, or solve. "
        "Peek only after you try!"))

    A(practice("Remember", [
        ("In <b>5x + 9</b>, what is the coefficient of x?", "<b>5</b>."),
        ("In <b>5x + 9</b>, what is the constant term?", "<b>9</b>."),
        ("What does <b>4n</b> mean as a multiplication?", "4 × n (four n's added together)."),
        ("Are 3x and 5x like terms or unlike terms?", "<b>Like</b> terms — same letter, x."),
    ]))
    A(practice("Understand", [
        ("Simplify <b>6x + 2x</b>.", "Add coefficients: 6 + 2 = 8 → <b>8x</b>."),
        ("Simplify <b>9k − 4k</b>.", "9 − 4 = 5 → <b>5k</b>."),
        ("Write '7 more than a number n' as an expression.", "<b>n + 7</b>."),
        ("Evaluate <b>4a − 1</b> when a = 5.", "4 × 5 − 1 = 20 − 1 = <b>19</b>."),
    ]))
    A(practice("Apply", [
        ("Simplify <b>4x + 3 + 2x + 5</b>.", "x-terms: 4x + 2x = 6x; constants: 3 + 5 = 8 → <b>6x + 8</b>."),
        ("Solve <b>x + 7 = 12</b>.", "Subtract 7: <b>x = 5</b>. Check: 5 + 7 = 12. ✓"),
        ("Solve <b>3x = 12</b>.", "Divide by 3: <b>x = 4</b>. Check: 3 × 4 = 12. ✓"),
        ("Evaluate <b>6 + 2m</b> when m = 7.", "2 × 7 = 14, then 6 + 14 = <b>20</b>."),
    ]))
    A(practice("Analyze", [
        ("Solve the two-step equation <b>2x + 3 = 11</b>.",
         "Subtract 3: 2x = 8. Divide by 2: <b>x = 4</b>. Check: 2 × 4 + 3 = 11. ✓"),
        ("A friend simplifies 4x + 3 to 7x. What's the mistake?",
         "4x and 3 are <b>unlike</b> terms (a box vs a plain number) and can't be combined. It stays <b>4x + 3</b>."),
        ("The perimeter of a square with side s is 4s. Write and evaluate the perimeter when s = 6 cm.",
         "Perimeter = 4s = 4 × 6 = <b>24 cm</b>."),
        ("Solve <b>3x − 5 = 16</b> and show your check.",
         "Add 5: 3x = 21. Divide by 3: <b>x = 7</b>. Check: 3 × 7 − 5 = 21 − 5 = 16. ✓"),
    ]))
    A(practice("Create", [
        ("Write your own one-step equation whose answer is x = 8, and show how to solve it.",
         "e.g. x + 5 = 13 → subtract 5 → x = 8. (Or 2x = 16 → divide by 2 → x = 8.) Any equation that "
         "works is fine."),
        ("Turn this riddle into an equation and solve it: 'I think of a number, multiply by 2, add 5, and "
         "get 17.'",
         "2x + 5 = 17 → subtract 5: 2x = 12 → divide by 2: <b>x = 6</b>."),
        ("Invent a 'collect like terms' expression that simplifies to 5y + 4, and show the steps.",
         "e.g. 2y + 1 + 3y + 3 → (2y + 3y) + (1 + 3) = <b>5y + 4</b>. Any matching split works."),
    ]))

    A(challenge(
        P("The final unlock! Riya thinks of a number. She notices something curious: if she <b>doubles her "
          "number and adds 4</b>, she gets the very same answer as when she <b>adds 19 to her number</b>. "
          "What is Riya's number? (Hint: write both descriptions as expressions, set them equal, and use "
          "the balance rule — this time there's an x on <em>both</em> pans!)") +
        tryit("Set the two expressions equal, then peel the boxes apart.",
              "Let her number be x. 'Double and add 4' = <b>2x + 4</b>. 'Add 19' = <b>x + 19</b>. Setting them "
              "equal: 2x + 4 = x + 19. Take one x off both pans (same to both sides!): x + 4 = 19. "
              "Now take 4 off both: <b>x = 15</b>. Check: 2 × 15 + 4 = 34, and 15 + 19 = 34 — they match! 🎉 "
              "You just solved an equation with the unknown on both sides — real algebra!")))

    A(kiwi("Outstanding — you now speak algebra! You can name variables, terms, coefficients and constants, "
           "simplify by collecting like terms, turn words into expressions, evaluate by substitution, and "
           "solve one-step <em>and</em> two-step equations by keeping the balance level. This letter-language "
           "is the key that unlocks all the maths ahead. 🔑"))

    chapter("Part 4 · Rule Finders & Letter Maths", 12, "The Language of Algebra",
            "Algebra · Letter Maths", "".join(b))
