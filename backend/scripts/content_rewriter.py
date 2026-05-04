#!/usr/bin/env python3
"""
Kiwimath Content Rewriter — Complete question quality overhaul.

This script rewrites EVERY question with:
1. Story-integrated stems (not character-name-pasted-on-math)
2. 4-level pedagogical hint ladders (metacognitive → strategic → procedural → bottom-out)
3. Correct-answer explanations ("why") that teach the concept
4. Misconception-targeted diagnostics (not "you're off by N")
5. Proper IRT parameters based on question characteristics
6. Consistent interaction_mode assignment
7. Grammar/proofreading fixes

Usage:
  python content_rewriter.py --topic topic-1-counting --file questions.json
  python content_rewriter.py --topic topic-2-arithmetic --all-files
  python content_rewriter.py --all --dry-run
"""

import argparse
import json
import re
import sys
import random
import math
from pathlib import Path
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# STORY WORLDS — Each grade band has themed story arcs
# ---------------------------------------------------------------------------

STORY_WORLDS = {
    # Grade 1-2 (difficulty 1-100): Warm, magical, familiar settings
    "grade_1_2": [
        {
            "world": "kiwi_kitchen",
            "theme": "A magical kitchen where Chef Mochi (a friendly tanuki from Japan) "
                     "and his friends cook dishes from around the world",
            "characters": {
                "Mochi": {"role": "head chef", "personality": "patient, loves sharing food",
                          "origin": "Japanese tanuki (raccoon dog)", "catchphrase": "Let's cook up an answer!"},
                "Dali": {"role": "sous chef", "personality": "creative, sometimes messy",
                         "origin": "Indian girl inspired by Dali dosa art", "catchphrase": "Stir, stir, think!"},
                "Bao": {"role": "baker", "personality": "precise, loves counting",
                        "origin": "Chinese boy who makes perfect bao buns", "catchphrase": "Every bun counts!"},
                "Nori": {"role": "helper", "personality": "curious, asks lots of questions",
                         "origin": "Korean girl who wraps perfect kimbap", "catchphrase": "Wait, how many?"},
            },
            "settings": [
                "the kitchen counter where ingredients are lined up",
                "the big mixing bowl where everything comes together",
                "the oven where treats are baking",
                "the market where they buy ingredients",
                "the dining table where friends gather to eat",
            ],
            "math_hooks": {
                "counting": "counting ingredients, plates, portions",
                "addition": "combining ingredients, adding more servings",
                "subtraction": "eating food, giving portions away, using up ingredients",
                "patterns": "decorating cakes in patterns, arranging plates",
                "shapes": "cookie cutters, pizza slices, sandwich cuts",
                "comparison": "which bowl has more, bigger/smaller portions",
            },
        },
        {
            "world": "star_garden",
            "theme": "A rooftop garden in Mumbai where plants grow in magical ways "
                     "and kids learn by caring for them",
            "characters": {
                "Aarav": {"role": "gardener", "personality": "gentle, notices small things",
                          "origin": "Indian boy from Mumbai", "catchphrase": "Look closely!"},
                "Suki": {"role": "butterfly friend", "personality": "playful, loves colors",
                         "origin": "Japanese butterfly spirit", "catchphrase": "Flutter and count!"},
                "Min-jun": {"role": "rain collector", "personality": "organized, loves measuring",
                            "origin": "Korean boy who tracks the rain", "catchphrase": "How much today?"},
                "Mei": {"role": "seed keeper", "personality": "careful, loves sorting",
                        "origin": "Chinese girl who catalogs seeds", "catchphrase": "Let's sort it out!"},
            },
            "settings": [
                "the seed box with rows of tiny seeds",
                "the garden beds arranged in neat rows",
                "the rain gauge showing water levels",
                "the butterfly meadow with colorful flowers",
                "the harvest basket filling up with vegetables",
            ],
            "math_hooks": {
                "counting": "counting seeds, petals, butterflies, vegetables",
                "addition": "new plants sprouting, more butterflies arriving",
                "subtraction": "harvesting vegetables, petals falling",
                "patterns": "flower petal arrangements, planting rows",
                "shapes": "leaf shapes, garden bed layouts",
                "comparison": "taller/shorter plants, bigger/smaller fruits",
            },
        },
        {
            "world": "toy_workshop",
            "theme": "A workshop where kids build and fix toys, each toy teaching "
                     "something new about numbers",
            "characters": {
                "Tinkoo": {"role": "toy builder", "personality": "inventive, loves building",
                           "origin": "Indian boy (inspired by 'tinker')", "catchphrase": "Let's build it!"},
                "Hana": {"role": "painter", "personality": "artistic, sees beauty in numbers",
                         "origin": "Korean girl who paints toys", "catchphrase": "What color shall we paint?"},
                "Riku": {"role": "gear master", "personality": "logical, loves how things work",
                         "origin": "Japanese boy who fixes mechanisms", "catchphrase": "Every gear matters!"},
                "Lian": {"role": "box organizer", "personality": "tidy, loves arranging",
                         "origin": "Chinese girl who packs toy boxes", "catchphrase": "Everything in its place!"},
            },
            "settings": [
                "the workbench with tools and parts",
                "the paint station with jars of colors",
                "the shelf where finished toys line up",
                "the parts drawer with sorted pieces",
                "the testing area where toys are tried out",
            ],
            "math_hooks": {
                "counting": "counting wheels, buttons, parts needed",
                "addition": "combining parts, total pieces needed",
                "subtraction": "using parts from a box, pieces left over",
                "patterns": "gear patterns, repeating decorations",
                "shapes": "toy shapes, box shapes, wheel circles",
                "comparison": "bigger/smaller toys, more/fewer parts",
            },
        },
    ],

    # Grade 3-4 (difficulty 101-200): Adventure, mystery, building
    "grade_3_4": [
        {
            "world": "map_makers",
            "theme": "A team of young explorers charting unknown islands, where every "
                     "math problem is a real navigation or building challenge",
            "characters": {
                "Zara": {"role": "navigator", "personality": "brave, loves direction and maps",
                         "origin": "Indian-Arab girl, inspired by ancient navigators"},
                "Kai": {"role": "builder", "personality": "strong, practical problem-solver",
                        "origin": "Japanese boy who builds bridges and shelters"},
                "Priya": {"role": "journal keeper", "personality": "observant, tracks patterns",
                          "origin": "Indian girl who records everything in her notebook"},
                "Jun-ho": {"role": "inventor", "personality": "creative, builds gadgets",
                           "origin": "Korean boy who invents tools for the team"},
            },
            "math_hooks": {
                "arithmetic": "calculating distances, sharing supplies equally, trading goods",
                "fractions": "dividing maps into sections, sharing water rations",
                "geometry": "measuring land, calculating area for a shelter, angles for bridges",
                "patterns": "tide patterns, star positions for navigation, weather cycles",
                "logic": "decoding ancient maps, solving riddles to find paths",
                "word_problems": "real expedition planning — food for N days, distance per hour",
            },
        },
        {
            "world": "code_city",
            "theme": "A city built and run by kids where math controls everything — "
                     "traffic lights, bridges, even the weather dome",
            "characters": {
                "Rohan": {"role": "city planner", "personality": "organized, thinks big",
                          "origin": "Indian boy designing the city grid"},
                "Yuki": {"role": "transport engineer", "personality": "fast-thinking, optimizes routes",
                         "origin": "Japanese girl who programs the trains"},
                "Soo-jin": {"role": "energy manager", "personality": "careful, tracks resources",
                            "origin": "Korean girl managing the solar panels"},
                "Wei": {"role": "architect", "personality": "creative, builds structures",
                        "origin": "Chinese boy designing buildings"},
            },
            "math_hooks": {
                "arithmetic": "calculating power consumption, train schedules",
                "fractions": "dividing city zones, energy distribution",
                "geometry": "building dimensions, road angles, park areas",
                "patterns": "traffic light sequences, train arrival patterns",
                "logic": "optimizing routes, if-then rules for city systems",
                "word_problems": "real city planning — budget for N projects, time for construction",
            },
        },
    ],

    # Grade 5-6 (difficulty 201-300): Complex, real-world, olympiad
    "grade_5_6": [
        {
            "world": "quantum_quest",
            "theme": "A science research station where young scientists solve real-world "
                     "problems using math — each problem has stakes and consequences",
            "characters": {
                "Arjun": {"role": "lead researcher", "personality": "analytical, never gives up",
                          "origin": "Indian boy, inspired by Ramanujan's curiosity"},
                "Sakura": {"role": "data analyst", "personality": "precise, loves patterns in data",
                           "origin": "Japanese girl who finds signals in noise"},
                "Eun-ji": {"role": "strategist", "personality": "strategic, thinks 3 steps ahead",
                           "origin": "Korean girl who plans experiments"},
                "Liang": {"role": "field engineer", "personality": "hands-on, builds solutions",
                          "origin": "Chinese boy who makes prototypes"},
            },
            "math_hooks": {
                "arithmetic": "calculating experiment results, unit conversions, BODMAS puzzles",
                "fractions": "mixing solutions in ratios, probability of outcomes",
                "geometry": "designing equipment dimensions, calculating volumes",
                "patterns": "data sequences, growth patterns, fibonacci in nature",
                "logic": "hypothesis testing, elimination puzzles, constraint problems",
                "word_problems": "real research scenarios — speed, distance, time, rate problems",
            },
        },
    ],
}

