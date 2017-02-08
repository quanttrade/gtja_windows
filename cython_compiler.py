
# coding: utf-8

# In[2]:

from distutils.core import setup
from Cython.Build import cythonize
setup(ext_modules=cythonize('DTW.pyx'))

