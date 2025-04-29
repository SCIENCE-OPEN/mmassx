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

- conda (recommended)

or

- python 3.9.19
- numPy 1.20.3
- wxPython 4.1.1
- wxwidgets 3.1.5
- pandas 1.3.4

## Installation

- create new virtual environment or activate virtual environment from file `environment.yml`

```
# new

$ conda create --prefix ./.mmass_env
$ conda activate ./.mmass_env
$ (.mmass_env) conda install python=3.9.19
$ (.mmass_env) conda install -c conda-forge wxwidgets=3.1.5 wxpython=4.1.1 numpy=1.20.3 pandas=1.3.4
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
$ cp -r configs ~/.mmass/
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
