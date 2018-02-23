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
import de21.geometries
import reegis_tools.geometries
import reegis_tools.inhabitants
import reegis_tools.config as cfg


def get_ew_by_de21(year):
    de21_regions = de21.geometries.de21_regions()
    return reegis_tools.inhabitants.get_ew_by_region(year, de21_regions)


def get_ew_by_de21_subregions(year):
    """Get a GeoDataFrame with the inhabitants of each region.

    Parameters
    ----------
    year : int

    Returns
    -------
    geopandas.geoDataFrame
    """
    de21_sub = reegis_tools.geometries.Geometry(name='de21_subregions')
    de21_sub.load(cfg.get('paths', 'geometry'), 'overlap_region_polygon.csv')
    de21_sub.gdf['ew'] = reegis_tools.inhabitants.get_ew_by_region(year,
                                                                   de21_sub)
    return de21_sub.gdf


if __name__ == "__main__":
    oemof.tools.logger.define_logging()
    logging.info("Getting inhabitants by region for de21.")
    get_ew_by_de21_subregions(2012)
    # print(get_ew_by_de21(2012))