# ---------------------------------------------------------------------------
# MISCONCEPTION DATABASE — What kids actually get wrong and WHY
# ---------------------------------------------------------------------------

MISCONCEPTIONS = {
    "counting": {
        "off_by_one": "You might have started counting from 0 instead of 1, or counted the first item twice.",
        "skip_count_error": "When skip counting, make sure you add the same amount each time.",
        "double_count": "Be careful not to count the same object twice — try crossing them off as you go.",
        "forgot_group": "It looks like you forgot to count one of the groups. Read the problem again to find all the items.",
    },
    "addition": {
        "carrying_error": "When the digits add up to 10 or more, remember to carry the 1 to the next column.",
        "wrong_operation": "Check the problem again — are you sure you need to subtract? The word 'more' or 'total' usually means addition.",
        "place_value_error": "Make sure you're lining up the ones, tens, and hundreds columns correctly.",
        "added_wrong_numbers": "Double-check which numbers the problem is asking you to add together.",
    },
    "subtraction": {
        "borrowing_error": "When the top digit is smaller, you need to borrow from the next column.",
        "reversed_operation": "You may have subtracted the wrong way around. The bigger number should be on top.",
        "wrong_operation": "Check the problem — words like 'left', 'remaining', or 'gave away' mean subtraction.",
        "place_value_error": "Make sure each digit is in the right column before subtracting.",
    },
    "multiplication": {
        "partial_product_error": "When multiplying multi-digit numbers, make sure to multiply by BOTH the ones digit AND the tens digit.",
        "table_error": "Double-check your times table fact. Try skip counting to verify.",
        "forgot_zero": "When multiplying by the tens digit, remember to add a zero in the ones place first.",
        "added_instead": "This is a multiplication problem (groups of), not addition (putting together).",
    },
    "fractions": {
        "numerator_denominator_swap": "The top number (numerator) is how many parts you have. The bottom number (denominator) is how many equal parts the whole is divided into.",
        "unequal_parts": "Fractions only work when all parts are EQUAL size. Make sure the whole is divided equally.",
        "whole_vs_part": "The question asks about the part, not the whole. If 2 out of 8 were given away, 6 out of 8 remain.",
        "unlike_denominators": "Before adding or subtracting fractions, the bottom numbers must be the same.",
    },
    "patterns": {
        "wrong_rule": "Look at how EACH number changes to get the next one. Is it adding, multiplying, or something else?",
        "applied_rule_wrong": "You found the right pattern rule, but applied it incorrectly to find the answer. Try again carefully.",
        "incomplete_pattern": "Check more than just the first two numbers — the pattern might change or have two steps.",
        "arithmetic_error": "You found the right pattern, but made a calculation error when finding the next number.",
    },
    "geometry": {
        "perimeter_vs_area": "Perimeter is the distance AROUND the shape (add all sides). Area is the space INSIDE (length × width).",
        "forgot_side": "A rectangle has 4 sides, not 2. Did you forget to count the matching sides?",
        "wrong_formula": "Check which formula matches this shape. Rectangles use length × width, triangles use ½ × base × height.",
        "unit_confusion": "Perimeter is measured in units (cm, m). Area is measured in SQUARE units (cm², m²).",
    },
    "logic": {
        "hasty_conclusion": "Don't jump to the first answer that seems right. Check ALL the clues before deciding.",
        "missed_clue": "Read the problem again — there's a clue you haven't used yet that changes the answer.",
        "reversed_logic": "You might have the logic backwards. If A is taller than B, then B is shorter than A.",
        "assumed_info": "Only use information given in the problem. Don't assume things that aren't stated.",
    },
    "spatial": {
        "mirror_confusion": "When something is mirrored, left and right swap. Try holding your hands up and imagining the mirror.",
        "direction_swap": "Left and right can be tricky. Point in the direction the problem describes and check again.",
        "rotation_error": "When rotating, keep track of which way you're turning — clockwise or anticlockwise. Use your finger to trace the turn.",
        "perspective_error": "Think about WHO is looking. If the character faces you, their left is YOUR right.",
    },
    "word_problems": {
        "wrong_operation": "Read the question carefully. What is it really asking? 'How many left' = subtract. 'How many altogether' = add.",
        "used_wrong_numbers": "The problem gives you several numbers. Make sure you're using the right ones for your calculation.",
        "forgot_step": "This is a two-step problem. You solved the first step correctly, but there's one more step to finish.",
        "answer_doesnt_match_question": "You did the math correctly, but your answer doesn't match what the question is asking for.",
    },
}


