# -*- coding: utf-8 -*-

"""
Reegis geometry tools.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os

# Internal libraries
from reegis_tools import config as cfg
from reegis_tools import geometries as geo


def deflex_regions(suffix='reegis', rmap=None, rtype='polygon'):
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'deflex_polygon').format(
                            suffix=suffix, map=rmap, type=rtype))
    regions = geo.Geometry(name='{map}_region'.format(
        map=rmap))
    regions.load(fullname=name)

    # Add 'DE' and leading zero to index
    regions.gdf['region'] = regions.gdf.index.to_series().astype(str).apply(
        'DE{:0>2}'.format)
    regions.gdf = regions.gdf.set_index('region')
    return regions


def deflex_power_lines(rmap=None, rtype='lines'):
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'powerlines').format(
                            map=rmap, type=rtype))
    lines = geo.Geometry(name='{map}_region'.format(
        map=rmap))
    lines.load(fullname=name)
    return lines
