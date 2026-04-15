# Kiwimath Android App

v0 scaffold. One screen, fetches a question from the local FastAPI backend, lets the kid tap an option, shows correct/wrong feedback, fetches the next one.

No auth, no persistence, no step-down navigation, no mascot. Those land Weeks 3 Day 3 → Week 4.

## One-time setup (45 minutes)

### 1. Install Flutter SDK

```bash
# On Mac with Homebrew:
brew install --cask flutter

# Or manual: https://docs.flutter.dev/get-started/install/macos
```

After install, verify:
```bash
flutter doctor
```

It'll tell you what else is missing — probably Android Studio, Android SDK, and a platform-tools setup.

### 2. Install Android Studio

Download from https://developer.android.com/studio. During first launch:
- Let it install the Android SDK (accept all defaults).
- Tools → SDK Manager → install "Android SDK Command-line Tools (latest)".
- Tools → Device Manager → Create virtual device → Pixel 6 with Android 14. This is your emulator.

Run `flutter doctor` again — all rows should be green (except maybe "Xcode" which is iOS-only and doesn't matter for v0).

### 3. Accept Android licenses

```bash
flutter doctor --android-licenses
# Press y through each prompt.
```

## Running the app

Every time you want to run:

**Terminal 1 — start the backend**

```bash
cd ~/Downloads/kiwimath/backend
source .venv/bin/activate
export KIWIMATH_CONTENT_DIR=~/Documents/Kiwimath-Content/Grade1
python -m uvicorn app.main:app --reload
```

Leave this running.

**Terminal 2 — launch the Android emulator + app**

First time only, in the `app/` folder, initialize a Flutter project shell around my code:

```bash
cd ~/Downloads/kiwimath/app
flutter create --project-name kiwimath_app --platforms android --org com.kiwimath .
# This creates android/, pubspec.lock, etc. without touching my lib/ files.
flutter pub get
```

Start the emulator (once):

```bash
flutter emulators --launch <emulator_id>
# find <emulator_id> via: flutter emulators
```

Then run the app:

```bash
flutter run
```

Wait ~1 minute for Gradle to build. You should see:
1. Green Kiwimath app bar with streak + gem counters.
2. A rendered question ("Aarav has 9 laddoos..." or similar, depending on locale).
3. Tappable option cards.
4. Tap one → correct = green, wrong = red, then 2 seconds later → next question.

## Changing the locale

Edit `lib/main.dart` line 15 — change `locale: 'IN'` to `locale: 'global'` or vice versa. Hot reload (`r` in the flutter run terminal) will pick it up instantly.

## Running on a real Android phone instead of emulator

1. Enable Developer mode on the phone (tap "Build Number" 7 times in Settings → About).
2. Turn on USB Debugging in Developer options.
3. Plug phone into Mac via USB.
4. Run `flutter devices` — your phone should show up.
5. Find your Mac's LAN IP: `ipconfig getifaddr en0` (something like `192.168.1.42`).
6. Run:

```bash
flutter run --dart-define=KIWIMATH_API=http://192.168.1.42:8000
```

Phone and Mac must be on the same Wi-Fi.

## Troubleshooting

**"Can't reach Kiwimath backend"** — make sure the backend is actually running in Terminal 1 (visit `http://localhost:8000/health` in your Mac browser). Android emulator reaches the Mac's localhost via `10.0.2.2` — that's automatic.

**Gradle takes forever first time** — normal. 3–5 minutes. Subsequent runs are fast.

**`flutter doctor` shows red rows** — fix them in order, top to bottom. The tool is very clear about what's wrong.

## File layout

```
app/
├── pubspec.yaml          # dependencies (flutter, http, flutter_svg)
├── lib/
│   ├── main.dart         # app entry
│   ├── theme/
│   │   └── kiwi_theme.dart
│   ├── models/
│   │   └── question.dart    # mirrors backend QuestionOut
│   ├── services/
│   │   └── api_client.dart  # HTTP client
│   ├── screens/
│   │   └── question_screen.dart  # main screen
│   └── widgets/
│       ├── svg_visual.dart      # inline SVG renderer
│       └── option_card.dart     # tappable MCQ card
└── README.md             # this file
```
