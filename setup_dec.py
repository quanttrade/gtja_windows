from distutils.core import setup, Extension

import numpy
from Cython.Build import cythonize

setup(ext_modules=cythonize(Extension(
    'stop_loss_dec',
    sources=['stop_loss_dec.pyx'],
    language='c',
    include_dirs=[numpy.get_include()],
    library_dirs=[],
    libraries=[],
    extra_compile_args=[],
    extra_link_args=[]
)))
