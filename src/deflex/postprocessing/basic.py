# -*- coding: utf-8 -*-

"""Basic result processing.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
import matplotlib.patches as patches
import networkx as nx
import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

from deflex import DeflexScenario
from deflex import scenario


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


def bus_flows2tables(results, bus_groups):
    levels = [[], [], [], [], [], [], [], []]
    tables = {}
    for key, buses in bus_groups.items():
        seq = pd.DataFrame(columns=pd.MultiIndex(levels=levels, codes=levels))
        name = "_".join(key).replace("_all", "")
        for bus in buses:
            flows = [k for k in results["main"].keys() if k[1] == bus]
            flows.extend([k for k in results["main"].keys() if k[0] == bus])
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
        tables[name] = seq.sort_index(axis=1)

    return tables


def group_buses(buses, fields):
    groups = {}
    for b in buses:
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
    SOMETHING

    Parameters
    ----------
    results

    Returns
    -------

    Examples
    --------
    >>> import os
    >>> from deflex.postprocessing import restore_results, dict2file
    >>> from deflex.tools import fetch_test_files
    >>> fn = fetch_test_files("de03_fictive.dflx")
    >>> my_results = restore_results(fn)
    >>> all_results = get_all_results(my_results)
    >>> sorted(list(all_results.keys()))[:4]
    ['commodity', 'electricity', 'heat_decentralised', 'heat_district']
    >>> sorted(list(all_results.keys()))[-5:]
    ['heat_district', 'meta', 'mobility', 'pyomo', 'storages']
    >>> fn_out = fn.replace(".dflx", "_all_results.csv")
    >>> dict2file(all_results, fn_out, "csv", drop_empty_columns=True)
    >>> my_bool = []
    >>> for key in all_results.keys():
    ...     fn_test = os.path.join(fn_out, key + ".csv")
    ...     my_bool.append(os.path.isfile(fn_test))
    >>> my_bool
    [True, True, True, True, True, True, True, True]
    """
    buses = set(
        [k[0] for k in results["main"].keys() if isinstance(k[0], solph.Bus)]
    )

    bus_groups = group_buses(buses, ["cat", "tag"])
    tables = bus_flows2tables(results, bus_groups)
    tables["storages"] = storage_results2table(results)
    tables["pyomo"] = pyomo_results2series(results)
    tables["meta"] = meta_results2series(results)
    return tables


