"""
Split Amnesty International PDFs into per-country files.

Reads parsed_contents.json with format:
{
  "2023_Amnesty_International.pdf": [
    { "name": "Afghanistan", "true_page": 23 },
    { "name": "Albania", "true_page": 29 }
  ]
}

Each country's range: from its true_page to the next country's true_page - 1
(last country runs to end of PDF).

Output: AI_split/<year>/<Country_Name>.pdf
"""

import json
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter

AI_DIR = Path("AI")
OUTPUT_DIR = Path("AI_split")
PARSED_PATH = AI_DIR / "parsed_contents.json"


def extract_year(pdf_name: str) -> str:
    match = re.match(r"(\d{4})_", pdf_name)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract year from {pdf_name}")


def sanitize_filename(name: str) -> str:
    name = name.replace("/", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    return name.strip()


def year_dir_for(pdf_name: str) -> Path:
    year = extract_year(pdf_name)
    if "Africa" in pdf_name and "Amnesty" in pdf_name and "Middle" not in pdf_name:
        return OUTPUT_DIR / f"{year}_Africa"
    if "Americas" in pdf_name:
        return OUTPUT_DIR / f"{year}_Americas"
    if "Asia_Pacific" in pdf_name:
        return OUTPUT_DIR / f"{year}_Asia_Pacific"
    if "Eastern_Europe" in pdf_name:
        return OUTPUT_DIR / f"{year}_Eastern_Europe_Central_Asia"
    if "Middle_East" in pdf_name:
        return OUTPUT_DIR / f"{year}_Middle_East_North_Africa"
    return OUTPUT_DIR / year


def split_pdf(pdf_name: str, countries: list[dict]):
    pdf_path = AI_DIR / pdf_name
    if not pdf_path.exists():
        print(f"WARNING: {pdf_name} not found, skipping")
        return

    if not countries:
        print(f"  No countries to split for {pdf_name}")
        return

    dest = year_dir_for(pdf_name)
    dest.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    for i, country in enumerate(countries):
        start_page = country["true_page"]  # 1-indexed

        if i + 1 < len(countries):
            end_page = countries[i + 1]["true_page"] - 1
        else:
            end_page = total_pages

        start_idx = start_page - 1
        end_idx = end_page - 1

        if start_idx < 0 or start_idx >= total_pages:
            print(f"  WARNING: {country['name']} page {start_page} out of range (total: {total_pages})")
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_name, countries in sorted(parsed.items()):
        print(f"Splitting {pdf_name}...")
        split_pdf(pdf_name, countries)

    print(f"\nDone. Output in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
