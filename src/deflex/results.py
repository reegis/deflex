# -*- coding: utf-8 -*-

"""Analyses of deflex.

SPDX-FileCopyrightText: 2016-2020 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import pickle

import pandas as pd
import requests
from oemof import solph

TEST_PATH = os.path.join(os.path.expanduser("~"), ".tmp_test_32traffic_43")


def fetch_example_results(key):
    """Download example results to enable tests.

    Make sure that the examples will
    have the same structure as the actual deflex results.
    """
    urls = {
        "de02_no_heat_reg_merit": "https://osf.io/9qt4a/download",
        "de02_heat_reg_merit": "https://osf.io/69mnu/download",
        "de22_no_heat_no_reg_merit": "https://osf.io/k4fdt/download",
        "de22_no_heat_reg_merit": "https://osf.io/3642z/download",
        "de22_heat_no_reg_merit": "https://osf.io/umvny/download",
        "de22_heat_reg_merit": "https://osf.io/yj4tm/download",
    }
    os.makedirs(TEST_PATH, exist_ok=True)
    file_name = os.path.join(TEST_PATH, key + ".esys")
    if not os.path.isfile(file_name):
        req = requests.get(urls[key])
        with open(file_name, "wb") as f_out:
            f_out.write(req.content)
    return file_name


def search_results(path=None, extension=".esys", **parameter_filter):
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

    Returns
    -------

    Examples
    --------
    >>> my_file_name = fetch_example_results("de22_no_heat_reg_merit")
    >>> search_results(path=TEST_PATH, map=["de22"])[0].split(os.sep)[-1]
    'de22_no_heat_reg_merit.esys'
    """
    if path is None:
        path = os.path.expanduser("~")

    # Search for files with ".esys" extension.
    result_files = []
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == "."]
        dirs[:] = [d for d in dirs if not d[0] == "."]
        if extension in str(files):
            for f in files:
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
            if meta.get(filter_key) not in filter_value:
                files.pop(fn, None)
    return list(files.keys())


def restore_energy_system(path):
    """Restore EnergySystem with results from file with the given path.

    Examples
    --------
    >>> fn = fetch_example_results("de02_no_heat_reg_merit")
    >>> type(restore_energy_system(fn))
    <class 'oemof.solph.network.EnergySystem'>
    """
    es = solph.EnergySystem()
    f = open(path, "rb")
    pickle.load(f)
    es.__dict__ = pickle.load(f)
    f.close()
    return es


def restore_results(file_names):
    """Load results from a file or a list of files.

    Parameters
    ----------
    file_names : list or string
        All file names (full path) that should be loaded.

    Returns
    -------
    list : A list of results dictionaries or a single dictionary if one file
        name is given.

    Examples
    --------
    >>> fn1 = fetch_example_results("de22_no_heat_reg_merit")
    >>> fn2 = fetch_example_results("de02_no_heat_reg_merit")
    >>> restore_results(fn1).keys()
    ['Problem', 'Solver', 'Solution', 'Main', 'Meta', 'Param']
    >>> restore_results([fn1, fn2])[0].keys()
    ['Problem', 'Solver', 'Solution', 'Main', 'Meta', 'Param']
    """
    if not isinstance(file_names, list):
        file_names = list((file_names,))
    results = []
    for path in file_names:
        results.append(restore_energy_system(path).results)
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
    """Create a MultiIndex DataFrame with all Flows around the Bus objects.

    Parameters
    ----------
    results: dict
        A solph results dictionary from a deflex scenario.
    buses : solph.Bus or list
        A single bus node or a list of buses.
    data : pandas.DataFrame
        MultiIndex DataFrame to add the results to.
    aggregate : list or None
        A list of tuples that will replace the subtag. The subtag normally
        devides similar nodes. The subtag of power plant nodes for example
        contains the used fuel, By replacing the fuel with a name such as "all"
        all powerplants will be aggregated. The tuple must have three fields:
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
    >>> fn = fetch_example_results("de22_no_heat_reg_merit")
    >>> my_es = restore_energy_system(fn)
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
    ['bioenergy', 'hard_coal', 'lignite', 'natural_gas']
    >>> list(df2["in", "trsf", "pp"].columns[:4])
    ['bioenergy_038', 'bioenergy_042', 'bioenergy_045', 'hard_coal_023']
    >>> int(df1.sum().sum())
    1426925322
    >>> int(df2.sum().sum())
    1426925322

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
                        val = "_".join(node.label.subtag.split("_")[agg[2]:])
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


# if __name__ == "__main__":
#     a = download_example_results()
#     exit(0)
#     # from pprint import pprint
#     from matplotlib import pyplot as plt
#     from oemof_visio.plot import io_plot
#
#     my_fn = download_example_results()
#     my_files = search_results(path=TEST_PATH)
#
#     print(my_files)
#
#     filenames = search_results(
#         map=["de22"], heat=["1"], year=["2014"], group_transformer=["0"]
#     )
#     print(filenames)
#     res = restore_energy_system(filenames[0])
#     busses = search_nodes(res.results, solph.Bus, tag="electricity")
#
#     am = [
#         ("cat", "line", "all"),
#         ("tag", "pp", "all"),
#         ("tag", "ee", "all"),
#         ("tag", "chp", "all"),
#     ]
#
#     df = reshape_bus_view(res.results, busses, aggregate=am)
#     df = df.groupby(level=[1, 2, 3, 4], axis=1).sum()
#     print(df.columns)
#     in_order = [
#         ("trsf", "pp", "nuclear"),
#         ("trsf", "pp", "lignite"),
#         ("trsf", "pp", "hard_coal"),
#         ("trsf", "pp", "natural_gas"),
#         ("trsf", "pp", "oil"),
#         ("trsf", "pp", "other"),
#         ("trsf", "pp", "waste"),
#         ("trsf", "pp", "bioenergy"),
#         ("trsf", "pp", "all"),
#         ("trsf", "chp", "all"),
#         ("storage", "electricity", "phes"),
#         ("storage", "electricity", "all"),
#         ("source", "ee", "geothermal"),
#         ("source", "ee", "hydro"),
#         ("source", "ee", "solar"),
#         ("source", "ee", "wind"),
#         ("source", "ee", "all"),
#         ("line", "electricity", "all"),
#         ("shortage", "electricity", "all"),
#     ]
#     out_order = [
#         ("demand", "electricity", "all"),
#         ("excess", "electricity", "all"),
#         ("storage", "electricity", "phes"),
#         ("line", "electricity", "all"),
#     ]
#     # exit(0)
#     io_plot(
#         df_in=df["in"],
#         df_out=df["out"],
#         inorder=in_order,
#         outorder=out_order,
#         smooth=True,
#     )
#     plt.show()
