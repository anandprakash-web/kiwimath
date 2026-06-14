# Kiwimath — Complete Launch Q&A + Step-by-Step Launch Guide

**Date:** 2026-06-14 · **Scope:** backend code, frontend↔backend integration, every tab & branch, UI/UX, and content↔tab wiring — followed by a launch plan. Findings are grounded in the actual code (file:line) from two full-codebase audit passes plus a content-resolution check.

---

## Verdict in one line

The **content, the remapped backend (`/v3`), and the new design are launch-grade**; the **Flutter client is the gap** — it still runs the old 4‑tab app on `/v2`+`/v4`, has a large block of dead Clan code, and isn't pointed at `/v3`. Nothing here is foundational: it's a focused front-end cutover plus a handful of fixes and two product decisions.

| Dimension | State |
|---|---|
| 1. Backend code | **8/10** — prior launch-blockers genuinely fixed; clean `/v3`; medium ops items |
| 2. Frontend↔backend integration | **5/10** — app not on `/v3`; two live economies; old contract |
| 3. Tabs & branching | **6/10** — 4 tabs work; Clan system is unreachable dead code |
| 4. UI/UX | **5/10** — fonts unbundled, mascot placeholder, emoji-as-icons |
| 5. Questions↔tabs | **9/10** — olympiad index == files exactly; curriculum 78% resolved |

---

## 1. Backend code — Q&A

**The five 2026‑06‑12 launch-blockers are all genuinely closed in the current code** (verified, not just claimed):

- **Auth everywhere.** Every user router is registered with `Depends(verify_token)` (`main.py:106–125`, including `/v3` at 108); admin routers use `verify_admin` (128–132); HTML/admin pages are admin-gated; `/health` public; `/debug/content` admin-gated *and* only registered off-production (`main.py:295`). `/v3` enforces identity with `assert_user_match` on `/answer/check`, `/me/wallet`, `/me/progress` (`level.py:204/260/271`).
- **State persists to Firestore.** engagement, daily-puzzle, clans, diagnostic sessions, session-locks and gamification all write through `state_store`/`clan_firestore` (module dicts are fallback-only). The "lost on every deploy" problem is fixed.
- **No answer leak / no committed secret / CORS fixed / prod docs off.** `_q_public()` omits answers at fetch (`level.py:64`); `kiwimath_internal_2026` is gone (hmac, fail-closed); CORS is env-driven, not `*`; `/docs` off when `KIWIMATH_ENV=production`.

**`/v3` rewire is correct:** no fetch-time leak, idempotency-keyed, one server-side economy — `/me/wallet` (`get_profile_summary`) and `/me/progress` (`get_state`) read the **same** gamification singleton, so they can't diverge.

**Backend issues to address (none are foundational):**

| Sev | Issue | Evidence | Fix |
|---|---|---|---|
| HIGH | **Two economies / two banks live at once.** `/v2`+`/v4` (drives IRT + mastery + Growth/Parent) and `/v3` (gamification-only) both serve overlapping question banks. A child on `/v3` builds wallet state but **not** the IRT θ that `/v2/proficiency` → Growth/Parent reads. | §4 of backend audit | Pick one live path at launch (see guide). |
| HIGH | **Cloud Run memory headroom thin.** `2Gi`/1-worker loads v2 + v4 + level(28k) + 4 redundant curriculum stores + pillar ≈ 75k objects; curriculum held 2–3×. Startup OOM → crash-loop risk. | `deploy.sh:138`, `main.py:221–262` | `--memory 4Gi`, and stop bootstrapping the ncert/singapore/uscc/icse stores once `/v3` is the source of truth. |
| MED | **`/v3 _is_correct` unguarded `int()` cast** on the MCQ branch → a malformed `correct_answer` 500s the hottest write path. | `level.py:179` | Wrap in try/except. |
| MED | **Deprecated `?api_key=` query auth** still accepted (gets logged). | `auth.py:82`, `clans.py:731` | Header-only (`X-Internal-Key`). |
| LOW | **Dead `session.py`** (`/session` router + in-memory `_sessions`) never registered. | `main.py` (no import) | Delete. |

---

## 2. Overall frontend ↔ backend — Q&A

**The integration is sound but on the OLD contract.** The Flutter client (`api_client.dart`) sends `Authorization: Bearer <id token>` on every call and `X-Idempotency-Key` on mutations (`authed_http.dart`, `auth_token.dart:54–71`) — good. **But a full grep of `app/lib` for `/v3` returns zero matches.** The app drives Olympiad off `/olympiad` + `/olympiad/v2/pillars` and School off `/v4/school`; it never touches the new level/curriculum API.

So today's reality: **everything you remapped and rebuilt lives on the backend and in the HTML prototype, not in the shipping app.** Wiring the client to `/v3` (prototype = the screen spec) is the single "last mile."

There are **two frontends** in the repo — keep them straight:
- `kiwimath_prototype.html` — the new 4‑tab design, fully QA'd, **not shippable** (it's the spec).
- `app/lib` (Flutter, ~80 files) — the shippable app, old structure, the thing the launch guide builds.

