#!/usr/bin/env python3
"""
Kiwimath Firestore cleanup tool — SAFE BY DEFAULT (dry-run unless --execute).

Run from your Mac (needs your Google credentials):
    cd ~/Downloads/kiwimath/backend
    pip3 install firebase-admin            # if not installed
    gcloud auth application-default login  # one-time credential setup

USAGE
  1. Audit first (always start here — read-only, lists every collection + counts):
       python3 scripts/cleanup_firestore.py audit

  2. Preview what a cleanup WOULD delete (dry-run, nothing deleted):
       python3 scripts/cleanup_firestore.py prune-logs --older-than-days 30
       python3 scripts/cleanup_firestore.py prune-locks
       python3 scripts/cleanup_firestore.py prune-idempotency
       python3 scripts/cleanup_firestore.py delete-test-users --prefix test_ --prefix demo_
       python3 scripts/cleanup_firestore.py delete-collection some_old_collection

  3. Actually delete — add --execute to any command above:
       python3 scripts/cleanup_firestore.py prune-logs --older-than-days 30 --execute

WHAT EACH COMMAND CLEANS
  audit               read-only inventory: every top-level collection, doc count,
                      one sample doc id, estimated junk
  prune-logs          response_logs older than N days (one doc per answer ever
                      given — the biggest growth collection; safe to prune, used
                      only for IRT calibration which needs recent data)
  prune-locks         expired session_locks (expires_at in the past)
  prune-idempotency   expired idempotency_keys (expires_at in the past)
  delete-test-users   user-scoped docs whose ID starts with given prefixes,
                      across: users, gamification, ability_v2, mastery, sessions,
                      response_logs (by student_id), daily_puzzle_streaks,
                      engagement_rewards, pledges, diagnostic_sessions
  delete-collection   nuke one named collection entirely (recursive — handles
                      subcollections like clans/{id}/challenges). Requires
                      --i-am-sure together with --execute.
"""

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    sys.exit("firebase-admin not installed. Run: pip3 install firebase-admin")

BATCH = 400  # Firestore batch limit is 500; stay under it

USER_SCOPED_COLLECTIONS = [
    "users", "gamification", "ability_v2", "mastery", "sessions",
    "daily_puzzle_streaks", "engagement_rewards", "pledges",
    "diagnostic_sessions", "streak_freezes",
]


def get_db():
    if not firebase_admin._apps:
        # Uses GOOGLE_APPLICATION_CREDENTIALS or gcloud Application Default Credentials
        firebase_admin.initialize_app()
    return firestore.client()


def count_collection(db, name):
    """Cheap aggregation count; falls back to streaming count capped at 50k."""
    try:
        agg = db.collection(name).count().get()
        return int(agg[0][0].value)
    except Exception:
        n = 0
        for _ in db.collection(name).limit(50000).stream():
            n += 1
        return n


def delete_query(db, query, label, execute, recursive=False):
    """Delete all docs matching a query, in batches. Returns count."""
    deleted = 0
    while True:
        docs = list(query.limit(BATCH).stream())
        if not docs:
            break
        if not execute:
            deleted += len(docs)
            if len(docs) < BATCH:
                break
            # dry-run: we can't paginate a delete-as-you-go query without
            # deleting, so report ">= count" and stop
            print(f"  [dry-run] {label}: at least {deleted} docs match (stopped counting)")
            return deleted
        batch = db.batch()
        for d in docs:
            if recursive:
                for sub in d.reference.collections():
                    delete_query(db, sub, f"{label}/{d.id}/{sub.id}", execute, recursive=True)
            batch.delete(d.reference)
        batch.commit()
        deleted += len(docs)
        print(f"  deleted {deleted} so far from {label}...")
        time.sleep(0.1)
    return deleted


def cmd_audit(db, args):
    print(f"== Firestore audit ({datetime.now(timezone.utc).isoformat()}) ==\n")
    total = 0
    rows = []
    for coll in db.collections():
        n = count_collection(db, coll.id)
        total += n
        sample = next(iter(coll.limit(1).stream()), None)
        rows.append((coll.id, n, sample.id if sample else "-"))
    rows.sort(key=lambda r: -r[1])
    print(f"{'collection':<32}{'docs':>10}   sample doc id")
    print("-" * 70)
    for name, n, sample in rows:
        print(f"{name:<32}{n:>10}   {sample}")
    print("-" * 70)
    print(f"{'TOTAL':<32}{total:>10}")
    print("\nLikely junk candidates:")
    print("  - response_logs: prune anything older than ~30-60 days (prune-logs)")
    print("  - session_locks / idempotency_keys: expired docs (prune-locks / prune-idempotency)")
    print("  - any *test*/demo user ids you recognize (delete-test-users --prefix ...)")
    print("  - collections you don't recognize from the table above (delete-collection)")


