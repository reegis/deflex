# --> scenario builder

# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
# Python libraries
import os

import pandas as pd

# internal modules
from deflex import config as cfg

# from reegis import demand_heat


def get_heat_profiles_deflex(
    deflex_geo, year, time_index=None, keep_unit=False
):
    """

    Parameters
    ----------
    year
    deflex_geo
    time_index
    keep_unit

    Returns
    -------

    """
    # separate_regions=keep all demand connected to the region
    separate_regions = cfg.get_list("demand_heat", "separate_heat_regions")
    # Add lower and upper cases to be not case sensitive
    separate_regions = ([x.upper() for x in separate_regions] +
                        [x.lower() for x in separate_regions])

    # add second fuel to first
    combine_fuels = cfg.get_dict("combine_heat_fuels")

    # fuels to be dissolved per region
    region_fuels = cfg.get_list("demand_heat", "local_fuels")

    fn = os.path.join(
        cfg.get("paths", "demand"),
        "heat_profiles_{year}_{map}".format(year=year, map=deflex_geo.name),
    )
    print(fn)
    demand_region = pd.DataFrame()
    # demand_region = (
    #     demand_heat.get_heat_profiles_by_region(
    #         deflex_geo, year, to_csv=fn, weather_year=weather_year
    #     )
    #     .groupby(level=[0, 1], axis=1)
    #     .sum()
    # )

    # Decentralised demand is combined to a nation-wide demand if not part
    # of region_fuels.
    regions = list(
        set(demand_region.columns.get_level_values(0).unique())
        - set(separate_regions)
    )

    # If region_fuels is 'all' fetch all fuels to be local.
    if "all" in region_fuels:
        region_fuels = demand_region.columns.get_level_values(1).unique()

    for fuel in demand_region.columns.get_level_values(1).unique():
        demand_region["DE_demand", fuel] = 0

    for region in regions:
        for f1, f2 in combine_fuels.items():
            demand_region[region, f1] += demand_region[region, f2]
            demand_region.drop((region, f2), axis=1, inplace=True)
        cols = list(set(demand_region[region].columns) - set(region_fuels))
        for col in cols:
            demand_region["DE_demand", col] += demand_region[region, col]
            demand_region.drop((region, col), axis=1, inplace=True)

    if time_index is not None:
        demand_region.index = time_index

    if not keep_unit:
        msg = (
            "The unit of the source is 'TJ'. "
            "Will be divided by {0} to get 'MWh'."
        )
        converter = 0.0036
        demand_region = demand_region.div(converter)
        logging.debug(msg.format(converter))

    demand_region.sort_index(1, inplace=True)

    for c in demand_region.columns:
        if demand_region[c].sum() == 0:
            demand_region.drop(c, axis=1, inplace=True)

    return demand_region


if __name__ == "__main__":
    pass
