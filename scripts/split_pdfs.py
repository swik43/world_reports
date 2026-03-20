"""
Split report PDFs into per-country files.

Reads parsed_contents.json for the given source. Each country's range runs
from its true_page to the next country's true_page - 1 (last country to EOF).

HRW-specific: double-layout PDFs read from unsplit_dir instead of source_dir.
AI-specific:  regional PDFs get output subdirectories like <year>_Africa.

Usage:
    python scripts/split_pdfs.py hrw                # all HRW PDFs
    python scripts/split_pdfs.py ai 2023 2015       # specific AI years
"""

import json
from pathlib import Path

from config import (
    SourceConfig,
    extract_year,
    get_source,
    make_layout,
    make_progress,
    sanitize_filename,
)
from pypdf import PdfReader, PdfWriter
from rich.live import Live
from rich.text import Text


def year_dir_for(pdf_name: str, output_dir: Path) -> Path:
    """Determine the output subdirectory for an AI regional PDF."""
    year = extract_year(pdf_name)
    if "Africa" in pdf_name and "Amnesty" in pdf_name and "Middle" not in pdf_name:
        return output_dir / f"{year}_Africa"
    if "Americas" in pdf_name:
        return output_dir / f"{year}_Americas"
    if "Asia_Pacific" in pdf_name:
        return output_dir / f"{year}_Asia_Pacific"
    if "Eastern_Europe" in pdf_name:
        return output_dir / f"{year}_Eastern_Europe_Central_Asia"
    if "Middle_East" in pdf_name:
        return output_dir / f"{year}_Middle_East_North_Africa"
    return output_dir / year


def get_source_dir(pdf_name: str, cfg: SourceConfig, config: dict) -> Path:
    """Pick the right source directory for a PDF.

    HRW double-layout PDFs read from unsplit_dir; everything else from source_dir.
    """
    if cfg.unsplit_dir and config.get(pdf_name, {}).get("layout") == "double":
        return cfg.unsplit_dir
    return cfg.source_dir


def get_dest_dir(pdf_name: str, cfg: SourceConfig, source_key: str) -> Path:
    """Pick the right output subdirectory for a PDF."""
    if source_key == "ai":
        return year_dir_for(pdf_name, cfg.output_dir)
    return cfg.output_dir / extract_year(pdf_name)


def split_pdf(
    pdf_name,
    countries,
    source_dir,
    dest,
    *,
    spinner,
    live,
    progress,
    overall_task,
):
    dest.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(source_dir / pdf_name))
    total_pages = len(reader.pages)

    for i, country in enumerate(countries):
        spinner.update(text=Text(f"{pdf_name} / {country['name']}", style="gray"))
        live.update(make_layout(spinner, progress))

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
            progress.advance(overall_task)
            continue

        end_idx = min(end_idx, total_pages - 1)

        writer = PdfWriter()
        for page_idx in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[page_idx])

        filename = sanitize_filename(country["name"]) + ".pdf"
        with open(dest / filename, "wb") as f:
            writer.write(f)

        progress.advance(overall_task)


def main():
    cfg, year_filter = get_source()
    source_key = cfg.source_dir.name.lower()  # "hrw" or "ai"

    if not cfg.parsed_path.exists():
        print(f"Error: {cfg.parsed_path} not found.")
        return

    with open(cfg.parsed_path) as f:
        parsed = json.load(f)

    # Load contents_config for HRW double-layout detection
    config: dict = {}
    if cfg.config_path.exists():
        with open(cfg.config_path) as f:
            config = json.load(f)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # Pre-scan: build eligible list and count total countries
    eligible: list[tuple[str, list[dict], Path, Path]] = []
    total_countries = 0

    for pdf_name, countries in sorted(parsed.items()):
        if year_filter:
            year = extract_year(pdf_name)
            if year not in year_filter:
                continue

        if not countries:
            continue

        source_dir = get_source_dir(pdf_name, cfg, config)
        pdf_path = source_dir / pdf_name
        if not pdf_path.exists():
            print(f"WARNING: {pdf_name} not found, skipping")
            continue

        dest = get_dest_dir(pdf_name, cfg, source_key)
        eligible.append((pdf_name, countries, source_dir, dest))
        total_countries += len(countries)

    if not eligible:
        print("No eligible PDFs found.")
        return

    progress, spinner = make_progress()
    overall_task = progress.add_task("Overall", total=total_countries)

    with Live(make_layout(spinner, progress), refresh_per_second=10) as live:
        for pdf_name, countries, source_dir, dest in eligible:
            split_pdf(
                pdf_name,
                countries,
                source_dir,
                dest,
                spinner=spinner,
                live=live,
                progress=progress,
                overall_task=overall_task,
            )

    print(f"\nDone. {total_countries} country files split to {cfg.output_dir}/")


if __name__ == "__main__":
    main()
