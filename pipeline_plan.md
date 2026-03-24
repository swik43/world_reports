# Pipeline Plan -- From Input to Final Structure

## Overview

This pipeline takes a folder of human rights report PDFs from four
organisations and produces a structured, ID-named, filtered output ready for
LLM classification. It builds on existing scripts that already handle
double-layout conversion, config-driven PDF splitting, and markdown conversion.

The pipeline is a sequence of focused steps. Each step reads from the previous
step's output, produces its own output, and writes a manifest of what it did.
Steps can be re-run individually, scoped by `--org`, `--year`, and `--country`.
Human intervention is required between certain steps (marked below).


## Input Structure

```
input/
  wr/
    ai/
      1999(1998)_Amnesty_International.pdf
      2000(1999)_Amnesty_International.pdf
      ...
      2019(2018)_Africa_Amnesty_International.pdf    # regional
      ...
    hrw/
      2005(2004)_World_Report_Human_Rights_Watch.pdf
      ...
    idmc/
      2004_Global.pdf
      ...
  cr/
    ai/
      Afghanistan/
        2003_Afghanistan.pdf
        2012_Afghanistan.pdf
        ...
      Guinea, Liberia, Sierra Leone/       # multi-country parent + splits
        2001_GuineaLiberiaSierra_Leone.pdf  # source document
        split_files/
          2001_Guinea.pdf                   # classification candidates
          2001_Liberia.pdf
          2001_Sierra_Leone.pdf
      ...
    hrw/
      Angola/
        2002_Angola.pdf
      ...
    idmc/
      Afghanistan/
        2006_Afghanistan_a.pdf
        2021_Afghanistan_IDMC_Profile.md
        ...
      Regional Reports/                     # nested subdirectories
        Africa/
          2006_Africa.pdf                   # source document
          split_files/
            2006_West_Africa_Cote_dIvoire.pdf
            2006_West_Africa_Guinea.pdf
            ...
        Eastern_Africa/
          2016_Eastern_Africa.pdf           # source document
          split_files/
            2016_Eastern_Africa_Djibouti.pdf
            ...
        Middle_East/
          2011_Middle_East.pdf              # no splits, goes to _general
      ...
    us/
      Afghanistan/
        1999_Afghanistan.pdf
        2000_Afghanistan.pdf
        ...
      Algeria/
        1999_Algeria.md        # md where no PDF exists
        ...
```

Notes:
- WR files are full annual reports (one PDF = many countries) or pre-split
  per-country files, depending on the year/org.
- CR files are standalone per-country reports, already in country folders.
- The `YYYY(YYYY-1)` format in filenames indicates publication year and
  coverage year. Not all files use this -- some are just `YYYY`. Both are valid.

### CR scanning rules

The CR tree is not a uniform depth. Some orgs have nested subdirectories
(e.g. `Regional Reports/Africa/split_files/`). Two rules handle this:

**Rule 1: Recursive scanning.** The CR scanner walks the tree recursively
under each `input/cr/{org}/` and collects all leaf files regardless of depth.
The entity/country name is derived from the filename (via the standardisation
map), not from the folder path. The folder path only determines the org.

**Rule 2: The `split_files/` convention.** Anywhere in the CR tree, if a
directory contains a `split_files/` subfolder:
- Files **inside** `split_files/` are classification candidates -- they get
  routed through name standardisation and into `samples_readable/`.
- Files **next to** `split_files/` (at the parent level) are source/parent
  documents -- they go to `sources/`.

If no `split_files/` subfolder exists, all files in the directory are
classification candidates (the normal case).

Files whose entity doesn't match any known country (e.g. `2011_Middle_East.pdf`,
`2006_Africa.pdf` without a split) get routed to `_general/` automatically
by the existing non-country routing logic.


## File ID Scheme

Every classification candidate gets a unique ID used as its filename:

```
{ORG}-{TYPE}-{YEAR}-{ENTITY}[-{SUFFIX}].{ext}
```