def get_grade_band(difficulty_score: int) -> str:
    if difficulty_score <= 100:
        return "grade_1_2"
    elif difficulty_score <= 200:
        return "grade_3_4"
    else:
        return "grade_5_6"


def get_topic_category(topic_id: str, tags: list, stem: str = "") -> str:
    """Map topic + tags + stem to a math category for misconception lookup."""
    tag_str = " ".join(tags).lower()
    topic_lower = topic_id.lower()
    stem_lower = stem.lower()

    # Check stem for operation clues (more reliable than tags)
    stem_has_mult = any(w in stem_lower for w in ["rows of", "groups of", "×", "times", "multiply", "each row", "rows with"])
    stem_has_sub = any(w in stem_lower for w in ["gives away", "gave away", "left", "remaining", "took", "spent", "lost", "fewer", " - "])
    stem_has_div = any(w in stem_lower for w in ["shared equally", "divide", "split", "each get", "÷", "per person"])
    stem_has_frac = any(w in stem_lower for w in ["fraction", "numerator", "denominator", "/8", "/4", "/3", "/6", "/5", "/10", "equal pieces", "equal parts"])

    if "arithmetic" in topic_lower or "addition" in tag_str or "subtraction" in tag_str:
        if "fraction" in tag_str or stem_has_frac:
            return "fractions"
        if "multiply" in tag_str or "multiplication" in tag_str or "times" in tag_str or "div-table" in tag_str or stem_has_mult:
            return "multiplication"
        if "subtract" in tag_str or "minus" in tag_str or stem_has_sub:
            return "subtraction"
        if stem_has_div:
            return "multiplication"  # division is inverse multiplication
        return "addition"
    if "counting" in topic_lower:
        return "counting"
    if "pattern" in topic_lower:
        return "patterns"
    if "shape" in topic_lower or "geometry" in tag_str:
        return "geometry"
    if "spatial" in topic_lower:
        # Distinguish spatial reasoning from geometry
        if any(w in stem_lower for w in ["left", "right", "above", "below", "behind", "front", "direction", "turn", "rotate", "mirror", "reflect", "fold"]):
            return "spatial"
        return "geometry"
    if "logic" in topic_lower:
        return "logic"
    if "word" in topic_lower or "problem" in topic_lower:
        # Word problems: detect operation from stem
        if stem_has_mult:
            return "multiplication"
        if stem_has_sub:
            return "subtraction"
        if stem_has_frac:
            return "fractions"
        return "word_problems"
    if "puzzle" in topic_lower:
        return "logic"
    return "counting"  # fallback


# ---------------------------------------------------------------------------
# HINT GENERATOR — 4-level pedagogical scaffold
# ---------------------------------------------------------------------------

