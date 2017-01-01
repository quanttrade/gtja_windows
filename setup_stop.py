from distutils.core import setup

from Cython.Build import cythonize

setup(
    name='stop_signal',
    ext_modules=cythonize('stop_signal.pyx')
)
