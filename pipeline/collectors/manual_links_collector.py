"""
manual_links_collector.py
=========================
Reads manually collected links/extracts from a JSON config file,
validates each entry, and writes them to a JSONL output file.

Can be used as a library (``collect_manual()``) or as a CLI script.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------
_DEFAULT_INPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "config",
    "manual_links.json",
)
_DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "output",
    "manual_items.jsonl",
)

REQUIRED_FIELDS: List[str] = ["source", "url", "title"]
OPTIONAL_FIELDS: List[str] = ["platform", "text", "notes", "collected_at"]


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _validate_entry(entry: Dict[str, Any], index: int) -> bool:
    """Return *True* if the entry has all required fields, *False* otherwise."""
    missing_required = [f for f in REQUIRED_FIELDS if f not in entry or not entry[f]]
    if missing_required:
        logger.error(
            "Entry #%d is missing required field(s): %s — skipping.",
            index,
            ", ".join(missing_required),
        )
        return False

    missing_optional = [f for f in OPTIONAL_FIELDS if f not in entry]
    if missing_optional:
        logger.warning(
            "Entry #%d (%s) is missing optional field(s): %s",
            index,
            entry.get("url", "<no url>"),
            ", ".join(missing_optional),
        )

    return True


def _load_entries(input_path: str) -> List[Dict[str, Any]]:
    """Load and return the raw list of entries from *input_path*."""
    logger.info("Loading manual links from: %s", input_path)

    if not os.path.isfile(input_path):
        logger.error("Input file does not exist: %s", input_path)
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        logger.error("Expected a JSON array at the top level, got %s", type(data).__name__)
        raise ValueError("Top-level JSON must be an array of entries.")

    logger.info("Loaded %d raw entries.", len(data))
    return data


def _write_records(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write validated records as JSONL to *output_path*."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info("Wrote %d records to: %s", len(records), output_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def collect_manual(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load, validate, and persist manual-link entries.

    Parameters
    ----------
    input_path:
        Path to the manual_links JSON file.
        Defaults to ``pipeline/config/manual_links.json``.
    output_path:
        Path for the JSONL output.
        Defaults to ``pipeline/output/manual_items.jsonl``.

    Returns
    -------
    list[dict]
        The list of validated records (each with an added ``id`` field).
    """
    input_path = os.path.normpath(input_path or _DEFAULT_INPUT)
    output_path = os.path.normpath(output_path or _DEFAULT_OUTPUT)

    raw_entries = _load_entries(input_path)

    validated: List[Dict[str, Any]] = []
    for idx, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            logger.error("Entry #%d is not a JSON object — skipping.", idx)
            continue

        if not _validate_entry(entry, idx):
            continue

        record: Dict[str, Any] = {"id": f"manual_{idx}"}
        record.update(entry)
        validated.append(record)

    if not validated:
        logger.warning("No valid entries found. Output file will NOT be created.")
        return []

    _write_records(validated, output_path)
    logger.info(
        "Collection complete: %d/%d entries passed validation.",
        len(validated),
        len(raw_entries),
    )
    return validated


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect and validate manually curated links/extracts.",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        default=None,
        help=(
            "Path to the input JSON file. "
            f"Default: {_DEFAULT_INPUT}"
        ),
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help=(
            "Path for the JSONL output file. "
            f"Default: {_DEFAULT_OUTPUT}"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug-level logging.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        records = collect_manual(
            input_path=args.input_path,
            output_path=args.output_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Aborted: %s", exc)
        sys.exit(1)

    print(f"Done. {len(records)} record(s) written.")


if __name__ == "__main__":
    main()
