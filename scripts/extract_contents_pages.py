"""
Extract contents pages from Amnesty International PDFs into short PDFs.

Reads contents_config.json for page ranges, extracts those pages,
and saves them to AI_contents/ mirroring the original file structure.
"""

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

AI_DIR = Path("AI")
OUTPUT_DIR = Path("AI_contents")
CONFIG_PATH = AI_DIR / "contents_config.json"


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_name, info in sorted(config.items()):
        pdf_path = AI_DIR / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_name} not found, skipping")
            continue

        contents_pages = info["contents_pages"]
        reader = PdfReader(str(pdf_path))

        writer = PdfWriter()
        for page_num in contents_pages:
            page_idx = page_num - 1  # config uses 1-indexed pages
            if 0 <= page_idx < len(reader.pages):
                writer.add_page(reader.pages[page_idx])
            else:
                print(f"  WARNING: Page {page_num} out of range for {pdf_name}")

        output_path = OUTPUT_DIR / pdf_name
        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"{pdf_name}: extracted pages {contents_pages} ({len(writer.pages)} pages)")

    print(f"\nDone. Output in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
