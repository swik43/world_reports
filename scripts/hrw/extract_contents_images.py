"""
Extract contents pages from HRW World Report PDFs as PNG images.

Reads data/hrw/contents_config.json, renders the specified contents pages
from each original PDF, and saves them as PNGs in data/hrw/contents_images/.

Usage:
    python scripts/hrw/extract_contents_images.py          # all PDFs
    python scripts/hrw/extract_contents_images.py 2023     # specific years
"""

import json
import sys
from pathlib import Path

import pypdfium2 as pdfium

HRW_DIR = Path("HRW")
CONFIG_PATH = Path("data/hrw/contents_config.json")
OUTPUT_DIR = Path("data/hrw/contents_images")

SCALE = 3  # render at 3x for readability


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_name, info in sorted(config.items()):
        if year_filter:
            year = pdf_name.split("_")[0]
            if year not in year_filter:
                continue

        contents_pages = info["contents_pages"]
        if not contents_pages:
            continue

        pdf_path = HRW_DIR / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_name} not found, skipping")
            continue

        stem = pdf_name.replace(".pdf", "")
        out_dir = OUTPUT_DIR / stem
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf = pdfium.PdfDocument(str(pdf_path))
        for page_num in contents_pages:
            page = pdf[page_num - 1]  # 0-indexed
            bitmap = page.render(scale=SCALE)
            image = bitmap.to_pil()
            out_path = out_dir / f"page_{page_num}.png"
            image.save(str(out_path))

        pdf.close()
        print(f"{pdf_name}: {len(contents_pages)} pages -> {out_dir}/")

    print(f"\nDone. Images in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
