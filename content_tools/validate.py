"""
Kiwimath content validator.

Scans a content folder for JSON question files, validates each against the
schema, and checks cross-file references (step-downs must exist, ids must be
unique, etc.).

Usage:
    python -m content_tools.validate <content_root>
    python -m content_tools.validate ~/Documents/Kiwimath-Content/Grade1/

Exit codes:
    0 — all questions valid
    1 — one or more questions invalid (details printed)
    2 — usage error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Make the sibling 'backend' package importable when running from repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.models.question import (  # noqa: E402
    Question,
    StepDownQuestion,
    is_step_down_id,
    parse_question_file,
)


# ANSI colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def find_question_files(root: Path) -> List[Path]:
    """Return all *.json files under root that look like question files."""
    if not root.exists():
        return []
    candidates = sorted(root.rglob("*.json"))
    # Skip anything inside .git, node_modules, etc.
    return [p for p in candidates if not any(part.startswith(".") for part in p.parts)]


def validate_one(path: Path) -> Tuple[bool, str, object]:
    """Validate a single file. Returns (ok, message, parsed_obj_or_None)."""
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e}", None
    try:
        obj = parse_question_file(data)
    except Exception as e:
        return False, f"schema error: {e}", None
    return True, "ok", obj


def validate_folder(root: Path) -> int:
    files = find_question_files(root)
    if not files:
        print(f"{YELLOW}No JSON files found under {root}{RESET}")
        return 0

    print(f"{BOLD}Kiwimath content validator{RESET}")
    print(f"Scanning {root} — found {len(files)} JSON file(s)\n")

    results: Dict[Path, Tuple[bool, str, object]] = {}
    parents: Dict[str, Question] = {}
    step_downs: Dict[str, StepDownQuestion] = {}
    all_ids: Dict[str, Path] = {}

    for f in files:
        ok, msg, obj = validate_one(f)
        results[f] = (ok, msg, obj)
        if ok and obj is not None:
            if obj.id in all_ids:
                results[f] = (
                    False,
                    f"duplicate id '{obj.id}' — also defined at {all_ids[obj.id]}",
                    None,
                )
                continue
            all_ids[obj.id] = f
            if isinstance(obj, Question):
                parents[obj.id] = obj
            elif isinstance(obj, StepDownQuestion):
                step_downs[obj.id] = obj

    # Cross-file checks
    cross_errors: List[Tuple[Path, str]] = []

    # 1) Every step_down_path id referenced by a parent must exist.
    for parent in parents.values():
        for m in parent.misconceptions:
            for sd_id in m.step_down_path:
                if sd_id not in step_downs:
                    cross_errors.append(
                        (
                            all_ids[parent.id],
                            f"references step-down '{sd_id}' which does not exist "
                            f"on disk (misconception: {m.diagnosis})",
                        )
                    )

    # 2) Every step-down must have a matching parent on disk.
    for sd in step_downs.values():
        if sd.parent_id not in parents:
            cross_errors.append(
                (
                    all_ids[sd.id],
                    f"parent_id '{sd.parent_id}' not found on disk "
                    f"(orphaned step-down)",
                )
            )

    # Report
    ok_count = sum(1 for (ok, _, _) in results.values() if ok) - len(
        [e for e in cross_errors]
    )
    fail_count = len(files) - ok_count

    for f in files:
        ok, msg, obj = results[f]
        rel = f.relative_to(root) if f.is_relative_to(root) else f
        if ok:
            qid = obj.id if obj else "?"
            kind = "step-down" if is_step_down_id(qid) else "parent"
            print(f"  {GREEN}✓{RESET} {rel}  {DIM}[{kind} {qid}]{RESET}")
        else:
            print(f"  {RED}✗{RESET} {rel}")
            print(f"      {RED}{msg}{RESET}")

    if cross_errors:
        print(f"\n{BOLD}Cross-file reference errors:{RESET}")
        for path, err in cross_errors:
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            print(f"  {RED}✗{RESET} {rel}")
            print(f"      {RED}{err}{RESET}")

    # Summary
    print()
    total_fail = fail_count + len(cross_errors)
    if total_fail == 0:
        print(
            f"{GREEN}{BOLD}All {len(files)} question(s) valid.{RESET}  "
            f"({len(parents)} parents, {len(step_downs)} step-downs)"
        )
        return 0
    print(
        f"{RED}{BOLD}{total_fail} error(s) across {len(files)} file(s).{RESET}  "
        f"Fix the above and re-run."
    )
    return 1


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = Path(argv[1]).expanduser().resolve()
    return validate_folder(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
