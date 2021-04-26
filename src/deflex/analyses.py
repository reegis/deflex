# -*- coding: utf-8 -*-

"""
Analyses of deflex.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
from collections import namedtuple

import pandas as pd
from oemof import solph
from pandas.testing import assert_frame_equal


def merit_order_from_scenario(
    scenario, with_downtime=True, with_co2_price=True
):
    """
    Create a merit order from a deflex scenario.

    TODO: Check transmission.
    TODO: Add volatile sources as an optional feature
    TODO: Check chp. Warn if chp are present. Add chp as an option
    TODO: Or warn if no chp are present, installed capacity might be too high

    Parameters
    ----------
    scenario : deflex.Scenario
        Path of the directory where the csv files of the scenario are located.
    with_downtime : bool
        Use down time factor to reduce the installed capacity.
    with_co2_price : bool
        Consider the CO2 price to calculate the merit order.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> import os
    >>> from deflex import DeflexScenario
    >>> from deflex.tools import TEST_PATH
    >>> my_path = os.path.join(TEST_PATH, "de02_no-heat_csv")
    >>> sc = DeflexScenario()
    >>> mo1 = merit_order_from_scenario(sc.read_csv(my_path))
    >>> round(mo1.capacity_cum.iloc[-1], 4)
    86.7028
    >>> round(mo1.capacity.sum(), 1)
    86702.8
    >>> round(mo1.loc[("DE01", "natural gas - 0.55"), "costs_total"], 2)
    49.37
    >>> mo2 = merit_order_from_scenario(sc.read_csv(my_path),
    ...                                 with_downtime=False)
    >>> int(round(mo2.capacity.sum(), 0))
    101405
    >>> mo3 = merit_order_from_scenario(sc.read_csv(my_path),
    ...                                 with_co2_price=False)
    >>> round(mo3.loc[("DE01", "natural gas - 0.55"), "costs_total"], 2)
    43.58

    """
    sc = scenario
    sc.name = sc.input_data["general"].get("name")
    transf = sc.input_data["power plants"]
    num_cols = ["capacity", "variable_costs", "efficiency", "count"]
    transf[num_cols] = transf[num_cols].astype(float)
    if with_downtime and "downtime_factor" in transf:
        transf["capacity"] *= 1 - pd.to_numeric(
            transf["downtime_factor"].fillna(0.1)
        )
    transf = transf.loc[transf["capacity"] != 0]
    my_data = sc.input_data["commodity sources"].loc["DE"]
    my_data["co2_price"] = float(sc.input_data["general"].get("co2 price", 0))
    transf = transf.merge(
        my_data, right_index=True, how="left", left_on="fuel"
    )
    transf.rename(columns={"emission": "fuel_emission"}, inplace=True)
    transf["spec_emission"] = transf["fuel_emission"].div(transf["efficiency"])
    transf["costs_total"] = pd.to_numeric(
        transf["variable_costs"].fillna(1)
    ) + transf["costs"].div(transf["efficiency"])
    if with_co2_price and "co2_price" in transf:
        transf["costs_total"] += transf["co2_price"] * transf[
            "fuel_emission"
        ].div(transf["efficiency"])

    transf.sort_values(["costs_total", "capacity"], inplace=True)
    transf["capacity_cum"] = transf.capacity.cumsum().div(1000)
    return transf


def get_line_inflows(result):
    return [
        x
        for x in result["Main"].keys()
        if isinstance(x[1], solph.Bus)
        and x[1].label.cat == "electricity"
        and not x[0].label.cat == "line"
    ]


def merit_order_from_results(result):
    """
    Create a merit order from deflex results.

    Parameters
    ----------
    result : dict
        A deflex results dictionary.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> from deflex import tools, postprocessing
    >>> fn = tools.fetch_test_files("de02_no-heat.dflx")
    >>> my_results = postprocessing.restore_results(fn)
    >>> a = merit_order_from_results(my_results)
    """
    # TODO: If there is a transmission limit or transmission losses
    #       the merit order cannot be calculated!!!!

    # Fetch all flows into any electricity bus
    inflows = get_line_inflows(result)

    # Create a DataFrame for the costs
    levels = [[], [], [], []]
    values = pd.DataFrame(index=pd.MultiIndex(levels=levels, codes=levels))
    for inflow in inflows:
        label = inflow[0].label

        component = inflow[0]
        electricity_bus = inflow[1]

        # Variable costs of the outflow of the component
        values.loc[label, "variable_costs_out"] = result["Param"][inflow][
            "scalars"
        ].variable_costs

        # Capacity of the component
        values.loc[label, "capacity"] = result["Param"][inflow]["scalars"].get(
            "nominal_value", 10000
        )

        srcbus2component = [
            x
            for x in result["Main"].keys()
            if x[1] == component and x[0] != electricity_bus
        ]

        if len(srcbus2component) > 0:
            srcbus = srcbus2component[0][0]
            # Variable costs of the inflow of the component
            values.loc[label, "variable_costs_in"] = result["Param"][
                srcbus2component[0]
            ]["scalars"].variable_costs

            # Efficiency of the component if component is a transformer.
            parameter_name = "conversion_factors_{0}".format(electricity_bus)
            values.loc[label, "efficiency"] = result["Param"][
                (component, None)
            ]["scalars"][parameter_name]

            src2srcbus = [
                x
                for x in result["Main"].keys()
                if x[1] == srcbus and x[0].label.cat != "shortage"
            ]
            if len(src2srcbus) > 1:
                msg = (
                    "More than one source found for {0}. "
                    "Source costs will be ambiguous."
                )
                raise ValueError(msg.format(srcbus))

            # Variable costs of the fuel source.
            values.loc[label, "fuel_costs"] = result["Param"][src2srcbus[0]][
                "scalars"
            ].variable_costs
            values.loc[label, "fuel_emission"] = result["Param"][
                src2srcbus[0]
            ]["scalars"].emission
            values.loc[label, "fuel"] = src2srcbus[0][0].label.subtag.replace(
                "_", " "
            )
            values.loc[label, "spec_emission"] = (
                values.loc[label, "fuel_emission"]
                / values.loc[label, "efficiency"]
            )
        else:
            values.loc[label, "efficiency"] = 1
            values.loc[label, "variable_costs_in"] = 0
            values.loc[label, "fuel_costs"] = 0
            values.loc[label, "fuel_emission"] = 0
            values.loc[label, "fuel"] = "no fuel"

        values.loc[label, "costs_total"] = (
            values.loc[label, "variable_costs_out"]
            + (
                values.loc[label, "variable_costs_in"]
                + values.loc[label, "fuel_costs"]
            )
            / values.loc[label, "efficiency"]
        )
    values = values.loc[values["fuel"] != "no fuel"]
    values.sort_values(["costs_total", "capacity"], inplace=True)
    values["capacity_cum"] = values.capacity.cumsum().div(1000)
    return values


def check_comparision_of_merit_order(scenario):
    """Comparison of two different ways to calculate the merit order.

    1. Calculate the merit order from scenario
    2. Calculate the merit order from the results

    The resulting tables are not exactly the same because they will have some
    additional columns. The following columns should be the same.

    "capacity", "efficiency", "fuel_emission", "fuel", "costs_total",
    "capacity_cum"

    Parameters
    ----------
    scenario : deflex.Scenario
        Full path of results file.

    Examples
    --------
    >>> from deflex import tools, scenario
    >>> my_path = tools.fetch_test_files("de02_no-heat.dflx")
    >>> sc = scenario.restore_scenario(my_path)
    >>> check_comparision_of_merit_order(sc)
    Check passed! Both merit order DataFrame tables are the same.
    """
    mo_scenario = merit_order_from_scenario(scenario)
    mo_results = merit_order_from_results(scenario.results)

    mo_results.index = mo_scenario.index

    compare_columns = [
        "capacity",
        "efficiency",
        "fuel_emission",
        "spec_emission",
        "fuel",
        "costs_total",
        "capacity_cum",
    ]
    assert_frame_equal(
        mo_scenario[compare_columns], mo_results[compare_columns]
    )
    print("Check passed! Both merit order DataFrame tables are the same.")


def meta_results2series(results):
    meta = results["Meta"]
    meta.pop("solver")
    meta.pop("problem")
    return pd.Series(meta)


def pyomo_results2series(results):
    pyomo = pd.Series(
        index=pd.MultiIndex(levels=[[], []], codes=[[], []]), dtype="object"
    )
    for k, v in dict(results["Solver"][0]).items():
        try:
            pyomo["Solver", k] = v.value
        except AttributeError:
            for k2, v2 in dict(results["Solver"][0][k]).items():
                for k3, v3 in dict(results["Solver"][0][k][k2]).items():
                    pyomo["Solver " + k2, k3] = v3.value
    for k, v in dict(results["Problem"][0]).items():
        pyomo["Problem", k] = v.value

    for k, v in results["Solution"].items():
        pyomo["Solution", k] = v.value
    return pyomo.sort_index()


def storage_results2table(results):
    storages = set(
        [
            k[0]
            for k in results["main"].keys()
            if isinstance(k[0], solph.GenericStorage)
        ]
    )

    levels = [[], [], [], [], []]
    store = pd.DataFrame(columns=pd.MultiIndex(levels=levels, codes=levels))
    for storage in storages:
        for col in results["main"][storage, None]["sequences"].columns:
            store[
                storage.label.cat,
                storage.label.tag,
                storage.label.subtag,
                storage.label.region,
                col,
            ] = results["main"][storage, None]["sequences"][col]
    return store


def bus_flows2tables(results, bus_tags):
    levels = [[], [], [], [], [], [], [], []]
    tables = {}
    for bus_tag in bus_tags:
        seq = pd.DataFrame(columns=pd.MultiIndex(levels=levels, codes=levels))
        if "heat" in bus_tag:
            cat, tag = bus_tag.split("_")
        else:
            cat = bus_tag
            tag = "all"
        buses = set(
            [
                k[0]
                for k in results["main"].keys()
                if isinstance(k[0], solph.Bus)
                and k[0].label.cat == cat
                and k[0].label.tag == tag
            ]
        )
        for c in buses:
            flows = [k for k in results["main"].keys() if k[1] == c]
            flows.extend([k for k in results["main"].keys() if k[0] == c])
            for f in flows:
                seq[
                    f[0].label.cat,
                    f[0].label.tag,
                    f[0].label.subtag,
                    f[0].label.region,
                    f[1].label.cat,
                    f[1].label.tag,
                    f[1].label.subtag,
                    f[1].label.region,
                ] = results["main"][f]["sequences"]["flow"]
        tables[bus_tag] = seq.sort_index(axis=1)

    return tables


def get_all_results(results):
    """
    SOMETHING

    Parameters
    ----------
    results

    Returns
    -------

    """
    bus_tags = set(
        [
            "_".join([k[0].label.cat, k[0].label.tag]).replace("_all", "")
            for k in results["main"].keys()
            if isinstance(k[0], solph.Bus)
        ]
    )

    tables = bus_flows2tables(results, bus_tags)
    tables["storages"] = storage_results2table(results)
    tables["pyomo"] = pyomo_results2series(results)
    tables["meta"] = meta_results2series(results)
    return tables


def allocate_fuel(method, **kwargs):
    """
    Allocate the fuel input of chp plants to the two output flows: heat and
    electricity.

    The following methods are available:

    * Alternative Generation or Finnish Method -> :py:func:`finnish_method`
    * Exergy Method or Carnot Method -> :py:func:`exergy_method`

    Parameters
    ----------
    method : str
        The method to allocate the output flows of chp plants:
        alternative_generation, exergy, iea, efficiency, electricity, heat

    Other Parameters
    ----------------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    eta_c : numeric
        The Carnot factor of the heating system. Mandatory in
        the following functions: exergy

    eta_e_ref : numeric
        The efficiency of the best power plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    eta_th_ref : numeric
        The efficiency of the best heat plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation


    Returns
    -------

    """
    fuel_factors = namedtuple("fuel_factors", ["heat", "electricity"])
    name = "{0} (method: {1})".format(allocate_fuel.__name__, method)

    if method == "alternative_generation" or method == "finnish":
        mandatory = ["eta_e", "eta_th", "eta_e_ref", "eta_th_ref"]
        check_input(name, *mandatory, **kwargs)
        f_elec = finnish_method(**kwargs)
    elif method == "efficiency":
        mandatory = ["eta_e", "eta_th", "eta_c"]
        check_input(name, *mandatory, **kwargs)
        f_elec = efficiency_method(**kwargs)
    elif method == "exergy" or method == "carnot":
        mandatory = ["eta_e", "eta_th", "eta_c"]
        check_input(name, *mandatory, **kwargs)
        f_elec = exergy_method(**kwargs)
    elif method == "iea":
        mandatory = ["eta_e", "eta_th", "eta_c"]
        check_input(name, *mandatory, **kwargs)
        f_elec = iea_method(**kwargs)
    elif method == "electricity":
        f_elec = 1
    elif method == "heat":
        f_elec = 0
    else:
        msg = (
            "Method '{0}' is not implemented to calculate the allocation "
            "factor of chp product flows."
        ).format(method)
        raise NotImplementedError(msg)

    return fuel_factors(heat=(1 - f_elec), electricity=f_elec)


def check_input(name, *mandatory_parameters, **kwargs):
    missing = []
    for arg in mandatory_parameters:
        if arg not in kwargs:
            missing.append(arg)
    if len(missing) > 0:
        msg = "The following parameters are missing for {0}: {1}".format(
            name, ", ".join(missing)
        )
        raise ValueError(msg)


def iea_method(eta_e, eta_th):
    return eta_e * 1 / (eta_e + eta_th)


def efficiency_method(eta_e, eta_th):
    """
    Efficiency Method - a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity

    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    """
    return eta_th * 1 / (eta_e + eta_th)


def finnish_method(eta_e, eta_th, eta_e_ref, eta_th_ref):
    r"""
    Alternative Generation or Finnish Method - a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity

    The allocation factor :math:`\alpha_{el}` of the electricity output is
    calculated as follows:
      .. math::
        \alpha_{el} = \frac{\eta_{el,ref}}{\eta_{el}} \cdot \left(
        \frac{\eta_{el}}{\eta_{el,ref}}+ \frac{\eta_{th}}{ \eta_{th,ref}}
        \right)

    :math:`\alpha_{el}` : Allocation factor of the electricity flow

    :math:`\eta_{el}` : Efficiency of the electricity output in the chp plant

    :math:`\eta_{th}` : Efficiency of the thermal output in the chp plant

    :math:`\eta_{el,ref}` : Efficiency of the reference power plant

    :math:`\eta_{th,ref}` : Efficiency of the reference heat plant


    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    eta_e_ref : numeric
        The efficiency of the best power plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    eta_th_ref : numeric
        The efficiency of the best heat plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    Examples
    --------
    >>> round(finnish_method(0.3, 0.5, 0.5, 0.9), 3)
    0.519

    """
    return (eta_e / eta_e_ref) / (eta_e / eta_e_ref + eta_th / eta_th_ref)


def exergy_method(eta_e, eta_th, eta_c):
    """
    Exergy Method or Carnot Method- a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity



    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    eta_c : numeric
        The Carnot factor of the heating system. Mandatory in
        the following functions: exergy

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    """
    return eta_e / (eta_e + eta_c * eta_th)


def power_bonus(eta):
    return eta


def get_all_nodes_from_results(results):
    keys = sorted(list(results["main"].keys()))
    unique_nodes = []
    for nodes in keys:
        unique_nodes.append(nodes[0])
        if nodes[1] is not None:
            unique_nodes.append(nodes[1])
    return set(unique_nodes)


def nodes2table(results):
    """
    Get a table with all nodes (class, category, tag, subtag, region) from a
    results dictionary.

    Parameters
    ----------
    results : dict

    Returns
    -------
    Table with all nodes : pandas.DataFrame

    Examples
    --------
    >>> from deflex import tools
    >>> from deflex import postprocessing
    >>> fn = tools.fetch_test_files("de03_fictive.dflx")
    >>> my_results = postprocessing.restore_results(fn)
    >>> all_nodes = nodes2table(my_results)
    >>> len(all_nodes)
    220
    >>> all_nodes.to_csv("your/path/file.csv")  # doctest: +SKIP


    """
    unique_nodes = get_all_nodes_from_results(results)
    df = pd.DataFrame()
    n = 0
    for node in unique_nodes:
        solph_class = type(node)
        label = node.label
        n += 1
        df.loc[n, "class"] = str(solph_class).split(".")[-1].replace("'>", "")
        df.loc[n, "cat"] = label.cat
        df.loc[n, "tag"] = label.tag
        df.loc[n, "subtag"] = label.subtag
        df.loc[n, "region"] = label.region
    df.sort_values(by=list(df.columns), inplace=True)
    return df.reset_index(drop=True)


def fetch_converter_with_in_out_flows(results):
    # Select all converters (class Transformer excluding lines)
    transformer_objects = set(
        [
            k[0]
            for k in results["main"].keys()
            if isinstance(k[0], solph.Transformer) and k[0].label.cat != "line"
        ]
    )

    # Create dictionary with all converters and their in- and outflows.
    converter = {}
    for t in transformer_objects:
        converter[t] = {}
        converter[t]["in"] = {}
        converter[t]["out"] = {}

        inflow = [k for k in results["main"].keys() if k[1] == t][0]
        sector = inflow[0].label.subtag
        if sector == "all":
            key = (inflow[0].label.cat, inflow[0].label.region)
        else:
            key = (sector, inflow[0].label.region)
        converter[t]["in"][key] = inflow

        outflows = [k for k in results["main"].keys() if k[0] == t]
        for outflow in outflows:
            converter[t]["out"][
                (outflow[1].label.cat, outflow[1].label.region)
            ] = outflow

    return converter


def get_time_index(results):
    key = list(results["main"].keys())[0]
    return results["main"][key]["sequences"].index


def fetch_parameter_of_commodity_sources(results):
    commodity_sources = [
        k
        for k in results["main"].keys()
        if isinstance(k[0], solph.Source)
        and k[0].label.tag == "commodity"
        and k[0].label.cat != "shortage"
    ]

    parameter = pd.DataFrame(
        index=pd.MultiIndex(levels=[[], []], codes=[[], []])
    )
    for c in commodity_sources:
        for k, v in results["param"][c]["scalars"].items():
            if k != "label":
                parameter.loc[(c[0].label.subtag, c[0].label.region), k] = v
    return parameter


def fetch_volatile_electricity_sources(results):
    """

    Parameters
    ----------
    results

    Returns
    -------
    pandas.DataFrame

    """
    volatile_sources = [
        k
        for k in results["main"].keys()
        if isinstance(k[0], solph.Source) and k[0].label.tag == "volatile"
    ]
    sources = pd.DataFrame(
        columns=pd.MultiIndex(levels=[[], []], codes=[[], []])
    )

    for src in volatile_sources:
        sources[src[0].label.subtag, src[0].label.region] = results["main"][
            src
        ]["sequences"]["flow"]
    return sources


def _calculate_emissions_from_energy_table(table, emissions):
    emission_table = table["in"].mul(emissions)
    emission_table = pd.concat([emission_table], axis=1, keys=["in"])
    emission_table["out", "electricity"] = emission_table["in"].sum(axis=1)
    # exit(0)
    table = pd.concat(
        [table, emission_table],
        axis=1,
        keys=["energy", "emission"],
    )
    return table.sort_index(axis=1)


def calculate_product_fuel_balance(results, chp_method, **kwargs):
    transformer = fetch_converter_with_in_out_flows(results)

    # Create a dictionary of empty tables (pandas.DataFrame) for all sectors
    tables = {}
    mcol = pd.MultiIndex(levels=[[], []], codes=[[], []])
    time_index = get_time_index(results)
    for t, f in transformer.items():
        for k1 in f["out"].keys():
            tables.setdefault(
                k1[0], pd.DataFrame(columns=mcol, index=time_index)
            )
            tables[k1[0]]["out", k1] = 0
            for k2 in f["in"].keys():
                tables[k1[0]]["in", k2] = 0

    # Assign inflows to cumulated product flows (fill empty tables from above)
    for t, f in transformer.items():
        # fuel_factor = {}
        if len(f["out"]) == 1:
            fuel_factors = allocate_fuel(list(f["out"].keys())[0][0])
        else:
            fuel_factors = allocate_fuel(method=chp_method, **kwargs)
            # fuel_factor["heat"] = fuel_factors.heat
            # fuel_factor["electricity"] = 1 - fuel_factors.electricity
        for sector, outflow in f["out"].items():
            tables[sector[0]]["out", sector] += results["main"][outflow][
                "sequences"
            ]["flow"]
            for fuel, inflow in f["in"].items():
                tables[sector[0]]["in", fuel] += results["main"][inflow][
                    "sequences"
                ]["flow"] * getattr(fuel_factors, sector[0])

    # Add volatile source to electricity table
    volatile_output_by_region = (
        fetch_volatile_electricity_sources(results)
        .groupby(level=1, axis=1)
        .sum()
    )

    for region in volatile_output_by_region.columns:
        if ("out", ("electricity", region)) in tables["electricity"]:
            tables["electricity"][
                "out", ("electricity", region)
            ] += volatile_output_by_region[region]
        else:
            tables["electricity"][
                "out", ("electricity", region)
            ] = volatile_output_by_region[region]

    emissions = fetch_parameter_of_commodity_sources(results)["emission"]
    emissions.index = emissions.index.to_flat_index()
    emission_series = (
        pd.DataFrame(index=time_index, columns=emissions.index)
        .fillna(1)
        .mul(emissions)
    )

    tables["electricity"] = _calculate_emissions_from_energy_table(
        tables["electricity"], emission_series
    )

    last_key = None
    for column in tables["electricity"]["energy", "out"].columns:
        emission_series[("electricity", column[1])] = tables["electricity"][
            "emission", "out", "electricity"
        ] / tables["electricity"]["energy", "out"].sum(axis=1)
        last_key = column[1]

    avg_elec_emissions = (
        tables["electricity"]["emission", "out", "electricity"].sum()
        / tables["electricity"]["energy", "out"].sum().sum()
    )
    emissions = emissions.append(
        pd.Series({("electricity", "all"): avg_elec_emissions})
    )
    print(avg_elec_emissions)
    sectors = [k for k in tables.keys() if k != "electricity"]

    for sector in sectors:
        tables[sector] = _calculate_emissions_from_energy_table(
            tables[sector], emissions
        )

    tables["emissions"] = emissions.reindex(emissions.index)
    tables["electricity emission series"] = emission_series[
        ("electricity", last_key)
    ]
    return tables


def get_flow_results(result):
    """
    Extract values from the flows and calculate key values.

    Parameters
    ----------
    result : dict
        A deflex results dictionary.

    Returns
    -------
    The results for each flow of a solved deflex scenario : pandas.DataFrame

    Examples
    --------
    >>> from deflex.tools import TEST_PATH, fetch_test_files
    >>> from deflex import postprocessing as pp
    >>> from deflex.analyses import get_flow_results
    >>> fn1 = fetch_test_files("de17_heat.dflx")
    >>> my_result = pp.restore_results(fn1)
    >>> res = get_flow_results(my_result)
    >>> round(res.loc[34, ("cost", "specific", "trsf")].max(), 2)
    209.34
    """
    inflows = get_line_inflows(result)
    levels = [[], [], [], []]
    seq = pd.DataFrame(
        columns=pd.MultiIndex(levels=levels, codes=levels),
        index=range(len(result["Main"][inflows[0]]["sequences"])),
    )

    for flow in inflows:
        seq[flow[0].label] = (
            result["Main"][flow]["sequences"].reset_index(drop=True).flow
        )
    mo = merit_order_from_results(result)

    seq = pd.concat(
        [seq, seq.div(seq).fillna(0)], axis=1, keys=["absolute", "specific"]
    )
    seq = pd.concat([seq], axis=1, keys=["values"])

    mo.rename(
        columns={"spec_emission": "emission", "costs_total": "cost"},
        inplace=True,
    )

    for weight in ["emission", "cost"]:
        for mode in ["absolute", "specific"]:
            temp = seq["values", mode].mul(mo[weight])
            temp = pd.concat([temp], axis=1, keys=[(weight, mode)])
            seq = pd.concat([seq, temp], axis=1)
            seq.sort_index(1, inplace=True)

    return seq


def calculate_market_clearing_price(result=None, flow_results=None):
    """
    Market Clearing Price (MCP), the costs of the most expensive
    running power plant, excluding chp.

    Parameters
    ----------
    result : deflex.Scenario.result
        A results dictionary from a deflex scenario.
    flow_results
        A flow results dictionary from the :py:func:`~get_flow_results`
        function.

    Returns
    -------
    Market clearing price : pandas.Series

    Examples
    --------
    >>> from deflex.tools import fetch_test_files
    >>> from deflex import postprocessing as pp
    >>> from deflex.analyses import calculate_market_clearing_price
    >>> fn1 = fetch_test_files("de17_heat.dflx")
    >>> my_result = pp.restore_results(fn1)
    >>> mcp = calculate_market_clearing_price(my_result)
    >>> round(mcp.mean(), 2)
    39.78
    >>> round(mcp.max(), 2)
    45.76

    """
    if flow_results is None:
        flow_results = get_flow_results(result)
    if "chp" in flow_results["cost", "specific", "trsf"].columns:
        mcp = flow_results.drop(("cost", "specific", "trsf", "chp"), axis=1)[
            "cost", "specific"
        ].max(axis=1)
    else:
        mcp = flow_results["cost", "specific"].max(axis=1)
    return mcp


def calculate_emissions_most_expensive_pp(result=None, flow_results=None):
    """
    The emissions of the most expensive running power plant. CHP plants are
    excluded.

    Parameters
    ----------
    result : deflex.Scenario.result
        A results dictionary from a deflex scenario.
    flow_results
        A flow results dictionary from the :py:func:`~get_flow_results`
        function.

    Returns
    -------
    The specific emissions of the most expensive power plant : pandas.Series

    Examples
    --------
    >>> from deflex.tools import fetch_test_files
    >>> from deflex import postprocessing as pp
    >>> from deflex.analyses import calculate_market_clearing_price
    >>> fn1 = fetch_test_files("de17_heat.dflx")
    >>> my_result = pp.restore_results(fn1)
    >>> emissions_mcp = calculate_emissions_most_expensive_pp(my_result)
    >>> round(emissions_mcp.mean(), 4)
    0.864
    >>> round(emissions_mcp.max(), 4)
    1.6423
    """
    if flow_results is None:
        flow_results = get_flow_results(result)

    if "chp" in flow_results["cost", "specific", "trsf"].columns:
        mcp_id = flow_results.drop(
            ("cost", "specific", "trsf", "chp"), axis=1
        )["cost", "specific"].idxmax(axis=1)
    else:
        mcp_id = flow_results["cost", "specific"].idxmax(axis=1)

    emissions = flow_results["emission", "specific"]
    emissions_most_expensive = pd.Series(
        emissions.lookup(*zip(*pd.DataFrame(data=mcp_id).to_records()))
    )
    return emissions_most_expensive


def get_key_values_from_results(results, **switch):
    """
    Extract key values from a list of solph results dictionaries.

     * emissions_most_expensive_pp: The emissions of the most expensive running
       power plant, excluding chp
     * mcp: Market Clearing Price (MCP), the costs of the most expensive
            running power plant, excluding chp.

    To exclude some of the values above one can set them to false with
    ``mcp=False`` and so on.

    If typical values are missing, please open an
    `issue <https://github.com/reegis/deflex>`_.

    Parameters
    ----------
    results : list
        A list of solph results dictionaries.

    Other Parameters
    ----------------
    emissions_average : bool
    emissions_most_expensive_pp : bool
    mcp : bool

    Returns
    -------
    pandas.DataFrame : Key values for each result dictionary with MultiIndex
        columns.

    Examples
    --------
    >>> from deflex.tools import TEST_PATH, fetch_test_files
    >>> from deflex import postprocessing as pp
    >>> from deflex.analyses import get_key_values_from_results
    >>> fn1 = fetch_test_files("de17_heat.dflx")
    >>> fn2 = fetch_test_files("de02_heat.dflx")
    >>> my_results = pp.restore_results([fn1, fn2])
    >>> kv = get_key_values_from_results(my_results)
    >>> list(kv.columns.get_level_values(1).unique())
    ['deflex_2014_de17_heat_reg-merit', 'deflex_2014_de02_heat_reg-merit']
    >>> round(kv.loc[34, ("mcp", "deflex_2014_de17_heat_reg-merit")], 2)
    42.16
    >>> list(kv.columns.get_level_values(0).unique())
    ['mcp', 'emissions_most_expensive_pp']
    >>> kv = get_key_values_from_results(my_results, mcp=False)
    >>> list(kv.columns.get_level_values(0).unique())
    ['emissions_most_expensive_pp']
    """
    key_values = {
        "mcp": calculate_market_clearing_price,
        "emissions_most_expensive_pp": calculate_emissions_most_expensive_pp,
    }

    kv = pd.DataFrame(columns=pd.MultiIndex(levels=[[], []], codes=[[], []]))
    for r in results:
        name = r["meta"]["name"]
        flrs = get_flow_results(r)
        for key, func in key_values.items():
            if switch.get(key, True) is True:
                kv[key, name] = func(flow_results=flrs)
    return kv


def remove_empty_columns(table):
    return


def dict2file(tables, path, filetype=None, drop_empty_columns=False):

    if filetype is None:
        filetype = path.split(".")[-1]

    if filetype == "xlsx":
        dict2spreadsheet(tables, path, drop_empty_columns)
    elif filetype == "csv":
        dict2csv(tables, path, drop_empty_columns)
    else:
        msg = "No function implemented for filetype: '{}'".format(filetype)
        raise NotImplementedError(msg)


def dict2spreadsheet(tables, path, drop_empty_columns=False):
    writer = pd.ExcelWriter(path)
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table.sort_index(axis=1, inplace=True)
            if drop_empty_columns:
                table = table.loc[:, (table.sum(axis=0) != 0)]
        table.to_excel(writer, name)
    writer.save()


def dict2csv(tables, path, drop_empty_columns=False):
    for name, table in tables.items():
        fn = os.path.join(path, name + ".csv")
        table.to_csv(fn)


if __name__ == "__main__":
    from deflex import postprocessing as pp
    import os

    allocate_fuel("finnish", eta_e=0.3, eta_th=0.5)
    # print(finnish_method(0.3, 0.5, 0.5, 0.9))
    exit(0)
    my_fn = "/home/uwe/.deflex/pedro/2030-DE02-Agora4.dflx"
    # fn = os.path.join(
    #     os.path.expanduser("~"),
    #     ".deflex",
    #     "tmp_test_32traffic_43",
    #     "results_cbc",
    #     "de03_fictive.dflx",
    # )

    my_results = pp.restore_results(my_fn)

    # filename1 = fn.replace(".dflx", "_results.xlsx")
    # all_results = get_all_results(my_results)
    # dict2file(all_results, filename1)

    filename2 = my_fn.replace(".dflx", "_results_emission.xlsx")
    my_tables = calculate_product_fuel_balance(my_results)
    dict2file(my_tables, filename2, drop_empty_columns=True)
    # for table in all_results._fields:
    #     print("\n\n***************** " + table + " ****************\n")
    #     print(getattr(all_results, table))
