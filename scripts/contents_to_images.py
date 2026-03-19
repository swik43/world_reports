"""
Convert AI_contents/ PDFs to PNG images for Claude vision.
Output: AI_contents_images/<pdf_name_without_ext>/page_1.png, page_2.png, ...

Uses pypdfium2 (already installed as pdfplumber dependency).
"""

from pathlib import Path

import pypdfium2 as pdfium

INPUT_DIR = Path("AI_contents")
OUTPUT_DIR = Path("AI_contents_images")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_path in sorted(INPUT_DIR.glob("*.pdf")):
        stem = pdf_path.stem
        out_dir = OUTPUT_DIR / stem
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf = pdfium.PdfDocument(str(pdf_path))
        for i in range(len(pdf)):
            page = pdf[i]
            bitmap = page.render(scale=3)  # 3x for readable text
            image = bitmap.to_pil()
            image.save(out_dir / f"page_{i + 1}.png")

        print(f"{stem}: {len(pdf)} page(s)")
        pdf.close()

    print(f"\nDone. Images in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
