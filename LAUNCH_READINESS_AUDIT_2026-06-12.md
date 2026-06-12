# Kiwimath — Launch Readiness Audit

**Prepared for:** Anand Prakash · **Date:** 2026-06-12
**Scope:** Full folder review — backend code, security, content JSONs, app UI/UX — plus next steps and a public launch plan.

---

## Verdict in one line

The product is substantial and the ideas are strong, but **it is not launch-ready today.** There are five launch-blocking issues: (1) the backend stores all social/streak/reward state in process memory on a multi-instance Cloud Run service, so it is lost on every deploy and inconsistent across instances; (2) the API has **no authentication at all** — anyone can read or overwrite any child's data; (3) a **live Gemini API key is committed to git**; (4) the entire school-curriculum mode returns **zero questions**; and (5) **68% of hints give away the answer** while the 6-level hint system never actually runs. None of these are cosmetic. Realistic path to a safe public launch is **4–6 weeks** of focused work.

Overall readiness: **Backend 4/10 · Security 2/10 · Content 5/10 · UI/UX 4.5/10.**

---

## 1. Critical tech gaps (code)

The backend is architected like a single-process prototype but is deployed to scale horizontally (`deploy.sh`: `--max-instances 10 --concurrency 80`). That mismatch is the root of most issues.

**Launch-blockers**

1. **In-memory state on a multi-instance service.** Clans, leagues, daily-puzzle streaks, leaderboards, rewards, pledges, diagnostic sessions and session locks all live in module-level dicts — `engagement.py:74`, `daily_puzzle.py:48`, `clans.py:50`, `assessment.py:42`, `session_lock.py:58`. They reset on every deploy and differ per instance, so a child's streak/clan/points read as zero on the next request that lands on another instance. A complete Firestore layer (`clan_firestore.py`) already exists but **is never imported** — it's dead code.
2. **Correct answers are shipped to the client.** `questions_v2.py:110` returns `correct_answer`, `correct_value`, and `solution_steps` with the question — the code even comments "should NOT be sent to client." The whole adaptive/reward economy is trivially gameable.
3. **Per-user caches never invalidated; writes are non-transactional read-modify-write.** `adaptive_engine_v2.py:384`, `gamification.py:1342` — two instances/devices for the same child permanently diverge on ability, coins, gems, streaks; last writer wins, silently corrupting the model. Also a slow memory leak (`question_history` grows unbounded, `gamification.py:1216`, and is never even persisted).
4. **Hottest endpoint does ~6 sequential blocking Firestore writes per answer** in a sync handler (`questions_v2.py:519`), with `response_logger` committing a batch per single answer. Latency stacks and the threadpool exhausts under load.
5. **Client retries non-idempotent POSTs** (`api_client.dart:41`) with no server-side idempotency keys → double XP/coins/streak on flaky networks, exactly the conditions of the India launch market.
6. **Offline mode is dead code.** `OfflineStore.queueResponse`, `fetchWithCache`, `DownloadsScreen` are never called; the "Offline mode — will sync" banner (`main.dart:188`) is a promise nothing fulfills. The connectivity service also imports `dart:io`, breaking the web target.
7. **No observability and no test safety net on the client.** No Crashlytics/Sentry; errors swallowed with `debugPrint`/`catch (_) {}`. The single Flutter test references a non-existent `MyApp` (`widget_test.dart:17`) so the suite doesn't even compile. Backend has zero tests for the actual production paths (adaptive engine, gamification, clans, puzzles).
8. **`setState` after `await` without `mounted` guards** across `main.dart` (`_loadClan`, `_loadEngagementData`, `_loadLeaderboard`) → "setState after dispose" crashes on navigation.

**High** · No CI/CD anywhere (manual `deploy.sh` that *mutates the Dockerfile at deploy time*) · 4 near-duplicate curriculum stores + 2 adaptive engines + 3 question APIs (heavy duplication, two sources of truth) · `/debug/content` publicly dumps env vars + filesystem · admin analytics read instance-local caches so numbers undercount and reset each deploy · version drift (pubspec 1.4.0 vs build script 1.2.0 vs API 2.0.0).

