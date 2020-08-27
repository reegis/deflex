# -*- coding: utf-8 -*-

"""
Analyses of deflex.

SPDX-FileCopyrightText: 2016-2020 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import pandas as pd
from deflex import scenario_tools


def merit_order_from_scenario(path, with_downtime=True, with_co2_price=True):
    """
    Create a merit order from a deflex scenario.

    TODO: Check transmission.
    TODO: Add volatile sources as an optional feature
    TODO: Check chp. Warn if chp are present. Add chp as an option
    TODO: Or warn if no chp are present, installed capacity might be too high

    Parameters
    ----------
    path : str
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
    >>> my_path = os.path.join(os.path.dirname(__file__), os.pardir, "tests",
    ...                        "data", "deflex_2014_de02_test_csv")
    >>> mo1 = merit_order_from_scenario(my_path)
    >>> round(mo1.capacity_cum.iloc[-1], 4)
    66.1328
    >>> round(mo1.capacity.sum(), 1)
    66132.8
    >>> round(mo1.loc[("DE01", "natural gas"), "costs_total"], 2)
    59.93
    >>> mo2 = merit_order_from_scenario(my_path, with_downtime=False)
    >>> int(round(mo2.capacity.sum(), 0))
    77664
    >>> mo3 = merit_order_from_scenario(my_path, with_co2_price=False)
    >>> round(mo3.loc[("DE01", "natural gas"), "costs_total"], 2)
    52.87

    """
    sc = scenario_tools.DeflexScenario(year=2014)
    sc.load_csv(path)
    sc.name = sc.table_collection["meta"].loc["name", "value"]
    transf = sc.table_collection["transformer"]
    num_cols = ["capacity", "variable_costs", "efficiency", "count"]
    transf[num_cols] = transf[num_cols].astype(float)
    if with_downtime and "downtime_factor" in transf:
        transf["capacity"] *= 1 - pd.to_numeric(
            transf["downtime_factor"].fillna(0.1)
        )
    transf = transf.loc[transf["capacity"] != 0]
    my_data = sc.table_collection["commodity_source"].loc["DE"]
    transf = transf.merge(
        my_data, right_index=True, how="left", left_on="fuel"
    )
    transf["costs_total"] = pd.to_numeric(
        transf["variable_costs"].fillna(1)
    ) + transf["costs"].div(transf["efficiency"])
    if with_co2_price and "co2_price" in transf:
        transf["costs_total"] += transf["co2_price"] * transf["emission"].div(
            1000
        ).div(transf["efficiency"])
    # transf.sort_values(["costs_total", "capacity"], inplace=True)
    # transf = transf.loc[transf["fuel"] != "bioenergy"]
    # transf = transf.loc[transf["fuel"] != "other"]
    transf.sort_values(["costs_total", "capacity"], inplace=True)
    transf["capacity_cum"] = transf.capacity.cumsum().div(1000)
    return transf


def merit_order_from_results(result):
    """

    Returns
    -------

    Examples
    --------
    >>> fn = results.download_example_results()
    >>> my_results = results.restore_results(fn.de02)
    >>> merit_order_from_results(my_results)
    """
    # TODO: If there is a transmission limit or transmission losses
    #       the merit order cannot be calculated!!!!

    # Fetch all flows into any electricity bus
    inflows = [x for x in result["Main"].keys() if
               isinstance(x[1], solph.Bus) and x[1].label.tag == "electricity"
               and not x[0].label.cat == "line"]

    # Create a DataFrame for the costs
    costs = pd.DataFrame()
    for inflow in inflows:
        label = inflow[0]  # str(inflow[0])
        # print(repr(inflow[0].label))
        component = inflow[0]
        electricity_bus = inflow[1]

        # Variable costs of the outflow of the component
        costs.loc[label, "variable_costs_out"] = (
            result["Param"][inflow]["scalars"].variable_costs)

        # Capacity of the component
        costs.loc[label, "capacity"] = (
            result["Param"][inflow]["scalars"].get(
                "nominal_value", 10000))

        srcbus2component = [x for x in result["Main"].keys()
                            if x[1] == component and x[0] != electricity_bus]

        if len(srcbus2component) > 0:
            srcbus = srcbus2component[0][0]
            # Variable costs of the inflow of the component
            costs.loc[label, "variable_costs_in"] = (
                result["Param"][srcbus2component[0]]["scalars"].variable_costs)

            # Efficiency of the component if component is a transformer.
            parameter_name = "conversion_factors_{0}".format(electricity_bus)
            costs.loc[label, "efficiency"] = (
                result["Param"][(component, None)]["scalars"][parameter_name])

            src2srcbus = [x for x in result["Main"].keys() if x[1] == srcbus
                          and x[0].label.cat != "shortage"]
            if len(src2srcbus) > 1:
                msg = ("More than one source found for {0}. "
                       "Source costs will be ambiguous.")
                raise ValueError(msg.format(srcbus))

            # Variable costs of the fuel source.
            costs.loc[label, "fuel_costs"] = (
                result["Param"][src2srcbus[0]]["scalars"].variable_costs)
            costs.loc[label, "fuel_emissions"] = (
                result["Param"][src2srcbus[0]]["scalars"].emission)
            costs.loc[label, "fuel"] = src2srcbus[0][0].label.subtag.replace(
                "_", " "
            )
        else:
            costs.loc[label, "efficiency"] = 1
            costs.loc[label, "variable_costs_in"] = 0
            costs.loc[label, "fuel_costs"] = 0
            costs.loc[label, "fuel_emissions"] = 0
            costs.loc[label, "fuel"] = "no fuel"

        costs.loc[label, "costs_total"] = (
            costs.loc[label, "variable_costs_out"] +
            (costs.loc[label, "variable_costs_in"] +
             costs.loc[label, "fuel_costs"]
             ) /
            costs.loc[label, "efficiency"]
        )

    # for c in costs.iterrows():
    #     print(c)
    # print(costs)
    # costs = costs.loc[costs["fuel"] != "bioenergy"]
    # costs = costs.loc[costs["fuel"] != "other"]
    costs = costs.loc[costs["fuel"] != "no fuel"]
    costs.sort_values(["costs_total", "capacity"], inplace=True)
    costs["capacity_cum"] = costs.capacity.cumsum().div(1000)
    return costs

