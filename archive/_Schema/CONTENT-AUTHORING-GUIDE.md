# Kiwimath v0.2 — Content Authoring Guide

> For the academic content team. This guide covers how to write questions in the hybrid v0.2 schema. If you've been writing v0.1 questions, nothing breaks — all your existing content still works. v0.2 just adds optional fields that make questions richer.

---

## Quick Start: The Minimum Viable Question

Every question needs these **required** fields (same as v0.1):

```json
{
  "id": "G1-COUNT-060",
  "grade": 1,
  "topic": "counting_observation",
  "subtopic": "counting_objects",
  "subskills": ["one_to_one_correspondence"],
  "difficulty": 1,
  "tier": "warmup",

  "stem_template": "{name} has {N} {object}. How many are there?",
  "answer_type": "multiple_choice",

  "params": {
    "N": {"range": [3, 7]},
    "name": {"pool": ["Aarav", "Mei", "Liam"]},
    "object": {"pool": ["apples", "marbles"]}
  },

  "answer_formula": "N",
  "distractors": [
    {"formula": "N + 1", "label": "over_count"},
    {"formula": "N - 1", "label": "under_count"}
  ],

  "misconceptions": [
    {
      "trigger_answer": "N + 1",
      "diagnosis": "double_counted_one",
      "feedback_child": "Almost! One got counted twice. Point to each one just once.",
      "step_down_path": ["G1-COUNT-060-S1"]
    },
    {
      "trigger_answer": "N - 1",
      "diagnosis": "skipped_one_object",
      "feedback_child": "So close! Check if you missed one.",
      "step_down_path": ["G1-COUNT-060-S1"]
    }
  ],

  "version": 1,
  "author": "AP",
  "status": "draft"
}
```

That's a valid v0.1 question, and it's also a valid v0.2 question. The v0.2 fields below are **all optional** — add them when they add value.

---

## v0.2 Optional Fields — When and How to Use Them

### 1. `pedagogy` — What teaching approach is this?

```json
"pedagogy": "cpa_concrete"
```

Values: `cpa_concrete` | `cpa_pictorial` | `cpa_abstract` | `drill` | `exploration`

Use this to tag which Singapore CPA stage the question targets. This helps us sequence questions (concrete before pictorial before abstract) and build reports for parents. If you're unsure, leave it out.

**Rules of thumb:**
- L1-L2 (Beginner/Intermediate): usually `cpa_concrete` or `cpa_pictorial`
- L3 (Advanced): usually `cpa_abstract` or `drill`
- L4-L5 (Competition/Olympiad): usually `exploration`


### 2. `visual_manifest` — Describe what the child should SEE

This is the biggest v0.2 addition. Instead of (or alongside) the technical `visual` field, you write a **plain English description** of the illustration.

```json
"visual_manifest": {
  "art_brief": "A picnic blanket with {N} bright red {object} scattered across it. Each {object} should be distinct and easy to tap.",
  "alt_text": "{N} red {object} on a picnic blanket.",
  "style": "warm_cartoon",
  "layout_hint": "scattered",
  "visual_type": "illustration"
}
```

**Fields:**

| Field | Required? | What it does |
|-------|-----------|-------------|
| `art_brief` | Yes | Describe the image in detail. Use `{param}` placeholders — they get filled in from `params`. Write it like you're briefing an illustrator. |
| `alt_text` | Yes | Short accessibility text. Also uses `{param}` placeholders. |
| `style` | No | Art style hint. Default: `"warm_cartoon"`. |
| `layout_hint` | No | How objects are arranged: `"scattered"`, `"row"`, `"grid"`, `"stacked"`, `"centered"`, `"side_by_side"`. |
| `visual_type` | No | What kind of visual: `"illustration"`, `"diagram"`, `"3D_diagram"`. |

**How it works with the old `visual` field:** Both can coexist. The app tries the SVG generator first (if one exists). If no generator exists, it uses the `visual_manifest` for AI-generated art or pre-rendered assets. If neither exists, no visual is shown.

**You should always write `visual_manifest`** for questions that need a visual. Even if there's also an SVG generator. The art_brief is the source of truth for what the child should see.


### 3. `interaction` — How does the child ANSWER?

```json
"interaction": {
  "type": "tap_to_count",
  "target_formula": "N",
  "tap_targets": "object",
  "fallback_type": "multiple_choice"
}
```

This is a richer replacement for `answer_type`. Keep `answer_type` for now (backward compat), but add `interaction` when the question uses a non-standard input method.

**Available types:**

| Type | What the child does | When to use |
|------|-------------------|-------------|
| `multiple_choice` | Tap one of 3-4 text options | Default. Most questions. |
| `multiple_choice_visual` | Tap one of 3-4 image options | When options are pictures, not numbers/text. |
| `tap_to_count` | Tap objects in the visual to count them | Counting questions with interactive visuals. |
| `drag_to_order` | Drag items into the right sequence | Ordering, sequencing questions. |
| `numeric_keypad` | Type a number on a keypad | Open-ended numeric answers. |

**Important:** `fallback_type` is what the app shows if it doesn't support the interaction type yet. Always set it to `"multiple_choice"` for now.

