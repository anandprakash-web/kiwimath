# Kiwimath — Your Step-by-Step Launch Checklist

Everything Claude built is on disk and verified; these are the steps only **you** can run (your Mac, your Google/Firebase/Play credentials). Do them in order. Each step says what it does, the exact command, and how to confirm it worked.

Legend: **[RUN]** = copy-paste command · **[DECIDE]** = a choice · **[BUILD]** = Flutter engineering.

Project facts: GCP project `kiwimath-801c1` · region `asia-south1` · service `kiwimath-api` · repo `~/Downloads/kiwimath`.

---

## Phase 0 — Security first (~20 min) ⚠️ do before anything public

**Step 1 [DECIDE/RUN] — Rotate the Gemini key + scrub git history.**
Only skip if you already did this on 2026-06-12. If unsure, assume you didn't.
```bash
# 1a. In Google AI Studio: create a NEW Gemini API key, DELETE the old one.
# 1b. Put the new key in local .env ONLY (never commit it).
# 1c. Purge the old key from git history:
cd ~/Downloads/kiwimath
brew install bfg            # or: pip install git-filter-repo
bfg --delete-files .env.save
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force origin main
```
✅ Confirm: `git log --all -- .env.save` shows nothing, and the old key is dead in AI Studio.

---

## Phase 1 — Commit & push the work (~10 min)

**Step 2 [RUN] — Clear the stale git lock** (the sandbox couldn't remove it):
```bash
cd ~/Downloads/kiwimath && rm -f .git/index.lock
```

**Step 3 [RUN] — Optional: delete the 9 dead Flutter screens** (unreferenced, harmless, but tidy):
```bash
cd ~/Downloads/kiwimath/app/lib/screens
rm -f home_screen.dart olympiad_screen.dart learning_path_screen.dart \
  topic_level_map_screen.dart companion_picker_screen.dart grade_upgrade_screen.dart \
  clan_hub_screen.dart downloads_screen.dart explanation_screen.dart
```

**Step 4 [RUN] — Review, commit, push.**
```bash
cd ~/Downloads/kiwimath
git status            # sanity-check the changes are what you expect
git add -A
git commit -m "Level/Grade remap + olympiad QA + backend /v3 rewire + 4-tab prototype + Flutter /v3 client"
git push origin main
```
✅ Confirm: `git push` succeeds; GitHub shows the new commit.

---

## Phase 2 — Deploy the backend (DB push) (~15 min) — this is "live" and ready

**Step 5 [RUN] — Set Cloud Run env vars (one-time).**
```bash
gcloud run services update kiwimath-api --region asia-south1 \
  --update-env-vars KIWIMATH_ADMIN_EMAILS=anand.prakash@vedantu.com,KIWIMATH_INTERNAL_API_KEY=$(openssl rand -hex 32)
```
(Then update the Cloud Scheduler clan-cron job to send that same key as the `X-Internal-Key` header — commands are in `backend/deploy/clan_cron.yaml`.)

**Step 6 [RUN] — Verify content, then deploy.**
```bash
cd ~/Downloads/kiwimath/backend
python3 pre_deploy_check.py        # expect: ✅ ALL CHECKS PASSED (olympiad 18,099 + curriculum 10,340)
./deploy.sh                        # bakes content + sets /v3 env vars; uses 4Gi
```

**Step 7 [RUN] — Confirm /v3 is live.**
```bash
curl https://kiwimath-api-deufqab6gq-el.a.run.app/health
```
✅ Confirm: the JSON shows `content_level: { olympiad_total: 18099, curriculum_total: 10340 }`.

> At this point the backend + remapped content are LIVE and verified. The old app keeps working; `/v3` is ready for the new app.

---

## Phase 3 — Finish the Flutter app on /v3 (the engineering block) [BUILD]

The `/v3` client (`app/lib/services/level_service.dart`) is written and ready; the screens still call `/v2`+`/v4`. This is the one part that needs a Flutter build environment (your Mac). Two ways to do it:

- **Option A (recommended):** ask Claude to write each screen change; you run `flutter analyze` after each and report errors back, until clean. This is how to converge safely without Claude being able to compile.
- **Option B:** you or a Flutter dev wire it using `kiwimath_prototype.html` as the exact screen spec.

The wiring, in order (uses `LevelService`):
**Step 8** — `cd ~/Downloads/kiwimath/app && flutter pub get`
**Step 9** — Olympiad tab → level picker L1–L8 → topics → `getNextQuestion` (no question counts shown).
**Step 10** — School tab → `getBoards` / `getGrades` / `getChapters` (already sequenced) / `getChapterQuestions`.
**Step 11** — Answer flow → `checkAnswer(...)`; refresh the wallet from its response.
**Step 12** — Progress → `getProgress` (Academic Height gauge + 4 pillars + Logic & Puzzles); Profile + the top wallet → `getWallet`. (All read one source = no disjoint.)
**Step 13** — Add fonts: drop `Nunito` + `Baloo 2` TTFs into `app/assets/fonts/`, declare them in `pubspec.yaml`, point `kiwi_theme.dart` at them (kills the runtime font fetch).
**Step 14** — Clan: add one entry point (a Progress sub-tab) or cut the dead clan code.
**Step 15 [RUN]** — Gate:
```bash
cd ~/Downloads/kiwimath/app && flutter analyze && flutter test
```
✅ Confirm: `flutter analyze` → **No issues found.**

---

## Phase 4 — Build & smoke-test the APK (~20 min) [RUN/BUILD]

**Step 16 [RUN]**
```bash
cd ~/Downloads/kiwimath/app
flutter build apk --release          # or: flutter build appbundle  (for Play Store)
```
**Step 17** — Install on a real device and walk the flows:
sign in → Olympiad (L1–L3 live, L4–L8 "coming soon") → answer a question (coins/XP/streak update **identically** on every tab) → School → grade → sequenced chapters → Progress (Academic Height + strands) → Me (edit/switch/sign-out, Parent PIN).
✅ Confirm: no crashes; numbers consistent across tabs.

---

## Phase 5 — Staged Play Store launch [RUN/STORE]

**Step 18** — Enable **Firebase App Check** (Console + a few app lines) to lock the client API keys.
**Step 19** — **Closed testing** (Play Console → 50–100 friendly families). Watch: crash-free >99%, that streaks/coins survive a redeploy.
**Step 20** — **Open testing / one Indian state**. Watch: D1/D7 retention, content-flag rate, cost per child.
**Step 21** — **Production** at 10–20% rollout once crash-free >99.5% and the Play **Data Safety** form matches real collection (child name + grade).

---

## Go / No-Go before public

- [ ] Gemini key rotated + history clean (Step 1)
- [ ] Backend deployed; `/health` shows `content_level` (Step 7)
- [ ] App points at `/v3`; `flutter analyze` clean (Step 15)
- [ ] APK smoke-tested; numbers consistent across tabs (Step 17)
- [ ] App Check on; privacy/Data-Safety accurate (Steps 18, 21)

**If you want to ship sooner:** Phases 0–2 + building the *current* app (skip Phase 3) launches the old grade-based experience now. The remapped Level/Grade experience needs Phase 3.