| Component | Values | Rules |
|-----------|--------|-------|
| ORG | `AI`, `HRW`, `IDMC`, `US` | Uppercase |
| TYPE | `WR`, `CR`, `CP`, `SR` | See type definitions below |
| YEAR | `1999`...`2023`, or `YYYY(YYYY-1)` | Publication year, optionally with coverage year in parentheses |
| ENTITY | Standardised name | Spaces replaced with `_` in filename; folder names keep spaces |
| SUFFIX | `-a`, `-b`, `-c`... | Only when multiple files share the same ORG-TYPE-YEAR-ENTITY |

**Type definitions:**

| Type | Meaning | Where they come from |
|------|---------|---------------------|
| `WR` | Per-country chapter split from an annual World Report | Split from WR PDFs by the pipeline, or pre-split at source |
| `CR` | Standalone country report | `input/cr/{ai,hrw,idmc}/` -- independently published |
| `CP` | IDMC Country Profile | `input/cr/idmc/` -- files matching `*_IDMC_Profile.md` |
| `SR` | U.S. State Dept annual country report | `input/cr/us/` |

**ID examples:**
- `AI-WR-1999(1998)-Afghanistan` -- AI World Report published 1999, covers 1998
- `HRW-CR-2003-Iraq` -- standalone HRW country report
- `IDMC-CP-2021-India` -- IDMC Country Profile
- `US-SR-2005-Sudan` -- US State Dept report
- `AI-CR-2016-Afghanistan-a` -- first of multiple AI country reports on Afghanistan in 2016

**Year parsing rule:** `(\d{4})(?:\((\d{4})\))?` extracts publication year
and optional coverage year.


## Final Output Structure

Three output locations plus an index file:

### samples_readable/

Human-readable format: PDF, HTML, or MD (whichever is the highest-fidelity
version available). Path structure:

```
samples_readable/{org}/{type}/{country_folder}/{ID}.{ext}
```

Where:
- `{org}` is lowercase: `ai`, `hrw`, `idmc`, `us`
- `{type}` is lowercase: `wr`, `cr`, `cp`, `sr`
- `{country_folder}` keeps original casing and spaces (e.g. `Bosnia and Herzegovina`)
- `{ID}` uses underscores for spaces in the entity portion

Example paths:
```
samples_readable/
  ai/
    wr/
      Afghanistan/
        AI-WR-1999(1998)-Afghanistan.pdf
        AI-WR-2014(2013)-Afghanistan.pdf
        ...
      Serbia/                              # shared country folder
        AI-WR-1999(1998)-Yugoslavia_(Federal_Republic_of).pdf
        AI-WR-2010(2009)-Serbia.pdf
      Israel and Palestine/                # shared country folder
        AI-WR-1999(1998)-Israel_and_the_Occupied_Territories.pdf
        AI-WR-2020(2019)-Israel_-_OPT.pdf
      _general/                            # non-country entities
        (regional or thematic reports that can't be assigned to one country)
    cr/
      Afghanistan/
        AI-CR-2003-Afghanistan.pdf
        AI-CR-2016-Afghanistan-a.pdf
        AI-CR-2016-Afghanistan-b.pdf
        ...
  hrw/
    wr/
      Afghanistan/
        HRW-WR-2000(1999)-Afghanistan.html   # HTML is the source of truth for some years
        HRW-WR-2005(2004)-Afghanistan.pdf
        ...
      Russia/
        HRW-WR-2004(2003)-Russia_Chechnya.pdf  # sub-national, filed under Russia
        ...
      _general/
        HRW-WR-2004(2003)-Balkans.pdf
    cr/
      Iraq/
        HRW-CR-2003-Iraq.pdf
        ...
  idmc/
    wr/
      Afghanistan/
        IDMC-WR-2008-Afghanistan.pdf
        ...
      _general/
        IDMC-WR-2004-Africa.pdf
        IDMC-WR-2017-Lake_Chad_Basin.pdf
        ...
    cr/
      Afghanistan/
        IDMC-CR-2006-Afghanistan-a.pdf
        ...
    cp/
      Afghanistan/
        IDMC-CP-2021-Afghanistan.md
        IDMC-CP-2022-Afghanistan.md
        IDMC-CP-2023-Afghanistan.md
      ...
  us/
    sr/
      Afghanistan/
        US-SR-1999-Afghanistan.pdf
        ...
      Algeria/
        US-SR-1999-Algeria.md              # .md where no PDF exists
        ...
```

