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
from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from rich.spinner import Spinner
from rich.text import Text

REPO = Path(__file__).resolve().parents[2]
PDF_DIR = REPO / "HRW"
OUT_DIR = REPO / "data" / "hrw" / "extracted"


def extract_pdf(
    pdf_path: Path,
    out_path: Path,
    *,
    spinner: Spinner,
    live: Live,
    overall_progress: Progress,
    overall_task,
):
    doc = pymupdf.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        spinner.update(
            text=Text(f"{pdf_path.name} / page {page_num + 1}", style="gray")
        )
        live.update(make_layout(spinner, overall_progress))

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

        overall_progress.advance(overall_task)

    doc.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(pages, f, indent=2)


def make_layout(spinner, overall_progress):
    return Group(spinner, overall_progress)


def main():
    years = [int(y) for y in sys.argv[1:]] if sys.argv[1:] else [2004, 2012]

    # Pre-scan: find valid PDFs and count total pages
    eligible: list[tuple[Path, Path]] = []
    total_pages = 0

    for year in years:
        pdf_path = PDF_DIR / f"{year}_World_Report_Human_Rights_Watch.pdf"
        if not pdf_path.exists():
            print(f"Not found: {pdf_path}")
            continue

        doc = pymupdf.open(pdf_path)
        total_pages += len(doc)
        doc.close()

        out_path = OUT_DIR / f"{year}.json"
        eligible.append((pdf_path, out_path))

    if not eligible:
        print("No eligible PDFs found.")
        return

    overall_progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )
    overall_task = overall_progress.add_task("Overall", total=total_pages)
    spinner = Spinner("dots", text=Text("Starting...", style="cyan"))

    with Live(make_layout(spinner, overall_progress), refresh_per_second=10) as live:
        for pdf_path, out_path in eligible:
            extract_pdf(
                pdf_path,
                out_path,
                spinner=spinner,
                live=live,
                overall_progress=overall_progress,
                overall_task=overall_task,
            )

    print(f"\nDone. {len(eligible)} PDFs extracted ({total_pages} pages) to {OUT_DIR}/")


if __name__ == "__main__":
    main()
