#!/usr/bin/env python3
"""Kiwi Maths Level/Topic reorg. DRY_RUN prints distribution; no writes unless --write."""
import json, glob, re, os, sys, hashlib
from collections import Counter, defaultdict

_dir = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_dir, "../content-live"))
WRITE = '--write' in sys.argv

def is_q(o): return isinstance(o,dict) and 'id' in o and ('stem' in o or 'choices' in o or 'hint' in o)
def qs_in(d):
    out=[]
    def w(o):
        if is_q(o): out.append(o)
        elif isinstance(o,dict): [w(v) for v in o.values()]
        elif isinstance(o,list): [w(v) for v in o]
    w(d); return out

# ---- Topic registry (L1-L8). key, pillar, display ----
TOPICS = {
 'L1':[('number_sense','NT','Numbers All Around'),('odd_even_skip','NT','Number Hops'),
       ('number_shape_patterns','ALG','Pattern Play'),('missing_number','ALG','Mystery Numbers'),
       ('shapes_2d_3d','GEO','Shape Spotters'),('spatial','GEO','Picture Puzzles'),
       ('sorting','COM','Sort It Out'),('counting_logic','COM','Think & Count')],
 'L2':[('place_value','NT','Big Numbers'),('factors_multiples','NT','Number Families'),
       ('unit_digit_patterns','NT','Last-Digit Detective'),('patterns_rules','ALG','Rule Finders'),
       ('equations_disguise','ALG','Balance the Scale'),('fractions_intro','ALG','Fair Shares'),
       ('perimeter_area','GEO','Measure Masters'),('angles_symmetry_grids','GEO','Turn & Flip'),
       ('systematic_listing','COM','List It All'),('logic_puzzles','COM','Brain Benders')],
 'L3':[('divisibility_primes','NT','Prime Hunters'),('hcf_lcm','NT','Common Ground'),
       ('remainders_cycles','NT','Clock Arithmetic'),('fractions_decimals_pct','ALG','Parts & Wholes'),
       ('ratio_proportion','ALG','In Proportion'),('variables_equations','ALG','Letter Maths'),
       ('sequences_series','ALG','What Comes Next'),('angles_triangles','GEO','Angle Chasers'),
       ('area_perimeter_volume','GEO','Space & Surface'),('coordinates','GEO','Map Makers'),
       ('counting_principles','COM','Smart Counting'),('pigeonhole','COM','Sock Drawer Logic'),
       ('games_invariants','COM','Winning Moves')],
 'L4':[('modular_intro','NT','Remainder World'),('primes_powers','NT','Power Numbers'),('number_bases','NT','Beyond Base 10'),
       ('diophantine_intro','NT','Whole-Number Equations'),('linear_systems','ALG','Equation Solvers'),
       ('polynomials_identities','ALG','Algebra Toolkit'),('inequalities_intro','ALG','Compare & Bound'),
       ('exponents_roots','ALG','Power Up'),('congruence_similarity','GEO','Twin Triangles'),
       ('pythagoras','GEO','Right-Angle Power'),('circles_basic','GEO','Round About'),
       ('quadrilaterals_area','GEO','Shape Strategies'),('permutations_combinations','COM','Arrange & Choose'),
       ('probability_intro','COM','Chance It'),('pigeonhole_colouring','COM','Clever Arguments'),
       ('recursion_patterns','COM','Step by Step')],
 'L5':[('modular_flt','NT','Modular & FLT'),('gcd_euclid','NT','GCD & Euclid'),('diophantine','NT','Diophantine'),
       ('digits_bases','NT','Digits & Bases'),('polynomials_vieta','ALG','Polynomials & Vieta'),
       ('quadratics','ALG','Quadratics'),('inequalities_amgm','ALG','Inequalities (AM-GM)'),
       ('sequences_floor','ALG','Sequences & Floor'),('functional_thinking','ALG','Functional Thinking'),
       ('triangle_geometry','GEO','Triangle Geometry'),('circle_geometry','GEO','Circle Geometry'),
       ('trig_geometry','GEO','Trig for Geometry'),('similarity_chasing','GEO','Similarity & Chasing'),
       ('advanced_counting','COM','Advanced Counting'),('recurrences','COM','Recurrences'),
       ('pigeonhole_extremal','COM','Pigeonhole & Extremal'),('combinatorial_games','COM','Combinatorial Games')],
 'L6':[('congruences_crt','NT','Congruences & CRT'),('orders_qr','NT','Orders & QR'),('diophantine_tech','NT','Diophantine Techniques'),
       ('padic','NT','p-adic Valuation'),('inequality_toolbox','ALG','Inequality Toolbox'),('polynomial_theory','ALG','Polynomial Theory'),
       ('functional_equations','ALG','Functional Equations'),('recurrence_proofs','ALG','Recurrence Proofs'),
       ('triangle_circle_configs','GEO','Triangle & Circle Configs'),('transformations_intro','GEO','Transformations'),
       ('geometric_inequalities','GEO','Geometric Inequalities'),('trig_length','GEO','Trig & Length'),
       ('double_counting','COM','Double Counting'),('extremal','COM','Extremal Arguments'),
       ('graph_theory_intro','COM','Graph Theory'),('invariants','COM','Invariants & Monovariants')],
 'L7':[('orders_primitive_qr','NT','Orders, Primitive Roots & QR'),('lte','NT','Lifting the Exponent'),
       ('advanced_diophantine','NT','Advanced Diophantine'),('nt_constructions','NT','NT Constructions'),
       ('functional_equations_rig','ALG','Functional Equations (Rigorous)'),('polynomials_adv','ALG','Polynomials (Advanced)'),
       ('advanced_inequalities','ALG','Advanced Inequalities'),('algebra_nt_crossover','ALG','Algebra-NT Crossover'),
       ('inversion','GEO','Inversion'),('projective','GEO','Projective Flavour'),('spiral_similarity','GEO','Spiral Similarity'),
       ('combinatorial_geometry','GEO','Combinatorial Geometry'),('graph_theory','COM','Graph Theory'),
       ('extremal_combinatorics','COM','Extremal Combinatorics'),('games_processes','COM','Games & Processes'),
       ('algebraic_counting','COM','Algebraic Methods in Counting')],
 'L8':[('full_nt','NT','Full NT Arsenal'),('nt_constructions_open','NT','NT Constructions & Open-Style'),
       ('fe_mastery','ALG','FE Mastery'),('polynomial_mastery','ALG','Polynomial Mastery'),
       ('inequality_mastery','ALG','Inequality Mastery'),('algebraic_combinatorics','ALG','Algebraic Combinatorics'),
       ('configurational_geometry','GEO','Configurational Geometry'),('transformation_toolkit','GEO','Transformation Toolkit'),
       ('computational_backup','GEO','Computational Backup'),('extremal_probabilistic','COM','Extremal & Probabilistic'),
       ('deep_invariants','COM','Deep Invariants & Processes'),('combinatorial_nt','COM','Combinatorial NT')],
}
TOPIC_KEYS = {L:{k for k,_,_ in v} for L,v in TOPICS.items()}
TOPIC_PILLAR = {(L,k):p for L,v in TOPICS.items() for k,p,_ in v}
TOPIC_DISPLAY = {(L,k):d for L,v in TOPICS.items() for k,p,d in v}

