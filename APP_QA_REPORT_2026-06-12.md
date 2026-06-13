# Kiwimath — Full App QA (Tabs, Branching, Content↔UI Integration) + Fixes

**Date:** 2026-06-12 · **Method:** complete static navigation trace of every tab/branch + live integration replay of all 112 API calls the app makes, against the real content. Then a full fix pass. Re-runnable harness: `qa-reports/app_integration_test.py`.

---

## Why content wasn't showing up (your exact symptom)

Three independent breaks, all now fixed:

1. **DPP/Daily tab had zero content.** Its 600 worksheet files (`g{N}_olympiad_batch*.json`) were **never committed to git** — they only existed on your Mac, and today's redeploy shipped an image without them. → **Regenerated all 600 worksheets (7,200 questions)** from the QA-verified question bank, same schema, answers copied verbatim, plus the SVG renderer sidecar. Verified live: 100 worksheets per grade, full 12-question days, visuals serve.
2. **School tab was querying the wrong bank.** It called the old `/v2/chapters` path (10 usable chapters total; Singapore rejected at load; USCC folder doesn't exist) while the real school bank — 282 chapters / 19,919 questions across 5 curricula — sits in v4 behind an endpoint that 500'd on every chapter (`q.options` vs `q.choices` bug). → **Fixed the endpoint, rewired the School tab to the v4 bank**, added US Common Core to the curriculum chips, 0-question chapters now show "Coming soon" instead of erroring, and `/v2/answer/check` now resolves v4 questions so answers check correctly. Also fixed the loader so the 325 Singapore SMC questions load (id format + letter answer keys).
3. **Every Practice-tab picture 404'd.** 3,846 questions store inline SVG but the visual endpoint only looked for files on disk. → Endpoint now serves inline SVG directly. Verified: 200, `image/svg+xml`.

## Other bugs found and fixed

**Backend:** `POST /v2/session/unified/complete` crashed (500) on every smart-session finish (dict treated as object) — fixed and verified. Benchmark tests returned 16/20 questions — now always 20, and a None-IRT crash the fix exposed is handled. Day-1 users got a 404 claiming their first daily reward — now initialized on first claim.

**App wiring (the "navigation changes" you noticed are the new 4-tab shell; these were its loose ends):**
- Saved tab → solving a saved question always failed (field-name mismatch) — fixed.
- "Daily Challenge" card on Practice was a dead button — now opens the daily puzzle.
- Parent dashboard: ran diagnostics with hardcoded Grade 1 for every child — now uses the real grade; clan section always said "not in a clan" — now receives real clan data; had no back button — close (X) added.
- Onboarding only offered grades 1–5 — Grade 6 added.
- "Got it, next question →" button didn't advance to the next question — now it does.
- Avatar circle dead tap → now jumps to the Me tab. Saved tab's dead back-arrow hidden.
- Two Dart↔API contract mismatches that crashed/blanked clan features (pledges response shape, daily-puzzle hint field names) — fixed.

## Known-and-deferred (no action needed for launch)

- **Clan system is built but not surfaced** in the 4-tab shell (clan hub, wars, rewards, leaderboard screens exist and the backend works — verified live — but only the daily puzzle is reachable via the Daily Challenge card). Surfacing clans in the Progress tab is a product decision + half-day of UI work.
- 15 orphan screens remain in the codebase (old home/learning-path/companion-picker etc.) — dead weight, not harmful.
- Grade chips don't persist to the profile (resets to onboarding grade on restart); two different streak counters share one flame icon; wavebook still grades client-side. Listed in the navigation trace for a post-launch pass.
- The old curated DPP worksheets are still extractable from your previous Cloud Run image if you ever want them instead of the regenerated ones (`gcloud run revisions list`, pull the previous image, copy `/app/content/olympiad/`).

## Verification

Backend: 115 tests passed (same 5 pre-existing content-count failures, no new); full integration replay green — every tab's endpoints return parseable, non-empty content: Practice (topics, sessions, answers, hints, visuals, completion), DPP (600 worksheets), School (all 5 curricula serving chapters+questions+answer-check), Clan core+puzzle (idempotent double-submit verified), Growth (journey, 20-question grade-filtered benchmarks), Parent, Profile. All 11 edited Dart files balance-checked (no Flutter SDK in sandbox — run `flutter analyze` as the final gate).

## Your deploy steps (both sides changed)

```bash
cd ~/Downloads/kiwimath
git add -A && git commit -m "App QA: fix DPP content, School tab v4 wiring, visuals, session completion, dead flows" && git push
cd backend && ./deploy.sh          # ships regenerated worksheets + endpoint fixes
cd ../app && flutter analyze       # expect 0 errors
flutter build apk --release        # then install + smoke test on device
```

On-device check: Practice → question with a picture (loads now) → finish a session (no error at the end now). DPP/Daily → worksheets listed for your grade. School → all 5 curricula chips → chapters with counts → answer a chapter question. Progress → run diagnostic (20 questions). Me → Parent (PIN) → X closes, diagnostic uses the right grade.
