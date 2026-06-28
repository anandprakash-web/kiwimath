# 03 · The Codebase

The engineering layer. Python + FastAPI backend, Flutter app, Firebase, content as JSON files baked into the backend image. This file is the map: the golden path, the services, the API, the app, deploy.

---

## 1. ⚠️ The golden path — fork this, ignore the rest

The repo has **years of superseded layers**. Only the **`/v3` "level" stack** is current. When reading, building, or forking, stay on the golden path:

**Backend services (golden path):**
`adaptive_skill.py` · `content_store_level.py` · `contest_service.py` · `league_service.py` · `economy_service.py` · `store_service.py` · `gamification.py` · `firestore_service.py` · `core/auth.py`

**Backend API (golden path):** `api/level.py`, `api/contest.py`, `api/store.py` (the `/v3` routes)

**App (golden path):** `app/lib/v3/*` + `app/lib/main_v3.dart`

**Tests:** `backend/tests/smoke_level_v3.py`, `smoke_adaptive_skill.py`, `smoke_contest_league.py`, `smoke_store.py`

**Leave behind (legacy — do NOT use or fork):** `content_store_v2.py`, `content_store_v4.py`, `content_store.py`, `questions_v2.py`, `questions_v4.py`, the Clan system (`clan_*`), Wavebook, Benjamin-olympiad, the v8 6-tab `main.dart`, and the `content-v2/` / `content-v4/` banks. They're superseded and only cause confusion. (They're still on disk so older paths don't break, but nothing new should touch them.)

> Rule of thumb: if a file isn't in the golden-path list and isn't obviously needed, don't touch it.

---

## 2. Backend services (what each does)

| Service | Responsibility | Notes for a new cowork |
|---------|----------------|------------------------|
| `content_store_level.py` | Loads question records into memory; holds the taxonomy (`OLYMPIAD_STRANDS`, `PILLAR_NAMES`); the `LQ` question class; `numeric_correct()` grading helper; `topic_in_level()`. | The one place that "knows the shelves." Edit the strand list + load paths to re-skin; keep the record fields. |
| `adaptive_skill.py` | `AdaptiveSkillEngine`: builds a per-(level,topic) skill ladder from the cluster tags; `next_qid` (pure read), `record` (advances per the rule), `status`. Position persisted per user. | **Subject-blind.** Reads skill tags + difficulty + right/wrong only. The heart of the product. |
| `economy_service.py` + `gamification.py` | One wallet (coins/gems/XP/streak); idempotent `spend`/`grant`; book entitlements on debit. | One shared ledger, "no disjoint." Money never buys rank. |
| `contest_service.py` | Deterministic daily question set per (date, level); server-side grading; one-attempt; score = base × correct × speed × streak × on-time; prefers the verified pool. | Generic timed-quiz logic. |
| `league_service.py` | Weekly cohorts (~30), tiers Bronze→Legendary, LP, standings, promote-top-7 / relegate-bottom-7, IST-aligned rollover. | Generic ranking. |
| `store_service.py` | Catalog (`_CATALOG`) + book file map (`_BOOK_FILES`) + per-user entitlements. | Append catalog rows to add books; don't reorder. |
| `firestore_service.py` | `FirestoreBackedStore` — durable per-user state with in-memory fallback (so tests run without Firestore). | All persistence rides this. |
| `core/auth.py` | Firebase token verify + `assert_user_match` (blocks cross-user access → 403). | Every per-user route guards with it. |

---

## 3. The `/v3` API surface

The current API. Key routes (all under `/v3`):

**Practice / adaptive** (`api/level.py`)
- olympiad levels / strands / topics; `GET /v3/olympiad/strands`
- `next` — default `mode=skill` when a user is given (returns the adaptive rung); falls back to IRT/ZPD without a user
- `question` + `visual`; curriculum boards / grades / sequenced-chapters / questions
- `POST /v3/answer/check` — server-side grade; drives the one economy; idempotency-keyed; returns the new adaptive status
- `me/wallet`, `me/progress` (level-scoped), `adaptive-status` (resume UI)