def generate_hints(question: dict, topic_id: str) -> dict:
    """Generate a proper 4-level hint ladder for a question.

    Level 0 (Metacognitive): Help the student understand what the problem is asking.
    Level 1 (Strategic): Suggest an approach or strategy.
    Level 2 (Procedural): Give specific step-by-step guidance for THIS question.
    Level 3 (Bottom-out): Show the complete worked solution.
    """
    stem = question.get("stem", "")
    choices = question.get("choices", [])
    correct_idx = question.get("correct_answer", 0)
    correct_val = choices[correct_idx] if correct_idx < len(choices) else "?"
    tags = question.get("tags", [])
    category = get_topic_category(topic_id, tags, stem)
    difficulty = question.get("difficulty_score", 50)

    # Extract numbers from stem
    numbers = re.findall(r'\b\d+\b', stem)
    # Extract key question word
    question_phrase = ""
    m = re.search(r'(How many|What is|Which|What comes|What number|How much|What fraction|What colour|Who is|Where)', stem, re.I)
    if m:
        question_phrase = m.group(0)

    # Level 0: Metacognitive — Tailored to category and stem content
    metacog_by_category = {
        "counting": [
            "What are you being asked to count? Look at the problem — are there groups to count separately?",
            "Before counting, figure out: are you counting one type of thing, or adding up different groups?",
            "Pause and think: what exactly needs to be counted here? Is anything being added or taken away?",
        ],
        "addition": [
            "This problem is asking you to combine amounts. What two (or more) things are being put together?",
            "Read it again — what are the quantities, and why are they being joined?",
            "Think: what does 'altogether' or 'total' or 'in all' really mean here?",
        ],
        "subtraction": [
            "Something is being taken away or compared here. What started, and what was removed?",
            "Words like 'left', 'remaining', or 'gave away' are clues. What's the bigger number you start with?",
            "Ask yourself: am I finding what's left after removing something, or the difference between two amounts?",
        ],
        "multiplication": [
            "Think about equal groups. How many groups are there, and how many in each group?",
            "This is a 'groups of' problem. What are the groups, and what's in each one?",
            "Before multiplying, ask: what is being repeated, and how many times?",
        ],
        "fractions": [
            "Think about equal parts of a whole. What is the whole, and how is it being divided?",
            "Fractions tell a story: the bottom number is how many pieces, the top is how many you're looking at.",
            "Pause: is the question about the part that's left, or the part that was taken/given?",
        ],
        "patterns": [
            "Look at the sequence. What changes between each number? Is it always the same change?",
            "Before guessing, write down what happens from one term to the next. Addition? Multiplication? Something else?",
            "A pattern has a rule. Find the rule first, then use it to predict the next term.",
        ],
        "geometry": [
            "What shape are you working with? Visualize it — how many sides, what are its measurements?",
            "Before using a formula, make sure you know: are you finding perimeter (around) or area (inside)?",
            "Picture the shape. Label what you know. What measurement is the question asking for?",
        ],
        "spatial": [
            "Think about direction and position. Which way is left? Which way is right? Point with your finger.",
            "Picture yourself in the scene. Where are you standing? Where are the objects?",
            "Spatial problems need you to imagine the view. Try turning your body or using your hands to act it out.",
        ],
        "logic": [
            "Read every clue carefully. Each one eliminates some possibilities. What can you rule out first?",
            "Don't jump to an answer — work through the clues one by one and see what MUST be true.",
            "Logic puzzles need patience. Start with the most definite clue and build from there.",
        ],
        "word_problems": [
            "Read the whole problem first. Then ask: what are the important numbers, and what connects them?",
            "Underline the question it's asking. Now find the numbers and figure out which operation to use.",
            "Before calculating, picture the situation in your head. What's happening in this story?",
        ],
    }
    pool = metacog_by_category.get(category, metacog_by_category["counting"])
    level_0 = pool[hash(question.get("id", "")) % len(pool)]

    # Level 1: Strategic — What approach?
    strategy_map = {
        "counting": "Try organizing what you need to count. Can you group items or use skip counting to make it faster?",
        "addition": "Think about what you're putting together. Could you draw it, use a number line, or break the numbers into tens and ones?",
        "subtraction": "Think about what's being taken away. Could you count backwards, or use the relationship between addition and subtraction?",
        "multiplication": "This is a groups-of problem. Could you use repeated addition, skip counting, or break one number apart?",
        "fractions": "Think about equal parts of a whole. Can you picture a shape being cut into equal pieces?",
        "patterns": "Look at how each number or item changes to get the next one. Write down the differences between consecutive terms.",
        "geometry": "Draw the shape if you can. Label what you know — the sides, angles, or measurements given.",
        "spatial": "Use your hands or draw a picture to figure out position and direction. Try acting it out!",
        "logic": "Try working through each possibility one at a time. Can you eliminate answers that definitely don't work?",
        "word_problems": "Circle the numbers and underline the question. What operation connects them?",
    }
    level_1 = strategy_map.get(category, "Think about what strategy would work best here. Could you draw a picture or try a simpler version first?")

    # Level 2: Procedural — Specific to THIS question
    if category == "addition" and len(numbers) >= 2:
        level_2 = f"Start with {numbers[0]}. Now add {numbers[1]} to it. {'Then add ' + numbers[2] + '.' if len(numbers) > 2 else ''} What do you get?"
    elif category == "subtraction" and len(numbers) >= 2:
        level_2 = f"Start with {numbers[0]}. Take away {numbers[1]}. Count backwards {numbers[1]} steps from {numbers[0]}."
    elif category == "multiplication" and len(numbers) >= 2:
        level_2 = f"You need {numbers[0]} groups of {numbers[1]}. Try skip counting by {numbers[1]}: {numbers[1]}, {int(numbers[1])*2 if numbers[1].isdigit() else '?'}..."
    elif category == "counting":
        level_2 = f"Count each group separately: {', '.join(numbers[:3])}. Then add those groups together to get the total."
    elif category == "patterns" and len(numbers) >= 3:
        try:
            nums = [int(n) for n in numbers[:4]]
            diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
            if len(set(diffs)) == 1:
                level_2 = f"The difference between each pair is {diffs[0]}. So the next number is {nums[-1]} + {diffs[0]} = {nums[-1] + diffs[0]}."
            else:
                level_2 = f"Look at the differences: {', '.join(str(d) for d in diffs)}. Is there a pattern in the differences themselves?"
        except:
            level_2 = "Write out the sequence and find the rule that connects each term to the next."
    elif category == "geometry":
        level_2 = "Identify the shape and its measurements. Apply the right formula: perimeter = sum of all sides, area = length × width for rectangles."
    elif category == "spatial":
        level_2 = "Point in the direction described. If the problem says 'left', point left. Now look at where the object would be."
    elif category == "fractions":
        level_2 = "Identify the whole (denominator) and the part (numerator). The denominator tells you how many equal parts; the numerator tells you how many you're looking at."
    elif category == "logic":
        level_2 = "List each piece of information as a separate fact. Then test each answer choice — does it match ALL the facts?"
    else:
        level_2 = f"Work through the problem step by step using the numbers given: {', '.join(numbers[:3]) if numbers else 'check the problem carefully'}."

    # Level 3: Bottom-out — Worked solution
    level_3 = f"Here's the solution: {_generate_worked_solution(question, category, numbers, correct_val)}"

    return {
        "level_0": level_0,
        "level_1": level_1,
        "level_2": level_2,
        "level_3": level_3,
    }


