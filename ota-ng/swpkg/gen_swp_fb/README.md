# Introduction 

## Development tool for generating signed UCM binary packages.

`gen_swp_fb.py` is a python tool that generates a binary package signed with RSA2048 algorithm.

```
Requirements:

To run this tool, you need:

- Python3 and required packages
- update-manifest-data.json file
- update-manifest-schema.fbs
- corresponding artefact files

Installation:

To run this tool on Windows/Linux:

1) Install required python packages

```
    python -m pip install -r requirements.txt
```

Usage:

To use this tool on Windows/Linux/Mac:

1. Open a terminal or command prompt window in the root directory of this project.
2. Run the following command:

    python gen_swp_fb.py    --container-format <CFV>
                            --update-manifest-data <update-manifest-data.json>
                            --update-manifest-schema <update-manifest-schema.fbs>
                            --artefact
                                ./<artefact_1> compressWhole
                            --artefact
                                ./<artefact_2> compressChunks
                            --artefact
                                ./<artefact_3> compressChunks
                            --artefact
                                ./<artefact_4> compressChunks
                            --compress zlib
                            --key-store ./key-store
                            --block-size 64536
                            --verification on
                            --verbose
                            --flatc-path ./flatbuffers/flatc
                            --estimated-speed 1024
                            --output ./_bin

    python gen_swp_fb.py  --configfile my_swp.json
    
Arguments:
    Options:
        The gen_swp_fb.py tool has two configuration options. First is using comand line arguemnts for each value:

        - --container-format: Container format version (ex: 0x0102, 0x0104, 0x0106)
        - --update-manifest-data.json: The path to the manifest data file (ex: manifest.json)
        - --update-manifest-schema.fbs: The path to the manifest schema file (ex: manifest.fbs)
        - --artefact: The path to one or more artefact files (ex: artefact_0.tar, artefact_1.tar, artefact_2.tar), 'compressWhole' or 'compressChunks' refers to compression type, respectivly whole file compression or by chunks.
        - --compress: The compression algorithm. Defaults to 'None'
        - --key-store: Path to the key store (.der file). Defaults to tool repository
        - --block-size: The whole block size (with header). Changed by the tool to a limit of 60K (ex: if --block-size 70000 =>  Input max size exceeds limit. Changed to 60000)
        - --verification: Write verification On/Off
        - --verbose: Verbose flag
        - --flatc-path: PAth the flat buffer compiler. Used to generate flatbuffer of update-manifest-data. Defaults to tool repository
        - --estimated-speed: Corresponds to estimated rate of processing the artefacts from UCMS side (KB/s)
        - --output ./_bin. Defaults to tool repository

        Second options is to use a cfgFile.json:

        - --configfile: Path to argument file. If given, any other argument is not taken into consideration.

Examples:

1. Single artefact:
python gen_swp_fb.py --container-format 0x0106 --update-manifest-data swp__test_swp_flatcfg.json --update-manifest-schema swc_flatcfg.fbs --artefact artefact_1 compressWhole --compress zlib --key-store keys/ --block-size 5000 --verification On --flatc-path ./flatbuffers/flatc --estimated-speed 1024

2. Multiple artefacts:
python gen_swp_fb.py --container-format 0x0106 --update-manifest-data swp__test_swp_flatcfg.json --update-manifest-schema swc_flatcfg.fbs --artefact artefact_1 compressWhole --artefact artefact_2 compressWhole --artefact artefact_3 compressWhole --artefact artefact_4 compressWhole --artefact artefact_5 compressWhole --compress zlib --key-store keys/ --block-size 5000 --verification On --flatc-path ./flatbuffers/flatc --estimated-speed 1024


Output:

The output binary package will be generated in the same directory with the name swpkg.bin.
```
