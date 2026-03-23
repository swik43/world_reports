#!/usr/bin/env python3
"""
Extract country-specific pages from IDMC World Reports (2008-2014) as separate PDFs.
Saves them to Reports/Country Reports/IDMC Reports/{Country}/{year}_{Country}_WR.pdf

Page maps are hardcoded from manual font-size scans.
Format: (start_1based, end_1based, country_or_countries)
  - country_or_countries is a string (single) or list (shared page)
"""

import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

THESIS_DIR = Path("/Users/samwikander/Documents/Thesis")
WORLD_REPORTS_DIR = THESIS_DIR / "Reports/World Reports/World Reports IDMC"
COUNTRY_REPORTS_DIR = THESIS_DIR / "Reports/Country Reports/IDMC Reports"


# ---------------------------------------------------------------------------
# Hardcoded page maps.  (start, end, country-or-[countries]) — 1-based pages
# Only countries that have an existing IDMC Reports folder are listed.
# ---------------------------------------------------------------------------

PAGE_MAPS = {
    # 2008_Global.pdf  (93 pages)
    ("2008_Global.pdf", 2008): [
        (38, 38, "CAR"),
        (39, 39, "Chad"),
        # p40 = Côte d'Ivoire — folder name "Cote D'ivoire"
        (40, 40, "Cote D'ivoire"),
        (41, 41, "DRC"),
        (42, 42, "Ethiopia"),
        (43, 43, "Kenya"),
        (44, 44, "Nigeria"),
        (45, 45, "Somalia"),
        (46, 47, "Sudan"),
        (48, 48, "Uganda"),
        # p49 = Zimbabwe — no folder, skip
        # p50 = Rwanda + Burundi (shared page)
        (50, 50, ["Rwanda", "Burundi"]),
        # p51 = Algeria + Eritrea
        (51, 51, ["Algeria", "Eritrea"]),
        # p52 = Senegal + Liberia
        (52, 52, ["Senegal", "Liberia"]),
        # p53 = Republic of Congo + Angola (runs to p57 before Asia section header)
        (53, 54, ["Republic of the Congo", "Angola"]),
        (58, 58, "Afghanistan"),
        (59, 59, "Bangladesh"),
        (60, 60, "India"),
        (61, 61, "Indonesia"),
        (62, 62, "Myanmar"),
        (63, 63, "Nepal"),
        (64, 64, "Pakistan"),
        (65, 65, "Philippines"),
        (66, 66, "Sri Lanka"),
        # p67-70 = Timor-Leste — no folder, skip
        (71, 71, "Azerbaijan"),
        (72, 72, "Bosnia and Herzegovina"),
        (73, 73, "Georgia"),
        (74, 74, "Russia"),
        (75, 75, "Turkey"),
        (76, 76, "Serbia"),
        # p77 = Croatia + Macedonia
        (77, 77, ["Croatia", "Macedonia"]),
        # p78 = Armenia + Cyprus — no folders, skip
        # p79 = Turkmenistan + Uzbekistan; Uzbekistan has folder
        (79, 79, "Uzbekistan"),
        (83, 83, "Iraq"),
        # p84 = Occupied Palestinian Territory → Israel folder
        (84, 84, ("Israel", "Israel_OPT")),
        (85, 85, "Lebanon"),
        (86, 86, "Yemen"),
        # p87 = Israel + Syria (shared page)
        (87, 87, ["Israel", "Syria"]),
        (90, 90, "Peru"),
        (91, 91, "Colombia"),
        # p92 = Mexico + Guatemala
        (92, 93, ["Mexico", "Guatemala"]),
    ],

    # 2009_Global.pdf  (87 pages)
    ("2009_Global.pdf", 2009): [
        (33, 33, "CAR"),
        (34, 34, "Chad"),
        # p35 = Côte d'Ivoire
        (35, 35, "Cote D'ivoire"),
        (36, 36, "DRC"),
        (37, 37, "Ethiopia"),
        (38, 38, "Kenya"),
        (39, 39, "Nigeria"),
        (40, 40, "Somalia"),
        (41, 42, "Sudan"),
        (43, 43, "Uganda"),
        # p44 = Zimbabwe — skip
        # p45 = Burundi + Algeria
        (45, 45, ["Burundi", "Algeria"]),
        # p46 = Eritrea + Niger
        (46, 46, ["Eritrea", "Niger"]),
        # p47 = Senegal + Liberia (runs to p49)
        (47, 47, ["Senegal", "Liberia"]),
        (50, 50, "Peru"),
        (51, 51, "Colombia"),
        # p52 = Mexico + Guatemala (runs to p55)
        (52, 52, ["Mexico", "Guatemala"]),
        (56, 56, "Azerbaijan"),
        (57, 57, "Bosnia and Herzegovina"),
        # p58 = Cyprus — skip
        (59, 59, "Georgia"),
        (60, 60, "Russia"),
        (61, 61, "Turkey"),
        (62, 62, "Croatia"),
        # p63 = Serbia + Kosovo; Kosovo no folder
        (63, 63, "Serbia"),
        (67, 67, "Iraq"),
        (68, 68, "Lebanon"),
        # p69 = Occupied Palestinian Territory → Israel
        (69, 69, ("Israel", "Israel_OPT")),
        (70, 70, "Yemen"),
        # p71 = Israel + Syria (shared page)
        (71, 71, ["Israel", "Syria"]),
        (76, 76, "Afghanistan"),
        (77, 77, "Bangladesh"),
        (78, 78, "India"),
        (79, 79, "Indonesia"),
        (80, 80, "Myanmar"),
        (81, 81, "Nepal"),
        (82, 82, "Pakistan"),
        (83, 83, "Philippines"),
        (84, 84, "Sri Lanka"),
        # p85 = Timor-Leste — skip
    ],

    # 2010_Global.pdf  (98 pages)
    ("2010_Global.pdf", 2010): [
        (40, 40, "Algeria"),
        (41, 41, "Burundi"),
        (42, 42, "CAR"),
        (43, 43, "Chad"),
        # p44 = Côte d'Ivoire
        (44, 44, "Cote D'ivoire"),
        (45, 45, "DRC"),
        (46, 46, "Eritrea"),
        (47, 47, "Ethiopia"),
        (48, 48, "Kenya"),
        # p49 = Liberia + Niger
        (49, 49, ["Liberia", "Niger"]),
        (50, 50, "Nigeria"),
        (51, 51, "Senegal"),
        (52, 52, "Somalia"),
        (53, 54, "Sudan"),
        (55, 55, "Uganda"),
        # p56 = Zimbabwe — skip
        # p61 = Azerbaijan + Armenia; Armenia no folder
        (61, 61, "Azerbaijan"),
        (62, 62, "Bosnia and Herzegovina"),
        # p63 = Croatia + Cyprus; Cyprus no folder
        (63, 63, "Croatia"),
        (64, 64, "Georgia"),
        # p65 = Kosovo + Kyrgyzstan — no folders, skip
        (66, 66, "Russia"),
        (67, 67, "Serbia"),
        (68, 68, "Turkey"),
        (72, 72, "Colombia"),
        # p73 = Guatemala + Mexico
        (73, 73, ["Guatemala", "Mexico"]),
        (74, 74, "Peru"),
        (78, 78, "Iraq"),
        (79, 79, "Lebanon"),
        # p80 = Occupied Palestinian Territory → Israel
        (80, 80, ("Israel", "Israel_OPT")),
        (81, 81, "Syria"),
        (82, 82, "Yemen"),
        (87, 87, "Afghanistan"),
        # p88 = Bangladesh + India
        (88, 88, ["Bangladesh", "India"]),
        (89, 89, "Indonesia"),
        # p90 = Lao PDR — skip
        (91, 91, "Myanmar"),
        # p92 = Nepal + Pakistan
        (92, 92, ["Nepal", "Pakistan"]),
        (93, 93, "Philippines"),
        (94, 94, "Sri Lanka"),
        # p95 = Timor-Leste — skip
    ],

    # 2011_Conflict and violence.pdf  (95 pages)
    ("2011_Conflict and violence.pdf", 2011): [
        (41, 41, "Burundi"),
        (42, 42, "CAR"),
        (43, 43, "Chad"),
        # p44 = Côte d'Ivoire
        (44, 44, "Cote D'ivoire"),
        (45, 45, "DRC"),
        (46, 46, "Ethiopia"),
        (47, 47, "Kenya"),
        # p48 = Liberia + Niger
        (48, 48, ["Liberia", "Niger"]),
        (49, 49, "Nigeria"),
        # p50 = Senegal + Somalia
        (50, 50, ["Senegal", "Somalia"]),
        (51, 51, "South Sudan"),
        (52, 52, "Sudan"),
        (53, 53, "Uganda"),
        # p54 = Zimbabwe — skip
        (58, 58, "Colombia"),
        # p59 = Guatemala + Mexico
        (59, 59, ["Guatemala", "Mexico"]),
        (60, 60, "Peru"),
        # p64 = Armenia — no folder, skip
        (65, 65, "Azerbaijan"),
        # p66 = Cyprus + Bosnia and Herzegovina
        (66, 66, "Bosnia and Herzegovina"),
        (67, 67, "Georgia"),
        # p68 = Kosovo + Kyrgyzstan — skip
        (69, 69, "Russia"),
        (70, 70, "Serbia"),
        (71, 71, "Turkey"),
        (75, 75, "Iraq"),
        (76, 76, "Lebanon"),
        # p77 = Libya — no folder, skip
        # p78 = Occupied Palestinian Territory → Israel
        (78, 78, ("Israel", "Israel_OPT")),
        (79, 79, "Syria"),
        (80, 80, "Yemen"),
        (85, 85, "Afghanistan"),
        # p86 = Bangladesh + India
        (86, 86, ["Bangladesh", "India"]),
        (87, 87, "Indonesia"),
        (88, 88, "Myanmar"),
        (89, 89, "Nepal"),
        (90, 90, "Pakistan"),
        (91, 91, "Philippines"),
        (92, 92, "Sri Lanka"),
        (93, 93, "Thailand"),
        # p93 also has Timor-Leste — skip, only Thailand has folder
    ],

    # 2012_Global.pdf  (74 pages)
    ("2012_Global.pdf", 2012): [
        # p20 = Burundi + CAR
        (20, 20, ["Burundi", "CAR"]),
        (21, 21, "Chad"),
        # p22 = Côte d'Ivoire
        (22, 22, "Cote D'ivoire"),
        (23, 23, "DRC"),
        (24, 24, "Ethiopia"),
        (25, 25, "Kenya"),
        # p26 = Liberia + Mali
        (26, 26, ["Liberia", "Mali"]),
        (27, 27, "Nigeria"),
        (28, 28, "Senegal"),
        (29, 29, "Somalia"),
        (30, 30, "South Sudan"),
        (31, 31, "Sudan"),
        # p32 = Zimbabwe + Uganda
        (32, 32, "Uganda"),
        (38, 38, "Colombia"),
        (39, 39, "Mexico"),
        (40, 40, "Peru"),
        (45, 45, "Azerbaijan"),
        # p46 = Bosnia and Herzegovina + Georgia
        (46, 46, ["Bosnia and Herzegovina", "Georgia"]),
        # p47 = Kosovo — no folder, skip
        # p48 = Kyrgyzstan — no folder, skip
        (49, 49, "Russia"),
        (50, 50, "Serbia"),
        (51, 51, "Turkey"),
        (56, 56, "Iraq"),
        # p57 = Lebanon + Libya; Libya no folder
        (57, 57, "Lebanon"),
        # p58 = Occupied Palestinian Territory → Israel
        (58, 58, ("Israel", "Israel_OPT")),
        (59, 59, "Syria"),
        (60, 60, "Yemen"),
        (65, 65, "Afghanistan"),
        # p66 = Bangladesh + India
        (66, 66, ["Bangladesh", "India"]),
        (67, 67, "Indonesia"),
        (68, 68, "Myanmar"),
        (69, 69, "Nepal"),
        (70, 70, "Pakistan"),
        (71, 71, "Philippines"),
        (72, 72, "Sri Lanka"),
        (73, 73, "Thailand"),
    ],

    # 2014_Conflict and Violence.pdf  (78 pages)
    ("2014_Conflict and Violence.pdf", 2014): [
        # p24 = Burundi + CAR
        (24, 24, ["Burundi", "CAR"]),
        (25, 25, "Chad"),
        # p26 = Côte d'Ivoire
        (26, 26, "Cote D'ivoire"),
        (27, 27, "DRC"),
        # p28 = Kenya + Ethiopia
        (28, 28, ["Kenya", "Ethiopia"]),
        (29, 29, "Liberia"),
        (30, 30, "Mali"),
        (31, 31, "Nigeria"),
        (32, 32, "Senegal"),
        (33, 33, "Somalia"),
        (34, 34, "South Sudan"),
        (35, 35, "Sudan"),
        # p36 = Uganda + Zimbabwe; Zimbabwe no folder
        (36, 36, "Uganda"),
        (41, 41, "Colombia"),
        # p42 = Honduras — no folder, skip
        (43, 43, "Mexico"),
        (44, 44, "Peru"),
        (49, 49, "Azerbaijan"),
        (50, 50, "Bosnia and Herzegovina"),
        (51, 51, "Georgia"),
        # p52 = Kosovo — no folder, skip
        (53, 53, "Russia"),
        (54, 54, "Serbia"),
        (55, 55, "Turkey"),
        (60, 60, "Iraq"),
        # p61 = Lebanon + Libya; Libya no folder
        (61, 61, "Lebanon"),
        # p62 = Palestine → Israel
        (62, 62, ("Israel", "Israel_OPT")),
        (63, 63, "Syria"),
        (64, 64, "Yemen"),
        (69, 69, "Afghanistan"),
        # p70 = Bangladesh + India
        (70, 70, ["Bangladesh", "India"]),
        (71, 71, "Indonesia"),
        (72, 72, "Myanmar"),
        (73, 73, "Nepal"),
        (74, 74, "Pakistan"),
        (75, 75, "Philippines"),
        (76, 76, "Sri Lanka"),
        (77, 77, "Thailand"),
    ],
}


