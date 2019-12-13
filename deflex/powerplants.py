# -*- coding: utf-8 -*-

"""Adapting the general reegis power plants to the deflex model.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import pandas as pd
import os
import logging
from reegis import geometries as reegis_geometries
from deflex import config as cfg
from reegis import powerplants


# Todo: Revise and test.


def pp_reegis2deflex(regions, name, filename_in=None, filename_out=None):
    """
    Add federal states and deflex regions to powerplant table from reegis. As
    the process takes a while the result is stored for further usage.

    Returns
    -------
    str : The full path where the result file is stored.

    """
    if filename_out is None:
        filename_out = os.path.join(
            cfg.get("paths", "powerplants"),
            cfg.get("powerplants", "deflex_pp"),
        ).format(map=cfg.get("init", "map"))

    # Add deflex regions to powerplants
    pp = powerplants.add_regions_to_powerplants(
        regions, name, dump=False, filename=filename_in
    )

    # Add federal states to powerplants
    federal_states = reegis_geometries.get_federal_states_polygon()
    pp = powerplants.add_regions_to_powerplants(
        federal_states, "federal_states", pp=pp, dump=False
    )

    # store the results for further usage of deflex
    pp.to_hdf(filename_out, "pp")
    return filename_out


# def remove_onshore_technology_from_offshore_regions(df):
#     """ This filter should be improved. It is slow and has to be adapted
#     manually. Anyhow it seems to work this way."""
#
#     logging.info("Removing onshore technology from offshore regions.")
#     logging.info("The code is not efficient. So it may take a while.")
#
#     offshore_regions=(
#         cfg.get_dict_list('offshore_regions_set')[cfg.get('init', 'map')])
#
#     coast_regions={'de02': {'MV': 'DE01',
#                               'SH': 'DE01',
#                               'NI': 'DE01 '},
#                      'de17': {'MV': 'DE13',
#                               'SH': 'DE01',
#                               'NI': 'DE03'},
#                      'de21': {'MV': 'DE01',
#                               'SH': 'DE13',
#                               'NI': 'DE14'},
#                      'de22': {'MV': 'DE01',
#                               'SH': 'DE13',
#                               'NI': 'DE14'}}
#     try:
#         dc=coast_regions[cfg.get('init', 'map')]
#     except KeyError:
#         raise ValueError('Coast regions not defined for {0} model.'.format(
#             cfg.get('init', 'map')))
#
#     region_column='{0}_region'.format(cfg.get('init', 'map'))
#
#     for ttype in ['Solar', 'Bioenergy', 'Wind']:
#         for region in offshore_regions:
#             logging.debug("Clean {1} from {0}.".format(region, ttype))
#
#             c1=df['energy_source_level_2'] == ttype
#             c2=df[region_column] == region
#
#             condition=c1 & c2
#
#             if ttype == 'Wind':
#                 condition=c1 & c2 & (df['technology'] == 'Onshore')
#
#             for i, v in df.loc[condition].iterrows():
#                 df.loc[i, region_column]=(
#                     dc[df.loc[i, 'federal_states']])
#     return df


def process_pp_table(pp):
    # # Remove powerplants outside Germany
    # for state in cfg.get_list('powerplants', 'remove_states'):
    #     pp=pp.loc[pp.state != state]
    #
    # if clean_offshore:
    #     pp=remove_onshore_technology_from_offshore_regions(pp)
    # Remove PHES (storages)
    if cfg.get("powerplants", "remove_phes"):
        pp = pp.loc[pp.technology != "Pumped storage"]
    return pp


def get_deflex_pp_by_year(regions, year, name, overwrite_capacity=False):
    """

    Parameters
    ----------
    regions : GeoDataFrame
    year : int
    name : str
    overwrite_capacity : bool
        By default (False) a new column "capacity_<year>" is created. If set to
        True the old capacity column will be overwritten.

    Returns
    -------

    """
    filename = os.path.join(
        cfg.get("paths", "powerplants"), cfg.get("powerplants", "deflex_pp")
    ).format(map=name)
    logging.info("Get deflex power plants for {0}.".format(year))
    if not os.path.isfile(filename):
        msg = "File '{0}' does not exist. Will create it from reegis file."
        logging.debug(msg.format(filename))
        filename = pp_reegis2deflex(regions, name)
    pp = pd.DataFrame(pd.read_hdf(filename, "pp", mode="r"))

    # Remove unwanted data sets
    pp = process_pp_table(pp)

    filter_columns = ["capacity_{0}", "capacity_in_{0}"]

    # Get all powerplants for the given year.
    # If com_month exist the power plants will be considered month-wise.
    # Otherwise the commission/decommission within the given year is not
    # considered.

    for fcol in filter_columns:
        filter_column = fcol.format(year)
        orig_column = fcol[:-4]
        c1 = (pp["com_year"] < year) & (pp["decom_year"] > year)
        pp.loc[c1, filter_column] = pp.loc[c1, orig_column]

        c2 = pp["com_year"] == year
        pp.loc[c2, filter_column] = (
            pp.loc[c2, orig_column] * (12 - pp.loc[c2, "com_month"]) / 12
        )
        c3 = pp["decom_year"] == year
        pp.loc[c3, filter_column] = (
            pp.loc[c3, orig_column] * pp.loc[c3, "com_month"] / 12
        )

        if overwrite_capacity:
            pp[orig_column] = 0
            pp[orig_column] = pp[filter_column]
            del pp[filter_column]

    return pp


if __name__ == "__main__":
    pass
