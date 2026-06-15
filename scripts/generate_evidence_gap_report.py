#!/usr/bin/env python3
"""
generate_evidence_gap_report.py

Scans synergies.json, reports.json, and issues.json for entries with empty or
missing evidence arrays. Produces pipeline/output/evidence_gap_report.json with
risk levels and recommended actions, plus a printed summary.

Idempotent: safe to re-run; output file is overwritten each time.
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "pipeline" / "output"
OUTPUT_FILE = OUTPUT_DIR / "evidence_gap_report.json"

SYNERGIES_FILE = DATA_DIR / "synergies.json"
REPORTS_FILE = DATA_DIR / "reports.json"
ISSUES_FILE = DATA_DIR / "issues.json"
AUGMENTS_FILE = DATA_DIR / "augments.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list:
    """Load and return a JSON array from the given path."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_effectively_empty_evidence(evidence) -> bool:
    """
    Return True when evidence should be treated as empty/gap.

    Counts as empty:
      - None or not a list
      - []
      - [{}]                      (single dict with no keys)
      - [{"url": ""}]             (single dict whose url is blank/missing)
      - Any combination of the above in a list
    """
    if not evidence or not isinstance(evidence, list):
        return True

    def _entry_is_empty(entry):
        if not isinstance(entry, dict):
            return True
        if not entry:
            return True
        # All string values are empty/whitespace
        url = entry.get("url", "")
        if isinstance(url, str) and url.strip() == "":
            # Check if there are other meaningful fields
            meaningful_keys = {k for k in entry if k not in ("url",)}
            if not meaningful_keys:
                return True
            # Has other keys but check if all their values are also empty
            for k in meaningful_keys:
                v = entry[k]
                if isinstance(v, str) and v.strip():
                    return False
                if isinstance(v, (int, float, bool)):
                    return False
                if isinstance(v, list) and v:
                    return False
                if isinstance(v, dict) and v:
                    return False
            return True
        return False

    return all(_entry_is_empty(e) for e in evidence)


def count_real_evidence(evidence) -> int:
    """Return the number of evidence entries that are not effectively empty."""
    if not evidence or not isinstance(evidence, list):
        return 0
    return sum(1 for e in evidence if not is_effectively_empty_evidence([e]))


def build_augment_prototype_map(augments: list) -> dict:
    """
    Build a lookup: augment name -> source_status.
    Checks both 'name' and 'name_en' fields, as well as 'aliases'.
    """
    mapping = {}
    for aug in augments:
        status = aug.get("source_status", "")
        names = set()
        if aug.get("name"):
            names.add(aug["name"])
        if aug.get("name_en"):
            names.add(aug["name_en"])
        for alias in aug.get("aliases", []):
            names.add(alias)
        for n in names:
            mapping[n] = status
    return mapping


def aug_is_prototype(aug_name: str, proto_map: dict) -> bool:
    """Check whether an augment name resolves to source_status='prototype'."""
    if not aug_name:
        return False
    return proto_map.get(aug_name) == "prototype"


def any_aug_is_prototype(aug_names: list, proto_map: dict) -> bool:
    """Return True if any of the given augment names is prototype."""
    return any(aug_is_prototype(n, proto_map) for n in aug_names if n)


# ---------------------------------------------------------------------------
# Risk / action determination
# ---------------------------------------------------------------------------

def determine_risk_and_action(status: str, src: str, aug_names: list,
                              proto_map: dict) -> tuple:
    """
    Apply the risk-level rules (in priority order) and return
    (risk_level, recommended_action).

    Priority (highest first):
      1. status="verified" + empty evidence  -> high / add_evidence
      2. src="data" or "community" + empty   -> high / downgrade_status
      3. status="investigating" + empty      -> medium / keep_but_warn
      4. augment has source_status=prototype -> low / mark_as_prototype_sample
      5. fallback                           -> medium / keep_but_warn
    """
    # Rule 1: verified + empty evidence
    if status == "verified":
        return ("high", "add_evidence")

    # Rule 2: src is data or community + empty evidence
    if src in ("data", "community"):
        return ("high", "downgrade_status")

    # Rule 3: investigating + empty evidence
    if status == "investigating":
        return ("medium", "keep_but_warn")

    # Rule 4: augment referenced has source_status="prototype"
    if any_aug_is_prototype(aug_names, proto_map):
        return ("low", "mark_as_prototype_sample")

    # Fallback
    return ("medium", "keep_but_warn")


# ---------------------------------------------------------------------------
# Gap entry builders
# ---------------------------------------------------------------------------