### samples_llm/

Exact structural mirror of `samples_readable/`. Contains the lowest-resolution
version of each file for LLM consumption. This is usually `.md` but for files
that can't be converted to markdown (e.g. scanned AI pre-2013 PDFs), the
original format (PDF, HTML) is kept. Every file in `samples_readable/` has a
corresponding entry in `samples_llm/`.

```
samples_llm/{org}/{type}/{country_folder}/{ID}.{ext}
```

### sources/

Original/parent reports from which WR splits were extracted. Kept for
provenance. Organised by org. Filenames are preserved from the input
(not renamed to IDs).

```
sources/
  ai/
    world_reports/
      1999(1998)_Amnesty_International.pdf
      ...
      2019(2018)_Africa_Amnesty_International.pdf
      ...
    country_reports/
      2001_Guinea_Liberia_Sierra_Leone.pdf    # multi-country parent
  hrw/
    world_reports/
      2000(1999)_split_files/                 # pre-split = source is the folder
        Albania.html
        ...
      2005(2004)_World_Report_Human_Rights_Watch.pdf
      ...
  idmc/
    world_reports/
      2004_Global.pdf
      ...
      2023_GRID.pdf
    regional_reports/
      2006_Africa.pdf
      2017_Eastern_Africa.pdf
```

### index.json

Master registry at the project root. Every classification candidate gets an
entry. Schema:

```json
{
  "meta": {
    "version": "3.0",
    "generated": "<ISO timestamp>",
    "filter": "conflict_years_first_relevant.csv",
    "total_files": 0,
    "total_sources": 0
  },
  "files": [
    {
      "id": "IDMC-WR-2010-Sudan",
      "org": "IDMC",
      "type": "WR",
      "year": 2010,
      "entity": "Sudan",
      "country_folder": "Sudan",
      "suffix": null,
      "readable_path": "samples_readable/idmc/wr/Sudan/IDMC-WR-2010-Sudan.pdf",
      "llm_path": "samples_llm/idmc/wr/Sudan/IDMC-WR-2010-Sudan.md",
      "readable_format": "pdf",
      "llm_format": "md",
      "source_id": "IDMC-SRC-WR-2010",
      "source_type": "split_from_world_report",
      "archive_path": "archive/WR_split_pdf/idmc/2010/2010_Sudan.pdf",
      "original_filename": "2010_Sudan.pdf",
      "spreadsheet_metadata": null
    }
  ],
  "sources": [
    {
      "source_id": "IDMC-SRC-WR-2010",
      "org": "IDMC",
      "year": 2010,
      "path": "sources/idmc/world_reports/2010_Global.pdf",
      "description": "IDMC Global Overview 2010"
    }
  ]
}
```

**Source type values:**
- `split_from_world_report` -- extracted from a full annual report
- `split_from_regional_report` -- extracted from a regional section
- `downloaded_pre_split` -- found already split online (source = sample)
- `standalone` -- independently published (country reports, US State Dept, IDMC profiles)

**Source ID format:** `{ORG}-SRC-WR-{YEAR}` for world reports.


## Country Name Standardisation

A JSON file (`country_name_standardisation.json`) provides three lookup tables:

