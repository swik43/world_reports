"""
Convert double-layout HRW PDFs into single-page-per-sheet PDFs.

For each double-layout PDF (as marked in contents_config.json), this script:
- Keeps page 1 (cover) as-is
- Splits every page from double_start onward into left and right halves
- Writes the result to output/hrw_unsplit/<pdf_name>

This is non-destructive -- original PDFs are never modified.

Usage:
    python scripts/unsplit_double_pages.py [year ...]
"""

import json
from copy import deepcopy

from config import SOURCES, extract_year, make_layout, make_progress
from pypdf import PdfReader, PdfWriter
from rich.live import Live
from rich.text import Text

cfg = SOURCES["hrw"]


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
    pdf_name,
    pdf_cfg,
    *,
    spinner,
    live,
    progress,
    overall_task,
):
    double_start = pdf_cfg["double_start"]  # 1-indexed PDF page where doubles begin
    reader = PdfReader(str(cfg.source_dir / pdf_name))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + 1  # 1-indexed

        spinner.update(text=Text(f"{pdf_name} / page {page_num}", style="gray"))
        live.update(make_layout(spinner, progress))

        if page_num < double_start:
            # Pre-double pages (cover, etc.) -- keep as-is
            writer.add_page(page)
        else:
            left, right = split_page_halves(page)
            writer.add_page(left)
            writer.add_page(right)

        progress.advance(overall_task)

    assert cfg.unsplit_dir is not None
    cfg.unsplit_dir.mkdir(parents=True, exist_ok=True)
    out_path = cfg.unsplit_dir / pdf_name
    with open(out_path, "wb") as f:
        writer.write(f)


def main():
    import sys

    with open(cfg.config_path) as f:
        config = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    # Pre-scan: filter to double-layout PDFs and count total pages
    eligible: list[tuple[str, dict]] = []
    total_pages = 0

    for pdf_name, pdf_cfg in sorted(config.items()):
        if pdf_cfg.get("layout") != "double":
            continue
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue

        pdf_path = cfg.source_dir / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_path} not found, skipping")
            continue

        reader = PdfReader(str(pdf_path))
        total_pages += len(reader.pages)
        eligible.append((pdf_name, pdf_cfg))

    if not eligible:
        print("No eligible double-layout PDFs found.")
        return

    progress, spinner = make_progress()
    overall_task = progress.add_task("Overall", total=total_pages)

    with Live(make_layout(spinner, progress), refresh_per_second=10) as live:
        for pdf_name, pdf_cfg in eligible:
            process_pdf(
                pdf_name,
                pdf_cfg,
                spinner=spinner,
                live=live,
                progress=progress,
                overall_task=overall_task,
            )

    print(
        f"\nDone. {len(eligible)} PDFs processed ({total_pages} pages) to {cfg.unsplit_dir}/"
    )


if __name__ == "__main__":
    main()
