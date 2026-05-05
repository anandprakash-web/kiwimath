# Wavebook Question Bank Index

## Overview
- **Total Questions:** 551
- **Level 3 (Grades 3-4):** 239 questions across 19 sessions
- **Level 4 (Grades 5-6):** 312 questions across 26 sessions
- **SVG Illustrations:** 25 created, 51 pending (figure-based questions)
- **Last Updated:** 2026-05-05

## Level 3 Batches

### wavebook_L3_batch1.json (67 questions)
Sessions: s01, s04, s06, s10, s11
Topics: Knowing about numbers, Factors and multiples, Multiplication and Division, Decimals Part 2, Area

### wavebook_L3_batch2.json (42 questions)
Sessions: s12, s14, s15, s17
Topics: Metric Conversion, Perimeter, Sets and its operations, Patterns

### wavebook_L3_batch3.json (40 questions)
Sessions: s18, s20, s22, s23
Topics: Perimeter advanced, Symmetry Introduction, Symmetry, Clocks and Time

### wavebook_L3_batch4.json (90 questions)
Sessions: s25, s29, s30, s32, s38, s40
Topics: Days months dates, Blood Relation, Mental Ability, Paper Folding, Pattern of shapes, Pie graph and pictograph, Data Handling, Nets of cuboids boxes

## Level 4 Batches

### wavebook_L4_batch1.json (71 questions)
Sessions: s01, s02, s03, s04, s07, s08
Topics: Knowing your numbers, Test of divisibility, Factors and multiples, Integers and Fractions, Addition and Subtraction, Percentage

### wavebook_L4_batch2.json (68 questions)
Sessions: s09, s10, s13, s15, s16, s17
Topics: Profit and Loss, Puzzles and Patterns, Magic Squares and Money, Geometry - Angles and Lines, Ratio and Proportion, Quadrilaterals and Polygons

### wavebook_L4_batch3.json (68 questions)
Sessions: s20, s21, s22, s23, s26, s27
Topics: Average and Pie Chart, Data Handling, Algebra, Algebra - Expressions, Counting Figures, Paper Cutting and Folding

### wavebook_L4_batch4.json (105 questions)
Sessions: s28, s29, s30, s31, s32, s37, s38, s40
Topics: Mental Ability, Mirror Images and Relationships, Clock and Calendar, Cubes and Dice, Direction Sense, Area of Plane Figures, Perimeter of Plane Figures, Logical Reasoning

## Question Schema
```json
{
  "id": "wb_L{level}_s{session:02d}_q{num:02d}",
  "stem": "question text",
  "interaction_mode": "mcq",
  "topic": "Topic Name",
  "difficulty_tier": "warmup|practice|challenge",
  "question_number": N,
  "choices": ["(a)...", "(b)...", "(c)...", "(d)..."],
  "correct_answer": 0,
  "grade_band": "3-4|5-6",
  "source": "Wavebook L{level} S{session}",
  "svg": "svg/wb_L{level}_s{session}_q{num}.svg"
}
```

## Difficulty Tiers
- Q1-5: warmup
- Q6-10: practice
- Q11-15: challenge

## Notes
- Source: Master Google Sheet "Wavebook of L3/L4/Grade 3/4/5/6" + linked PDFs
- Assignment numbers in PDFs don't always match session numbers in spreadsheet
- Questions requiring purely visual figures are marked with SVG paths
- 22 questions removed due to being open-ended (non-MCQ format)