**`variant_to_standard`** (95 entries): Maps any known spelling variant to the
standardised entity name. Example: `"Phillipines"` -> `"Philippines"`,
`"Russian Federation"` -> `"Russia"`, `"Côte d'Ivoire"` -> `"Cote_D'Ivoire"`.
If a name is not in this dict, it's already standard -- use as-is.

**`entity_to_folder`** (18 entries): Maps standardised entities to shared
country folders where multiple entities coexist. Example:
- `"Israel_-_OPT"` -> `"Israel and Palestine"`
- `"Yugoslavia_(Federal_Republic_of)"` -> `"Serbia"`
- `"China_and_Tibet"` -> `"China"`

If an entity is not in this dict, its folder is the entity name with
underscores replaced by spaces.

**`csv_to_folder`** (12 entries): Maps names from
`conflict_years_first_relevant.csv` to folder names where they differ.
Example: `"DR Congo (Zaire)"` -> `"DRC"`, `"Ivory Coast"` -> `"Cote D'Ivoire"`.

Non-country entities (regional reports, thematic reports like "Displacement",
"Lake Chad Basin", "Sub-Saharan Africa", etc.) are routed to a `_general/`
folder under the relevant `{org}/{type}/`.


## Country/Year Filter

`conflict_years_first_relevant.csv` defines 84 countries and a start year for
each. Only files whose country_folder matches a row in the CSV and whose year
>= that country's `First_Relevant_Year` are included in `samples_*`.

Special inclusion rules:
- `_general/` files are always included (they span multiple countries)
- Sub-national entities filed under an included country are included:
  `Yugoslavia_(Kosovo)` under Serbia, `Russia_Chechnya` under Russia,
  `Occupied_Palestinian_Territories_(OPT)` under Israel and Palestine


## Pipeline Steps

### Step 0: Validate Input
**Script:** `validate_input.py`
**Reads:** `input/`
**Writes:** `manifests/0_input_inventory.json`
**Human intervention:** None

Walks the input tree and produces an inventory of every file with:
- path, org, type (wr/cr), filename, extension, detected year, detected country
  (for CR files only -- WR files are multi-country at this point)

Checks:
- All WR source PDFs listed in configs actually exist in input
- No unexpected files or structures
- Reports any anomalies

The CR tree may contain nested subdirectories and `split_files/` folders --
these are expected patterns (see "CR scanning rules" above), not anomalies.
The validator should flag them as informational, not warnings.

This is a sanity check, not a transformation step.


### Step 1: Convert Double-Layout PDFs (WR only)
**Script:** `unsplit_double_pages.py` (existing, unchanged)
**Reads:** `input/wr/{org}/`, `data/{org}/1_unsplit_config.json`
**Writes:** `intermediate/unsplit/{org}/`
**Human intervention:** None (config must be pre-populated)

Takes double-layout WR PDFs (two printed pages per PDF page) and produces
single-page-per-sheet versions. Only processes files listed in the unsplit
config. Original files are not modified.

**Already implemented.** The existing script works as-is. The only change
needed is to read from `input/wr/{org}/` instead of `HRW/` etc., which means
updating the source_dir in `config.py`.


### Step 2: Extract Contents Page Images (WR only)
**Script:** `extract_contents_images.py` (existing, unchanged)
**Reads:** `input/wr/{org}/`, `data/{org}/*_contents_config.json`
**Writes:** `data/{org}/contents_images/`
**Human intervention:** None (config must be pre-populated)

Renders the table-of-contents pages from each WR PDF as PNG images, which
are then fed to Claude for country/page extraction.

**Already implemented.**


### --- HUMAN INTERVENTION POINT ---

The operator takes the contents page images to Claude, gets back structured
JSON with country names and page numbers, and saves them in
`data/{org}/contents_json/`. Or uses the override mechanism to provide
country data directly.

This is inherently manual and cannot be automated within the pipeline.


