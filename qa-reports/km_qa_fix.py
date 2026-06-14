import json, glob, re, hashlib
from collections import Counter, defaultdict
ROOT='/sessions/compassionate-zealous-pasteur/mnt/kiwimath/content-live'

CONN=r'(wants to solve|is working on a problem|needs to work out|is helping[^.:!?]{0,30}|needs to figure out|does the math|solves the problem|calculates the figures|tackles the problem|works on the numbers|runs the numbers|runs the calculation|crunches the numbers|figures this out|works out the answer|is curious|wants to know)'
STRIP=re.compile(r'^\s*[A-Z][^.:!?]{0,80}?\b'+CONN+r'\b[^.:!?]{0,40}?[.:]\s+', re.I)
def strip_filler(s):
    if not s: return s, False
    m=STRIP.match(s)
    if not m: return s, False
    rest=s[m.end():].strip()
    if len(rest)<5: return s, False
    rest=rest[0].upper()+rest[1:]
    return rest, True

REVEAL=lambda cval: re.compile(r'(=|\bis\b|equals|gives|gets?|makes|answer\s*:?|→|\bso\b)(\s*)'+re.escape(cval)+r'\b', re.I)
def mask_leak(h, cval):
    if not cval or len(cval)<2: return h, False
    nh=REVEAL(cval).sub(lambda m:m.group(1)+m.group(2)+'?', h)
    return nh, (nh!=h)

# topic-aware 3-level nudges (never reveal the number)
NUDGE={
 'number_sense':("Look at each number carefully.","Line them up by place value to compare or count.","Which is larger/smaller, or how many in total?"),
 'odd_even_skip':("Think about counting in steps.","Skip-count by 2s, 5s, or 10s, or check odd vs even.","Continue the count carefully to the value asked."),
 'number_shape_patterns':("Look at how the pattern changes each step.","Find the rule (what is added, repeated, or grows).","Apply that rule to find the next term."),
 'missing_number':("Read what is known and what is missing.","Write it as a number sentence with a box for the unknown.","Work backwards to find the missing value."),
 'shapes_2d_3d':("Picture the shape and its parts.","Count sides, corners, or faces carefully.","Match what you counted to the question."),
 'spatial':("Picture the position or movement.","Track left/right, turns, or folds step by step.","Where does it end up?"),
 'sorting':("Look at the attribute that groups them.","Sort by that property; find the odd one out.","Which item does not belong?"),
 'counting_logic':("Read the clues carefully.","Order or count the items without missing any.","Use the clues to decide the answer."),
 'place_value':("Look at each digit's place.","Compare or round using the highest place value first.","Read off the value the question asks for."),
 'factors_multiples':("Think about what divides the number evenly.","List its factors or multiples; test 2, 5, 10.","Use that to answer the question."),
 'unit_digit_patterns':("Focus on the last (units) digit.","Look for the repeating cycle of unit digits.","Use the cycle to find the required digit."),
 'patterns_rules':("Find what turns one term into the next.","State the rule (input → output).","Apply the rule to the value asked."),
 'equations_disguise':("Turn the words into a number sentence.","Identify the operation and the unknown.","Solve step by step."),
 'fractions_intro':("Think of the whole split into equal parts.","Compare the parts (same-size pieces).","Which fraction is asked for?"),
 'perimeter_area':("Recall the rule for this shape.","Perimeter adds the sides; area multiplies length × width.","Substitute the measurements."),
 'angles_symmetry_grids':("Recall the angle or symmetry property.","A right angle is 90°; count lines of symmetry carefully.","Apply it to this shape."),
 'systematic_listing':("List the possibilities in order.","Be organised so none are missed or repeated.","Count the list."),
 'logic_puzzles':("Read each clue carefully.","Eliminate what cannot be true.","What must be true?"),
 'divisibility_primes':("Test small primes (2, 3, 5, 7…).","Use divisibility rules; factorise the number.","Decide if it is prime or what divides it."),
 'hcf_lcm':("Factorise each number into primes.","HCF takes common factors; LCM takes all factors.","Combine them as the question needs."),
 'remainders_cycles':("Think about what is left after dividing.","Look for the repeating remainder/unit-digit cycle.","Use the cycle to answer."),
 'fractions_decimals_pct':("Keep the parts and the whole in the same form.","Convert between fraction/decimal/percent as needed.","Then compute what is asked."),
 'ratio_proportion':("Compare the quantities as a ratio.","Find one part (unitary method), then scale.","Answer for the amount asked."),
 'variables_equations':("Let the unknown be a letter.","Write an equation from the words.","Solve for the unknown step by step."),
 'sequences_series':("Find the rule linking the terms.","Is it adding a fixed amount, or a known pattern?","Use it to find the term or sum."),
 'angles_triangles':("Recall angle facts (angles in a triangle sum to 180°).","Set up the relationship between the angles.","Solve for the unknown angle."),
 'area_perimeter_volume':("Recall the formula for this shape/solid.","Substitute the given measurements.","Compute carefully with units."),
 'coordinates':("Read the coordinates as (across, up).","Plot or move point by point.","Find the position or distance asked."),
 'counting_principles':("Break the choice into stages.","Multiply choices per stage (or add cases).","Count without double-counting."),
 'pigeonhole':("Think: items shared among groups.","If there are more items than groups, some group must repeat.","How many guarantee the result?"),
 'games_invariants':("Look for something that stays the same (parity/invariant).","Test small cases to spot the pattern.","Use it to decide who wins or if it's possible."),
}
def gen_hint(tkey, pillar):
    t=NUDGE.get(tkey)
    if not t:
        t=("What exactly is being asked?","Break it into smaller steps using the numbers given.","Work through one step at a time.")
    return {"level_0":t[0],"level_1":t[1],"level_2":t[2]}

