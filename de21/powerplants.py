"""
Adapting the general reegis power plants to the de21 model.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


import pandas as pd
import os
import logging
import oemof.tools.logger as logger
import reegis_tools.geometries
import reegis_tools.config as cfg
import reegis_tools.powerplants
import de21.geometries


def add_model_region_pp(df):
    """Load the pp data set with geometries and add a column with the model
    region. Afterwards the geometry column is removed. As the renewable data
    set is big, the hdf5 format is used.
    """
    # Load de21 geometries
    de21_regions = de21.geometries.de21_regions()

    # Load power plant geometries
    pp = geo.Geometry(name='power plants', df=df)
    pp.create_geo_df()

    # Add region names to power plant table
    pp.gdf = reegis_tools.geometries.spatial_join_with_buffer(pp, de21_regions)
    pp.gdf2df()

    # Delete real geometries because they are not needed anymore.
    del pp.df['geometry']

    logging.info("de21 regions added to power plant table.")
    return pp.df


def add_capacity_in(pp):
    """Add a column to the conventional power plants to make it possible to
    calculate an average efficiency for the summed up groups.
    """
    # Calculate the inflow capacity for power plants with an efficiency value.
    pp['capacity_in'] = pp['capacity'].div(pp['efficiency'])

    # Sum up the valid in/out capacities to calculate an average efficiency
    cap_valid = pp.loc[pp['efficiency'].notnull(), 'capacity'].sum()
    cap_in = pp.loc[pp['efficiency'].notnull(), 'capacity_in'].sum()

    # Set the average efficiency for missing efficiency values
    pp['efficiency'] = pp['efficiency'].fillna(
        cap_valid / cap_in)

    # Calculate the inflow for all power plants
    pp['capacity_in'] = pp['capacity'].div(pp['efficiency'])
    
    logging.info("'capacity_in' column added to power plant table.")
    return pp


def pp_reegis2de21():
    filename_in = os.path.join(cfg.get('paths', 'powerplants'),
                               cfg.get('powerplants', 'reegis_pp'))
    filename_out = os.path.join(cfg.get('paths', 'powerplants'),
                                cfg.get('powerplants', 'de21_pp'))
    if not os.path.isfile(filename_in):
        filename_in = reegis_tools.powerplants.pp_opsd2reegis()
    pp = pd.read_hdf(filename_in, 'pp', mode='r')
    pp = add_model_region_pp(pp)
    pp = add_capacity_in(pp)

    pp.to_hdf(filename_out, 'pp')
    return filename_out


def get_de21_pp_by_year(year, overwrite_capacity=False):
    """

    Parameters
    ----------
    year : int
    overwrite_capacity : bool
        By default (False) a new column "capacity_<year>" is created. If set to
        True the old capacity column will be overwritten.

    Returns
    -------

    """
    filename = os.path.join(cfg.get('paths', 'powerplants'),
                            cfg.get('powerplants', 'de21_pp'))
    logging.info("Get de21 power plants for {0}.".format(year))
    if not os.path.isfile(filename):
        filename = pp_reegis2de21()
    pp = pd.read_hdf(filename, 'pp', mode='r')

    filter_columns = ['capacity_{0}', 'capacity_in_{0}']

    # Get all powerplants for the given year.
    # If com_month exist the power plants will be considered month-wise.
    # Otherwise the commission/decommission within the given year is not
    # considered.
    for fcol in filter_columns:
        filter_column = fcol.format(year)
        orig_column = fcol[:-4]
        c1 = (pp['com_year'] < year) & (pp['decom_year'] > year)
        pp.loc[c1, filter_column] = pp.loc[c1, orig_column]

        c2 = pp['com_year'] == year
        pp.loc[c2, filter_column] = (pp.loc[c2, orig_column] *
                                     (12 - pp.loc[c2, 'com_month']) / 12)
        c3 = pp['decom_year'] == year
        pp.loc[c3, filter_column] = (pp.loc[c3, orig_column] *
                                     pp.loc[c3, 'com_month'] / 12)

        if overwrite_capacity:
            pp[orig_column] = 0
            pp[orig_column] = pp[filter_column]
            del pp[filter_column]
    return pp


if __name__ == "__main__":
    logger.define_logging()
    pp_reegis2de21()
    my_df = get_de21_pp_by_year(2012, overwrite_capacity=False)
    logging.info('Done!')
    # exit(0)
    print(my_df[['capacity_2012', 'capacity_in_2012']].sum())
    print(my_df.groupby(['de21_regions', 'energy_source_level_2']).sum()[[
        'capacity_2012', 'capacity_in_2012']])
    # print(my_df[['capacity', 'capacity_2012']].sum(axis=0))
