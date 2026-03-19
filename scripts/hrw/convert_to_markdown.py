"""
Convert per-country HRW PDFs to Markdown using pymupdf4llm.

Reads split PDFs from output/hrw/<year>/<Country>.pdf and writes
Markdown files to output/hrw_markdown/<year>/<Country>.md.

Usage:
    python scripts/hrw/convert_to_markdown.py              # all years
    python scripts/hrw/convert_to_markdown.py 2023 2022    # specific years
"""

import re
import sys
from pathlib import Path

import pymupdf4llm
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

PDF_DIR = Path("output/hrw")
MD_DIR = Path("output/hrw_markdown")


def extract_year(dir_name: str) -> int:
    match = re.match(r"(\d{4})", dir_name)
    if match:
        return int(match.group(1))
    return 0


def convert_dir(year_dir: Path, progress: Progress, year_task_id: int) -> None:
    md_dest = MD_DIR / year_dir.name
    md_dest.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(year_dir.glob("*.pdf"))
    file_task = progress.add_task(f"  [cyan]{year_dir.name}", total=len(pdfs))

    for pdf_path in pdfs:
        progress.update(
            file_task, description=f"  [cyan]{year_dir.name}[/] {pdf_path.stem}"
        )
        out_path = md_dest / pdf_path.with_suffix(".md").name
        md_text = pymupdf4llm.to_markdown(str(pdf_path))
        out_path.write_text(md_text, encoding="utf-8")  # pyright: ignore[reportArgumentType]
        progress.advance(file_task)
        progress.advance(year_task_id)  # pyright: ignore[reportArgumentType]

    progress.update(file_task, visible=False)


def main():
    if not PDF_DIR.exists():
        print(f"Error: {PDF_DIR} not found.")
        return

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    year_dirs = sorted(
        d for d in PDF_DIR.iterdir() if d.is_dir() and extract_year(d.name) > 0
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

    MD_DIR.mkdir(parents=True, exist_ok=True)

    total_pdfs = sum(len(list(d.glob("*.pdf"))) for d in year_dirs)

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ) as progress:
        overall = progress.add_task("Overall", total=total_pdfs)
        for year_dir in year_dirs:
            convert_dir(year_dir, progress, overall)

    print(f"\nDone. {total_pdfs} files converted to {MD_DIR}/")


if __name__ == "__main__":
    main()
