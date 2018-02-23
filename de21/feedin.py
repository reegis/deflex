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
import de21.powerplants as powerplants


def aggregate_by_region_coastdat_feedin(pp, year, category, outfile):
    cat = category.lower()

    logging.info("Aggregating {0} feed-in for {1}...".format(cat, year))

    # Define the path for the input files.
    coastdat_path = os.path.join(cfg.get('paths_pattern', 'coastdat')).format(
        year=year, type=cat)

    # Prepare the lists for the loops
    set_names = []
    set_name = None
    pwr = dict()
    columns = dict()
    replace_str = 'coastdat_{0}_solar_'.format(year)
    for file in os.listdir(coastdat_path):
        if file[-2:] == 'h5':
            set_name = file[:-3].replace(replace_str, '')
            set_names.append(set_name)
            pwr[set_name] = pd.HDFStore(os.path.join(coastdat_path, file))
            columns[set_name] = pwr[set_name]['/A1129087'].columns

    # Create DataFrame with MultiColumns to take the results
    my_index = pwr[set_name]['/A1129087'].index
    my_cols = pd.MultiIndex(levels=[[], [], []], labels=[[], [], []],
                            names=[u'region', u'set', u'subset'])
    feedin = pd.DataFrame(index=my_index, columns=my_cols)

    # Loop over all aggregation regions
    # Sum up time series for one region and divide it by the
    # capacity of the region to get a normalised time series.
    regions = pp.index.get_level_values(1).unique().sort_values()
    for region in regions:
        try:
            coastdat_ids = pp.loc[(category, region)].index
        except KeyError:
            coastdat_ids = []
        number_of_coastdat_ids = len(coastdat_ids)
        logging.info("{0} - {1} ({2})".format(
            year, region, number_of_coastdat_ids))
        logging.debug("{0}".format(coastdat_ids))

        # Loop over all sets that have been found in the coastdat path
        if number_of_coastdat_ids > 0:
            for name in set_names:
                # Loop over all sub-sets that have been found within each file.
                for col in columns[name]:
                    temp = pd.DataFrame(index=my_index)

                    # Loop over all coastdat ids, that intersect with the
                    # actual region.
                    for coastdat in coastdat_ids:
                        # Create a tmp table for each coastdat id.
                        coastdat_id = '/A{0}'.format(int(coastdat))
                        pp_inst = float(pp.loc[(category, region, coastdat),
                                               'capacity_{0}'.format(year)])
                        temp[coastdat_id] = (
                            pwr[name][coastdat_id][col][:8760].multiply(
                                pp_inst))
                    # Sum up all coastdat columns to one region column
                    colname = '_'.join(col.split('_')[-3:])
                    feedin[region, name, colname] = (
                        temp.sum(axis=1).divide(float(
                            pp.loc[(category, region), 'capacity_{0}'.format(
                                year)].sum())))

    feedin.to_csv(outfile)
    for name_of_set in set_names:
        pwr[name_of_set].close()


def aggregate_by_region_hydro(feedin_de21, regions, pp, year):
    hydro_energy = pd.read_csv(
        os.path.join(cfg.get('paths', 'data_de21'),
                     'energy_capacity_bmwi.csv'),
        header=[0, 1], index_col=[0])['Wasserkraft']['energy']
    capacity_column = 'capacity_{0}'.format(year)
    hydro_capacity = pp.loc['Hydro'].groupby(level=[0]).sum()[capacity_column]

    full_load_hours = hydro_energy.loc[year] / hydro_capacity.sum() * 1000

    hydro_path = os.path.abspath(os.path.join(
        *feedin_de21.format(year=0, type='hydro').split('/')[:-1]))

    if not os.path.isdir(hydro_path):
        os.makedirs(hydro_path)

    filename = feedin_de21.format(year=year, type='hydro')
    idx = pd.date_range(start="{0}-01-01 00:00".format(year),
                        end="{0}-12-31 23:00".format(year),
                        freq='H', tz='Europe/Berlin')
    feedin = pd.DataFrame(columns=regions, index=idx)
    feedin[feedin.columns] = full_load_hours / len(feedin)
    feedin.to_csv(filename)

    # https://shop.dena.de/fileadmin/denashop/media/Downloads_Dateien/esd/
    # 9112_Pumpspeicherstudie.pdf
    # S. 110ff


def get_grouped_power_plants(year):
    """Filter the capacity of the powerplants for the given year.
    """
    return powerplants.get_de21_pp_by_year(year).groupby(
        ['energy_source_level_2', 'de21_regions', 'coastdat2']).sum()


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
            ['energy_source_level_2', 'de21_regions', 'coastdat2']).sum()

    # Loop over weather depending feed-in categories.
    for cat in ['Wind', 'Solar']:
        outfile_name = feedin_de21_outfile_name.format(type=cat.lower())
        if not os.path.isfile(outfile_name):
            if pp is None:
                pp = get_grouped_power_plants(year)
            aggregate_by_region_coastdat_feedin(pp, year, cat, outfile_name)

    outfile_name = feedin_de21_outfile_name.format(type='hydro')
    if not os.path.isfile(outfile_name):
        if pp is None:
            pp = get_grouped_power_plants(year)
        regions = pp.index.get_level_values(1).unique().sort_values()
        aggregate_by_region_hydro(outfile_name, regions, pp, year)


def get_de21_feedin(year, feedin_type):
    feedin_de21_file_name = os.path.join(
        cfg.get('paths_pattern', 'de21_feedin'),
        cfg.get('feedin', 'feedin_de21_pattern')).format(
            year=year, type=feedin_type)
    if feedin_type in ['solar', 'wind']:
        return pd.read_csv(feedin_de21_file_name, index_col=[0],
                           header=[0, 1, 2])
    elif feedin_type in ['hydro', 'geothermal']:
        return pd.read_csv(feedin_de21_file_name, index_col=[0], header=[0])
    else:
        return None


if __name__ == "__main__":
    logger.define_logging()
    aggregate_by_region(2013)