def process_synergies(synergies: list, proto_map: dict) -> list:
    gaps = []
    for idx, entry in enumerate(synergies):
        evidence = entry.get("evidence")
        if not is_effectively_empty_evidence(evidence):
            continue
        hero = entry.get("hero", "")
        aug = entry.get("aug", "")
        aug_names = [aug] if aug else []
        status = entry.get("status", "")
        src = entry.get("src", "")
        risk, action = determine_risk_and_action(status, src, aug_names, proto_map)
        gaps.append({
            "file": "synergies.json",
            "index": idx + 1,
            "id_or_key": f"{hero}+{aug}",
            "hero": hero,
            "aug": aug,
            "tier_or_type": entry.get("tier", ""),
            "status": status,
            "src": src,
            "current_evidence_count": count_real_evidence(evidence),
            "risk_level": risk,
            "recommended_action": action,
        })
    return gaps


def process_reports(reports: list, proto_map: dict) -> list:
    gaps = []
    for idx, entry in enumerate(reports):
        evidence = entry.get("evidence")
        if not is_effectively_empty_evidence(evidence):
            continue
        hero = entry.get("hero", "")
        aug = entry.get("aug", "")
        aug_names = [aug] if aug else []
        status = entry.get("status", "")
        src = entry.get("src", "")
        risk, action = determine_risk_and_action(status, src, aug_names, proto_map)
        gaps.append({
            "file": "reports.json",
            "index": idx + 1,
            "id_or_key": str(idx + 1),  # use index for reports
            "hero": hero,
            "aug": aug,
            "tier_or_type": entry.get("type", ""),
            "status": status,
            "src": src,
            "current_evidence_count": count_real_evidence(evidence),
            "risk_level": risk,
            "recommended_action": action,
        })
    return gaps


def process_issues(issues: list, proto_map: dict) -> list:
    gaps = []
    for idx, entry in enumerate(issues):
        evidence = entry.get("evidence")
        if not is_effectively_empty_evidence(evidence):
            continue
        title = entry.get("title", "")
        heroes = entry.get("heroes", [])
        augs = entry.get("augs", [])
        hero = heroes[0] if heroes else ""
        aug = ", ".join(augs) if augs else ""
        status = entry.get("status", "")
        src = entry.get("src", "")
        risk, action = determine_risk_and_action(status, src, augs, proto_map)
        gaps.append({
            "file": "issues.json",
            "index": idx + 1,
            "id_or_key": title,
            "hero": hero,
            "aug": aug,
            "tier_or_type": entry.get("sev", ""),
            "status": status,
            "src": src,
            "current_evidence_count": count_real_evidence(evidence),
            "risk_level": risk,
            "recommended_action": action,
        })
    return gaps


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load data
    synergies = load_json(SYNERGIES_FILE)
    reports = load_json(REPORTS_FILE)
    issues = load_json(ISSUES_FILE)
    augments = load_json(AUGMENTS_FILE)

    # Build prototype lookup
    proto_map = build_augment_prototype_map(augments)

    # Collect gaps
    all_gaps = []
    all_gaps.extend(process_synergies(synergies, proto_map))
    all_gaps.extend(process_reports(reports, proto_map))
    all_gaps.extend(process_issues(issues, proto_map))

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_gaps, f, ensure_ascii=False, indent=2)

    # ---- Summary ----
    risk_counts = {}
    action_counts = {}
    file_counts = {}
    for g in all_gaps:
        risk_counts[g["risk_level"]] = risk_counts.get(g["risk_level"], 0) + 1
        action_counts[g["recommended_action"]] = action_counts.get(g["recommended_action"], 0) + 1
        file_counts[g["file"]] = file_counts.get(g["file"], 0) + 1

    total = len(all_gaps)
    print("=" * 60)
    print("  Evidence Gap Report Summary")
    print("=" * 60)
    print(f"\n  Total gaps found: {total}")
    print(f"  Output written to: {OUTPUT_FILE}")

    print(f"\n  --- By source file ---")
    for fname in ("synergies.json", "reports.json", "issues.json"):
        print(f"    {fname}: {file_counts.get(fname, 0)}")

    print(f"\n  --- By risk_level ---")
    for level in ("high", "medium", "low"):
        print(f"    {level}: {risk_counts.get(level, 0)}")

    print(f"\n  --- By recommended_action ---")
    for action in ("add_evidence", "downgrade_status", "keep_but_warn",
                    "mark_as_prototype_sample"):
        print(f"    {action}: {action_counts.get(action, 0)}")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
