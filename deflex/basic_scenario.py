# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

# Python libraries
import os
import logging
import calendar
from collections import namedtuple

# External libraries
import pandas as pd

# internal modules
from reegis import commodity_sources
from reegis import bmwi
from reegis import storages
from reegis import coastdat
from reegis import demand_elec
from reegis import energy_balance
from reegis import powerplants as reegis_powerplants
from deflex import powerplants
from deflex import demand
from deflex import transmission
from deflex import scenario_tools
from deflex import geometries
from deflex import config as cfg


def create_scenario(
    regions, year, name, round_values=0, weather_year=None, copperplate=False
):
    table_collection = {}

    logging.info("BASIC SCENARIO - STORAGES")
    table_collection["storages"] = scenario_storages(regions, year, name)

    logging.info("BASIC SCENARIO - POWER PLANTS")
    table_collection = scenario_powerplants(
        table_collection, regions, year, name, round_values
    )

    logging.info("BASIC SCENARIO - TRANSMISSION")
    table_collection["transmission"] = scenario_transmission(
        table_collection, regions, name, copperplate=copperplate
    )

    logging.info("BASIC SCENARIO - CHP PLANTS")
    table_collection = scenario_chp(
        table_collection, regions, year, name, weather_year=weather_year
    )

    logging.info("BASIC SCENARIO - DECENTRALISED HEAT")
    table_collection["decentralised_heat"] = scenario_decentralised_heat()

    logging.info("BASIC SCENARIO - SOURCES")
    table_collection = scenario_commodity_sources(table_collection, year)
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
    stor = storages.pumped_hydroelectric_storage_by_region(
        regions, year, name
    ).transpose()
    return pd.concat([stor], axis=1, keys=["phes"]).swaplevel(0, 1, 1)


def scenario_powerplants(table_collection, regions, year, name, round_values):
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
    return create_powerplants(pp, table_collection, year, name, round_values)


def create_powerplants(
    pp,
    table_collection,
    year,
    region_column="deflex_region",
    round_values=None,
):
    """This function works for all power plant tables with an equivalent
    structure e.g. power plants by state or other regions."""
    logging.info("Adding power plants to your scenario.")

    replace_names = cfg.get_dict("source_names")
    replace_names.update(cfg.get_dict("source_groups"))

    pp["energy_source_level_2"].replace(replace_names, inplace=True)

    pp["model_classes"] = pp["energy_source_level_2"].replace(
        cfg.get_dict("model_classes")
    )

    pp = pp.groupby(
        ["model_classes", region_column, "energy_source_level_2"]
    ).sum()[["capacity", "capacity_in"]]

    for model_class in pp.index.get_level_values(level=0).unique():
        pp_class = pp.loc[model_class]
        if model_class != "volatile_source":
            pp_class["efficiency"] = (
                pp_class["capacity"] / pp_class["capacity_in"] * 100
            )
        del pp_class["capacity_in"]
        if round_values is not None:
            pp_class = pp_class.round(round_values)
        if "efficiency" in pp_class:
            pp_class["efficiency"] = pp_class["efficiency"].div(100)
        pp_class = pp_class.transpose()
        pp_class.index.name = "parameter"
        table_collection[model_class] = pp_class
    table_collection = add_pp_limit(table_collection, year)
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
            cap_sum = trsf.loc[
                "capacity", (slice(None), slice(limit_trsf))
            ].sum()
            for region in trsf.columns.get_level_values(level=0).unique():
                trsf.loc["limit_elec_pp", (region, limit_trsf)] = round(
                    trsf.loc["capacity", (region, limit_trsf)]
                    / cap_sum
                    * limit
                    + 0.5
                )

        trsf.loc["limit_elec_pp"] = trsf.loc["limit_elec_pp"].fillna(
            float("inf")
        )

        table_collection["transformer"] = trsf
    return table_collection


def scenario_transmission(table_collection, regions, name, copperplate=False):
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

    if name in ["de21", "de22"] and not copperplate:
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
            vs[offreg].sum().sum() * 1.1
        )

    elec_trans = pd.concat(
        [elec_trans], axis=1, keys=["electrical"]
    ).sort_index(1)
    if cfg.get("init", "map") == "de22" and not copperplate:
        elec_trans.loc["DE22-DE01", ("electrical", "efficiency")] = 0.9999
        elec_trans.loc["DE22-DE01", ("electrical", "capacity")] = 9999999
    return elec_trans