### Step 3: Build Split Config (WR only)
**Script:** `build_final_config.py` (existing, unchanged)
**Reads:** `data/{org}/contents_json/`, `data/{org}/*_overrides.json`,
           `data/{org}/*_contents_config.json`
**Writes:** `data/{org}/*_split_config.json`
**Human intervention:** Operator should review the output config before proceeding

Merges Claude's extracted data with offsets to produce the final split config:
which pages to extract for which country from which PDF.

**Already implemented.**


### --- HUMAN INTERVENTION POINT ---

Operator reviews the split config, spot-checks a few page numbers against
the actual PDFs.


### Step 4: Split WR PDFs
**Script:** `split_pdfs.py` (existing, minor modifications)
**Reads:** `input/wr/{org}/` or `intermediate/unsplit/{org}/`,
           `data/{org}/*_split_config.json`
**Writes:** `intermediate/split_wr/{org}/{year}/{Country}.pdf`
**Writes manifest:** `manifests/4_split_wr.json`
**Human intervention:** None

Splits each WR PDF into per-country files based on the split config.

**Already implemented.** Modifications needed:
- Write output to `intermediate/split_wr/` instead of `output/`
- Produce a manifest listing every file created:
  `{org, year, country_raw, input_path, output_path}`

Pre-split WR files (scenario 2 and 4) are handled here too: the split
config can list them as "already split, just copy" by setting
`"pre_split": true` on the entry. The script copies them into the same
intermediate structure without re-splitting.


