#!/usr/bin/env python3
"""
Kiwimath Content v4 Reorganizer
================================
Loads all 22,467 questions from content-v3, maps them to grade-specific
adaptive topics using topic_map.json, dual-tags curriculum questions,
IRT-sequences within each topic, and writes content-v4 output.

Olympiad levels 1-4 map to grades 1-4.
For grades 5-6, olympiad questions with matching skills are cloned with
adjusted difficulty (questions whose skill_id exists in the grade 5/6 topic map).
Curriculum questions have explicit grade from their folder/level field.
"""

import json
import os
import glob
import copy
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3 = os.path.join(BASE, 'content-v3')
V4 = os.path.join(BASE, 'content-v4')

def load_topic_map():
    with open(os.path.join(V4, 'topic_map.json')) as f:
        return json.load(f)

def build_skill_to_topic(topic_map):
    """For each grade, build skill_id -> topic mapping."""
    mapping = {}
    for grade_str, grade_info in topic_map['grades'].items():
        grade = int(grade_str)
        skill_map = {}
        for topic in grade_info['topics']:
            for skill in topic['skills']:
                skill_map[skill] = {
                    'topic_id': topic['id'],
                    'topic_name': topic['name'],
                    'topic_emoji': topic['emoji'],
                    'domain': topic['domain']
                }
        mapping[grade] = skill_map
    return mapping

def load_olympiad_questions():
    """Load all olympiad questions from topic-* folders."""
    questions = []
    for topic_dir in sorted(glob.glob(os.path.join(V3, 'topic-*'))):
        for jf in sorted(glob.glob(os.path.join(topic_dir, '*.json'))):
            with open(jf) as f:
                data = json.load(f)
            for q in data.get('questions', []):
                q['_source_type'] = 'olympiad'
                q['_source_file'] = os.path.relpath(jf, V3)
                questions.append(q)
    return questions

def load_curriculum_questions():
    """Load all curriculum questions."""
    questions = []
    curriculum_dirs = {
        'ncert-curriculum': 'ncert',
        'icse-curriculum': 'icse',
        'igcse-curriculum': 'igcse',
        'singapore-curriculum': 'singapore',
        'us-common-core': 'us-common-core'
    }
    for dirname, curr_key in curriculum_dirs.items():
        for jf in sorted(glob.glob(os.path.join(V3, dirname, 'grade*', '*.json'))):
            with open(jf) as f:
                data = json.load(f)
            for q in data.get('questions', []):
                q['_source_type'] = 'curriculum'
                q['_source_file'] = os.path.relpath(jf, V3)
                q['_curriculum_key'] = curr_key
                if 'chapter' not in q:
                    q['chapter'] = None
                questions.append(q)
    return questions

def determine_grades_for_olympiad(level):
    """Map olympiad level to the school grades it spans.

    The KiwiTier system maps:
      Level 1 (Explorer) -> Grade 1, Grade 2  (Junior tier)
      Level 2 (Builder)  -> Grade 2, Grade 3
      Level 3 (Thinker)  -> Grade 3, Grade 4
      Level 4 (Solver)   -> Grade 4, Grade 5
    This ensures each level's questions appear in both the starting
    grade and the next grade up, matching the product's tier system.
    """
    mapping = {
        1: [1, 2],
        2: [2, 3],
        3: [3, 4],
        4: [4, 5],
    }
    return mapping.get(level, [min(level, 6)])

def determine_grade(question):
    """Map a curriculum question to its school grade (1-6)."""
    if question.get('school_grade') and question['school_grade'] in range(1, 7):
        return question['school_grade']
    level = question.get('level', 1)
    # For curriculum questions, level == grade
    return min(level, 6)

def find_topic_for_question(question, grade, skill_to_topic):
    """Find the matching topic for a question in the given grade."""
    skill = question.get('skill_id')
    grade_map = skill_to_topic.get(grade, {})
    if skill in grade_map:
        return grade_map[skill]
    # Fallback: try to match by domain
    domain = question.get('skill_domain', '')
    for s, info in grade_map.items():
        if info['domain'] == domain:
            return info
    # Last resort: word problems / catch-all
    for topic_info in grade_map.values():
        if 'word' in topic_info['topic_name'].lower():
            return topic_info
    # Absolute fallback: first topic
    if grade_map:
        return next(iter(grade_map.values()))
    return None

