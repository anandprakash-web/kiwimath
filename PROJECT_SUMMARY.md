# Kiwimath Project Summary

**Owner:** Anand Prakash (anand.prakash@vedantu.com)
**Machine:** Mohan's Mac Mini (username: ap)
**Project Location:** `~/Downloads/kiwimath/`
**Flutter App:** `~/Downloads/kiwimath/app/`
**Backend:** `~/Downloads/kiwimath/backend/`
**Last Updated:** 2026-04-27

## What Is Kiwimath

An adaptive K-5 math olympiad app for Indian students. Children practice Kangaroo/Felix-style competition questions with adaptive difficulty, Socratic hints, gamification (XP, coins, gems, badges), and parent auth.

## Architecture

**Backend:** Python FastAPI on Google Cloud Run (project: `kiwimath-801c1`, region: `asia-south1`)
- Service name: `kiwimath-api`
- Production URL: `https://kiwimath-api-deufqab6gq-el.a.run.app`
- Content baked into Docker image from `content-v2/` folder
- Deploy script: `backend/deploy.sh`

**Frontend:** Flutter (Android-first, iOS planned)
- Firebase project: `kiwimath-801c1`
- Firebase Auth: email/password + Google Sign-In + Phone OTP (+91 default)
- API client auto-switches between localhost (debug) and Cloud Run (release)

**Content:** 800 questions across 8 olympiad topics, flat JSON + SVG visuals
- Grade 1: difficulty 1-50
- Grade 2: difficulty 51-100
- 100 questions per topic, evenly split across grades

## What We Built (189 tasks completed)

### Content Pipeline (Tasks #59-#183)
1. Extracted curricula from Beast Academy (G1-G5), Felix workbooks, and Kangaroo Ecolier papers
2. Built 32-column enhanced curriculum spreadsheet (G1-G5)
3. Created 800 production questions across 8 topics: Counting, Logic, Arithmetic, Geometry, Patterns, Spatial, Measurement, Data
4. Each question has: parametric stem, 4 choices, SVG visual, diagnostics per wrong answer, difficulty 1-100, 6-level Socratic hint ladder
5. Multiple QA rounds: visual-stem mismatch audit, duplicate-option fix, answer-position bias fix, missing question marks, render validation

### Backend Systems (Tasks #1-#27, #113-#173)
1. **Content Store v2** (`content_store_v2.py`): Loads flat JSON, serves by topic/difficulty/grade, `by_difficulty_range()` for grade filtering
2. **Adaptive Engine v2** (`adaptive_engine_v2.py`): ELO/IRT-based ability tracking, question selection, latency x accuracy behavioral matrix
3. **Gamification** (`gamification.py`): Kiwi Brain reward system - XP, coins, gems, badges, titles, level-ups, micro-celebrations, child state detection, intervention recommendations
4. **API v2** (`questions_v2.py`): `/v2/topics`, `/v2/questions/next`, `/v2/answer/check`, `/v2/student/summary` - all with grade filtering and hint ladder support
5. **Grade-difficulty mapping**: `_GRADE_DIFFICULTY = {1: (1, 50), 2: (51, 100)}`

### Flutter App (Tasks #12-#17, #84-#164)
1. **Auth flow** (`main.dart`): `_AuthWrapper` listens to `authStateChanges`, shows `SignInScreen` or main app
2. **Auth service** (`auth_service.dart`): Email/password, Google Sign-In, Phone OTP (with +91 auto-prefix), human-friendly error messages
3. **Sign-in screen** (`sign_in_screen.dart`): 3-tab toggle (Sign in / Sign up / Phone), Google button, forgot password, OTP flow
4. **Home screen** (`home_screen.dart`): Grade 1/Grade 2 selector, topic cards with difficulty distribution, navigates to question screen
5. **Question screen v2** (`question_screen_v2.dart`): 10-question sessions, SVG visuals, hint ladder button (opens bottom sheet), adaptive difficulty, XP/coin/gem toasts, badge unlock dialogs, level-up celebrations, streak tracking
6. **Hint ladder** (`hint_ladder_bar.dart`): 6-level Socratic hints (L0 pause -> L5 teach), animated progress dots, color-coded cards, compact `HintButton` that opens bottom sheet
7. **Theme** (`kiwi_theme.dart`): Grade-adaptive theming (K-2 playful/candy colors, 3-5 mature), `KiwiTier.forGrade()` system
8. **API client** (`api_client.dart`): All v2 endpoints, grade param, hints_used param, retry logic, auto base URL resolution

