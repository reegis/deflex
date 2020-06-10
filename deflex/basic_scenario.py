# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import calendar
import json
import logging
import os
from collections import namedtuple
from warnings import warn

import pandas as pd

from deflex import analyses
from deflex import config as cfg
from deflex import (
    demand,
    geometries,
    powerplants,
    scenario_tools,
    transmission,
)
from reegis import (
    bmwi,
    coastdat,
    commodity_sources,
    demand_elec,
    energy_balance,
)
from reegis import powerplants as reegis_powerplants
from reegis import storages


def create_scenario(regions, year, name, weather_year=None):
    table_collection = {}

    logging.info("BASIC SCENARIO - STORAGES")
    table_collection["storages"] = scenario_storages(regions, year, name)

    logging.info("BASIC SCENARIO - POWER PLANTS")
    table_collection = scenario_powerplants(
        table_collection, regions, year, name
    )

    logging.info("BASIC SCENARIO - TRANSMISSION")
    if len(regions) > 1:
        table_collection["transmission"] = scenario_transmission(
            table_collection, regions, name
        )
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - CHP PLANTS")
    if cfg.get("basic", "heat"):
        table_collection = scenario_chp(
            table_collection, regions, year, name, weather_year=weather_year
        )
    logging.info("BASIC SCENARIO - DECENTRALISED HEAT")
    if cfg.get("basic", "heat"):
        table_collection["decentralised_heat"] = scenario_decentralised_heat()
    else:
        logging.info("...skipped")

    logging.info("BASIC SCENARIO - SOURCES")
    table_collection["commodity_source"] = scenario_commodity_sources(year)
    table_collection["volatile_series"] = scenario_feedin(
        regions, year, name, weather_year=weather_year
    )

    logging.info("BASIC SCENARIO - DEMAND")
    table_collection["demand_series"] = scenario_demand(
        regions, year, name, weather_year=weather_year
    )
    return table_collection


def scenario_storages(regions, year, name):
    """
    Fetch storage, pump and turbine capacity and their efficiency of
    hydroelectric storages for each deflex region.

    Parameters
    ----------
    regions
    year
    name

    Returns
    -------

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de17')
    >>> deflex_storages=scenario_storages(regions, 2012, 'de17')
    >>> list(deflex_storages.columns.get_level_values(0))
    ['DE01', 'DE03', 'DE05', 'DE06', 'DE08', 'DE09', 'DE14', 'DE15', 'DE16']
    >>> int(deflex_storages.loc['turbine', 'DE03'])
    220
    >>> int(deflex_storages.loc['energy', 'DE16'])
    12115
    """
    stor = storages.pumped_hydroelectric_storage_by_region(regions, year, name)
    return pd.concat([stor], keys=["phes"]).swaplevel(0, 1)


def scenario_powerplants(table_collection, regions, year, name):
    """Get power plants for the scenario year

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')
    >>> pp=scenario_powerplants(
    ...     dict(), regions, 2014, 'de21', 1)  # doctest: +SKIP
    >>> float(pp['volatile_source']['DE03', 'wind'])  # doctest: +SKIP
    3052.8
    >>> float(pp['transformer'].loc[
    ...     'capacity', ('DE03', 'lignite')])  # doctest: +SKIP
    1135.6
    """
    pp = powerplants.get_deflex_pp_by_year(
        regions, year, name, overwrite_capacity=True
    )
    return create_powerplants(pp, table_collection, year, name)


