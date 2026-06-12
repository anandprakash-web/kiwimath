#!/usr/bin/env python3
"""Append manual-reading + systemic findings to v4_issues.json."""
import json, re, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', 'content-live', 'content-v4', 'adaptive'))
issues = json.load(open(os.path.join(HERE, 'v4_issues.json')))
already_leak = {i['id'] for i in issues if i['check'] == 'hint_answer_leak'}
new = []

for path in sorted(glob.glob(os.path.join(ROOT, 'grade*', 'g*-*.json'))):
    fname = os.path.relpath(path, ROOT)
    d = json.load(open(path))
    for q in d['questions']:
        qid = q['id']
        ch = q.get('choices') or []
        ca = q.get('correct_answer')
        stem = q.get('stem') or ''
        h = q.get('hint') or {}
        ht = ' '.join(str(v) for v in h.values())
        # 1. "(alt)" duplicate choices
        for i, c in enumerate(ch):
            if isinstance(c, str) and c.endswith(' (alt)'):
                base = c[:-6]
                dup_of_correct = isinstance(ca, int) and 0 <= ca < len(ch) and str(ch[ca]) == base
                new.append({"check": "duplicate_choice_alt",
                            "severity": "critical" if dup_of_correct else "high",
                            "id": qid, "file": fname,
                            "detail": f'choice {i} is {c!r} — duplicates {"the CORRECT choice" if dup_of_correct else "another distractor"} {base!r}; a student picking it is marked wrong for an identical answer. choices={ch}'})
        # 2. extra hint leak styles
        val = None
        if ch and isinstance(ca, int) and 0 <= ca < len(ch):
            val = str(ch[ca])
        elif q.get('correct_value') is not None:
            val = str(q['correct_value'])
        if val and qid not in already_leak and re.search(r'(?:Next|Sum|Total|Answer)\s*[:=]\s*' + re.escape(val) + r'\b', ht):
            new.append({"check": "hint_answer_leak", "severity": "high", "id": qid, "file": fname,
                        "detail": f'hint states the answer via "Next:/Sum:/Total:/Answer: {val}" style'})
        # 3. tautological length questions
        m = re.search(r'is (\d+(?:\.\d+)?) (\w+) long\. What is its length in (\w+)\?', stem)
        if m and m.group(2) == m.group(3):
            new.append({"check": "stem_tautological", "severity": "high", "id": qid, "file": fname,
                        "detail": f'answer is stated verbatim in the stem (no math to do): {stem[:90]!r}'})
        # 4. garbled (00 + ...) hints
        if re.search(r'\(00 \+|\+ 00\)', ht):
            new.append({"check": "hint_garbled", "severity": "medium", "id": qid, "file": fname,
                        "detail": 'hint contains garbled place-value decomposition like "24 × (00 + 7)"'})

# 5. systemic template noise (summary entry)
new.append({"check": "hint_stitched_template_noise", "severity": "medium", "id": "SYSTEMIC", "file": "(9,315 questions)",
            "detail": '9,315 hint ladders end level_1 with the boilerplate "Try working out the calculation step-by-step. Compare your result to the choices: <all 4 choices>". Pure template noise; reads absurd on non-numeric questions (e.g. "Compare your result to the choices: Football, Cricket, Badminton, Kabaddi"). Recommend stripping the sentence pair globally.'})

# 6. manual reading findings
manual = [
    ("A5-MSR-0120", "grade5/g5-measurement.json", "critical",
     "SUSPECT WRONG KEY: stem says rectangle 5x4 (=20) + right triangle base 3 height 1 (=1.5) -> 21.5, and 21.5 is choice 0; but keyed answer is 25.5 and hint literally says 'The total area per the competition key is 25.5' (also an answer leak). level_2 hint is garbage ('5 cm².'). Verify against source figure or rekey to 21.5."),
    ("A1-PAT-0143", "grade1/g1-patterns.json", "high",
     "Wrong-topic hint ladder: question is a number bond (13 = 2 + ?), all 3 hints talk about repeating visual patterns ('Look for what repeats!')."),
    ("A2-PAT-0028", "grade2/g2-patterns.json", "high",
     "Wrong-topic hints: magic-square sum question, hints describe counting shape sides/corners (Triangle=3 sides...). visual_context 'A square with equal sides marked' is stale."),
    ("A4-SHP-0644", "grade4/g4-shapes.json", "high",
     "level_2 hint states the answer outright ('A square pyramid has 8 edges.') — leak style not caught by '=' regex. visual_context 'A square with equal sides marked' is wrong for a pyramid question."),
    ("A6-DAT-0042", "grade6/g6-data.json", "critical",
     "Choices contain both 'pencils' (keyed correct) and 'pencils (alt)' — two identical correct answers, one marked wrong."),
    ("A6-ARI-0187", "grade6/g6-arithmetic.json", "high",
     "Nonsense hint: question is 6/3 × 5/7 (fraction multiplication), hint says 'Multiply 6 × 3 using the standard method... multiply 6 by each digit of 3'."),
    ("A6-MSR-0027", "grade6/g6-measurement.json", "medium",
     "All 3 diagnostics talk about fraction work ('did you flip and multiply?') for a speed/distance/time question."),
    ("A2-CNT-0224", "grade2/g2-counting.json", "medium",
     "Odd framing for age 7: 'Diya is lying and actually has 18' — answer is just restated in the stem; trivial comprehension check dressed as math, plus 'lying' wording."),
    ("A1-TIM-0217", "grade1/g1-time-money.json", "medium",
     "Age-appropriateness: 6:20 + 120 minutes with hour rollover is well above Grade 1; several similar items in g1-time-money."),
    ("A1-SHP-0559", "grade1/g1-shapes.json", "medium",
     "Age-appropriateness: perimeter formula question (2×(9+6)) tagged Grade 1; formula-based perimeter is G3+ in most curricula."),
    ("A3-ASB-0285", "grade3/g3-add-sub.json", "medium",
     "Garbled hint: '24 × 7 = 24 × (00 + 7)' — place-value decomposition broken (should be 20 + 4). 14 questions bank-wide share this pattern."),
    ("A2-ADD-0096", "grade2/g2-addition.json", "medium",
     "Story wrapper disconnected from task: 'Ranger Roo found some marbles...' prepended to a 4x4 grid colouring combinatorics question; visual_context stale ('A square with equal sides marked'); also misfiled under addition."),
    ("A2-CNT-0239", "grade2/g2-counting.json", "medium",
     "Wrapper/metadata mismatch: 'Vanya found some coins and wants to count them' prepended to a place-value question; visual_context says 'Coins and notes arranged for counting' but there is no svg."),
    ("A1-CNT-0282", "grade1/g1-counting.json", "medium",
     "Hints are generic counting ('point to each object') for a 9-5 comparison word problem; visual_context is placeholder text 'A visual representation of the problem.'"),
    ("A4-WPR-0197", "grade4/g4-word-problems.json", "medium",
     "Weak distractors: 'Is 21 a multiple of 7?' offers 'Cannot tell' and 'Sometimes'; hint dumps unrelated LCM/HCF boilerplate."),
]
for qid, fname, sev, detail in manual:
    new.append({"check": "manual_reading", "severity": sev, "id": qid, "file": fname, "detail": detail})

issues.extend(new)
json.dump(issues, open(os.path.join(HERE, 'v4_issues.json'), 'w'), indent=2)
from collections import Counter
c = Counter((i['check'], i['severity']) for i in issues)
for k, v in sorted(c.items()):
    print(k, v)
print('total issues:', len(issues), '| appended:', len(new))
