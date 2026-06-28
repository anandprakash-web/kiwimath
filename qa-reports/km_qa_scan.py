import json, glob, re
from collections import defaultdict, Counter
import os
_dir = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_dir, "../content-live"))
# topic->pillar registry to validate tags
PILLAR_OF={}
tm=json.load(open(ROOT+'/olympiad/topic_map.json'))
for lv in tm['levels']:
    for t in lv['topics']: PILLAR_OF[(lv['level'],t['topic_key'])]=t['pillar']

def norm(s): return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]',' ',str(s).lower())).strip()
qs=[]
for f in glob.glob(ROOT+'/olympiad/L*/*.json'):
    d=json.load(open(f))
    if not isinstance(d, dict) or 'questions' not in d:
        continue
    for q in d.get('questions',[]):
        q['_file']=f; q['_topic']=d['display_name']; q['_tkey']=d['topic_key']; q['_level']=d['level']
        qs.append(q)
N=len(qs)
issues=defaultdict(list)
def add(cat,q,note=''): issues[cat].append((q.get('id'),q.get('_topic'),note,(q.get('stem') or '')[:90]))

# ---- duplicates ----
byfull=defaultdict(list)
for q in qs: byfull[(norm(q.get('stem','')),tuple(map(str,q.get('choices',[]) or [])),str(q.get('correct_answer')))].append(q)
dup_exact=sum(len(v)-1 for k,v in byfull.items() if len(v)>1 and k[0])

for q in qs:
    stem=q.get('stem') or ''; ns=norm(stem)
    choices=q.get('choices') or []
    mode=q.get('interaction_mode','mcq'); ca=q.get('correct_answer'); cv=q.get('correct_value')
    hint=q.get('hint'); 
    # ---- answers ----
    if choices:
        if isinstance(ca,int):
            if ca<0 or ca>=len(choices): add('ans_index_out_of_range',q,f'idx={ca} len={len(choices)}')
        # duplicate correct value among distractors
        if isinstance(ca,int) and 0<=ca<len(choices):
            cval=str(choices[ca])
            if [str(c) for c in choices].count(cval)>1: add('ans_dup_correct_in_choices',q,f'val={cval}')
        # duplicate choices generally
        sc=[str(c) for c in choices]
        if len(sc)!=len(set(sc)): add('choices_have_duplicates',q)
    else:
        if mode in ('mcq','multiple_choice') or (mode is None): add('mcq_no_choices',q,f'mode={mode}')
        if cv is None and mode in ('integer','fill_up'): add('integer_no_value',q)
    # ---- stem issues ----
    if len(ns)<6: add('stem_empty_or_tiny',q)
    if re.search(r'(older|younger|taller|shorter|bigger|faster) than\s*\.', stem) or ' than . ' in stem or re.search(r'\bis\s+older than\s*\.', stem):
        add('stem_truncated_name',q)
    if re.search(r'\.\s*\.', stem) or '  ' in stem or re.search(r'\b(Help calculate|Needs to work out|works on the numbers|runs the numbers|does the math|calculates the figures)\b', stem):
        add('stem_filler_or_debris',q)
    if re.search(r'than\s+\.', stem) or re.search(r'\bthan\s*$', stem.strip()): add('stem_dangling',q)
    # ---- images ----
    svg=q.get('visual_svg'); vreq=q.get('visual_requirement'); vctx=str(q.get('visual_context') or '')
    refs_pic=bool(re.search(r'\b(picture|figure|shown below|diagram|image|the graph|in the chart|given below|following figure)\b', stem.lower()))
    if vreq in ('required','essential') and not svg: add('img_missing_required',q,f'req={vreq}')
    if refs_pic and not svg: add('img_referenced_but_absent',q)
    if 'visual representation of the prob' in vctx: add('img_placeholder_caption',q)
    # chart-type mismatch between stem and visual_context
    for a,b in [('bar graph','pictograph'),('pictograph','bar graph'),('bar chart','pie'),('pie chart','bar')]:
        if a in stem.lower() and b in vctx.lower(): add('img_type_mismatch',q,f'{a} vs {b}')
    # ---- hints ----
    if not hint or (isinstance(hint,dict) and not any((hint.get(k) or '').strip() for k in hint)) or (isinstance(hint,str) and not hint.strip()):
        add('hint_missing',q)
    else:
        ht = ' '.join(str(v) for v in hint.values()) if isinstance(hint,dict) else str(hint)
        # leak: hint reveals the correct value
        if isinstance(ca,int) and 0<=ca<len(choices):
            cval=str(choices[ca]).strip()
            if cval and re.search(r'\b'+re.escape(cval)+r'\b', ht) and len(cval)>1: add('hint_leaks_answer',q,f'val={cval}')
        if re.search(r'answer is\s*[0-9]', ht.lower()) or 'the answer is' in ht.lower(): add('hint_says_answer',q)
        # lists all choices
        if choices and all(str(c) in ht for c in choices) and len(choices)>=3: add('hint_lists_choices',q)
    # ---- tags ----
    exp_pillar=PILLAR_OF.get((q.get('_level'),q.get('_tkey')))
    if q.get('km_pillar')!=exp_pillar: add('tag_pillar_mismatch',q,f'{q.get("km_pillar")} vs {exp_pillar}')
    if q.get('km_level')!=q.get('_level'): add('tag_level_mismatch',q)
    for lk in ('chapter','curriculum_map','curriculum_source','curriculum_tags','dual_tagged'):
        if q.get(lk): add('tag_leftover_curriculum',q,lk); break

print('OLYMPIAD QA SCAN —', N, 'questions')
print('exact duplicate redundant copies:', dup_exact)
print()
order=['ans_index_out_of_range','ans_dup_correct_in_choices','choices_have_duplicates','mcq_no_choices','integer_no_value',
 'stem_empty_or_tiny','stem_truncated_name','stem_dangling','stem_filler_or_debris',
 'img_missing_required','img_referenced_but_absent','img_placeholder_caption','img_type_mismatch',
 'hint_missing','hint_leaks_answer','hint_says_answer','hint_lists_choices',
 'tag_pillar_mismatch','tag_level_mismatch','tag_leftover_curriculum']
for c in order:
    print('%-28s %6d'%(c,len(issues.get(c,[]))))
print()
print('=== examples ===')
for c in order:
    if issues.get(c):
        e=issues[c][0]; print('%-26s e.g. %s | %s | %s'%(c, e[0], e[2], e[3]))
json.dump({k:v for k,v in issues.items()}, open(os.path.abspath(os.path.join(_dir, '../outputs/km_qa_issues.json')),'w'))