def create_powerplants(
    pp, table_collection, year, region_column="deflex_region"
):
    """This function works for all power plant tables with an equivalent
    structure e.g. power plants by state or other regions."""
    logging.info("Adding power plants to your scenario.")

    replace_names = cfg.get_dict("source_names")

    # TODO Waste is not "other"
    replace_names.update(cfg.get_dict("source_groups"))
    pp["count"] = 1
    pp["energy_source_level_2"].replace(replace_names, inplace=True)

    pp["model_classes"] = pp["energy_source_level_2"].replace(
        cfg.get_dict("model_classes")
    )

    power_plants = {
        "volatile_source": pp.groupby(
            ["model_classes", region_column, "energy_source_level_2"]
        )
        .sum()[["capacity", "count"]]
        .loc["volatile_source"]
    }

    if cfg.get("basic", "group_transformer") is True:
        power_plants["transformer"] = (
            pp.groupby(
                ["model_classes", region_column, "energy_source_level_2"]
            )
            .sum()[["capacity", "capacity_in", "count"]]
            .loc["transformer"]
        )
        power_plants["transformer"]["fuel"] = power_plants[
            "transformer"
        ].index.get_level_index(1)
    else:
        pp["efficiency"] = pp["efficiency"].round(2)
        power_plants["transformer"] = (
            pp.groupby(
                [
                    "model_classes",
                    region_column,
                    "energy_source_level_2",
                    "efficiency",
                ]
            )
            .sum()[["capacity", "capacity_in", "count"]]
            .loc["transformer"]
        )
        power_plants["transformer"]["fuel"] = power_plants[
            "transformer"
        ].index.get_level_values(1)
        power_plants["transformer"].index = [
            power_plants["transformer"].index.get_level_values(0),
            power_plants["transformer"].index.map("{0[1]} - {0[2]}".format),
        ]

    for class_name, pp_class in power_plants.items():
        if "capacity_in" in pp_class:
            pp_class["efficiency"] = (
                pp_class["capacity"] / pp_class["capacity_in"] * 100
            )
            del pp_class["capacity_in"]
        if cfg.get("basic", "round") is not None:
            pp_class = pp_class.round(cfg.get("basic", "round"))
        if "efficiency" in pp_class:
            pp_class["efficiency"] = pp_class["efficiency"].div(100)
        pp_class = pp_class.transpose()
        pp_class.index.name = "parameter"
        table_collection[class_name] = pp_class.transpose()
    table_collection = add_pp_limit(table_collection, year)
    table_collection = add_additional_values(table_collection)
    return table_collection


def add_additional_values(table_collection):
    transf = table_collection["transformer"]
    for values in ["variable_costs", "downtime_factor"]:
        if cfg.get("basic", "use_{0}".format(values)) is True:
            add_values = getattr(analyses.download_ewi_data(), values)
            transf = transf.merge(
                add_values, right_index=True, how="left", left_on="fuel",
            )
            transf.drop(["unit", "source"], axis=1, inplace=True)
            transf.rename({"value": values}, axis=1, inplace=True)
        else:
            transf[values] = 0
    table_collection["transformer"] = transf
    return table_collection


def add_pp_limit(table_collection, year):
    """

    Parameters
    ----------
    table_collection
    year

    Returns
    -------

    """
    if len(cfg.get_dict("limited_transformer").keys()) > 0:
        # Multiply with 1000 to get MWh (bmwi: GWh)
        repp = bmwi.bmwi_re_energy_capacity() * 1000
        trsf = table_collection["transformer"]
        for limit_trsf in cfg.get_dict("limited_transformer").keys():
            trsf = table_collection["transformer"]
            try:
                limit = repp.loc[year, (limit_trsf, "energy")]
            except KeyError:
                msg = "Cannot calculate limit for {0} in {1}."
                raise ValueError(msg.format(limit_trsf, year))
            cond = trsf["fuel"] == limit_trsf
            cap_sum = trsf.loc[pd.Series(cond)[cond].index, "capacity"].sum()
            trsf.loc[pd.Series(cond)[cond].index, "limit_elec_pp"] = (
                trsf.loc[pd.Series(cond)[cond].index, "capacity"]
                .div(cap_sum)
                .multiply(limit)
                + 0.5
            )
        trsf["limit_elec_pp"] = trsf["limit_elec_pp"].fillna(
            float("inf")
        )

        table_collection["transformer"] = trsf
    return table_collection


