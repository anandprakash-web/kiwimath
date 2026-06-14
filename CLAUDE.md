# Memory

## ⚠️ REORGANIZED 2026-06-12 — READ FIRST
- **Canonical content = `content-live/`** (content-live/content-v2 + content-live/content-v4). All question QA/fixes happen ONLY here. Old paths `content-v2/`, `content-v4/` moved under it; deploy.sh/main.py/pre_deploy_check.py updated.
- **`archive/`** holds everything not served: content-production (never wired, ~97% overlap with live), Benjamin olympiad (QUARANTINED — placeholder answer keys, do not serve), old docs/tools/strays. See archive/ARCHIVE_INDEX.md.
- Full question QA done 2026-06-12 (QA_FULL_REPORT_2026-06-12.md): 0 critical issues in content-live; 209 unanswerable deleted (recoverable in qa-reports/); hints de-leaked. Security hardening + API auth + Firestore persistence done (FIXES_APPLIED_2026-06-12.md).

## ⚠️ LEVEL RE-TAG 2026-06-13 — Olympiad section is now LEVEL-based (L1–L8), not grade-based
- New tagging system per uploaded `00_TAGGING_SYSTEM.md` + `01_TOPIC_MAP.md`: every olympiad question carries a **Level (L1–L8)** + internal **Pillar (NT/ALG/GEO/COM, never shown to users)** + a friendly **Topic display name**. Levels: L1=G1/2, L2=G3/4, L3=G5/6, L4=G7/8, L5=G9/10(IOQM), L6=RMO, L7=INMO, L8=IMO.
- **Two consolidated stores created** (full reorg): `content-live/olympiad/L{1-8}/{Ln}_{PILLAR}_{topic}.json` (**18,803 olympiad qs**, new IDs `KM-L{n}-{PILLAR}-{serial}`, old id kept as `legacy_id`; `topic_map.json`, `id_map.json`, `counts_report.json` alongside) and `content-live/curriculum/{board}/grade{n}/` (**10,340 school-curriculum qs**, school-only, **grade-tagged** `km_grade` 1-6 verified vs original_id+school_grade = 0 mismatches, chapters.json copied, refs still 78% resolve). Curriculum by grade: G1=1,663 G2=1,612 G3=1,581 G4=1,684 G5=2,065 G6=1,735.
- Pool split = original_id prefix: olympiad = T/GEN/PCT + all v2 topic-1..8 + wavebook; curriculum = NCERT/IGCSE/ICSE/SING/USCC. Conflicting curriculum tags (chapter, curriculum_map/source/tags, dual_tagged) STRIPPED from olympiad qs.
- Integrity VERIFIED: answers/hints/difficulty/IRT/SVG byte-identical to source (0 mismatches, hash + field-by-field). Counts: L1=9,660 · L2=6,320 · L3=2,823 · **L4–L8=0 (empty structure, fill later)**. Report: `KM_LEVEL_REORG_REPORT_2026-06-13.md`.
- **Old `content-v2/` + `content-v4/` banks are NOW SUPERSEDED but still on disk** (kept so backend doesn't break pre-cutover). NEXT PHASE: (1) UI/UX level-picker for Olympiad section, (2) rewire backend (content_store_*, deploy.sh, pre_deploy_check.py) to read olympiad/+curriculum/, then archive content-v2/content-v4.
- **OLYMPIAD QA + FIXES done 2026-06-13** (KM_OLYMPIAD_QA_REPORT_2026-06-13.md): 7-dimension scan. Bank **18,803→18,099** (704 hidden duplicates removed, exposed after stripping ~6,650 story-wrapper filler prefixes — "On the world tour, X runs the numbers." etc., logic puzzles protected). Hints: 1,393 answer-leaks masked + 545 missing generated → **0 leaks**. 550 over-tagged required-visuals downgraded to optional. 2,064 placeholder visual_context cleared. 1 truncated stem fixed (KM-L3-NT-0574). Integrity: choices/answer/IRT/difficulty 0 mismatches every pass. Final L1=9,298 L2=5,978 L3=2,823. Residual: ~103 bespoke filler intros, generic-hint quality.
- **UI PROTOTYPE built** (`kiwimath_prototype.html`, openable): modern 4-tab redesign (Olympiad levels / School grades / Progress / Profile), brilliant.org-style line icons, no question counts in Olympiad, numerically-sequenced chapters, Academic Height gauge (200-800 scale, 500=avg, 800=ceiling), 4-pillar + Logic&Puzzles strands, Profile with edit/switch/sign-out, and a UNIFIED ECONOMY (one shared state → wallet+Progress+Profile always match; practising earns XP/coins/gems/streak, awards unlock live; jsdom-verified no-disjoint). To become Flutter next.
- **BACKEND REWIRE done 2026-06-13** (serves the remapped banks live): new `backend/app/services/content_store_level.py` (lightweight LQ wrapper — QuestionV2's id-validator rejects KM-* ids; loads olympiad 18,099 + curriculum 10,340) + new `backend/app/api/level.py` (`/v3`): olympiad levels/topics/next/question/visual, curriculum boards/grades/sequenced-chapters/questions, **server-side `/v3/answer/check`** (grades + drives ONE economy via `gamification.record_answer`, idempotency-keyed) + `/v3/me/wallet` + `/v3/me/progress` (academic height + strands from the SAME state = no disjoint). Wired into `main.py` (router + startup bootstrap + /health). `deploy.sh` bakes content-olympiad/+content-curriculum/ and sets `KIWIMATH_OLYMPIAD_CONTENT_DIR`/`KIWIMATH_CURRICULUM_CONTENT_DIR`. `pre_deploy_check.py` verifies new banks (+ fixed a pre-existing inline-SVG false-positive). **Smoke test 17/17 PASS** (`backend/tests/smoke_level_v3.py`): no answer-leak at fetch, economy consistent, idempotent. **REMAINING last mile:** point the Flutter app at `/v3` (it still calls /v2,/v4); the prototype is the screen spec.

## Me
Anand Prakash (anand.prakash@vedantu.com), Founder of Kiwimath — adaptive math learning app for K-6 kids. Building with Flutter + FastAPI + Firebase.

## Current Status (May 5, 2026)

**v8 APP: 6-tab nav (Practice/Worksheets/School/Clan/Growth/Parent), 28,803+ questions, all systems live**

### What's Built & Verified:
- ✅ **v8 Flutter App**: 6-tab nav — Practice (smart adaptive), Worksheets (100 daily olympiad), School (multi-curriculum), Clan (social+puzzles), Growth (mountain journey), Parent (PIN-protected)
- ✅ **Practice tab**: Smart adaptive practice with topic unlocking, 8 core topics per grade
- ✅ **Worksheets tab**: 600 olympiad worksheets (100/grade × 6 grades), 3 views (Topics/Journey/Grid), per-worksheet + bulk download, offline cache
- ✅ **School tab**: Multi-curriculum chapter browser (Cambridge, NCERT, Singapore, ICSE, US Common Core sub-tabs)
- ✅ **Clan tab**: Daily puzzle + streak system, clan wars, engagement rewards, join/create clan
- ✅ **Growth tab**: Mountain journey visualization, milestones, scale scores, proficiency levels
- ✅ **Parent tab**: PIN-gated dashboard with diagnostic reports, clan section
- ✅ **Terry Chew "why" explanations**: All 21,603 practice questions + 7,200 olympiad questions have Analysis-style explanations
- ✅ **Olympiad worksheet system**: 30 batch JSON files, SVG visual renderer, mixed interaction modes (MCQ, integer, fill-up, drag-drop, match-column)
- ✅ Vedantu LO System: competency taxonomy (K/A/R), 6-level proficiency, scale scores, growth tracking, benchmark tests, auto-remedial, parent diagnostic reports
- ✅ Adaptive engine (5 phases) + Flutter wired to `/v2/session/unified`
- ✅ Content v4: 22,467 base questions → 36,459 grade-topic organized (multi-grade overlap via KiwiTier)
- ✅ Clan system: 14 clan endpoints + engagement (daily puzzle, streak, leagues, wars, rewards)

### Content v4 Summary:
| Grade | Topics | Questions |
|-------|--------|-----------|
| 1 | 8 | 4,301 |
| 2 | 8 | 6,674 |
| 3 | 11 | 7,437 |
| 4 | 11 | 7,055 |
| 5 | 10 | 5,104 |
| 6 | 9 | 5,888 |
| **Total** | **57** | **36,459** |

### KiwiTier Level→Grade Mapping:
```
Level 1 → Grade 1 + Grade 2
Level 2 → Grade 2 + Grade 3
Level 3 → Grade 3 + Grade 4
Level 4 → Grade 4 + Grade 5
Grade 6 ← cloned from Level 3-4 with +0.3 IRT bump
```

### Content v4 File Structure:
```
content-v4/
  adaptive/grade{1-6}/{topic-id}.json  — IRT-sequenced questions per topic
  adaptive/grade{1-6}/index.json       — grade-level topic index
  school/{curriculum}/grade{1-6}/chapters.json — chapter references
  locale_config.json                   — shared locale data (india/singapore/us)
  topic_map.json                       — master topic definitions
  visual_coverage_report.json          — visual audit results
```

### Quality Fixes Applied (schema 4.0 → 4.1):
- Domain misclassifications fixed (algebra, data topics)
- 2,883+ identical diagnostics deduplicated
- 7,978 hint spoilers remediated
- country_context extracted to shared locale_config.json (160MB → 100.5MB)
- 23,194 null school_grade values populated
- 43 cross-operation diagnostic errors fixed
- 433 pure arithmetic questions moved out of word-problem files
- g5-percent rebuilt from 5 rounding stubs → 120 proper percentage/ratio questions
- G3/G4 data_handling separated from measurement into dedicated topics
- G3 multiplication (215→400) and division (178→398) bolstered
- Visual requirements audited: 9,425 over-tagged essentials downgraded, 6,686 fake SVG refs cleared
- 15 genuinely essential questions got inline SVGs generated
- Final: 636 essential (all covered), 22,090 optional, 13,733 none

### Flutter v8 Navigation:
```
Tab 0: Practice    → OlympiadScreen (Smart adaptive practice, topic unlocking G1-G6)
Tab 1: Worksheets  → OlympiadTabScreen (sub-tabs: Smart Practice / Daily Worksheets / Downloads)
Tab 2: School      → CurriculumScreen (Cambridge/NCERT/Singapore/ICSE/USCC sub-tabs)
Tab 3: Clan        → ClanHubScreen (daily puzzle, streak, wars, rewards) or ClanLanding (join/create)
Tab 4: Growth      → GrowthScreen (mountain journey, milestones, proficiency)
Tab 5: Parent      → ParentDashboardScreen (PIN-gated via PinGate)
```
- PIN gate: `app/lib/widgets/pin_gate.dart` — 4-digit numeric PIN, SharedPreferences
- Bottom nav: `_AppShell` in `app/lib/main.dart` (v8) — 6 tabs: Olympiad (star icon, orange), School (house), Growth (chart), Clan (people group), Parent (person+child), Profile (person)
- App icon: minimal white kiwi bird + sparkle on orange gradient

### Olympiad Worksheet System (BUILT):
- **600 worksheets**: 100 per grade × 6 grades, stored in `content/olympiad/g{1-6}_olympiad_batch{1-5}.json`
- **12 questions each**: Mixed difficulty (warmup/practice/challenge), mixed interaction modes
- **5 interaction modes**: MCQ, integer, fill_up, drag_drop, match_column
- **SVG visuals**: Parameterized components in `content/olympiad/svg_components/`, rendered on-demand via `/olympiad/questions/{id}/visual`
- **Titles & topics**: Each worksheet has engaging title (e.g., "Pattern Detective", "Number Ninja"), subtitle (topic chips), dominant_topic
- **Terry Chew Analysis**: All 7,200 question approaches normalized to "Analysis: [method]... Answer: [correct]." format
- **Offline cache**: `WorksheetCache` — per-worksheet + bulk download, disk persistence, SVG pre-fetch
- **3-view UI**: Topic-grouped (default), Journey (swipeable cards), Grid (10×10 calendar)
- **API**: GET `/olympiad/worksheets?grade=N&day=D`, GET `/olympiad/worksheets/list?grade=N` (rich metadata), GET `/olympiad/questions/{qid}/visual`, GET `/olympiad/stats`

### Practice Bank "Why" Explanations (BUILT):
- **21,603 practice questions** have `w` field with Terry Chew-style Analysis explanations
- **Format**: "Analysis: [method/insight].\n[step-by-step reasoning with actual math].\nAnswer: [correct answer]."
- **Topic-specific generators**: pattern_sequence, word_problem, logic, spatial, shapes, fractions, measurement, data_handling, algebra, ratio_proportion, etc.
- **Zero fallbacks**: All questions have specific, math-aware explanations (not generic)
- **File**: `backend/static/all_questions.json` — compact format with keys: id, s, c, a, d, k, t, g, src, svg, w

## Key Architecture:
| Component | File | Purpose |
|-----------|------|---------|
| Content Store v4 | `content_store_v4.py` | Grade-topic structured content, adaptive selection |
| Content Store v2 | `content_store_v2.py` | QuestionV2 pydantic model (50+ fields) |
| v4 API Router | `api/questions_v4.py` | 14 endpoints: topics, adaptive, school, offline, locking |
| Session Lock | `session_lock.py` | Multi-device session locking with TTL + heartbeat |
| Skill Mapper | `skill_mapper.py` | Maps questions → 37 skill nodes |
| Unified Planner | `unified_session_planner.py` | Cross-curriculum adaptive sessions + Welcome Back mode |
| Path Engine | `path_engine.py` | 37-node prerequisite graph + learning paths |
| IRT Model | `irt_model.py` | 3PL with EAP estimation |

## Terms
| Term | Meaning |
|------|---------|
| **KiwiTier** | Level system: Junior (G1-2) + Senior (G3-6), each Level spans 2 grades |
| **dual-tagging** | Curriculum questions tagged for both adaptive topics AND school chapters |
| **IRT-b** | Item difficulty parameter; questions sorted ascending within each topic |
| **theta (θ)** | Student ability estimate on IRT scale (-3 to +3) |
| **essential visual** | Question cannot be answered without seeing the SVG/image |
| **smart practice** | Unified session pulling from all curricula adaptively |
| **the moat** | Content quality + explanation quality + parent trust + child delight |
| **AH** | Academic Height — 3D mastery: Depth + Breadth + Stability |
| **ZPD** | Zone of Proximal Development — P(correct) ∈ [0.60, 0.85] |
| **3-R Framework** | "Why?" diagnostics: Re-Contextualize → Redirect → Reinforce |
| **Crunch Mode** | Weeks 31-40: retrieval practice, no new levels, exam-ready |
| **K/A/R** | TIMSS competency taxonomy: Knowing, Applying, Reasoning |
| **Scale Score** | IRT theta → 200-800 scale (mean=500, SD=50) for parent-friendly reporting |
| **Proficiency Level** | L1-L6 named levels (Explorer→Legend), mapped from theta ranges |
| **Benchmark Test** | 20-question structured diagnostic with anchor items for equating |
| **Auto-Remedial** | K-wrong → insert 3 easier same-concept questions (max 2/session) |

## Clan System (BUILT — Social/Engagement Layer)
| Term | Meaning |
|------|---------|
| **Clan** | Student-created group, invite-only, grade-locked, max 15 members |
| **Brain Points** | Clan points from members' challenge scores (top 10 count) |
| **Brawn Points** | Bonus points: 50 × active members |
| **Quiz Points** | Weighted mean of daily quiz scores × active count × 10 |
| **Full Squad Bonus** | 2× Brain Points if ALL members practice same day |
| **Picture Unravel** | Clan-exclusive challenge: earn points → reveal olympiad-level PUZZLE image, group solves it |
| **Guess Board** | 1 guess/day per member, 60 chars max, profanity-filtered — collaborative puzzle-solving workspace |
| **Challenge Bust** | When a challenge expires/completes and points refresh |
| **Clan Leader** | Creator of clan, only one who can submit Picture Unravel answers |
| **Clan Levels** | Seedling (0) → Sapling (5K) → Tree (15K) → Forest (40K) → Ancient Grove (100K) XP |

### Clan Architecture:
| Component | File | Purpose |
|-----------|------|---------|
| Clan Service | `backend/app/services/clan_service.py` | Core logic: scoring, levels, filtering, invites |
| Clan Firestore | `backend/app/services/clan_firestore.py` | Firestore persistence layer (14 methods) |
| Clan API | `backend/app/api/clans.py` | 14 REST endpoints under /v4 |
| Clan Models | `app/lib/models/clan.dart` | 8 Dart data models |
| Clan Service (Flutter) | `app/lib/services/clan_service.dart` | Flutter API client (13 methods) |
| Clan Hub | `app/lib/screens/clan_hub_screen.dart` | Main clan view |
| Create/Join | `app/lib/screens/clan_create_screen.dart`, `clan_join_screen.dart` | Parent-gated flows |
| Challenge | `app/lib/screens/picture_challenge_screen.dart` | Pixel grid + guess board |
| Leaderboard | `app/lib/screens/clan_leaderboard_screen.dart` | Grade-scoped top 20 |
| Widgets | `app/lib/widgets/clan_crest_widget.dart`, `pixel_grid_widget.dart`, `squad_activity_bar.dart`, `guess_board_widget.dart` | Reusable clan UI components |
| Puzzles | `backend/static/puzzles/` | 6 SVG puzzles (Star Map, Locked Grid, Code Breaker, River Crossing, Spiral Tower, Einstein's Garden) |
| Daily Cron | `backend/deploy/clan_cron.yaml` | Cloud Scheduler for midnight IST aggregation |

→ Full details: memory/projects/clan-construct.md

### Engagement System (BUILT):
| Component | File | Purpose |
|-----------|------|---------|
| Daily Puzzle API | `backend/app/api/engagement.py` | Daily puzzle endpoints (get, submit, streak) |
| League API | `backend/app/api/engagement.py` | League leaderboards, clan wars |
| Rewards API | `backend/app/api/engagement.py` | Achievement unlocks, XP tracking |
| Puzzle Screen | `app/lib/screens/daily_puzzle_screen.dart` | Daily puzzle solve flow |
| Streak Screen | `app/lib/screens/streak_screen.dart` | Streak calendar + rewards |
| Wars Screen | `app/lib/screens/clan_wars_screen.dart` | Clan vs clan battles |
| Rewards Screen | `app/lib/screens/rewards_screen.dart` | Achievements + XP store |
| Growth Screen | `app/lib/screens/growth_screen.dart` | Mountain journey + milestones |
| Growth API | `backend/app/api/growth.py` | Growth endpoints, milestone detection |

### Daily Puzzle System (BUILT)
| Term | Meaning |
|------|---------|
| **Daily Puzzle** | One new puzzle per grade per day, drops 4 PM IST (after school), closes 10 PM IST |
| **Narrative Style** | Story-wrapped puzzles from 9 books (~2,000 puzzles analyzed). 5 styles: Smullyan Dialogue Logic, Moscow Real-World, Everything Kids Visual, Yoshigahara Spatial, Party Trick/Game |
| **Puzzle Books Deep-Read** | Alice in Puzzle-Land, Lady or Tiger, What is the Name of This Book, To Mock a Mockingbird, This Book Needs No Title, Riddle of Scheherazade, Godelian Puzzle Book (all Smullyan) + Moscow Puzzles (Kordemsky) + Puzzles of Yoshigahara |
→ Full analysis: memory/puzzle-books/ (4 files: smullyan-storytelling-patterns.md, moscow-puzzles-patterns.md, yoshigahara-visual-puzzles.md, puzzle-creation-guide.md) |
| **IPS** | Individual Puzzle Score: Accuracy(50%) + Speed(30%) + Streak(15%) + Bonus(5%) = max 1,000 |
| **CDS** | Clan Daily Score: Brain(top 10 IPS × participation multiplier) + Brawn(solvers×50) + Full Squad(+500) |
| **Streak** | Consecutive daily solves: Day 1=10 → Day 7+=150 pts. Missing a day resets. |
| **Puzzle Types** | 10 types: Number Crunch, Pattern Hunt, Shape Shift, Logic Lock, Measure Up, Code Break, Speed Race, Coin & Dice, KenKen Grid, Story Puzzle |
| **Leagues** | Bronze → Silver → Gold → Diamond → Legendary (trophy-based, seasonal reset) |
| **Special Modifiers** | Double XP (10%), Boss Puzzle (10%), Mystery (5%), Clan vs Clan Duel (5%) |
| **Build Plan** | Phase 1: 60 puzzles/grade MVP → Phase 2: Social layer → Phase 3: Leagues → Phase 4: 360/grade/year |
→ Design doc: Kiwimath_Clan_Daily_Puzzle_System.docx

## Vedantu Learning Outcomes System (BUILT — Assessment & Reporting Layer)
| Term | Meaning |
|------|---------|
| **K/A/R** | Competency taxonomy: Knowing (recall), Applying (use/solve), Reasoning (analyze/justify) — TIMSS-aligned |
| **Scale Score** | Student ability on 200-800 scale (mean=500, SD=50), transformed from IRT theta |
| **Proficiency Levels** | L1 Explorer → L2 Builder → L3 Achiever → L4 Star → L5 Champion → L6 Legend |
| **Benchmark Test** | 20-question structured diagnostic with anchor items for score equating |
| **MLE Theta** | Newton-Raphson 3PL estimation for scoring benchmarks (more accurate than practice ELO) |
| **Auto-Remedial** | When K-tagged question wrong → insert 3 easier same-concept questions |
| **Growth Tracking** | GrowthSnapshot records over time, trajectory: improving/steady/declining |

### LO Architecture:
| Component | File | Purpose |
|-----------|------|---------|
| Competency Tagger | `backend/scripts/competency_tagger.py` | Auto-classifies 26,722 questions as K/A/R |
| Proficiency Levels | `backend/app/services/proficiency_levels.py` | 6-level system, scale scores, CompetencyProfile, GrowthSnapshot |
| Remedial Engine | `backend/app/services/remedial_engine.py` | Auto-remedial: concept groups, trigger logic, question selection |
| Benchmark Service | `backend/app/services/benchmark_test.py` | Structured tests, anchor items, MLE scoring |
| Proficiency Card | `app/lib/widgets/proficiency_card.dart` | Flutter widget: level badge, scale score, K/A/R bars, growth |
| Benchmark Screen | `app/lib/screens/benchmark_test_screen.dart` | Flutter: 20-question diagnostic flow with results |

### LO API Endpoints:
```
GET  /v2/proficiency         — student's level, scale score, competency breakdown
GET  /v2/proficiency/levels  — all 6 level definitions
POST /v2/benchmark/create    — create structured diagnostic test
POST /v2/benchmark/submit    — submit and score benchmark responses
GET  /v2/benchmark/history   — benchmark history with growth comparison
GET  /v2/remedial/stats      — remedial effectiveness analytics
```

### Competency Distribution (26,722 questions):
K=11,766 (44%), A=12,542 (47%), R=2,414 (9%)

### Clan API Contract (Dart → Python field mapping):
```
POST /v4/clans:        leader_uid, parent_uid, name, grade, crest_shape, crest_color
POST /v4/clans/join:   invite_code, uid, parent_uid, grade
POST /v4/clans/{id}/react:  uid, emoji
POST /v4/challenges/{id}/answer:  clan_id, uid, answer
POST /v4/challenges/{id}/guess:   clan_id, uid, guess_text
Crest shapes: bolt, lion, wave, rocket, blossom, dolphin
parent_uid = same as userId (parent gate is 4-digit PIN in UI)
```

### Clan Local Test Results (May 3, 2026):
All 14 endpoints passing: create, get, mine, join, invite regen, remove member, leaderboard, react, active challenge, progress, submit guess, get guesses, submit answer, daily aggregate

### Bug Fixes (May 3, 2026):
- **tap_to_reveal "no option" bug FIXED**: Two bugs — (1) `questions_v2.py` `_to_response()` stripped choices for non-mcq modes, fixed to send choices whenever they exist; (2) 1,555 questions had unimplemented `tap_to_reveal` mode across 11 content-v2 files, all changed to `mcq`
- **Color(KiwiColors.xxx) compile errors FIXED**: 4 widget files had `Color(KiwiColors.xxx)` wrapping already-typed Color values; removed redundant Color() constructors

### Benchmark Audit & Fixes (May 4, 2026):
- **CRITICAL: Grade filtering added to benchmark tests**: `benchmark_test.py` now filters questions by grade before selection — Grade N test only gets Grade N-1 + N content. Previously used ALL 26,722 questions regardless of grade.
- **8 wrong ICSE-G3 comparison answers FIXED**: Choices contained neither of the two numbers being compared. All 8 in `icse_g3_questions.json`.
- **2 competency mistagged questions FIXED**: T4-0905, T4-0915 (logical negation) changed K → R
- **26 placeholder rect-only SVGs cleared**: ICSE-G1 (12) + USCC-G1/G3 (14) had empty rectangles
- **3,600 curriculum questions got topic tags**: Singapore, USCC, ICSE questions had empty topic field, now auto-assigned based on chapter/tags/stem
- **Full audit report**: `BENCHMARK_AUDIT_REPORT.md`

### Benjamin Olympiad G6 Content (May 4, 2026):
- **17 Benjamin PDFs extracted**: 2009-2025, 408 questions total (24 per year)
- **2009-2012 manually extracted** from visual PDF reading (OCR failed on 2009-2011, 2012 had artifacts)
- **379 original questions** built in content-v2 format with IRT parameters and competency tags
- **505 variant questions** generated: 202 step-down + 202 step-up + 101 similar
- **G6 Smart Practice enabled**: QA review server now serves Benjamin questions for Grade 6
- **Content location**: `content-v2/benjamin-olympiad/grade6/`
- **216 filler sentences removed**: "workspace" intros, disconnected character names stripped from stems across 11 files

### Story Rewriting System (May 4, 2026):
- **All 12,185 Kangaroo questions rewritten** with continuous story narratives
- **16 story themes** across 8 topics × 2 grade bands (junior G1-3 + senior G4-6)
- **Characters G1-3**: Kiwi (lead), Chikoo, Aarohi, Vanya, Riya
- **Characters G4-6**: Kiwi (lead), Ved, Nuha, Google, Veronica
- **Story themes**: The Enchanted Garden, The LEGO Kingdom, The Music Festival, The Treasure Hunt, The Pirate Ship, The Shape Village, The Forest Bakery, The Wizard's Tower (junior) | The Lost City Expedition, The Racing Garage, The Code Breakers, The Demon Hunters, The Space Station, The Architect's Challenge, The World Tour, The Escape Room (senior)
- **8 chapters per topic** — questions progress through the story arc
- **Zero junk remaining**: all old character names (Knight Koko, Chef Cheetah, etc.), workspace mentions, filler sentences stripped
- **Math preserved**: all numbers, operations, choices, and correct answers unchanged
- **Pipeline**: `content-v2/_workspace/rewrite_stories.py` — re-runnable, idempotent
- **Story design**: `content-v2/_workspace/story_design.md`

### Visual & Quality Audit (May 4, 2026):
- **111 visual_context mismatches fixed**: ctx said "pictograph" but stem said "bar graph", wrong clock/number line refs
- **262 empty math stems reconstructed**: 75 from original_stem, 187 from tags/choices
- **74 old character names stripped**: Professor Panda, Ninja Nemo, Astronaut Ava, etc.
- **138 fragment leftovers cleaned**: "Help calculate:", "Needs to work out:", "Needs the GCD!"

### Deduplication (May 4, 2026):
- **12,185 → 8,902 questions** after removing duplicates and near-duplicates
- **342 exact duplicates removed**: same stem + same choices + same answer
- **1,147 near duplicates removed**: same stem, different distractors, same answer
- **1,790 skeleton overloads trimmed**: 4+ questions with identical template in same file (kept max 8 per group)
- **18 duplicate IDs fixed**: T2-1001–T2-1020 clashed between g56 and grade34_variety files
- **Final distribution**: G1-2: 5,387 | G3-4: 1,079 | G5-6: 2,373 | Other: 63
- **All 8,902 IDs verified unique**

### Curriculum Deduplication (May 4, 2026):
- **Singapore**: 1,200 → 1,023 (-177) — number bonds, fraction bars, angle type dupes
  - **+325 SMC questions added** (from 2023 Singapore Math Challenge PDFs G1-G6): fills 104 gap topics (money, time, logic, algebra, patterns, combinatorics, etc.) → **1,348 total Singapore questions**
- **IGCSE (Cambridge Primary)**: 3,600 → 2,808 (-792) — place value, triangle angles, shape sides dupes
- **NCERT**: 3,159 → 2,734 (-425) — G3-G6 had heavy skeleton overload
- **ICSE**: 2,372 → 1,835 (-537) — G1 had 154 dupes alone
- **US Common Core**: 1,200 → 990 (-210) — G1-G3 most affected
- **All 6 curricula verified clean**: 0 dup IDs, 0 exact dupes, 0 skeleton overload
- **Grand total across all content**: 18,617 unique questions (18,292 + 325 SMC)

### Wavebook Question Bank (BUILT — May 5, 2026):
- **551 questions** from Vedantu live olympiad class worksheets (separate from main olympiad system)
- **Level 3** (Grades 3-4): 239 questions, 21 topics, 4 batches — Numbers, Multiplication, Factors, Area, Perimeter, Symmetry, Venn Diagrams, Patterns, Clocks, Data Handling
- **Level 4** (Grades 5-6): 312 questions, 26 topics, 4 batches — Numbers, Divisibility, Factors, Percentage, Profit/Loss, Ratio/Proportion, Quadrilaterals/Polygons
- **25 SVG illustrations**: Geometry figures, Venn diagrams, bar charts, clock faces, symmetry shapes, area grids, number patterns
- **Content location**: `content-v2/wavebook/` — 8 batch JSONs + `svg/` subfolder + `memory/wavebook-index.md`
- **Source**: 18 Google Drive PDFs (file IDs in `_meta.json`)
- **Backend**: `backend/app/api/wavebook.py` — 4 endpoints (/wavebook/topics, /questions, /download, /stats)
- **Flutter**: `app/lib/screens/wavebook_screen.dart` — full MCQ solve flow with per-topic download

### UI Redesign (May 5, 2026) — Worksheet Tab Addition:
- **Bottom nav remains 6 tabs**: Olympiad (star, orange active), School (house), Growth (chart), Clan (people group), Parent (person+child), Profile (person)
- **DPP tab** (formerly "Worksheets"): Daily Practice Problems — olympiad worksheets, all grades, Topics|Grid toggle, Journey removed, play bar removed, downloadable per-worksheet
- **Worksheet tab**: NEW tab added in top shelf alongside DPP — only for G3+, shows live class wavebook MCQs
  - G3/G4 share Level 3 content, G5/G6 share Level 4 content
  - Downloadable individually per topic
  - Topics|Grid toggle (same as DPP)
  - No Journey toggle, no play bar, no "New" badge, no numeric counts (question counts, worksheet counts, completion stats)
- **Top shelf sub-tabs** (within the DPP bottom nav tab): Practice | DPP | Worksheet | Saved
- **Kiwimath Orange**: #FF6F00 (primary accent throughout)

### Currency System (Audited May 5, 2026):
- **Kiwi Coins**: Effort-based, spendable in Shop (avatar items). Earned on every practice session.
- **Mastery Gems**: Skill-based, achievement-gated legendary items. Harder to earn.
- **totalGems**: Engagement gems from daily calendar (7-day cycle: day1=10, day3=25, day5=50, day7=100) + mystery boxes. Separate from Mastery Gems.
- **XP**: Earned per question answered. Drives level system.
- **Profile screen shows**: XP, totalGems, Streak, Topics Mastered, Kiwi Coins, Mastery Gems (6 stats in 3x2 grid — FIXED May 5)
- **⚠️ "gems" exists in TWO backend systems**: gamification (state.gems = Mastery Gems) AND engagement (total_gems = calendar rewards). Profile now shows both separately.
- **Parent dashboard deliberately hides all currencies** — shows only mastery/accuracy/strengths.
- **Clan Hub is the reward HUB** — daily calendar, mystery boxes, stickers, leagues all claimed here.
- **Wavebook/Worksheet**: No client-side reward logic — rewards granted server-side on answer submit (same as Practice/DPP).

### Pending:
- **⚠️ CRITICAL: Git commit needed** — Worksheet tab files are UNTRACKED: olympiad_tab_screen.dart, wavebook_screen.dart, worksheet_list_screen.dart, wavebook.py, content-v2/wavebook/. Anand must `git add` + commit + push from Terminal.
- **Deploy**: Backend + Flutter need redeployment (worksheet tab, gems fix, "why" explanations, engagement system)
- **Benjamin answers need verification**: correct_answer currently set to first choice as placeholder
- **Benjamin visual questions**: 175 questions need SVG generation from PDF images
- **Benjamin variants**: choices need recalculation (inherited from originals, not recomputed)
- **FlagStore → Firestore**: flag_store.py is in-memory only, flags lost on deploy/restart. Need to wire to Firestore.
- **Git push**: .git/index.lock blocks sandbox — Anand needs to run `git add -A && git commit && git push` from Terminal

## Critical Product Principles:
- **IRON RULE: Grades exist ONLY in the Curriculum tab** — core PLAY uses Levels only
- **The REAL moat is content quality** — engine only adapts BAD content faster
- **Child feels:** "This is fun. I can win." **Parent feels:** "I understand exactly what is happening."
- Never expose engineering complexity (IRT/theta/FSRS) to users
- IGCSE → **Cambridge Primary** (IGCSE is not K-6)
- Kiwimath Orange: Primary #FF6D00, Dark #E65100, Light #FFF3E0

## Deploy Instructions
```bash
cd ~/Downloads/kiwimath/backend && ./deploy.sh   # Backend → Cloud Run (asia-south1)
cd ~/Downloads/kiwimath/app && flutter build apk --release   # Flutter APK
```

## Preferences
- "keep working on it and ill be back in sometime"
- Research-first approach: study papers, plan, then execute
- Don't add unnecessary visuals — only where genuinely required
- Go screen-by-screen sequentially (UI only)
