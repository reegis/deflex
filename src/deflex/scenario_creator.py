# --> kein reegis nur scenario_builder und den als optional requirement


# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""


import json
import logging
import os
from collections import namedtuple

import pandas as pd

from deflex import config as cfg
from deflex import scenario_tools
from deflex import transmission

from scenario_builder import commodity
from scenario_builder import demand
from scenario_builder import feedin
from scenario_builder import mobility
from scenario_builder import powerplants
from scenario_builder import storages


def scenario_default_decentralised_heat():
    """

    Returns
    -------

    """
    df = pd.DataFrame(columns=pd.MultiIndex(levels=[[], []], codes=[[], []]))
    fuels = ["hard coal", "lignite", "natural gas", "oil", "other", "re"]
    for fuel in fuels:
        df.loc["efficiency", ("DE_demand", fuel)] = 0.85
        df.loc["source", ("DE_demand", fuel)] = fuel

    return df


def create_scenario(regions, year, name, lines, opsd_version=None, weather_year=None):
    """

    Parameters
    ----------
    regions
    year
    name
    lines
    weather_year

    Returns
    -------

    """
    if opsd_version is None:
        if year < 2015:
            opsd_version = "2019-06-05"

    table_collection = {}

    logging.info("BASIC SCENARIO - STORAGES")
    table_collection["storages"] = storages.scenario_storages(
        regions, year, name
    )

    logging.info("BASIC SCENARIO - POWER PLANTS")
    table_collection = powerplants.scenario_powerplants(
        table_collection, regions, year, name
    )

    logging.info("BASIC SCENARIO - TRANSMISSION")
    print("******************", name)
    if len(regions) > 1:
        table_collection["transmission"] = transmission.scenario_transmission(
            table_collection, regions, name, lines
        )
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - CHP PLANTS")
    if cfg.get("creator", "heat"):
        table_collection = powerplants.scenario_chp(
            table_collection, regions, year, name, weather_year=weather_year
        )
    logging.info("BASIC SCENARIO - DECENTRALISED HEAT")
    if cfg.get("creator", "heat"):
        table_collection[
            "decentralised_heat"
        ] = scenario_default_decentralised_heat()
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - SOURCES")
    table_collection[
        "commodity_source"
    ] = commodity.scenario_commodity_sources(year)
    table_collection["volatile_series"] = feedin.scenario_feedin(
        regions, year, name, weather_year=weather_year
    )

    logging.info("BASIC SCENARIO - DEMAND")
    table_collection["demand_series"] = demand.scenario_demand(
        regions,
        year,
        name,
        opsd_version=opsd_version,
        weather_year=weather_year,
    )

    logging.info("BASIC SCENARIO - MOBILITY")
    table_collection = mobility.scenario_mobility(year, table_collection)

    logging.info("ADD META DATA")
    table_collection["meta"] = meta_data(year)
    return table_collection


def meta_data(year):
    meta = pd.DataFrame.from_dict(
        cfg.get_dict("creator"), orient="index", columns=["value"]
    )
    meta.loc["year"] = year
    meta.loc["map"] = cfg.get("init", "map")

    # Create name
    if cfg.get("creator", "heat"):
        heat = "heat"
    else:
        heat = "no-heat"
    if cfg.get("creator", "group_transformer"):
        merit = "no-reg-merit"
    else:
        merit = "reg-merit"
    meta.loc["name"] = "{0}_{1}_{2}_{3}_{4}".format(
        "deflex", year, cfg.get("init", "map"), heat, merit
    )
    return meta


def clean_time_series(table_collection):
    """

    Parameters
    ----------
    table_collection

    Returns
    -------

    """
    dts = table_collection["demand_series"]
    vts = table_collection["volatile_series"]
    vs = table_collection["volatile_source"]

    regions = list(dts.columns.get_level_values(0).unique())
    if "DE_demand" in regions:
        regions.remove("DE_demand")
    for reg in regions:
        for load in ["district heating", "electrical_load"]:
            if dts[reg].get(load) is not None:
                if dts[reg, load].sum() == 0:
                    msg = (
                        "Removing %s time series of region %s because"
                        "sum of time series is %s"
                    )
                    logging.debug(msg, load, reg, dts[reg, load].sum())
                    del dts[reg, load]

    regions = list(vts.columns.get_level_values(0).unique())
    for reg in regions:
        for t in ["hydro", "solar", "wind", "geothermal"]:
            if (t not in vs.loc[reg].index) or (
                vs.loc[(reg, t), "capacity"].sum() == 0
            ):
                if vts.get(reg) is not None:
                    if vts[reg].get(t) is not None:
                        msg = (
                            "Removing %s time series of region %s "
                            "because installed capacity is %s"
                        )
                        logging.debug(msg, t, reg, vs.loc[reg].get(t))
                        vts.drop((reg, t), axis=1, inplace=True)

    return table_collection


def create_basic_scenario(
    year,
    name,
    regions,
    transmission=None,
    csv_path=None,
    excel_path=None,
):
    """
    Create a basic scenario for a given year and region-set.

    Parameters
    ----------
    year : int
        Year of the scenario.
    name : str
        Name of the scenario
    regions : geopandas.geoDataFrame
        Set of region polygons.
    transmission : geopandas.geoDataFrame
        Set of transmission lines.
    csv_path : str
        A directory to store the scenario as csv collection. If None no csv
        collection will be created. Either csv_path or excel_path must not be
        'None'.
    excel_path : str
        A file to store the scenario as an excel map. If None no excel file
        will be created. Both suffixes 'xls' or 'xlsx' are possible. The excel
        format can be used in most spreadsheet programs such as LibreOffice or
        Gnumeric. Either csv_path or excel_path must not be 'None'.

    Returns
    -------
    namedtuple : Path

    Examples
    --------
    >>> my_year=2014  # doctest: +SKIP
    >>> my_map="de21"  # doctest: +SKIP
    >>> p=create_basic_scenario(my_year, regions=my_map)  # doctest: +SKIP
    >>> print("Xls path: {0}".format(p.xls))  # doctest: +SKIP
    >>> print("Csv path: {0}".format(p.csv))  # doctest: +SKIP

    """
    configuration = json.dumps(
        cfg.get_dict("creator"), indent=4, sort_keys=True
    )
    logging.info(
        "The following configuration is used to build the scenario:" " %s",
        configuration,
    )
    paths = namedtuple("paths", "xls, csv")

    table_collection = create_scenario(regions, year, name, transmission)

    table_collection = clean_time_series(table_collection)

    name = table_collection["meta"].loc["name", "value"]
    sce = scenario_tools.Scenario(
        table_collection=table_collection, name=name, year=year
    )

    if csv_path is not None:
        os.makedirs(csv_path, exist_ok=True)
        sce.to_csv(csv_path)
    if excel_path is not None:
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        sce.to_excel(excel_path)

    return paths(xls=excel_path, csv=csv_path)


if __name__ == "__main__":
    from deflex.geometries import deflex_regions, deflex_power_lines
    from oemof.tools import logger

    logger.define_logging(screen_level=logging.DEBUG)
    de02 = deflex_regions(rmap="de02", rtype="polygons")
    de02_lines = deflex_power_lines("de02")
    create_basic_scenario(
        2013, "myde02", de02, de02_lines, excel_path="/home/uwe/de02_test.xls"
    )