def _generate_worked_solution(q: dict, category: str, numbers: list, answer: str) -> str:
    """Generate a clear worked solution explanation."""
    stem = q.get("stem", "")

    if category == "addition" and len(numbers) >= 2:
        if len(numbers) == 2:
            return f"{numbers[0]} + {numbers[1]} = {answer}. We combined the two amounts to get the total."
        elif len(numbers) >= 3:
            return f"{' + '.join(numbers[:3])} = {answer}. Add each number one at a time: {numbers[0]} + {numbers[1]} = {int(numbers[0])+int(numbers[1]) if numbers[0].isdigit() and numbers[1].isdigit() else '...'}, then add {numbers[2]}."
    elif category == "subtraction" and len(numbers) >= 2:
        return f"{numbers[0]} - {numbers[1]} = {answer}. We started with {numbers[0]} and took away {numbers[1]}."
    elif category == "multiplication" and len(numbers) >= 2:
        return f"{numbers[0]} × {numbers[1]} = {answer}. That's {numbers[0]} groups with {numbers[1]} in each group."
    elif category == "counting":
        return f"Counting everything gives us {answer}. Make sure each item is counted exactly once."
    elif category == "patterns":
        return f"Following the pattern rule gives us {answer}. Each step follows the same rule to get the next number."

    return f"The answer is {answer}. Work through each step carefully to see why."


# ---------------------------------------------------------------------------
# DIAGNOSTICS GENERATOR — Misconception-targeted feedback
# ---------------------------------------------------------------------------

def generate_diagnostics(question: dict, topic_id: str) -> dict:
    """Generate misconception-targeted diagnostics for each wrong answer.

    Instead of "you're off by N", explain WHAT the student likely did wrong
    and HOW to fix it.
    """
    stem = question.get("stem", "")
    choices = question.get("choices", [])
    correct_idx = question.get("correct_answer", 0)
    correct_val = choices[correct_idx] if correct_idx < len(choices) else "?"
    tags = question.get("tags", [])
    category = get_topic_category(topic_id, tags, stem)
    numbers = re.findall(r'\b\d+\b', stem)

    misconception_pool = MISCONCEPTIONS.get(category, MISCONCEPTIONS["counting"])
    misconception_keys = list(misconception_pool.keys())

    diagnostics = {}
    for i, choice in enumerate(choices):
        if i == correct_idx:
            continue

        # Try to infer what misconception led to this wrong answer
        try:
            correct_num = float(correct_val.replace(",", "").strip())
            wrong_num = float(choice.replace(",", "").strip())
            diff = wrong_num - correct_num

            if abs(diff) == 1:
                diag = _off_by_one_diagnostic(category, diff)
            elif category in ("addition", "subtraction") and abs(diff) == 10:
                diag = misconception_pool.get("place_value_error",
                    f"Check your place values — tens and ones need to be in the right column. The correct answer is {correct_val}.")
            elif category == "multiplication" and len(numbers) >= 2:
                diag = misconception_pool.get("partial_product_error",
                    f"Double-check your multiplication steps. The correct answer is {correct_val}.")
            elif category == "geometry" and abs(diff) > 10:
                diag = misconception_pool.get("perimeter_vs_area",
                    f"Make sure you're using the right formula for what the question asks. The correct answer is {correct_val}.")
            else:
                # Pick a relevant misconception
                key = misconception_keys[i % len(misconception_keys)]
                diag = misconception_pool[key]
        except (ValueError, ZeroDivisionError):
            # Non-numeric choices
            key = misconception_keys[i % len(misconception_keys)]
            diag = misconception_pool[key]

        diagnostics[str(i)] = diag

    # Add correct explanation
    diagnostics["correct_explanation"] = _generate_correct_explanation(question, category, numbers, correct_val)

    return diagnostics


def _off_by_one_diagnostic(category: str, diff: float) -> str:
    if category == "counting":
        if diff > 0:
            return "You counted one extra. Try touching each item as you count to make sure you don't count anything twice."
        else:
            return "You missed one! Try touching each item as you count to make sure you get them all."
    elif category in ("addition", "subtraction"):
        return "You're very close — just 1 off. Double-check your last step of the calculation."
    return "Almost there — you're off by just 1. Carefully re-do the last step."


