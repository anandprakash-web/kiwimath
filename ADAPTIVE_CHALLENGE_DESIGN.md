# The Climb — adaptive Challenge (GRE/GMAT-style mini-CAT)

*Design for review. Build only on your nod. 2026-06-28.*

## Why this, for this audience
Your real users are the curious math-lover and the child of a serious parent. They burn
through easy content and get bored if made to grind. A CAT (computer-adaptive test, the
GMAT engine) does one thing brilliantly: it **finds the exact edge of your ability and
keeps you there**, then reports **how high you reached**. That is catnip for a gifted kid
("how high can I climb?") and a credible signal for a serious parent.

It does **not** replace the skill-ladder. The ladder = *Practice to learn* (the moat).
The Climb = *a separate challenge that measures and stretches*. Two jobs, two surfaces.

## The good news: the engine already exists
`app/assessment/irt_model.py` is a complete 3PL CAT toolkit — I verified it:
- `ItemParameters.information(θ)` → Fisher information (this is how a CAT picks the next item)
- `estimate_ability_eap(items, responses)` → ability θ **and** its standard error (SE)
- `AbilityEstimate.is_converged` → SE < 0.30 stop signal
- `proficiency_levels.theta_to_scale_score(θ)` → the **200–800 scale the Progress tab already shows** (so the Climb rating reconciles with Progress — no disjoint)

So this is assembly, not invention. The loop:
1. **Start** at the learner's current Progress level (warm start — no cold, friendly).
2. **Ask** an item near that ability.
3. **Re-estimate** θ + SE from all answers so far (EAP).
4. **Pick next** = the unseen item with the most information at the current θ (light
   exposure control so everyone doesn't see the same 3 items).
5. **Stop** at convergence or the length cap.
6. **Score** θ → 200–800 "Climb rating" + a friendly band (Explorer → … → Legend) and a
   peak-altitude visual.

Built as a **new** `challenge_service.py` + `/v3/challenge/*` endpoints + a Flutter screen.
It touches **no** content, **no** skill/cluster tags, **no** ladder engine → passes the
ship gate untouched.

## The one honest caveat (you'll want this straight)
Our item difficulties (`irt_b`) are **heuristic, not empirically calibrated**, and we have
no per-item discrimination yet (`a` defaults to 1.0, `c`≈0.2 for MCQ). A CAT is only as
sharp as its calibration. So for v1:
- It still **works** — it targets the edge using the best difficulty we have, which makes
  the experience genuinely adaptive from day one.
- We present the rating **modestly** — "Climb rating, sharpens as you play" — **not** a
  validated percentile.
- Every Climb logs responses to feed `scripts/irt_calibrator.py`. As your serious users
  play, item parameters get **real** calibration → the CAT gets sharper. **That response
  data is itself a moat** — a competitor can't copy it.

## Decisions that are genuinely yours
1. **Length / stop rule** — (a) fixed 10 questions (predictable, kid-friendly) — *my pick
   for v1*; or (b) adaptive 6–15, stop when confident (more precise, variable time).
2. **How loud is the score** — show the 200–800 rating + band to everyone — *my pick*; or
   keep the number on the parent dashboard and show kids only the altitude/band. Given the
   calibration caveat, I'd keep copy modest either way.
3. **Cadence** — unlimited Climbs, track your **best** rating — *my pick for v1*; a daily
   "rated" Climb (like the contest) can come later.

(Warm-start from Progress, 200–800 scale reuse, and moat-safety are not up for debate —
they're the consistency-correct choices.)

## Build plan (on your nod) — small, gated
1. `challenge_service.py` — pool from a level's `irt_b`, EAP loop, max-info select,
   exposure control, SE/length stop, θ→scale, per-user best in `FirestoreBackedStore`.
2. `/v3/challenge/start`, `/submit` (returns next item or final result), `/me` (best/history)
   — `assert_user_match`, no answer leak mid-test.
3. `tests/smoke_challenge.py` — convergence on a simulated high/low learner, no-leak,
   resume, scale matches Progress.
4. Flutter `challenge_screen.dart` — the Climb: altitude visual, one item at a time,
   result card; entry point near Compete on the Olympiad home.
5. `./ship_gate.sh` green + the new smoke green → then deploy.

Calibration (`irt_calibrator.py` on accumulated responses) is a **follow-on**, not a
launch blocker.
