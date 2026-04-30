# Kiwimath — Play Store Submission Guide

## Pre-submission: Things I've Already Done

- [x] App icon generated (all 5 densities + adaptive icon)
- [x] App name set to "Kiwimath" in AndroidManifest.xml
- [x] Version set to 1.0.0+1 in pubspec.yaml
- [x] applicationId set to `com.kiwimath.app`
- [x] Release signing config wired in build.gradle.kts
- [x] ProGuard rules added for Flutter + Firebase
- [x] Feature graphic created (1024x500) in `playstore_assets/`
- [x] Play Store listing text written in `playstore_assets/listing.txt`
- [x] Privacy policy updated for Grades 1-6
- [x] Firebase Hosting config created for privacy policy

---

## Step 1: Generate Upload Keystore (one-time, ~2 min)

```bash
cd ~/Downloads/kiwimath/app/android
chmod +x generate_keystore.sh
./generate_keystore.sh
```

You'll be prompted for a password. **Remember this password** and **back up the .jks file** — you can never update the app without it.

Then create the `key.properties` file:

```bash
cat > ~/Downloads/kiwimath/app/android/key.properties << 'EOF'
storePassword=YOUR_PASSWORD_HERE
keyPassword=YOUR_PASSWORD_HERE
keyAlias=kiwimath-upload
storeFile=/Users/YOUR_USERNAME/kiwimath-upload-key.jks
EOF
```

Replace `YOUR_PASSWORD_HERE` and `YOUR_USERNAME` with your actual values.

---

## Step 2: Deploy Backend (updated content)

```bash
cd ~/Downloads/kiwimath/backend
chmod +x deploy.sh
./deploy.sh
```

Wait for "Service deployed successfully" message.

---

## Step 3: Host Privacy Policy

```bash
cd ~/Downloads/kiwimath
firebase deploy --only hosting
```

Your privacy policy will be at: `https://kiwimath-801c1.web.app/privacy-policy.html`

If you haven't set up Firebase CLI:
```bash
npm install -g firebase-tools
firebase login
firebase init hosting  # select kiwimath-801c1 project, use "public" folder
firebase deploy --only hosting
```

---

## Step 4: Build App Bundle (AAB)

Google Play now requires AAB format (not APK):

```bash
cd ~/Downloads/kiwimath/app
flutter build appbundle --release
```

The bundle will be at:
`build/app/outputs/bundle/release/app-release.aab`

---

## Step 5: Take Screenshots

You'll need at least 2 screenshots (recommended 4-8) for each device type. Run the app on an emulator or device:

```bash
flutter run --release
```

Take screenshots of:
1. **Home screen** — showing topic cards
2. **Question screen** — a question with options
3. **Correct answer** — celebration animation
4. **Hint system** — showing a hint expanded
5. **Parent dashboard** (if visible in app)

Screenshot specs:
- Phone: minimum 320px, maximum 3840px (any side)
- 16:9 or 9:16 aspect ratio recommended
- PNG or JPEG format

---

## Step 6: Google Play Console Submission

### 6a. Go to [play.google.com/console](https://play.google.com/console)

### 6b. Create New App
- App name: **Kiwimath**
- Default language: **English (United States)**
- App type: **App** (not Game)
- Free or paid: **Free**
- Accept declarations

### 6c. Store Listing
- **Short description**: Copy from `playstore_assets/listing.txt`
- **Full description**: Copy from `playstore_assets/listing.txt`
- **App icon**: Upload `app_icon_512.png` (512x512)
- **Feature graphic**: Upload `playstore_assets/feature_graphic.png` (1024x500)
- **Screenshots**: Upload at least 2 phone screenshots

### 6d. Content Rating
- Go to **Policy → App content → Content rating**
- Start the IARC questionnaire
- Answer: No violence, no sexual content, no gambling, no user interaction
- This will give you an **Everyone** rating

### 6e. Target Audience & Children's Policy
- **Target age group**: 5-12 years old
- **Appeals to children**: Yes
- **Ads**: No ads in the app
- **Privacy policy URL**: `https://kiwimath-801c1.web.app/privacy-policy.html`
- **Teachers Approved program**: Optional, apply later if desired

### 6f. Data Safety
- Go to **Policy → App content → Data safety**
- The app collects:
  - Email address (for Firebase Auth) — required for app functionality
  - App activity (answers, scores) — for personalization
- The app does NOT:
  - Share data with third parties
  - Collect location data
  - Collect financial data
  - Use tracking or advertising

### 6g. App Release
- Go to **Release → Production**
- Upload the AAB file from Step 4
- Set release name: `1.0.0`
- Add release notes: "Initial release — 10,000+ adaptive math questions for Grades 1-6"
- Review and start rollout

---

## Step 7: Post-Submission

- Review typically takes **1-3 business days**
- Check for policy violations in Play Console dashboard
- Once approved, the app goes live on the Play Store
- Share the Play Store link!

---

## Important Files Reference

| File | Purpose |
|------|---------|
| `app/android/key.properties` | Signing credentials (DO NOT commit) |
| `~/kiwimath-upload-key.jks` | Upload keystore (BACK UP!) |
| `playstore_assets/feature_graphic.png` | Play Store header image |
| `playstore_assets/listing.txt` | Store description text |
| `app_icon_512.png` | High-res icon for Play Store |
| `privacy-policy.html` | Privacy policy (host publicly) |
| `firebase.json` | Firebase Hosting config |
