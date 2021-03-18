# -*- coding: utf-8 -*-

"""Results handling in deflex.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import pickle

import pandas as pd

from deflex.scenario import DeflexScenario
from deflex.scenario import restore_scenario


def search_results(path=None, extension="dflx", **parameter_filter):
    """Filter results by extension and meta data.

    The function will search the $HOME folder recursively for files with the
    '.esys' extension. Afterwards all files will filtered by the meta data.

    Parameters
    ----------
    path : str
        Start folder from where to search recursively.
    extension : str
        Extension of the results files (default: ".esys")
    **parameter_filter
        Set filter always with lists e.g. map=["de21"] or map=["de21", "de22"].
        The values in the list have to be strings.

    Returns
    -------

    Examples
    --------
    >>> from deflex.tools import TEST_PATH
    >>> from deflex.tools import fetch_test_files
    >>> my_file_name = fetch_test_files("de17_heat.dflx")
    >>> res = search_results(path=TEST_PATH, map=["de17"])
    >>> len(res)
    2
    >>> sorted(res)[0].split(os.sep)[-1]
    'de17_heat.dflx'
    >>> res = search_results(path=TEST_PATH, map=["de17", "de21"])
    >>> len(res)
    4
    >>> res = search_results(
    ...     path=TEST_PATH, map=["de17", "de21"], heat=["True"])
    >>> len(res)
    1
    >>> res[0].split(os.sep)[-1]
    'de17_heat.dflx'
    """
    if path is None:
        path = os.path.expanduser("~")

    # Search for files with ".esys" extension.
    result_files = []
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == "."]
        dirs[:] = [d for d in dirs if not d[0] == "."]
        if "." + extension in str(files):
            for f in files:
                if f.split(".")[-1] == extension:
                    result_files.append(os.path.join(root, f))
    files = {}

    # filter by meta data.
    for name in result_files:
        fn = os.path.join(path, name)
        f = open(fn, "rb")
        files[name] = pickle.load(f)
        f.close()
    for filter_key, filter_value in parameter_filter.items():
        iterate = list(files.keys())
        for fn in iterate:
            meta = files[fn]
            if str(meta.get(filter_key)) not in filter_value:
                files.pop(fn, None)
    return list(files.keys())


def restore_results(file_names, scenario_class=DeflexScenario):
    """Load results from a file or a list of files. The results will be


    Parameters
    ----------
    file_names : list or string
        All file names (full path) that should be loaded.
    scenario_class : deflex.Scenario
        The Scenario class. ToDo How to reference the class and an object.

    Returns
    -------
    list : A list of results dictionaries or a single dictionary if one file
        name is given.

    Examples
    --------
    >>> from deflex.tools import fetch_test_files
    >>> fn1 = fetch_test_files("de21_no-heat_transmission.dflx")
    >>> fn2 = fetch_test_files("de02_no-heat.dflx")
    >>> sorted(restore_results(fn1).keys())
    ['Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    >>> sorted(restore_results([fn1, fn2])[0].keys())
    ['Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    """
    if not isinstance(file_names, list):
        file_names = list((file_names,))
    results = []

    for path in file_names:
        tmp_res = restore_scenario(path, scenario_class).results
        tmp_res["meta"]["filename"] = os.path.basename(path)
        results.append(tmp_res)

    if len(results) < 2:
        results = results[0]
    return results


def search_nodes(results, node_type, **label_filter):
    nodes = {
        x[0] for x in results["Main"].keys() if isinstance(x[0], node_type)
    }

    for filter_key, filter_value in label_filter.items():
        if not isinstance(filter_value, list):
            filter_value = list((filter_value,))
        nodes = [
            n for n in nodes if getattr(n.label, filter_key) in filter_value
        ]
    return nodes


def reshape_bus_view(results, buses, data=None, aggregate=None):
    """
    Create a MultiIndex DataFrame with all Flows around the Bus objects. The
    first column level contains ``'in'`` or ``'out'`` for ingoing and outgoing
    flows.


    Parameters
    ----------
    results: dict
        A solph results dictionary from a deflex scenario.
    buses : list or solph.Bus
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
        If the last field of the tuble is an integer the last (-1) or first (1)
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
    >>> fn = fetch_test_files("de21_no-heat.dflx")
    >>> my_es = restore_scenario(fn).es
    >>> my_buses = search_nodes(
    ...     my_es.results, node_type=solph.Bus, tag="electricity")
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
                    elif agg[2] > 0:
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
            elif flow[1] == bus:
                subtag = change_subtag(flow[0], aggregate)
                flow_label = (
                    bus.label,
                    "in",
                    flow[0].label.cat,
                    flow[0].label.tag,
                    subtag,
                )
            else:
                flow_label = None

            if flow_label in data:
                data[flow_label] += results["Main"][flow]["sequences"]["flow"]
            else:
                data[flow_label] = results["Main"][flow]["sequences"]["flow"]

    return data.sort_index(axis=1)
