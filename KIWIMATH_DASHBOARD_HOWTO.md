# Kiwimath — Usage & Live Dashboard

Two ways to see who's using the app: a **30-second manual check** (no deploy), and a **live dashboard** (after one deploy).

---

## A · The fastest answer right now (no code, no deploy)

"How many people used it" = how many installs signed in. That's your **Firebase Auth** user list.

1. Open the [Firebase console](https://console.firebase.google.com/) → project **kiwimath-801c1**.
2. **Authentication → Users** → the count at the top is your total users. Each row = one person; "Signed In" shows when they were last active.
3. For *what* they did: **Firestore Database → `users` collection.** Each document is a user; open one to see `grade`, `streak_current`, `xp_total`, `last_active`, plus a `gamification/state` sub-doc (questions answered, accuracy, topics) and a `sessions` sub-collection.

With 7–10 testers this tells you everything in under a minute.

---

## B · The live dashboard (auto-refreshing, pretty)

### ✅ Recommended: open the hosted dashboard URL (no file, no CORS)

The backend now **serves the dashboard itself** at `/v3/dashboard`, so it's same-origin with the data and just works in any browser — nothing to download.

1. Deploy once: `cd ~/Downloads/kiwimath/backend && ./deploy.sh`
2. Open (and bookmark):

```
https://kiwimath-api-deufqab6gq-el.a.run.app/v3/dashboard?key=kmx-founder-7Q2v9Lp4Ad
```

That's it — KPIs, charts, and the per-user table, auto-refreshing every 60s. Leave it open on a second monitor.

### Alternative: the local file (`kiwimath_dashboard.html`)
The downloadable file does the same thing, but because it's a `file://` page reading a different domain, some browsers block it with a CORS error ("Couldn't reach the backend"). If that happens, use the hosted URL above instead — it has no such limitation. (The endpoint `GET /v3/admin/usage` lives in `backend/app/api/usage.py`, wired into `main.py`.)

### What it shows
- **KPIs:** total users, active today / this week, new this week, questions answered, average accuracy, sessions, anonymous logins.
- **Charts:** new users by day, users by grade, top topics practised.
- **Per-user table:** name, grade, joined, last seen (today / Nd ago), questions, accuracy, sessions, streak, XP — click any column header to sort.

---

## The admin key (security)

The endpoint is gated by a key so only you can read it. Default: `kmx-founder-7Q2v9Lp4Ad`.

To rotate it (recommended once you have real users): set an env var on the service and put the same value in the dashboard's "admin key" box.

```bash
# in backend/deploy.sh, add to the --set-env-vars list:
KIWIMATH_ADMIN_KEY=your-own-long-secret
```

The endpoint only ever returns **aggregate, read-only** stats (counts, accuracy, last-seen). It changes nothing. Still, treat the key like a password.

---

## What the numbers mean

- **Total users = Firebase Auth accounts** = installs that signed in (even anonymously). This is the truest "how many people."
- **Active today / this week** = most recent of their last sign-in and last activity.
- **Questions / accuracy / sessions / streak / XP** = from each user's `gamification/state` in Firestore — the real record of what they did.
- The older `/admin/analytics/overview` endpoint reads in-memory data and **undercounts** on Cloud Run (it only sees users loaded into the current server instance) — the new `/v3/admin/usage` reads Firebase/Firestore directly, so it's accurate.

---

## If the dashboard won't load

- **"Unauthorized"** → the key in the box doesn't match the server. Use the default, or whatever you set `KIWIMATH_ADMIN_KEY` to.
- **"Couldn't reach the backend" / CORS** → make sure you ran `./deploy.sh`. If your browser still blocks the cross-origin read, click **"open the JSON"** in the error message to view the raw numbers directly (that always works).
- **"data layer unavailable"** → the endpoint is live but the server couldn't reach Firestore; check the service's permissions/logs.
