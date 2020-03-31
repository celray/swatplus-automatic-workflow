from distutils.core import setup
    
from Cython.Build import cythonize
import os
import numpy
if 'QSWAT_PROJECT' in os.environ and 'Linux' in os.environ['QSWAT_PROJECT']:
    includePath = '/usr/include/python3.6'
    sep = ':'
else:
    includePath = os.environ['OSGEO4W_ROOT'] + r'/apps/Python36/include'
    sep = ';'
if 'INCLUDE' in os.environ:
    os.environ['INCLUDE'] = os.environ['INCLUDE'] + sep + includePath + sep + numpy.get_include()
else:
    os.environ['INCLUDE'] = includePath + sep + numpy.get_include()

setup(
    name = "pyxes",
    package_dir = {'QSWATPlus': ''}, 
    ext_modules = cythonize('*.pyx', include_path = [os.environ['INCLUDE']]),
)
