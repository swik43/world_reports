"""
Split HRW World Report PDFs into per-country files.

Reads parsed_contents.json with format:
{
  "2023_World_Report_Human_Rights_Watch.pdf": [
    { "name": "Afghanistan", "true_page": 23 },
    { "name": "Albania", "true_page": 29 }
  ]
}

Each country's range: from its true_page to the next country's true_page - 1
(last country runs to end of PDF).

Output: output/hrw/<year>/<Country_Name>.pdf
"""

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

HRW_DIR = Path("HRW")
UNSPLIT_DIR = Path("output/hrw_unsplit")
OUTPUT_DIR = Path("output/hrw")
PARSED_PATH = Path("data/hrw/parsed_contents.json")
CONFIG_PATH = Path("data/hrw/contents_config.json")


def extract_year(pdf_name: str) -> str:
    match = re.match(r"(\d{4})_", pdf_name)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract year from {pdf_name}")


def sanitize_filename(name: str) -> str:
    name = name.replace("/", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    return name.strip()


def split_pdf(pdf_name: str, countries: list[dict], config: dict):
    is_double = config.get(pdf_name, {}).get("layout") == "double"
    source_dir = UNSPLIT_DIR if is_double else HRW_DIR
    pdf_path = source_dir / pdf_name
    if not pdf_path.exists():
        print(f"WARNING: {pdf_name} not found, skipping")
        return

    if not countries:
        print(f"  No countries to split for {pdf_name}")
        return

    year = extract_year(pdf_name)
    dest = OUTPUT_DIR / year
    dest.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    for i, country in enumerate(countries):
        start_page = country["true_page"]  # 1-indexed

        if i + 1 < len(countries):
            end_page = max(start_page, countries[i + 1]["true_page"] - 1)
        else:
            end_page = total_pages

        start_idx = start_page - 1
        end_idx = end_page - 1

        if start_idx < 0 or start_idx >= total_pages:
            print(
                f"  WARNING: {country['name']} page {start_page} out of range (total: {total_pages})"
            )
            continue

        end_idx = min(end_idx, total_pages - 1)

        writer = PdfWriter()
        for page_idx in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[page_idx])

        filename = sanitize_filename(country["name"]) + ".pdf"
        with open(dest / filename, "wb") as f:
            writer.write(f)

    print(f"  Split into {len(countries)} files in {dest}")


def main():
    if not PARSED_PATH.exists():
        print(f"Error: {PARSED_PATH} not found.")
        return

    with open(PARSED_PATH) as f:
        parsed = json.load(f)
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    # Optional year filter: python split_pdfs.py 2023 2015 2019
    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_name, countries in sorted(parsed.items()):
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue
        print(f"Splitting {pdf_name}...")
        split_pdf(pdf_name, countries, config)

    if year_filter:
        print(f"\nDone. Processed years: {', '.join(sorted(year_filter))}")
    else:
        print(f"\nDone. Output in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
