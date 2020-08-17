# -*- coding: utf-8 -*-

"""Analyses of deflex.

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
    >>> path = os.path.join(os.path.dirname(__file__), os.pardir, "tests",
    ...                     "data", "deflex_2014_de02_test_csv")
    >>> mo1 = merit_order_from_scenario(path)
    >>> round(mo1.capacity_cum.iloc[-1], 4)
    66.1328
    >>> round(mo1.capacity.sum(), 1)
    66132.8
    >>> round(mo1.loc[("DE01", "natural gas"), "costs_total"], 2)
    59.93
    >>> mo2 = merit_order_from_scenario(path, with_downtime=False)
    >>> int(round(mo2.capacity.sum(), 0))
    77664
    >>> mo3 = merit_order_from_scenario(path, with_co2_price=False)
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
    transf.sort_values(["costs_total", "capacity"], inplace=True)
    transf = transf.loc[transf["fuel"] != "bioenergy"]
    transf = transf.loc[transf["fuel"] != "other"]
    transf.sort_values(["costs_total", "capacity"], inplace=True)
    transf["capacity_cum"] = transf.capacity.cumsum().div(1000)
    return transf
