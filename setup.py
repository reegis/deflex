#! /usr/bin/env python

from setuptools import setup

setup(name='de21',
      version='0.0.1',
      author='Uwe Krien',
      author_email='uwe.krien@rl-institut.de',
      description='A reegis model of Germany with 21 region (18 +3).',
      package_dir={'de21': 'de21'},
      install_requires=['oemof >= 0.1.0',
                        'pandas >= 0.17.0',
                        'reegis_tools',
                        'demandlib',
                        'workalendar',
                        'networkx',
                        'numpy',
                        'shapely']
      )
