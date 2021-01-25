# --> kein reegis nur scenario_builder und den als optional requirement

# --> Nutze try except beim Import von scenariobuilder mit INst. hinweis

# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import json
import logging
import os
from collections import namedtuple

import pandas as pd

from deflex import config as cfg
from deflex import geometries
from deflex import scenario_tools
from deflex import transmission

try:
    from scenario_builder import commodity
    from scenario_builder import demand
    from scenario_builder import feedin
    from scenario_builder import mobility
    from scenario_builder import powerplants
    from scenario_builder import storages
except ModuleNotFoundError:
    scenario_builer = None


def scenario_decentralised_heat():
    """

    Returns
    -------

    """
    filename = os.path.join(
        cfg.get("paths", "data_deflex"), cfg.get("heating", "table")
    )
    return pd.read_csv(filename, header=[0, 1], index_col=[0]).transpose()


def create_scenario(regions, year, name, weather_year=None):
    """

    Parameters
    ----------
    regions
    year
    name
    weather_year

    Returns
    -------

    """
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
    if len(regions) > 1:
        table_collection["transmission"] = transmission.scenario_transmission(
            table_collection, regions, name
        )
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - CHP PLANTS")
    if cfg.get("basic", "heat"):
        table_collection = powerplants.scenario_chp(
            table_collection, regions, year, name, weather_year=weather_year
        )
    logging.info("BASIC SCENARIO - DECENTRALISED HEAT")
    if cfg.get("basic", "heat"):
        table_collection["decentralised_heat"] = scenario_decentralised_heat()
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
        regions, year, name, weather_year=weather_year
    )

    logging.info("BASIC SCENARIO - MOBILITY")
    table_collection = mobility.scenario_mobility(year, table_collection)

    logging.info("ADD META DATA")
    table_collection["meta"] = meta_data(year)
    return table_collection


def meta_data(year):
    meta = pd.DataFrame.from_dict(
        cfg.get_dict("basic"), orient="index", columns=["value"]
    )
    meta.loc["year"] = year
    meta.loc["map"] = cfg.get("init", "map")

    # Create name
    if cfg.get("basic", "heat"):
        heat = "heat"
    else:
        heat = "no-heat"
    if cfg.get("basic", "group_transformer"):
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
                        "Removing {0} time series of region {1} because"
                        "sum of time series is {2}"
                    )
                    logging.debug(msg.format(load, reg, dts[reg, load].sum()))
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
                            "Removing {0} time series of region {1} "
                            "because installed capacity is {2}"
                        )
                        logging.debug(msg.format(t, reg, vs.loc[reg].get(t)))
                        vts.drop((reg, t), axis=1, inplace=True)

    return table_collection


def create_basic_scenario(
    year,
    rmap=None,
    path=None,
    csv_dir=None,
    xls_name=None,
    only_out=None,
):
    """
    Create a basic scenario for a given year and region-set.

    Parameters
    ----------
    year : int
    rmap : str
    path : str
    csv_dir : str
    xls_name : str
    only_out : str

    Returns
    -------
    namedtuple : Path

    Examples
    --------
    >>> year=2014  # doctest: +SKIP
    >>> my_rmap="de21"  # doctest: +SKIP
    >>> p=create_basic_scenario(year, rmap=my_rmap)  # doctest: +SKIP
    >>> print("Xls path: {0}".format(p.xls))  # doctest: +SKIP
    >>> print("Csv path: {0}".format(p.csv))  # doctest: +SKIP

    """
    configuration = json.dumps(cfg.get_dict("basic"), indent=4, sort_keys=True)
    logging.info(
        "The following configuration is used to build the scenario:"
        " {0}".format(configuration)
    )
    paths = namedtuple("paths", "xls, csv")
    if rmap is not None:
        cfg.tmp_set("init", "map", rmap)

    regions = geometries.deflex_regions(rmap=cfg.get("init", "map"))

    table_collection = create_scenario(regions, year, cfg.get("init", "map"))

    table_collection = clean_time_series(table_collection)

    name = table_collection["meta"].loc["name", "value"]
    sce = scenario_tools.Scenario(
        table_collection=table_collection, name=name, year=year
    )

    if path is None:
        path = os.path.join(cfg.get("paths", "scenario"), "deflex", str(year))

    if only_out == "xls":
        csv_path = None
    elif csv_dir is None:
        csv_path = os.path.join(path, "{0}_csv".format(name))
    else:
        csv_path = os.path.join(path, csv_dir)

    if only_out == "csv":
        xls_path = None
    elif xls_name is None:
        xls_path = os.path.join(path, name + ".xls")
    else:
        xls_path = os.path.join(path, xls_name)
    fullpath = paths(xls=xls_path, csv=csv_path)
    if not only_out == "xls":
        os.makedirs(csv_path, exist_ok=True)
        sce.to_csv(fullpath.csv)
    if not only_out == "csv":
        os.makedirs(path, exist_ok=True)
        sce.to_excel(fullpath.xls)

    return fullpath


if __name__ == "__main__":
    pass
