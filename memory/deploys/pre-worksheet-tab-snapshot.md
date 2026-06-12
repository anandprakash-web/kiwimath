# Pre-Worksheet-Tab Snapshot (May 5, 2026)

Save this to revert if the Worksheet tab changes break anything.

## Bottom Nav (6 tabs) — main.dart lines 1148-1153
```dart
_buildNavItem(0, Icons.emoji_events_rounded, 'Olympiad', tier),
_buildNavItem(1, Icons.school_rounded, 'School', tier),
_buildNavItem(2, Icons.trending_up_rounded, 'Growth', tier),
_buildNavItem(3, Icons.groups_rounded, 'Clan', tier),
_buildNavItem(4, Icons.family_restroom_rounded, 'Parent', tier),
_buildNavItem(5, Icons.person_rounded, 'Profile', tier),
```

## Tab 0 Body — OlympiadTabScreen (main.dart lines 1000-1008)
```dart
OlympiadTabScreen(
  selectedGrade: _selectedGrade,
  onGradeChanged: _onGradeChanged,
  onStartPractice: (topicId, topicName) => _navigateToQuestions(
    topicId: topicId,
    topicName: topicName,
  ),
),
```

## OlympiadTabScreen sub-tabs (olympiad_tab_screen.dart)
3 sub-tabs inside segmented control:
- 0: Practice (OlympiadScreen) — smart adaptive
- 1: Worksheets (WorksheetListScreen) — daily olympiad worksheets
- 2: Downloads (DownloadsScreen) — offline management

## WorksheetListScreen (worksheet_list_screen.dart)
- 3 view modes: topics, journey, grid
- Loads from `/olympiad/worksheets/list?grade=N`
- Uses WorksheetCache for offline
- Topic config: 7 categories (counting_observation, arithmetic, logic_ordering, word_problems, shapes_folding, patterns_sequences, mixed)

## Backend Routers registered (main.py)
```python
questions_v2_router, questions_v4_router, onboarding_router, parent_router,
learning_path_router, gamification_router, paywall_router, user_router,
admin_router, analytics_router, companion_router, portal_router,
assessment_router, flag_router, clans_router, daily_puzzle_router,
engagement_router, growth_router, content_editor_router, olympiad_router
```

## Backend Olympiad Router (api/olympiad.py)
- Prefix: `/olympiad`
- Content dir: `content/olympiad/g{grade}_olympiad_batch{1-5}.json`
- Endpoints:
  - GET `/olympiad/worksheets?grade=N&day=D`
  - GET `/olympiad/worksheets/list?grade=N`
  - GET `/olympiad/questions/{qid}/visual`
  - GET `/olympiad/stats?grade=N`

## Wavebook Content Location
- `content-v2/wavebook/wavebook_L{3,4}_batch{1-4}.json`
- Schema: {id, stem, interaction_mode, topic, difficulty_tier, question_number, choices, correct_answer, grade_band, source, svg}
- L3 (G3-4): 239 questions, 4 batches, 19 sessions
- L4 (G5-6): 312 questions, 4 batches, 26 sessions
- Total: 551 questions

## Deploy Script (deploy.sh)
- Project: kiwimath-801c1
- Region: asia-south1
- Service: kiwimath-api
- Copies content-v2/ into Docker image at /content-v2/
- ENV: KIWIMATH_V2_CONTENT_DIR=/content-v2
- Memory: 1Gi, CPU: 1, min-instances: 1, max: 10

## API Client (Flutter)
- Production URL: https://kiwimath-api-deufqab6gq-el.a.run.app
- Debug: localhost:8000 (web), 10.0.2.2:8000 (Android)

## PIN Gate
- Tab 4 (Parent) requires PIN verification
- `_parentPinVerified` flag in _AppShellState
- 4-digit numeric PIN via PinGate.show()

## Key Files to Revert
If reverting, restore these files to their pre-change state:
1. `app/lib/main.dart` — bottom nav, tab body, imports
2. `app/lib/screens/olympiad_tab_screen.dart` — sub-tab labels
3. `app/lib/screens/worksheet_list_screen.dart` — view modes
4. `backend/app/main.py` — router registrations
5. `backend/app/api/wavebook.py` — DELETE this file (didn't exist before)
6. `app/lib/screens/wavebook_screen.dart` — DELETE this file (didn't exist before)
7. `app/lib/services/api_client.dart` — wavebook API methods