**Contest / league** (`api/contest.py`) — `contest/today`, `contest/submit`, `contest/leaderboard`, `league/me`, internal rollover.

**Store / economy** (`api/store.py`) — `store/catalog|entitlements|claim`, `economy/wallet|spend|grant`, `store/content/{id}/manifest|bytes|cover` (entitlement-gated).

**Two grading paths exist** (contest and practice) and both go through the same `numeric_correct()` — keep them consistent. The practice payload exposes `video_url`/`solution` as a post-answer reveal; the **contest payload deliberately omits the solution** (no mid-quiz leak).

**Answer-leak boundary:** the question payload sent to the client before submission **never contains the answer** — verified by the smoke tests. This is a hard invariant; don't break it.

---

## 4. The Flutter app

- `app/lib/main_v3.dart` — the entry point: wraps the app in the providers, sets the theme (Kiwimath orange `#FF6F00`), branding.
- `app/lib/v3/kiwi_v3.dart` — the shell: the tabbed navigation and the practice/olympiad/school/progress/profile surfaces.
- `app/lib/v3/contest_screens.dart` — Daily Contest + League screens (lobby → timed quiz → results + board, MathText + svg/png rendering).
- `app/lib/v3/books_browse.dart`, `html_book_reader.dart`, `book_reader.dart` — the Library + reader (see `02`).
- Math rendering: `flutter_math_fork` renders mixed prose + `$LaTeX$`; `Image.memory` for base64 `visual_png`; SVG via the string renderer.

**Build entry is `lib/main_v3.dart`** (not `main.dart`, which is the legacy v8 shell). A content/book/economy change ships via backend deploy only; UI changes need an APK build.

---

## 5. Security + correctness (hardening already done)

These were found and fixed in independent reviews — keep them intact:
- **IDOR fixes:** every per-user route (`/next`, wallet, progress, contest) asserts the caller matches the user → cross-user access is 403.
- **Idempotency:** `answer/check`, contest submit, and `economy/spend` are idempotency-keyed so a replay/double-tap can't double-award or double-debit.
- **Spend currency pinning:** unlocking a book requires the *correct* currency (a 300-coin book can't be paid with 300 gems).
- **Monotonic adaptive state:** the skill-ladder position never regresses (re-read guard), so re-login never jumps a learner backwards.

**Known accepted limitation:** the coin debit + idempotency is not yet a single Firestore *transaction* (a cross-instance double-tap could double-debit). Safe today (virtual currency, client in-flight guard, money stubbed) but **must become a transaction before real-money/IAP.** This is the #1 thing to fix before charging real money.

---

## 6. Deploy + verify

```bash
cd ~/Downloads/kiwimath/backend && ./deploy.sh        # backend → Cloud Run (asia-south1); bakes content-live/ + content-books/
cd ~/Downloads/kiwimath/app && flutter build apk --release -t lib/main_v3.dart   # only if app code changed
```

**Always keep green before deploy** (and after every change):
- `python3 backend/pre_deploy_check.py` → "ALL CHECKS PASSED"
- `smoke_level_v3.py` (17/17), `smoke_adaptive_skill.py` (18/18), `smoke_contest_league.py` (23/23), `smoke_store.py`

Two working-dir conventions exist among the tests (some run from repo root with `content-live/...`, some from `backend/` with `../content-live/...`) — `05_SCRIPTS.md` documents which is which. Several tests carry **hard-coded expected counts** (catalog size, bank totals) — bump them when content changes, or they'll fail green-for-the-wrong-reason.

**What ships how:**
- Content / book / catalog / economy-field change → **backend deploy only** (baked into the image).
- Navigation / reader / screen change → **APK build** required.

---

## 7. The mental model to keep

The backend is a **content server + a set of subject-blind engines**. Questions load from files; the engines read difficulty + concept tags + right/wrong + wallets. Nothing below the content layer knows the subject. That is what makes the platform forkable (the `HANDOVER_MINIAPP/` pack is the fork recipe) — and it's why the discipline in `01` and `04` (keeping the *content* correct) matters more than any engine code.
