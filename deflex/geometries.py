# -*- coding: utf-8 -*-

"""
Reegis geometry tools.

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


# Python libraries
import os

# Internal libraries
from reegis import config as cfg
from reegis import geometries as geo


def deflex_regions(suffix='reegis', rmap=None, rtype='polygon'):
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'deflex_polygon').format(
                            suffix=suffix, map=rmap, type=rtype))
    regions = geo.load(fullname=name)

    # Add 'DE' and leading zero to index
    regions['region'] = regions.index.to_series().astype(str).apply(
        'DE{:0>2}'.format)
    regions = regions.set_index('region')
    return regions


def deflex_power_lines(rmap=None, rtype='lines'):
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'powerlines').format(
                            map=rmap, type=rtype))
    lines = geo.load(fullname=name)
    return lines
