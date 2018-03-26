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
import reegis_tools.config as cfg
import reegis_tools.coastdat

import de21.powerplants as powerplants


def get_grouped_power_plants(year):
    """Filter the capacity of the powerplants for the given year.
    """
    return powerplants.get_de21_pp_by_year(year).groupby(
        ['energy_source_level_2', 'de21_region', 'coastdat2']).sum()


def aggregate_by_region(year, pp=None):
    # Create the path for the output files.
    feedin_de21_path = cfg.get('paths_pattern', 'de21_feedin').format(
        year=year)
    os.makedirs(feedin_de21_path, exist_ok=True)

    # Create pattern for the name of the resulting files.
    feedin_de21_outfile_name = os.path.join(
        feedin_de21_path,
        cfg.get('feedin', 'feedin_de21_pattern').format(
            year=year, type='{type}'))

    # Filter the capacity of the powerplants for the given year.
    if pp is not None:
        pp = pp.groupby(
            ['energy_source_level_2', 'de21_region', 'coastdat2']).sum()
    else:
        pp = get_grouped_power_plants(year)

    regions = pp.index.get_level_values(1).unique().sort_values()

    # Loop over weather depending feed-in categories.
    # WIND and PV
    for cat in ['Wind', 'Solar']:
        outfile_name = feedin_de21_outfile_name.format(type=cat.lower())
        if not os.path.isfile(outfile_name):
            reegis_tools.coastdat.aggregate_by_region_coastdat_feedin(
                pp, regions, year, cat, outfile_name)

    # HYDRO
    outfile_name = feedin_de21_outfile_name.format(type='hydro')
    if not os.path.isfile(outfile_name):
        reegis_tools.coastdat.aggregate_by_region_hydro(
            pp, regions, year, outfile_name)

    # GEOTHERMAL
    outfile_name = feedin_de21_outfile_name.format(type='geothermal')
    if not os.path.isfile(outfile_name):
        reegis_tools.coastdat.aggregate_by_region_geothermal(
            regions, year, outfile_name)


def get_de21_feedin(year, feedin_type):
    feedin_de21_file_name = os.path.join(
        cfg.get('paths_pattern', 'de21_feedin'),
        cfg.get('feedin', 'feedin_de21_pattern')).format(
            year=year, type=feedin_type)
    if feedin_type in ['solar', 'wind']:
        if not os.path.isfile(feedin_de21_file_name):
            aggregate_by_region(year)
        return pd.read_csv(feedin_de21_file_name, index_col=[0],
                           header=[0, 1, 2])
    elif feedin_type in ['hydro', 'geothermal']:
        if not os.path.isfile(feedin_de21_file_name):
            aggregate_by_region(year)
        return pd.read_csv(feedin_de21_file_name, index_col=[0], header=[0])
    else:
        return None


if __name__ == "__main__":
    logger.define_logging()
    logging.info("Aggregating regions.")
    aggregate_by_region(2014)
