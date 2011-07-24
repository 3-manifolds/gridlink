#!/usr/bin/env python

from setuptools import setup, Command
from distutils.command.install_data import install_data

setup(name='Gridlink',
      version='2.0',
      description='Graphical tool for working with gridlinks.',
      author='Marc Culler',
      author_email='culler@math.uic.edu',
      url='http://www.math.uic.edu/~t3m',
      zip_safe=False,
      packages=['gridlink'],
      entry_points = {'console_scripts': ['gridlink = gridlink.app:main']},
      package_data={'gridlink':['doc/gridlink.html']},
#      scripts=['bin/gridlink']
     )
