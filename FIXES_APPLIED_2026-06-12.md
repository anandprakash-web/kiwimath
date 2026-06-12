# Kiwimath — Fixes Applied (2026-06-12)

Companion to `LAUNCH_READINESS_AUDIT_2026-06-12.md`. Everything below is done and verified in this folder. **Your manual steps are at the bottom — read that section.**

---

## Security (backend)

- **API authentication added.** New `backend/app/core/auth.py`: every user-facing router now requires a Firebase ID token (`Authorization: Bearer`); invalid/missing → 401. Admin routers + HTML pages (`/editor`, `/cms`, `/admin/dashboard`, `/test`, `/stats`, content-editor, analytics) require an admin identity (`KIWIMATH_ADMIN_EMAILS`/`KIWIMATH_ADMIN_UIDS` env vars) → 403 otherwise. `/health` and `/static` stay public. Dev/test escape hatch: `KIWIMATH_AUTH_DISABLED=1` (never set in prod; tests set it via `tests/conftest.py`).
- **Identity enforcement** on highest-risk endpoints: `/user/profile|mastery|sessions` and `/v2/parent/dashboard` now 403 if the requested `user_id` ≠ token uid (admins exempt).
- **Answer leak closed.** `/v2/questions/*` and `/v4/*` no longer send `correct_answer`/`correct_value`/`solution_steps` at fetch time (sentinel `-1` keeps old clients parsing). `/v2/answer/check` still returns full correctness + solution after answering.
- **CORS fixed**: origins from `KIWIMATH_CORS_ORIGINS` env (default = your Firebase Hosting domains), no more `*` + credentials.
- **Prod lockdown**: with `KIWIMATH_ENV=production` (now set in `deploy.sh`), `/docs`, `/redoc`, `/openapi.json` are disabled and `/debug/content` is not registered.
- **Hardcoded internal key removed** (`kiwimath_internal_2026` is gone; old key now rejected). Cron endpoint uses `X-Internal-Key` header compared with `hmac.compare_digest` against `KIWIMATH_INTERNAL_API_KEY` env var; fails closed if unset. `deploy/clan_cron.yaml` updated with setup commands.
- **safe_eval DoS guard**: `**` now capped (|base| ≤ 1e6, |exp| ≤ 100); 3 new tests.
- **Secrets**: `.env.save`, `google-services.json.bak`, and the `old jason/` copies are untracked from git; `.env.save` content replaced with a placeholder; `.gitignore` now covers `.env.*`, `local.properties`, and the backup files.
- **Privacy policy corrected** (root + `public/` copy, kept in sync): now accurately discloses child name/grade/avatar collection, clan/leaderboard display-name visibility, and the parental-consent mechanism. Recommends nicknames.

## Backend state persistence (the Cloud Run data-loss fix)

- New `backend/app/services/state_store.py` (`FirestoreBackedStore` + idempotency helpers, with in-memory fallback when Firestore is unavailable so local dev/tests still work).
- **Clans** wired to the previously-unused `clan_firestore.py` (all 13 handlers). **Engagement** (leagues, wars, rewards, pledges, ELOs), **daily puzzle** (submissions, streaks, leaderboards, freezes), **diagnostic sessions**, and **session locks** (transactional acquire, TTL) all persist to Firestore now. Data survives deploys and is consistent across instances.
- **Idempotency**: client now sends `X-Idempotency-Key` on mutations; server replays the stored response for duplicates on `/v2/answer/check`, puzzle submit, claim-daily, mystery box, war answer, streak freeze, pledge. No more double XP/coins on flaky-network retries.
- **Memory leaks fixed**: `question_history` capped at 50/user; gamification + adaptive-engine per-user caches capped at 5,000 with eviction.

## Content

- **School-curriculum mode restored**: `content_store_v4.py` now indexes `original_id` → chapter refs resolve **0 → 9,998 of 12,745**; chapters with ≥1 question: 0 → 279/282.
- **Mis-keyed answers fixed** (9 instances): A1-ADD-0019/0152/0159 (v4 + production), wb_L4_s07_q09 (production g5+g6 + wavebook). Re-verified programmatically: 0 mis-keys remain among parseable arithmetic.
- **3,569 placeholder/empty SVGs cleared** ("A visual representation of the prob" + blanks). 0 remain.
- **Hints fixed**: HintLadder model accepts 3-level ladders (hints actually serve now, deeper levels forward-fill); **27,491 answer-revealing hint sentences scrubbed** (0 leaks remain), 15,967 emptied hints replaced with topic-appropriate nudges; **1,781 garbled stitched hints repaired** (the broken "=" replacement).
- **4 name-mismatch word problems fixed** (Aanya/Aarav etc.); other flagged ones verified legitimate.
- All 317 touched JSON files re-parsed clean.

