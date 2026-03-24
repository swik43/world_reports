## The general story

Our current pipeline is still a little fragmented. I want to be able to give people access to the repo and then a zip of all the PDFs and then they can then run a bunch of scripts and get out the final structure that I will use for my classification.

The input folder would be structured like:
```
input
├── cr
│   ├── ai
│   │   └── <country>
│   │       └── <year>.something
│   ├── hrw
│   ├── idmc
│   └── us
└── wr
    ├── ai
    │   └── <year>.something
    ├── hrw
    └── idmc
```

And the output, well we'll get to it. For now it can be similar, just changing the filename to be the full document ID (more on that in a moment):
```
output
├── cr
│   ├── ai
│   │   └── <country>
│   │       └── <id>.something
│   ├── hrw
│   ├── idmc
│   └── us
└── wr
    ├── ai
    │   └── <year>
    │       └── <id>.something
    ├── hrw
    └── idmc
```

The difference is that in `input/wr` we have a lot of files in each of those directories that contain information about individual countries. One of the things this pipeline will do is break down those multi-country reports into individual country reports.

The reason this is a little bit difficult is that the reports change shape, layout, size, names, formats, a whole bunch of times throughout the years. So I want us to use a declarative, config-driven approach to, well, configuring our pipeline.

The current pipeline already does this (though it expects the inputs in a slightly different format), but it does not cover everything. I will try and list all the possible scenarios that we need to support and then we can think through the best way to structure and breakdown our configuration files.

### World Reports
The pipeline so far has only really been designed with the world reports in mind, because the country reports don't really need to be cut up or anything.

#### scenario 1
`input`: there's a world report document for year `yyyy` which is just a single PDF which contains information about multiple countries
`output`: under the same type (wr | cr), org (ai | idmc | hrw), there would be a folder labelled `yyyy` with a bunch of individual country PDFs extracted from that original PDF.

#### scenario 2
`input`: there's a folder labelled `yyyy` under some `<type>/<org>` which contains a bunch of individual country PDFs (so they were already split by country at the source).
`output`: they are essentially copied over as is under the same `<type>/<org>/<yyyy>` structure.

#### scenario 3
`input`: the same as scenario 1, except the PDF pages are double layout (one PDF page = 2 report pages), this could start from the very first page or it could start at some page `p`
`output`: this should be the same as the output in scenario 1, which means we first need to format that PDF into a single page layout. There's already a script and way to handle this in the pipeline, just letting you know.

#### scenario 4
`input`: like scenario 2, but instead of PDFs we have HTML files.
`output`: like scenario 2, just copy them over.

### Country Reports

But the country reports do need _some_ work as well. Ultimately what we want to do with these files is use an LLM to classify them, so what we're trying to do with this is break the documents into their smallest unit for classification (org-type-country-year) and then convert them to as low-res of a file as we can. We are aiming for markdown, but some older documents can't realiably be converted into markdown so in those cases we will just use whatever the lowest res we can achieve (which happens to be PDF).

#### scenario 5

`input`: a country folder full of PDFs, named `<yyyy>_<country>.pdf`
`output`: a country folder full of PDFs, named `<id>.pdf` (again we'll get to the ID in a sec)

#### scenario 6

`input`: a country folder full of PDFs, named `<yyyy>_<country>.md`
`output`: a country folder full of PDFs, named `<id>.md` (this is highest res we got, so we just preserve it forward)

I don't want the pipeline to try and guess what scenario is taking place or how to handle a particular folder or year from the input. That's the point of the configuration files. Everything should be transparent. We should be able to list which files are pre-split and just need to be carried forward, which files are double layout and need to be made into single layout, etc.


### The ID

The id of a file is made up of 5 parts.
```
{org}-{type}-{year}-{country}-{suffix (optional)}
```
everything should be self explanatory and should also be pretty clear from the input data structure. The only thing that's not clear is the suffix. Sometimes there might be multiple entries for an `org + type + year + country`, and in those cases we add a suffix to keep them distinct starting with `_a` and going down the alphabet.

The other thing that's not really clear is that the year isn't just a 4 digit number. There are two formats:

1. `YYYY`
2. `YYYY (YYYY-1)`

Some reports were published in year YYYY, but they discuss events that happened in the previous year. We want to preserve that information in the filenames, so our pipeline scripts will need to know how to handle both formats for a year.


### Country filenames

Another big one is that sometimes the same country may appear under slightly different names. We need a way to consolidate and standardise country names. For that we already set up a big hashmap that collapses ambiguous counttry names into pre-selected labels / groups. There are a couple of odd cases which I will explain in a moment, but the map is obviously not bullet proof and it's very possible that some names might slip through the cracks. We don't want them going unnoticed. If a name is found that we cannot deal with we need to know about it so we can update the map. I haven't yet decided how to handle this, we can either write their path to a file and ignore them while the rest of the pipeline runs, then go back and fix the map and re-run the pipeline. Or we can eject from the pipeline to fix the map and then re-run. Or maybe there's some third option.

Some files won't be of countries but of some other entity or region or something, those should just be grouped under a `_general` folder both in the `cr` and the `wr` output folders, in the latter that means that they would be nested under the `year` folder and then again under `_general` where the rest of the countries would live flat under `year`.

### Final filtering

Once the step in the pipeline that transforms the files is done, but before the renaming step we should filter and keep the countries and years that we care about. That information can be found in `conflict_years_first_relevant.csv`, it maps countries to the first year we care about. Anything outside that should be moved to a `discared` folder at the top level (potentially retaining its structure from the `input` folder, or they can be listed in a `discared.txt` file and just not copied over to the final destination.)

There are again a couple special cases:
- Kosovo (which would be grouped under Serbia)
- OPT or Palestine (which would be grouped under Israel)
- Chechnya (which would be grouped under Russia)
should not be excluded (maybe that means we should just add them to the filtering CSV, provided the map file would clearly group them under the correct country)
