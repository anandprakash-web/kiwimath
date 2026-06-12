# Kiwimath — Your Step-by-Step Guide

Everything code-side is already fixed in this folder. These are the steps only you can do, in order. Each step is copy-paste ready for Terminal on your Mac. Total time: ~1–2 hours (plus Flutter build time).

---

## Step 1 — Rotate the Gemini API key (5 min) 🔴 DO THIS FIRST

The old key is in your git history on GitHub, so treat it as stolen.

1. Go to https://aistudio.google.com/apikey
2. Create a new key. **Delete the old one** (the one starting `AIzaSyBK`).
3. Put the new key in your local `.env` only:
   ```bash
   cd ~/Downloads/kiwimath
   echo 'GEMINI_API_KEY=PASTE_NEW_KEY_HERE' > .env
   ```
   (`.env` is gitignored — it will never be committed. `.env.save` has already been neutralized and untracked.)

## Step 2 — Commit and push everything (10 min)

```bash
cd ~/Downloads/kiwimath
git add -A
git commit -m "Security hardening, Firestore persistence, content fixes, UI quick wins, junk cleanup"
git push
```

If push fails with `index.lock`, run `rm -f .git/index.lock` and retry.
If push fails complaining about file size, the big files are already untracked in this commit — but they may exist in **history**. Fix history in the same pass as the leaked key:

```bash
brew install bfg
cd ~/Downloads
git clone --mirror https://github.com/anandprakash-web/kiwimath.git kiwimath-mirror.git
bfg --delete-files .env.save --strip-blobs-bigger-than 90M kiwimath-mirror.git
cd kiwimath-mirror.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```
Then back in `~/Downloads/kiwimath`: `git fetch origin && git reset --hard origin/main` (or your branch name).

## Step 3 — Set Cloud Run secrets & admin (5 min)

```bash
gcloud run services update kiwimath-api --region asia-south1 \
  --set-env-vars "KIWIMATH_INTERNAL_API_KEY=$(openssl rand -hex 32),KIWIMATH_ADMIN_EMAILS=anand.prakash@vedantu.com"
```

Then update the Cloud Scheduler cron to send the same key as a header (commands and details are documented inside `backend/deploy/clan_cron.yaml`). To see the key you just set:
```bash
gcloud run services describe kiwimath-api --region asia-south1 --format json | grep -A1 KIWIMATH_INTERNAL
```
⚠️ Never set `KIWIMATH_AUTH_DISABLED` on production.

## Step 4 — Verify the Flutter app builds (15 min)

I couldn't run Flutter in my sandbox, so this is the safety gate:

```bash
cd ~/Downloads/kiwimath/app
flutter pub get        # pulls the new google_fonts package
flutter analyze        # must show no NEW errors
flutter test           # 5 tests should pass
```

If `flutter analyze` flags anything in files mentioned in `FIXES_APPLIED_2026-06-12.md`, send me the output and I'll fix it.

## Step 5 — Deploy: backend FIRST, then app (30 min)

Order matters: the new app sends auth headers the old backend simply ignores (safe), but the new backend rejects old unauthenticated apps — so backend first, app update promptly after.

```bash
cd ~/Downloads/kiwimath/backend && ./deploy.sh
```

Smoke-test the deployed backend:
```bash
URL=https://kiwimath-api-deufqab6gq-el.a.run.app
curl -s $URL/health            # expect 200 OK
curl -s -o /dev/null -w "%{http_code}\n" $URL/docs           # expect 404 (locked)
curl -s -o /dev/null -w "%{http_code}\n" $URL/debug/content  # expect 404 (locked)
curl -s -o /dev/null -w "%{http_code}\n" $URL/v2/topics      # expect 401 (auth required)
curl -s -o /dev/null -w "%{http_code}\n" $URL/cms            # expect 401/403 (admin only)
```

Then build and test the app on a device:
```bash
cd ~/Downloads/kiwimath/app && flutter build apk --release
```
On-device checklist: sign in → answer 2–3 questions (feel the haptics, see the skeleton between questions, score count-up at the end) → check headings render in Baloo 2 / body in Nunito → open a question with a picture (SVG must load) → daily puzzle: answer wrong on purpose (must NOT say correct) → parent dashboard opens with your PIN.

## Step 6 — Clean the database (Firestore) (15 min)

I wrote you a safe cleanup tool: `backend/scripts/cleanup_firestore.py`. It NEVER deletes anything unless you add `--execute`.

```bash
cd ~/Downloads/kiwimath/backend
pip3 install firebase-admin                 # once
gcloud auth application-default login       # once

# 1. See what's in the database (read-only inventory of every collection):
python3 scripts/cleanup_firestore.py audit

# 2. Preview cleanups (dry-run — shows what WOULD be deleted):
python3 scripts/cleanup_firestore.py prune-logs --older-than-days 30
python3 scripts/cleanup_firestore.py prune-locks
python3 scripts/cleanup_firestore.py prune-idempotency
python3 scripts/cleanup_firestore.py delete-test-users --prefix test_ --prefix demo_

# 3. When happy with a preview, add --execute to run it for real, e.g.:
python3 scripts/cleanup_firestore.py prune-logs --older-than-days 30 --execute
```

Send me the `audit` output if you want — I'll tell you exactly which collections are junk and which commands to run. For any collection you don't recognize:
`python3 scripts/cleanup_firestore.py delete-collection NAME` (preview) then add `--execute --i-am-sure`.

## Step 7 — Firestore housekeeping (5 min, in the web console)

1. **TTL policy**: Firebase Console → Firestore → TTL → add policy on collection `idempotency_keys`, field `expires_at`. (Auto-deletes old keys forever — no script needed.)
2. **Indexes**: the first time clan screens run against the new persistence, Cloud Run logs may show "index required" errors with a direct creation link — click each link once. (Queries involved: clan member lookup, invite codes, grade leaderboards.)

## Step 8 — Enable Firebase App Check (15 min, recommended before public launch)

Console → App Check → register the Android app with **Play Integrity**. Then in the app add the `firebase_app_check` package and call `FirebaseAppCheck.instance.activate()` after `Firebase.initializeApp()` in `main.dart`. Tell me when you're ready and I'll wire the code side.

## Step 9 — Already-cleaned folder (FYI, nothing to do)

I cleared **~1.4 GB** of junk from the project folder (1.9 GB → 513 MB): `_archive/`, `archived_duplicates/`, `app/archive_v1/`, `backend/.venv`, Flutter/Gradle build artifacts, caches, lock/tmp files, the `old jason/` config backups, and `all_questions.json.bak`. Everything deleted was either regenerable or preserved in git history. I also untracked the 117 MB + 81 MB `all_questions*.json` files from git (they stay on disk — they hold the "why" explanations) so GitHub stops rejecting your pushes.

---

## What's intentionally still open (no action needed now)

- Olympiad/wavebook/offline-bundle endpoints still include answers at fetch time (needed for offline play; now auth-gated). Follow-up: signed offline bundles.
- 2,747 school-curriculum chapter refs point to questions deleted in the May dedup (3 Singapore chapters empty) — needs chapters.json regeneration.
- Grades 5–6 content depth, Rive mascot, TTS/audio, illustrations, tablet layouts — Phase 3 roadmap in `LAUNCH_READINESS_AUDIT_2026-06-12.md`.

**Stuck on any step? Paste the error output to me and I'll sort it.**
