# Curriculum Selection Feature

**Status:** COMPLETE & READY TO DEPLOY (May 2, 2026)
**Priority:** HIGH — was blocking shipping, now done. Anand approved layout, deploy pending (run locally).

## Context (from conversation May 1, 2026)

Anand pointed out that there's no way for a student to select which curriculum they follow (NCERT, ICSE, Olympiad/Kangaroo). This changes the entire home screen content:
- **NCERT/ICSE** → show chapters in sequence (Ch 1: Numbers, Ch 2: Addition...)
- **Olympiad (Kangaroo)** → show topics (Counting & Observation, Logic & Puzzles...)

## What Exists Already (Backend)

1. **`icse_content_store.py`** — Full ICSE content loader with chapter→domain mapping
2. **`content_store_v2.py`** — `_load_curriculum_folder()` can load NCERT/SING/USCC/ICSE
3. **Question ID regex** accepts `NCERT-G3-001`, `ICSE-G4-100` format
4. **`CurriculumAlignment` model** in `question.py` — has `framework`, `chapter`, `olympiad_skill`
5. **`path_engine.py`** — accepts `curriculum` parameter
6. **`cat_engine.py`** — CAT session accepts `curriculum` param

## Implementation Complete

### Backend
- `DEFAULT_USER` dict has `"curriculum": None` field in `firestore_service.py`
- `ProfileResponse` + `UpdateProfileRequest` in `user.py` include `curriculum`
- `ProfileUpdateRequest` in `questions_v2.py` (`/v2/student/profile`) includes `curriculum`
- `GET /v2/chapters?grade=1&curriculum=ncert` → returns ordered chapter list with question counts
- `content_store_v2.py` → `get_chapters()` scans questions by ID prefix (NCERT-G1-, etc.), groups by `chapter` field

### Flutter
- `UserProfile` model has `curriculum` field + `hasCurriculum` getter
- `_CurriculumCard` widget in `onboarding_screen.dart` — 4 options: NCERT, ICSE, IGCSE, Olympiad
- `_submitAllAnswers()` passes `curriculum` to `updateStudentProfile()`
- `api_client.dart` → `getChapters(curriculum, grade)` + `updateStudentProfile(curriculum:)`
- `LearningPathScreen` accepts `curriculum` param, sets default tab accordingly
- `main.dart` passes `_profile.curriculum` to LearningPathScreen
- Chapters tab fetches real data from `/v2/chapters` API (no more placeholder)
- `_ChapterCard` widget shows chapter number, name, topics preview, question count

### Onboarding Flow
Welcome → Name → **Curriculum Picker** → Grade → Diagnostic Quiz → Results → Plan

## Learning Path Tab — Dual Mode Design (May 1, 2026)

Anand decided the Path tab should have **tabs at the top** to toggle between:
- **Curriculum tab** (default for NCERT/ICSE kids): chapters in sequence (Ch 1, Ch 2...)
- **Olympiad tab** (default for Olympiad kids): 8 Kangaroo topics

**Smart Nudge:** If a curriculum kid is doing great (high level in chapters), show a nudge: "You're showing great progress here! Try Olympiad-level questions too." This is an upsell from curriculum → olympiad difficulty.

### Content Coverage (May 1, 2026)
- **NCERT**: G1-G6 × 500 questions/grade (3,000 total). IDs: NCERT-G{N}-{NNN}
- **ICSE**: G1-G6 × 200 questions/grade (1,200 total). IDs: ICSE-G{N}-{NNN}
- **IGCSE**: G1-G6 × 200 questions/grade (1,200 total). IDs: IGCSE-G{N}-{NNN}
- **Olympiad**: 8 topics × 300/grade × 6 grades (existing T{N}-{NNN} content)
- Backend `content_store_v2.py` loads all via `igcse-curriculum` folder entry
- `main.dart` wired: `_loadChapters()` → chapters + curriculum passed to HomeScreen

### Open Questions
- What triggers the nudge? (Level 5+ in a chapter? 3 chapters mastered?)
- Olympiad-only kids: do they see a "Curriculum" tab at all?
- How does Smart Practice mix between curriculum and olympiad content?

## Anand's Exact Words
"if i select ncert then this will be chapters name instead of topic"
"I did not see how to select which curriculum student will take and this should change as per that selection"
"Check for all data flow here and all tabs should have data flowing properly"
"if kid has selected NCERT then it should be chapter flow and if student is doing great in that one line should be there that you should try olympiad level questions too"
"There can be tab at the top to toggle between olympiad and curriculum"
