"""
Split Amnesty International PDFs into per-country files.

Reads parsed_contents.json with format:
{
  "2023_Amnesty_International.pdf": [
    { "name": "Afghanistan", "true_page": 23 },
    { "name": "Albania", "true_page": 29 }
  ]
}

Each country's range: from its true_page to the next country's true_page - 1
(last country runs to end of PDF).

Output: output/ai/<year>/<Country_Name>.pdf
"""

import json
import re
import sys
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

AI_DIR = Path("AI")
OUTPUT_DIR = Path("output/ai")
PARSED_PATH = Path("data/ai/parsed_contents.json")


def extract_year(pdf_name: str) -> str:
    match = re.match(r"(\d{4})_", pdf_name)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract year from {pdf_name}")


def sanitize_filename(name: str) -> str:
    name = name.replace("/", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    return name.strip()


def year_dir_for(pdf_name: str) -> Path:
    year = extract_year(pdf_name)
    if "Africa" in pdf_name and "Amnesty" in pdf_name and "Middle" not in pdf_name:
        return OUTPUT_DIR / f"{year}_Africa"
    if "Americas" in pdf_name:
        return OUTPUT_DIR / f"{year}_Americas"
    if "Asia_Pacific" in pdf_name:
        return OUTPUT_DIR / f"{year}_Asia_Pacific"
    if "Eastern_Europe" in pdf_name:
        return OUTPUT_DIR / f"{year}_Eastern_Europe_Central_Asia"
    if "Middle_East" in pdf_name:
        return OUTPUT_DIR / f"{year}_Middle_East_North_Africa"
    return OUTPUT_DIR / year


def split_pdf(
    pdf_name: str,
    countries: list[dict],
    *,
    spinner: Spinner,
    live: Live,
    overall_progress: Progress,
    overall_task,
):
    dest = year_dir_for(pdf_name)
    dest.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(AI_DIR / pdf_name))
    total_pages = len(reader.pages)

    for i, country in enumerate(countries):
        spinner.update(text=Text(f"{pdf_name} / {country['name']}", style="gray"))
        live.update(make_layout(spinner, overall_progress))

        start_page = country["true_page"]  # 1-indexed

        if i + 1 < len(countries):
            end_page = max(start_page, countries[i + 1]["true_page"] - 1)
        else:
            end_page = total_pages

        start_idx = start_page - 1
        end_idx = end_page - 1

        if start_idx < 0 or start_idx >= total_pages:
            live.console.print(
                f"  WARNING: {country['name']} page {start_page} out of range (total: {total_pages})"
            )
            overall_progress.advance(overall_task)
            continue

        end_idx = min(end_idx, total_pages - 1)

        writer = PdfWriter()
        for page_idx in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[page_idx])

        filename = sanitize_filename(country["name"]) + ".pdf"
        with open(dest / filename, "wb") as f:
            writer.write(f)

        overall_progress.advance(overall_task)


def make_layout(spinner, overall_progress):
    return Group(spinner, overall_progress)


def main():
    if not PARSED_PATH.exists():
        print(f"Error: {PARSED_PATH} not found.")
        return

    with open(PARSED_PATH) as f:
        parsed = json.load(f)

    year_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-scan: build eligible list and count total countries
    eligible: list[tuple[str, list[dict]]] = []
    total_countries = 0

    for pdf_name, countries in sorted(parsed.items()):
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue

        if not countries:
            continue

        pdf_path = AI_DIR / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_name} not found, skipping")
            continue

        eligible.append((pdf_name, countries))
        total_countries += len(countries)

    if not eligible:
        print("No eligible PDFs found.")
        return

    overall_progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )
    overall_task = overall_progress.add_task("Overall", total=total_countries)
    spinner = Spinner("dots", text=Text("Starting...", style="cyan"))

    with Live(make_layout(spinner, overall_progress), refresh_per_second=10) as live:
        for pdf_name, countries in eligible:
            split_pdf(
                pdf_name,
                countries,
                spinner=spinner,
                live=live,
                overall_progress=overall_progress,
                overall_task=overall_task,
            )

    print(f"\nDone. {total_countries} country files split to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
