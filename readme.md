# mMassX

[![GitHub Release](https://img.shields.io/github/release/science-open/mmassx.svg?style=flat)](https://github.com/SCIENCE-OPEN/mmassx/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-3.0.en.html)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20about-anything-1abc9c.svg)](https://github.com/asus-linux-drivers/asus-numberpad-driver/issues/new/choose)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
![Badge](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2Fscience-open%2Fmmassx&label=Visitors&icon=suit-heart-fill&color=%23e35d6a)

This work continues [gyellen fork](https://github.com/gyellen/mMass), which is based on [xxao original v5.5.0](https://github.com/xxao/mMass).

## Changelog

[changelog.md](changelog.md)

## Requirements

- (Windows) download .exe from the [releases](https://github.com/SCIENCE-OPEN/mmassx/releases) page

or 

- conda (recommended)

or

- python 3.9.19
- numPy 1.20.3
- wxPython 4.1.1
- wxwidgets 3.1.5
- pandas 1.3.4
- (optional, precomputing/using ions cache) joblib 1.5.0
- (optional, linux only) distro 1.9.0
- (dev, generating .exe) pyinstaller 6.9.0
- (dev, processing KEGG database) httpx 0.28.1

## Installation

- (Windows) download .exe from the [releases](https://github.com/SCIENCE-OPEN/mmassx/releases) page

or 
- create new virtual environment or activate virtual environment from file `environment.yml`

```
# new

$ conda create --prefix ./.mmass_env
$ conda activate ./.mmass_env
$ (.mmass_env) conda install python=3.9.19
$ (.mmass_env) conda install -c conda-forge wxwidgets=3.1.5 wxpython=4.1.1 numpy=1.20.3 pandas=1.3.4
# (optional) joblib=1.5.0
# (optional) distro=1.9.0
# (dev) pyinstaller=6.9.0 httpx=0.28.1
```

```
# from `environment.yml`

$ conda env create --prefix .mmass_env -f environment.yml
$ conda activate .mmass_env
```

- build `mspy`

```
$ cd mspy
$ rm -rf build
$ python3 setup.py build_ext --inplace
```

- configs (use default configs if needed)

```
$ cp -r configs/* ~/.mmass/
```

- run or debug in VS Code

```
$ conda activate ./.mmass_env
$ (.mmass_env) python3 ./mmass.py
```

## Contribution guide

- download repository

```
$ git clone git@github.com:SCIENCE-OPEN/mmassx.git
$ cd mmassx
```

- to avoid changing line endings each commit

```
# linux
$ git config core.autocrlf input

# windows
$ git config core.autocrlf true
```

- for `.editorconfig` support, install in VS Code official extension `EditorConfig for VS Code`

## Goodies

- **An cache of ions** `~/.mmass/cache/ions/*.joblib` for current version of `configs/compounds.xml` is updated every time when is combination used in compound search window, this behaviour can be disabled in `config/config.xml`:

```
  </compoundsSearch>
    ...
    <param name="saveCache" value="1" type="int" />
  </compoundsSearch>
```

all combinations for all compound may be precomputed by `python3 precompute_ions_cache.py`:

```
$ python3 precompute_ions_cache.py --home --group-name "HMDB v5_Detected_Test"
Reading compounds from XML...
Loaded 10 compounds.
Using 6 worker(s)

Scanning approximately 7200 configs...
Checked 7200/7200 configs. New tasks: 2308
Summary for charge 1:
  Total configs:         7200
  Already cached:        4892
  New to generate:       2308
Generating 2308 ion configs for charge 1...
Progress [+1]: 2308/2308
Done: 2308/2308 generated for charge 1
Scanning approximately 7200 configs...
Checked 7200/7200 configs. New tasks: 2308
Summary for charge -1:
  Total configs:         7200
  Already cached:        4892
  New to generate:       2308
Generating 2308 ion configs for charge -1...
Progress [-1]: 2308/2308
Done: 2308/2308 generated for charge -1

All done! Ion cache stored in: /home/ldrahnik/.mmass/cache/ions
```

## Compound datasets

- **HMDB database** was processed by these steps:

  - downloaded `All Metabolites` manually from the https://hmdb.ca/downloads and unzipped into `$ cd datasets/HMDB` & `$ unzip hmdb_metabolites.zip`
  - downloaded `.xml` were split into multiple `.xml` files using
  ```
  $ mkdir -p hmdb_metabolites_split_output
  $ cd hmdb_metabolites_split_output
  $ xml_split < ../hmdb_metabolites.xml
  ```
  - converted split `.xml` to one `.csv` using `$ python split_xml_to_one_csv.py hmdb_metabolites_split_output hmdb_metabolites.csv`
  - sanitized and split one `.csv` into `.xml|.csv` by status column (`detected`, `quantified`, ..) using `$ cd datasets` & `$ python3 sanitize_csv_and_create_split_up_csv_and_xml.py HMDB/hmdb_metabolites.csv` with output:
  ```
  Final XML saved: hmdb_metabolites_quantified_processed.xml
  Fixed CSV saved: hmdb_metabolites_quantified_processed.csv
  Final XML saved: hmdb_metabolites_detected_processed.xml
  Fixed CSV saved: hmdb_metabolites_detected_processed.csv
  Final XML saved: hmdb_metabolites_expected_processed.xml
  Fixed CSV saved: hmdb_metabolites_expected_processed.csv
  Final XML saved: hmdb_metabolites_predicted_processed.xml
  Fixed CSV saved: hmdb_metabolites_predicted_processed.csv
  Processing complete
  ```

- **KEGG database** was processed by these steps:

  - downloaded `All Metabolites` from API using `$ python3 download.py` with output:
  ```
  Found 19464 missing compounds. Downloading in batches...
  ...
  Download complete in 924.56 seconds.
  ```
  - sanitized output `.csv` into `.xml|.csv` using `$ cd datasets` & `$ python3 sanitize_csv_and_create_split_up_csv_and_xml.py KEGG/kegg_metabolites.csv` with output:
  ```
  Final XML saved: kegg_metabolites_processed.xml
  Fixed CSV saved: kegg_metabolites_processed.csv
  Processing complete.
  ```

## Maintenance guide

- An executable file (e.g. `dist/mmassx-6.0.1.exe`) is generated by script `$ build-mmassx.bat` which has to be executed on Windows or on Windows inside virtualbox (the script is build around `$ pyinstaller --clean mmass.spec`)

# Gyellen fork of official mMass Repository ([link](https://github.com/gyellen/mMass))

This fork of the mMass 5.5.0 repo (xxao\\mMass) has been extensively updated to run with
- python 3.9
- numPy 1.20.3
- wxPython 4.1.1
- pandas 1.3.4

Some additional changes have been made to allow
- zooming in on annotated or unannotated peak
- import of .csv files
- lookup in KEGG for mass-to-formula

# Official mMass Repository ([link](https://github.com/xxao/mMass))

This is the official source code backup repository for
[mMass](http://www.mmass.org) software. Although mMass is no longer actively
developed and supported I decided to put the code here for others to be able
to share it, fork it and all the git craziness. Feel free to make your own
changes but please do not expect further contributions from my side.

At the time of writing the mMass code I was really not a programmer.
Programming was just a hobby and I was doing it rather for fun. Please respect
this while reading and modifying the original code :)

For more information and latest distributions please see the official mMass
homepage at [www.mmass.org](http://www.mmass.org).

Thank you for your interest, and ... have fun!


## Requirements

The mMass code was developed under Python 2 and has never been updated to
Python 3. Same is true for all the dependencies such as wxPython and NumPy.
The code was last tested against the following versions of said libraries
and **it is known to not work properly with current versions**. At the end
of the day, the code has not been touched since 2013.

- Python 2.7
- NumPy 1.5
- wxPython 2.8.12.1


## Disclaimer

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.

For Research Use Only. Not for use in diagnostic procedures.



## License

This program and its documentation are Copyright 2005-2013 by Martin Strohalm.

This program, along with all associated documentation, is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation.
See the LICENSE.TXT file for details (and make sure that you have entirely
read and understood it!)

Please note in particular that, if you use this program, or ANY part of
it - even a single line of code - in another application, the resulting
application becomes also GPL. In other words, GPL is a "contaminating" license.

If you do not understand any portion of this notice, please seek appropriate
professional legal advice. If you do not or - for any reason - you can not
accept ALL of these conditions, then you must not use nor distribute this
program.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
(file LICENSE.TXT) for more details.

The origin of this software must not be misrepresented; you must not claim
that you wrote the original software. Altered source versions must be clearly
marked as such, and must not be misrepresented as being the original software.

This notice must not be removed or altered from any source distribution.
