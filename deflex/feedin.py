# -*- coding: utf-8 -*-

"""Aggregating feed-in time series for the model regions.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os
import logging

# External libraries
import pandas as pd

# oemof packages
from oemof.tools import logger

# internal modules
import reegis.config as cfg
import reegis.coastdat

import deflex.powerplants as powerplants
import deflex.geometries


def get_grouped_power_plants(year):
    """Filter the capacity of the powerplants for the given year.
    """
    region_column = '{0}_region'.format(cfg.get('init', 'map'))
    return powerplants.get_deflex_pp_by_year(year).groupby(
        ['energy_source_level_2', region_column, 'coastdat2']).sum()


def aggregate_by_region(year, pp=None, weather_year=None):

    d_regions = deflex.geometries.deflex_regions()
    name = '{0}_region'.format(cfg.get('init', 'map'))

    return reegis.coastdat.get_feedin_per_region(year, d_regions, name, pp=pp,
                                                 weather_year=weather_year)


def get_deflex_feedin(year, feedin_type, weather_year=None):
    if weather_year is None:
        feedin_deflex_file_name = os.path.join(
            cfg.get('paths_pattern', 'deflex_feedin'),
            cfg.get('feedin', 'feedin_deflex_pattern')).format(
                year=year, type=feedin_type, map=cfg.get('init', 'map'))
    else:
        feedin_deflex_file_name = os.path.join(
            cfg.get('paths_pattern', 'deflex_feedin'), 'weather_variations',
            cfg.get('feedin', 'feedin_deflex_pattern_var')).format(
                year=year, type=feedin_type, map=cfg.get('init', 'map'),
                weather_year=weather_year)

    if feedin_type in ['solar', 'wind']:
        if not os.path.isfile(feedin_deflex_file_name):
            aggregate_by_region(year, weather_year=weather_year)
        return pd.read_csv(feedin_deflex_file_name, index_col=[0],
                           header=[0, 1, 2])
    elif feedin_type in ['hydro', 'geothermal']:
        if not os.path.isfile(feedin_deflex_file_name):
            aggregate_by_region(year)
        return pd.read_csv(feedin_deflex_file_name, index_col=[0], header=[0])
    else:
        return None


if __name__ == "__main__":
    logger.define_logging()
    logging.info("Aggregating regions.")
    aggregate_by_region(2014)
