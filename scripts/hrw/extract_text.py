"""
Extract text from HRW World Report PDFs with font metadata.

For each page, outputs each text block with its font size, font name,
and whether it's bold — so we can inspect how headings differ from body text.

Usage:
    python extract_text.py [year1 year2 ...]
    python extract_text.py          # defaults to 2004 and 2012
"""

import json
import sys
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
PDF_DIR = REPO / "HRW"
OUT_DIR = REPO / "data" / "hrw" / "extracted"


def extract_pdf(pdf_path: Path, out_path: Path):
    doc = pymupdf.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = []

        # Get detailed text info: spans with font metadata
        text_dict = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict["blocks"]:
            if block["type"] != 0:  # skip image blocks
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    blocks.append(
                        {
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"], 1),
                            "bold": "bold" in span["font"].lower()
                            or "black" in span["font"].lower(),
                            "bbox": [round(x, 1) for x in span["bbox"]],
                        }
                    )

        pages.append(
            {
                "page": page_num + 1,
                "blocks": blocks,
            }
        )

    doc.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(pages, f, indent=2)

    print(f"Wrote {len(pages)} pages to {out_path}")


def main():
    years = [int(y) for y in sys.argv[1:]] if sys.argv[1:] else [2004, 2012]

    for year in years:
        pdf_path = PDF_DIR / f"{year}_World_Report_Human_Rights_Watch.pdf"
        if not pdf_path.exists():
            print(f"Not found: {pdf_path}")
            continue

        out_path = OUT_DIR / f"{year}.json"
        print(f"Extracting {pdf_path.name}...")
        extract_pdf(pdf_path, out_path)


if __name__ == "__main__":
    main()
