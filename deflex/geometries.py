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
from deflex import config as cfg
from reegis import geometries as geo


def deflex_regions(rmap=None, rtype='polygons'):
    """

    Parameters
    ----------
    rmap : str
        Name of the deflex map.
    rtype : str
        Type of the deflex map ('polygon', 'labels').

    Returns
    -------
    GeoDataFrame

    Examples
    --------
    >>> len(deflex_regions('de17'))
    17
    >>> l = deflex_regions('de21', 'labels').loc['DE04', 'geometry']
    >>> l.x
    13.2
    >>> l.y
    51.1
    >>> cfg.tmp_set('init', 'map', 'de22')
    >>> deflex_regions().name
    'de22'
    >>> list(deflex_regions('de02').index)
    ['DE01', 'DE02']
    """
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'deflex_polygon').format(
                            suffix='.geojson', map=rmap, type=rtype))
    regions = geo.load(fullname=name)
    regions.set_index('region', inplace=True)
    regions.name = rmap
    return regions


def deflex_power_lines(rmap=None, rtype='lines'):
    """

    Parameters
    ----------
    rmap : str
        Name of the deflex powerline map.
    rtype : str
        Type of the deflex powerline map ('lines', 'labels').

    Returns
    -------

    Examples
    --------
    >>> len(deflex_power_lines('de17'))
    31
    >>> deflex_power_lines('de02').index[0]
    'DE01-DE02'
    >>> cfg.tmp_set('init', 'map', 'de21')
    >>> deflex_power_lines().name
    'de21'
    """
    if rmap is None:
        rmap = cfg.get('init', 'map')
    name = os.path.join(cfg.get('paths', 'geo_deflex'),
                        cfg.get('geometry', 'powerlines').format(
                            map=rmap, type=rtype, suffix='.geojson'))
    lines = geo.load(fullname=name)
    lines.set_index('name', inplace=True)
    lines.name = rmap
    return lines
