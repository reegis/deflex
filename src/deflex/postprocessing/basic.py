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


class Edge:
    def __init__(self, **kwargs):
        self.nodes = kwargs.get("key", None)
        self.sequence = kwargs.get("sequence", None)
        self.weight = kwargs.get("weight", None)
        self.color = kwargs.get("color", None)


class DeflexGraph:
    def __init__(self, results, **kwargs):
        self.results = results
        self.default_node_color = kwargs.get(
            "default_node_color", {"bg": "#6a6a72", "fg": "#000000"}
        )
        self.default_edge_color = kwargs.get("default_edge_color", "#000000")
        self.nodes = self.fetch_nodes()
        self.edges = self.fetch_edges()
        self.graph = None

    def fetch_nodes(self):
        nodes = [n[0] for n in self.results["main"].keys()]
        nodes.extend(
            [n[1] for n in self.results["main"].keys() if n[1] is not None]
        )
        return list(set(nodes))

    def group_nodes_by_type(self, use_str=False):
        node_groups = {}
        node_types = set([type(n) for n in self.nodes])
        for node_type in node_types:
            if use_str is True:
                name = node_type.__name__
            else:
                name = node_type
            node_groups[name] = [
                n for n in self.nodes if isinstance(n, node_type)
            ]
        return node_groups

    def color_nodes_by_type(self, colors, use_str=True):
        groups = self.group_nodes_by_type(use_str)
        for ntype, nodes in groups.items():
            type_color = colors.get(ntype, self.default_node_color)
            for n in nodes:
                n.bgcolor = type_color["bg"]
                n.fgcolor = type_color["fg"]
        self.graph = None

    def fetch_edges(self):
        edges = []
        for n in self.results["main"]:
            if n[1] is not None:
                seq = self.results["main"][n]["sequences"]["flow"]
                edges.append(
                    Edge(
                        key=n, weight=seq.sum(), color=self.default_edge_color,
                        sequence=seq
                    )
                )
        return edges

    # def color_nodes(self, color_function, **kwargs):
    #     self.nodes = map(color_function, **kwargs)

    def color_edges_by_weight(self, cmap="cool", max_weight=None):
        cmap = get_cmap(cmap)
        if max_weight is None:
            max_weight = self.max_edge_weight()
        norm = Normalize(vmin=0.0, vmax=max_weight)
        for e in self.edges:
            e.color = rgb2hex(cmap(norm(e.weight)))
        self.graph = None

    def max_edge_weight(self):
        return pd.Series([e.weight for e in self.edges]).max()

    def create_di_graph(self, weight_exponent=0):
        self.graph = nx.DiGraph()
        for n in self.nodes:
            self.graph.add_node(
                str(n.label),
                label=str(n.label),
                bg_color=getattr(n, "bgcolor", self.default_node_color["bg"]),
                fg_color=getattr(n, "fgcolor", self.default_node_color["fg"]),
            )

        for e in self.edges:
            self.graph.add_edge(
                str(e.nodes[0].label),
                str(e.nodes[1].label),
                weigth=format(e.weight * 10 ** weight_exponent, ".1f"),
                color=e.color,
                sequence=str(e.sequence.values)
            )
        return self

    def write(self, filename, **kwargs):
        nx.write_graphml(self.get(**kwargs), filename)

    def get(self, **kwargs):
        if self.graph is None:
            self.create_di_graph(
                weight_exponent=kwargs.get("weight_exponent", 0)
            )
        return self.graph


def nx_graph_from_results(results, filename=None):
    """
    Create a `networkx.DiGraph` for the passed results.

    If a filename is given it is possible to write the file as an `.graphml`
    file. See http://networkx.readthedocs.io/en/latest/ for more information.

    Parameters
    ----------
    results : dict
        A deflex result dictionary.

    filename : str
        Absolute filename (with path) to write your graph in the graphml
        format. If no filename is given no file will be written.

    Examples
    --------
    >>> import os
    >>> from deflex.postprocessing import restore_results
    >>> from deflex.postprocessing import dict2file
    >>> from deflex.postprocessing import nx_graph_from_results
    >>> from deflex.tools import fetch_test_files
    >>> fn = fetch_test_files("de03_fictive.dflx")
    >>> my_results = restore_results(fn)
    >>> my_graph = nx_graph_from_results(my_results)
    >>> nx.number_of_nodes(my_graph)
    231
    >>> nx.number_weakly_connected_components(my_graph)
    3
    >>> fn_out = fn.replace(".dflx", "_graph.graphml")
    >>> my_graph = nx_graph_from_results(my_results, fn_out)
    >>> os.path.isfile(fn_out)
    True
    >>> os.remove(fn_out)

    Notes
    -----
    Needs the networkx (>= v.1.11) package to work .
    """
    # construct graph from nodes and flows
    grph = nx.DiGraph()

    # get all nodes
    nodes = [n[0] for n in results["main"].keys()]
    nodes.extend([n[1] for n in results["main"].keys() if n[1] is not None])
    nodes = set(nodes)

    if filename is not None:
        if filename[-8:] != ".graphml":
            filename = filename + ".graphml"
        nx.write_graphml(grph, filename)
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
    # import pprint as pp
    from matplotlib.cm import get_cmap
    from matplotlib.colors import rgb2hex, Normalize

    # my_cmap = get_cmap("cool")
    # print(rgb2hex(my_cmap(0.2)))
    # print(my_cmap(0.2, bytes=True))
    # exit(0)
    # fn = "/home/uwe/.deflex/tmp_test_32traffic_43/de03_fictive.dflx"
    fn = "/home/uwe/.deflex/pedro/2030-DE02-Agora4.dflx"
    # get_results_graph(fn)
    # exit(0)
    my_results = restore_results(fn)
    dg = DeflexGraph(my_results)
    # my_colors = {
    #     "commodity_all_H2": {"bg": "#00ff11", "fg": "#000000"},
    #     "electricity": {"bg": "#efb507", "fg": "#000000"},
    #     "heat": {"bg": "#94221d", "fg": "#000000"},
    #     "commodity_all_other heat": {"bg": "#996967", "fg": "#000000"},
    #     "commodity_all_syn-fuel": {"bg": "#9969c3", "fg": "#000000"},
    #     "commodity_all_bioenergy": {"bg": "#063313", "fg": "#ffffff"},
    #     "commodity_all_other-elect": {"bg": "#c07b56", "fg": "#000000"},
    #     "commodity_all_oil": {"bg": "#1d101b", "fg": "#ffffff"},
    #     "mobility": {"bg": "#31306e", "fg": "#ffffff"},
    #     "default": {"bg": "#6a6a72", "fg": "#000000"},
    # }

    my_colors = {
        "Bus": {"bg": "#00ff11", "fg": "#000000"},
        "GenericStorage": {"bg": "#efb507", "fg": "#000000"},
        "Transformer": {"bg": "#94221d", "fg": "#000000"},
        "Source": {"bg": "#996967", "fg": "#000000"},
        "Sink": {"bg": "#31306e", "fg": "#ffffff"},
        "default": {"bg": "#6a6a72", "fg": "#000000"},
    }

    dg.color_nodes_by_type(my_colors)
    dg.color_edges_by_weight()
    dg.write(fn.replace(".dflx", "_graph.graphml"), weight_exponent=-6)

    # pp.pprint(ng)
    # nx_graph_from_results(my_results, fn.replace(".dflx", ".graphml"))
    exit(0)
    all_results = get_all_results(my_results)
    fn_out = fn.replace(".dflx", "_all_results.csv")
    dict2file(all_results, fn_out, "csv", drop_empty_columns=True)
