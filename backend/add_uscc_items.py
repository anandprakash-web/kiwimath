"""
Script to add US Common Core items to assessment_items.json.

Reads 6 USCC question files, extracts IRT params, maps chapters to domains,
and appends to the existing assessment_items.json.
"""

import json
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content-v2" / "us-common-core"
ITEMS_FILE = Path(__file__).resolve().parent / "assessment_items.json"

# Chapter -> domain mapping
CHAPTER_TO_DOMAIN = {
    "Operations & Algebraic Thinking": "arithmetic",
    "Number & Operations in Base Ten": "numbers",
    "Number & Operations--Fractions": "fractions",
    "Measurement & Data": "measurement",
    "Geometry": "geometry",
    "Ratios & Proportional Relationships": "arithmetic",
    "The Number System": "numbers",
    "Expressions & Equations": "arithmetic",
    "Statistics & Probability": "measurement",
}


def get_subdomain(chapter: str, tags: list) -> str:
    """Build a subdomain string from chapter and tags."""
    # Use the first CCSS standard tag if available (e.g., '1.OA.1')
    for tag in tags:
        if "." in tag and any(c.isdigit() for c in tag):
            return tag
    # Fallback: use chapter abbreviated
    return chapter.lower().replace(" & ", "_").replace(" ", "_")[:30]


def get_grade_range(grade: int) -> list:
    """Return grade range [grade, grade+1] capped at 6."""
    return [grade, min(grade + 1, 6)]


def main():
    # Load existing items
    with open(ITEMS_FILE) as f:
        existing_items = json.load(f)

    existing_ids = {item["item_id"] for item in existing_items}
    print(f"Existing items: {len(existing_items)}")
    print(f"Existing unique IDs: {len(existing_ids)}")

    new_items = []
    skipped = 0

    for grade_num in range(1, 7):
        json_path = CONTENT_DIR / f"grade{grade_num}" / f"uscc_g{grade_num}_questions.json"
        if not json_path.exists():
            print(f"  WARNING: {json_path} not found")
            continue

        with open(json_path) as f:
            data = json.load(f)

        questions = data.get("questions", [])
        grade_count = 0

        for q in questions:
            item_id = q.get("id")
            if not item_id:
                continue
            if not item_id.startswith("USCC-"):
                continue
            if item_id in existing_ids:
                skipped += 1
                continue

            irt_params = q.get("irt_params", {})
            chapter = q.get("chapter", "")
            tags = q.get("tags", [])

            domain = CHAPTER_TO_DOMAIN.get(chapter, "numbers")
            subdomain = get_subdomain(chapter, tags)

            item = {
                "item_id": item_id,
                "a": irt_params.get("a", 1.0),
                "b": irt_params.get("b", 0.0),
                "c": irt_params.get("c", 0.25),
                "domain": domain,
                "subdomain": subdomain,
                "curriculum_tags": ["US_COMMON_CORE"],
                "grade_range": get_grade_range(grade_num),
                "state": "active",
            }

            new_items.append(item)
            existing_ids.add(item_id)
            grade_count += 1

        print(f"  Grade {grade_num}: {grade_count} items added")

    print(f"\nNew items to add: {len(new_items)}")
    print(f"Skipped (duplicates): {skipped}")

    # Append and write
    all_items = existing_items + new_items
    print(f"Total items after merge: {len(all_items)}")

    # Verify no duplicates
    all_ids = [item["item_id"] for item in all_items]
    unique_ids = set(all_ids)
    if len(all_ids) != len(unique_ids):
        print(f"ERROR: Found {len(all_ids) - len(unique_ids)} duplicate IDs!")
        return
    else:
        print("No duplicates found.")

    with open(ITEMS_FILE, "w") as f:
        json.dump(all_items, f, indent=2)

    print(f"\nWrote {len(all_items)} items to {ITEMS_FILE}")

    # Print domain breakdown of new items
    domain_counts = {}
    for item in new_items:
        d = item["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1
    print("\nUSCC domain breakdown:")
    for d, c in sorted(domain_counts.items()):
        print(f"  {d}: {c}")


if __name__ == "__main__":
    main()
