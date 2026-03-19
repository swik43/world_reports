"""
Convert per-country PDFs to Markdown using pymupdf4llm.

Reads split PDFs from output/ai/<year>/<Country>.pdf and writes
Markdown files to output/ai_markdown/<year>/<Country>.md.

Only processes post-2012 reports where the layout is single-column
and pymupdf4llm produces clean output.

Usage:
    python scripts/ai/convert_to_markdown.py              # all eligible years
    python scripts/ai/convert_to_markdown.py 2023 2022    # specific years
"""

import re
import sys
from pathlib import Path

import pymupdf4llm

PDF_DIR = Path("output/ai")
MD_DIR = Path("output/ai_markdown")

MIN_YEAR = 2013


def extract_year(dir_name: str) -> int:
    match = re.match(r"(\d{4})", dir_name)
    if match:
        return int(match.group(1))
    return 0


def convert_dir(year_dir: Path) -> None:
    md_dest = MD_DIR / year_dir.name
    md_dest.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(year_dir.glob("*.pdf"))
    converted = 0

    for pdf_path in pdfs:
        out_path = md_dest / pdf_path.with_suffix(".md").name
        md_text = pymupdf4llm.to_markdown(str(pdf_path))
        out_path.write_text(md_text, encoding="utf-8")
        converted += 1

    print(f"  {year_dir.name}: {converted} files -> {md_dest}")


def main():
    if not PDF_DIR.exists():
        print(f"Error: {PDF_DIR} not found.")
        return

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    year_dirs = sorted(
        d for d in PDF_DIR.iterdir()
        if d.is_dir() and extract_year(d.name) >= MIN_YEAR
    )

    if year_filter:
        year_dirs = [d for d in year_dirs if re.match(r"(\d{4})", d.name).group(1) in year_filter]

    if not year_dirs:
        print("No matching year directories found.")
        return

    MD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Converting PDFs to Markdown...")
    for year_dir in year_dirs:
        convert_dir(year_dir)

    print(f"\nDone. Output in {MD_DIR}/")


if __name__ == "__main__":
    main()
