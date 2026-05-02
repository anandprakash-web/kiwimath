#!/usr/bin/env python3
"""Validate the assessment item bank."""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(os.path.dirname(BASE)), "backend")

items_path = os.path.join(BACKEND, "assessment_items.json")
with open(items_path) as f:
    items = json.load(f)

print(f"=== VALIDATION REPORT ===")
print(f"Total items: {len(items)}")

# 1. Check unique IDs
ids = [item["item_id"] for item in items]
duplicates = [x for x in ids if ids.count(x) > 1]
unique_ids = len(set(ids))
print(f"\n1. ID Uniqueness:")
print(f"   Unique IDs: {unique_ids}/{len(ids)}")
if duplicates:
    print(f"   DUPLICATES FOUND: {set(duplicates)}")
else:
    print(f"   PASS - All IDs unique")

# 2. All domains assigned
domains = set(item["domain"] for item in items)
items_without_domain = [item["item_id"] for item in items if not item.get("domain")]
print(f"\n2. Domain Assignment:")
print(f"   Domains present: {sorted(domains)}")
if items_without_domain:
    print(f"   FAIL - {len(items_without_domain)} items missing domain")
else:
    print(f"   PASS - All items have domain assigned")

# 3. IRT parameter ranges
a_violations = []
b_violations = []
c_violations = []

for item in items:
    if not (0.3 <= item["a"] <= 3.0):
        a_violations.append((item["item_id"], item["a"]))
    if not (-4.0 <= item["b"] <= 4.0):
        b_violations.append((item["item_id"], item["b"]))
    if not (0.0 <= item["c"] <= 0.4):
        c_violations.append((item["item_id"], item["c"]))

print(f"\n3. IRT Parameter Ranges:")
print(f"   a (discrimination 0.3-3.0): {len(a_violations)} violations")
print(f"   b (difficulty -4.0 to 4.0): {len(b_violations)} violations")
print(f"   c (guessing 0.0-0.4): {len(c_violations)} violations")
if not (a_violations or b_violations or c_violations):
    print(f"   PASS - All IRT params in valid ranges")
else:
    if a_violations:
        print(f"   a violations: {a_violations[:5]}")
    if b_violations:
        print(f"   b violations: {b_violations[:5]}")
    if c_violations:
        print(f"   c violations: {c_violations[:5]}")

# 4. Domain balance
from collections import Counter
domain_counts = Counter(item["domain"] for item in items)
print(f"\n4. Domain Balance:")
total = len(items)
for domain in sorted(domain_counts.keys()):
    count = domain_counts[domain]
    pct = count / total * 100
    bar = "#" * int(pct / 2)
    print(f"   {domain:14s}: {count:4d} ({pct:5.1f}%) {bar}")

# Balance metric: ratio of min to max
min_count = min(domain_counts.values())
max_count = max(domain_counts.values())
ratio = min_count / max_count
print(f"\n   Min/Max ratio: {ratio:.2f} (1.0 = perfectly balanced)")
if ratio >= 0.3:
    print(f"   ACCEPTABLE - Reasonable distribution across domains")
else:
    print(f"   WARNING - Domains are significantly imbalanced")

# 5. Additional stats
print(f"\n5. Additional Statistics:")
a_vals = [item["a"] for item in items]
b_vals = [item["b"] for item in items]
c_vals = [item["c"] for item in items]
print(f"   a: min={min(a_vals):.3f}, max={max(a_vals):.3f}, mean={sum(a_vals)/len(a_vals):.3f}")
print(f"   b: min={min(b_vals):.3f}, max={max(b_vals):.3f}, mean={sum(b_vals)/len(b_vals):.3f}")
print(f"   c: min={min(c_vals):.3f}, max={max(c_vals):.3f}, mean={sum(c_vals)/len(c_vals):.3f}")

# Grade range check
grade_ranges = [tuple(item["grade_range"]) for item in items]
print(f"   Grade ranges present: {sorted(set(grade_ranges))}")

# Curriculum tags coverage
items_with_tags = sum(1 for item in items if item.get("curriculum_tags"))
print(f"   Items with curriculum_tags: {items_with_tags}/{len(items)}")

print(f"\n=== VALIDATION COMPLETE ===")
all_pass = (not duplicates and not items_without_domain and
            not a_violations and not b_violations and not c_violations)
print(f"Overall: {'ALL CHECKS PASSED' if all_pass else 'ISSUES FOUND'}")
