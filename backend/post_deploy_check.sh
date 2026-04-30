#!/usr/bin/env bash
# Kiwimath Post-Deployment Verification
# Run this AFTER deploy.sh to confirm the live API is correct.
#
# Usage: bash post_deploy_check.sh

API_URL="${API_URL:-https://kiwimath-api-deufqab6gq-el.a.run.app}"

echo "=== Kiwimath Post-Deploy Check ==="
echo "API: $API_URL"
echo ""

# Step 1: Health check
echo ">>> Step 1: Health endpoint..."
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
echo ""

# Step 2: Check total question count
TOTAL=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['total_questions'])" 2>/dev/null)
echo ">>> Step 2: Total questions = $TOTAL"
if [ "$TOTAL" = "4800" ]; then
    echo "   ✅ Correct! 4800 questions loaded."
else
    echo "   ❌ WRONG! Expected 4800, got $TOTAL"
    echo "   Content was not baked correctly. Check deploy.sh output."
    exit 1
fi
echo ""

# Step 3: Check per-topic counts
echo ">>> Step 3: Per-topic counts..."
echo "$HEALTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
topics = d['content']['questions_per_topic']
all_ok = True
for tid, count in sorted(topics.items()):
    status = '✅' if count == 600 else '❌'
    if count != 600: all_ok = False
    print(f'   {status} {tid}: {count}')
if all_ok:
    print('   All 8 topics have 600 questions each.')
else:
    print('   SOME TOPICS HAVE WRONG COUNTS!')
" 2>/dev/null
echo ""

# Step 4: Test v2/topics endpoint with grade filter
echo ">>> Step 4: Grade 1 topics (difficulty 1-50)..."
G1_TOPICS=$(curl -s "$API_URL/v2/topics?grade=1")
echo "$G1_TOPICS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
topics = data if isinstance(data, list) else data.get('topics', [])
total = 0
for t in topics:
    name = t.get('topic_name', t.get('topic_id', '?'))
    count = t.get('total_questions', 0)
    total += count
    print(f'   {name}: {count} questions')
print(f'   Total Grade 1 questions: {total}')
if total > 2000:
    print('   ✅ Grade 1 has sufficient questions')
else:
    print(f'   ⚠️  Expected ~2400 Grade 1 questions, got {total}')
" 2>/dev/null
echo ""

# Step 5: Test a sample question
echo ">>> Step 5: Sample question fetch..."
SAMPLE=$(curl -s "$API_URL/v2/next?topic_id=counting_observation&difficulty=25")
echo "$SAMPLE" | python3 -c "
import sys, json
q = json.load(sys.stdin)
print(f'   ID: {q.get(\"id\", \"?\")}')
print(f'   Stem: {q.get(\"stem\", \"?\")[:80]}...')
print(f'   Choices: {len(q.get(\"choices\", []))}')
print(f'   Has visual: {bool(q.get(\"visual_svg\"))}')
print(f'   Has hint: {bool(q.get(\"hint\"))}')
print(f'   Difficulty: {q.get(\"difficulty_score\", \"?\")}')
if q.get('id') and q.get('stem') and len(q.get('choices',[])) == 4:
    print('   ✅ Question fetched successfully')
else:
    print('   ❌ Question fetch failed or incomplete')
" 2>/dev/null
echo ""

echo "=== Post-Deploy Check Complete ==="