def nx_graph_from_results(results, filename):
    """
    Create a `networkx.DiGraph` for the passed energy system and plot it.
    See http://networkx.readthedocs.io/en/latest/ for more information.

    Parameters
    ----------
    energy_system : `oemof.solph.network.EnergySystem`

    filename : str
        Absolute filename (with path) to write your graph in the graphml
        format. If no filename is given no file will be written.

    remove_nodes: list of strings
        Nodes to be removed e.g. ['node1', node2')]

    remove_nodes_with_substrings: list of strings
        Nodes that contain substrings to be removed e.g. ['elec', 'heat')]

    remove_edges: list of string tuples
        Edges to be removed e.g. [('resource_gas', 'gas_balance')]

    Examples
    --------
    >>> import os
    >>> import pandas as pd
    >>> from oemof.solph import (Bus, Sink, Transformer, Flow, EnergySystem)
    >>> import oemof.graph as grph
    >>> datetimeindex = pd.date_range('1/1/2017', periods=3, freq='H')
    >>> es = EnergySystem(timeindex=datetimeindex)
    >>> b_gas = Bus(label='b_gas', balanced=False)
    >>> bel1 = Bus(label='bel1')
    >>> bel2 = Bus(label='bel2')
    >>> demand_el = Sink(label='demand_el',
    ...                  inputs = {bel1: Flow(nominal_value=85,
    ...                            actual_value=[0.5, 0.25, 0.75],
    ...                            fixed=True)})
    >>> pp_gas = Transformer(label=('pp', 'gas'),
    ...                            inputs={b_gas: Flow()},
    ...                            outputs={bel1: Flow(nominal_value=41,
    ...                                                variable_costs=40)},
    ...                            conversion_factors={bel1: 0.5})
    >>> line_to2 = Transformer(label='line_to2',
    ...                        inputs={bel1: Flow()}, outputs={bel2: Flow()})
    >>> line_from2 = Transformer(label='line_from2',
    ...                          inputs={bel2: Flow()}, outputs={bel1: Flow()})
    >>> es.add(b_gas, bel1, demand_el, pp_gas, bel2, line_to2, line_from2)
    >>> my_graph = grph.create_nx_graph(es)
    >>> # export graph as .graphml for programs like Yed where it can be
    >>> # sorted and customized. this is especially helpful for large graphs
    >>> # grph.create_nx_graph(es, filename="my_graph.graphml")
    >>> [my_graph.has_node(n)
    ...  for n in ['b_gas', 'bel1', "('pp', 'gas')", 'demand_el', 'tester']]
    [True, True, True, True, False]
    >>> list(nx.attracting_components(my_graph))
    [{'demand_el'}]
    >>> sorted(list(nx.strongly_connected_components(my_graph))[1])
    ['bel1', 'bel2', 'line_from2', 'line_to2']
    >>> new_graph = grph.create_nx_graph(energy_system=es,
    ...                                  remove_nodes_with_substrings=['b_'],
    ...                                  remove_nodes=["('pp', 'gas')"],
    ...                                  remove_edges=[('bel2', 'line_from2')],
    ...                                  filename='test_graph')
    >>> [new_graph.has_node(n)
    ...  for n in ['b_gas', 'bel1', "('pp', 'gas')", 'demand_el', 'tester']]
    [False, True, False, True, False]
    >>> my_graph.has_edge("('pp', 'gas')", 'bel1')
    True
    >>> new_graph.has_edge('bel2', 'line_from2')
    False
    >>> os.remove('test_graph.graphml')

    Notes
    -----
    Needs graphviz and networkx (>= v.1.11) to work properly.
    Tested on Ubuntu 16.04 x64 and solydxk (debian 9).
    """
    # construct graph from nodes and flows
    grph = nx.DiGraph()

    # get all nodes
    nodes = [n[0] for n in results["main"].keys()]
    nodes.extend([n[1] for n in results["main"].keys() if n[1] is not None])
    nodes = set(nodes)

    colors = {
        "commodity_all_H2": {"bg": "#00ff11", "fg": "#000000"},
        "electricity": {"bg": "#efb507", "fg": "#000000"},
        "heat": {"bg": "#94221d", "fg": "#000000"},
        "commodity_all_other heat": {"bg": "#996967", "fg": "#000000"},
        "commodity_all_syn-fuel": {"bg": "#9969c3", "fg": "#000000"},
        "commodity_all_bioenergy": {"bg": "#063313", "fg": "#ffffff"},
        "commodity_all_other-elect": {"bg": "#c07b56", "fg": "#000000"},
        "commodity_all_oil": {"bg": "#1d101b", "fg": "#ffffff"},
        "mobility": {"bg": "#31306e", "fg": "#ffffff"},
        "default": {"bg": "#6a6a72", "fg": "#000000"},
    }

    # add nodes
    for n in nodes:
        if isinstance(n, solph.Bus):
            for k, c in colors.items():
                if k in str(n.label):
                    color = c

        else:
            color = colors["default"]
        grph.add_node(
            str(n.label),
            label=str(n.label),
            bg_color=color["bg"],
            fg_color=color["fg"],
        )

    # add labeled flows on directed edge if an optimization_model has been
    # passed or undirected edge otherwise
    for n in nodes:
        for i in [f[0] for f in results["main"].keys() if f[1] == n]:
            weight = (
                results["main"][(i, n)]["sequences"]["flow"].sum() / 10 ** 6
            )
            grph.add_edge(str(i.label), str(n.label))
            # if weight is None:
            #     grph.add_edge(str(i.label), str(n.label))
            # else:
            grph.add_edge(
                str(i.label), str(n.label), weigth=format(weight, ".1f")
            )
    print("**********************")
    for g in grph.edges:
        print(g)

    if filename is not None:
        if filename[-8:] != ".graphml":
            filename = filename + ".graphml"
        nx.write_graphml(grph, filename)

    print(colors)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    w = 0.5
    h = 1 / 15
    x = 0
    y = 0
    for k, c in colors.items():
        pos1 = (x, y)
        pos2 = (x + w / 2, y + h / 2)
        ax.add_patch(patches.Rectangle(pos1, w, h, color=c["bg"]))
        ax.annotate(k, xy=pos2, color=c["fg"], ha="center", va="center")
        y += h
    plt.show()

    return grph


def get_results_graph(path, scenario_class=DeflexScenario):
    sc = scenario.restore_scenario(path, scenario_class=scenario_class)
    print(sc.es)
    graph = sc.plot_nodes()
    for g in graph:
        print(g)


if __name__ == "__main__":
    from deflex.postprocessing import dict2file
    from deflex.postprocessing import get_all_results
    from deflex.postprocessing import restore_results

    # fn = "/home/uwe/.deflex/tmp_test_32traffic_43/de03_fictive.dflx"
    fn = "/home/uwe/.deflex/pedro_new/2050-DE02-Agora2.dflx"
    # get_results_graph(fn)
    # exit(0)
    my_results = restore_results(fn)
    nx_graph_from_results(my_results, fn.replace(".dflx", ".graphml"))
    exit(0)
    all_results = get_all_results(my_results)
    fn_out = fn.replace(".dflx", "_all_results.csv")
    dict2file(all_results, fn_out, "csv", drop_empty_columns=True)
