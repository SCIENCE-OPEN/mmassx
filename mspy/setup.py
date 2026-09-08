import sys
import numpy
# from distutils.core import setup
# from distutils.extension import Extension

from setuptools import setup, Extension


# Build on WIN using MinGW:
# python setup.py build --compiler=mingw32
# Copy calculations.pyd to mspy directory

# Build on Mac:
# python setup.py build
# Copy calculations.so to mspy directory


# make include paths
# calculations.c does `#include "arrayobject.h"` (needs the numpy/
# subdir itself on the path) but arrayobject.h then does
# `#include "numpy/ndarrayobject.h"` etc. (needs the parent of that
# subdir on the path too), so both must be included.
numpyInclude = numpy.get_include()
pythonInclude = sys.prefix + '/include'

# make setup
setup(
    name = 'calculations',
    version = '1.1',
    author = "Martin Strohalm",
    maintainer = 'Martin Strohalm',
    description = "Fast calculations for mspy.",
    ext_modules=[
        Extension('calculations', ['calculations.c'],
            include_dirs=[numpyInclude, numpyInclude + '/numpy', pythonInclude]
            # ,libraries=['m']
        )
    ],
)