def scenario_transmission(table_collection, regions, name):
    """Get power plants for the scenario year

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')  # doctest: +SKIP
    >>> pp=scenario_powerplants(dict(), regions, 2014, 'de21', 1
    ...     )  # doctest: +SKIP
    >>> lines=scenario_transmission(pp, regions, 'de21')  # doctest: +SKIP
    >>> int(lines.loc['DE07-DE05', ('electrical', 'capacity')]
    ...     )  # doctest: +SKIP
    1978
    >>> int(lines.loc['DE07-DE05', ('electrical', 'distance')]
    ...     )  # doctest: +SKIP
    199
    >>> float(lines.loc['DE07-DE05', ('electrical', 'efficiency')]
    ...     )  # doctest: +SKIP
    0.9
    >>> lines=scenario_transmission(pp, regions, 'de21', copperplate=True
    ...     )  # doctest: +SKIP
    >>> float(lines.loc['DE07-DE05', ('electrical', 'capacity')]
    ...     )  # doctest: +SKIP
    inf
    >>> float(lines.loc['DE07-DE05', ('electrical', 'distance')]
    ...     )  # doctest: +SKIP
    nan
    >>> float(lines.loc['DE07-DE05', ('electrical', 'efficiency')]
    ...     )  # doctest: +SKIP
    1.0
    """
    vs = table_collection["volatile_source"]

    # This should be done automatic e.g. if representative point outside the
    # landmass polygon.
    offshore_regions = geometries.divide_off_and_onshore(regions).offshore

    if name in ["de21", "de22"] and not cfg.get("basic", "copperplate"):
        elec_trans = transmission.get_electrical_transmission_renpass()
        general_efficiency = cfg.get("transmission", "general_efficiency")
        if general_efficiency is not None:
            elec_trans["efficiency"] = general_efficiency
        else:
            msg = (
                "The calculation of the efficiency by distance is not yet "
                "implemented"
            )
            raise NotImplementedError(msg)
    else:
        elec_trans = transmission.get_electrical_transmission_default()

    # Set transmission capacity of offshore power lines to installed capacity
    # Multiply the installed capacity with 1.1 to get a buffer of 10%.
    for offreg in offshore_regions:
        elec_trans.loc[elec_trans.index.str.contains(offreg), "capacity"] = (
            vs.loc[offreg].sum().sum() * 1.1
        )

    elec_trans = pd.concat(
        [elec_trans], axis=1, keys=["electrical"]
    ).sort_index(1)
    if cfg.get("init", "map") == "de22" and not cfg.get(
        "basic", "copperplate"
    ):
        elec_trans.loc["DE22-DE01", ("electrical", "efficiency")] = 0.9999
        elec_trans.loc["DE22-DE01", ("electrical", "capacity")] = 9999999
    return elec_trans


def scenario_commodity_sources(year):
    """

    Parameters
    ----------
    year

    Returns
    -------

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')  # doctest: +SKIP
    >>> pp=scenario_powerplants(dict(), regions, 2014, 'de21', 1
    ...     )  # doctest: +SKIP
    >>> src=scenario_commodity_sources(pp, 2014)  # doctest: +SKIP
    >>> src=src['commodity_source']  # doctest: +SKIP
    >>> round(src.loc['costs', ('DE', 'hard coal')], 2)  # doctest: +SKIP
    8.93
    >>> round(src.loc['emission',  ('DE', 'natural gas')], 2)  # doctest: +SKIP
    201.24
    """
    if cfg.get("basic", "costs_source") == "reegis":
        commodity_src = create_commodity_sources_reegis(year)
    elif cfg.get("basic", "costs_source") == "ewi":
        commodity_src = create_commodity_sources_ewi()
    else:
        commodity_src = None

    commodity_src = commodity_src.transpose()

    # Add region level to be consistent to other tables
    commodity_src.columns = pd.MultiIndex.from_product(
        [["DE"], commodity_src.columns]
    )

    return commodity_src.transpose()


def create_commodity_sources_ewi():
    ewi = analyses.download_ewi_data()
    df = pd.DataFrame()
    df["costs"] = ewi.fuel_costs["value"] + ewi.transport_costs["value"]
    df["emission"] = ewi.emission["value"].multiply(1000)
    df["co2_price"] = float(ewi.co2_price["value"])
    missing = "bioenergy"
    msg = (
        "Costs/Emission for {0} in ewi is missing.\n"
        "Values for {0} are hard coded! Use with care."
    )
    warn(msg.format(missing), UserWarning)
    df.loc[missing, "emission"] = 7.2
    df.loc[missing, "costs"] = 20
    df.loc[missing, "co2_price"] = df.loc["natural gas", "co2_price"]
    return df


