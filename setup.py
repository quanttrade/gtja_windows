from distutils.core import setup

from Cython.Build import cythonize

setup(
    name='stop_loss',
    ext_modules=cythonize('stop_loss.pyx')
)
