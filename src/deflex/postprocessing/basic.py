# -*- coding: utf-8 -*-

"""Basic result processing.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

__all__ = [
    "get_all_results",
    "nodes2table",
    "fetch_dual_results",
    "group_buses",
    "solver_results2series",
    "meta_results2series",
    "get_time_index",
]

import pandas as pd
from oemof import solph


def get_time_index(results):
    """Get the time index of the model."""
    key = list(results["main"].keys())[0]
    return results["main"][key]["sequences"].index


def meta_results2series(results):
    """Get meta results as a pandas.Series"""
    meta = results["Meta"]
    meta.pop("solver")
    meta.pop("problem")
    return pd.Series(meta)


def fetch_dual_results(results, bus=None, exclude_commodities=True):
    """
    Collect all the results of the dual variables.

    A bus can be passed to get only the dual variables of this specific bus,
    otherwise the results of the dual variables of all buses are collected. The
    variables of the commodity buses can be excluded using the
    `exclude_commodities` parameter.

    Parameters
    ----------
    results : dict
        A valid deflex results dictionary.
    bus : oemof.network.Bus
        An existing Bus of the deflex model results.
    exclude_commodities : bool
        Exclude the results of the commodity buses.

    Returns
    -------
    pandas.Series
    """
    if bus is None:
        buses = set(
            [
                k[0]
                for k in results["main"].keys()
                if isinstance(k[0], solph.network.bus.Bus) and k[1] is None
            ]
        )
        if exclude_commodities:
            buses = [b for b in buses if b.label.cat != "commodity"]
    else:
        buses = list((bus,))
    duals = {}
    for b in buses:
        duals[b] = results["main"][b, None]["sequences"]["duals"]
    return pd.DataFrame(duals)


def solver_results2series(results):
    """
    Get the meta results from the solver.

    The keys in the first index level are:

     * Problem
     * Solution
     * Solver
     * Solver Black box
     * Solver Branch and bound

    Parameters
    ----------
    results : dict
        A valid deflex results dictionary.

    Returns
    -------
    pd.Series

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de02_heat.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> slvr = solver_results2series(my_results)
    >>> list(slvr.index.get_level_values(0).unique())[:4]
    ['Problem', 'Solution', 'Solver', 'Solver Black box']
    >>> round(slvr["Solver", "Time"],5)
    0.07627
    >>> int(slvr["Solution", "Objective"])
    7516285616

    """
    solver = pd.Series(
        index=pd.MultiIndex(levels=[[], []], codes=[[], []]), dtype="object"
    )
    for k, v in dict(results["Solver"][0]).items():
        try:
            solver["Solver", k] = v.value
        except AttributeError:
            for k2, v2 in dict(results["Solver"][0][k]).items():
                for k3, v3 in dict(results["Solver"][0][k][k2]).items():
                    solver["Solver " + k2, k3] = v3.value
    for k, v in dict(results["Problem"][0]).items():
        solver["Problem", k] = v.value

    for k, v in results["Solution"].items():
        solver["Solution", k] = v.value
    solver["Solution", "Objective"] = results["meta"]["objective"]
    return solver.sort_index()


def _components2table(results):
    """
    Get all results of variables of components (dual, storage content etc.).
    """
    classes = {
        solph.GenericStorage: "storages",
        solph.custom.SinkDSM: "demand response sinks",
        solph.network.bus.Bus: "buses",
    }
    components = set([k[0] for k in results["main"].keys() if k[1] is None])
    seq = {}
    for component in components:
        ctype = classes[type(component)]
        for col in results["main"][component, None]["sequences"].columns:
            seq[
                ctype,
                component.label.cat,
                component.label.tag,
                component.label.subtag,
                component.label.region,
                col,
            ] = results["main"][component, None]["sequences"][col]
    return {"components": pd.DataFrame(seq)}


def _get_flows_per_busgroup(results, bus_groups):
    """
    Collect all flows of each bus_group as a dict of tables.
    The keys of the dictionary are the keys of the bus_groups as reformatted
    strings.
    """
    tables = {}

    for key, buses in bus_groups.items():
        seq = {}
        name = "_".join(key).replace("_all", "")
        for bus in buses:
            flows = [k for k in results["main"].keys() if k[1] == bus]
            flows.extend(
                [
                    k
                    for k in results["main"].keys()
                    if k[0] == bus and k[1] is not None
                ]
            )
            for f in flows:
                seq[
                    (
                        f[0].label.cat,
                        f[0].label.tag,
                        f[0].label.subtag,
                        f[0].label.region,
                        f[1].label.cat,
                        f[1].label.tag,
                        f[1].label.subtag,
                        f[1].label.region,
                    )
                ] = results["main"][f]["sequences"]["flow"]
        tables[name] = pd.DataFrame(seq).sort_index(axis=1)

    return tables


def _get_all_nodes_from_results(results):
    """Collect all nodes of the results in one set."""
    unique_nodes = [n[0] for n in results["main"].keys()]
    unique_nodes.extend(
        [n[1] for n in results["main"].keys() if n[1] is not None]
    )
    return set(unique_nodes)


def nodes2table(results, no_sums=False):
    """
    Get a table with all nodes as a MultiIndex with the sum of their in an out
    flows.

    The index contains the following levels: class, category, tag, subtag,
    region

    The sums can be found in the columns "in" and "out".

    Parameters
    ----------
    results : dict
        Deflex results dictionary.
    no_sums : bool
        Set to False to get an empty DataFrame with no sums (default: True)

    Returns
    -------
    Table with all nodes and sums : pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> all_nodes = nodes2table(my_results)
    >>> len(all_nodes)
    226
    >>> all_nodes.to_csv("your/path/file.csv")  # doctest: +SKIP


    """
    unique_nodes = _get_all_nodes_from_results(results)
    nodes = []
    for node in unique_nodes:
        dc = {}
        solph_class = type(node)
        label = node.label
        dc["class"] = (
            str(solph_class).rsplit(".", maxsplit=1)[-1].replace("'>", "")
        )
        dc["cat"] = label.cat
        dc["tag"] = label.tag
        dc["subtag"] = label.subtag
        dc["region"] = label.region
        if no_sums is False:
            from_node = sum(
                [
                    v["sequences"]["flow"]
                    for k, v in results["Main"].items()
                    if k[0].label == label and k[1] is not None
                ]
            )
            if isinstance(from_node, pd.Series):
                from_node = from_node.sum()
            to_node = sum(
                [
                    v["sequences"]["flow"]
                    for k, v in results["Main"].items()
                    if getattr(k[1], "label", "") == label
                ]
            )
            if isinstance(to_node, pd.Series):
                to_node = to_node.sum()
            dc["out"] = from_node
            dc["in"] = to_node
        nodes.append(dc)
    df = pd.DataFrame(nodes)
    df.sort_values(by=list(df.columns), inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df.set_index(["class", "cat", "tag", "subtag", "region"], drop=True)


def group_buses(buses, fields):
    """
    Group buses by parts of the label.

    Parameters
    ----------
    buses : list
        Buses to group.
    fields : list
        Fields of the label to group the buses. Valid labels are `cat`, `tag`,
        `subtag`, `region`.

    Returns
    -------
    Grouped buses : dict of lists

    Examples
    --------
    >>> import deflex as dflx
    >>> from oemof.network.network import Bus
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> mybuses = set([r[0] for r in my_results["main"].keys()
    ...     if isinstance(r[0], Bus)])
    >>> sorted(dflx.group_buses(mybuses, ["cat", "tag", "subtag"]).keys())[:2]
    [('commodity', 'all', 'H2'), ('commodity', 'all', 'bioenergy')]
    >>> sorted(dflx.group_buses(mybuses, ["cat"]).keys())[:4]
    [('commodity',), ('electricity',), ('heat',), ('mobility',)]
    >>> c_buses = dflx.group_buses(mybuses, ["cat"])[('commodity',)]
    >>> sorted(c_buses)[0].label
    Label(cat='commodity', tag='all', subtag='H2', region='DE')
    >>> len(c_buses)
    10
    >>> for bu in sorted(c_buses)[:3]:
    ...     print(repr(bu.label))
    Label(cat='commodity', tag='all', subtag='H2', region='DE')
    Label(cat='commodity', tag='all', subtag='bioenergy', region='DE01')
    Label(cat='commodity', tag='all', subtag='bioenergy', region='DE02')
    """
    groups = {}
    for b in set(buses):
        temp = []
        for field in fields:
            temp.append(getattr(b.label, field))
        if tuple(temp) in groups.keys():
            groups[tuple(temp)].append(b)
        else:
            groups[tuple(temp)] = [b]
    return groups


def get_all_results(results):
    """
    Get all results from a computed deflex scenario.

    The results will be returned as a dictionary of pandas.DataFrame that can
    be stored in the xlsx or csv format using `dict2file`.
    This function can be used to transfer the results to another programming
    language or an external tool.

    Parameters
    ----------
    results : dict
        A valid deflex results dictionary.

    Returns
    -------
    dict of pandas.DataFrame

    Examples
    --------
    >>> import os
    >>> import shutil
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> all_results = get_all_results(my_results)
    >>> sorted(list(all_results.keys()))[:4]
    ['commodity', 'components', 'electricity', 'heat_decentralised']
    >>> sorted(list(all_results.keys()))[-5:]
    ['heat_decentralised', 'heat_district', 'meta', 'mobility', 'solver']
    >>> fn_out = fn.replace(".dflx", "_all_results.csv")
    >>> dflx.dict2file(all_results, fn_out, "csv", drop_empty_columns=True)
    >>> my_bool = []
    >>> for key in all_results.keys():
    ...     fn_test = os.path.join(fn_out, key + ".csv")
    ...     my_bool.append(os.path.isfile(fn_test))
    >>> my_bool
    [True, True, True, True, True, True, True, True]
    >>> shutil.rmtree(fn_out)
    """
    buses = set(
        [k[0] for k in results["main"].keys() if isinstance(k[0], solph.Bus)]
    )
    bus_groups = group_buses(buses, ["cat", "tag"])
    tables = _get_flows_per_busgroup(results, bus_groups)
    tables.update(_components2table(results))
    tables["solver"] = solver_results2series(results)
    tables["meta"] = meta_results2series(results)
    return tables