**Extra fields by type:**
- `tap_to_count`: set `target_formula` (e.g., `"N"`) and `tap_targets` (param key for what's tappable)
- `multiple_choice_visual`: set `options_descriptions` (text descriptions of the image options) and `correct_option_index` (0-based)


### 4. `socratic_feedback` — What to say when the child makes mistakes

```json
"socratic_feedback": {
  "on_correct": "Great job! You counted {N} {object}!",
  "on_under_count": "Almost! Keep counting — what comes after {attempt}?",
  "on_over_count": "Oops! Looks like one got counted twice.",
  "on_timeout": "Take your time! Start from the left.",
  "encouragement_after_retry": "You've got this!"
}
```

**How this differs from `misconceptions`:** Misconceptions handle *specific wrong answers* ("the child picked N+1, so they double-counted"). Socratic feedback handles *categories of mistakes* that don't map to a specific distractor — partial attempts, timeouts, over/under counting on tap interactions, or generic encouragement.

**Available feedback keys:**

| Key | When it fires |
|-----|--------------|
| `on_correct` | Child gets it right |
| `on_partial` | Child started but didn't finish (tap_to_count) |
| `on_timeout` | Child took too long |
| `on_under_count` | Tap count is less than target |
| `on_over_count` | Tap count exceeds target |
| `generic_incorrect` | Wrong answer but no matching misconception |
| `incorrect_low` | Numeric answer is below correct |
| `incorrect_high` | Numeric answer is above correct |
| `incorrect_selection` | Wrong visual/spatial selection |
| `encouragement_after_retry` | After "Try again" on a retry |

You don't need all of them — just the ones that make sense for the question. All are optional.

**Tone rules:** Write like you're sitting next to the child. First person plural ("Let's count together"). Max 20 words per message. Use `{param}` placeholders.


### 5. `curriculum_alignment` — Which frameworks does this cover?

```json
"curriculum_alignment": {
  "common_core": "K.CC.B.4",
  "cambridge_stage": 1,
  "cambridge_strand": "Thinking and Working Mathematically: Counting",
  "singapore_strand": "Whole Numbers",
  "kangaroo_level": "Felix",
  "olympiad_skill": "Spatial Transformation / Invariants",
  "reference": "Felix 2021 Q5"
}
```

All fields optional. Fill in the ones you know. This replaces putting curriculum info in `tags` (though you can still use tags too).


---

## ID Format

IDs remain the same format: `G{grade}-{TOPIC}-{nnn}`

- **Grade**: 1-8
- **Topic codes**: COUNT, ADD, SUB, SHAPE, PATT, MEAS, LOGIC, PUZZLE
- **Number**: 001-999

Step-downs: `G1-COUNT-050-S1`, `G1-COUNT-050-S2`, etc. (max S5)


## Difficulty Levels (1-5)

| Level | Name | Description | Typical pedagogy |
|-------|------|-------------|-----------------|
| 1 | Beginner | Core curriculum basics | `cpa_concrete` |
| 2 | Intermediate | Confident application | `cpa_pictorial` |
| 3 | Advanced | Multi-step, less scaffolding | `cpa_abstract` / `drill` |
| 4 | Competition Prep | National math competition level | `exploration` |
| 5 | Olympiad Foundation | Kangaroo/Felix/IMO-style | `exploration` |


## Parametric Questions: Making One JSON Generate Many Problems

The biggest advantage of our schema: **template variables**. Instead of writing "How many apples?", write:

```
"stem_template": "How many {object} does {name} have?"
```

Then define the pools:

```json
"params": {
  "name": {"pool": ["Aarav", "Mei", "Liam", "Sofia"]},
  "object": {"pool": ["apples", "marbles", "stickers"]},
  "N": {"range": [3, 8]}
}
```

The engine picks one value from each pool/range per play, so one question file generates `4 x 3 x 6 = 72` unique instances.

**Rules:**
- Every `{placeholder}` in `stem_template` must have a matching entry in `params` or `derived`
- `derived` is for computed values: `"N_total": "A + B"`
- Template vars work in `visual_manifest.art_brief` and `socratic_feedback` too!
- For L5/Olympiad questions where the puzzle is inherently unique, it's OK to have minimal or no params


## Validation

Run the validator before submitting:

```bash
cd kiwimath
python3 -m content_tools.validate /path/to/your/questions/
```

It checks: valid JSON, all required fields, ID format, placeholder resolution, misconception-distractor linking, step-down references, and more. Fix any errors before submitting.


## Sample Files

See `_Schema/samples/` for 5 complete examples:
- `G1-COUNT-050.json` — L1 Beginner: counting objects (tap_to_count)
- `G1-COUNT-051.json` — L1 Beginner: ordinal numbers (multiple_choice_visual)
- `G1-COUNT-052.json` — L1 Beginner: subitizing/composition (multiple_choice)
- `G1-COUNT-080.json` — L5 Olympiad: mirror reflection (multiple_choice_visual)
- `G1-COUNT-081.json` — L5 Olympiad: perspective projection (multiple_choice)
