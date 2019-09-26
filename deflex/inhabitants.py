# -*- coding: utf-8 -*-

"""Aggregate the number of inhabitants for each de21 region.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import logging

# oemof libraries
import oemof.tools.logger

# Internal libraries
import deflex.geometries
import reegis.geometries
import reegis.inhabitants
import reegis.config as cfg


def get_ew_by_deflex(year, rmap=None):
    deflex_regions = deflex.geometries.deflex_regions(rmap=rmap)
    name = '{0}_region'.format(cfg.get('init', 'map'))
    return reegis.inhabitants.get_inhabitants_by_region(
        year, deflex_regions, name=name)


if __name__ == "__main__":
    oemof.tools.logger.define_logging()
    logging.info("Getting inhabitants by region for {0}.".format(cfg.get(
        'init', 'map')))
    print(get_ew_by_deflex(2012))
