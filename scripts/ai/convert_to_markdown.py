"""
Convert per-country PDFs to Markdown using pymupdf4llm.

Reads split PDFs from output/ai/<year>/<Country>.pdf and writes
Markdown files to output/ai_markdown/<year>/<Country>.md.

Only processes post-2012 reports where the layout is single-column
and pymupdf4llm produces clean output.

Usage:
    python scripts/ai/convert_to_markdown.py              # all eligible years
    python scripts/ai/convert_to_markdown.py 2023 2022    # specific years
"""

import re
import sys
from pathlib import Path

import pymupdf4llm
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

PDF_DIR = Path("output/ai")
MD_DIR = Path("output/ai_markdown")

MIN_YEAR = 2013


def extract_year(dir_name: str) -> int:
    match = re.match(r"(\d{4})", dir_name)
    if match:
        return int(match.group(1))
    return 0


def main():
    if not PDF_DIR.exists():
        print(f"Error: {PDF_DIR} not found.")
        return

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    year_dirs = sorted(
        d for d in PDF_DIR.iterdir() if d.is_dir() and extract_year(d.name) >= MIN_YEAR
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

    overall_progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )
    overall_task = overall_progress.add_task("Overall", total=total_pdfs)

    spinner = Spinner("dots", text=Text("Starting...", style="cyan"))

    def make_layout():
        return Group(spinner, overall_progress)

    with Live(make_layout(), refresh_per_second=10) as live:
        for year_dir in year_dirs:
            md_dest = MD_DIR / year_dir.name
            md_dest.mkdir(parents=True, exist_ok=True)

            pdfs = sorted(year_dir.glob("*.pdf"))

            for pdf_path in pdfs:
                spinner.update(
                    text=Text(f"{year_dir.name} / {pdf_path.stem}", style="gray")
                )
                live.update(make_layout())

                out_path = md_dest / pdf_path.with_suffix(".md").name
                md_text = pymupdf4llm.to_markdown(str(pdf_path))
                out_path.write_text(md_text, encoding="utf-8")  # pyright: ignore[reportArgumentType]

                overall_progress.advance(overall_task)

    print(f"\nDone. {total_pdfs} files converted to {MD_DIR}/")


if __name__ == "__main__":
    main()
