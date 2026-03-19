"""
Script 1: Parse Contents pages from Amnesty International PDFs.

Reads contents_config.json for page ranges and format presets,
extracts country names and report page numbers using pdfplumber,
and outputs parsed_contents.json for user review.

Presets:
  slash      - 2 columns, title case, "Country / page"  (1999-2012)
  space      - 2 columns, title case, "Country    page"  (2014, 2016-17, 2020-23)
  dots       - 1 column,  UPPERCASE,  "COUNTRY....page"  (2015)
  wide_space - 1 column,  UPPERCASE,  "COUNTRY      page" (2019)
"""

import json
import re
import sys
from pathlib import Path

import pdfplumber

AI_DIR = Path("AI")
CONFIG_PATH = AI_DIR / "contents_config.json"
OUTPUT_PATH = AI_DIR / "parsed_contents.json"

# Regex patterns per preset
PRESETS = {
    "slash": {
        "columns": 2,
        "pattern": re.compile(r"^(.+?)\s*/\s*(\d{1,4})\s*$"),
    },
    "space": {
        "columns": 2,
        "pattern": re.compile(r"^(.+?)\s+(\d{1,4})\s*$"),
    },
    "dots": {
        "columns": 1,
        "pattern": re.compile(r"^(.+?)\.{2,}\s*(\d{1,4})\s*$"),
    },
    "wide_space": {
        "columns": 1,
        "pattern": re.compile(r"^(.+?)\s+(\d{1,4})\s*$"),
    },
}


def extract_column_text(page, columns: int) -> str:
    """Extract text from a page, handling 1 or 2 column layouts."""
    if columns == 1:
        return page.extract_text() or ""

    # Split page into left and right halves
    width = page.width
    mid = width / 2

    left = page.crop((0, 0, mid, page.height))
    right = page.crop((mid, 0, width, page.height))

    left_text = left.extract_text() or ""
    right_text = right.extract_text() or ""

    return left_text + "\n" + right_text


def parse_entries(text: str, pattern: re.Pattern) -> list[dict]:
    """Parse country/page entries from text using the given regex pattern."""
    entries = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            name = match.group(1).strip().rstrip(".")
            page = int(match.group(2))

            if _is_country_entry(name):
                entries.append(
                    {
                        "name": _normalize_name(name),
                        "report_page": page,
                    }
                )

    return entries


def _is_country_entry(name: str) -> bool:
    """Filter out non-country entries like section headers."""
    skip_patterns = [
        r"^contents?$",
        r"^part\s",
        r"^chapter\s",
        r"^section\s",
        r"^foreword",
        r"^preface",
        r"^introduction",
        r"^appendix",
        r"^annex",
        r"^index",
        r"^glossary",
        r"^abbreviation",
        r"^acknowledgement",
        r"^regional\s+overview",
        r"^amnesty\s+international",
        r"^what\s+",
        r"^how\s+",
        r"^selected\s+",
        r"^international\s+",
    ]
    lower = name.lower().strip()
    if len(lower) < 3:
        return False
    for pat in skip_patterns:
        if re.match(pat, lower):
            return False
    return True


def _normalize_name(name: str) -> str:
    """Normalize country name to title case."""
    if name.isupper():
        name = name.title()
    name = re.sub(r"\s+", " ", name).strip()
    return name


def extract_contents_for_pdf(
    pdf_path: Path, contents_pages: list[int], preset_name: str
) -> dict:
    """Extract country entries from a single PDF's contents pages."""
    preset = PRESETS[preset_name]

    with pdfplumber.open(pdf_path) as pdf:
        all_entries = []
        for page_num in contents_pages:
            page_idx = page_num - 1  # config uses 1-indexed pages
            if page_idx < 0 or page_idx >= len(pdf.pages):
                print(f"  WARNING: Page {page_num} out of range for {pdf_path.name}")
                continue

            page = pdf.pages[page_idx]
            text = extract_column_text(page, preset["columns"])
            entries = parse_entries(text, preset["pattern"])
            all_entries.extend(entries)

        # Deduplicate (same country might appear at page boundary)
        seen = set()
        unique = []
        for entry in all_entries:
            key = (entry["name"], entry["report_page"])
            if key not in seen:
                seen.add(key)
                unique.append(entry)

        last_contents_page = max(contents_pages)

        # Calculate true pages
        for entry in unique:
            entry["true_page"] = last_contents_page + entry["report_page"]

        return {
            "last_contents_page": last_contents_page,
            "countries": unique,
        }


def main():
    debug = "--debug" in sys.argv

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    results = {}
    for pdf_name, info in sorted(config.items()):
        pdf_path = AI_DIR / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_name} not found, skipping")
            continue

        contents_pages = info["contents_pages"]
        preset_name = info["preset"]
        preset = PRESETS[preset_name]
        print(
            f"Processing {pdf_name} (pages: {contents_pages}, preset: {preset_name})..."
        )

        data = extract_contents_for_pdf(pdf_path, contents_pages, preset_name)
        results[pdf_name] = data

        n = len(data["countries"])
        print(f"  Found {n} countries")
        if n == 0 or debug:
            if n == 0:
                print("  WARNING: No countries found!")
            # Print raw extracted text for debugging
            with pdfplumber.open(pdf_path) as pdf:
                for page_num in contents_pages:
                    page = pdf.pages[page_num - 1]
                    text = extract_column_text(page, preset["columns"])
                    print(f"  --- Raw text page {page_num} ---")
                    for line in text.split("\n")[:15]:
                        print(f"    |{line}|")
                    print(f"    ... ({len(text.split(chr(10)))} lines total)")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {OUTPUT_PATH}")
    print("Review the output for correctness before running split_pdfs.py")


if __name__ == "__main__":
    main()