CURR_BOARDS = {'NCERT':'ncert','IGCSE':'igcse','ICSE':'icse','SING':'singapore','USCC':'us-common-core'}
OLY_PREFIX = {'T','GEN','PCT'}

def kw(q):
    parts=[str(q.get('stem','')), str(q.get('topic','')), str(q.get('topic_name','')),
           str(q.get('skill_id','')), str(q.get('skill_domain','')), ' '.join(map(str,q.get('tags',[]) or []))]
    return ' '.join(parts).lower()

def coarse(q, src_topic_folder):
    """coarse category from v2 folder or v4 topic/domain."""
    t = str(q.get('topic','')).lower()
    d = str(q.get('skill_domain','')).lower()
    if src_topic_folder:  # v2
        return src_topic_folder
    m = {'counting_observation':'counting','arithmetic_missing_numbers':'arithmetic','patterns_sequences':'patterns',
         'logic_ordering':'logic','spatial_reasoning_3d':'spatial','shapes_folding_symmetry':'shapes',
         'word_problems_stories':'word','number_puzzles_games':'puzzles'}
    for k,v in m.items():
        if k in t: return v
    if d in ('geometry',): return 'shapes'
    if d in ('measurement',): return 'measurement'
    if d in ('fractions',): return 'fractions'
    if d in ('ratio',): return 'ratio'
    if d in ('data',): return 'data'
    if d in ('algebra',): return 'algebra'
    if d in ('numbers',): return 'counting'
    if d in ('arithmetic',): return 'arithmetic'
    return 'arithmetic'