def process_questions(olympiad_qs, curriculum_qs, skill_to_topic, topic_map):
    """Assign all questions to grade-topic buckets."""
    # Track used IDs globally to prevent duplicates from pre-existing data issues
    used_ids = set()
    # Buckets: (grade, topic_id) -> list of questions
    buckets = defaultdict(list)
    # School buckets: (curriculum_key, grade) -> list of questions
    school_buckets = defaultdict(list)

    stats = {
        'olympiad_mapped': 0,
        'olympiad_cloned_g56': 0,
        'curriculum_mapped': 0,
        'fallback_used': 0,
        'skill_mismatches': defaultdict(int)
    }

    # Process olympiad questions: each level spans 2 grades
    # Level 1 -> G1+G2, Level 2 -> G2+G3, Level 3 -> G3+G4, Level 4 -> G4+G5
    for q in olympiad_qs:
        level = q.get('level', 1)
        target_grades = determine_grades_for_olympiad(level)
        skill = q.get('skill_id')

        for grade in target_grades:
            topic_info = find_topic_for_question(q, grade, skill_to_topic)
            if topic_info:
                enriched = copy.deepcopy(q)
                # Use grade-suffixed ID for the second grade OR if ID already used
                candidate_id = q['id'] if grade == target_grades[0] else f"{q['id']}-G{grade}"
                if candidate_id in used_ids:
                    candidate_id = f"{q['id']}-G{grade}-L{level}"
                enriched['id'] = candidate_id
                used_ids.add(candidate_id)
                enriched['adaptive_topic_id'] = topic_info['topic_id']
                enriched['adaptive_topic_name'] = topic_info['topic_name']
                enriched['adaptive_topic_emoji'] = topic_info['topic_emoji']
                enriched['adaptive_grade'] = grade
                enriched['dual_tagged'] = False
                enriched['content_source'] = 'olympiad'
                # Slight difficulty adjustment for higher grade placement
                if grade != target_grades[0]:
                    irt_b = enriched.get('irt_b', enriched.get('irt_params', {}).get('b', 0))
                    enriched['irt_b'] = round(irt_b - 0.2, 3)  # easier relative to grade
                    if 'irt_params' in enriched:
                        enriched['irt_params'] = copy.deepcopy(enriched['irt_params'])
                        enriched['irt_params']['b'] = enriched['irt_b']
                buckets[(grade, topic_info['topic_id'])].append(enriched)
                stats['olympiad_mapped'] += 1
            else:
                stats['skill_mismatches'][q.get('skill_id', 'unknown')] += 1

    # Clone level 3-4 olympiad questions for grade 6 (not covered by level mapping)
    for q in olympiad_qs:
        level = q.get('level', 1)
        if level not in (3, 4):
            continue
        skill = q.get('skill_id')
        grade_map = skill_to_topic.get(6, {})
        if skill in grade_map:
            topic_info = grade_map[skill]
            enriched = copy.deepcopy(q)
            candidate_id = f"{q['id']}-G6"
            if candidate_id in used_ids:
                candidate_id = f"{q['id']}-G6-L{level}"
            enriched['id'] = candidate_id
            used_ids.add(candidate_id)
            enriched['adaptive_topic_id'] = topic_info['topic_id']
            enriched['adaptive_topic_name'] = topic_info['topic_name']
            enriched['adaptive_topic_emoji'] = topic_info['topic_emoji']
            enriched['adaptive_grade'] = 6
            enriched['level'] = 6
            enriched['dual_tagged'] = False
            enriched['content_source'] = 'olympiad_clone'
            irt_b = enriched.get('irt_b', enriched.get('irt_params', {}).get('b', 0))
            enriched['irt_b'] = round(irt_b + 0.3, 3)
            if 'irt_params' in enriched:
                enriched['irt_params'] = copy.deepcopy(enriched['irt_params'])
                enriched['irt_params']['b'] = enriched['irt_b']
            buckets[(6, topic_info['topic_id'])].append(enriched)
            stats['olympiad_cloned_g56'] += 1

    # Process curriculum questions
    for q in curriculum_qs:
        grade = determine_grade(q)
        topic_info = find_topic_for_question(q, grade, skill_to_topic)
        if topic_info:
            enriched = copy.deepcopy(q)
            enriched['adaptive_topic_id'] = topic_info['topic_id']
            enriched['adaptive_topic_name'] = topic_info['topic_name']
            enriched['adaptive_topic_emoji'] = topic_info['topic_emoji']
            enriched['adaptive_grade'] = grade
            enriched['dual_tagged'] = True  # Curriculum questions are dual-tagged
            enriched['content_source'] = q.get('_curriculum_key', 'curriculum')
            buckets[(grade, topic_info['topic_id'])].append(enriched)
            stats['curriculum_mapped'] += 1

            # Also add to school bucket
            curr_key = q.get('_curriculum_key', 'unknown')
            school_buckets[(curr_key, grade)].append(enriched)
        else:
            stats['fallback_used'] += 1
            stats['skill_mismatches'][q.get('skill_id', 'unknown')] += 1

    return buckets, school_buckets, stats

