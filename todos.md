# todo

- should be able to list files as only needing to be copied over (AI <=2007, HRW <=2003)
    - some files won't get converted
    - some files are pre-split and can just move

- half the scripts only work with a single year prefix or they don't carry forward the double yeare prefix
    - double year prefix should be respected in both filenames and folders

- actually just use the IDs from now for the filenames

- pipeline right now is fragmented. It does not produce the final outcome that will be sued for coding. Need a script for that

- need a big map of all country names so that we can group any non-country entity under `_general`
- country names should ideally be standardised (we already told Claude about these decisions and where special cases should be grouped under somewhere)
- countries and years that are irrelevant do not need to be converted, but the pdfs should be but in a discarded folder
- It is based on conflict-years (Kosovo (shoudl be included under Serbia), OPT or Palestine (under Israel), Checnya (under Russia) are special cases) and should not be excluded 
- It's very important that countries are not arbitrarily excluded based on naming

- We want readable and LLM - mirrors 
- The final naming convention is 

ORG-TYPE (all are WR for world report)-YEAR(REPORT_YEAR)-COUNTRY.SUFFIX

- Need to somehow merge with the country-specific
- Need to get some type of master spreadsheet
- All split files need to have their own unique ID name and be mapped to source document

---

- each step just dumps its files in a folder inside intermediate. Those folders should have the step name prefixed like the manifest files do

- the standardise_names script does not show progress

- the filter_files script also doe not show progress