def create_commodity_sources_reegis(year, use_znes_2014=True):
    """

    Parameters
    ----------
    year
    use_znes_2014

    Returns
    -------

    """
    msg = (
        "The unit for {0} of the source is '{1}'. "
        "Will multiply it with {2} to get '{3}'."
    )

    converter = {
        "costs": ["costs", "EUR/J", 1e9 * 3.6, "EUR/MWh"],
        "emission": ["emission", "g/J", 1e6 * 3.6, "kg/MWh"],
    }

    cs = commodity_sources.get_commodity_sources()
    rename_cols = {
        key.lower(): value
        for key, value in cfg.get_dict("source_names").items()
    }
    cs = cs.rename(columns=rename_cols)
    cs_year = cs.loc[year]
    if use_znes_2014:
        before = len(cs_year[cs_year.isnull()])
        cs_year = cs_year.fillna(cs.loc[2014])
        after = len(cs_year[cs_year.isnull()])
        if before - after > 0:
            logging.warning("Values were replaced with znes2014 data.")
    cs_year = cs_year.sort_index().unstack()

    # convert units
    for key in converter.keys():
        cs_year[key] = cs_year[key].multiply(converter[key][2])
        logging.warning(msg.format(*converter[key]))

    return cs_year


def scenario_demand(regions, year, name, weather_year=None):
    """

    Parameters
    ----------
    regions
    year
    name
    weather_year

    Returns
    -------

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')  # doctest: +SKIP
    >>> my_demand=scenario_demand(regions, 2014, 'de21')  # doctest: +SKIP
    >>> int(my_demand['DE01', 'district heating'].sum())  # doctest: +SKIP
    18639262
    >>> int(my_demand['DE05', 'electrical_load'].sum())  # doctest: +SKIP
    10069

    """
    demand_series = scenario_elec_demand(
        pd.DataFrame(), regions, year, name, weather_year=weather_year
    )
    if cfg.get("basic", "heat"):
        demand_series = scenario_heat_demand(
            demand_series, regions, year, weather_year=weather_year
        )
    return demand_series


def scenario_heat_demand(table, regions, year, weather_year=None):
    idx = table.index  # Use the index of the existing time series
    table = pd.concat(
        [
            table,
            demand.get_heat_profiles_deflex(
                regions, year, idx, weather_year=weather_year
            ),
        ],
        axis=1,
    )
    return table.sort_index(1)


def scenario_elec_demand(table, regions, year, name, weather_year=None):
    if weather_year is None:
        demand_year = year
    else:
        demand_year = weather_year

    df = demand_elec.get_entsoe_profile_by_region(
        regions, demand_year, name, annual_demand="bmwi"
    )
    df = pd.concat([df], axis=1, keys=["electrical_load"]).swaplevel(0, 1, 1)
    df = df.reset_index(drop=True)
    if not calendar.isleap(year) and len(df) > 8760:
        df = df.iloc[:8760]
    return pd.concat([table, df], axis=1).sort_index(1)


def scenario_feedin(regions, year, name, weather_year=None):
    """

    Parameters
    ----------
    regions
    year
    name
    weather_year

    Returns
    -------

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')  # doctest: +SKIP
    >>> f=scenario_feedin(regions, 2014, 'de21')  # doctest: +SKIP
    >>> f['DE01'].sum()  # doctest: +SKIP
    geothermal    4380.000000
    hydro         1346.632529
    solar          913.652083
    wind          2152.983589
    dtype: float64
    >>> f['DE16'].sum()  # doctest: +SKIP
    geothermal    4380.000000
    hydro         1346.632529
    solar          903.527200
    wind          1753.673492
    dtype: float64
    """
    wy = weather_year
    try:
        feedin = coastdat.scenario_feedin(year, name, weather_year=wy)
    except FileNotFoundError:
        coastdat.get_feedin_per_region(year, regions, name, weather_year=wy)
        feedin = coastdat.scenario_feedin(year, name, weather_year=wy)
    return feedin


def scenario_decentralised_heat():
    filename = os.path.join(
        cfg.get("paths", "data_deflex"), cfg.get("heating", "table")
    )
    return pd.read_csv(filename, header=[0, 1], index_col=[0]).transpose()


