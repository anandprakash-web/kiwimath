"""Content quality report — scans every topic in content-v2/ and emits a
human-readable summary of stem-template repetition, choice-length sanity,
hint-ladder coverage, and difficulty distribution.

Run from the kiwimath repo root:

    python3 backend/scripts/content_quality_report.py \
        --content-dir content-v2 \
        --top-templates 10 \
        --output content-v2/_workspace/quality_report.md

Designed to be safe to run repeatedly; never modifies content files.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NUM_RE = re.compile(r"\d+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def normalize_stem(stem: str, words: int = 8) -> str:
    """Collapse numbers + punctuation + lowercase, keep first N words.

    Two questions that only differ in their numbers will map to the same
    template — this is what we use to detect template repetition.
    """
    s = _NUM_RE.sub("#", stem)
    s = _PUNCT_RE.sub("", s)
    s = " ".join(s.split())
    s = " ".join(s.lower().split()[:words])
    return s


def grade_band(diff: int) -> str:
    if diff <= 50:
        return "G1"
    if diff <= 100:
        return "G2"
    if diff <= 150:
        return "G3"
    if diff <= 200:
        return "G4"
    return "G5+"


def difficulty_bucket(diff: int) -> str:
    if diff <= 33:
        return "easy"
    if diff <= 66:
        return "medium"
    if diff <= 100:
        return "hard"
    if diff <= 130:
        return "advanced"
    if diff <= 170:
        return "expert"
    return "olympiad"


def iter_topic_questions(topic_dir: Path) -> Iterable[dict]:
    for f in sorted(topic_dir.glob("*questions*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        items = data.get("questions") if isinstance(data, dict) else data
        for q in items or []:
            q.setdefault("_source_file", f.name)
            yield q


# ---------------------------------------------------------------------------
# Per-topic report
# ---------------------------------------------------------------------------


def topic_report(topic_dir: Path, top_templates: int) -> str:
    out: list[str] = []
    qs = list(iter_topic_questions(topic_dir))

    if not qs:
        return f"## {topic_dir.name}\n_no questions found._\n"

    out.append(f"## {topic_dir.name} — {len(qs)} questions\n")

    # Difficulty + grade distribution
    diffs = [int(q.get("difficulty_score", 0)) for q in qs]
    bucket_counts = Counter(difficulty_bucket(d) for d in diffs)
    grade_counts = Counter(grade_band(d) for d in diffs)
    out.append("**Difficulty distribution**\n")
    for b in ["easy", "medium", "hard", "advanced", "expert", "olympiad"]:
        c = bucket_counts.get(b, 0)
        if c:
            out.append(f"- {b}: {c}")
    out.append("")
    out.append("**Grade-band distribution**")
    for g in ["G1", "G2", "G3", "G4", "G5+"]:
        c = grade_counts.get(g, 0)
        if c:
            out.append(f"- {g}: {c}")
    out.append(f"- range: [{min(diffs)}, {max(diffs)}]")
    out.append("")

    # Hint-ladder coverage. Different generators use different field names
    # for the hint ladder — check all of them.
    def _hint_count(q: dict) -> int:
        for key in ("hints", "hint_ladder", "hint"):
            v = q.get(key)
            if isinstance(v, list):
                return len(v)
            if isinstance(v, dict):
                return len(v)
        return 0
    no_hints = sum(1 for q in qs if _hint_count(q) == 0)
    short_hints = sum(1 for q in qs if 0 < _hint_count(q) < 3)
    out.append("**Hint coverage**")
    out.append(f"- questions with zero hints: {no_hints}")
    out.append(f"- questions with fewer than 3 hints: {short_hints}")
    out.append("")

    # Choice sanity
    bad_choices = []
    for q in qs:
        ch = q.get("choices") or []
        if len(ch) < 2 or any(not str(c).strip() for c in ch):
            bad_choices.append(q.get("question_id", "?"))
    if bad_choices:
        out.append(f"**Choice issues**: {len(bad_choices)} (e.g. {bad_choices[:5]})")
        out.append("")

    # Template repetition — split by grade band so G1-2 and G3-4 are scored
    # independently (their templates are written by different generators).
    out.append("**Template repetition (top stem prefixes by grade band)**\n")
    by_band: dict[str, list[dict]] = defaultdict(list)
    for q in qs:
        by_band[grade_band(int(q.get("difficulty_score", 0)))].append(q)

    flag = False
    for band in ["G1", "G2", "G3", "G4"]:
        items = by_band.get(band, [])
        if not items:
            continue
        templates = Counter(normalize_stem(q.get("stem", ""), words=8) for q in items)
        most = templates.most_common(top_templates)
        # Worst offender threshold — flag if any template covers >5% of band.
        worst = most[0] if most else (None, 0)
        worst_pct = (worst[1] / len(items)) * 100 if items else 0
        flag_marker = " ⚠️" if worst_pct >= 5 else ""
        out.append(f"_{band} ({len(items)} questions, top template = {worst_pct:.1f}%){flag_marker}_")
        for tpl, c in most:
            pct = (c / len(items)) * 100
            short = (tpl[:60] + "…") if len(tpl) > 60 else tpl
            out.append(f"- {c}× ({pct:.1f}%) `{short}`")
        out.append("")
        if worst_pct >= 5:
            flag = True

    if flag:
        out.append("> ⚠️ Topic has at least one stem template covering ≥5% of a "
                   "grade band. Worth a content-variety pass.")
        out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-dir", default="content-v2")
    ap.add_argument("--top-templates", type=int, default=8)
    ap.add_argument("--output", default=None,
                    help="Write report to this path (default: stdout).")
    args = ap.parse_args()

    root = Path(args.content_dir)
    if not root.exists():
        raise SystemExit(f"content-dir not found: {root}")

    parts: list[str] = [
        "# Kiwimath content quality report",
        "",
        f"_content-dir: `{root}`_",
        "",
    ]
    total = 0
    for topic_dir in sorted(root.glob("topic-*")):
        section = topic_report(topic_dir, args.top_templates)
        parts.append(section)
        # Accumulate total
        total += sum(1 for _ in iter_topic_questions(topic_dir))

    parts.insert(2, f"**Total questions: {total}**")
    parts.insert(3, "")

    text = "\n".join(parts)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"Wrote {out} ({len(text):,} bytes)")
    else:
        print(text)


if __name__ == "__main__":
    main()