---

## 3. All tabs & branching — Q&A

**Current shipping shell is 4 tabs (v9), not the 6‑tab "v8" the docs claim** (`main.dart:91`, an `IndexedStack` at 1131):

| Tab | Opens | Sub-tabs |
|---|---|---|
| Practice | `OlympiadTabScreen` | Practice · Daily · Worksheets · Saved |
| School | `CurriculumScreen` | NCERT/ICSE/Cambridge/Singapore/USCC |
| Progress | `GrowthTabScreen` | mountain journey, milestones |
| Me | `ProfileScreen` | → Parent dashboard (PIN-gated) |

**Flows that work:** auth gate → onboarding (name → grade → 10‑Q diagnostic → plan), practice loop (server-graded), parent PIN gate. **Daily puzzle is reachable** (Practice sub-tab).

**Branching defects:**
- **The entire Clan social system is dead code (launch-blocker-class).** Create/join/leaderboard/picture-challenge/guess-board and the whole RewardsScreen exist in `main.dart` (`_buildClanLanding:677`, `_navigateTo*Clan`, `_handle*`) but **nothing calls them from `build()`** — there's no entry point in the 4‑tab shell. Either wire a Clan entry (5th tab or Progress sub-tab) or cut it before launch.
- **~9 orphan screens** imported by nobody: `home_screen`, `olympiad_screen`, `learning_path_screen`, `topic_level_map_screen`, `companion_picker_screen`, `grade_upgrade_screen`, `clan_hub_screen`, `downloads_screen`, `explanation_screen`. Dead weight; delete.

---

## 4. UI/UX flaws — Q&A (rating 5/10)

