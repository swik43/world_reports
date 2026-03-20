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
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf4llm
from config import get_source
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)


def convert_file(pdf_path: str, out_path: str) -> None:
    """Convert a single PDF to Markdown. Runs in a worker process."""
    md_text = pymupdf4llm.to_markdown(pdf_path)
    Path(out_path).write_text(md_text, encoding="utf-8")  # pyright: ignore[reportArgumentType]


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

    # Build work items and per-year file counts
    work_items: list[tuple[str, str, str]] = []  # (pdf_path, out_path, year)
    year_file_counts: dict[str, int] = {}

    for year_dir in year_dirs:
        md_dest = md_dir / year_dir.name
        md_dest.mkdir(parents=True, exist_ok=True)

        pdfs = sorted(year_dir.glob("*.pdf"))
        year_file_counts[year_dir.name] = len(pdfs)

        for pdf_path in pdfs:
            out_path = md_dest / pdf_path.with_suffix(".md").name
            work_items.append((str(pdf_path), str(out_path), year_dir.name))

    total_pdfs = len(work_items)

    if not total_pdfs:
        print("No PDF files found.")
        return

    # One progress bar per year
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )

    year_tasks = {}
    for year_name in sorted(year_file_counts):
        year_tasks[year_name] = progress.add_task(
            year_name, total=year_file_counts[year_name]
        )

    errors: list[str] = []

    with Live(progress, refresh_per_second=10):
        with ProcessPoolExecutor() as pool:
            future_to_year = {}
            for pdf_path, out_path, year_name in work_items:
                future = pool.submit(convert_file, pdf_path, out_path)
                future_to_year[future] = year_name

            for future in as_completed(future_to_year):
                year_name = future_to_year[future]
                try:
                    future.result()
                except Exception as exc:
                    errors.append(f"{year_name}: {exc}")
                progress.advance(year_tasks[year_name])

    if errors:
        print(f"\n{len(errors)} errors:")
        for err in errors:
            print(f"  {err}")

    print(f"\nDone. {total_pdfs - len(errors)} files converted to {md_dir}/")


if __name__ == "__main__":
    main()
