# -*- coding: utf-8 -*-

"""
Analyses of deflex.

SPDX-FileCopyrightText: 2016-2020 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
from shutil import rmtree

import pandas as pd
from oemof import solph
from pandas.testing import assert_frame_equal

from deflex import results
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
    >>> my_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
    ...                        "tests", "data", "deflex_2014_de02_test_csv")
    >>> mo1 = merit_order_from_scenario(my_path)
    >>> round(mo1.capacity_cum.iloc[-1], 4)
    71.9878
    >>> round(mo1.capacity.sum(), 1)
    71987.8
    >>> round(mo1.loc[("DE01", "natural gas"), "costs_total"], 2)
    59.93
    >>> mo2 = merit_order_from_scenario(my_path, with_downtime=False)
    >>> int(round(mo2.capacity.sum(), 0))
    84225
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
    transf.rename(columns={"emission": "fuel_emission"}, inplace=True)
    transf["spec_emission"] = transf["fuel_emission"].div(transf["efficiency"])
    transf["costs_total"] = pd.to_numeric(
        transf["variable_costs"].fillna(1)
    ) + transf["costs"].div(transf["efficiency"])
    if with_co2_price and "co2_price" in transf:
        transf["costs_total"] += transf["co2_price"] * transf[
            "fuel_emission"
        ].div(1000).div(transf["efficiency"])

    transf.sort_values(["costs_total", "capacity"], inplace=True)
    transf["capacity_cum"] = transf.capacity.cumsum().div(1000)
    return transf


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
    >>> from deflex import results
    >>> fn = results.fetch_example_results("de02_no_heat_reg_merit")
    >>> my_results = results.restore_results(fn)
    >>> a = merit_order_from_results(my_results)
    """
    # TODO: If there is a transmission limit or transmission losses
    #       the merit order cannot be calculated!!!!

    # Fetch all flows into any electricity bus
    inflows = [
        x
        for x in result["Main"].keys()
        if isinstance(x[1], solph.Bus)
        and x[1].label.tag == "electricity"
        and not x[0].label.cat == "line"
    ]

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


def check_comparision_of_merit_order(path):
    """Comparison of two different ways to calculate the merit order.

    1. Calculate the merit order from scenario
    2. Calculate the merit order from the results

    The resulting tables are not exactly the same because they will have some
    additional columns. The following columns should be the same.

    "capacity", "efficiency", "fuel_emission", "fuel", "costs_total",
    "capacity_cum"

    Parameters
    ----------
    path : str
        Full path of results file.

    Examples
    --------
    >>> from deflex import results
    >>> name = "de02_no_heat_reg_merit"
    >>> my_path = results.fetch_example_results(name)
    >>> check_comparision_of_merit_order(my_path)
    Check passed! Both merit order DataFrame tables are the same.
    """

    tmp_path = os.path.join(os.path.expanduser("~"), ".deflex", "tmp_dx34_f")

    # Fetch Results and store
    my_results = results.restore_results(path)
    deflex_scenario = scenario_tools.DeflexScenario(results=my_results)
    deflex_scenario.results2scenario(tmp_path)
    mo_scenario = merit_order_from_scenario(tmp_path)
    mo_results = merit_order_from_results(my_results)

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

    rmtree(tmp_path)


def get_flow_results(result):
    """
    Extract values from the flows and calculate key values.

    Parameters
    ----------
    result : dict
        A deflex results dictionary.

    Returns
    -------
    pandas.DataFrame

    """
    inflows = [
        x
        for x in result["Main"].keys()
        if isinstance(x[1], solph.Bus)
        and x[1].label.tag == "electricity"
        and not x[0].label.cat == "line"
    ]
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


if __name__ == "__main__":
    pass