def scenario_commodity_sources(table_collection, year):
    """

    Parameters
    ----------
    year
    table_collection

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
    commodity_src = create_commodity_sources(year)
    commodity_src = commodity_src.swaplevel().unstack()

    msg = (
        "The unit for {0} of the source is '{1}'. "
        "Will multiply it with {2} to get '{3}'."
    )

    converter = {
        "costs": ["costs", "EUR/J", 1e9 * 3.6, "EUR/MWh"],
        "emission": ["emission", "g/J", 1e6 * 3.6, "kg/MWh"],
    }

    transformer_list = (
        table_collection["transformer"]
        .columns.get_level_values(level=1)
        .unique()
    )

    # Delete unused sources
    for col in commodity_src.columns:
        if col not in transformer_list:
            del commodity_src[col]

    # convert units
    for key in converter.keys():
        commodity_src.loc[key] = commodity_src.loc[key].multiply(
            converter[key][2]
        )
        logging.warning(msg.format(*converter[key]))

    # Add region level to be consistent to other tables
    commodity_src.columns = pd.MultiIndex.from_product(
        [["DE"], commodity_src.columns]
    )

    table_collection["commodity_source"] = commodity_src
    return table_collection


def create_commodity_sources(year, use_znes_2014=True):
    """

    Parameters
    ----------
    year
    use_znes_2014

    Returns
    -------

    """
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
    cs_year.sort_index(inplace=True)
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
    return pd.read_csv(filename, header=[0, 1], index_col=[0])


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
    trsf = table_collection["transformer"]
    trsf = trsf.fillna(0)

    rows = ["Heizkraftwerke der allgemeinen Versorgung (nur KWK)", "Heizwerke"]
    if regions is None:
        regions = sorted(heat_b.keys())

    logging.info("start")
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

        for fuel in share.columns:
            if fuel == "gas":
                src = "natural gas"
            else:
                src = fuel

            # CHP
            trsf.loc["limit_heat_chp", (region, src)] = round(
                sum_val * share.loc[rows[0], fuel] * out_share_factor_chp + 0.5
            )
            cap_heat_chp = round(
                max_val * share.loc[rows[0], fuel] * out_share_factor_chp
                + 0.005,
                2,
            )
            trsf.loc["capacity_heat_chp", (region, src)] = cap_heat_chp
            cap_elec = cap_heat_chp / eta_heat_chp * eta_elec_chp
            trsf.loc["capacity_elec_chp", (region, src)] = round(cap_elec, 2)
            trsf[region] = trsf[region].fillna(0)
            trsf.loc["capacity", (region, src)] = round(
                trsf.loc["capacity", (region, src)] - cap_elec
            )

            # If the power plant limit is not 'inf' the limited electricity
            # output of the chp plant has to be subtracted from the power plant
            # limit because this is related to the overall electricity output.
            if not trsf.loc["limit_elec_pp", (region, src)] == float("inf"):
                trsf.loc["limit_elec_pp", (region, src)] -= round(
                    trsf.loc["limit_heat_chp", (region, src)]
                    / eta_heat_chp
                    * eta_elec_chp
                )

            # HP
            trsf.loc["limit_hp", (region, src)] = round(
                sum_val * share.loc[rows[1], fuel] * out_share_factor_hp + 0.5
            )
            trsf.loc["capacity_hp", (region, src)] = round(
                max_val * share.loc[rows[1], fuel] * out_share_factor_hp
                + 0.005,
                2,
            )
            if trsf.loc["capacity_hp", (region, src)] > 0:
                trsf.loc["efficiency_hp", (region, src)] = eta_hp
            if cap_heat_chp * cap_elec > 0:
                trsf.loc["efficiency_heat_chp", (region, src)] = eta_heat_chp
                trsf.loc["efficiency_elec_chp", (region, src)] = eta_elec_chp

    logging.info("Done")

    trsf.sort_index(axis=1, inplace=True)
    for col in trsf.sum().loc[trsf.sum() == 0].index:
        del trsf[col]
    trsf[trsf < 0] = 0

    table_collection["transformer"] = trsf
    return table_collection


def clean_time_series(table_collection):
    dts = table_collection["demand_series"]
    vts = table_collection["volatile_series"]
    vs = table_collection["volatile_source"]

    regions = list(dts.columns.get_level_values(0).unique())
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
            if vs[reg].get(t) is None or vs[reg].get(t).sum() == 0:
                if vts.get(reg) is not None:
                    if vts[reg].get(t) is not None:
                        msg = (
                            "Removing {0} time series of region {1} "
                            "because installed capacity is {2}"
                        )
                        logging.debug(msg.format(t, reg, vs[reg].get(t)))
                        del vts[reg, t]

    return table_collection


def create_basic_scenario(
    year,
    rmap=None,
    path=None,
    csv_dir=None,
    xls_name=None,
    round_values=None,
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
    round_values : bool
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
    paths = namedtuple("paths", "xls, csv")
    if rmap is not None:
        cfg.tmp_set("init", "map", rmap)
    name = cfg.get("init", "map")
    regions = geometries.deflex_regions(rmap=cfg.get("init", "map"))

    table_collection = create_scenario(regions, year, name, round_values)
    table_collection = clean_time_series(table_collection)
    name = "{0}_{1}_{2}".format("deflex", year, cfg.get("init", "map"))
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
    if not only_out == "csv":
        os.makedirs(path, exist_ok=True)
        sce.to_excel(fullpath.xls)
    if not only_out == "xls":
        os.makedirs(csv_path, exist_ok=True)
        sce.to_csv(fullpath.csv)

    return fullpath


if __name__ == "__main__":
    pass
