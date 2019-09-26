# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os
import logging

# oemof libraries
from oemof.tools import logger

# internal modules
from reegis import config as cfg
from reegis import geometries
from reegis import demand_heat
from reegis import demand_elec


def get_elec_profiles_deflex(year, deflex_geo):
    return demand_elec.get_entsoe_profile_by_region(
        deflex_geo, year, deflex_geo.name, annual_demand='bmwi')


def get_heat_profiles_deflex(year, deflex_geo, time_index=None,
                             weather_year=None, keep_unit=False):
    """

    Parameters
    ----------
    year
    deflex_geo
    time_index
    weather_year
    keep_unit

    Returns
    -------

    """
    # separate_regions = keep all demand connected to the region
    separate_regions = cfg.get_list('demand_heat', 'separate_heat_regions')

    # add second fuel to first
    combine_fuels = cfg.get_dict('combine_heat_fuels')

    # fuels to be dissolved per region
    region_fuels = cfg.get_list('demand_heat', 'local_fuels')

    fn = os.path.join(
        cfg.get('paths', 'demand'),
        'heat_profiles_{year}_{map}'.format(year=year, map=deflex_geo.name))

    demand_region = demand_heat.get_heat_profiles_by_region(
        year, deflex_geo, to_csv=fn, weather_year=weather_year).groupby(
            level=[0, 1], axis=1).sum()

    # Decentralised demand is combined to a nation-wide demand if not part
    # of region_fuels.
    regions = list(set(demand_region.columns.get_level_values(0).unique()) -
                   set(separate_regions))

    # If region_fuels is 'all' fetch all fuels to be local.
    if 'all' in region_fuels:
        region_fuels = demand_region.columns.get_level_values(1).unique()

    for fuel in demand_region.columns.get_level_values(1).unique():
        demand_region['DE_demand', fuel] = 0

    for region in regions:
        for f1, f2 in combine_fuels.items():
            demand_region[region, f1] += demand_region[region, f2]
            demand_region.drop((region, f2), axis=1, inplace=True)
        cols = list(set(demand_region[region].columns) - set(region_fuels))
        for col in cols:
            demand_region['DE_demand', col] += demand_region[region, col]
            demand_region.drop((region, col), axis=1, inplace=True)

    if time_index is not None:
        demand_region.index = time_index

    if not keep_unit:
        msg = ("The unit of the source is 'TJ'. "
               "Will be divided by {0} to get 'MWh'.")
        converter = 0.0036
        demand_region = demand_region.div(converter)
        logging.debug(msg.format(converter))

    demand_region.sort_index(1, inplace=True)

    for c in demand_region.columns:
        if demand_region[c].sum() == 0:
            demand_region.drop(c, axis=1, inplace=True)

    return demand_region


if __name__ == "__main__":
    logger.define_logging(screen_level=logging.ERROR,
                          file_level=logging.ERROR)
    deflex_map = cfg.get('init', 'map')

    my_deflex_geo = geometries.load(
        cfg.get('paths', 'geo_deflex'),
        cfg.get('geometry', 'deflex_polygon').format(
            type='polygon', map=deflex_map, suffix='reegis'))
    my_deflex_geo = my_deflex_geo.set_index(
        'DE' + my_deflex_geo.index.map(str).str.zfill(2))
    my_deflex_geo.name = deflex_map
    get_elec_profiles_deflex(2014, my_deflex_geo)