def scenario_chp(table_collection, regions, year, name, weather_year=None):
    """

    Parameters
    ----------
    table_collection
    regions
    year
    name
    weather_year

    Returns
    -------

    Examples
    --------
    >>> regions=geometries.deflex_regions(rmap='de21')  # doctest: +SKIP
    >>> pp=scenario_powerplants(dict(), regions, 2014, 'de21', 1
    ...     )  # doctest: +SKIP
    >>> int(pp['transformer'].loc['capacity', ('DE01', 'hard coal')]
    ...     )  # doctest: +SKIP
    1291
    >>> transf=scenario_chp(pp, regions, 2014, 'de21')  # doctest: +SKIP
    >>> transf=transf['transformer']  # doctest: +SKIP
    >>> int(transf.loc['capacity', ('DE01', 'hard coal')])  # doctest: +SKIP
    485
    >>> int(transf.loc['capacity_elec_chp', ('DE01', 'hard coal')]
    ...     )  # doctest: +SKIP
    806
    """
    # values from heat balance

    cb = energy_balance.get_transformation_balance_by_region(
        regions, year, name
    )
    cb.rename(columns={"re": cfg.get("chp", "renewable_source")}, inplace=True)
    heat_b = reegis_powerplants.calculate_chp_share_and_efficiency(cb)

    heat_demand = demand.get_heat_profiles_deflex(
        regions, year, weather_year=weather_year
    )
    return chp_table(heat_b, heat_demand, table_collection)


def chp_table(heat_b, heat_demand, table_collection, regions=None):

    chp_hp = pd.DataFrame(
        columns=pd.MultiIndex(levels=[[], []], codes=[[], []])
    )

    rows = ["Heizkraftwerke der allgemeinen Versorgung (nur KWK)", "Heizwerke"]
    if regions is None:
        regions = sorted(heat_b.keys())

    eta_heat_chp = None
    eta_elec_chp = None

    for region in regions:
        eta_hp = round(heat_b[region]["sys_heat"] * heat_b[region]["hp"], 2)
        eta_heat_chp = round(
            heat_b[region]["sys_heat"] * heat_b[region]["heat_chp"], 2
        )
        eta_elec_chp = round(heat_b[region]["elec_chp"], 2)

        # Due to the different efficiency between heat from chp-plants and
        # heat from heat-plants the share of the output is different to the
        # share of the input. As heat-plants will produce more heat per fuel
        # factor will be greater than 1 and for chp-plants smaller than 1.
        out_share_factor_chp = heat_b[region]["out_share_factor_chp"]
        out_share_factor_hp = heat_b[region]["out_share_factor_hp"]

        # Remove 'district heating' and 'electricity' and spread the share
        # to the remaining columns.
        share = pd.DataFrame(columns=heat_b[region]["fuel_share"].columns)
        for row in rows:
            tmp = heat_b[region]["fuel_share"].loc[region, :, row]
            tot = float(tmp["total"])

            d = float(tmp["district heating"] + tmp["electricity"])
            tmp = tmp + tmp / (tot - d) * d
            tmp = tmp.reset_index(drop=True)
            share.loc[row] = tmp.loc[0]
        del share["district heating"]
        del share["electricity"]

        # Remove the total share
        del share["total"]

        max_val = float(heat_demand[region]["district heating"].max())
        sum_val = float(heat_demand[region]["district heating"].sum())

        share = share.rename({"gas": "natural gas"}, axis=1)

        for fuel in share.columns:
            # CHP
            chp_hp.loc["limit_heat_chp", (region, fuel)] = round(
                sum_val * share.loc[rows[0], fuel] * out_share_factor_chp + 0.5
            )
            cap_heat_chp = round(
                max_val * share.loc[rows[0], fuel] * out_share_factor_chp
                + 0.005,
                2,
            )
            chp_hp.loc["capacity_heat_chp", (region, fuel)] = cap_heat_chp
            cap_elec = cap_heat_chp / eta_heat_chp * eta_elec_chp
            chp_hp.loc["capacity_elec_chp", (region, fuel)] = round(
                cap_elec, 2
            )
            chp_hp[region] = chp_hp[region].fillna(0)

            # HP
            chp_hp.loc["limit_hp", (region, fuel)] = round(
                sum_val * share.loc[rows[1], fuel] * out_share_factor_hp + 0.5
            )
            chp_hp.loc["capacity_hp", (region, fuel)] = round(
                max_val * share.loc[rows[1], fuel] * out_share_factor_hp
                + 0.005,
                2,
            )
            if chp_hp.loc["capacity_hp", (region, fuel)] > 0:
                chp_hp.loc["efficiency_hp", (region, fuel)] = eta_hp
            if cap_heat_chp * cap_elec > 0:
                chp_hp.loc[
                    "efficiency_heat_chp", (region, fuel)
                ] = eta_heat_chp
                chp_hp.loc[
                    "efficiency_elec_chp", (region, fuel)
                ] = eta_elec_chp
            chp_hp.loc["fuel", (region, fuel)] = fuel

    logging.info("Done")

    chp_hp.sort_index(axis=1, inplace=True)

    # for col in trsf.sum().loc[trsf.sum() == 0].index:
    #     del trsf[col]
    # trsf[trsf < 0] = 0

    table_collection["chp_hp"] = chp_hp.transpose()

    table_collection = substract_chp_capacity_and_limit_from_pp(
        table_collection, eta_heat_chp, eta_elec_chp)

    return table_collection


