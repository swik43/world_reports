"""
Build parsed_contents.json from Claude's output JSONs.

Reads each JSON in data/ai/contents_json/ (name + report_page from Claude),
applies the offset from data/ai/contents_config.json to compute true_page,
normalizes country names to title case, and writes data/ai/parsed_contents.json.

Files with offset=null in the config (e.g. 2006) must provide true_page
directly in their JSON instead of report_page.

Usage:
    python scripts/ai/build_final_config.py
"""

import json
from pathlib import Path

IMAGE_DIR = Path("data/ai/contents_json")
CONFIG_PATH = Path("data/ai/contents_config.json")
OUTPUT_PATH = Path("data/ai/parsed_contents.json")


def titlecase_name(name: str) -> str:
    """Normalize country name to title case."""
    if not name.isupper():
        return name
    result = name.title()
    for word in ["And", "Of", "The"]:
        result = result.replace(f" {word} ", f" {word.lower()} ")
    result = result.replace("D'", "d'")
    return result


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    result = {}

    for path in sorted(IMAGE_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        for pdf_name, entries in data.items():
            # Support both list and {"countries": [...]} wrapper
            countries = (
                entries.get("countries", entries)
                if isinstance(entries, dict)
                else entries
            )

            cfg = config.get(pdf_name)
            if cfg is None:
                print(f"WARNING: {pdf_name} not in contents_config.json, skipping")
                continue

            offset = cfg.get("offset")

            processed = []
            for country in countries:
                name = titlecase_name(country["name"])

                if "true_page" in country:
                    true_page = country["true_page"]
                elif offset is not None:
                    true_page = offset + country["report_page"]
                else:
                    print(
                        f"  ERROR: {pdf_name}/{name} has no true_page and offset is null"
                    )
                    continue

                processed.append({"name": name, "true_page": true_page})

            result[pdf_name] = processed
            offset_str = (
                f"offset {offset:+d}" if offset is not None else "true_page direct"
            )
            print(f"{pdf_name}: {len(processed)} countries ({offset_str})")

    result = dict(sorted(result.items()))

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = sum(len(v) for v in result.values())
    print(f"\nWrote {OUTPUT_PATH} ({len(result)} PDFs, {total} total country entries)")


if __name__ == "__main__":
    main()