def classify(level, q, cf):
    s = kw(q)
    has = lambda *ws: any(w in s for w in ws)
    # ---------- L1 ----------
    if level=='L1':
        if cf in ('shapes',): return 'shapes_2d_3d'
        if cf in ('spatial',): return 'spatial'
        if cf in ('patterns',): return 'number_shape_patterns'
        if cf in ('logic',): return 'counting_logic'
        if cf in ('puzzles',):
            if has('odd one','odd-one','group','sort','classif','belong','match','same as'): return 'sorting'
            if has('magic square','missing','digit','sum to','add up','number sentence','? ='): return 'missing_number'
            return 'counting_logic'
        if cf in ('counting','numbers'):
            if has('odd','even','skip count','count by','in twos','in fives','in tens'): return 'odd_even_skip'
            if has('how many ways','arrange','count the','in the picture','altogether in'): return 'counting_logic'
            return 'number_sense'
        if cf in ('arithmetic',):
            if has('__','___','missing','blank','? +','+ ?','balance','box','square ='): return 'missing_number'
            return 'missing_number' if has('=','sum','add','subtract','+','-') else 'number_sense'
        if cf in ('word','measurement','fractions','data','ratio','algebra'):
            if has('shape','triangle','square','circle','side','corner'): return 'shapes_2d_3d'
            if has('pattern','next','sequence'): return 'number_shape_patterns'
            if has('odd','even','skip'): return 'odd_even_skip'
            return 'counting_logic' if has('how many','count','more','fewer','tall','order') else 'missing_number'
        return 'number_sense'
    # ---------- L2 ----------
    if level=='L2':
        if has('unit digit','last digit','ones digit','units digit'): return 'unit_digit_patterns'
        if has('factor','multiple','divisib','remainder','prime') and cf in ('arithmetic','counting','numbers','puzzles','word'): return 'factors_multiples'
        if cf=='fractions' or has('fraction','half','quarter','numerator'): return 'fractions_intro'
        if cf=='measurement' or has('perimeter','area of','fencing'): return 'perimeter_area'
        if cf=='shapes':
            return 'angles_symmetry_grids' if has('angle','symmetry','right angle','grid','flip','turn') else 'perimeter_area'
        if cf=='spatial': return 'angles_symmetry_grids'
        if cf=='patterns':
            return 'patterns_rules'
        if cf=='logic':
            return 'systematic_listing' if has('how many ways','list all','arrange','route','order them') else 'logic_puzzles'
        if cf=='puzzles':
            return 'systematic_listing' if has('list','ways','route','outfit','arrange','combinatio','how many different','choose') else 'logic_puzzles'
        if cf=='data': return 'systematic_listing'
        if cf=='ratio': return 'fractions_intro'
        if cf in ('counting','numbers'):
            if has('place value','digit','round','thousand','lakh','ten thousand','compare'): return 'place_value'
            return 'place_value'
        if cf=='arithmetic':
            if has('missing','=','equation','number sentence','balance','operation'): return 'equations_disguise'
            return 'place_value'
        if cf=='word':
            if has('perimeter','area','length','fencing'): return 'perimeter_area'
            if has('fraction'): return 'fractions_intro'
            if has('factor','multiple','divisib','remainder'): return 'factors_multiples'
            return 'equations_disguise'
        return 'place_value'
    # ---------- L3 ----------
    if level=='L3':
        if has('hcf','lcm','gcd','highest common','lowest common','least common'): return 'hcf_lcm'
        if has('prime','divisib','factoris','factoriz','composite'): return 'divisibility_primes'
        if has('remainder','unit digit of','last digit of','cycle','calendar','clock arithmetic','mod '): return 'remainders_cycles'
        if cf=='ratio' or has('ratio','proportion','unitary','scale'): return 'ratio_proportion'
        if has('percent','%','profit','loss','discount','interest'): return 'fractions_decimals_pct'
        if cf=='fractions' or has('fraction','decimal'): return 'fractions_decimals_pct'
        if cf=='algebra' or has('variable','equation','solve for','let x','value of x','age of'): return 'variables_equations'
        if cf=='patterns' or has('sequence','series','term','nth','arithmetic progression','sum of'): return 'sequences_series'
        if cf=='measurement' or has('volume','surface area','cuboid','cube','capacity'): return 'area_perimeter_volume'
        if cf=='shapes':
            return 'angles_triangles' if has('angle','triangle') else 'area_perimeter_volume'
        if cf=='spatial' or has('coordinate','plot','net of','view of','map','axis'): return 'coordinates'
        if cf=='logic':
            if has('pigeonhole','must be','at least','guarantee','sock'): return 'pigeonhole'
            if has('game','win','strategy','invariant','parity','move'): return 'games_invariants'
            return 'counting_principles'
        if cf=='puzzles':
            if has('game','win','strategy','invariant','move','parity'): return 'games_invariants'
            if has('pigeonhole','at least','guarantee'): return 'pigeonhole'
            return 'counting_principles'
        if cf=='data': return 'counting_principles'
        if cf in ('counting','numbers','arithmetic'):
            if has('prime','factor','divisib'): return 'divisibility_primes'
            if has('hcf','lcm'): return 'hcf_lcm'
            if has('remainder','cycle'): return 'remainders_cycles'
            return 'fractions_decimals_pct' if has('percent','fraction','decimal','ratio') else 'divisibility_primes'
        if cf=='word':
            if has('ratio','proportion'): return 'ratio_proportion'
            if has('percent','profit','loss'): return 'fractions_decimals_pct'
            if has('volume','area','perimeter'): return 'area_perimeter_volume'
            return 'variables_equations'
        return 'divisibility_primes'
    return None

