# Pre-deploy code QA — adaptive skill-ladder (2026-06-18)

Full review of the adaptive feature before deploy: the engine, the endpoint wiring, the content tags, plus an **independent subagent code review**. Verdict at the bottom.

## Scope (what's shipping)
- `content-live/qa-reports/cluster_concepts.py` — now emits `skill_seq` + `skill_difficulty`.
- 30,349 questions re-tagged (additive skill fields only).
- `backend/app/services/content_store_level.py` — `LQ` exposes the skill fields.
- `backend/app/services/adaptive_skill.py` — **new** engine + persistent state.
- `backend/app/api/level.py` — `/next` (skill mode), `/answer/check` (records), new `/adaptive-status`.

## Checks performed
| Check | Result |
|------|--------|
| `py_compile` all changed files | ✅ |
| Full app import (route table) | ✅ 265 routes, no collisions |
| Data integrity — tags complete | ✅ 30,349 q, **0 missing fields** |
| Data integrity — cluster consistency | ✅ 0 seq/difficulty disagreements; exactly 1 `is_skill_original`/cluster; original is `skill_rank 0`; every ladder contiguous `0…N-1` |
| Existing-field integrity | ✅ tagger reports **0** core-field changes |
| Engine edge cases | ✅ empty/nonexistent topic, completed, bad qid, double-submit, size-1 cluster, malformed stored cell |
| Security — answer leak | ✅ `_q_public` omits `correct_answer`/`correct_value` |
| Security — identity binding | ✅ cross-user `/next` & `/adaptive-status` → **403** (see fix #1) |
| Regression — `smoke_adaptive_skill` | ✅ **18/18** |
| Regression — `smoke_level_v3` | ✅ **17/17** |
| `pre_deploy_check` | ✅ olympiad 20,013 unchanged, ALL CHECKS PASSED |
| Deploy bundling | ✅ Dockerfile `COPY . .` includes new service; `deploy.sh` bakes tagged content; **no new deps** |

## Findings → fixes applied
The subagent flagged a "FIX FIRST" verdict on two items; both are now fixed and re-verified.

1. **[major → fixed] IDOR on `/olympiad/.../next`.** Took `user_id` but never bound it to the token — any signed-in user could *read* another's ladder position (read-only; `/next` doesn't mutate). **Fix:** added `Depends(verify_token)` + `assert_user_match(decoded, user_id)`. Verified: own→200, other→**403**, no-user IRT path still 200.
2. **[major → hardened] Non-transactional `record()` could regress under concurrent/out-of-order writes.** `FirestoreBackedStore` isn't transactional. In practice the app **serialises** answers (awaits each `/answer/check` before showing the next), and the `si < pos` guard already blocks re-answering cleared skills. **Fix:** added a **re-read monotonic guard** — re-reads the saved position immediately before writing and refuses to persist a lower one. Verified: forcing `(skill 5, cursor 2)` then answering the skill-5 parent wrong does **not** regress to cursor 1. Residual sub-millisecond TOCTOU is accepted (consistent with the store's documented last-write-wins policy).
3. **[nit → fixed] `_get_pos` could 500 on a malformed stored cell.** Wrapped in safe int parsing (`int(x or 0)` with try). Verified: a `{"pos":"oops","cursor":null}` cell no longer crashes `status`/`next`.
4. **[nit → fixed] `/adaptive-status` had no error guard.** Wrapped so a read error returns a fresh/empty ladder instead of 500.

## Residual / follow-ups (not blockers for this deploy)
- **⚠️ Ladder versioning before any future re-cluster.** Saved positions are integer indices into the per-topic ladder. **This deploy is safe** (the `adaptive_skill_state` collection is brand-new — no user has a saved position yet). But if `cluster_concepts.py` is re-run *after* users have progress (e.g. when L8 or new content is imported and the ordering shifts), stored indices would point at different skills. **Before the next re-cluster, add a ladder version/hash stored with the position and reset on mismatch.** Flagged as the #1 follow-up.
- **Silent IRT fallthrough** if a ladder qid ever fails to resolve (`get(qid)` → None). Extremely low risk (content is static after boot); acceptable.
- **App polish** (optional, no rebuild needed for behaviour): show "Skill X of Y" from the `adaptive` block; in skill mode the manual forward/skip just re-shows the current question, so consider hiding it.

## Verdict: ✅ SAFE TO DEPLOY
Both blocker-grade findings fixed and re-verified; data integrity perfect; 18/18 + 17/17 + pre-deploy green; deploy bundling confirmed; no new dependencies.

```
cd ~/Downloads/kiwimath/backend && ./deploy.sh
```
Backend-only (content tags baked in + new service/endpoints). The app already sends `user_id` to `/next` and `/answer/check`, so the skill ladder activates on deploy — **no APK rebuild required**.