---

## 2. Security gaps

This is the weakest dimension and the most urgent, because it's a children's app (COPPA-relevant).

**Critical**

- **C1 — No authentication on any endpoint.** Zero `Depends`/`verify_id_token` in the entire backend. Identity is a client-supplied `user_id` query param. The production URL ships in the app and no `Authorization` header is ever sent. Anyone can enumerate Firebase UIDs and read or overwrite any child's profile and parent dashboard (`user.py:77`, `parent.py:198`). This is an unauthenticated PII read/write on a kids' app — the single biggest risk.
- **C2 — Admin and content-editor endpoints fully exposed.** `/editor`, `/cms`, `/admin/dashboard` serve admin HTML with no auth; `PUT /content-editor/questions/{qid}` rewrites question files unauthenticated (`content_editor.py:132`); `POST /admin/purge-and-reimport` can wipe content. Anyone on the internet can edit what children see.
- **C3 — CORS `allow_origins=["*"]` with `allow_credentials=True`** (`main.py:72`) — broken origin policy.
- **C4 — Hardcoded internal secret** `kiwimath_internal_2026` in `clans.py:639`, passed as a URL query param (so it's logged).
- **C5 — Live Gemini API key committed to git** in `.env.save` (tracked; `.gitignore` only covers `.env`). It's in history and on the GitHub remote. **Rotate immediately.**

**High** · `safe_eval` blocks RCE but allows unbounded `**` → `9**9**9` DoS (`safe_eval.py:50`) · parental PIN stored plaintext in SharedPreferences with no lockout (`pin_gate.dart`) · **privacy policy contradicts reality** — it says "we do NOT collect names/ages/DOB" but the app collects `child_name`, grade, and emails (direct COPPA/FTC exposure) · `/debug/content` and Swagger `/docs` exposed in prod.

**Good, for the record** · `firestore.rules` are solid (per-user scoping, default-deny) — but the Admin SDK backend bypasses them, so they don't protect the real data path · Android manifest is clean (INTERNET only, no cleartext in release, minify+proguard on) · keystore/`key.properties` correctly not committed · Firebase `google-services.json` keys are client-side by design (lock down with **Firebase App Check** + API key restrictions rather than hiding).

---

## 3. Content JSON gaps

**What's actually served:** the Dockerfile bakes in **content-v4/** and **content-v2/** (20,056 + 8,308 questions). The cleanest set, **content-production/ (29,504 questions, schema 5.0), is NOT wired to the backend at all** — it's orphaned. This is the most important finding: a better, cleaner content set already exists and isn't being used.

**Critical**

- **School-curriculum mode is 100% broken.** All 12,745 chapter→question references dangle because questions were renamed (e.g. `NCERT-G1-045` → `A1-TIM-0006`, old ID kept only in `original_id`) but `content_store_v4.get_chapter_questions()` looks up only new IDs. Every chapter of every curriculum returns 404. **One-line fix: also index `original_id`.**
- **Curriculum banks are stubs:** NCERT 11 questions, ICSE 5, IGCSE 58, Singapore 325; `us-common-core` is referenced by the Dockerfile but **the directory doesn't exist**.
- **Hints reveal the answer:** 13,658/20,056 (68%) served hints contain "the answer is X". Separately, all ladders have only 3 levels but the backend model requires 6, so `hint_ladder()` returns None for **every question** — the Socratic system is dead. (The orphaned content-production set is already cleaned to 23% leak.)
- **Mis-keyed grade-1 answers:** `A1-ADD-0019` (7+2+1 keyed 9, should be 10), `A1-ADD-0152` (4+4+1 keyed 8→9), `A1-ADD-0159` (3+3+3 keyed 6→9), plus `wb_L4_s07_q09` in the production set. Overall error rate is low (0.15%) but these are front-facing.

**High** · 1,739 questions ship a placeholder SVG whose text reads "A visual representation of the prob" + 19 empty SVGs; only 48% of v4 have real visuals · grades 5–6 have ~half the depth of 1–4 (g5 2,146 / g6 1,732), several near-empty topics (g5-patterns has 31) · inconsistent difficulty-tier taxonomy across grades breaks adaptive banding · 538 garbled machine-stitched hints and 22 word problems where the character names don't match ("Aanya has 2 apples… how many does Aarav have?").

**Clean:** no duplicate IDs in served sets, no encoding/mojibake, no duplicate choices, healthy answer-position distribution.

---

## 4. UI/UX — is it ultra-modern?

**No — 4.5/10.** Well-architected design system, visually under-produced. It reads as a competent 2019 Material app with emojis. Three things hold it back: **no bundled assets at all** (the `assets/` dir doesn't exist — no fonts, illustrations, Lottie/Rive, or sound), **no motion stack** (pubspec has nothing beyond `flutter_svg`), and **the mascot is a placeholder** — a colored circle with the character's initial (`companion_view.dart:173` literally says "beautiful placeholder"). Against Duolingo ABC / Khan Academy Kids, where the character *is* the product, it reads as a prototype.

**Already good:** real token system (`kiwi_theme.dart` — tier colors, 4px spacing grid, Material 3 on, grade-adaptive theming), pedagogy-aware UX (hint ladder, scaffolded wrong-answer sheet, broken-question auto-skip), tasteful hand-rolled micro-motion, COPPA-correct parent-first sign-in, kid-appropriate copy.

**Top modernization moves (ranked):**

1. **Ship fonts — the typography system is dead code.** `KiwiTierTypography` names Nunito/Poppins but pubspec has no fonts and no `google_fonts`, so everything falls back to Roboto. Bundling Nunito + a rounded display font (Baloo 2/Fredoka) is ~1 hour and the single biggest visual delta.
2. **Replace the placeholder mascot with an animated Rive character** (idle/think/celebrate/sad). The whole companion system is built and starving for art — #1 gap vs competitors.
3. **Make celebrations celebrate** — confetti + count-up + haptic + star rating (`celebration_screen.dart` is currently an emoji fade-in).
4. **Kill blocking spinners, add skeleton shimmers** (30+ raw `CircularProgressIndicator`s; worst: a modal spinner before Smart Session, `main.dart:949`).
5. **Haptics + press physics in the answer loop** (`option_card.dart` has neither — the most-tapped widget).
6. **Wire grade-adaptive theme into MaterialApp** (currently hardcoded to grade 1, so the senior tier never reaches `ThemeData`) + modern page transitions.
7. **Duolingo-style pressable 2.5D buttons** as one reusable component.
8. **Audio/TTS for pre-readers** — there's zero audio; a Grade-1 child can't read the stems. `flutter_tts` + a speaker button is table stakes for K-2.
9. **Real brand assets** — the Google sign-in button is a fake "G" Text widget (a Google branding-policy violation that can fail review); logo is a letter in a box.
10. **Responsive + accessibility pass** — tablets get stretched 2-column grids; only 2 `Semantics` widgets in the whole app.

Quick wins (days): #1, #3, #4, #5, #6, #7. Bigger (needs art/audio production): #2, #8, #9, tablet layouts.

**Bonus bug found:** `daily_puzzle_screen.dart:103` treats option index 0 as always correct, so the daily puzzle mis-grades whenever the right answer isn't first.

---

## 5. Next steps — prioritized plan

### Phase 0 — Emergency (this week, before anything else)
1. **Rotate the Gemini key**, `git rm --cached .env.save`, gitignore `.env*`, scrub git history (BFG/filter-repo).
2. **Rotate** `kiwimath_internal_2026`; move to Secret Manager; pass via header.
3. **Disable `/debug/*` and `/docs`** in production; lock CORS to known origins.
4. Take the **admin/editor endpoints off the public service** immediately (IAP or kill the routes).

### Phase 1 — Launch blockers (Weeks 1–3)
5. **Add Firebase ID-token verification** as a FastAPI dependency on every non-public route; derive identity from the token, never from params. Attach `Authorization: Bearer <idToken>` in the Flutter client. Gate admin routes behind an admin-UID allowlist.
6. **Persist all in-memory state to Firestore** — wire up the existing `clan_firestore.py`, move engagement/puzzle/session/lock state off module dicts. Make reward writes transactional; add idempotency keys for answer/reward POSTs.
7. **Stop sending correct answers to the client**; validate answers server-side only.
8. **Content swap:** deploy the cleaned **content-production** set (cuts hint leak 68%→23%) *or*, faster, fix the two regressions on the current set: index `original_id` (restores 12,745 school-curriculum refs) and strip the 1,739 placeholder SVGs. Fix the 4 mis-keyed grade-1 answers. Decide: 3-level or 6-level hints, and make the model match the data so hints actually render.
9. **Fix the privacy policy** to match real data collection; confirm the parental-consent mechanism.
10. **Add Crashlytics**, fix the compiling test, add `mounted` guards, fix the daily-puzzle index-0 bug.

### Phase 2 — Quality & modern feel (Weeks 3–5)
11. UI quick wins: fonts, skeletons, haptics, pressable buttons, confetti, grade-theme wiring.
12. Backend hygiene: move the 6 per-answer writes to batched/async, add response-log rollup/TTL, delete the duplicate curriculum stores and superseded APIs, add CI (GitHub Actions: flutter test + pytest + build).
13. Fill the grade 5–6 content gaps and the near-empty topics; normalize difficulty tiers across grades.

### Phase 3 — Differentiation (Weeks 5–6+)
14. Rive mascot, TTS/audio, illustration system, tablet layouts, path/map home metaphor.

---

## 6. Public launch plan

**Recommended shape: a staged soft launch, not a big-bang public release.** The content and pedagogy are good enough that a controlled rollout will generate real signal while the hardening lands.

**Gate 0 — Security & data integrity sign-off.** No public traffic until Phase 0 + items 5/6/7 are done and verified (auth on every route confirmed, state survives a deploy, answers no longer leak). This is non-negotiable for a kids' app.

**Stage 1 — Private beta (Week 4, ~50–100 families).** Internal + friendly families via Play Console **closed testing** track. Goals: validate persistence across deploys, crash-free rate (target >99%), answer-check latency, and that streaks/clans actually survive. Instrument with Crashlytics + basic analytics first.

**Stage 2 — Open beta / regional soft launch (Week 5–6, single region).** Play Console **open testing** or a geo-limited production release (one Indian state). Watch retention D1/D7, hint usage, content flag rate, and infra cost per active child. This is where the content depth gaps (grades 5–6) will show up in usage — fill reactively.

**Stage 3 — Public launch (Week 7+).** Full Play Store release once crash-free >99.5%, content flag rate is low, and unit economics are understood. iOS follows after the Apple review pass (note the privacy-label and parental-consent requirements are stricter on iOS).

**Launch checklist (Play Store):** Data Safety form matching the *corrected* privacy policy · Families/Designed-for-Families program compliance (it's K-5) · content rating questionnaire · App Check enabled · signed release build with the upload key backed up · store listing assets (the `playstore_assets/` folder exists — verify screenshots reflect the modernized UI) · staged rollout percentage (start 10–20%).

**Go/No-go criteria for public:** auth enforced everywhere ✓ · no secrets in repo ✓ · state persists across deploy ✓ · hints don't leak answers ✓ · school-curriculum returns questions or is hidden ✓ · crash-free >99.5% · privacy policy accurate ✓.

---

*Evidence for every finding above is cited by file and line. The four highest-leverage actions are: rotate the leaked keys today, add API authentication, persist state to Firestore, and swap to the clean content set.*
