#!/usr/bin/env python3
"""Chapter 1 — Place Value & Reading Big Numbers  (Number Theory · Big Numbers)."""
from l2_helpers import (H, P, kiwi, big_q, figure, example, steps, tryit, practice,
                        challenge, base_ten, pv_table, place_arrows, number_line)


def build(chapter):
    b = []
    A = b.append

    A(big_q("There are only <b>ten</b> little symbols — 0, 1, 2, 3, 4, 5, 6, 7, 8, 9. "
            "So how on earth can we write <b>every</b> number in the world… even a million?"))
    A(kiwi("Hi, I'm <b>Kiwi</b>! I'll be right beside you the whole way. Here's a secret that great "
           "mathematicians know: it's not just <em>which</em> digits you use — it's <em>where you put them</em>. "
           "That idea is called <b>place value</b>, and once it clicks, big numbers stop being scary."))

    A(H("A digit's home decides how big it is"))
    A(P("Look at the number <b>2</b> in these two numbers: <b>2</b>5 and 5<b>2</b>. Same digit, "
        "but in the first it means <em>twenty</em>, and in the second it means just <em>two</em>. "
        "The digit didn't change — its <b>place</b> did."))
    A(P("Think of numbers as built from three kinds of building blocks: single <b>ones</b>, "
        "sticks of <b>tens</b>, and flat squares of <b>hundreds</b>. Here is the number <b>243</b> built from blocks:"))
    A(figure(base_ten(2, 4, 3), "243 = 2 hundred-squares + 4 ten-sticks + 3 ones"))
    A(P("Every time you collect <b>ten</b> of something, it bundles up into the next block: "
        "ten ones make one ten, ten tens make one hundred, ten hundreds make one thousand. "
        "That bundling-by-ten is why we call it the <b>base-ten</b> system."))

    A(H("The place-value chart"))
    A(P("We give each place a name. Reading from the right: <b>Ones</b>, <b>Tens</b>, "
        "<b>Hundreds</b>, <b>Thousands</b>. Let's drop the number <b>8964</b> into a chart:"))
    A(figure(pv_table(8964), "8964 in a place-value chart: 8 thousands, 9 hundreds, 6 tens, 4 ones"))
    A(kiwi("Notice the places get <b>ten times bigger</b> each step to the left: 1 → 10 → 100 → 1000. "
           "Stepping left multiplies by ten; stepping right divides by ten."))

    A(H("Two values for every digit: face value and place value"))
    A(P("Each digit carries <em>two</em> numbers with it:"))
    A(P("• Its <b>face value</b> — just the digit itself. The face value of the 8 in 8964 is simply <b>8</b>.<br>"
        "• Its <b>place value</b> — the digit <em>multiplied by what its place is worth</em>. "
        "The 8 sits in the <b>thousands</b> place, so its place value is 8 × 1000 = <b>8000</b>."))
    A(P("If we pull 8964 apart by place value, we can see exactly what each digit is really worth. "
        "This is called <b>expanded form</b>:"))
    A(figure(place_arrows(8964), "8964 = 8000 + 900 + 60 + 4"))

    A(example("place value of each digit in 8964", steps([
        "The <b>8</b> is in thousands → place value = 8 × 1000 = <b>8000</b>.",
        "The <b>9</b> is in hundreds → place value = 9 × 100 = <b>900</b>.",
        "The <b>6</b> is in tens → place value = 6 × 10 = <b>60</b>.",
        "The <b>4</b> is in ones → place value = 4 × 1 = <b>4</b>.",
        "Add them back up: 8000 + 900 + 60 + 4 = 8964. ✓ It really is the same number!",
    ])))

    A(tryit("In the number <b>5 7 3 2</b>, what is the <b>place value</b> of the 7? "
            "And what is its <b>face value</b>?",
            "The 7 is in the <b>hundreds</b> place, so its place value is 7 × 100 = <b>700</b>. "
            "Its face value is just <b>7</b>."))

    A(H("A favourite puzzle: the difference of two place values"))
    A(P("Olympiads love this one, and now you can crack it. <b>In 8964, what is the difference "
        "between the place value of 8 and the place value of 9?</b>"))
    A(example("difference of place values", steps([
        "Place value of <b>8</b> = 8000 (it's in thousands).",
        "Place value of <b>9</b> = 900 (it's in hundreds).",
        "Difference = 8000 − 900 = <b>7100</b>.",
    ]) + P("<b>Watch out!</b> A common trap is to subtract the digits (8 − 9) or the face values. "
           "The question asks about <em>place</em> values, so we use 8000 and 900.")))

    A(H("Reading and writing big numbers"))
    A(P("When numbers get long, we group the digits to read them easily — and there are <b>two systems</b> "
        "for doing it. In the <b>Indian system</b> we group as <b>2,31,456</b> (a group of 3, then groups "
        "of 2) and say “two lakh thirty-one thousand four hundred fifty-six”. "
        "In the <b>international system</b> we group in threes — <b>231,456</b> — “two hundred thirty-one "
        "thousand, four hundred fifty-six”. Same number, two ways to write the commas and say it."))
    A(P("As numbers grow past the thousands, the two systems use <b>different big-number names</b>. "
        "The Indian system counts in <b>lakhs</b> and <b>crores</b>; the international system counts in "
        "<b>millions</b>. Line them up side by side:"))
    A('<table class="pv"><tr><th>Number</th><th>Indian grouping &amp; name</th>'
      '<th>International grouping &amp; name</th></tr>'
      '<tr><td>1,000</td><td>1,000 — one thousand</td><td>1,000 — one thousand</td></tr>'
      '<tr><td>100,000</td><td><b>1,00,000</b> — one <b>lakh</b></td>'
      '<td><b>100,000</b> — one hundred thousand</td></tr>'
      '<tr><td>1,000,000</td><td><b>10,00,000</b> — ten <b>lakh</b></td>'
      '<td><b>1,000,000</b> — one <b>million</b></td></tr>'
      '<tr><td>10,000,000</td><td><b>1,00,00,000</b> — one <b>crore</b></td>'
      '<td><b>10,000,000</b> — ten million</td></tr></table>')
    A(P("So <b>1 lakh = 100 thousand</b>, <b>10 lakh = 1 million</b>, and <b>1 crore = 10 million</b>. "
        "Notice how the commas fall in different places: the Indian way puts the first comma after 3 digits "
        "from the right and then every 2 digits (1,00,000), while the international way puts a comma every "
        "3 digits (100,000)."))
    A(example("write 12,34,567 and read it the Indian way", steps([
        "Indian grouping puts commas as <b>12,34,567</b> — a 3-digit group on the right, then 2-digit groups.",
        "Read it from the left: <b>12 lakh</b>, <b>34 thousand</b>, <b>5 hundred</b>, <b>67</b>.",
        "So 12,34,567 is “<b>twelve lakh thirty-four thousand five hundred sixty-seven</b>”.",
        "The same number in the international system is grouped <b>1,234,567</b> — “one million, two hundred "
        "thirty-four thousand, five hundred sixty-seven”.",
    ])))
    A(kiwi("Tip: always build the number from the <b>right</b> (the ones), because that's where the bundling starts. "
           "Find the ones first, then tens, then hundreds… and place the commas to match whichever system "
           "you're using."))
    A(tryit("Write <b>4 thousands, 0 hundreds, 7 tens and 5 ones</b> as one number.",
            "Place them in order: thousands 4, hundreds 0, tens 7, ones 5 → <b>4075</b>. "
            "(The 0 is important — it holds the hundreds place empty so the 4 stays in thousands.)"))

    A(H("Now you try — climb the ladder"))
    A(P("Start easy and move up. Peek at an answer only after you've tried!"))

    A(practice("Remember", [
        ("Name the place of the underlined digit: 3<b>4</b>72.", "Hundreds place."),
        ("What is the <b>face value</b> of 6 in 7613?", "6."),
        ("Which digit is in the <b>tens</b> place of 5098?", "9."),
    ]))
    A(practice("Understand", [
        ("Write 6051 in <b>expanded form</b>.", "6000 + 0 + 50 + 1 = 6000 + 50 + 1."),
        ("What is the <b>place value</b> of 7 in 2719?", "7 is in hundreds → 7 × 100 = 700."),
        ("Build the number: 3 thousands + 2 tens + 8 ones.", "3028 (hundreds place is empty, so it's 0)."),
    ]))
    A(practice("Apply", [
        ("In 4286, find the difference between the place value of 4 and the place value of 2.",
         "4000 − 200 = 3800."),
        ("The place value of a digit is 600 and it sits in a 4-digit number. Which place is it, and what is the digit?",
         "Hundreds place; the digit is 6 (because 6 × 100 = 600)."),
        ("Add the place values of the two 5s in 5350.",
         "First 5 (thousands) = 5000; second 5 (tens) = 50; total = 5050."),
    ]))
    A(practice("Analyze", [
        ("How many of these numbers have the digit <b>3</b> in the <b>hundreds</b> place? "
         "4302, 1234, 8365, 9300, 5031, 2317.",
         "Check the hundreds digit of each: 4<u>3</u>02 ✓, 12<u>3</u>4 ✗(that 3 is tens), 8<u>3</u>65 ✓, "
         "9<u>3</u>00 ✓, 50<u>3</u>1 ✗(tens), 2<u>3</u>17 ✓ → <b>4 numbers</b>."),
        ("True or false: in 7777, every 7 has the same place value.",
         "False — the place values are 7000, 700, 70 and 7. Same face value, different place values."),
    ]))
    A(practice("Create", [
        ("Use the digits <b>1, 3, 7, 9</b> once each to make the <b>largest</b> possible 4-digit number, "
         "then the <b>smallest</b>.",
         "Largest: put the biggest digit on the left → <b>9731</b>. Smallest: smallest digit on the left → <b>1379</b>."),
        ("Make a 4-digit number where the place value of one digit is exactly <b>100 times</b> its face value, "
         "and explain why.",
         "Any number with that digit in the hundreds place, e.g. 2<b>5</b>14: the 5 has place value 500 = 100 × 5."),
    ]))

    A(challenge(
        P("I am a 4-digit number. The place value of my thousands digit is <b>6000</b>. My hundreds digit "
          "is <b>2 less</b> than my thousands digit. My tens digit equals my hundreds digit, and my ones "
          "digit is <b>0</b>. Who am I?") +
        tryit("Work it out place by place.",
              "Thousands digit = 6 (since its place value is 6000). Hundreds digit = 6 − 2 = 4. "
              "Tens digit = 4. Ones digit = 0. So I am <b>6440</b>.")))

    A(kiwi("Nice — you worked that out place by place, which is exactly the right method. You now know "
           "place value, face value, expanded form, the lakh/crore vs million systems, and even the "
           "place-value difference puzzle. In the next chapter we'll use this to <b>compare and order</b> "
           "big numbers — and add, subtract and multiply them. 🚀"))

    chapter("Part 1 · Big Numbers", 1, "Place Value & Reading Big Numbers",
            "Number Theory · Big Numbers", "".join(b))
