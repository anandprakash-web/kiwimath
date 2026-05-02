"""
IGCSE Content Quality Fix Script
Addresses 5 critical issues in order of criticality:
1. Giveaway hints → micro-step scaffolding
2. Generic diagnostics → error-specific feedback
3. Visual context strings for geometry/measurement
4. Stem variety (reduce repetition)
"""

import json
import re
import random
import os
import copy

random.seed(42)

BASE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# 1. HINT REPAIR: Replace giveaway hints with micro-step scaffolding
# ─────────────────────────────────────────────────────────────────────────────

def is_giveaway_hint(hint_text):
    """Detect hints that just state the answer."""
    lower = hint_text.lower()
    patterns = [
        'the correct answer is',
        'the answer is',
        'correct answer:',
        'answer =',
    ]
    return any(p in lower for p in patterns)


def build_micro_step_hint(q):
    """Generate a pedagogically sound level_2 hint based on question content."""
    stem = q['stem']
    tags = q.get('tags', [])
    chapter = q.get('chapter', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer', 0)
    correct_val = choices[correct_idx] if choices and correct_idx < len(choices) else str(q.get('correct_value', ''))
    
    # Detect question type from stem and tags
    stem_lower = stem.lower()
    
    # Addition
    if re.search(r'[\+]|what is \d+\s*\+\s*\d+|sum of|add', stem_lower):
        nums = re.findall(r'-?\d+', stem)
        if len(nums) >= 2:
            return f"Add the numbers column by column, starting from the ones place. Check: does {nums[0]} + {nums[1]} give you a number close to your answer?"
        return "Line up the numbers by place value and add column by column, carrying over when needed."
    
    # Subtraction
    if re.search(r'[\-]|what is \d+\s*-\s*\d+|difference|subtract|minus', stem_lower) and 'negative' not in stem_lower:
        nums = re.findall(r'-?\d+', stem)
        if len(nums) >= 2:
            return f"Subtract step by step. Start with {nums[0]}, then take away {nums[1]}. Borrow from the next column if needed."
        return "Work from right to left, borrowing from the next column when the top digit is smaller."
    
    # Multiplication
    if re.search(r'[×]|what is \d+\s*[×x\*]\s*\d+|multiply|product|times', stem_lower):
        nums = re.findall(r'\d+', stem)
        if len(nums) >= 2:
            return f"Break it down: multiply {nums[0]} by each digit of {nums[1]} separately, then add the partial products."
        return "Use the standard algorithm: multiply by ones digit first, then tens digit, then add."
    
    # Division
    if re.search(r'[÷]|what is \d+\s*÷\s*\d+|divide|quotient', stem_lower):
        nums = re.findall(r'\d+', stem)
        if len(nums) >= 2:
            return f"Ask yourself: how many groups of {nums[1]} fit into {nums[0]}? Use your multiplication tables to check."
        return "Think: what number times the divisor gives you the dividend? Use multiplication facts to find it."
    
    # Integers / negative numbers
    if re.search(r'-\d+|negative|integer', stem_lower) or 'integers' in str(tags):
        return "Use a number line: positive numbers go right, negative go left. Adding a positive means move right; adding a negative means move left."
    
    # Perimeter
    if 'perimeter' in stem_lower:
        return "Perimeter = sum of ALL sides. For a rectangle: add length + width, then double it (multiply by 2)."
    
    # Area
    if 'area' in stem_lower:
        if 'triangle' in stem_lower:
            return "Area of triangle = ½ × base × height. First multiply base × height, then divide by 2."
        if 'circle' in stem_lower:
            return "Area of circle = π × r². First find the radius, square it, then multiply by π (≈ 3.14)."
        return "Area of rectangle = length × width. Multiply the two dimensions given to find the space inside."
    
    # Volume
    if 'volume' in stem_lower:
        return "Volume = length × width × height. Multiply all three dimensions step by step."
    
    # Fractions
    if re.search(r'fraction|simplif|numerator|denominator|½|⅓|¼', stem_lower) or 'fractions' in str(tags):
        return "Find the highest number that divides both the numerator and denominator evenly (the HCF), then divide both by it."
    
    # Angles
    if re.search(r'angle|degree|°|triangle.*sum', stem_lower):
        return "Remember: angles in a triangle add to 180°, angles on a straight line add to 180°, angles in a quadrilateral add to 360°."
    
    # Time
    if re.search(r'time|hour|minute|clock|:.*\d{2}', stem_lower):
        return "Count the hours first, then the minutes. Remember: 60 minutes = 1 hour. If minutes go past 60, add 1 to the hour."
    
    # Place value
    if re.search(r'tens place|hundreds place|ones place|digit in the', stem_lower):
        return "Count positions from the right: 1st = ones, 2nd = tens, 3rd = hundreds, 4th = thousands. Identify which position is asked."
    
    # Money / change
    if re.search(r'change|cost|pay|price|₹|\$|buy', stem_lower):
        return "Change = Amount paid − Cost. Subtract the price from what was given to find how much comes back."
    
    # Comparison / ordering
    if re.search(r'greatest|smallest|ascending|descending|order|compare|which.*most|which.*least', stem_lower):
        return "Compare the numbers digit by digit starting from the leftmost. The number with a larger digit in the highest place value is greater."
    
    # Counting / sequence
    if re.search(r'comes after|comes before|next number|what number|count', stem_lower):
        return "Look at the pattern: is it counting by 1s, 2s, 5s, or 10s? Apply that same step to find the next number."
    
    # Data handling / statistics
    if re.search(r'tally|survey|bar chart|pie chart|mean|average|total.*data', stem_lower) or 'data_handling' in str(tags):
        return "Read each value from the data carefully, then apply the operation asked (add for total, compare for most/least, divide for average)."
    
    # Conversion (units)
    if re.search(r'convert|cm to m|m to cm|kg to g|g to kg|l to ml|ml to l', stem_lower):
        return "Remember the conversion factor: 1 m = 100 cm, 1 kg = 1000 g, 1 L = 1000 mL. Multiply or divide accordingly."
    
    # Pattern / sequence
    if re.search(r'pattern|sequence|next term|rule', stem_lower):
        return "Find the rule: what operation takes you from one term to the next? Apply that rule one more time."

    # Ratio / proportion
    if re.search(r'ratio|proportion|share|divide.*equal', stem_lower):
        return "Add the ratio parts to find the total shares, then divide the quantity by total shares to find one share's value."
    
    # Percentage
    if re.search(r'percent|%', stem_lower):
        return "To find a percentage: divide by 100, then multiply by the percentage value. Or find 10% first and scale up."
    
    # Equations
    if re.search(r'solve|find x|equation|value of', stem_lower):
        return "Isolate the unknown by doing the inverse operation on both sides. Check your answer by substituting back."

    # Default — still better than giving the answer
    return "Work through the problem step by step. Write down what you know, identify the operation needed, then calculate carefully."


# ─────────────────────────────────────────────────────────────────────────────
# 2. DIAGNOSTIC REPAIR: Replace generic diagnostics with error-specific ones
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_PATTERNS = [
    'check your', 're-read the', 'make sure you', 'identify all given',
    'think about the method', 'check your working'
]

def is_generic_diagnostic(diag_text):
    lower = diag_text.lower()
    return any(p in lower for p in GENERIC_PATTERNS)


def build_specific_diagnostics(q):
    """Generate error-specific diagnostics based on question structure."""
    stem = q['stem']
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer', 0)
    if not choices:
        return q.get('diagnostics', {})
    
    correct_val = choices[correct_idx] if correct_idx < len(choices) else ''
    stem_lower = stem.lower()
    diagnostics = {}
    
    for i, choice in enumerate(choices):
        if i == correct_idx:
            continue
        
        # Try to detect what error the distractor represents
        diag = _infer_distractor_error(stem, correct_val, choice, i, stem_lower, q)
        diagnostics[str(i)] = diag
    
    return diagnostics


def _infer_distractor_error(stem, correct_val, wrong_val, idx, stem_lower, q):
    """Infer what mistake leads to a particular wrong answer."""
    
    # Try numeric comparison
    try:
        correct_num = float(re.sub(r'[^\d.\-]', '', correct_val))
        wrong_num = float(re.sub(r'[^\d.\-]', '', wrong_val))
        diff = wrong_num - correct_num
        
        # Off by one
        if abs(diff) == 1:
            return "You're off by one. Double-check your counting — did you include or exclude the starting number?"
        
        # Double / half error
        if abs(wrong_num) == abs(correct_num) * 2:
            return "Your answer is double what it should be. Check whether you multiplied when you should have just added, or counted something twice."
        if abs(wrong_num) * 2 == abs(correct_num):
            return "Your answer is half of the correct value. Did you forget to double (e.g., for perimeter) or multiply by 2?"
        
        # Sign error
        if wrong_num == -correct_num:
            return "Check the sign of your answer. Remember the rules: positive + positive = positive, negative + negative = negative."
        
        # Added instead of multiplied
        nums_in_stem = re.findall(r'\d+', stem)
        if len(nums_in_stem) >= 2:
            a, b = int(nums_in_stem[0]), int(nums_in_stem[1])
            if wrong_num == a + b and correct_num == a * b:
                return "It looks like you added the numbers instead of multiplying them. Re-read the question — which operation is asked?"
            if wrong_num == a * b and correct_num == a + b:
                return "It looks like you multiplied instead of adding. Check what operation the question is asking for."
            if wrong_num == a - b and correct_num == a + b:
                return "You subtracted instead of adding. Check the operation sign in the question."
    except (ValueError, ZeroDivisionError):
        pass
    
    # Place value error
    if 'place' in stem_lower or 'digit' in stem_lower:
        return "You may have counted from the wrong end. Remember: ones place is rightmost, then tens, hundreds, thousands moving left."
    
    # Perimeter vs area confusion
    if 'perimeter' in stem_lower or 'area' in stem_lower:
        return "Make sure you're using the right formula. Perimeter adds all sides; Area multiplies length × width."
    
    # Time errors
    if re.search(r'time|hour|minute', stem_lower):
        return "Check your time calculation. Remember there are 60 minutes in an hour — did you carry over correctly?"
    
    # Fraction errors
    if re.search(r'fraction|simplif', stem_lower):
        return "Check your fraction work. Did you apply the operation to both numerator and denominator correctly?"
    
    # Unit conversion
    if re.search(r'convert|cm|kg|ml|litre', stem_lower):
        return "Check the conversion factor. Did you multiply when you should divide, or vice versa? (e.g., cm→m means ÷100)"
    
    # Data reading
    if re.search(r'tally|chart|survey|data', stem_lower):
        return "Re-read the data values carefully. Make sure you picked the right item from the list or chart."
    
    # Generic but still better than "check your working"
    topic_hints = {
        'counting': "Count again carefully from the starting number. Use your fingers or draw marks if it helps.",
        'arithmetic': "Redo the calculation step by step. Line up place values and check each column.",
        'geometry': "Draw a quick sketch and label the measurements. Then apply the formula.",
        'fractions': "Check: did you find a common denominator? Did you simplify at the end?",
        'data_handling': "Look at the data again. Make sure you read the correct row/column.",
    }
    
    for tag_key, hint in topic_hints.items():
        if tag_key in str(q.get('tags', [])):
            return hint
    
    return "Trace through your work step by step. The mistake is likely in one specific calculation — find which step went wrong."


# ─────────────────────────────────────────────────────────────────────────────
# 3. VISUAL CONTEXT: Add descriptive text for geometry/measurement questions
# ─────────────────────────────────────────────────────────────────────────────

def needs_visual_context(q):
    """Determine if a question should have visual_context."""
    tags = str(q.get('tags', []))
    stem_lower = q['stem'].lower()
    keywords = ['rectangle', 'triangle', 'circle', 'square', 'perimeter', 'area',
                'volume', 'angle', 'shape', 'line', 'symmetry', 'cube', 'prism',
                'cylinder', 'polygon', 'parallel', 'perpendicular', 'bar chart',
                'pie chart', 'tally', 'graph', 'diagram', 'number line']
    return any(k in stem_lower or k in tags for k in keywords)


def generate_visual_context(q):
    """Generate a description of what visual should accompany this question."""
    stem = q['stem']
    stem_lower = stem.lower()
    
    # Rectangle/square
    if 'rectangle' in stem_lower:
        nums = re.findall(r'\d+', stem)
        if len(nums) >= 2:
            return f"A rectangle with length {nums[0]} cm and width {nums[1]} cm, with dimensions labeled on sides."
        return "A rectangle with labeled dimensions on two adjacent sides."
    
    if 'square' in stem_lower and ('area' in stem_lower or 'perimeter' in stem_lower):
        nums = re.findall(r'\d+', stem)
        if nums:
            return f"A square with side length {nums[0]} cm labeled."
        return "A square with one side length labeled."
    
    # Triangle
    if 'triangle' in stem_lower:
        if 'area' in stem_lower:
            return "A triangle with base and height labeled, height shown as a dashed perpendicular line from vertex to base."
        if 'angle' in stem_lower:
            nums = re.findall(r'\d+', stem)
            labeled = ', '.join(f'{n}°' for n in nums[:2]) if nums else 'known angles'
            return f"A triangle with angles labeled ({labeled}), one angle marked with '?'."
        return "A triangle with relevant measurements labeled."
    
    # Circle
    if 'circle' in stem_lower:
        if 'area' in stem_lower or 'circumference' in stem_lower:
            nums = re.findall(r'\d+', stem)
            if nums:
                return f"A circle with radius {nums[0]} cm drawn and labeled from center to edge."
            return "A circle with radius labeled from center to circumference."
        return "A circle with radius or diameter labeled."
    
    # Volume / 3D shapes
    if 'volume' in stem_lower or 'cube' in stem_lower or 'prism' in stem_lower or 'cylinder' in stem_lower:
        nums = re.findall(r'\d+', stem)
        if 'cube' in stem_lower:
            return f"A 3D cube with edge length labeled."
        if 'cylinder' in stem_lower:
            return f"A 3D cylinder with radius and height labeled."
        return f"A 3D rectangular prism (cuboid) with length, width, and height labeled on edges."
    
    # Angles
    if 'angle' in stem_lower and 'triangle' not in stem_lower:
        return "Two lines meeting at a point, with the angle between them marked with an arc and measurement."
    
    # Bar chart / data
    if re.search(r'bar chart|bar graph', stem_lower):
        return "A colorful bar chart with labeled axes and bars of different heights representing the data values."
    
    if 'pie chart' in stem_lower:
        return "A pie chart divided into colored sectors with labels showing category names and values/percentages."
    
    if 'tally' in stem_lower:
        return "A tally chart showing groups of five (crossed lines) for each category listed."
    
    # Number line
    if 'number line' in stem_lower:
        return "A horizontal number line with evenly spaced marks, relevant numbers labeled, and an arrow or dot at the answer position."
    
    # Symmetry
    if 'symmetry' in stem_lower or 'symmetrical' in stem_lower:
        return "A shape with a dashed line of symmetry drawn through it, showing the mirror relationship."
    
    # Generic geometry
    if any(k in stem_lower for k in ['perimeter', 'area', 'shape']):
        return "A labeled geometric shape with all relevant measurements shown."
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. STEM VARIETY: Rephrase repetitive "Calculate: X op X = ?" stems
# ─────────────────────────────────────────────────────────────────────────────

WORD_PROBLEM_TEMPLATES = {
    'addition': [
        "A farmer has {a} apples and picks {b} more. How many apples does the farmer have now?",
        "There are {a} students in Class A and {b} students in Class B. How many students are there in total?",
        "A train travels {a} km on Monday and {b} km on Tuesday. What is the total distance?",
        "A library has {a} fiction books and {b} non-fiction books. How many books are there altogether?",
        "{a} birds are sitting on a tree. {b} more birds join them. How many birds are on the tree now?",
        "A shop sold {a} items in the morning and {b} items in the afternoon. What is the total sold?",
    ],
    'subtraction': [
        "A baker made {a} cakes and sold {b}. How many cakes are left?",
        "There are {a} students in a class. {b} are absent today. How many are present?",
        "A bottle has {a} mL of water. If {b} mL is poured out, how much remains?",
        "A bus has {a} passengers. At the next stop, {b} get off. How many are still on the bus?",
        "{a} stickers were in a collection. {b} were given away. How many stickers remain?",
        "A rope is {a} cm long. If {b} cm is cut off, what length remains?",
    ],
    'multiplication': [
        "There are {a} boxes, each containing {b} pencils. How many pencils are there in total?",
        "A garden has {a} rows of plants with {b} plants in each row. How many plants altogether?",
        "If one ticket costs ₹{b}, how much do {a} tickets cost?",
        "A book has {a} chapters with {b} pages each. How many pages in total?",
        "{a} friends each bring {b} sweets to a party. How many sweets are there altogether?",
        "A car travels {b} km per hour. How far does it go in {a} hours?",
    ],
    'division': [
        "{a} sweets are shared equally among {b} children. How many does each child get?",
        "A ribbon {a} cm long is cut into {b} equal pieces. How long is each piece?",
        "If {a} apples are packed into bags of {b}, how many full bags can be made?",
        "₹{a} is divided equally among {b} friends. How much does each friend get?",
        "A farmer plants {a} seeds in rows of {b}. How many rows are there?",
        "{a} students are split into {b} equal teams. How many students per team?",
    ],
}

def detect_bare_arithmetic(stem):
    """Detect if stem is a bare 'Calculate: A op B = ?' pattern."""
    patterns = [
        (r'(?:calculate|compute|find|what is|solve)?\s*:?\s*(-?\d+)\s*\+\s*(-?\d+)\s*=?\s*\??', 'addition'),
        (r'(?:calculate|compute|find|what is|solve)?\s*:?\s*(-?\d+)\s*[-−–]\s*(-?\d+)\s*=?\s*\??', 'subtraction'),
        (r'(?:calculate|compute|find|what is|solve)?\s*:?\s*(-?\d+)\s*[×x\*]\s*(-?\d+)\s*=?\s*\??', 'multiplication'),
        (r'(?:calculate|compute|find|what is|solve)?\s*:?\s*(-?\d+)\s*÷\s*(-?\d+)\s*=?\s*\??', 'division'),
    ]
    for pattern, op_type in patterns:
        m = re.match(pattern, stem.strip(), re.IGNORECASE)
        if m:
            return op_type, int(m.group(1)), int(m.group(2))
    return None, None, None


def rephrase_as_word_problem(stem, op_type, a, b):
    """Convert a bare arithmetic stem into a word problem."""
    templates = WORD_PROBLEM_TEMPLATES.get(op_type, [])
    if not templates:
        return stem
    
    # Make sure numbers make sense for the template
    if op_type == 'subtraction' and a < b:
        a, b = b, a  # ensure positive result for word problems
    if op_type == 'division' and (b == 0 or a % b != 0):
        return stem  # skip if not clean division
    
    template = random.choice(templates)
    return template.format(a=a, b=b)


# ─────────────────────────────────────────────────────────────────────────────
# 5. FIX LEVEL_1 HINTS TOO (many are also generic)
# ─────────────────────────────────────────────────────────────────────────────

def fix_level1_hint(q):
    """Fix generic level_1 hints like 'Write down the formula'."""
    hint = q.get('hint', {})
    l1 = hint.get('level_1', '')
    
    generic_l1 = ['write down the formula', 'break the problem', 'substitute values']
    if not any(p in l1.lower() for p in generic_l1):
        return l1  # Keep if already specific
    
    stem_lower = q['stem'].lower()
    
    if re.search(r'\+|add|sum', stem_lower):
        nums = re.findall(r'\d+', q['stem'])
        if len(nums) >= 2:
            return f"Add {nums[0]} and {nums[1]}. Start from the ones column."
    if re.search(r'[-−]|subtract|minus', stem_lower):
        nums = re.findall(r'\d+', q['stem'])
        if len(nums) >= 2:
            return f"Subtract: start with {nums[0]} and take away {nums[1]}."
    if re.search(r'[×x\*]|multiply|times', stem_lower):
        nums = re.findall(r'\d+', q['stem'])
        if len(nums) >= 2:
            return f"Multiply {nums[0]} × {nums[1]} using the standard method."
    if re.search(r'÷|divide', stem_lower):
        nums = re.findall(r'\d+', q['stem'])
        if len(nums) >= 2:
            return f"How many times does {nums[1]} fit into {nums[0]}?"
    if 'perimeter' in stem_lower:
        return "Perimeter = 2 × (length + width). First add the two dimensions."
    if 'area' in stem_lower:
        return "Area = length × width. Multiply the two measurements."
    
    return l1  # Keep original if no match


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def process_grade(grade):
    path = os.path.join(BASE, f'grade{grade}', f'igcse_grade{grade}.json')
    with open(path) as f:
        data = json.load(f)
    
    questions = data['questions']
    stats = {
        'total': len(questions),
        'hints_fixed': 0,
        'diagnostics_fixed': 0,
        'visual_context_added': 0,
        'stems_diversified': 0,
        'l1_hints_fixed': 0,
    }
    
    # Track which bare-arithmetic questions to rephrase (only 40% to keep some plain computation)
    bare_stems = []
    for i, q in enumerate(questions):
        op_type, a, b = detect_bare_arithmetic(q['stem'])
        if op_type:
            bare_stems.append((i, op_type, a, b))
    
    # Randomly select 40% of bare stems to rephrase
    rephrase_count = int(len(bare_stems) * 0.4)
    to_rephrase = set(idx for idx, _, _, _ in random.sample(bare_stems, min(rephrase_count, len(bare_stems))))
    
    for i, q in enumerate(questions):
        # 1. Fix giveaway hints
        hint = q.get('hint', {})
        if hint and is_giveaway_hint(hint.get('level_2', '')):
            hint['level_2'] = build_micro_step_hint(q)
            stats['hints_fixed'] += 1
        
        # Fix generic level_1 hints
        new_l1 = fix_level1_hint(q)
        if new_l1 != hint.get('level_1', ''):
            hint['level_1'] = new_l1
            stats['l1_hints_fixed'] += 1
        
        q['hint'] = hint
        
        # 2. Fix generic diagnostics
        diag = q.get('diagnostics', {})
        has_generic = any(is_generic_diagnostic(v) for v in diag.values())
        if has_generic:
            q['diagnostics'] = build_specific_diagnostics(q)
            stats['diagnostics_fixed'] += 1
        
        # 3. Add visual context
        if q.get('visual_svg') is None and needs_visual_context(q):
            vc = generate_visual_context(q)
            if vc:
                q['visual_context'] = vc
                stats['visual_context_added'] += 1
        
        # 4. Diversify stems
        if i in to_rephrase:
            op_type, a, b = detect_bare_arithmetic(q['stem'])
            if op_type:
                new_stem = rephrase_as_word_problem(q['stem'], op_type, a, b)
                if new_stem != q['stem']:
                    q['stem'] = new_stem
                    stats['stems_diversified'] += 1
    
    data['questions'] = questions
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return stats


if __name__ == '__main__':
    print("=" * 60)
    print("IGCSE CONTENT QUALITY FIX")
    print("=" * 60)
    
    total_stats = {}
    for grade in range(1, 7):
        print(f"\nProcessing Grade {grade}...")
        stats = process_grade(grade)
        total_stats[grade] = stats
        print(f"  Hints fixed: {stats['hints_fixed']}")
        print(f"  L1 hints fixed: {stats['l1_hints_fixed']}")
        print(f"  Diagnostics fixed: {stats['diagnostics_fixed']}")
        print(f"  Visual contexts added: {stats['visual_context_added']}")
        print(f"  Stems diversified: {stats['stems_diversified']}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_h = sum(s['hints_fixed'] for s in total_stats.values())
    total_d = sum(s['diagnostics_fixed'] for s in total_stats.values())
    total_v = sum(s['visual_context_added'] for s in total_stats.values())
    total_s = sum(s['stems_diversified'] for s in total_stats.values())
    total_l1 = sum(s['l1_hints_fixed'] for s in total_stats.values())
    print(f"Total giveaway hints fixed: {total_h}")
    print(f"Total L1 hints fixed: {total_l1}")
    print(f"Total diagnostics fixed: {total_d}")
    print(f"Total visual contexts added: {total_v}")
    print(f"Total stems diversified: {total_s}")