| Sev | Flaw | Evidence |
|---|---|---|
| HIGH | **Fonts not bundled** — `google_fonts` declared but no `fonts:`/`assets:` in `pubspec.yaml`; Poppins/Nunito/Baloo fetched at runtime → FOUT and system-font fallback offline (bad for an offline kids' app). | `kiwi_theme.dart:201,341` |
| HIGH | **Mascot is a placeholder** — colored circle + initial + emoji badge; code comment literally says "for now it's a beautiful placeholder". No character art ships. | `companion_view.dart:174` |
| MED | **Emoji as icons/art** — 224 emoji literals across 27 screens (🥝 brand, 🔥 streak, 💎 gems, ⚔️ clan) render inconsistently per device. | (27 files) |
| MED | **43 blocking spinners** incl. full-screen barriers before Smart Session. | `main.dart:974` |
| MED | **Accessibility ~absent** — only 2 `Semantics` in the whole app. | — |
| ✅ | **Good:** real Google "G" via CustomPaint (compliant), 28 `HapticFeedback` calls, skeleton loader in the practice loop. | `sign_in_screen.dart:814` |

Plus two **bugs**: benchmark `setState` after `await` with no `mounted` guard (`benchmark_test_screen.dart:73/76/78/141/143`, crash risk on the slow diagnostic) and **grade change is never persisted** — `_onGradeChanged` only `setState`s, never calls `updateStudentProfile`, so a grade switch reverts on restart (`main.dart:1079`). (The old daily-puzzle option‑0 bug is confirmed **fixed**.)

---

## 5. All questions ↔ tab connection — Q&A (verified clean)

| Check | Result |
|---|---|
| Olympiad total | **18,099** — L1 9,298 · L2 5,978 · L3 2,823 · L4–L8 0 (empty by design) |
| Questions missing id/answer | **0** |
| `topic_map.json` counts vs actual file counts | **0 mismatches** — the index and the files agree exactly (no disjoint) |
| Curriculum chapters → questions | 282 chapters, 12,745 refs, **9,947 resolve (78%)**, 3 chapters fully orphaned (May‑dedup casualties) |
| Prototype data vs backend bank | **exact match (18,099)** |
| `/v3` smoke test | **17/17 pass** — no answer leak at fetch, wallet==wallet (no disjoint), idempotent |

The content↔tab wiring is the strongest part: Olympiad routes by Level→Topic, School by Board→Grade→Chapter, both resolve to real questions on `/v3`, and the only blemish is 3 orphaned curriculum chapters (regenerate `chapters.json` against the deduped bank, or hide them).

---

## Consolidated issue list (do before launch)

**Must-fix (blockers):**
1. Decide & wire the **single live path** — cut the app over to `/v3` (recommended) and stop serving `/v2`+`/v4` question/answer routes, *or* hold `/v3` dark and launch the old app honestly. Don't ship two economies.
2. **Clan system**: wire an entry point or cut it (it's dead code today).
3. Confirm the **Gemini key was rotated and git history scrubbed** (flagged 2026‑06‑12; `.env.save` is now a placeholder but verify the old key is dead and purged from history).

**High:**
4. Persist grade change (`_onGradeChanged` → `updateStudentProfile`).
5. Add `mounted` guards in `BenchmarkTestScreen`.
6. Bump Cloud Run to `--memory 4Gi` (and drop redundant curriculum stores).
7. Bundle fonts; replace the mascot placeholder (or accept emoji for v1).

**Medium:** guard `/v3 _is_correct` int-cast · remove `?api_key=` query auth · delete orphan screens + dead `session.py` · regenerate 3 orphaned curriculum chapters.

---

## Step-by-step launch guide

You have two honest paths. Pick one.

### Path A — Soft-launch the **current** app now (fastest)
Ships the existing 4‑tab Flutter app on `/v2`+`/v4` (old grade-based olympiad, no `/v3`, no new design). Use this only if speed matters more than shipping the remap.

### Path B — Launch the **remapped** experience (recommended)
Ships the new Level/Grade model + 4‑tab redesign + unified economy. Requires the Flutter cutover. This is what all the recent work was for.

The steps below cover **Path B** (Path A is the same minus steps 1–2).

**Phase 0 — Security & decisions (this week)**
1. **Rotate the Gemini key + scrub git history** if not already done: new key in local `.env` only, delete the old key in Google AI Studio, `bfg --delete-files .env.save` (or `git filter-repo`), force-push. Non-negotiable for a kids' app.
2. **Decide:** single economy path = `/v3`; Clan = wire-or-cut; confirm grade band → scale-score mapping is acceptable (or plug in the IRT proficiency service).

**Phase 1 — Commit the backend + content (Terminal)**
```bash
cd ~/Downloads/kiwimath && rm -f .git/index.lock
git add CLAUDE.md KM_LEVEL_REORG_REPORT_2026-06-13.md KM_OLYMPIAD_QA_REPORT_2026-06-13.md \
  LAUNCH_QA_AND_GUIDE_2026-06-14.md kiwimath_prototype.html \
  content-live/olympiad content-live/curriculum \
  qa-reports/km_reorg.py qa-reports/km_qa_scan.py qa-reports/km_qa_fix.py \
  backend/app/services/content_store_level.py backend/app/api/level.py \
  backend/app/main.py backend/deploy.sh backend/pre_deploy_check.py backend/tests/smoke_level_v3.py
git commit -m "Level/Grade remap + olympiad QA + 4-tab prototype + backend /v3 rewire"
git push origin main
```

**Phase 2 — Flutter cutover to `/v3` (the last mile; engineering)**
3. Point the API client at `/v3`: Olympiad → `/v3/olympiad/levels`, `/levels/{L}/topics`, `…/topics/{tk}/next`; School → `/v3/curriculum/...`; answers → `POST /v3/answer/check`; wallet/progress → `/v3/me/wallet` + `/v3/me/progress`. Use `kiwimath_prototype.html` as the exact screen spec (level picker, sequenced chapters, Academic Height gauge, 4 pillars + Logic & Puzzles, unified wallet on every tab).
4. Fix the two high front-end bugs (grade persistence, benchmark `mounted`), wire-or-cut Clan, bundle fonts.
5. `cd app && flutter pub get && flutter analyze && flutter test` — fix anything analyze flags.

**Phase 3 — Backend deploy**
```bash
cd ~/Downloads/kiwimath/backend
python3 pre_deploy_check.py        # expect: ALL CHECKS PASSED (verifies olympiad 18,099 + curriculum 10,340)
# one-time env (if not set): admin emails + internal key
gcloud run services update kiwimath-api --region asia-south1 \
  --update-env-vars KIWIMATH_ADMIN_EMAILS=anand.prakash@vedantu.com
# edit deploy.sh: --memory 4Gi  (headroom for the content set)
./deploy.sh
curl https://<service-url>/health   # confirm content_level: olympiad 18099, curriculum 10340
```

**Phase 4 — App build & internal test**
```bash
cd ~/Downloads/kiwimath/app
flutter build apk --release          # or appbundle for Play Store
```
Install on a device → smoke test: sign in → Olympiad level picker (L1–L3 live, L4–L8 "coming soon") → answer a question (coins/XP/streak update in the wallet on every tab) → School grade → sequenced chapters → Progress (Academic Height + 5 strands) → Me (edit/switch/sign-out, Parent PIN).

**Phase 5 — Staged Play Store rollout** (per the existing `PLAY_STORE_SUBMISSION_GUIDE.md`)
6. Enable **Firebase App Check** (locks the client API keys).
7. **Closed testing** (50–100 families) → watch crash-free rate (>99%), answer-check latency, and that streaks/coins survive a redeploy.
8. **Open testing / one-region** → watch D1/D7 retention, content-flag rate, infra cost per child.
9. **Production** at 10–20% rollout once crash-free >99.5% and the privacy/Data-Safety form matches real collection (child name + grade).

**Go/No-go:** single live economy ✓ · key rotated + history clean ✓ · state survives a deploy ✓ · `/v3` serves L1–L8 + grades ✓ · app on `/v3` ✓ · Clan wired-or-cut ✓ · crash-free >99.5% · privacy policy accurate ✓.