### Step 5: Standardise Country Names
**Script:** `standardise_names.py` (new)
**Reads:** `intermediate/split_wr/`, `input/cr/`, `country_name_standardisation.json`
**Writes:** `intermediate/standardised/` (same structure, renamed files)
**Writes manifest:** `manifests/5_standardised.json`
**Writes:** `unknown_countries.txt` (if any names can't be resolved)
**Human intervention:** Only if unknown countries are found

For every file produced by step 4 (WR) and every file in `input/cr/` (CR):

1. Extract the raw country name from the filename
2. Look it up in `variant_to_standard` from the standardisation map
3. If found: use the standardised name
4. If not found and it's a recognisable country (exact match in known list): use as-is
5. If not found at all: log to `unknown_countries.txt`, skip the file

Also determines the `country_folder` via `entity_to_folder` (for multi-entity
folders like "Israel and Palestine", "Serbia", "China", etc.).

Non-country entities (regional reports, thematic reports) are routed to
`_general/` instead of a country folder.

**CR scanning follows the two rules from the "CR scanning rules" section above:**
- Scan recursively under `input/cr/{org}/` -- don't assume fixed folder depth.
- If a `split_files/` subfolder exists, only process files inside it as
  classification candidates. Files next to it (at the parent level) are source
  documents and should be routed to `sources/` in step 8. The manifest should
  record `"is_source": true` for these parent files so step 8 knows where to
  put them.

Output structure:
```
intermediate/standardised/
  wr/
    {org}/
      {year}/
        {Standardised_Country}.pdf
        ...
      {year}/
        _general/
          Africa.pdf
          ...
  cr/
    {org}/
      {Standardised_Country}/
        {year}_{Standardised_Country}[_suffix].{ext}
        ...
```

The manifest records for each file:
`{org, type, year, country_raw, country_standardised, country_folder, input_path, output_path, is_source}`


### Step 6: Filter by Country and Year
**Script:** `filter_files.py` (new)
**Reads:** `intermediate/standardised/`, `conflict_years_first_relevant.csv`,
           `csv_to_folder` mapping from standardisation JSON
**Writes:** `intermediate/filtered/` (same structure, subset of files)
**Writes:** `intermediate/discarded/` or `discarded.txt`
**Writes manifest:** `manifests/6_filtered.json`
**Human intervention:** None

Copies files from `intermediate/standardised/` to `intermediate/filtered/` only
if:
1. The country_folder matches a row in the CSV (after applying `csv_to_folder` mapping)
2. The year >= `First_Relevant_Year` for that country

Special cases built into the filter:
- Files under `Serbia/` with entity `Yugoslavia_(Kosovo)` are included if Serbia is in the CSV
- Files under `Israel and Palestine/` with entity `Occupied_Palestinian_Territories_(OPT)` are included if Israel is in the CSV
- Files under `Russia/` with entity `Russia_Chechnya` are included if Russia is in the CSV
- `_general/` files are always included (they span multiple countries)

Everything else goes to `discarded.txt` (list of paths not copied).


### Step 7: Convert to Markdown
**Script:** `convert_to_markdown.py` (existing, extended)
**Reads:** `intermediate/filtered/`
**Writes:** `intermediate/markdown/` (mirror structure)
**Writes manifest:** `manifests/7_converted.json`
**Human intervention:** None

Every file in `intermediate/filtered/` must end up in `intermediate/markdown/`.
The goal is to produce the lowest-resolution version of each file for LLM
consumption. Usually that's markdown, but when conversion isn't possible
the original file is copied as-is.

For each file in `intermediate/filtered/`:
- If it's a PDF and conversion is possible: convert to markdown using pymupdf4llm
- If it's a PDF but below `min_markdown_year` (scanned docs): copy the PDF as-is
- If it's already `.md`: copy as-is
- If it's `.html`: convert to markdown (simple html-to-md conversion)
- If conversion fails: copy the original file as-is, log error in manifest

The `samples_llm/` folder (produced by step 8) will contain whatever format
ended up in `intermediate/markdown/` -- usually `.md` but sometimes `.pdf`
or `.html` for files that couldn't be converted.

**The existing script handles PDF-to-markdown conversion.** It needs to be
extended to:
- Process CR files (currently only handles WR year directories)
- Handle HTML files
- Handle unconvertible PDFs by copying them through
- Process from `intermediate/filtered/` instead of `output/`
- Support `--org`, `--type`, `--year`, `--country` scoping flags
- Respect the per-org `min_markdown_year` setting (AI pre-2013 = copy, not convert)
- Write a manifest


### Step 8: Assign IDs and Organise
**Script:** `organise.py` (new)
**Reads:** `intermediate/filtered/`, `intermediate/markdown/`, `input/wr/` (for source files)
**Writes:** `samples_readable/`, `samples_llm/`, `sources/`
**Writes manifest:** `manifests/8_organised.json`
**Human intervention:** None

This is the final assembly step. For each file in `intermediate/filtered/`:

1. Generate the file ID: `{ORG}-{TYPE}-{YEAR}-{ENTITY}[-{SUFFIX}]`
   - Detect TYPE: `WR` for files from split_wr, `CR` for standalone country
     reports, `CP` for IDMC Profile files, `SR` for US State Dept
   - Year format: `YYYY(YYYY-1)` if both years are known, else just `YYYY`
   - Handle suffix collisions: sort alphabetically, assign `-a`, `-b`, etc.

2. Copy to `samples_readable/{org}/{type}/{country_folder}/{ID}.{ext}`

3. Copy the corresponding file from `intermediate/markdown/` to
   `samples_llm/{org}/{type}/{country_folder}/{ID}.{ext}`
   The extension matches whatever step 7 produced: `.md` for converted files,
   or the original extension (`.pdf`, `.html`) for unconvertible files.

4. Copy WR source PDFs from `input/wr/` to `sources/{org}/world_reports/`
   (keep original filenames)

5. Copy CR parent/source files to `sources/{org}/country_reports/` or
   `sources/{org}/regional_reports/`. These are identified by the
   `"is_source": true` flag in the step 5 manifest -- they are the files
   that sat next to a `split_files/` subfolder in the input tree.

The manifest records: `{id, org, type, year, entity, country_folder, suffix,
readable_path, llm_path, source_path, source_id, original_filename}`


### Step 9: Generate Index
**Script:** `generate_index.py` (new)
**Reads:** all manifests from `manifests/`, `2_IDP.numbers` (or exported CSV),
           `country_name_standardisation.json`
**Writes:** `index.json`
**Human intervention:** None

Assembles the master index from the chain of manifests. For each file in
`manifests/8_organised.json`:

1. Build the index entry with all fields from the index.json schema defined above
2. Match against the IDP spreadsheet by (original_filename, org) to pull in
   `spreadsheet_metadata` (date, title, link)
3. Set `source_type` based on provenance:
   - came from split_wr + has source PDF = `split_from_world_report`
   - came from split_wr + pre-split = `downloaded_pre_split`
   - came from cr = `standalone`
4. Set `archive_path` to the file's location in the input tree (since the
   input folder is what gets archived)
