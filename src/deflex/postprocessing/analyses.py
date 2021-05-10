# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from collections import namedtuple

import pandas as pd
from oemof import solph


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
    236
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


if __name__ == "__main__":
    pass
    # from deflex import postprocessing as pp
    # import os
    #
    # allocate_fuel("finnish", eta_e=0.3, eta_th=0.5)
    # # print(finnish_method(0.3, 0.5, 0.5, 0.9))
    # exit(0)
    # my_fn = "/home/uwe/.deflex/pedro/2030-DE02-Agora4.dflx"
    # # fn = os.path.join(
    # #     os.path.expanduser("~"),
    # #     ".deflex",
    # #     "tmp_test_32traffic_43",
    # #     "results_cbc",
    # #     "de03_fictive.dflx",
    # # )
    #
    # my_results = pp.restore_results(my_fn)
    #
    # # filename1 = fn.replace(".dflx", "_results.xlsx")
    # # all_results = get_all_results(my_results)
    # # dict2file(all_results, filename1)
    #
    # filename2 = my_fn.replace(".dflx", "_results_emission.xlsx")
    # my_tables = calculate_product_fuel_balance(my_results)
    # dict2file(my_tables, filename2, drop_empty_columns=True)
    # # for table in all_results._fields:
    # #     print("\n\n***************** " + table + " ****************\n")
    # #     print(getattr(all_results, table))
