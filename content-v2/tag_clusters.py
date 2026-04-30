"""
Tag all questions with a concept_cluster field for adaptive deduplication.

Each question gets a cluster like "compare/which-tallest" that groups
functionally identical questions (same skill, same question pattern,
just different names/numbers). The adaptive engine uses this to skip
repetitive questions once a child demonstrates mastery of the pattern.
"""
import json, re, glob, os

def extract_concept_cluster(stem, tags, difficulty_score):
    s = stem.lower().strip()
    tag_str = ' '.join(tags) if tags else ''
    tier = 'easy' if difficulty_score <= 30 else ('medium' if difficulty_score <= 120 else 'hard')
    
    # --- Height/size comparison ---
    if re.search(r'who is the tallest', s): return 'compare/who-tallest'
    if re.search(r'who is the shortest', s): return 'compare/who-shortest'
    if re.search(r'which is the tallest', s): return 'compare/which-tallest'
    if re.search(r'which is the shortest', s): return 'compare/which-shortest'
    if re.search(r'which is the (biggest|largest)', s): return 'compare/which-biggest'
    if re.search(r'which is the smallest', s): return 'compare/which-smallest'
    m = re.search(r'which is the (longest|heaviest|lightest)', s)
    if m: return f'compare/which-{m.group(1)}'
    if re.search(r'arrange .* (tallest|shortest|smallest|biggest|order)', s): return 'compare/arrange-order'
    if re.search(r'(lighter|heavier) than', s): return 'compare/weight-transitive'
    if re.search(r'(taller|shorter) than', s): return 'compare/height-transitive'
    if re.search(r'(bigger|smaller) than', s): return 'compare/size-transitive'
    
    # --- Race/position ---
    if re.search(r'in a race.*who came first', s): return 'position/race-first'
    if re.search(r'in a race.*who came second', s): return 'position/race-second'
    if re.search(r'in a race.*who came third', s): return 'position/race-third'
    if re.search(r'in a race.*who came (fourth|fifth|last)', s): return 'position/race-last'
    m = re.search(r'who (?:is|was|came) (first|second|third|last|next)', s)
    if m: return f'position/who-{m.group(1)}'
    
    # --- Counting ---
    if re.search(r'how many .* (?:are there|can you (?:see|count|find))', s): return f'counting/how-many-{tier}'
    if re.search(r'count the', s): return f'counting/count-{tier}'
    if re.search(r'how many (sides|corners)', s): return 'counting/sides-corners'
    if re.search(r'how many (edges|faces|vertices)', s): return 'counting/3d-props'
    if re.search(r'how many (triangles|squares|circles|rectangles)', s): return 'shape/count-shapes'
    
    # --- Sequence ---
    if re.search(r'what comes (?:next|after)\b', s): return f'sequence/next-{tier}'
    if re.search(r'what comes before', s): return f'sequence/before-{tier}'
    if re.search(r'missing number', s): return f'sequence/missing-{tier}'
    
    # --- Arithmetic (cluster by operation + tier, not every single sum) ---
    if re.search(r'\d+\s*\+\s*\d+\s*=', s): return f'arithmetic/addition-{tier}'
    if re.search(r'\d+\s*[-–−]\s*\d+\s*=', s): return f'arithmetic/subtraction-{tier}'
    if re.search(r'\d+\s*[x×\*]\s*\d+', s): return f'arithmetic/multiplication-{tier}'
    if re.search(r'\d+\s*[÷/]\s*\d+', s): return f'arithmetic/division-{tier}'
    
    # --- Pattern ---
    if re.search(r'(?:what comes next|next in|continue the)', s): return f'pattern/continue-{tier}'
    if re.search(r'(?:odd one out|which.*different|which.*not belong)', s): return f'pattern/odd-one-out-{tier}'
    if re.search(r'pattern', s): return f'pattern/identify-{tier}'
    
    # --- Shape ---
    if re.search(r'(?:name|identify|what) (?:the|this) shape', s): return 'shape/identify'
    if re.search(r'(?:symmetr|line of symmetry|mirror)', s): return f'shape/symmetry-{tier}'
    if re.search(r'(?:fold|unfold|net)', s): return 'shape/nets'
    
    # --- Word problems (split by operation type) ---
    if re.search(r'how many .* (?:left|remain)', s): return f'word-problem/subtraction-{tier}'
    if re.search(r'how many .* (?:altogether|total|in all)', s): return f'word-problem/addition-{tier}'
    if re.search(r'how many .* more', s): return f'word-problem/comparison-{tier}'
    if re.search(r'how many .* (?:less|fewer)', s): return f'word-problem/less-{tier}'
    
    # Tag-based fallback
    if 'height-comparison' in tag_str: return 'compare/height-general'
    if 'comparison' in tag_str: return 'compare/general'
    if 'ordering' in tag_str: return 'ordering/general'
    if 'position' in tag_str: return 'position/general'
    if 'counting' in tag_str: return f'counting/general-{tier}'
    
    return None

# Process all question files
total = 0
tagged = 0
for jf in sorted(glob.glob("topic-*/questions.json") + glob.glob("topic-*/grade34_questions.json")):
    data = json.load(open(jf))
    if not isinstance(data, dict) or 'questions' not in data:
        continue
    modified = False
    for q in data['questions']:
        total += 1
        cluster = extract_concept_cluster(q['stem'], q.get('tags', []), q['difficulty_score'])
        if cluster:
            q['concept_cluster'] = cluster
            tagged += 1
            modified = True
        elif 'concept_cluster' not in q:
            q['concept_cluster'] = None
    
    if modified:
        with open(jf, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Tagged: {jf}")

print(f"\nTotal: {total}, Tagged: {tagged} ({tagged/total*100:.1f}%)")