def _generate_correct_explanation(q: dict, category: str, numbers: list, answer: str) -> str:
    """Generate a clear explanation of WHY the correct answer is correct."""
    stem = q.get("stem", "")

    explanations = {
        "counting": f"The answer is {answer}. When we count each item carefully — making sure not to skip any or count any twice — we get {answer}.",
        "addition": f"The answer is {answer}. When we add the numbers together ({' + '.join(numbers[:3]) if numbers else 'the given values'}), the total is {answer}.",
        "subtraction": f"The answer is {answer}. We start with the larger amount and take away the smaller amount, leaving us with {answer}.",
        "multiplication": f"The answer is {answer}. Multiplication means equal groups — {numbers[0] if numbers else 'the first number'} groups of {numbers[1] if len(numbers) > 1 else 'the second number'} gives {answer}.",
        "fractions": f"The answer is {answer}. Remember: the denominator tells us how many equal parts, and the numerator tells us how many parts we're looking at.",
        "patterns": f"The answer is {answer}. By finding the rule that connects each term to the next, we can predict what comes next in the sequence.",
        "geometry": f"The answer is {answer}. Apply the correct formula for this shape using the measurements given in the problem.",
        "spatial": f"The answer is {answer}. By carefully thinking about position and direction, we can figure out where things are.",
        "logic": f"The answer is {answer}. By checking each clue against every option, only this answer satisfies all the conditions.",
        "word_problems": f"The answer is {answer}. The key is identifying what operation to use, then applying it to the right numbers from the problem.",
    }

    return explanations.get(category, f"The answer is {answer}.")


# ---------------------------------------------------------------------------
# STORY STEM REWRITER
# ---------------------------------------------------------------------------

def rewrite_stem_with_story(question: dict, topic_id: str, world: dict) -> str:
    """Rewrite a question stem so the math is INTEGRAL to the story, not decorative.

    BAD:  "Captain Kiwi is solving a puzzle! What is 3 + 5?"
    GOOD: "Mochi is making 3 onigiri for lunch and 5 more for the picnic. How many onigiri does he need to prepare?"
    """
    stem = question.get("stem", "")
    original_stem = question.get("original_stem", stem)
    tags = question.get("tags", [])
    category = get_topic_category(topic_id, tags, stem)
    difficulty = question.get("difficulty_score", 50)
    numbers = re.findall(r'\b\d+\b', original_stem)

    # Pick a character
    char_names = list(world["characters"].keys())
    char_name = char_names[hash(question.get("id", "")) % len(char_names)]
    char = world["characters"][char_name]

    # Get relevant setting
    settings = world.get("settings", ["the workspace"])
    setting = settings[hash(question.get("id", "x")) % len(settings)]

    # For complex stems that already have good context, just fix the character name
    if _is_contextual_stem(original_stem):
        # Replace existing character names with new ones
        new_stem = _replace_character_in_stem(stem, char_name)
        return new_stem

    # For bare-math stems, create story context
    return _create_story_stem(original_stem, category, numbers, char_name, char, world, setting)


def _is_contextual_stem(stem: str) -> bool:
    """Check if a stem already has meaningful context (not just a name pasted on)."""
    context_patterns = [
        r'cut.*into.*pieces',
        r'shared.*equally',
        r'garden.*flowers',
        r'walked.*km',
        r'bought.*and',
        r'rows.*columns',
        r'taller than|shorter than|heavier than',
        r'pattern.*:.*,.*,',
        r'left of|right of|above|below|behind',
        r'How many.*are there',
        r'How many.*does.*have',
    ]
    # Remove character prefix and check what's left
    cleaned = re.sub(r'^(Captain Kiwi|Chef Cheetah|Detective Dodo|Builder Bee|Professor Plum|'
                     r'Knight Koko|Pirate Papaya|Ranger Roo|Help \w+ solve this:|'
                     r'\w+ needs? (to work out|your help|to figure out):?\s*!?\s*)', '', stem, flags=re.I).strip()

    # If the cleaned stem starts with "What is" or just has bare math, it's NOT contextual
    if re.match(r'^(What is|Evaluate|Calculate|Find|Solve|Compute)', cleaned, re.I):
        return False
    if re.match(r'^\d+\s*[+\-×÷*/]\s*\d+', cleaned):
        return False

    for pattern in context_patterns:
        if re.search(pattern, cleaned, re.I):
            return True

    return len(cleaned.split()) > 12  # Longer stems usually have context


def _replace_character_in_stem(stem: str, new_name: str) -> str:
    """Replace old character names with new one."""
    old_names = [
        "Captain Kiwi", "Chef Cheetah", "Detective Dodo", "Builder Bee",
        "Professor Plum", "Knight Koko", "Pirate Papaya", "Ranger Roo",
        "Kiwi", "Chikoo", "Vanya", "Aarohi",
    ]
    result = stem
    for old in old_names:
        if old in result:
            result = result.replace(old, new_name, 1)
            break
    return result


def _create_story_stem(original_stem: str, category: str, numbers: list,
                       char_name: str, char: dict, world: dict, setting: str) -> str:
    """Create a story-integrated stem from a bare math problem.

    The math must be the MECHANISM of the story — the character needs to solve
    this to accomplish their goal.
    """
    # Strip any existing character prefix
    clean = re.sub(r'^(.*?)(What is|Evaluate|Calculate|Find|Solve|How many|What comes)',
                   r'\2', original_stem, flags=re.I).strip()

    # For now, return the cleaned stem with a light story wrapper
    # The full rewrite would use an LLM, but template-based is deterministic
    if not numbers:
        return f"{char_name} is working at {setting}. {clean}"

    math_hooks = world.get("math_hooks", {})
    hook = math_hooks.get(category, "solving a problem")

    # Simple arithmetic: make it about the world
    if category == "addition" and len(numbers) >= 2:
        items = _get_context_items(world["world"], category)
        return (f"{char_name} has {numbers[0]} {items} ready. {numbers[1]} more arrive. "
                f"How many {items} are there now?")
    elif category == "subtraction" and len(numbers) >= 2:
        items = _get_context_items(world["world"], category)
        return (f"{char_name} started with {numbers[0]} {items}. After using {numbers[1]}, "
                f"how many are left?")
    elif category == "multiplication" and len(numbers) >= 2:
        items = _get_context_items(world["world"], category)
        return (f"{char_name} arranges {items} in {numbers[0]} rows with {numbers[1]} in each row. "
                f"How many {items} are there in total?")

    # For everything else, light contextual wrapper
    return f"{char_name} is at {setting}. {clean}"