### Infrastructure
1. **Dockerfile**: Python 3.12-slim, uvicorn, health check, content baked in
2. **deploy.sh**: Automated Cloud Run deployment (build + push + deploy)
3. **Firebase**: Auth enabled (email, Google, phone), Firestore (native mode)
4. **Firebase options**: Android + Web configured in `firebase_options.dart`

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/api/questions_v2.py` | All API endpoints, grade filtering |
| `backend/app/services/content_store_v2.py` | Content loader, difficulty range queries |
| `backend/app/services/adaptive_engine_v2.py` | ELO/IRT adaptive engine |
| `backend/app/services/gamification.py` | Kiwi Brain reward system |
| `backend/deploy.sh` | Cloud Run deployment script |
| `backend/Dockerfile` | Docker build config |
| `app/lib/main.dart` | App entry, AuthWrapper, grade state |
| `app/lib/services/auth_service.dart` | Firebase Auth (email/Google/phone) |
| `app/lib/services/api_client.dart` | HTTP client for all v2 endpoints |
| `app/lib/screens/sign_in_screen.dart` | Parent auth screen (3 modes) |
| `app/lib/screens/home_screen.dart` | Topic browser with grade selector |
| `app/lib/screens/question_screen_v2.dart` | Practice session (10 Qs) |
| `app/lib/widgets/hint_ladder_bar.dart` | Socratic hint UI |
| `app/lib/theme/kiwi_theme.dart` | Grade-adaptive theme system |
| `app/lib/models/question_v2.dart` | Dart data models |
| `app/lib/firebase_options.dart` | Firebase config (Android + Web) |
| `backend/app/api/admin.py` | CMS admin API (18 endpoints) |
| `backend/app/services/cms_store.py` | SQLite CMS store (CRUD, workflow, QA, versions) |
| `backend/admin.html` | CMS admin frontend (served at /cms) |
| `SPECS.md` | Complete technical specs (all formulas, methods) |
| `question-review-tool.html` | Static question review tool (800 Qs embedded) |

## Content Management System (CMS)

Built April 27, 2026. SQLite-backed CMS with full content lifecycle:

**Backend** (`/admin/*` routes):
- Question CRUD with auto-QA (10-point checklist on every save)
- Workflow: Draft → Review → Approved → Published (must pass QA ≥8/10 to publish)
- Version history (every edit creates a snapshot)
- Reviewer actions: approve/reject/flag/comment
- Bulk import from content-v2/ JSON files
- Export published questions back to content-v2/ format
- Dashboard with pipeline stats, topic coverage, QA health

**Frontend** (`/cms`):
- Full question editor (stem, choices, hints, diagnostics, SVG)
- Workflow management (submit, approve, reject, publish, archive)
- Live QA checklist panel
- Review history and version timeline
- Dashboard with content pipeline visualization
- QA report with issue grouping

**To run:** `cd backend && uvicorn app.main:app --reload` then visit `http://localhost:8000/cms`
**First time:** Click "Import from content-v2/" to load all 800 questions into the CMS.

## What Remains (Deployment Only)

All code is complete. Only terminal commands remain:

### Step 1: Firebase Console Setup
```
1. Go to Firebase Console -> Authentication -> Sign-in method
2. Enable Phone authentication
3. Enable Google authentication  
4. Go to Project Settings -> Android app
5. Add SHA-1 fingerprint (from: cd app/android && ./gradlew signingReport)
6. Add SHA-256 fingerprint
7. Download updated google-services.json -> app/android/app/
```

### Step 2: Deploy Backend
```bash
cd kiwimath/backend
gcloud auth login
gcloud config set project kiwimath-801c1
./deploy.sh
# Verify:
curl https://<service-url>/v2/topics
curl https://<service-url>/v2/topics?grade=1
```

### Step 3: Build Android APK
```bash
cd kiwimath/app
flutter clean
flutter pub get
flutter build apk --release
# APK at: build/app/outputs/flutter-apk/app-release.apk
```

### Step 4: Install & Test
```bash
adb install build/app/outputs/flutter-apk/app-release.apk
```
Test checklist:
- Google Sign-In (account picker should appear)
- Phone OTP (enter number, receive SMS, verify 6-digit code)
- Grade 1 vs Grade 2 content (different difficulty ranges)
- Hint ladder (tap hint button, progressive reveal)
- Gamification (XP toasts, coin rewards, badge unlocks)

## Pending Tasks
- **#124**: Add iOS platform support
- **#127**: Set up iOS platform and TestFlight
- **#136**: Rebuild Android APK with gamification UI
- **#187**: Deploy backend to Cloud Run with hint ladder + grade filtering
- **#189**: Rebuild Android APK with all fixes and verify on device
