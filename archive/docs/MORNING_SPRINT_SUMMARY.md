# Kiwimath Morning Sprint — 29 April 2026 (today)

This morning's autonomous run picked up where yesterday left off. All five
priority tasks (#194, #196, #199, #197, #191) shipped end-to-end yesterday;
today's pass focused on the explicit "did NOT do" list from yesterday's
summary plus a content-quality follow-up. **Yesterday's writeup is
preserved below verbatim — scroll past this block.**

## TL;DR — what's new today

| # | What | Where |
|---|------|-------|
| 1 | Verified yesterday's work — 15/15 endpoint smoke tests pass on the merged corpus | `python3 -c "..."` (TestClient) |
| 2 | Wired Onboarding into `main.dart` with first-launch detection (zero-XP / zero-streak heuristic) | `app/lib/main.dart`, `app/lib/screens/home_screen.dart` |
| 3 | Wired Parent Dashboard + Learning Path into a new "More" menu in the home top bar | `app/lib/main.dart`, `app/lib/screens/home_screen.dart` |
| 4 | New `LearningPathScreen` — vertical timeline UI over `/v2/learning-path` with a "Start this stop" CTA on the current node | `app/lib/screens/learning_path_screen.dart` (NEW) |
| 5 | Refreshed `content-v2/manifest.json` — now reflects 1200 q/topic across difficulty 1-200, with per-grade and advanced/expert/olympiad buckets | `content-v2/manifest.json` |
| 6 | New content-quality report tool — flags stem-template concentration ≥5% per grade band; surfaces hint-coverage gaps | `backend/scripts/content_quality_report.py` (NEW); report at `content-v2/_workspace/quality_report.md` |
| 7 | Targeted variety augmentation for Arithmetic G3-4 — 120 new questions across money, time, comparison, missing-number, doubling/halving, mental-math, sharing. **Worst-template concentration in arithmetic G3 went from 80.8% → 67.2%.** All 120 generated answers programmatically verified. | `backend/scripts/augment_arithmetic_variety.py` (NEW), `content-v2/topic-2-arithmetic/grade34_variety_questions.json` (NEW) |
| 8 | Loader extended to recognise the new file (explicit allow-list, not glob — keeps content opt-in) | `backend/app/services/content_store_v2.py` |

Total corpus is now **9,720 questions** (was 9,600 yesterday).

## Endpoint smoke test (TestClient, 15/15 pass)

```
✓ 200 GET  /health
✓ 200 GET  /v2/topics
✓ 200 GET  /v2/topics?grade=3
✓ 200 GET  /v2/onboarding/benchmark/questions?grade=2&count=10
✓ 200 POST /v2/onboarding/benchmark
✓ 200 GET  /v2/parent/dashboard
✓ 200 GET  /v2/learning-path?grade=2
✓ 200 GET  /v2/questions/next?use_learning_path=true
✓ 200 GET  /v2/questions/T2-0901          (new variety question)
✓ 200 POST /v2/questions/T2-0901/feedback
✓ 200 GET  /v2/admin/feedback
✓ 200 GET  /v2/admin/feedback/summary
✓ 200 GET  /v2/questions/next?grade=3
✓ 200 GET  /v2/questions/next?grade=4
✓ 422 POST /v2/questions/T1-001/feedback   (bad feedback_type rejected)
```

## Today's changes in detail

### Onboarding & dashboard wiring (yesterday's "did NOT do" #1)

`_AppShell` in `lib/main.dart` now does first-launch detection: if the
profile loaded from `/v2/profile` reports `xp_total == 0`, `streak == 0`,
`daily_progress == 0`, and `kiwi_coins == 0`, we push `OnboardingScreen` as
a fullscreen modal on the next frame. The `_onboardingHandled` flag prevents
re-prompting after the kid finishes onboarding (so re-entering the app
won't loop them through again). On completion, the result's grade is
applied to the home view and the profile reloads.

`HomeScreen` got three optional callbacks — `onOpenLearningPath`,
`onOpenParentDashboard`, `onRestartOnboarding` — and a small `more_vert`
overflow menu in the top bar that surfaces them alongside Sign Out. The
existing long-press-emoji-to-sign-out shortcut still works; the menu is
purely additive. Sign-out is kept inside the menu because the long-press is
hard to discover.

### Learning Path UI

`learning_path_screen.dart` renders the `/v2/learning-path` response as a
vertical timeline with a coloured rail. Each stop shows topic, kid-readable
reason, target difficulty, and recommended question count; review stops
get a blue "Review" pill, mastered stops show a green check. The first
not-yet-mastered stop is the "current" node — only that stop has a "Start
this stop" CTA, which drops the kid into `QuestionScreenV2` with the
recommended topic and grade. Pull-to-refresh reloads the path. Backed by
the existing `ApiClient.getLearningPath` method (no API client changes).

### Content quality tooling

`backend/scripts/content_quality_report.py` is a no-side-effects scanner
that emits a Markdown report covering, per topic and per grade band:
difficulty bucket distribution, hint-ladder coverage (with field-name
fallback for `hints` / `hint_ladder` / `hint`), choice sanity, and the
top-N most-common stem prefixes (numbers normalised to `#`). Any topic
where a single template covers ≥5% of a grade band is flagged with a ⚠️.
First report is checked in at `content-v2/_workspace/quality_report.md`
and shows several G3-4 topics over the threshold — useful triage list for
the next content pass.

### Arithmetic G3-4 variety augmentation

`backend/scripts/augment_arithmetic_variety.py` is a deterministic,
seeded generator that emits 120 new G3-4 arithmetic questions covering
seven framings the existing corpus barely touches:

- money (`pays ₹X for an item costing ₹Y, what's the change?`)
- time (`it is H:MM, what time after N minutes?`)
- comparison (`how many more children on Monday than Tuesday?`)
- mental-math rounding tricks (`29 is close to 30; what is 29 + 67?`)
- missing-number (`A + ___ = T`, both addition and subtraction variants)
- doubling / halving
- equal sharing (introduces division)

Each question gets:
- a 4-choice multiple choice with plausible distractors,
- diagnostic hints keyed off common mistakes (wrong operator, swapped
  operands, off-by-one, etc.),
- the standard 6-level Socratic hint ladder,
- the existing question schema (verified by loading through
  `content_store_v2.QuestionV2`).

All 120 generated answers were independently verified by a regex-based
checker — 0 failures. The new file lives at
`content-v2/topic-2-arithmetic/grade34_variety_questions.json` and is
opted into the loader by name. After merge, the worst-template
concentration in arithmetic G3 dropped from 80.8% → 67.2% (G4: 81.5% →
69.0%); the new top templates now include time, money, and missing-number
framings rather than being 80% "What is N + M?".

### Manifest refresh

`content-v2/manifest.json` was rewritten to reflect the current corpus —
1200 questions per topic for 7 topics + 1320 for arithmetic, difficulty
range 1-200, grade-band counts (g1/g2/g3/g4), and six-bucket difficulty
distribution including `advanced`/`expert`/`olympiad`. Bumped to schema
version 2.1 with a changelog entry. The auto-loader doesn't read this
file, but downstream tooling (preview/admin pages) that reads counts from
the manifest will now be in sync.

## Files touched today

```
NEW  app/lib/screens/learning_path_screen.dart
NEW  backend/scripts/content_quality_report.py
NEW  backend/scripts/augment_arithmetic_variety.py
NEW  content-v2/topic-2-arithmetic/grade34_variety_questions.json
NEW  content-v2/_workspace/quality_report.md
EDIT app/lib/main.dart                                 (imports + first-launch routing + 3 navigation handlers)
EDIT app/lib/screens/home_screen.dart                  (3 optional callbacks + _buildMoreMenu)
EDIT backend/app/services/content_store_v2.py         (add variety file to allow-list)
EDIT content-v2/manifest.json                         (rewritten to reflect 9,720 q corpus)
```

## What I still deliberately did NOT do

- **Generate variety packs for the other 7 topics.** The arithmetic pack is
  a working template; replicating it for counting/patterns/logic/spatial/
  shapes/word-problems/puzzles is the next obvious step. The quality report
  shows which topics are most concentrated.
- **SVG visuals for G3-4.** Out of scope for this run, same as yesterday.
- **APK build / Cloud Run deploy.** Per task brief — needs your machine.
- **Wire SharedPreferences for first-launch detection.** The zero-XP
  heuristic works but is fragile if a brand-new auth user resumes mid-flow.
  A `flutter_secure_storage` flag would be more robust; left alone because
  it adds a dependency.

## Quick sanity-check commands

```bash
# Re-run today's smoke suite
cd backend && KIWIMATH_V2_CONTENT_DIR=../content-v2 python3 -c "
import sys, os; sys.path.insert(0, '.')
os.environ['KIWIMATH_V2_CONTENT_DIR'] = os.path.abspath('../content-v2')
from app.main import app
from fastapi.testclient import TestClient
with TestClient(app) as c:
    print(c.get('/v2/questions/T2-0901').json()['stem'])
"

# Re-generate the quality report
python3 backend/scripts/content_quality_report.py \
    --content-dir content-v2 --top-templates 8 \
    --output content-v2/_workspace/quality_report.md

# Re-generate the variety pack (deterministic — same seed = same 120 q's)
python3 backend/scripts/augment_arithmetic_variety.py \
    --content-dir content-v2 --count 120 --seed 4729
```

---

# Kiwimath Morning Sprint — 28 April 2026 (yesterday)

Autonomous morning run covering tasks #194, #196, #199, #197, and #191. All
five priority items shipped end-to-end (backend + Flutter where applicable).
Backend verified by spinning up `app.main:app` with the FastAPI test client
and exercising every new endpoint — every call returned 2xx with the
expected payload shape.

## TL;DR

| # | Task | Backend | Flutter | Status |
|---|------|---------|---------|--------|
| 194 | Question feedback / report | `POST /v2/questions/{qid}/feedback`, `GET /v2/admin/feedback`, `GET /v2/admin/feedback/summary` | Flag icon in question top bar + bottom-sheet `_ReportQuestionSheet` | done |
| 196 | Onboarding benchmark | `GET /v2/onboarding/benchmark/questions`, `POST /v2/onboarding/benchmark` | New `onboarding_screen.dart` (welcome → grade → 10-q quiz → results) | done |
| 199 | Parent dashboard | `GET /v2/parent/dashboard` (file already existed; wired into `main.py`) | New `parent_dashboard_screen.dart` | done |
| 197 | Adaptive learning path | `GET /v2/learning-path` + `use_learning_path=true` flag on `/v2/questions/next` | API client method `getLearningPath()` (UI deferred for review) | done |
| 191 | Grade 3-4 content | Schema bumped to support difficulty 1-200 + 4-digit IDs; loader now merges `grade34_questions.json` automatically | Grade 3 + 4 grade picker entries already supported via existing tier theming | done |

Total content now in the store: **7200 questions** (4800 G1-2 + 2400 G3-4).

## Endpoint test results (in-process via TestClient)

```
=== /health ===                       200 (7200 questions loaded)
=== /v2/topics?grade=3 ===            200 (8 topics)
=== POST /v2/questions/T1-001/feedback === 200 (record returned w/ feedback_id)
=== bad feedback_type ===             422 (validator rejects)
=== GET  /v2/admin/feedback ===       200 (1 record after seed)
=== GET  /v2/admin/feedback/summary === 200 (counts by_type + top_flagged_questions)
=== GET  /v2/onboarding/benchmark/questions?grade=2&count=10 === 200 (10 q's)
=== POST /v2/onboarding/benchmark ===  200 (estimated_ability=11, rec_start=6,
                                            suggested_topics=[counting, patterns, spatial])
=== GET  /v2/parent/dashboard ===      200 (overall_acc=50.0, 8 topics,
                                            plain-language recommendations)
=== GET  /v2/learning-path?grade=2 === 200 (8-stop plan, weakest topic first)
=== /v2/questions/next?use_learning_path=true === 200 (picked T2-051)
=== /v2/questions/next?grade=3 ===     200 (picked T2-0601, advanced tier)
```

---

## Task #194 — User-side question feedback

**Backend (`backend/app/api/questions_v2.py`)**

Added at the bottom of the file:
- Feedback type whitelist: `wrong_answer`, `unclear_stem`, `bad_visual`, `too_easy`, `too_hard`, `other`.
- `POST /v2/questions/{qid}/feedback` — Pydantic-validated request, generates a UUID, stores in an in-memory dict, also writes to Firestore `question_feedback` collection if available (best-effort, never blocks user).
- `GET /v2/admin/feedback` — paginated list with `question_id`, `feedback_type`, `user_id` filters; merges in-memory + Firestore records, dedupes, sorts most-recent first.
- `GET /v2/admin/feedback/summary` — total count, breakdown by type, top-10 most-flagged questions.

**Flutter (`app/lib/screens/question_screen_v2.dart`, `app/lib/services/api_client.dart`)**

- New `submitQuestionFeedback()` method on `ApiClient`.
- Tiny flag/report button added to the question top bar (between progress dots and XP badge).
- Tapping it opens `_ReportQuestionSheet` — a draggable bottom sheet with:
  - 6 emoji-tagged categories (matching the backend whitelist),
  - optional 200-char comment field,
  - submit button → calls API → renders a "Thanks for letting us know!" check-mark for ~1.1s before auto-dismissing.
- All errors fall through to a snackbar; the sheet doesn't trap the kid if the network is flaky.

## Task #196 — Onboarding benchmark + guided path

**Backend (`backend/app/api/onboarding.py`, NEW)**

- Round-robin question picker: every topic gets one mid-difficulty diagnostic + the rest fills with a curve of easy → hard within the grade band. Sorted easiest-first for a gentle ramp.
- Grade bands (extended to support the new G3-4 content):
  - G1: 1–50 · G2: 1–100 · G3: 50–150 · G4: 75–175 · G5: 100–200
- `POST /v2/onboarding/benchmark` runs every answer through `engine_v2.process_answer`, so the user's per-topic θ is initialised live and `/v2/questions/next` immediately starts targeting the right zone.
- Response includes: `estimated_ability`, `recommended_starting_difficulty` (≈avg − 5 for kid-feels-capable), `suggested_topics` (weakest first), `strengths` (100% topics), and a per-topic ability table.

**Flutter (`app/lib/screens/onboarding_screen.dart`, NEW)**

- Welcome screen with kiwi emoji + reassuring copy.
- Grade picker grid (1–5) using the existing `KiwiColors.topicGradients` so it visually matches the home screen.
- Quiz UI mirrors the question screen but stripped down: progress bar, stem, optional SVG visual, vertical 4-option layout, Next/Finish button.
- Results screen calls out strengths, focus topics, and starting level via `_ResultCard` tiles, then hands the parsed `OnboardingResult` to a parent-supplied `onComplete` callback.

## Task #199 — Parent dashboard

**Backend (`backend/app/api/parent.py`)**

Already existed in the repo; wired into `main.py`'s router list. Returns:
- Headline: overall_accuracy, total_questions, current/longest streak, level + name, XP, kiwi_coins, mastery_gems.
- Per-topic: ability_score, accuracy, attempts, mastery label (`learning` / `practising` / `mastered`), confidence, last_practised timestamp.
- Strengths, needs_practice, plain-language recommendations (capped at 3, e.g. *"Your child is strong in Counting (88% accuracy). Great time to try a harder challenge here."*).
- Recent activity: last 10 answers across all topics.

**Flutter (`app/lib/screens/parent_dashboard_screen.dart`, NEW)**

- 2×2 summary cards: Accuracy, Streak, Level, XP.
- Recommendations as soft-green callouts with lightbulb icon.
- Strengths / Needs-practice as colored pills.
- Per-topic cards with mastery chip + linear progress bar tinted by mastery state (green/amber/coral).
- Recent activity scroll list.
- Pull-to-refresh + retry-on-error states baked in.

## Task #197 — Adaptive learning path

**Backend (`backend/app/api/learning_path.py`)**

Existing file; wired into `main.py`. Ordering rules implemented:
1. New / under-explored topics (attempts < 3) — gentle introduction.
2. Weakest learning/practising topics next (lowest accuracy first).
3. Mastered topics that are *due* for review — spaced-repetition ladder: 1 / 3 / 5 days.
4. Mastered + not due — bottom of the queue.

Each stop returns a `target_difficulty`, a `[lo, hi]` range, suggested `questions_to_attempt` (5 for review, 8 for new, 10 for practising, 12 for weak), and a parent-readable `reason` string.

**Integration with `/v2/questions/next`**

Added `use_learning_path: bool` query param. When true (and no explicit `topic` given), the endpoint internally calls `get_learning_path()` and uses the first stop's `topic_id` + `target_difficulty`. Falls back silently to legacy behaviour if anything goes wrong, so this is purely additive.

**Flutter (`app/lib/services/api_client.dart`)**

- `getLearningPath({userId, grade})` returns the raw map.
- A dedicated UI screen wasn't built — recommendation is to thread learning-path stops directly into the home screen's "next session" CTA. Happy to mock that up once you've seen the API output.

## Task #191 — Grade 3-4 content (300 questions / topic)

**Schema changes (`backend/app/services/content_store_v2.py`)**

- `_QUESTION_ID_RE` widened from `^T[1-8]-\d{3}$` to `^T[1-8]-\d{3,4}$` (so IDs like `T2-0601` are valid).
- `QuestionV2.difficulty_score` capped at **200** instead of 100.
- `difficulty_tier` comment updated to include `advanced` / `expert` / `olympiad` (used by the new content).
- `load_folder` now scans for `questions.json` *and* `grade34_questions.json` in each topic folder and merges them into a single sorted topic list with a combined `difficulty_distribution`. Logs which files it loaded for each topic.
- `by_difficulty_range` default ceiling raised to 200.

**Generator (`backend/scripts/generate_grade34_content.py`, NEW)**

- 8 topic-specific generators with diverse styles per topic (e.g. arithmetic gets 3-digit add/subtract, 2-digit multiplication, simple division, missing-number fill-ins; spatial gets faces/edges/cubes-in-a-box/rotational-symmetry).
- Difficulty band 101–200 split into three tiers: `advanced` (101–130), `expert` (131–170), `olympiad` (171–200).
- Each question carries a full Socratic 6-level hint ladder with concrete numbers from the problem.
- Uses a deterministic per-topic `random.Random` seed so reruns are reproducible.

**Output**

- `content-v2/topic-{N}-…/grade34_questions.json` — exactly **300 questions per topic**, IDs `Tx-0601` … `Tx-0900`. Total **2,400 new questions**.
- After merge, every topic now has 900 questions spanning difficulty 1–200.

```
counting_observation: 600 + 300 = 900 (1-200)
arithmetic_missing_numbers: 600 + 300 = 900
patterns_sequences: 600 + 300 = 900
logic_ordering: 600 + 300 = 900
spatial_reasoning_3d: 600 + 300 = 900
shapes_folding_symmetry: 600 + 300 = 900
word_problems_stories: 600 + 300 = 900
number_puzzles_games: 600 + 300 = 900
```

**Notes / caveats for review**

- These are programmatically generated. They follow the schema and have proper hint ladders, diagnostics, and tags, but the stems are templated. Worth a content-quality pass before shipping to real Grade 3-4 students — especially for puzzles and word-problem variety.
- No SVG visuals attached for the new questions — the existing visual_registry hasn't been extended for G3-4 yet. That's a separate content task.
- `manifest.json` was *not* updated — the loader auto-discovers files. If you want the manifest to reflect 900-per-topic, that's a quick edit.

---

## Other touched files (full list)

```
backend/app/main.py                          # registered onboarding/parent/learning_path routers
backend/app/api/questions_v2.py              # feedback endpoints + use_learning_path flag, grades 3-4
backend/app/api/onboarding.py                # NEW
backend/app/api/parent.py                    # already existed; ran integration test
backend/app/api/learning_path.py             # already existed; wired up
backend/app/services/content_store_v2.py     # schema + multi-file loader for G3-4
backend/scripts/generate_grade34_content.py  # NEW

app/lib/services/api_client.dart             # 4 new client methods
app/lib/screens/question_screen_v2.dart      # flag button + report bottom sheet
app/lib/screens/onboarding_screen.dart       # NEW
app/lib/screens/parent_dashboard_screen.dart # NEW

content-v2/topic-{1..8}-*/grade34_questions.json  # NEW × 8
```

## What I deliberately did NOT do

- **Wire the new screens into `main.dart` / route table.** Onboarding and parent-dashboard navigation are deliberately left for you because the routing pattern depends on auth state + first-launch detection, which I didn't want to guess.
- **Build a learning-path UI screen.** API is solid and `/v2/questions/next?use_learning_path=true` already routes the kid to the right next topic. A standalone "your plan" screen would be a nice next step.
- **Update `content-v2/manifest.json`.** The loader auto-discovers, so it isn't required, but you may want it for downstream consumers.
- **Generate SVG visuals for Grade 3-4 content.** Out of scope for the morning; flagged in the section above.
- **APK build / Cloud Run deploy.** Per the task brief, anything that needs your machine is left for you.

## Quick sanity-check commands

```bash
# Start the server (loads all 7200 questions)
cd backend && KIWIMATH_V2_CONTENT_DIR=../content-v2 uvicorn app.main:app --port 8899

# Smoke-test the new endpoints
curl -s 'http://localhost:8899/v2/topics?grade=3' | jq '. | length'
curl -s 'http://localhost:8899/v2/onboarding/benchmark/questions?grade=2&count=10' | jq '. | length'
curl -s -X POST 'http://localhost:8899/v2/questions/T1-001/feedback' \
     -H 'Content-Type: application/json' \
     -d '{"feedback_type":"unclear_stem","comment":"manual test","user_id":"anand"}'
curl -s 'http://localhost:8899/v2/admin/feedback/summary' | jq

# Re-generate Grade 3-4 content if you want a different seed
cd backend && python3 scripts/generate_grade34_content.py --content-dir ../content-v2 --per-topic 300 --seed 12345
```

---

## Addendum — second sprint pass (autonomous, ~14:45 IST)

A second autonomous run hit the same task list and overlapped with the work
above. Net effect of the second pass:

- **Verified end-to-end with FastAPI TestClient** — wrote a 13-assertion smoke
  suite covering health, topics-by-grade, next-question-grade-3, onboarding
  questions for grades 1 and 3, benchmark submit, parent dashboard, learning
  path, feedback submit / list / summary, feedback validation rejection, and
  G3-4 question well-formedness. **All 13 passing.**
- **Bumped the G3-4 corpus** — added a *second* set of 300 questions per topic
  to `content-v2/topic-{1..8}-*/questions.json` via a new generator
  (`content_tools/gen_g34_questions.py`). These have 3-digit IDs (`T*-601` …
  `T*-900`); the original `grade34_questions.json` 4-digit IDs (`T*-0601` …
  `T*-0900`) coexist cleanly thanks to the regex widening. Final corpus:
  - 4,800 Grade 1-2 questions (unchanged)
  - 4,800 Grade 3-4 questions (2,400 from first pass + 2,400 from this pass)
  - **9,600 total** (vs. 7,200 documented above)
- **Patched a parent-dashboard bug** — the gamification profile returns `level`
  as a dict (`{level, name, emoji, ...}`), not an int. Fixed `parent.py` to
  unwrap it (and to read `streak_current` / `streak_longest` / `xp_total` /
  `gems` instead of the originally-assumed flat keys). Smoke test now passes.
- **Templates differ between the two G3-4 generators** — the second-pass
  generator (`content_tools/gen_g34_questions.py`) has different topic
  recipes (e.g. money counting in T1, multi-step rate × time word problems
  in T7, magic-square-style algebra in T8), so the doubling adds genuine
  variety rather than duplicates. Both generators are deterministic
  (seeded), so reruns are reproducible.

No other behaviour changed. All Flutter screens, ApiClient methods, and other
backend endpoints from the first pass remain in place.
