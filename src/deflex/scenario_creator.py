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
from reegis import config
from scenario_builder import commodity
from scenario_builder import demand
from scenario_builder import feedin
from scenario_builder import mobility
from scenario_builder import powerplants
from scenario_builder import storages

from deflex import __file__ as dfile
from deflex import config as cfg
from deflex import scenario_tools
from deflex import transmission


def scenario_default_decentralised_heat():
    """

    Returns
    -------

    """
    df = pd.DataFrame(index=pd.MultiIndex(levels=[[], []], codes=[[], []]))
    fuels = [
        ("gas", "natural gas"),
        ("hard coal", "hard_coal"),
        ("lignite", "lignite"),
        ("natural gas", "natural gas"),
        ("oil", "oil"),
        ("other", "other"),
        ("re", "other"),
    ]
    for fuel, source in fuels:
        df.loc[("DE_demand", fuel), "efficiency"] = 0.85
        df.loc[("DE_demand", fuel), "source"] = source

    return df


def create_scenario(regions, year, name, lines, opsd_version=None):
    """

    Parameters
    ----------
    regions
    year
    name
    lines : iterable[str]
        A list of names of transmission lines. All name must contain a dash
        between the id of the regions (FromRegion-ToRegion).
    opsd_version

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
    pp = powerplants.scenario_powerplants(
        table_collection, regions, year, name
    )
    table_collection["volatile_source"] = pp["volatile_source"]
    table_collection["transformer"] = pp["transformer"]

    logging.info("BASIC SCENARIO - TRANSMISSION")
    print("******************", name)
    if len(regions) > 1:
        table_collection["transmission"] = transmission.scenario_transmission(
            regions, name, lines
        )
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - CHP PLANTS")
    if cfg.get("creator", "heat"):
        chp = powerplants.scenario_chp(table_collection, regions, year, name)
        table_collection["chp_hp"] = chp["chp_hp"]
        table_collection["transformer"] = chp["transformer"]
    else:
        logging.info("...skipped")

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
        regions, year, name
    )

    logging.info("BASIC SCENARIO - DEMAND")
    table_collection["demand_series"] = demand.scenario_demand(
        regions,
        year,
        name,
        opsd_version=opsd_version,
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
    meta.loc["map"] = cfg.get("creator", "map")

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
        "deflex", year, cfg.get("creator", "map"), heat, merit
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


def create_basic_reegis_scenario(
    name,
    regions,
    parameter,
    lines=None,
    csv_path=None,
    excel_path=None,
):
    """
    Create a basic scenario for a given year and region-set.

    Parameters
    ----------
    name : str
        Name of the scenario
    regions : geopandas.geoDataFrame
        Set of region polygons.
    lines : geopandas.geoDataFrame
        Set of transmission lines.
    parameter : dict
        Parameter set for the creation process. Some parameters will have a
        default value. See the list of default values:
            * copperplate: True
            * default_transmission_efficiency: 0.9
            * costs_source: "ewi"
            * downtime_bioenergy: 0.1
            * group_transformer: False
            * heat: False
            * limited_transformer: "bioenergy",
            * local_fuels: "district heating",
            * map: "de02",
            * mobility_other: "petrol",
            * round: 1,
            * separate_heat_regions: "de22",
            * use_CO2_costs: False,
            * use_downtime_factor: True,
            * use_variable_costs: False,
            * year: 2014
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

    Notes
    -----

    }

    Examples
    --------
    >>> from oemof.tools import logger
    >>> from deflex.geometries import deflex_power_lines
    >>> from deflex.geometries import deflex_regions
    >>>
    >>> logger.define_logging(screen_level=logging.DEBUG)  # doctest: +SKIP
    >>>
    >>> my_parameter = {
    ...     "year": 2014,
    ...     "map": "de02",
    ...     "copperplate": True,
    ...     "heat": True,
    ... }
    >>>
    >>> my_name = "deflex"
    >>> for k, v in my_parameter.items():
    ...     my_name += "_" + str(k) + "-" + str(v)
    >>>
    >>> polygons = deflex_regions(rmap=my_parameter["map"], rtype="polygons")
    >>> my_lines = deflex_power_lines(my_parameter["map"]).index
    >>> path = "/my/path/creator/{0}{1}".format(my_name, "{0}")
    >>>
    >>> create_basic_reegis_scenario(
    ...     name=my_name,
    ...     regions=polygons,
    ...     lines=my_lines,
    ...     parameter=my_parameter,
    ...     excel_path=path.format(".xlsx"),
    ...     csv_path=path.format("_csv"),
    ... )  # doctest: +SKIP
    """
    default = {
        "costs_source": "ewi",
        "downtime_bioenergy": 0.1,
        "limited_transformer": "bioenergy",
        "local_fuels": "district heating",
        "map": "de02",
        "mobility_other": "petrol",
        "round": 1,
        "separate_heat_regions": "de22",
        "copperplate": True,
        "default_transmission_efficiency": 0.9,
        "group_transformer": False,
        "heat": False,
        "use_CO2_costs": False,
        "use_downtime_factor": True,
        "use_variable_costs": False,
        "year": 2014,
    }

    default.update(parameter)
    config.init(paths=[os.path.dirname(dfile)])
    for option, value in default.items():
        cfg.tmp_set("creator", option, str(value))
        config.tmp_set("creator", option, str(value))

    year = cfg.get("creator", "year")

    configuration = json.dumps(
        cfg.get_dict("creator"), indent=4, sort_keys=True
    )

    logging.info(
        "The following configuration is used to build the scenario:" " %s",
        configuration,
    )
    paths = namedtuple("paths", "xls, csv")

    table_collection = create_scenario(regions, year, name, lines)

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
