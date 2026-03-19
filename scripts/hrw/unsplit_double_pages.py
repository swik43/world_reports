"""
Convert double-layout HRW PDFs into single-page-per-sheet PDFs.

For each double-layout PDF (as marked in contents_config.json), this script:
- Keeps page 1 (cover) as-is
- Splits every page from double_start onward into left and right halves
- Writes the result to output/hrw_unsplit/<pdf_name>

This is non-destructive — original PDFs are never modified.

Usage:
    python scripts/hrw/unsplit_double_pages.py [year ...]
"""

import json
import re
import sys
from copy import deepcopy
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm

HRW_DIR = Path("HRW")
CONFIG_PATH = Path("data/hrw/contents_config.json")
OUTPUT_DIR = Path("output/hrw_unsplit")


def extract_year(pdf_name: str) -> str:
    match = re.match(r"(\d{4})_", pdf_name)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract year from {pdf_name}")


def split_page_halves(page):
    """Return (left_page, right_page) by cropping a page down the middle."""
    left = deepcopy(page)
    right = deepcopy(page)

    box = page.mediabox
    mid_x = (box.left + box.right) / 2

    left.mediabox.upper_right = (mid_x, box.top)
    right.mediabox.upper_left = (mid_x, box.top)
    right.mediabox.lower_left = (mid_x, box.bottom)

    return left, right


def process_pdf(pdf_name: str, cfg: dict):
    pdf_path = HRW_DIR / pdf_name
    if not pdf_path.exists():
        print(f"  WARNING: {pdf_path} not found, skipping")
        return

    double_start = cfg["double_start"]  # 1-indexed PDF page where doubles begin
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    for i, page in enumerate(tqdm(reader.pages, desc=f"  {pdf_name}", unit="pg")):
        page_num = i + 1  # 1-indexed

        if page_num < double_start:
            # Pre-double pages (cover, etc.) — keep as-is
            writer.add_page(page)
        else:
            left, right = split_page_halves(page)
            writer.add_page(left)
            writer.add_page(right)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / pdf_name
    with open(out_path, "wb") as f:
        writer.write(f)

    print(f"  {len(reader.pages)} pages -> {len(writer.pages)} pages -> {out_path}")


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    for pdf_name, cfg in sorted(config.items()):
        if cfg.get("layout") != "double":
            continue
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue
        print(f"Processing {pdf_name}...")
        process_pdf(pdf_name, cfg)

    print("\nDone.")


if __name__ == "__main__":
    main()