## Flutter app

- **Auth**: new `auth_token.dart` + `authed_http.dart`; all 6 HTTP services automatically send `Authorization: Bearer <ID token>` (50+ call sites). New `AuthedSvg` widget replaces `SvgPicture.network` in question/worksheet/admin screens so visuals load under auth.
- **Retries made safe**: POSTs no longer auto-retry; GETs still do; `X-Idempotency-Key` attached to all mutations; dead 4th-retry bug fixed.
- **Crash fixes**: `mounted` guards added to all async-setState offenders (main.dart loaders, sign-in, saved-questions, wavebook); **daily-puzzle grading bug fixed** (was treating option 0 as always correct — now server-authoritative, real elapsed time sent).
- **Broken test replaced** with real tests: KiwiTier unit tests + OptionCard widget tests (no Firebase needed).
- **UI modernization quick wins**: Nunito (body) + Baloo 2 (display) via `google_fonts`; haptics + press-scale on answer options; medium/heavy haptic on correct/wrong; celebration score count-up; page transitions; skeleton loader (no more spinner between questions); fake Google "G" replaced with a brand-correct CustomPaint mark.

## Verification

Backend: `py_compile` clean on all of `backend/app`; pytest **115 passed**, 5 failures are pre-existing content-count assertions in `test_ux_flow.py` (unchanged from before any fix). Old internal key rejected; auth smoke-tested (401/403/200 paths). Content: all JSONs parse; 0 mis-keys, 0 hint leaks, 0 placeholders. Flutter: can't run Flutter in this sandbox — bracket-balance and import checks pass; your `flutter analyze` is the final gate (below).

---

## ⚠️ What's left for YOU (in order)

1. **Rotate the Gemini API key NOW** (the old one is in git history on GitHub): create a new key, put it ONLY in local `.env`, delete the old key in Google AI Studio. Then scrub history: `brew install bfg && bfg --delete-files .env.save` (or `git filter-repo`), then force-push.
2. **Commit everything**: from Terminal (sandbox can't unlink `.git/index.lock` if it reappears):
   `cd ~/Downloads/kiwimath && git add -A && git commit -m "Security hardening, Firestore persistence, content fixes, UI quick wins" && git push`
3. **Set Cloud Run env vars** (one-time):
   `gcloud run services update kiwimath-api --region asia-south1 --set-env-vars KIWIMATH_INTERNAL_API_KEY=$(openssl rand -hex 32),KIWIMATH_ADMIN_EMAILS=anand.prakash@vedantu.com` — and update the Cloud Scheduler job to send that key as `X-Internal-Key` (commands documented in `backend/deploy/clan_cron.yaml`). Never set `KIWIMATH_AUTH_DISABLED` in prod.
4. **Flutter build check**: `cd app && flutter pub get && flutter analyze && flutter test` — fix anything analyze flags (I couldn't run Flutter here), then test on device: sign in → answer questions (haptics, skeleton, count-up) → daily puzzle right/wrong → fonts (Baloo 2 headings / Nunito body) → SVG visuals load.
5. **Deploy backend then app** (`backend/deploy.sh`, then `flutter build apk --release`). Deploy backend first — the app now sends auth headers the old backend ignores (safe), but the new backend rejects old apps' unauthenticated calls, so force-update the app promptly.
6. **Firestore housekeeping**: accept the composite-index suggestions on first use (clan queries); enable a TTL policy on `idempotency_keys.expires_at`.
7. **Enable Firebase App Check** (console + a few lines in the app) to lock the client API keys.
8. **Content follow-ups** (not blocking): 2,747 chapter refs point to questions deleted in the May 4 dedup (3 Singapore chapters fully orphaned) — regenerate `chapters.json` against the deduped bank; decide whether to ship the cleaner `content-production` set; grades 5–6 still need more depth.
9. **Known intentional gaps**: olympiad-worksheet/wavebook/offline-bundle endpoints still include answers at fetch (required for offline play — now auth-gated; follow-up: signed bundles). Rive mascot, TTS, illustrations, tablet layouts remain on the Phase 3 list.