def irt_sequence(questions):
    """Sort questions by IRT difficulty (irt_b) ascending."""
    def get_irt_b(q):
        if 'irt_b' in q and q['irt_b'] is not None:
            return q['irt_b']
        if 'irt_params' in q and isinstance(q['irt_params'], dict):
            return q['irt_params'].get('b', 0)
        return 0

    questions.sort(key=get_irt_b)
    # Assign sequence IDs and difficulty tiers
    n = len(questions)
    for i, q in enumerate(questions):
        q['sequence_id'] = i + 1
        pct = i / max(n - 1, 1)
        if pct < 0.2:
            q['difficulty_tier_in_topic'] = 'intro'
        elif pct < 0.5:
            q['difficulty_tier_in_topic'] = 'practice'
        elif pct < 0.8:
            q['difficulty_tier_in_topic'] = 'challenge'
        else:
            q['difficulty_tier_in_topic'] = 'mastery'
    return questions

def clean_question(q):
    """Remove internal processing fields."""
    for key in ['_source_type', '_source_file', '_curriculum_key']:
        q.pop(key, None)
    return q

def write_adaptive_files(buckets, topic_map):
    """Write content-v4/adaptive/grade{N}/{topic-id}.json files."""
    total_written = 0
    for (grade, topic_id), questions in sorted(buckets.items()):
        # IRT sequence
        questions = irt_sequence(questions)

        # Clean internal fields
        questions = [clean_question(q) for q in questions]

        # Find topic metadata from topic_map
        grade_topics = topic_map['grades'].get(str(grade), {}).get('topics', [])
        topic_meta = next((t for t in grade_topics if t['id'] == topic_id), {})

        output = {
            'topic_id': topic_id,
            'topic_name': topic_meta.get('name', topic_id),
            'topic_emoji': topic_meta.get('emoji', ''),
            'grade': grade,
            'domain': topic_meta.get('domain', ''),
            'skills': topic_meta.get('skills', []),
            'total_questions': len(questions),
            'difficulty_range': {
                'min_irt_b': round(min((q.get('irt_b', 0) for q in questions), default=0), 3),
                'max_irt_b': round(max((q.get('irt_b', 0) for q in questions), default=0), 3),
            },
            'source_breakdown': {},
            'schema_version': '4.0',
            'generated_at': datetime.now().isoformat(),
            'questions': questions
        }

        # Source breakdown
        sources = defaultdict(int)
        for q in questions:
            sources[q.get('content_source', 'unknown')] += 1
        output['source_breakdown'] = dict(sources)

        # Write file
        out_dir = os.path.join(V4, 'adaptive', f'grade{grade}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'{topic_id}.json')
        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        total_written += len(questions)
        print(f"  Grade {grade} | {topic_meta.get('name', topic_id):30s} | {len(questions):5d} questions | IRT [{output['difficulty_range']['min_irt_b']:.2f} → {output['difficulty_range']['max_irt_b']:.2f}]")

    return total_written

def write_school_files(school_buckets):
    """Write content-v4/school/{curriculum}/grade{N}/chapters.json reference files."""
    curriculum_name_map = {
        'ncert': 'NCERT',
        'icse': 'ICSE',
        'igcse': 'Cambridge IGCSE',
        'singapore': 'Singapore Math',
        'us-common-core': 'US Common Core'
    }

    total_written = 0
    for (curr_key, grade), questions in sorted(school_buckets.items()):
        # Group by chapter
        chapters = defaultdict(list)
        for q in questions:
            ch = q.get('chapter', 'General')
            if not ch:
                ch = 'General'
            chapters[ch].append(q)

        # Build chapter list with question references
        chapter_list = []
        for ch_name, ch_questions in sorted(chapters.items()):
            # Sort by sequence within chapter
            ch_questions.sort(key=lambda q: q.get('irt_b', q.get('irt_params', {}).get('b', 0)))

            chapter_list.append({
                'chapter_name': ch_name,
                'total_questions': len(ch_questions),
                'skill_ids': list(set(q.get('skill_id', '') for q in ch_questions)),
                'adaptive_topic_ids': list(set(q.get('adaptive_topic_id', '') for q in ch_questions)),
                'question_ids': [q['id'] for q in ch_questions],
                'difficulty_range': {
                    'min': round(min((q.get('irt_b', 0) for q in ch_questions), default=0), 3),
                    'max': round(max((q.get('irt_b', 0) for q in ch_questions), default=0), 3),
                }
            })

        output = {
            'curriculum': curr_key,
            'curriculum_name': curriculum_name_map.get(curr_key, curr_key),
            'grade': grade,
            'total_chapters': len(chapter_list),
            'total_questions': len(questions),
            'chapters': chapter_list,
            'schema_version': '4.0',
            'generated_at': datetime.now().isoformat()
        }

        # Write file
        folder_map = {
            'ncert': 'ncert',
            'icse': 'icse',
            'igcse': 'igcse',
            'singapore': 'singapore',
            'us-common-core': 'us-common-core'
        }
        out_dir = os.path.join(V4, 'school', folder_map.get(curr_key, curr_key), f'grade{grade}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'chapters.json')
        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        total_written += len(questions)
        print(f"  {curriculum_name_map.get(curr_key, curr_key):20s} Grade {grade} | {len(chapter_list):3d} chapters | {len(questions):5d} questions")

    return total_written

def write_grade_index(buckets, topic_map):
    """Write a grade-level index file for each grade."""
    for grade in range(1, 7):
        grade_topics = topic_map['grades'].get(str(grade), {}).get('topics', [])
        index_topics = []
        for topic in grade_topics:
            key = (grade, topic['id'])
            questions = buckets.get(key, [])
            index_topics.append({
                'id': topic['id'],
                'name': topic['name'],
                'emoji': topic['emoji'],
                'domain': topic['domain'],
                'skills': topic['skills'],
                'total_questions': len(questions),
                'difficulty_range': {
                    'min': round(min((q.get('irt_b', 0) for q in questions), default=0), 3),
                    'max': round(max((q.get('irt_b', 0) for q in questions), default=0), 3),
                } if questions else {'min': 0, 'max': 0}
            })

        index = {
            'grade': grade,
            'total_topics': len(index_topics),
            'total_questions': sum(t['total_questions'] for t in index_topics),
            'topics': index_topics,
            'schema_version': '4.0',
            'generated_at': datetime.now().isoformat()
        }

        out_path = os.path.join(V4, 'adaptive', f'grade{grade}', 'index.json')
        with open(out_path, 'w') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 70)
    print("KIWIMATH CONTENT v4 REORGANIZATION")
    print("=" * 70)

    # Load topic map
    print("\n[1/6] Loading topic map...")
    topic_map = load_topic_map()
    skill_to_topic = build_skill_to_topic(topic_map)
    for g in range(1, 7):
        print(f"  Grade {g}: {len(skill_to_topic[g])} skills mapped to topics")

    # Load all questions
    print("\n[2/6] Loading olympiad questions...")
    olympiad_qs = load_olympiad_questions()
    print(f"  Loaded {len(olympiad_qs)} olympiad questions")

    print("\n[3/6] Loading curriculum questions...")
    curriculum_qs = load_curriculum_questions()
    print(f"  Loaded {len(curriculum_qs)} curriculum questions")
    print(f"  Total: {len(olympiad_qs) + len(curriculum_qs)} questions")

    # Process and assign to topics
    print("\n[4/6] Mapping questions to adaptive topics...")
    buckets, school_buckets, stats = process_questions(
        olympiad_qs, curriculum_qs, skill_to_topic, topic_map
    )
    print(f"  Olympiad mapped: {stats['olympiad_mapped']}")
    print(f"  Olympiad cloned for G5-6: {stats['olympiad_cloned_g56']}")
    print(f"  Curriculum mapped: {stats['curriculum_mapped']}")
    print(f"  Fallback used: {stats['fallback_used']}")
    if stats['skill_mismatches']:
        print(f"  Skill mismatches: {dict(stats['skill_mismatches'])}")

    total_adaptive = sum(len(qs) for qs in buckets.values())
    print(f"  Total in adaptive buckets: {total_adaptive}")

    # Write adaptive files
    print("\n[5/6] Writing adaptive topic files (IRT-sequenced)...")
    adaptive_written = write_adaptive_files(buckets, topic_map)

    # Write grade indexes
    write_grade_index(buckets, topic_map)
    print(f"\n  Total adaptive questions written: {adaptive_written}")

    # Write school files
    print("\n[6/6] Writing school curriculum reference files...")
    school_written = write_school_files(school_buckets)
    print(f"\n  Total school references written: {school_written}")

    # Summary
    print("\n" + "=" * 70)
    print("REORGANIZATION COMPLETE")
    print("=" * 70)
    print(f"  Original questions:     {len(olympiad_qs) + len(curriculum_qs):,}")
    print(f"  Adaptive (with clones): {adaptive_written:,}")
    print(f"  School references:      {school_written:,}")
    print(f"  Unique topics:          {len(buckets)}")
    print(f"  Grade breakdown:")
    for grade in range(1, 7):
        grade_total = sum(len(qs) for (g, _), qs in buckets.items() if g == grade)
        n_topics = sum(1 for (g, _) in buckets if g == grade)
        print(f"    Grade {grade}: {grade_total:5d} questions across {n_topics} topics")

if __name__ == '__main__':
    main()