def cmd_prune_logs(db, args):
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    print(f"Pruning response_logs older than {args.older_than_days} days "
          f"(before {cutoff.date()}) {'[EXECUTE]' if args.execute else '[dry-run]'}")
    # response_logs docs store a timestamp field; try common field names
    for field in ("timestamp", "created_at", "ts"):
        try:
            q = db.collection("response_logs").where(field, "<", cutoff)
            n = delete_query(db, q, f"response_logs.{field}", args.execute)
            if n:
                print(f"  -> {n} docs ({'deleted' if args.execute else 'would delete'}) via field '{field}'")
                return
        except Exception as e:
            print(f"  (field '{field}' not usable: {e})")
    print("  No prunable docs found (or timestamp field mismatch — run audit and check a sample doc).")


def cmd_prune_locks(db, args):
    now = time.time()
    print(f"Pruning expired session_locks {'[EXECUTE]' if args.execute else '[dry-run]'}")
    q = db.collection("session_locks").where("expires_at", "<", now)
    n = delete_query(db, q, "session_locks", args.execute)
    print(f"  -> {n} expired locks ({'deleted' if args.execute else 'would delete'})")


def cmd_prune_idempotency(db, args):
    now = time.time()
    print(f"Pruning expired idempotency_keys {'[EXECUTE]' if args.execute else '[dry-run]'}")
    q = db.collection("idempotency_keys").where("expires_at", "<", now)
    n = delete_query(db, q, "idempotency_keys", args.execute)
    print(f"  -> {n} expired keys ({'deleted' if args.execute else 'would delete'})")
    print("  Tip: enable a Firestore TTL policy on idempotency_keys.expires_at to automate this.")


def cmd_delete_test_users(db, args):
    if not args.prefix:
        sys.exit("Provide at least one --prefix (e.g. --prefix test_ --prefix demo_)")
    print(f"Deleting user-scoped docs with id prefixes {args.prefix} "
          f"{'[EXECUTE]' if args.execute else '[dry-run]'}")
    grand = 0
    for coll in USER_SCOPED_COLLECTIONS:
        for prefix in args.prefix:
            # ID range scan: [prefix, prefix + ]
            q = (db.collection(coll)
                 .where("__name__", ">=", db.collection(coll).document(prefix))
                 .where("__name__", "<", db.collection(coll).document(prefix + "")))
            n = delete_query(db, q, f"{coll} ({prefix}*)", args.execute, recursive=True)
            if n:
                print(f"  {coll}: {n} docs matching '{prefix}*'")
                grand += n
    # response_logs are keyed by auto-id but carry student_id field
    for prefix in args.prefix:
        q = (db.collection("response_logs")
             .where("student_id", ">=", prefix)
             .where("student_id", "<", prefix + ""))
        try:
            n = delete_query(db, q, f"response_logs (student {prefix}*)", args.execute)
            if n:
                print(f"  response_logs: {n} docs for students '{prefix}*'")
                grand += n
        except Exception as e:
            print(f"  response_logs scan failed (may need an index): {e}")
    print(f"TOTAL: {grand} docs {'deleted' if args.execute else 'would be deleted'}")


def cmd_delete_collection(db, args):
    if args.execute and not args.i_am_sure:
        sys.exit("Refusing: deleting a whole collection needs BOTH --execute and --i-am-sure")
    print(f"Deleting ENTIRE collection '{args.name}' "
          f"{'[EXECUTE]' if args.execute else '[dry-run]'}")
    n = delete_query(db, db.collection(args.name), args.name, args.execute, recursive=True)
    print(f"  -> {n} docs ({'deleted' if args.execute else 'would delete'})")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("audit")
    sp = sub.add_parser("prune-logs")
    sp.add_argument("--older-than-days", type=int, default=30)
    sub.add_parser("prune-locks")
    sub.add_parser("prune-idempotency")
    sp = sub.add_parser("delete-test-users")
    sp.add_argument("--prefix", action="append", default=[])
    sp = sub.add_parser("delete-collection")
    sp.add_argument("name")
    sp.add_argument("--i-am-sure", action="store_true")

    for name, spp in sub.choices.items():
        spp.add_argument("--execute", action="store_true",
                         help="Actually delete (default is dry-run)")

    args = p.parse_args()
    db = get_db()
    {
        "audit": cmd_audit,
        "prune-logs": cmd_prune_logs,
        "prune-locks": cmd_prune_locks,
        "prune-idempotency": cmd_prune_idempotency,
        "delete-test-users": cmd_delete_test_users,
        "delete-collection": cmd_delete_collection,
    }[args.cmd](db, args)


if __name__ == "__main__":
    main()