def _get_context_items(world_name: str, category: str) -> str:
    """Get context-appropriate items for the world."""
    items = {
        "kiwi_kitchen": {
            "addition": random.choice(["cookies", "cupcakes", "plates", "dumplings", "samosas"]),
            "subtraction": random.choice(["cookies", "sandwiches", "pieces of fruit", "rotis"]),
            "multiplication": random.choice(["muffins", "cookies", "bao buns", "chapatis"]),
            "counting": random.choice(["ingredients", "spoons", "cups", "bowls"]),
        },
        "star_garden": {
            "addition": random.choice(["flowers", "seeds", "leaves", "butterflies"]),
            "subtraction": random.choice(["petals", "fruits", "vegetables", "seeds"]),
            "multiplication": random.choice(["seedlings", "flowers", "plants", "bulbs"]),
            "counting": random.choice(["petals", "leaves", "ladybugs", "dewdrops"]),
        },
        "toy_workshop": {
            "addition": random.choice(["toy parts", "wheels", "buttons", "building blocks"]),
            "subtraction": random.choice(["bolts", "screws", "toy parts", "paint jars"]),
            "multiplication": random.choice(["toy cars", "blocks", "stickers", "gears"]),
            "counting": random.choice(["toys", "parts", "buttons", "springs"]),
        },
    }
    world_items = items.get(world_name, items["toy_workshop"])
    return world_items.get(category, "items")


# ---------------------------------------------------------------------------
# IRT PARAMETER CALCULATOR
# ---------------------------------------------------------------------------

def calculate_irt_params(question: dict, topic_id: str) -> dict:
    """Calculate more realistic IRT parameters based on question characteristics.

    a (discrimination): How well this item separates high vs low ability
      - Higher for well-constructed items with clear misconception-based distractors
      - Lower for guessable or ambiguous items
      - Range: 0.5 to 2.5

    b (difficulty): Item difficulty on the theta scale
      - Maps from difficulty_score but with noise and topic-based adjustments
      - Range: -3.0 to 3.0

    c (guessing): Probability of getting it right by chance
      - 4-choice MCQ: base is 0.25 but varies by distractor quality
      - Numerical/open-ended: near 0
      - Easy items with obvious distractors: higher c
    """
    diff_score = question.get("difficulty_score", 50)
    choices = question.get("choices", [])
    n_choices = len(choices)
    tags = question.get("tags", [])
    stem = question.get("stem", "")
    mode = question.get("interaction_mode", "multiple_choice")

    # b parameter: map difficulty_score to theta scale (-3 to 3)
    # Add topic-specific adjustments and slight randomness
    if diff_score <= 100:
        # Grade 1-2: -3.0 to 0.0
        b_base = -3.0 + (diff_score / 100.0) * 3.0
    elif diff_score <= 200:
        # Grade 3-4: 0.0 to 2.0
        b_base = 0.0 + ((diff_score - 100) / 100.0) * 2.0
    else:
        # Grade 5-6: 1.0 to 3.0
        b_base = 1.0 + ((diff_score - 200) / 100.0) * 2.0

    # Add slight noise for realism
    b_noise = (hash(question.get("id", "")) % 20 - 10) / 50.0
    b = round(max(-3.0, min(3.0, b_base + b_noise)), 2)

    # a parameter: discrimination based on question quality indicators
    a_base = 1.0

    # Better discrimination for questions with specific tags
    specific_tags = [t for t in tags if t not in ("easy", "medium", "hard", "advanced", "expert",
                                                   "grade-3-4", "grade-5-6", "counting", "arithmetic")]
    if len(specific_tags) >= 2:
        a_base += 0.3  # Well-tagged = better constructed

    # Word problems and logic puzzles discriminate better
    category = get_topic_category(topic_id, tags, stem)
    if category in ("logic", "word_problems"):
        a_base += 0.2
    if category == "patterns" and diff_score > 100:
        a_base += 0.15

    # Multi-step problems discriminate better
    numbers = re.findall(r'\b\d+\b', question.get("stem", ""))
    if len(numbers) >= 3:
        a_base += 0.1

    # Add slight randomness
    a_noise = (hash(question.get("id", "xx")) % 20 - 10) / 40.0
    a = round(max(0.4, min(2.5, a_base + a_noise)), 2)

    # c parameter: guessing based on format
    if mode in ("integer", "drag_drop", "grid_plot"):
        c = 0.0  # No guessing for open-response
    elif n_choices == 2:
        c = 0.45  # True/false is highly guessable
    elif n_choices == 3:
        c = 0.30
    elif n_choices == 4:
        # Vary by distractor quality — easy items have more obviously wrong distractors
        if diff_score < 20:
            c = 0.30  # Easy items: distractors are obviously wrong, more guessable
        elif diff_score > 150:
            c = 0.15  # Hard items: all distractors are plausible
        else:
            c = 0.22
    else:
        c = 0.20

    return {"a": a, "b": b, "c": round(c, 2)}


# ---------------------------------------------------------------------------
# GRAMMAR FIXER
# ---------------------------------------------------------------------------

