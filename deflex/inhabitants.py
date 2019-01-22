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
    return reegis.inhabitants.get_ew_by_region(year, deflex_regions, name=name)


def get_ew_by_deflex_subregions(year):
    """Get a GeoDataFrame with the inhabitants of each region.

    Parameters
    ----------
    year : int

    Returns
    -------
    geopandas.geoDataFrame
    """
    deflex_sub = reegis.geometries.load(
        cfg.get('paths', 'geo_deflex'),
        cfg.get('geometry', 'overlap_federal_states_deflex_polygon').format(
            map=cfg.get('init', 'map')))
    deflex_sub['state'] = deflex_sub.index.to_series().str[2:]
    deflex_sub['region'] = deflex_sub.index.to_series().str[:2]
    deflex_sub['ew'] = reegis.inhabitants.get_ew_by_region(
        year, deflex_sub, name='deflex_subregions')

    deflex_sub = deflex_sub.replace({'state': cfg.get_dict(
        'STATE_KEYS')})
    deflex_sub['region'] = deflex_sub.region.astype(str).apply(
        'DE{:0>2}'.format)
    no_inhabitants = deflex_sub[deflex_sub.ew == 0]
    deflex_sub = deflex_sub[deflex_sub.ew != 0]
    logging.info("States with no inhabitants have been removed: {0}".format(
        no_inhabitants.index))

    return deflex_sub


if __name__ == "__main__":
    oemof.tools.logger.define_logging()
    logging.info("Getting inhabitants by region for {0}.".format(cfg.get(
        'init', 'map')))
    print(get_ew_by_deflex_subregions(2012)['ew'])
    print(get_ew_by_deflex(2012))
