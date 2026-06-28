#!/usr/bin/env python3
"""Chapter 2 — Comparing, Ordering & Smart Operations  (Number Theory · Big Numbers)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, compare, number_line, pv_table, array_dots)


def build(chapter):
    b = []
    A = b.append

    A(big_q("Two video-game high scores flash on the screen: <b>2304</b> and <b>2340</b>. They look almost "
            "the same — both start with 23! So which player scored more… and how can you be <em>sure</em> "
            "in one quick glance?"))
    A(kiwi("Welcome back, it's <b>Kiwi</b> again! In Chapter 1 you learned that a digit's <b>place</b> "
           "decides how big it is. That very idea is the key to comparing numbers quickly. "
           "Let's begin where every detective begins — by counting the clues."))

    # ── COMPARING ────────────────────────────────────────────────
    A(H("Step 1 — count the digits first"))
    A(P("Before you look at anything else, count <em>how many digits</em> each number has. "
        "A number with <b>more digits</b> is always bigger. Think about it: the smallest 4-digit number "
        "is 1000, but the biggest 3-digit number is only 999. So <b>any</b> 4-digit number beats <b>any</b> "
        "3-digit number — no contest!"))
    A(figure(compare(1000, 999), "1000 has 4 digits, 999 has only 3 — so 1000 wins."))
    A(kiwi("Quick rule: <b>longer number = larger number</b> (as long as there are no extra zeros stuck "
           "on the front). Count the digits before anything else."))

    A(H("Step 2 — same length? Compare from the LEFT"))
    A(P("When two numbers have the <em>same</em> number of digits, we line them up and compare digit by "
        "digit, starting from the <b>left</b> — the biggest place first. The first place where they "
        "differ decides the winner."))
    A(P("Let's settle our two game scores, <b>2304</b> and <b>2340</b>:"))
    A(example("comparing 2304 and 2340", steps([
        "Thousands: 2 = 2 (tie, keep going).",
        "Hundreds: 3 = 3 (tie, keep going).",
        "Tens: <b>0</b> vs <b>4</b> — here they differ! 4 is bigger than 0.",
        "So 2340 is the larger number: <b>2340 &gt; 2304</b>.",
    ]) + P("We never even needed the ones digit. The first difference settles it.")))
    A(figure(compare(2304, 2340), "2304 < 2340"))
    A(P("It helps to stack them in a place-value chart so every column lines up — then your eye sweeps "
        "from the left and stops at the first column that's different (here, the tens):"))
    A(figure(pv_table(2304) + pv_table(2340), "Stacked in place-value columns: same until the tens, where 0 < 4."))
    A(P("The two signs we use are <b>&gt;</b> (greater than) and <b>&lt;</b> (less than). The open, "
        "hungry mouth always gobbles the <em>bigger</em> number. So 2340 &gt; 2304 reads "
        "“2340 is greater than 2304”."))
    A(kiwi("Memory trick: the <b>&gt;</b> sign is a hungry crocodile 🐊 — it always opens its mouth "
           "toward the bigger meal!"))

    A(tryit("Put the correct sign (&gt; or &lt;) between <b>5176</b> and <b>5168</b>.",
            "Thousands tie (5=5), hundreds tie (1=1), tens differ: 7 vs 6 → 7 is bigger. "
            "So <b>5176 &gt; 5168</b>."))

    # ── ORDERING ─────────────────────────────────────────────────
    A(H("Ordering — lining numbers up smallest to biggest"))
    A(P("<b>Ascending order</b> means going <em>up</em> — smallest to biggest (think of climbing stairs). "
        "<b>Descending order</b> means going <em>down</em> — biggest to smallest (think of a slide). "
        "A number line is the perfect picture: numbers always grow as you move to the right."))
    A(figure(number_line(0, 50, 10, [(15, "15", "#3B9CE6"), (28, "28", "#39A85B"), (44, "44", "#E0556E")]),
             "On a number line, bigger numbers always sit further right."))
    A(example("order 415, 451, 145, 154 from smallest to largest", steps([
        "All four have 3 digits, so we compare from the left.",
        "Look at the hundreds digit: 145 and 154 start with <b>1</b>; 415 and 451 start with <b>4</b>. "
        "So the two 1__ numbers are smaller.",
        "Between 145 and 154: tens are 4 vs 5, so 145 &lt; 154.",
        "Between 415 and 451: tens are 1 vs 5, so 415 &lt; 451.",
        "Ascending order: <b>145, 154, 415, 451</b>.",
    ])))
    A(tryit("Write <b>2090, 2009, 2900, 2099</b> in <b>descending</b> order (biggest first).",
            "All start with 2. Compare hundreds: 2<b>9</b>00 is biggest. Then among 2090, 2009, 2099 the "
            "hundreds are all 0, so compare tens: 2<b>9</b>9 → 2099, then 2<b>9</b>0 → 2090, then 2009. "
            "Descending: <b>2900, 2099, 2090, 2009</b>."))

    # ── FORMING LARGEST / SMALLEST ───────────────────────────────
    A(H("The digit puzzle — building the biggest and smallest number"))
    A(P("Here's a favourite olympiad game. You're handed some digit cards and asked to arrange them into "
        "the <b>largest</b> or <b>smallest</b> number. The secret comes straight from place value: the "
        "<em>leftmost place is worth the most</em>, so that's where your most powerful digit should go."))
    A(P("Suppose your cards are <b>7, 2, 9, 4</b>."))
    A(example("largest number from 7, 2, 9, 4", steps([
        "Biggest place (thousands) gets the biggest digit: 9.",
        "Next place (hundreds) gets the next biggest: 7.",
        "Then 4, then 2.",
        "Largest number = <b>9742</b>.",
    ])))
    A(example("smallest number from 7, 2, 9, 4", steps([
        "Biggest place gets the <em>smallest</em> digit this time: 2.",
        "Then 4, then 7, then 9.",
        "Smallest number = <b>2479</b>.",
    ])))
    A(kiwi("So <b>largest</b> = sort the digits big→small. <b>Smallest</b> = sort them small→big. "
           "Same digits, opposite order!"))
    A(P("⚠️ <b>The zero trap.</b> If <b>0</b> is one of your cards, you can't start the smallest number "
        "with it — a number can't begin with 0 (0468 is really just 468, a 3-digit number). So for the "
        "smallest number, put the <em>smallest digit that isn't zero</em> first, then drop the 0 right "
        "after it."))
    A(example("smallest 4-digit number from 0, 5, 3, 8", steps([
        "Sorted small→big that's 0, 3, 5, 8 — but we can't lead with 0.",
        "Put the smallest non-zero digit (3) first.",
        "Then place the 0 next, then 5, then 8.",
        "Smallest number = <b>3058</b>.  (The largest is easy: <b>8530</b>.)",
    ])))
    A(tryit("Using the digits <b>6, 0, 1, 4</b> once each, make the largest and smallest 4-digit numbers.",
            "Largest: sort big→small → <b>6410</b>. Smallest: can't start with 0, so smallest non-zero "
            "is 1, then 0, then 4, then 6 → <b>1046</b>."))

    # ── SMART OPERATIONS: ADDITION ───────────────────────────────
    A(H("Smart addition — line up the places and carry"))
    A(P("Adding big numbers is easy if you obey one golden rule: <b>line up the places</b> — ones under "
        "ones, tens under tens — and add each column starting from the <b>right</b>. When a column adds "
        "up to 10 or more, you <b>carry</b> the extra ten into the next column."))
    A(P("Why carry? Because ten ones bundle into one ten — exactly the base-ten idea from Chapter 1!"))
    A(example("add 3 8 6 5 + 2 4 7 8", steps([
        "Ones: 5 + 8 = 13. Write <b>3</b>, carry <b>1</b> ten.",
        "Tens: 6 + 7 = 13, plus the carried 1 = 14. Write <b>4</b>, carry <b>1</b> hundred.",
        "Hundreds: 8 + 4 = 12, plus carried 1 = 13. Write <b>3</b>, carry <b>1</b> thousand.",
        "Thousands: 3 + 2 = 5, plus carried 1 = <b>6</b>.",
        "Answer: <b>6343</b>.  (Check: 3865 + 2478 = 6343 ✓)",
    ])))
    A(kiwi("To check an addition quickly, add the numbers in a different order or round them: "
           "3865 ≈ 3900 and 2478 ≈ 2500, so the answer should be near 6400 — and 6343 is. Close estimate = "
           "good sign!"))
    A(tryit("Add <b>4 5 9 6 + 1 7 0 8</b>.",
            "Ones: 6+8=14 (write 4, carry 1). Tens: 9+0+1=10 (write 0, carry 1). Hundreds: 5+7+1=13 "
            "(write 3, carry 1). Thousands: 4+1+1=6. Answer = <b>6304</b>."))

    # ── SMART OPERATIONS: SUBTRACTION ────────────────────────────
    A(H("Smart subtraction — borrow when you need to"))
    A(P("Subtraction works the same way, but instead of carrying we <b>borrow</b>. If the top digit in a "
        "column is too small, we borrow one from the place to its left. That borrowed 1 is worth "
        "<em>ten</em> in the column it moves into."))
    A(example("subtract 6 0 0 4 − 2 7 5 8", steps([
        "Ones: 4 − 8 won't work. Borrow from the tens — but the tens are 0, and so are the hundreds! "
        "So we borrow all the way from the thousands.",
        "After borrowing across the zeros: 6004 becomes 5 thousands, 9 hundreds, 9 tens, 14 ones.",
        "Ones: 14 − 8 = <b>6</b>.",
        "Tens: 9 − 5 = <b>4</b>.",
        "Hundreds: 9 − 7 = <b>2</b>.",
        "Thousands: 5 − 2 = <b>3</b>.",
        "Answer: <b>3246</b>.  (Check by adding back: 3246 + 2758 = 6004 ✓)",
    ])))
    A(kiwi("Always check a subtraction by <b>adding your answer back</b> to the number you took away — "
           "you should land on the number you started with. It's like undoing the subtraction!"))
    A(tryit("Subtract <b>5 2 0 3 − 1 6 4 7</b>.",
            "Ones: 3−7 → borrow, 13−7=6. Tens: the 0 lent out so it's 9; 9−4=5. Hundreds: 1−6 → borrow, "
            "11−6=5. Thousands: 4−1=3. Answer = <b>3556</b>. (Check: 3556 + 1647 = 5203 ✓)"))

    # ── SMART OPERATIONS: MULTIPLICATION ─────────────────────────
    A(H("Multiplication — fast repeated adding"))
    A(P("Multiplication is just adding the same number over and over, but much quicker. "
        "5 × 4 means <em>five groups of four</em> — and we can draw it as a neat <b>array</b> of dots:"))
    A(figure(array_dots(5, 4), "5 rows of 4 dots = 20 dots, so 5 × 4 = 20"))
    A(P("A super-handy trick is multiplying by <b>10, 100 or 1000</b>: just stick on zeros! "
        "Multiplying by 10 shifts every digit one place to the left (it becomes ten times bigger), "
        "so you tack a 0 on the end."))
    A(example("multiply by 10, 100 and 1000", steps([
        "47 × 10 = <b>470</b> (one zero added).",
        "47 × 100 = <b>4700</b> (two zeros added).",
        "47 × 1000 = <b>47000</b> (three zeros added).",
    ])))
    A(P("For a bigger multiply, we break the second number into its places. To work out <b>234 × 6</b>:"))
    A(example("multiply 234 × 6", steps([
        "Ones: 6 × 4 = 24. Write <b>4</b>, carry <b>2</b>.",
        "Tens: 6 × 3 = 18, plus carried 2 = 20. Write <b>0</b>, carry <b>2</b>.",
        "Hundreds: 6 × 2 = 12, plus carried 2 = <b>14</b>. Write 14.",
        "Answer: <b>1404</b>.  (Check by estimate: 234 ≈ 230, 230 × 6 = 1380 — close to 1404 ✓)",
    ])))
    A(tryit("What is <b>125 × 8</b>?",
            "Ones: 8×5=40 (write 0, carry 4). Tens: 8×2=16, +4=20 (write 0, carry 2). Hundreds: "
            "8×1=8, +2=10. Answer = <b>1000</b>. (Neat — 125 × 8 = 1000!)"))

    # ── SMART OPERATIONS: DIVISION ───────────────────────────────
    A(H("Division — sharing equally"))
    A(P("Division asks: <em>if I share this fairly, how much does each one get?</em> "
        "It's the <b>opposite</b> of multiplication. Because 6 × 4 = 24, we also know 24 ÷ 6 = 4 and "
        "24 ÷ 4 = 6. They're a family!"))
    A(P("Sometimes a number doesn't share evenly and a little is left over — we call that the "
        "<b>remainder</b>."))
    A(P("A number line makes the remainder easy to see. To share 27 by 4, hop in 4s — you land on 24 "
        "(that's 6 hops) but 27 is 3 steps further on, so 3 is left over:"))
    A(figure(number_line(0, 28, 4, [(24, "6×4", "#39A85B"), (27, "27", "#E0556E")]),
             "27 sits 3 steps past 24, so 27 ÷ 4 = 6 remainder 3."))
    A(example("share 27 marbles among 4 friends", steps([
        "How many 4s fit into 27? 4 × 6 = 24, and 4 × 7 = 28 (too big).",
        "So each friend gets <b>6</b> marbles, using up 24.",
        "Left over: 27 − 24 = <b>3</b> marbles — that's the remainder.",
        "Answer: 27 ÷ 4 = <b>6 remainder 3</b>.",
    ])))
    A(kiwi("Word-problem tip: read it twice. Ask yourself — am I putting things <b>together</b> (add), "
           "taking <b>away</b> (subtract), making equal <b>groups</b> (multiply), or <b>sharing</b> "
           "equally (divide)? Picking the right action is half the battle."))
    A(tryit("A baker packs <b>96 cookies</b> into boxes of <b>8</b>. How many full boxes does she get?",
            "We need how many 8s are in 96. 8 × 12 = 96 exactly, so she gets <b>12</b> full boxes, with "
            "no cookies left over."))

    A(example("a two-step word problem", P("A shop had <b>1500</b> pencils. It sold <b>378</b> on Monday "
        "and <b>425</b> on Tuesday. How many pencils are left?") + steps([
        "First find the total sold: 378 + 425 = <b>803</b> pencils.",
        "Then subtract from the start: 1500 − 803 = <b>697</b> pencils left.",
        "Answer: <b>697 pencils</b>. (Two steps: add, then subtract.)",
    ])))

    # ── PRACTICE LADDER ──────────────────────────────────────────
    A(H("Now you climb the ladder — practice!"))
    A(P("Start at the bottom and work up. Try each one before you peek at the answer."))

    A(practice("Remember", [
        ("Which sign goes here: 487 ? 489 ?  (&gt; or &lt;)", "&lt; — because 487 is less than 489."),
        ("Which is bigger: 6000 or 999?", "6000 (it has 4 digits; 999 has only 3)."),
        ("What does <b>ascending order</b> mean?", "Arranging numbers from smallest to largest."),
        ("Fill in: 8 × 100 = ?", "800."),
        ("What is the remainder when 20 is shared among 6?", "6 × 3 = 18, so quotient 3, remainder <b>2</b>."),
    ]))
    A(practice("Understand", [
        ("Put the right sign between 3 0 5 6 and 3 0 6 5.",
         "Thousands tie, hundreds tie, tens differ: 5 vs 6 → 3056 &lt; 3065."),
        ("Arrange in ascending order: 707, 770, 77, 700.",
         "Count digits: 77 is 2-digit (smallest). Then 700, 707, 770. → 77, 700, 707, 770."),
        ("Estimate 596 + 311 by rounding to the nearest hundred.",
         "596 ≈ 600 and 311 ≈ 300, so about 900. (Exact answer is 907.)"),
        ("Write the multiplication and division facts in the family of 7 × 9 = 63.",
         "7 × 9 = 63, 9 × 7 = 63, 63 ÷ 7 = 9, 63 ÷ 9 = 7."),
    ]))
    A(practice("Apply", [
        ("Add: 4 9 0 7 + 3 6 9 8.",
         "Ones 7+8=15(5,c1), tens 0+9+1=10(0,c1), hundreds 9+6+1=16(6,c1), thousands 4+3+1=8 → <b>8605</b>."),
        ("Subtract: 7 0 0 5 − 2 4 6 7.",
         "Borrowing across the zeros: ones 15−7=8, tens 9−6=3, hundreds 9−4=5, thousands 6−2=4 → <b>4538</b>. "
         "(Check: 4538 + 2467 = 7005 ✓)"),
        ("Multiply: 408 × 7.",
         "Ones 7×8=56(6,c5), tens 7×0=0+5=5, hundreds 7×4=28 → <b>2856</b>."),
        ("A train has 9 coaches and each coach seats 84 people. How many seats in all?",
         "84 × 9: ones 9×4=36(6,c3), tens 9×8=72+3=75 → <b>756 seats</b>."),
        ("Share 75 sweets equally among 9 children. How many each, and how many left?",
         "9 × 8 = 72, so 8 each, remainder 75 − 72 = <b>3</b>. So 8 sweets each, 3 left over."),
    ]))
    A(practice("Analyze", [
        ("Use the digits 5, 0, 8, 2 once each. Make the largest and smallest 4-digit numbers, then "
         "find their <b>difference</b>.",
         "Largest = 8520. Smallest (no leading 0) = 2058. Difference = 8520 − 2058 = <b>6462</b>."),
        ("Without fully calculating, which is bigger: 2999 + 1 or 3000 − 1? Explain.",
         "2999 + 1 = 3000 and 3000 − 1 = 2999, so <b>2999 + 1 is bigger</b> by 1."),
        ("A 4-digit number rounds to 5000 (nearest hundred) and its ones digit is 0. Could it be 4960? "
         "Could it be 5040?",
         "4960 rounds to 5000 ✓ and ends in 0 ✓. 5040 rounds to 5000 ✓ and ends in 0 ✓. <b>Both work.</b>"),
        ("Two numbers add up to 1000. One of them is 627. Which is bigger, and by how much?",
         "The other is 1000 − 627 = 373. So 627 is bigger, by 627 − 373 = <b>254</b>."),
    ]))
    A(practice("Create", [
        ("Using the digits 3, 4, 1, 0, make the smallest 4-digit number that is also <b>even</b>.",
         "Smallest using 0,1,3,4 without a leading zero is 1034 — and it ends in 4, so it's even ✓. "
         "Answer: <b>1034</b>."),
        ("Invent a subtraction of two 4-digit numbers whose answer is exactly 1111, then check it.",
         "Many work! E.g. 3456 − 2345 = 1111. Check: 1111 + 2345 = 3456 ✓."),
        ("Design a word problem that needs <b>two</b> steps (one add and one subtract) and solve it.",
         "Example: “I had ₹500, earned ₹120, then spent ₹275. How much now?” → 500 + 120 = 620; "
         "620 − 275 = <b>₹345</b>."),
    ]))

    A(challenge(
        P("Riya has four digit cards: <b>9, 5, 0, 7</b>. She makes the largest possible number and the "
          "smallest possible number (no number may start with 0). She then <b>adds</b> them together. "
          "What total does she get?") +
        tryit("Build both numbers carefully, then add.",
              "Largest = 9750. Smallest (can't lead with 0) = 5079. "
              "Add: 9750 + 5079 → ones 0+9=9, tens 5+7=12(2,c1), hundreds 7+0+1=8, thousands 9+5=14. "
              "Total = <b>14829</b>.")))

    A(kiwi("Nice — you compared those by reading the places left to right, exactly the right way. You can "
           "now compare and order any numbers, build the biggest and smallest, "
           "and add, subtract, multiply and divide them — even in word problems. Next up: we meet the "
           "secret <b>families</b> that numbers belong to — factors, multiples and the mysterious "
           "primes. 🔍"))

    chapter("Part 1 · Big Numbers", 2, "Comparing, Ordering & Smart Operations",
            "Number Theory · Big Numbers", "".join(b))
