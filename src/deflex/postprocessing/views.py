# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import pandas as pd


def reshape_bus_view(results, buses, aggregate=None):
    """
    Create a MultiIndex DataFrame with all Flows around the Bus objects. The
    first column level contains ``'in'`` or ``'out'`` for ingoing and outgoing
    flows.

    Replaced by `get_combined_bus_balance`?

    Parameters
    ----------
    results: dict
        A solph results dictionary from a deflex scenario.
    buses : list[solph.Bus] or solph.Bus
        A single bus node or a list of buses.
    aggregate : list or None
        A list of tuples to replace the tag or subtag of a group of Flows.
        With the first two fields the group of Flows can be defined e.g.
        ("cat", "power plant",...) or ("cat" "line",...) With the second two
        fields the field that wants to be replaced has to be defined. Typically
        the field will be replaced by "all" so that all fields will have the
        same name. In a second step all Flows with the same name will be
        aggregated.
        If there are different natural gas power plants in the system e.g.
        The tag of these power plants differ in the "tag": "combined cycle",
        "gas turbine"....
        Using ("cat", "power plant", "tag", "all"), the different tags will be
        replaced with "all":
        ("power plant", "combined cycle" "natural gas") ->
        ("power plant", "all", "natural gas") and
        ("power plant", "gas turbine" "natural gas") ->
        ("power plant", "all", "natural gas")
        As they do have the same name they will be aggregated.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> from oemof import solph
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de02_heat.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> my_buses = list(set([flow[0] for flow in my_results["main"].keys() if
    ...            isinstance(flow[0], solph.Bus) and
    ...            flow[0].label.cat == "electricity"]))
    >>> # aggregate power plants and chp plants with the same fuel
    >>> agg = [("cat", "power plant", "tag", "all"),
    ...        ("cat", "chp plant", "tag", "all")]
    >>> df = reshape_bus_view(my_results, my_buses, aggregate=agg)
    >>> df = df.groupby(level=[1, 2, 3, 4], axis=1).sum()
    >>> sorted(list(df["in", "power plant", "all"].columns))[:5]
    ['bioenergy', 'hard coal', 'lignite', 'natural gas', 'nuclear']

    """
    # IM DOCSTRING NUR FUNKTION ERKLÄREN, DEN REST DANN IN TEST VERSCHIEBEN!
    if aggregate is None:
        aggregate = []

    if not isinstance(buses, list):
        buses = [buses]
    else:
        buses = list(set(buses))

    def change_field(node, changes):
        val = {"subtag": node.label.subtag, "tag": node.label.tag}
        for agg in changes:
            field = agg[2]
            if getattr(node.label, agg[0]) == agg[1]:
                val[field] = agg[3]
        return val

    data = {}
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
                fields = change_field(flow[1], aggregate)
                flow_label = (
                    bus.label,
                    "out",
                    flow[1].label.cat,
                    fields["tag"],
                    fields["subtag"],
                )

            else:
                fields = change_field(flow[0], aggregate)
                flow_label = (
                    bus.label,
                    "in",
                    flow[0].label.cat,
                    fields["tag"],
                    fields["subtag"],
                )
            if flow_label in data.keys():
                data[flow_label] += results["Main"][flow]["sequences"]["flow"]
            else:
                data[flow_label] = results["Main"][flow]["sequences"]["flow"]
    data = pd.DataFrame(data)
    return data.sort_index(axis=1)
