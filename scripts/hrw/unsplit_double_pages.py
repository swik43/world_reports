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


def process_pdf(
    pdf_name: str,
    cfg: dict,
    *,
    spinner: Spinner,
    live: Live,
    overall_progress: Progress,
    overall_task,
):
    double_start = cfg["double_start"]  # 1-indexed PDF page where doubles begin
    reader = PdfReader(str(HRW_DIR / pdf_name))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + 1  # 1-indexed

        spinner.update(text=Text(f"{pdf_name} / page {page_num}", style="gray"))
        live.update(make_layout(spinner, overall_progress))

        if page_num < double_start:
            # Pre-double pages (cover, etc.) — keep as-is
            writer.add_page(page)
        else:
            left, right = split_page_halves(page)
            writer.add_page(left)
            writer.add_page(right)

        overall_progress.advance(overall_task)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / pdf_name
    with open(out_path, "wb") as f:
        writer.write(f)


def make_layout(spinner, overall_progress):
    return Group(spinner, overall_progress)


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    # Pre-scan: filter to double-layout PDFs and count total pages
    eligible: list[tuple[str, dict]] = []
    total_pages = 0

    for pdf_name, cfg in sorted(config.items()):
        if cfg.get("layout") != "double":
            continue
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue

        pdf_path = HRW_DIR / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_path} not found, skipping")
            continue

        reader = PdfReader(str(pdf_path))
        total_pages += len(reader.pages)
        eligible.append((pdf_name, cfg))

    if not eligible:
        print("No eligible double-layout PDFs found.")
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
        for pdf_name, cfg in eligible:
            process_pdf(
                pdf_name,
                cfg,
                spinner=spinner,
                live=live,
                overall_progress=overall_progress,
                overall_task=overall_task,
            )

    print(f"\nDone. {len(eligible)} PDFs processed ({total_pages} pages) to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