def output_filename(year: int, folder_name: str, file_stem: str = None) -> Path:
    """
    Return output path like IDMC Reports/{folder}/{year}_{stem}_WR.pdf.
    file_stem defaults to folder_name. Adds _b, _c etc. if the base name already exists.
    """
    stem = file_stem or folder_name
    folder_path = COUNTRY_REPORTS_DIR / folder_name
    base = f"{year}_{stem}_WR.pdf"
    out = folder_path / base
    if not out.exists():
        return out
    for letter in "bcdefghij":
        alt = folder_path / f"{year}_{stem}_WR_{letter}.pdf"
        if not alt.exists():
            return alt
    return folder_path / f"{year}_{stem}_WR_z.pdf"


def extract_pages(pdf_path: Path, start_1: int, end_1: int) -> PdfWriter:
    """Extract pages start..end (1-based inclusive) using pypdf."""
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for i in range(start_1 - 1, end_1):
        writer.add_page(reader.pages[i])
    return writer


def process_report(
    fname: str, year: int, entries: list, dry_run: bool = False, data_year: int = None
) -> int:
    pdf_path = WORLD_REPORTS_DIR / fname
    if not pdf_path.exists():
        print(f"  MISSING: {pdf_path}", flush=True)
        return 0

    # data_year is the year used in output filenames (may differ from source report year)
    file_year = data_year if data_year is not None else year

    print(f"\n{'='*60}", flush=True)
    print(f"Processing: {fname}  (year={year}, data_year={file_year})", flush=True)
    print(f"{'='*60}", flush=True)

    extracted = 0
    skipped = []

    for start, end, countries in entries:
        page_str = f"p{start}" if start == end else f"p{start}-{end}"

        # Normalise to list of (folder_name, file_stem) pairs.
        # tuple  → single entry with custom stem: ("Folder", "stem")
        # str    → single entry, stem defaults to folder name
        # list   → multiple countries on same page, each stem = folder name
        if isinstance(countries, tuple):
            items = [(countries[0], countries[1])]
        elif isinstance(countries, str):
            items = [(countries, None)]
        else:
            items = [(c, None) for c in countries]

        for folder_name, file_stem in items:
            folder_path = COUNTRY_REPORTS_DIR / folder_name
            if not folder_path.exists():
                skipped.append(f"{folder_name} ({page_str})")
                continue

            out_path = output_filename(file_year, folder_name, file_stem)
            print(f"  [{page_str}] {folder_name} → {out_path.name}", flush=True)

            if not dry_run:
                writer = extract_pages(pdf_path, start, end)
                with open(out_path, "wb") as f:
                    writer.write(f)

            extracted += 1

    print(f"\n  Extracted: {extracted}", flush=True)
    if skipped:
        print(f"  Skipped (no folder / not listed): {', '.join(skipped)}", flush=True)

    return extracted


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract country pages from IDMC World Reports"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview only, don't write files"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no files will be written\n", flush=True)

    # Reports where the source year differs from the data year it covers.
    # e.g. "Global Overview 2014" covers 2013 displacement data.
    DATA_YEAR_OVERRIDES = {
        2014: 2013,
    }

    total = 0
    for (fname, year), entries in PAGE_MAPS.items():
        data_year = DATA_YEAR_OVERRIDES.get(year)
        total += process_report(fname, year, entries, dry_run=args.dry_run, data_year=data_year)

    print(f"\n{'='*60}", flush=True)
    print(
        f"Total files {'previewed' if args.dry_run else 'extracted'}: {total}",
        flush=True,
    )


if __name__ == "__main__":
    main()