5. Populate the `sources` array from the WR source files in `sources/`

Also produces the updated IDP spreadsheet with `ID` and `New Path` columns.


## Configuration Files

The pipeline uses multiple focused config files rather than one monolith.
This is because human intervention is required between certain steps, and
some configs can only be created after earlier steps have run.

### Pre-existing (per org, in `data/{org}/`):

| File | Step | Purpose | Created by |
|------|------|---------|------------|
| `1_unsplit_config.json` | 1 | Which PDFs are double-layout, where doubles start | Human (manual) |
| `*_contents_config.json` | 2,3 | Which pages are the table of contents, page offset | Human (manual) |
| `contents_json/*.json` | 3 | Country names + page numbers from Claude | Human (Claude-assisted) |
| `*_overrides.json` | 3 | Manual country data bypassing Claude | Human (manual) |
| `*_split_config.json` | 4 | Final merged config: country + true_page + source_path | `build_final_config.py` |

### New (at project root):

| File | Step | Purpose |
|------|------|---------|
| `country_name_standardisation.json` | 5 | Maps variant names to standard names and folders |
| `conflict_years_first_relevant.csv` | 6 | Which countries and start years to include |


## Scoping Flags

Every script supports these flags for targeted re-runs:

```
--org ai|hrw|idmc|us       # process only this organisation
--year 2010 2015           # process only these years
--country Sudan Iraq       # process only these countries (steps 5+ only)
--dry-run                  # preview without writing files
```

When re-running a step, it checks the manifest from the previous step to
determine which files need processing, and skips files that already have
valid output (unless `--force` is passed).


## Manifest Format

Each step writes a JSON manifest to `manifests/`:

```json
{
  "step": 4,
  "name": "split_wr",
  "timestamp": "2026-03-24T14:30:00Z",
  "scoped_to": {"org": "hrw", "year": ["2010"]},
  "files": [
    {
      "input_path": "input/wr/hrw/2010(2009)_World_Report_Human_Rights_Watch.pdf",
      "output_path": "intermediate/split_wr/hrw/2010(2009)/Afghanistan.pdf",
      "org": "hrw",
      "year": "2010(2009)",
      "country_raw": "Afghanistan",
      "status": "ok"
    }
  ],
  "summary": {
    "total": 85,
    "ok": 85,
    "skipped": 0,
    "error": 0
  }
}
```

Manifests are append-friendly: re-running a step with a narrow scope merges
the new results into the existing manifest rather than overwriting it.


## Error Handling

**Unknown country names (step 5):** Written to `unknown_countries.txt` with
their full path. The rest of the pipeline continues. Fix the standardisation
map and re-run step 5 with `--country` scoping to process just the fixed ones.

**Markdown conversion failures (step 7):** Logged in the manifest with
`"status": "error"`. The file is still available in `samples_readable/` as a
PDF. Re-run step 7 scoped to the failed files after fixing the issue.

**Suffix collisions (step 8):** If multiple files map to the same ID, suffixes
are assigned deterministically (alphabetical sort of original filenames). This
is logged in the manifest so it can be audited.

**Missing source PDFs:** Logged as warnings. The split can't proceed for that
year/org, but other years continue normally.


