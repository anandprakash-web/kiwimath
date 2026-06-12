# Kiwimath Deployment — May 1, 2026
## Version 1.2.0+4

## What's new in this release

1. **Question Flagging System** — Students can flag questions with categories (wrong answer, bad hint, visual issues, etc.)
2. **Spaced Revision for Mistakes** — Wrong answers trigger periodic re-testing at 1→3→7→14→30 day intervals
3. **Diagnostic Anti-Cheat** — Retest questions are never repeated from previous diagnostics
4. **IRT Parameters** — All 19,185 questions now have proper 3PL IRT calibration (a, b, c)
5. **4 Curricula** — NCERT, Singapore Math, US Common Core, ICSE all wired in
6. **Bottom Navigation** — Parent Dashboard, Learning Path, Profile now visible in bottom nav (no longer hidden behind avatar)
7. **Flag Icon on Questions** — Flag button in question screen header with 6 category bottom sheet

---

## Part 1: Deploy Backend to Cloud Run

Open Terminal on your Mac:

```bash
cd ~/Downloads/kiwimath/backend
chmod +x deploy.sh
./deploy.sh
```

This builds the Docker image with all content baked in and deploys to Cloud Run (asia-south1).

### Verify backend

```bash
# Get the URL
URL=$(gcloud run services describe kiwimath-api --region asia-south1 --format 'value(status.url)')

# Health check
curl "$URL/health"

# Check item bank (should show ~19,185 items)
curl "$URL/assess/item-bank/stats" | python3 -m json.tool

# Check all 4 curricula
curl "$URL/assess/curricula" | python3 -m json.tool

# Test flagging endpoint
curl -X POST "$URL/flag/submit" \
  -H "Content-Type: application/json" \
  -d '{"question_id":"T1-001","student_id":"test","flag_type":"other","comment":"test flag"}'

# Test revision queue
curl "$URL/v2/revision-queue/test-user" | python3 -m json.tool
```

---

## Part 2: Build Flutter Release APK

### Prerequisites
- Flutter SDK 3.3+ installed
- Android SDK with build-tools
- Keystore at `/Users/ap/kiwimath-upload-key.jks` (already configured in key.properties)

### Build commands

```bash
cd ~/Downloads/kiwimath/app

# Clean previous builds
flutter clean

# Get dependencies
flutter pub get

# Build release APK (signed with your keystore)
flutter build apk --release

# The APK will be at:
#   build/app/outputs/flutter-apk/app-release.apk
```

### If you also want an App Bundle (for Play Store):

```bash
flutter build appbundle --release

# The AAB will be at:
#   build/app/outputs/bundle/release/app-release.aab
```

### Install on device for testing

```bash
# Connect your Android phone via USB with USB debugging enabled, then:
flutter install --release

# Or use adb directly:
adb install build/app/outputs/flutter-apk/app-release.apk
```

### Quick test checklist after install

- [ ] App opens, shows onboarding for new user (or home screen for existing)
- [ ] **Bottom nav visible** — 4 tabs: Home, Path, Parent, Profile
- [ ] Home tab shows topics, grade selector, continue card
- [ ] Path tab shows learning path timeline
- [ ] Parent tab asks multiplication gate, then shows dashboard
- [ ] Profile tab shows avatar, name, stats, retake test, sign out
- [ ] Start a topic → question screen loads with **flag icon** in header
- [ ] Tap flag icon → bottom sheet with 6 categories appears
- [ ] Answer a question wrong → check that revision scheduling works (answer will reappear in future smart sessions)
- [ ] Retake diagnostic → questions should be different from first time

---

## Version details

| Component | Version |
|-----------|---------|
| App version | 1.2.0+4 |
| Application ID | com.vedantu.kiwimath |
| Min SDK | Flutter default (21) |
| Target SDK | Flutter default (34) |
| Backend items | 19,185 IRT-calibrated |
| Content questions | 12,185 (8 topics × 6 grades) |
| Curricula | NCERT, Singapore, USCC, ICSE |
| API routes | 153 endpoints |
