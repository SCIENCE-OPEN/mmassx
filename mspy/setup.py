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
numpyInclude = numpy.get_include() + '/numpy'
pythonInclude = sys.prefix + '/include'
gyInclude = 'C:\Xilinx\Vivado\2019.1\msys64\mingw64\lib\gcc\x86_64-w64-mingw32\6.2.0\include'

# make setup
setup(
    name = 'calculations',
    version = '1.1',
    author = "Martin Strohalm",
    maintainer = 'Martin Strohalm',
    description = "Fast calculations for mspy.",
    ext_modules=[
        Extension('calculations', ['calculations.c'],
            include_dirs=[numpyInclude, pythonInclude, gyInclude]
            # ,libraries=['m']
        )
    ],
)