def ht(h): return ' '.join(str(v) for v in h.values()) if isinstance(h,dict) else (str(h) if h else '')
def integ(q):  # fields that MUST NOT change
    keep={k:q.get(k) for k in ('choices','correct_answer','correct_value','answer','irt_a','irt_b','irt_c','irt_params','difficulty_tier','difficulty_score')}
    return hashlib.md5(json.dumps(keep,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

REALPIC=re.compile(r'(in the picture|picture above|picture below|shown below|shown above|the figure shows|figure below|figure above|in the figure|see the figure|given figure|following figure|the diagram|diagram below|from the graph|in the graph|the bar chart|the pictograph|number line below|grid below|shaded)', re.I)

stats=Counter(); deleted=[]; pre_hash={}
files=glob.glob(ROOT+'/olympiad/L*/*.json')
# pass 1: collect for dup removal (global, keep first by id)
seen=set()
allq=[]
for f in files:
    d=json.load(open(f))
    for q in d.get('questions',[]):
        pre_hash[q['id']]=integ(q)
        allq.append((f,q))
# dup key
def dupkey(q):
    ns=re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]',' ',str(q.get('stem','')).lower())).strip()
    return (ns, tuple(map(str,q.get('choices',[]) or [])), str(q.get('correct_answer')))
keep_first={}
for f,q in sorted(allq, key=lambda x:x[1]['id']):
    k=dupkey(q)
    if k[0] and k in keep_first: deleted.append(q['id']); stats['removed_duplicate']+=1
    else: keep_first[k]=q['id']
del_ids=set(deleted)

# pass 2: edit + write
for f in files:
    d=json.load(open(f)); out=[]
    changed=False
    for q in d.get('questions',[]):
        if q['id'] in del_ids: changed=True; continue
        # stem filler
        ns,did=strip_filler(q.get('stem',''))
        if did: q['stem']=ns; stats['stem_filler_stripped']+=1; changed=True
        # hint: missing -> generate
        if not ht(q.get('hint')).strip():
            q['hint']=gen_hint(q.get('km_topic'), q.get('km_pillar')); stats['hint_generated']+=1; changed=True
        else:
            ch=q.get('choices') or []; ca=q.get('correct_answer')
            if isinstance(ca,int) and 0<=ca<len(ch):
                cval=str(ch[ca]).strip()
                if isinstance(q.get('hint'),dict):
                    hh=q['hint']; any_mask=False
                    for kk in list(hh):
                        nv,m=mask_leak(str(hh[kk]),cval)
                        if m: hh[kk]=nv; any_mask=True
                    if any_mask: stats['hint_leak_masked']+=1; changed=True
                else:
                    nv,m=mask_leak(str(q['hint']),cval)
                    if m: q['hint']=nv; stats['hint_leak_masked']+=1; changed=True
        # visual_requirement downgrade
        if q.get('visual_requirement') in ('required','essential') and not q.get('visual_svg') and not REALPIC.search(q.get('stem','')):
            q['visual_requirement']='optional'; stats['visual_downgraded']+=1; changed=True
        # clear placeholder visual_context
        if 'visual representation of the prob' in str(q.get('visual_context') or ''):
            q['visual_context']=None; stats['placeholder_context_cleared']+=1; changed=True
        out.append(q)
    if changed:
        d['questions']=out; d['total_questions']=len(out)
        json.dump(d, open(f,'w'), ensure_ascii=False)

# verify integrity (answers/choices/difficulty unchanged for survivors)
mismatch=0; survivors=0
for f in files:
    for q in json.load(open(f)).get('questions',[]):
        survivors+=1
        if pre_hash.get(q['id'])!=integ(q): mismatch+=1
json.dump({'stats':dict(stats),'deleted':deleted}, open('/sessions/compassionate-zealous-pasteur/mnt/outputs/km_qa_fix_report.json','w'))
print('=== FIXES APPLIED ===')
for k,v in stats.most_common(): print('  %-26s %6d'%(k,v))
print()
print('survivors:',survivors,'| removed:',len(deleted))
print('INTEGRITY (choices/answer/difficulty/IRT unchanged): mismatches =', mismatch)
