"""
Convert per-country PDFs to Markdown using pymupdf4llm.

Reads split PDFs from the source's output directory and writes
Markdown files to the source's markdown directory.

AI reports are filtered to min_markdown_year (2013+) where the
single-column layout produces clean output.

Usage:
    python scripts/convert_to_markdown.py hrw              # all HRW years
    python scripts/convert_to_markdown.py ai 2023 2022     # specific AI years
"""

import re

import pymupdf4llm
from config import get_source, make_layout, make_progress
from rich.live import Live
from rich.text import Text


def extract_year_int(dir_name: str) -> int:
    match = re.match(r"(\d{4})", dir_name)
    return int(match.group(1)) if match else 0


def main():
    cfg, year_filter = get_source()

    pdf_dir = cfg.output_dir
    md_dir = cfg.markdown_dir
    min_year = cfg.min_markdown_year or 0

    if not pdf_dir.exists():
        print(f"Error: {pdf_dir} not found.")
        return

    year_dirs = sorted(
        d
        for d in pdf_dir.iterdir()
        if d.is_dir() and extract_year_int(d.name) >= min_year
    )

    if year_filter:
        year_dirs = [
            d
            for d in year_dirs
            if re.match(r"(\d{4})", d.name).group(1) in year_filter  # pyright: ignore[reportOptionalMemberAccess]
        ]

    if not year_dirs:
        print("No matching year directories found.")
        return

    md_dir.mkdir(parents=True, exist_ok=True)

    total_pdfs = sum(len(list(d.glob("*.pdf"))) for d in year_dirs)

    progress, spinner = make_progress()
    overall_task = progress.add_task("Overall", total=total_pdfs)

    with Live(make_layout(spinner, progress), refresh_per_second=10) as live:
        for year_dir in year_dirs:
            md_dest = md_dir / year_dir.name
            md_dest.mkdir(parents=True, exist_ok=True)

            pdfs = sorted(year_dir.glob("*.pdf"))

            for pdf_path in pdfs:
                spinner.update(
                    text=Text(f"{year_dir.name} / {pdf_path.stem}", style="gray")
                )
                live.update(make_layout(spinner, progress))

                out_path = md_dest / pdf_path.with_suffix(".md").name
                md_text = pymupdf4llm.to_markdown(str(pdf_path))
                out_path.write_text(md_text, encoding="utf-8")  # pyright: ignore[reportArgumentType]

                progress.advance(overall_task)

    print(f"\nDone. {total_pdfs} files converted to {md_dir}/")


if __name__ == "__main__":
    main()
