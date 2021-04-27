# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import pandas as pd


def reshape_bus_view(results, buses, data=None, aggregate=None):
    """
    Create a MultiIndex DataFrame with all Flows around the Bus objects. The
    first column level contains ``'in'`` or ``'out'`` for ingoing and outgoing
    flows.


    Parameters
    ----------
    results: dict
        A solph results dictionary from a deflex scenario.
    buses : list[solph.Bus] or solph.Bus
        A single bus node or a list of buses.
    data : pandas.DataFrame
        MultiIndex DataFrame to add the results to.
    aggregate : list or None
        A list of tuples that will replace the subtag. The subtag normally
        divides similar nodes. The subtag of power plant nodes for example
        contains the used fuel, By replacing the fuel with a name such as "all"
        all power plants will be aggregated. The tuple must have three fields:
        (field to check, value of the field, new value of subtag)
        e.g. ("tag", "pp", "all") will change all power plants:
        trsf_pp_oil_DE02 -> trsf_pp_all_DE02
        trsf_pp_lignite_DE02 -> trsf_pp_all_DE02
        trsf_chp_oil_DE02 ->  trsf_chp_oil_DE02
        If the last field of the tuple is an integer the last (-1) or first (1)
        part of a subtag is removed
        e.g. ("tag", "pp", -1) will change all power plants:
        trsf_pp_oil_038_DE02 -> trsf_pp_oil_DE02
        trsf_pp_oil_039_DE02 -> trsf_pp_oil_DE02
        trsf_pp_lignite_035_DE02 ->  trsf_pp_lignite_DE02
        Nodes with the same label will be aggregated.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> from oemof import solph
    >>> from deflex.tools import fetch_test_files
    >>> from deflex.postprocessing import restore_scenario
    >>> fn = fetch_test_files("de21_no-heat.dflx")
    >>> my_es = restore_scenario(fn).es
    >>> my_buses = [bus for flow in my_es.results if
    ...             isinstance(flow[0], solph.Bus) and
    ...             flow[0].label.tag == "electricity"]
    >>> # aggregate lines for all regions and remove suffix of power plants
    >>> agg = [("cat", "line", "all"),
    ...        ("tag", "pp", -1)]
    >>> df1 = reshape_bus_view(my_es.results, my_buses, aggregate=agg)
    >>> df2 = reshape_bus_view(my_es.results, my_buses)
    >>> df1 = df1.groupby(level=[1, 2, 3, 4], axis=1).sum()
    >>> df2 = df2.groupby(level=[1, 2, 3, 4], axis=1).sum()
    >>> list(df1["in", "line", "electricity"].columns[:5])
    ['all']
    >>> list(df2["in", "line", "electricity"].columns[:5])
    ['DE01', 'DE02', 'DE03', 'DE04', 'DE05']
    >>> list(df1["in", "trsf", "pp"].columns[:4])
    ['bioenergy', 'hard coal', 'lignite', 'natural gas']
    >>> list(df2["in", "trsf", "pp"].columns[:4])
    ['bioenergy_038', 'bioenergy_042', 'bioenergy_045', 'hard coal_023']
    >>> int(df1.sum().sum())
    7529364
    >>> int(df2.sum().sum())
    7529364

    """
    if aggregate is None:
        aggregate = []
    if data is None:
        m_cols = pd.MultiIndex(
            levels=[[], [], [], [], []], codes=[[], [], [], [], []]
        )
        data = pd.DataFrame(columns=m_cols)

    if not isinstance(buses, list):
        buses = [buses]

    def change_subtag(node, changes):
        val = node.label.subtag
        for agg in changes:
            if getattr(node.label, agg[0]) == agg[1]:
                if isinstance(agg[2], int):
                    if agg[2] < 0:
                        val = "_".join(node.label.subtag.split("_")[: agg[2]])
                    else:
                        val = "_".join(node.label.subtag.split("_")[agg[2] :])
                else:
                    val = agg[2]
        return val

    for bus in buses:
        # filter all nodes and sub-list import/exports
        node_flows = [
            x
            for x in results["Main"].keys()
            if bus in (x[1], x[0]) and x[1] is not None
        ]

        # Add all flow time series to a MultiIndex DataFrame using in/out
        for flow in node_flows:
            if flow[0] == bus:
                subtag = change_subtag(flow[1], aggregate)
                flow_label = (
                    bus.label,
                    "out",
                    flow[1].label.cat,
                    flow[1].label.tag,
                    subtag,
                )
            else:
                subtag = change_subtag(flow[0], aggregate)
                flow_label = (
                    bus.label,
                    "in",
                    flow[0].label.cat,
                    flow[0].label.tag,
                    subtag,
                )

            if flow_label in data:
                data[flow_label] += results["Main"][flow]["sequences"]["flow"]
            else:
                data[flow_label] = results["Main"][flow]["sequences"]["flow"]

    return data.sort_index(axis=1)