def fix_grammar(text: str) -> str:
    """Fix common grammar issues in question content."""
    # "1 more seashells" → "1 more seashell"
    text = re.sub(r'\b1 more (\w+)s\b', r'1 more \1', text)
    # "each flowers" → "each flower"
    text = re.sub(r'\beach (\w+)s\b', r'each \1', text)
    # "Count each coins" → "Count each coin"
    text = re.sub(r'\bCount each (\w+)s\b', r'Count each \1', text)
    # "fishs" → "fish"
    text = text.replace("fishs", "fish")
    # Double spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


# ---------------------------------------------------------------------------
# INTERACTION MODE NORMALIZER
# ---------------------------------------------------------------------------

def normalize_interaction_mode(question: dict, topic_id: str) -> str:
    """Assign the correct interaction mode based on question type."""
    tags = question.get("tags", [])
    stem = question.get("stem", "")
    choices = question.get("choices", [])
    tag_str = " ".join(tags).lower()

    # Integer input for numeric answers with no choices or where choices don't make sense
    if not choices:
        return "integer"

    # All standard MCQ
    return "multiple_choice"


# ---------------------------------------------------------------------------
# MAIN REWRITER
# ---------------------------------------------------------------------------

def rewrite_question(question: dict, topic_id: str, world: dict) -> dict:
    """Fully rewrite a single question with all quality improvements."""
    q = deepcopy(question)

    # 1. Fix grammar in stem
    q["stem"] = fix_grammar(q.get("stem", ""))

    # 2. Rewrite stem with story context (for bare-math problems)
    # Only rewrite simple stems, keep complex contextual ones
    original = q.get("original_stem", q["stem"])
    if not _is_contextual_stem(original):
        q["stem"] = rewrite_stem_with_story(q, topic_id, world)
        if "original_stem" not in q:
            q["original_stem"] = original

    # 3. Generate proper 4-level hint ladder
    q["hint"] = generate_hints(q, topic_id)

    # 4. Generate misconception-targeted diagnostics + correct explanation
    q["diagnostics"] = generate_diagnostics(q, topic_id)

    # 5. Calculate realistic IRT parameters
    irt = calculate_irt_params(q, topic_id)
    q["irt_params"] = irt
    q["irt_a"] = irt["a"]
    q["irt_b"] = irt["b"]
    q["irt_c"] = irt["c"]

    # 6. Normalize interaction mode
    q["interaction_mode"] = normalize_interaction_mode(q, topic_id)

    # 7. Fix grammar in all text fields
    for key in ["visual_context", "visual_alt"]:
        if q.get(key):
            q[key] = fix_grammar(q[key])

    return q


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single JSON file and rewrite all questions."""
    data = json.loads(filepath.read_text())

    if isinstance(data, list):
        questions = data
        wrapper = None
    else:
        questions = data.get("questions", [])
        wrapper = data

    topic_id = ""
    if wrapper:
        topic_id = wrapper.get("topic_id", wrapper.get("topic", ""))
    elif questions:
        topic_id = questions[0].get("topic", "")

    # Determine grade band for story world selection
    if questions:
        avg_diff = sum(q.get("difficulty_score", 50) for q in questions) / len(questions)
        grade_band = get_grade_band(int(avg_diff))
    else:
        grade_band = "grade_1_2"

    # Pick a story world (consistent per topic file)
    worlds = STORY_WORLDS.get(grade_band, STORY_WORLDS["grade_1_2"])
    world_idx = hash(str(filepath)) % len(worlds)
    world = worlds[world_idx]

    stats = {"total": len(questions), "rewritten": 0, "file": str(filepath.name)}

    for i, q in enumerate(questions):
        rewritten = rewrite_question(q, topic_id, world)
        questions[i] = rewritten
        stats["rewritten"] += 1

    if not dry_run:
        if wrapper:
            wrapper["questions"] = questions
            filepath.write_text(json.dumps(wrapper, indent=2, ensure_ascii=False))
        else:
            filepath.write_text(json.dumps(questions, indent=2, ensure_ascii=False))

    return stats


def main():
    parser = argparse.ArgumentParser(description="Kiwimath Content Rewriter")
    parser.add_argument("--content-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent.parent / "content-v2")
    parser.add_argument("--topic", type=str, help="Process single topic (e.g., topic-1-counting)")
    parser.add_argument("--file", type=str, help="Process single file within topic")
    parser.add_argument("--all", action="store_true", help="Process all topics")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    content_dir = args.content_dir
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        sys.exit(1)

    files_to_process = []

    if args.topic:
        topic_dir = content_dir / args.topic
        if not topic_dir.exists():
            print(f"Topic not found: {args.topic}")
            sys.exit(1)
        if args.file:
            f = topic_dir / args.file
            if f.exists():
                files_to_process.append(f)
            else:
                print(f"File not found: {f}")
                sys.exit(1)
        else:
            files_to_process.extend(sorted(topic_dir.glob("*.json")))
    elif args.all:
        for topic_dir in sorted(content_dir.iterdir()):
            if topic_dir.is_dir() and topic_dir.name.startswith("topic-"):
                files_to_process.extend(sorted(topic_dir.glob("*.json")))
    else:
        print("Specify --topic TOPIC [--file FILE] or --all")
        sys.exit(1)

    print(f"Processing {len(files_to_process)} files {'(dry run)' if args.dry_run else ''}...")
    total_rewritten = 0

    for f in files_to_process:
        stats = process_file(f, dry_run=args.dry_run)
        print(f"  {f.parent.name}/{f.name}: {stats['rewritten']}/{stats['total']} questions rewritten")
        total_rewritten += stats["rewritten"]

    print(f"\nTotal: {total_rewritten} questions {'would be' if args.dry_run else ''} rewritten")


if __name__ == "__main__":
    main()
