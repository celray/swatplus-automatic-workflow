from distutils.core import setup
    
from Cython.Build import cythonize  # @UnresolvedImport
import os
import numpy

includePath = os.environ['OSGEO4W_ROOT'] + r'/apps/Python39/include'
numpyInclude = numpy.get_include()
sep = ';'
if 'INCLUDE' in os.environ:
    os.environ['INCLUDE'] = os.environ['INCLUDE'] + sep + includePath + sep + numpyInclude
else:
    os.environ['INCLUDE'] = includePath + sep + numpyInclude
    
print('include path is {0}'.format(os.environ['INCLUDE']))


setup(
    name = "pyxes",
    package_dir = {'QSWATPlus': ''}, 
    ext_modules = cythonize('*.pyx', include_path = [os.environ['INCLUDE']]),
)
