"""
Merge all intermediate JSON files (with report_page) into one final
parsed_contents.json (with true_page).

- Reads AI/contents_config.json for the last_contents_page offset per PDF
- Reads each file in AI_contents_json_intermediate/ and computes:
    true_page = last_contents_page + report_page
- Includes any files in AI_contents_json_final/ as-is (already have true_page)
- Final files override intermediate ones if the same PDF appears in both
- Writes the merged result to AI/parsed_contents.json
"""

import json
from pathlib import Path

INTERMEDIATE_DIR = Path("AI_contents_json_intermediate")
FINAL_DIR = Path("AI_contents_json_final")
CONFIG_PATH = Path("AI/contents_config.json")
OUTPUT_PATH = Path("AI/parsed_contents.json")


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    result = {}

    # Process intermediate files (report_page -> true_page)
    for path in sorted(INTERMEDIATE_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        for pdf_name, countries in data.items():
            if pdf_name not in config:
                print(f"WARNING: {pdf_name} not in contents_config.json, skipping")
                continue

            last_contents_page = max(config[pdf_name]["contents_pages"])

            for country in countries:
                country["true_page"] = last_contents_page + country["report_page"]
                del country["report_page"]

            result[pdf_name] = countries
            print(
                f"{pdf_name}: {len(countries)} countries (offset +{last_contents_page})"
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
