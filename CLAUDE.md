# Memory

## Me
Anand Prakash (anand.prakash@vedantu.com), Founder of Kiwimath — adaptive math learning app for K-6 kids. Building with Flutter + FastAPI + Firebase.

## Current Status (May 2, 2026)

**ALL PRE-DEPLOY TASKS DONE. Ready to deploy.**

### What's Done (Ready for Deploy):
- ✅ IGCSE content quality fix (3,600 Qs): 0% giveaway hints, 0% generic diagnostics, 447 visual contexts, 370 stems diversified
- ✅ NCERT content quality fix (4,633→4,373 Qs): 0% giveaway hints, 0% generic diagnostics, 260 duplicates removed, 468 visual contexts
- ✅ Drag-and-drop widget fixed — now uses `ReorderableListView.builder` (was broken: tiles in Column made drag non-functional)
- ✅ IRT chapter-based adaptive selection wired for curriculum chapters (not just Olympiad topics)
- ✅ Integer + drag_drop interaction modes added (backend + Flutter)
- ✅ Diagnostic test flagging system — backend (`/flag/diagnostic-review`, `/flag/review-queue`, `/flag/resolve/{id}`) + Flutter UI (flag button in quiz, reason+severity dialog, batch submit at end)
- ✅ Onboarding won't repeat — `onboarded_at` flag in Firestore, checked by `hasOnboarded` in Flutter
- ✅ Full Q&A verification — all 7 backend endpoints verified, all 3 Flutter tabs (Home/Path/Parent) wired correctly

### What's Next:
1. **Deploy** (`cd backend && ./deploy.sh` + `flutter build apk --release`)
2. **Anand reviews diagnostic questions** — flag button active during quiz
3. **Fix flagged questions** via `/flag/review-queue` endpoint
4. **More critical feedback** from Anand post-deploy

### Content Quality Numbers (Post-Fix):
| Dataset | Questions | Giveaway Hints | Generic Diagnostics | Visual Context |
|---------|-----------|----------------|--------------------:|----------------|
| IGCSE G1-G6 | 3,600 | 0% (was 52-83%) | 0% (was 33%) | 12.4% |
| NCERT G1-G6 | 4,373 | 0% (was 6-82%) | 0% (was 8-41%) | 5-14% |

### Deploy Instructions
```bash
cd ~/Downloads/kiwimath/backend && ./deploy.sh   # Backend → Cloud Run (asia-south1)
cd ~/Downloads/kiwimath/app && flutter build apk --release   # Flutter APK
```

## UI/UX Redesign Sprint — COMPLETE

| Screen | Status |
|--------|--------|
| Onboarding | DONE — Welcome → Name → **Curriculum** → Grade → Diagnostic → Results → Plan |
| Home Screen | DONE — v4 build, curriculum-aware (chapters vs topics) |
| Learning Path | DONE — v4, dual tabs (Chapters/Olympiad) + smart nudge |
| Parent Dashboard | DONE — v4, score circle + weekly goal + strengths/weaknesses |

## Home Screen — DONE (v4, curriculum-aware)
- Orange gradient "Smart Practice" hero (compact row)
- Badge milestone progress (every 50 questions → next badge)
- Level colors: green (1-3), blue (4-6), purple/gold (7-10)
- **NCERT/ICSE/IGCSE users**: see numbered chapter list (fetched from `/v2/chapters` API)
- **Olympiad users**: see 8 Kangaroo topics in 2-col grid with level badges
- Avatar tap → profile bottom sheet (3-tab nav, no Profile tab)
- `main.dart` → `_loadChapters()` → passes `curriculum` + `chapters` + `chaptersLoading` to HomeScreen
- Bottom nav: 3 tabs (Home, Path, Parent) — Profile via avatar tap

## Learning Path — DONE (v4, curriculum wired)
- Dual tabs at top: **Chapters** (curriculum) | **Olympiad** (8 Kangaroo topics)
- Default tab = user's onboarded curriculum (Chapters for NCERT/ICSE/IGCSE, Olympiad for olympiad)
- Smart nudge: orange banner on Curriculum tab when any topic hits level 4+ → "Try Olympiad!"
- Chapters tab fetches real data from `/v2/chapters` API (no placeholder)
- No AppBar — clean in-body header consistent with home screen

## Diagnostic Test Flagging System — COMPLETE (May 2, 2026)

### How it works
1. During diagnostic quiz (onboarding), a **Flag button** appears next to each question
2. Anand taps Flag → dialog asks for **reason** (free text) + **severity** (low/medium/high/critical)
3. All flags are batch-submitted to backend at quiz end via `POST /flag/diagnostic-review`
4. Backend stores flags in `flag_store` with `flag_type=diagnostic_review`
5. `GET /flag/review-queue` returns flagged Qs enriched with full question content for immediate fix
6. `POST /flag/resolve/{flag_id}` marks a flag resolved

