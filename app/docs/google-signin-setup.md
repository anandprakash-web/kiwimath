# Google Sign-In setup (one-time, 5 minutes)

Google Sign-In on Android requires your app to register an **SHA-1 fingerprint**
(a cryptographic hash of your signing key) with Firebase. This is how Google
knows the sign-in request is coming from YOUR app and not an imposter.

You only do this once per developer machine + signing key.

## Step 1 — Generate the debug SHA-1

```bash
cd ~/Downloads/kiwimath/app/android
./gradlew signingReport
```

Wait ~30 seconds. You'll see a big block of output with multiple "Variant"
sections. Scroll up to find the `Variant: debug` block. It'll look like:

```
Variant: debug
Config: debug
Store: /Users/ap/.android/debug.keystore
Alias: AndroidDebugKey
MD5: ...
SHA1: A1:B2:C3:D4:E5:F6:07:...
SHA-256: ...
```

**Copy the `SHA1` line** (the colon-separated hex string after SHA1:).

## Step 2 — Add it to Firebase

1. Open https://console.firebase.google.com and select your kiwimath project.
2. Click the **gear icon** (top-left, next to "Project overview") → **Project settings**.
3. Scroll down to **"Your apps"** → find your Android app.
4. Click **"Add fingerprint"**.
5. Paste the SHA-1 you copied → **Save**.

## Step 3 — Download the updated google-services.json

Still in Project settings, on your Android app:

1. Click the **"google-services.json"** download link (small icon next to the app name).
2. Save the file.
3. Replace the existing file:

```bash
mv ~/Downloads/google-services.json ~/Downloads/kiwimath/app/android/app/google-services.json
```

(Confirm overwrite if prompted.)

## Step 4 — Clean and rebuild

```bash
cd ~/Downloads/kiwimath/app
flutter clean
flutter pub get
flutter run
```

The clean rebuild picks up the new google-services.json. Takes a couple of
minutes.

## Step 5 — Test

In the emulator:
1. You should see the sign-in screen with a "Continue with Google" button at the top.
2. Tap it.
3. If the emulator has a Google account configured: native account picker appears.
4. Pick an account → brief redirect → you're signed in.
5. Your user appears in Firebase console → Authentication → Users, with
   "Google" as the sign-in provider.

## Common issues

**"ApiException: 10"** — SHA-1 mismatch. Re-check Steps 1–3. The SHA-1 in
Firebase must match what `./gradlew signingReport` shows for the debug variant.

**"ApiException: 12501"** — user cancelled. Not an error.

**No Google account on the emulator** — in the emulator's Settings app, go to
Accounts → Add account → Google → sign in with any Gmail.

**For a real physical phone** — the phone's Google account is used. You'll
need the phone's debug SHA-1 too (same `./gradlew signingReport` command —
same SHA-1 if same machine).

## For production release later

Release builds use a different signing key than debug. When you generate
your release keystore, you'll need to add its SHA-1 to Firebase the same way.
Don't worry about this until we're preparing the Play Store release (Week 11).
