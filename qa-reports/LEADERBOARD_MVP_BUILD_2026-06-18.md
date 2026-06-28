# Leaderboard MVP — backend build (2026-06-18)

The first executable slice of the competitive layer: **Daily Contest + Weekly League + League Points**, riding on the existing economy, the adaptive content bank, and `FirestoreBackedStore`. Server-graded, no answer leak, idempotent one-attempt, identity-bound. **21/21 new tests; existing 17/17 + 18/18 still green; pre-deploy clean.**

## What's built

**Services**
- `backend/app/services/contest_service.py` — `ContestService`:
  - `todays_qids(level)` — a deterministic **8-question set per (date, level)**, drawn from `level_store`, gradeable only (mcq/integer; proofs excluded), ordered by increasing difficulty. Same for everyone in a level that day (fair), varies daily (md5 seed).
  - `get_contest(user, level)` — public payload (no `correct_answer`/`correct_value`), with live/upcoming/closed status and your attempt state.
  - `submit(user, level, answers)` — server-grades, scores `base(difficulty) × correct × speed × streak × on-time`, awards the **economy** through `gamification.record_answer` (coins/gems/xp/streak — the one ledger) **and League Points** via the league. **One attempt** (re-submit replays the stored result; never double-awards).
  - `leaderboard(level, date)` — today's board, ranked by score.
- `backend/app/services/league_service.py` — `LeagueService`:
  - Cohorts of **~30** per (level, tier); tiers **Bronze → Silver → Gold → Platinum → Diamond → Legendary**.
  - `add_lp`, `standings` (your rank + promotion/relegation zones + week-end), `rollover` (top 7 promote, bottom 7 relegate, middle holds; sets each member's next-week tier).
  - Durable via `FirestoreBackedStore` (in-mem fallback for local/tests).

**API** (`backend/app/api/contest.py`, mounted under the shared `verify_token`)
- `GET  /v3/contest/today?user_id=&level=`
- `POST /v3/contest/submit`
- `GET  /v3/contest/leaderboard?level=&date=`
- `GET  /v3/league/me?user_id=&level=`
- All `user_id` endpoints bind identity with `assert_user_match` (cross-user → 403).

**Economy wiring** — practice now nudges the league: a correct answer in `/v3/answer/check` adds **+5 LP** (best-effort). The Daily Contest dwarfs it (hundreds of LP), keeping the contest the apex.

## Tested (`backend/tests/smoke_contest_league.py`, 21/21)
deterministic set · level-specific · increasing difficulty · **no answer leak** · correct grading (8/8 vs 3/8) · **one-attempt replay (no double-award)** · leaderboard ranks · league cohort + rank + zones + promotes-to-Silver · practice LP accrues · **rollover (top→Platinum, bottom→Silver, middle holds)** · persistence (fresh instance still sees the attempt) · **auth 403** on contest/today, league/me, submit.

## Rollover cron (built)
- `POST /v3/internal/league-rollover` — runs `league.rollover()`. Auth mirrors the clan cron: the `X-Internal-Key` header is accepted by `verify_token` as an internal identity; admins (and dev mode) may also trigger it; **a normal user → 403** (tested). League weeks are now **IST-aligned**.
- `backend/deploy/league_cron.yaml` — Cloud Scheduler config, **Sunday 23:55 IST (18:25 UTC)**, same `X-Internal-Key` secret as the clan cron. Apply with the `gcloud scheduler jobs create` command in the file's header after deploy.

## App (built — needs an APK rebuild)
- `app/lib/services/contest_service.dart` — Dart client (`getContestToday`, `submitContest`, `contestLeaderboard`, `leagueMe`).
- `app/lib/v3/contest_screens.dart` — `CompeteHubScreen` (level picker + Daily Olympiad card + League card), `DailyContestScreen` (lobby → timed quiz → results + live board; MathText + SVG/PNG figures), `LeagueScreen` (cohort board with promotion/relegation stripes, your row highlighted).
- Wired into `app/lib/v3/kiwi_v3.dart`: a **"Compete"** banner on the Olympiad tab → `CompeteHubScreen`. Structurally verified (balanced delimiters, all symbols present); needs `flutter build apk` on your Mac.

## Not yet — V2 (per the design doc)
Kiwi Rating + divisions/titles · Monthly Seasons + cosmetics + Hall of Fame · on-time/rank-bonus polish · contest content curation (currently auto-picked from the bank) · age-tiered presentation (Junior hides rating, etc.).

## Ship
Backend-only, no content change:
```
cd ~/Downloads/kiwimath/backend && ./deploy.sh
```
- The Daily Contest opens **6 PM IST** with a 4-hour window by default (`OPEN_HOUR`/`WINDOW_HOURS` in `contest_service.py`). For staging/testing you can force it open with env `KIWIMATH_CONTEST_ALWAYS_OPEN=1`.
- After deploy, add the weekly rollover cron (above) so leagues cycle.

## Notes
- New Firestore collections: `contest_results`, `contest_board`, `league_member`, `league_cohort`, `league_ptr` — created on first write, no migration.
- Cohort/board writes are read-modify-write (last-write-wins, documented) — acceptable (a 29–31 cohort or a lost microscopic LP race is harmless; the spendable economy is never touched here).
- The per-process daily-set cache grows one tiny entry per (date, level) — negligible; cap later if desired.