def substract_chp_capacity_and_limit_from_pp(tc, eta_heat_chp, eta_elec_chp):
    chp_hp = tc["chp_hp"]
    pp = tc["transformer"]
    diff = 0
    for region in chp_hp.index.get_level_values(0).unique():
        for fuel in chp_hp.loc[region].index:
            # If the power plant limit is not 'inf' the limited electricity
            # output of the chp plant has to be subtracted from the power plant
            # limit because this is related to the overall electricity output.
            limit_elec_pp = pp.loc[
                (pp.index.get_level_values(0) == region) &
                (pp.fuel == fuel), "limit_elec_pp"
            ].sum()
            if not limit_elec_pp == float("inf"):
                limit_elec_chp = (
                    chp_hp.loc[(region, fuel), "limit_heat_chp"]
                    / eta_heat_chp
                    * eta_elec_chp
                )
                factor = 1 - limit_elec_chp/limit_elec_pp
                pp.loc[
                    (pp.index.get_level_values(0) == region) &
                    (pp.fuel == fuel), "limit_elec_pp"
                ] *= factor

            # Substract the electric capacity of the chp from the capacity
            # of the power plant.
            capacity_elec_pp = pp.loc[
                (pp.index.get_level_values(0) == region) &
                (pp.fuel == fuel), "capacity"
            ].sum()
            capacity_elec_chp = chp_hp.loc[(region, fuel), "capacity_elec_chp"]
            if capacity_elec_chp < capacity_elec_pp:
                factor = 1 - capacity_elec_chp/capacity_elec_pp
            elif capacity_elec_chp == capacity_elec_pp:
                factor = 0
            else:
                factor = 0
                diff += capacity_elec_chp - capacity_elec_pp
                msg = ("Electricity capacity of chp plant it greater than "
                       "existing electricity capacity in one region.\n"
                       "Region: {0}, capacity_elec: {1}, capacity_elec_chp: "
                       "{2}, fuel: {3}")
                warn(msg.format(
                        region, capacity_elec_pp, capacity_elec_chp, fuel),
                     UserWarning)
            pp.loc[
                    (pp.index.get_level_values(0) == region) &
                    (pp.fuel == fuel), "capacity"
                ] *= factor
    if diff > 0:
        msg = ("Electricity capacity of some chp plants it greater than "
               "existing electricity capacity.\n"
               "Overall difference: {0}")
        warn(msg.format(diff), UserWarning)
    return tc


def clean_time_series(table_collection):
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
            # if the column does not exist or is 0 the corresponding column
            # of the time_series table can be removed.
            if vs.loc[reg].get(t) is None or vs.loc[reg].get(t).sum() == 0:
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
    year, rmap=None, path=None, csv_dir=None, xls_name=None, only_out=None,
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
    >>> my_rmap='de21'  # doctest: +SKIP
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
    name = cfg.get("init", "map")
    regions = geometries.deflex_regions(rmap=cfg.get("init", "map"))

    table_collection = create_scenario(regions, year, name)
    table_collection = clean_time_series(table_collection)

    # Create name
    if cfg.get("basic", "heat"):
        heat = "heat"
    else:
        heat = "no-heat"
    if cfg.get("basic", "group_transformer"):
        merit = "no-reg-merit"
    else:
        merit = "reg-merit"
    name = "{0}_{1}_{2}_{3}_{4}".format(
        "deflex", year, cfg.get("init", "map"), heat, merit
    )
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
