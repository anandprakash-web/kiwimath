# Adaptive Rule Set — skill-ladder engine (2026-06-17)

The adaptive practice rule, built on the concept clusters. **Skill question** = the cluster's canonical parent; **cluster questions** = its number/wording variants. Implemented, wired into `/v3`, and verified (18/18 adaptive tests + 17/17 smoke).

## The rule

Per **(level, topic)** the skills form a **difficulty ladder** (ordered by the skill question's difficulty). For each rung:

1. Show the **skill question**.
2. **Correct** → advance to the **next skill** (its cluster questions are *not* shown).
3. **Wrong** → show the next **cluster question**, and keep dripping them one at a time until
   - one is answered **correct** → advance to the next skill, or
   - the cluster is **exhausted** → advance to the next skill anyway.

The student's position is **remembered**: on the next login they resume on the exact question they were on — the engine never jumps back to skills already cleared.

```
skill 0 ── correct ──────────────► skill 1 ── correct ──► skill 2 ...
   │                                  │
  wrong                              wrong
   ▼                                  ▼
 cluster q1 ─ correct ─► skill 1    cluster q1 ─ wrong ─► cluster q2 ─ correct ─► skill 2
   │ wrong                                                   │ wrong (last)
   ▼                                                         ▼
 cluster q2 ... exhausted ─► skill 1                       skill 2  (exhausted)
```

## Difficulty tagging (the ladder)

Every question now carries (additive — **0 existing-field changes**, re-run idempotent via `content-live/qa-reports/cluster_concepts.py`):

| Field | Meaning |
|-------|---------|
| `skill_id` | the concept cluster |
| `is_skill_original` | `true` on the **skill question** (one per cluster) |
| `skill_rank` | order **within** a cluster (0 = the skill question, then cluster questions by difficulty) |
| `skill_seq` | the skill's **position on the topic ladder** (0 = easiest skill) |
| `skill_difficulty` | the skill question's difficulty — **every cluster question inherits it**, so the whole cluster sits at one rung |

So within a topic: skills are arranged by `skill_seq`; inside a skill the order is `skill_rank` (parent first).

## Engine + persistence

`backend/app/services/adaptive_skill.py` — `AdaptiveSkillEngine`:
- Builds the per-(level, topic) ladder from the tags (cached).
- `next_qid(user, level, topic)` — the current question (pure read; never advances).
- `record(user, level, topic, qid, correct)` — advances per the rule; **monotonic** (a re-answered earlier question can't drag the student back).
- `status(...)` — `{skills_total, skill_index, on_cluster_question, completed}`.

State lives in **`FirestoreBackedStore("adaptive_skill_state")`** — one Firestore doc per user, `{ "L4|geometry": {pos, cursor}, ... }`. Firestore = durable across logins/instances; in-memory fallback for local/tests. **This is what makes re-login resume work.**

## API wiring (`backend/app/api/level.py`)

- `GET /v3/olympiad/levels/{level}/topics/{tk}/next?user_id=…` — **default `mode=skill`**: returns the student's current rung question + an `adaptive` block (`skill_index` etc.). `mode=irt` or no `user_id` falls back to the older ZPD/IRT selection.
- `POST /v3/answer/check` — after grading, calls `engine.record(...)` to advance + persist, and returns the new `adaptive` status.
- `GET /v3/olympiad/levels/{level}/topics/{tk}/adaptive-status?user_id=…` — the saved rung, for a "resume where you left off" UI.

The economy / IRT / proficiency updates are untouched — the skill engine runs alongside them.

## Verified (`backend/tests/smoke_adaptive_skill.py`, 18/18)

skill-correct → next skill (cluster skipped) · skill-wrong → cluster drip · cluster-correct → next skill · cluster-exhausted → next skill · **fresh engine resumes the same question (re-login, no jump back)** · no-regress on re-answering cleared skills · full API round-trip (next → answer/check → next) with status flowing. Existing v3 smoke stays **17/17**, pre-deploy green (olympiad 20,013 unchanged).

## Ship

Backend change (content tags baked in + new service/endpoints):
```
cd ~/Downloads/kiwimath/backend && ./deploy.sh
```
The current app already sends `user_id` to `next` and `answer/check`, so the rule activates on deploy — **no APK rebuild required** for the behaviour. (Optional app polish: show "Skill X of Y" from the `adaptive` block, and hide the manual forward/skip in skill mode since answering is what advances.)

## Notes / tunables
- Ladder order ties (same difficulty) break by `skill_id` for stable, deterministic sequencing.
- Topic completion (all skills cleared) returns 404 "Topic complete"; if you'd rather loop for endless practice, that's a one-line change in `next_qid`.
- Same engine works for curriculum chapters later (the tags already exist there too).
