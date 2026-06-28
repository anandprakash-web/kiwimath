#!/usr/bin/env bash
# ============================================================================
# SHIP GATE — run this BEFORE every ./deploy.sh.  Protects the MOAT:
#   the skill questions, the nested cluster questions, and the adaptive ruleset.
#
#   ./ship_gate.sh        # full gate
#
# A change may only ship if this prints "GATE GREEN".  If anything is red,
# DO NOT DEPLOY — inspect first.  (The founder's rule, 2026-06-28.)
# ============================================================================
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BK="$ROOT/backend"
export PYTHONPATH="$BK"
export KIWIMATH_OLYMPIAD_CONTENT_DIR="$ROOT/content-live/olympiad"
export KIWIMATH_CURRICULUM_CONTENT_DIR="$ROOT/content-live/curriculum"
export KIWIMATH_CONTEST_ALWAYS_OPEN=1

# Highest count of content-scanner flags we currently tolerate (the known,
# pre-existing L3–L7 backlog). A change must NEVER push it higher.
# Lower this number whenever a real fix pass reduces the backlog.
SCANNER_BASELINE=80

fails=0
note(){ printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
ok(){   printf '   \033[32mOK\033[0m   %s\n' "$1"; }
bad(){  printf '   \033[31mFAIL\033[0m %s\n' "$1"; fails=$((fails+1)); }

# 1) Counts / IDs / visuals -------------------------------------------------
note "1. pre_deploy_check (counts, ids, visuals)"
out="$(cd "$BK" && python3 pre_deploy_check.py 2>&1)"
echo "$out" | grep -q "ALL CHECKS PASSED" && ok "pre_deploy green" || { echo "$out" | tail -5; bad "pre_deploy_check"; }

# 2) Content defect scanner (A–N) — must not increase -----------------------
note "2. content_qa_scan (A–N detectors)"
sc="$(cd "$ROOT/content-live/qa-reports" && python3 content_qa_scan.py 2>&1)"
flags="$(echo "$sc" | sed -n 's/.*TOTAL outstanding flags: *\([0-9][0-9]*\).*/\1/p' | tail -1)"
flags="${flags:-999}"
if [ "$flags" -le "$SCANNER_BASELINE" ]; then ok "scanner flags = $flags (<= baseline $SCANNER_BASELINE)";
else echo "$sc" | tail -20; bad "scanner flags ROSE to $flags (baseline $SCANNER_BASELINE) — a change introduced content defects"; fi

# 3) Skill / nested-cluster tag integrity (the moat structure) --------------
note "3. skill + nested tags intact on the served bank"
tagout="$(cd "$ROOT" && python3 - <<'PY'
import json,glob
tot=mi=ms=md=0
for f in glob.glob('content-live/olympiad/L*/L*_*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    qs=d.get('questions',[]) if isinstance(d,dict) else (d if isinstance(d,list) else [])
    for q in qs:
        if not (isinstance(q,dict) and 'stem' in q): continue
        tot+=1
        if 'skill_id' not in q: mi+=1
        if q.get('skill_seq') is None: ms+=1
        if q.get('skill_difficulty') is None: md+=1
print(f"{tot} {mi} {ms} {md}")
PY
)"
read -r TOT MI MS MD <<<"$tagout"
if [ "${MI:-1}" = 0 ] && [ "${MS:-1}" = 0 ] && [ "${MD:-1}" = 0 ]; then
  ok "all $TOT served questions carry skill_id + skill_seq + skill_difficulty"
else bad "missing tags — skill_id:$MI skill_seq:$MS skill_difficulty:$MD (re-run cluster_concepts.py)"; fi

# 4) Smoke suites -----------------------------------------------------------
for t in smoke_level_v3 smoke_adaptive_skill smoke_contest_league smoke_store smoke_challenge; do
  note "4. $t"
  o="$(cd "$BK" && python3 "tests/$t.py" 2>&1)"
  nfail="$(echo "$o" | grep -c '\[FAIL\]')"
  if echo "$o" | grep -q "DONE" && [ "$nfail" = 0 ]; then ok "$t passed"; else echo "$o" | grep -E '\[FAIL\]|Error|Traceback' | head -8; bad "$t"; fi
done

# Verdict -------------------------------------------------------------------
echo
if [ "$fails" = 0 ]; then
  printf '\033[1;32m========== GATE GREEN — safe to ./deploy.sh ==========\033[0m\n'; exit 0
else
  printf '\033[1;31m========== GATE RED (%s failed) — DO NOT DEPLOY ==========\033[0m\n' "$fails"; exit 1
fi
