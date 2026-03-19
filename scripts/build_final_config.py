"""
Merge all intermediate JSON files (with report_page) into one final
parsed_contents.json (with true_page).

- Reads AI/offsets.csv for the true offset per PDF (true_page - report_page)
- Falls back to max(contents_pages) from contents_config.json if no offset found
- Reads each file in AI_contents_json_intermediate/ and computes:
    true_page = offset + report_page
- Includes any files in AI_contents_json_final/ as-is (already have true_page)
- Final files override intermediate ones if the same PDF appears in both
- Writes the merged result to AI/parsed_contents.json
"""

import csv
import json
from pathlib import Path

INTERMEDIATE_DIR = Path("AI_contents_json_intermediate")
FINAL_DIR = Path("AI_contents_json_final")
CONFIG_PATH = Path("AI/contents_pages.json")
OFFSETS_PATH = Path("AI/offsets.csv")
OUTPUT_PATH = Path("AI/parsed_contents.json")


def load_offsets() -> dict[str, int]:
    """Load offsets from CSV. Returns {file_prefix: offset}."""
    offsets = {}
    with open(OFFSETS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            prefix = row["file"].strip()
            report_page = int(row["report_page"])
            true_page = int(row["true_page"])
            offsets[prefix] = true_page - report_page
    return offsets


def find_offset(pdf_name: str, offsets: dict[str, int]) -> int | None:
    """Match a PDF filename to its offset using the CSV prefix."""
    # e.g. "2004_Amnesty_International.pdf" should match prefix "2004"
    # e.g. "2019_Africa_Amnesty_International.pdf" should match "2019_Africa"
    stem = pdf_name.replace("_Amnesty_International.pdf", "")
    # Try exact match first, then progressively shorter prefixes
    for prefix, offset in offsets.items():
        if stem == prefix or stem.startswith(prefix):
            return offset
    return None


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    offsets = load_offsets()

    result = {}

    # Process intermediate files (report_page -> true_page)
    for path in sorted(INTERMEDIATE_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        for pdf_name, countries in data.items():
            if pdf_name not in config:
                print(f"WARNING: {pdf_name} not in contents_config.json, skipping")
                continue

            offset = find_offset(pdf_name, offsets)
            if offset is not None:
                source = "offsets.csv"
            else:
                offset = max(config[pdf_name]["contents_pages"])
                source = "contents_config (fallback)"
                print(f"  WARNING: no offset in CSV, using {source}")

            for country in countries:
                country["true_page"] = offset + country["report_page"]
                del country["report_page"]

            result[pdf_name] = countries
            print(
                f"{pdf_name}: {len(countries)} countries (offset {offset:+d}, {source})"
            )

    # Include/override with any hand-converted final files (already have true_page)
    if FINAL_DIR.exists():
        for path in sorted(FINAL_DIR.glob("*.json")):
            with open(path) as f:
                data = json.load(f)

            for pdf_name, info in data.items():
                # Support both list and {"countries": [...]} wrapper formats
                countries = (
                    info.get("countries", info) if isinstance(info, dict) else info
                )
                clean = [
                    {"name": c["name"], "true_page": c["true_page"]} for c in countries
                ]
                overridden = " (override)" if pdf_name in result else ""
                result[pdf_name] = clean
                print(f"{pdf_name}: {len(clean)} countries (from final/){overridden}")

    # Sort by PDF name
    result = dict(sorted(result.items()))

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = sum(len(v) for v in result.values())
    print(f"\nWrote {OUTPUT_PATH} ({len(result)} PDFs, {total} total country entries)")


if __name__ == "__main__":
    main()