# ---- gather olympiad questions ----
records=[]  # (level, pillar, topic, q, srcbank, srcfile)
src_hash={} # legacy_id -> integrity hash
def integ(q):
    keep={k:q.get(k) for k in ('stem','choices','correct_answer','correct_value','answer','hint','solution_steps','diagnostics','irt_a','irt_b','irt_c','irt_params','difficulty_tier','difficulty_score','visual_svg')}
    return hashlib.md5(json.dumps(keep,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

curr_records=[]
unclassified=Counter()

# v4 adaptive
for f in glob.glob(ROOT+'/content-v4/adaptive/grade*/*.json'):
    g=int(re.search(r'grade(\d)',f).group(1))
    level={1:'L1',2:'L1',3:'L2',4:'L2',5:'L3',6:'L3'}[g]
    for q in qs_in(json.load(open(f))):
        oid=str(q.get('original_id') or q.get('id'))
        pref=re.match(r'[A-Za-z]+',oid).group() if re.match(r'[A-Za-z]+',oid) else ''
        legacy=str(q.get('id'))
        src_hash[('v4',legacy)]=integ(q)
        if pref in CURR_BOARDS:
            curr_records.append((CURR_BOARDS[pref], g, q, 'v4'))
        else:  # olympiad
            cf=coarse(q,None)
            tk=classify(level,q,cf)
            if tk not in TOPIC_KEYS[level]: unclassified[(level,cf)]+=1; tk=TOPICS[level][0][0]
            records.append((level, TOPIC_PILLAR[(level,tk)], tk, q, 'v4', f))

# v2 olympiad topics
TF={'topic-1-counting':'counting','topic-2-arithmetic':'arithmetic','topic-3-patterns':'patterns',
    'topic-4-logic':'logic','topic-5-spatial':'spatial','topic-6-shapes':'shapes',
    'topic-7-word-problems':'word','topic-8-puzzles':'puzzles'}
for f in glob.glob(ROOT+'/content-v2/topic-*/*.json'):
    folder=f.split('/')[-2]; cf=TF.get(folder,'arithmetic'); b=os.path.basename(f)
    if 'g56' in b: level='L3'
    elif 'grade34' in b: level='L2'
    else: level='L1'
    for q in qs_in(json.load(open(f))):
        legacy=str(q.get('id')); src_hash[('v2',legacy)]=integ(q)
        tk=classify(level,q,cf)
        if tk not in TOPIC_KEYS[level]: unclassified[(level,cf)]+=1; tk=TOPICS[level][0][0]
        records.append((level, TOPIC_PILLAR[(level,tk)], tk, q, 'v2', f))

# wavebook (wavebook L3->our L2, L4->our L3)
for f in glob.glob(ROOT+'/content-v2/wavebook/*.json'):
    b=os.path.basename(f).lower()
    level='L3' if ('l4' in b or '_l4' in b) else 'L2'
    for q in qs_in(json.load(open(f))):
        legacy=str(q.get('id')); src_hash[('wb',legacy)]=integ(q)
        cf=coarse(q,None)
        tk=classify(level,q,cf)
        if tk not in TOPIC_KEYS[level]: unclassified[(level,cf)]+=1; tk=TOPICS[level][0][0]
        records.append((level, TOPIC_PILLAR[(level,tk)], tk, q, 'wb', f))

# v2 curriculum remnant
for f in glob.glob(ROOT+'/content-v2/*-curriculum/**/*.json', recursive=True):
    board=f.split('/')[-3].replace('-curriculum','') if '-curriculum' in f else 'other'
    board={'igcse':'igcse','ncert':'ncert','icse':'icse','singapore':'singapore'}.get(board,board)
    gm=re.search(r'grade(\d)',f); g=int(gm.group(1)) if gm else 0
    for q in qs_in(json.load(open(f))):
        src_hash[('v2c',str(q.get('id')))]=integ(q)
        curr_records.append((board,g,q,'v2c'))

# ---- report ----
print('OLYMPIAD total:', len(records), '| CURRICULUM total:', len(curr_records))
by_level=Counter(r[0] for r in records)
bylt=Counter((r[0],r[2]) for r in records)

LEVEL_NAME={'L1':'Grade 1/2','L2':'Grade 3/4','L3':'Grade 5/6','L4':'Grade 7/8','L5':'Grade 9/10 (IOQM)','L6':'Olympiad (RMO)','L7':'Olympiad (INMO)','L8':'Olympiad (IMO)'}

# ---- assign new KM ids per (level,pillar), ordered by topic then difficulty ----
recs_by_lp=defaultdict(list)
for r in records: recs_by_lp[(r[0],r[1])].append(r)
def irtb(q):
    v=q.get('irt_b')
    if v is None: v=(q.get('irt_params') or {}).get('b')
    try: return float(v)
    except: return 0.0
newid_of={}
for (L,P),rs in recs_by_lp.items():
    rs.sort(key=lambda r:(r[2], irtb(r[3]), str(r[3].get('id'))))
    for i,r in enumerate(rs,1):
        newid_of[str(r[3].get('id'))]=f'KM-{L}-{P}-{i:04d}'

STRIP=['curriculum_map','curriculum_source','curriculum_tags','dual_tagged','chapter',
       'adaptive_topic_id','adaptive_topic_name','adaptive_topic_emoji','adaptive_grade','sequence_id','topic','topic_name']
def build_oly(L,P,tk,q,bank):
    o=dict(q); legacy=str(q.get('id')); orig=q.get('original_id')
    for k in STRIP: o.pop(k,None)
    o['id']=newid_of[legacy]; o['legacy_id']=legacy
    if orig: o['legacy_original_id']=orig
    o['km_level']=L; o['km_pillar']=P; o['km_topic']=tk
    o['km_topic_display']=TOPIC_DISPLAY[(L,tk)]; o['km_source_bank']=bank
    return o

if WRITE:
    OUT_OLY=ROOT+'/olympiad'; OUT_CUR=ROOT+'/curriculum'
    grp=defaultdict(list)
    for (L,P,tk,q,bank,f) in records: grp[(L,tk)].append((P,q,bank))
    written_oly=0
    for L in ['L1','L2','L3','L4','L5','L6','L7','L8']:
        os.makedirs(f'{OUT_OLY}/{L}',exist_ok=True)
        for tk,P,disp in TOPICS[L]:
            qs=[build_oly(L,P,tk,q,bank) for (PP,q,bank) in grp.get((L,tk),[])]
            qs.sort(key=lambda x:x['id'])
            obj={'level':L,'level_name':LEVEL_NAME[L],'pillar':P,'topic_key':tk,
                 'display_name':disp,'total_questions':len(qs),'questions':qs}
            json.dump(obj,open(f'{OUT_OLY}/{L}/{L}_{P}_{tk}.json','w'),ensure_ascii=False)
            written_oly+=len(qs)
    tmap={'note':'Kiwi Maths Level/Topic taxonomy. Pillars (NT/ALG/GEO/COM) are internal only.','levels':[]}
    for L in ['L1','L2','L3','L4','L5','L6','L7','L8']:
        tmap['levels'].append({'level':L,'level_name':LEVEL_NAME[L],
          'topics':[{'topic_key':k,'pillar':p,'display_name':d,'count':bylt.get((L,k),0)} for k,p,d in TOPICS[L]]})
    json.dump(tmap,open(f'{OUT_OLY}/topic_map.json','w'),ensure_ascii=False,indent=1)
    json.dump(newid_of,open(f'{OUT_OLY}/id_map.json','w'),ensure_ascii=False)

    # curriculum
    cgrp=defaultdict(list)
    for (board,g,q,srcc) in curr_records: cgrp[(board,g)].append(q)
    written_cur=0
    for (board,g),items in cgrp.items():
        d=f'{OUT_CUR}/{board}/grade{g}'; os.makedirs(d,exist_ok=True)
        qs=[]
        for q in items:
            o=dict(q); o['legacy_id']=str(q.get('id')); o['km_board']=board; o['km_grade']=g; qs.append(o)
        json.dump({'board':board,'grade':g,'total_questions':len(qs),'questions':qs},open(d+'/questions.json','w'),ensure_ascii=False)
        written_cur+=len(qs)
    import shutil
    for chp in glob.glob(ROOT+'/content-v4/school/*/grade*/chapters.json'):
        board=chp.split('/')[-3]; g=re.search(r'grade(\d)',chp).group(1)
        dst=f'{OUT_CUR}/{board}/grade{g}'; os.makedirs(dst,exist_ok=True)
        shutil.copy(chp,dst+'/chapters.json')

    # ---- INTEGRITY VERIFY ----
    bad=[]; seen=set()
    for L in ['L1','L2','L3']:
        for fp in glob.glob(f'{OUT_OLY}/{L}/*.json'):
            for q in json.load(open(fp))['questions']:
                lid=q['legacy_id']; seen.add(lid); h=integ(q)
                if not any(src_hash.get((b,lid))==h for b in ('v4','v2','wb')): bad.append(lid)
    cbad=[]; cseen=set()
    for fp in glob.glob(f'{OUT_CUR}/*/grade*/questions.json'):
        for q in json.load(open(fp))['questions']:
            lid=q['legacy_id']; cseen.add(lid); h=integ(q)
            if not any(src_hash.get((b,lid))==h for b in ('v4','v2c')): cbad.append(lid)
    print()
    print('=== WRITE COMPLETE ===')
    print(f'olympiad written={written_oly} (expect {len(records)}); unique legacy={len(seen)}')
    print(f'curriculum written={written_cur} (expect {len(curr_records)}); unique legacy={len(cseen)}')
    print(f'INTEGRITY olympiad mismatches={len(bad)}  curriculum mismatches={len(cbad)}')
    print(f'new KM ids unique={len(set(newid_of.values()))} of {len(newid_of)}')

    # ---- counts report (json + md) ----
    rep={'generated':'level-reorg','olympiad_total':len(records),'curriculum_total':len(curr_records),'levels':{}}
    for L in ['L1','L2','L3','L4','L5','L6','L7','L8']:
        rep['levels'][L]={'level_name':LEVEL_NAME[L],'total':by_level.get(L,0),
            'topics':[{'pillar':p,'display':d,'topic_key':k,'count':bylt.get((L,k),0)} for k,p,d in TOPICS[L]]}
    rep['curriculum']={f'{b}_G{g}':n for (b,g),n in sorted(Counter((b,g) for b,g,_,_ in curr_records).items())}
    json.dump(rep,open(ROOT+'/olympiad/counts_report.json','w'),ensure_ascii=False,indent=1)
    print('counts_report.json written')
