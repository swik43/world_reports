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

HRW_DIR = Path("HRW")
CONFIG_PATH = Path("data/hrw/contents_config.json")
OUTPUT_DIR = Path("data/hrw/contents_images")

SCALE = 3  # render at 3x for readability


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-scan: build eligible list and count total pages
    eligible: list[tuple[str, dict]] = []
    total_pages = 0

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

        eligible.append((pdf_name, info))
        total_pages += len(contents_pages)

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

    def make_layout():
        return Group(spinner, overall_progress)

    with Live(make_layout(), refresh_per_second=10) as live:
        for pdf_name, info in eligible:
            contents_pages = info["contents_pages"]
            stem = pdf_name.replace(".pdf", "")
            out_dir = OUTPUT_DIR / stem
            out_dir.mkdir(parents=True, exist_ok=True)

            pdf = pdfium.PdfDocument(str(HRW_DIR / pdf_name))
            for page_num in contents_pages:
                spinner.update(text=Text(f"{pdf_name} / page {page_num}", style="gray"))
                live.update(make_layout())

                page = pdf[page_num - 1]  # 0-indexed
                bitmap = page.render(scale=SCALE)
                image = bitmap.to_pil()
                out_path = out_dir / f"page_{page_num}.png"
                image.save(str(out_path))

                overall_progress.advance(overall_task)

            pdf.close()

    print(f"\nDone. {total_pages} pages extracted to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