### Files
- Backend: `backend/app/api/flag.py` (DiagnosticReviewBatch, review-queue, resolve endpoints)
- Backend: `backend/app/services/flag_store.py` (FlagType enum, FlagStore singleton)
- Flutter: `app/lib/screens/onboarding_screen.dart` (_flaggedQuestions, _showFlagDialog, batch submit)
- Flutter: `app/lib/services/api_client.dart` (submitDiagnosticReview method)

### Onboarding won't repeat
- `onboarded_at` timestamp saved to Firestore on benchmark submit
- `UserProfile.hasOnboarded` checked by `_maybeShowOnboarding()` in main.dart
- Flags are submitted alongside benchmark — no separate flow needed

## Hint System — Khan Academy Style (May 2, 2026) — COMPLETE

### Old system (removed)
- `HintLadderBar` + `HintButton` → bottom sheet with generic nudges ("Take a breath")
- Covered the question, didn't teach, not useful

### New system (deployed)
- `InlineHintSteps` widget — Khan Academy-style inline progressive reveal
- Steps appear between question stem and options (question stays visible)
- 2-4 steps per question, teaching the method, never reveals the answer
- Color-coded: blue → amber → purple → green
- 19,985 questions now have `solution_steps` field
- 495 duplicate-choice questions fixed during QA
- Backend `QuestionOutV2` serves `solution_steps: List[str]`
- Flutter `QuestionV2` model parses `solution_steps` from API

## Curriculum Selection Feature — COMPLETE (May 1-2, 2026)

### Onboarding Flow
Welcome → Name → **Curriculum Picker** → Grade → Diagnostic Quiz → Results → Plan

### 4 Curriculum Options
| Curriculum | Color | Content |
|-----------|-------|---------|
| NCERT/CBSE | Green (#2E7D32) | G1-G6 × 500 Qs (3,000 total), 12-14 chapters/grade |
| ICSE | Blue (#1565C0) | G1-G6 × 200 Qs (1,200 total), 7-12 chapters/grade |
| IGCSE | Purple (#6A1B9A) | G1-G6 × 200 Qs (1,200 total), 12 chapters/grade (Cambridge Primary) |
| Olympiad/Kangaroo | Orange (#FF6D00) | 8 topics × 300/grade × 6 grades (T1-T8 content) |

### Backend
- `curriculum` field in Firestore DEFAULT_USER, ProfileResponse, UpdateProfileRequest
- `/v2/chapters?grade=N&curriculum=ncert|icse|igcse` → ordered chapter list with question counts
- `content_store_v2.py` → `get_chapters()` scans by ID prefix (NCERT-G{N}-, ICSE-G{N}-, IGCSE-G{N}-)
- `_load_curriculum_folder()` loads: ncert-curriculum, icse-curriculum, igcse-curriculum, singapore-curriculum, us-common-core
- Dockerfile has `IGCSE_CONTENT_DIR=/content-v2/igcse-curriculum`

### Flutter
- `api_client.dart` → `getChapters(curriculum, grade)` + `updateStudentProfile(curriculum:)`
- `UserProfile` model has `curriculum` field + `hasCurriculum` getter
- `main.dart` → `_loadChapters()` method, called after profile load / onboarding / grade change
- `HomeScreen` accepts `curriculum`, `chapters`, `chaptersLoading` — branches between chapter list and topic grid
- `LearningPathScreen` accepts `curriculum` — sets default tab accordingly

### Data Flow (All Working)
- Streak: Firestore → profile API → Flutter ✓
- Daily progress: sessions completed / daily_goal ✓
- Curriculum: Onboarding → Firestore → profile API → Flutter screens ✓
- Chapters: `main.dart _loadChapters()` → HomeScreen + LearningPathScreen ✓

### Content Files
- `content-v2/ncert-curriculum/grade{1-6}/` — G1-G2: `questions.json`, G3-G6: `ncert_g{N}_questions.json`
- `content-v2/icse-curriculum/grade{1-6}/icse_g{N}_questions.json`
- `content-v2/igcse-curriculum/grade{1-6}/igcse_grade{N}.json`
- Question ID format: `{CURRICULUM}-G{grade}-{NNN}` (e.g. NCERT-G3-042, ICSE-G1-105, IGCSE-G5-200)

## Deploy Instructions
```bash
cd ~/Downloads/kiwimath/backend && ./deploy.sh   # Backend → Cloud Run (asia-south1)
cd ~/Downloads/kiwimath/app && flutter build apk --release   # Flutter APK
```

## Projects
| Name | What |
|------|------|
| **Kiwimath** | K-6 adaptive math app (Flutter + FastAPI + Firebase + Cloud Run) |

## Preferences
- Debate/approve before building each screen
- Go screen-by-screen sequentially
- Check all data flow across tabs before implementing
- "keep working on it and ill be back in sometime .. dont seek my permission in between"
