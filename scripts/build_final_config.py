"""
Build parsed_contents.json from Claude's output JSONs.

Reads each JSON in the source's contents_json/ directory (name + report_page
from Claude), applies the offset from contents_config.json to compute true_page,
normalizes country names to title case, and writes parsed_contents.json.

Files with offset=null in the config must provide true_page
directly in their JSON instead of report_page.

Usage:
    python scripts/build_final_config.py hrw
    python scripts/build_final_config.py ai
"""

import json

from config import get_source, titlecase_name


def main():
    cfg, _ = get_source()

    with open(cfg.config_path) as f:
        config = json.load(f)

    result = {}

    for path in sorted(cfg.contents_json_dir.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        for pdf_name, entries in data.items():
            # Support both list and {"countries": [...]} wrapper
            countries = (
                entries.get("countries", entries)
                if isinstance(entries, dict)
                else entries
            )

            pdf_cfg = config.get(pdf_name)
            if pdf_cfg is None:
                print(f"WARNING: {pdf_name} not in contents_config.json, skipping")
                continue

            offset = pdf_cfg.get("offset")

            # For double-layout PDFs, unsplit_double_pages.py has already
            # split each double page into two single pages, so we compute
            # the equivalent offset for the unsplit PDF.
            if pdf_cfg.get("layout") == "double":
                offset = 2 * pdf_cfg["report_page_1"] - pdf_cfg["double_start"]

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

    with open(cfg.parsed_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = sum(len(v) for v in result.values())
    print(
        f"\nWrote {cfg.parsed_path} ({len(result)} PDFs, {total} total country entries)"
    )


if __name__ == "__main__":
    main()
