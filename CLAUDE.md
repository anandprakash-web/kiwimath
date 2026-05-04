# Memory

## Me
Anand Prakash (anand.prakash@vedantu.com), Founder of Kiwimath — adaptive math learning app for K-6 kids. Building with Flutter + FastAPI + Firebase.

## Current Status (May 3, 2026)

**DEPLOYMENT READY: All systems verified — 36,459 questions, v4 API wired, offline + locking + clan + Vedantu LO system done**

### What's Built & Verified:
- ✅ Vedantu LO System: competency taxonomy (K/A/R), 6-level proficiency, scale scores, growth tracking, benchmark tests, auto-remedial, parent diagnostic reports
- ✅ Adaptive engine (5 phases) + Flutter wired to `/v2/session/unified`
- ✅ Content v4: 22,467 base questions → 36,459 grade-topic organized (multi-grade overlap via KiwiTier)
- ✅ 57 adaptive topics (8 per G1-G2, 10-11 per G3-G6), IRT-sequenced within each
- ✅ School tab: 5 curricula (NCERT, ICSE, Cambridge, Singapore, US Common Core) with chapter references
- ✅ Dual-tagging: 12,745 curriculum questions appear in both adaptive + school views
- ✅ Backend content_store_v4.py with adaptive question selection + school chapter queries
- ✅ All quality issues fixed (diagnostics, hints, visuals, domain classification, locale extraction)
- ✅ v4 API router: 14 endpoints (topics, adaptive next, school chapters, offline bundle/sync, session lock)
- ✅ Flutter ApiClient updated with all v4 methods
- ✅ Offline session download + sync (`/v4/offline/bundle` + `/v4/offline/sync`)
- ✅ Multi-device session locking (`/v4/session/lock` + heartbeat + unlock)
- ✅ Review caps (max 3/session) + Welcome Back mode (≥3 days away → boosted warmups)
- ✅ QA verified: all 525 AI-generated questions (120 PCT, 185 mult, 220 div) pass math + structure checks
- ✅ E2E test: all 8 verification checks pass
- ✅ Clan system: 14 clan endpoints, 11 Flutter screens/widgets, 6 puzzle SVGs, all locally tested
- ✅ API contract verified: Dart client ↔ Python backend field names aligned
- ✅ Parent dashboard updated with clan section

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
parent_uid = same as userId (parent gate is multiplication question in UI)
```

### Clan Local Test Results (May 3, 2026):
All 14 endpoints passing: create, get, mine, join, invite regen, remove member, leaderboard, react, active challenge, progress, submit guess, get guesses, submit answer, daily aggregate

### Bug Fixes (May 3, 2026):
- **tap_to_reveal "no option" bug FIXED**: Two bugs — (1) `questions_v2.py` `_to_response()` stripped choices for non-mcq modes, fixed to send choices whenever they exist; (2) 1,555 questions had unimplemented `tap_to_reveal` mode across 11 content-v2 files, all changed to `mcq`
- **Color(KiwiColors.xxx) compile errors FIXED**: 4 widget files had `Color(KiwiColors.xxx)` wrapping already-typed Color values; removed redundant Color() constructors

### Pending:
- **FlagStore → Firestore**: flag_store.py is in-memory only, flags lost on deploy/restart. Need to wire to Firestore.
- **Git push**: .git/index.lock blocks sandbox — Anand needs to run `git add -A && git commit && git push` from Terminal
- **Deploy**: Backend needs redeployment to Cloud Run for tap_to_reveal fix to go live

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
