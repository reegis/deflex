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


def de21_regions(suffix='vg'):
    name = os.path.join(cfg.get('paths', 'geo_de21'),
                        cfg.get('geometry', 'de21_polygon').format(
                            suffix=suffix))
    regions = geo.Geometry(name='de21_region')
    regions.load(fullname=name)
    return regions