## Year Format

Years appear in two formats: `YYYY` and `YYYY(YYYY-1)`.

The parenthetical indicates the coverage year (what the report discusses) vs
the publication year. For example, `2010(2009)` means "published 2010,
covers events from 2009."

In the file ID, the year component uses whichever format the source file uses.
Parsing rule: `(\d{4})(?:\((\d{4})\))?` extracts both years.

The `add_covered_year.py` script (existing) can be used to annotate files that
are missing the coverage year.


## What Exists vs What's New

| Script | Status | Changes Needed |
|--------|--------|----------------|
| `unsplit_double_pages.py` | Exists | Update source paths to read from `input/` |
| `extract_contents_images.py` | Exists | Update source paths |
| `build_final_config.py` | Exists | Update source paths |
| `split_pdfs.py` | Exists | Update paths, add manifest output, handle pre-split passthrough |
| `convert_to_markdown.py` | Exists | Extend to handle CR files, HTML, new paths, scoping flags, manifest |
| `add_covered_year.py` | Exists | No changes needed |
| `offset_years.py` | Exists | No changes needed |
| `config.py` | Exists | Update paths, possibly add new source configs |
| `validate_input.py` | New | |
| `standardise_names.py` | New | |
| `filter_files.py` | New | |
| `organise.py` | New | |
| `generate_index.py` | New | |


## Intermediate Directory Structure

```
intermediate/
  unsplit/              # step 1: double-layout PDFs made single-page
    hrw/
    idmc/
  split_wr/             # step 4: per-country PDFs from WR splitting
    ai/
      1999(1998)/
        Afghanistan.pdf
        ...
    hrw/
    idmc/
  standardised/         # step 5: renamed with standardised country names
    wr/
      ai/
        1999(1998)/
          Afghanistan.pdf
          ...
    cr/
      ai/
        Afghanistan/
          2003_Afghanistan.pdf
          ...
  filtered/             # step 6: only countries/years we care about
    (same structure as standardised, minus excluded files)
  markdown/             # step 7: markdown conversions
    (mirrors filtered/ structure, all .md)
```

The intermediate directory can be deleted once the final output is validated.
The manifests in `manifests/` provide a complete audit trail.


## Running the Full Pipeline

```bash
# One-time setup
uv venv && source .venv/bin/activate && uv sync

# Step 0: Validate
python scripts/validate_input.py

# Step 1: Double-layout conversion (HRW and IDMC only, where needed)
python scripts/unsplit_double_pages.py hrw
python scripts/unsplit_double_pages.py idmc

# Step 2: Extract contents images
python scripts/extract_contents_images.py hrw
python scripts/extract_contents_images.py ai
python scripts/extract_contents_images.py idmc

# --- HUMAN: feed images to Claude, save JSON responses ---

# Step 3: Build split configs
python scripts/build_final_config.py hrw
python scripts/build_final_config.py ai
python scripts/build_final_config.py idmc

# --- HUMAN: review split configs ---

# Step 4: Split WR PDFs
python scripts/split_pdfs.py hrw
python scripts/split_pdfs.py ai
python scripts/split_pdfs.py idmc

# Step 5: Standardise country names
python scripts/standardise_names.py --org ai --org hrw --org idmc --org us

# Step 6: Filter by country/year
python scripts/filter_files.py

# Step 7: Convert to markdown
python scripts/convert_to_markdown.py --org ai --org hrw --org idmc --org us

# Step 8: Organise into final structure
python scripts/organise.py

# Step 9: Generate index
python scripts/generate_index.py
```

For re-runs after fixing issues:
```bash
# Fix a few unknown country names, re-run only those
python scripts/standardise_names.py --country "New Country Name"

# Re-convert a specific failed file
python scripts/convert_to_markdown.py --org idmc --year 2010 --country Sudan

# Rebuild just the index after manual corrections
python scripts/generate_index.py
```
