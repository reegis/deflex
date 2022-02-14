# -*- coding: utf-8 -*-

"""Create a result graph.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import networkx as nx
import pandas as pd
from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize, rgb2hex

from deflex.scenario_tools.helpers import label2str


class Edge:
    """
    An edge of a DeflexGraph

    All attributes can be defined using keyword arguments.

    Attributes
    ----------
    nodes : tuple
        The node where the edge comes from and the node where it goes to.
    label : str
        A string representation of the `nodes` attribute.
    sequence : iterable
        A time series of the flow variable of the edge.
    weight : float
        The sum of the `sequence` attribute.
    color : str
        A color string for plots/drawings of the graph.
    """

    def __init__(self, **kwargs):
        self.nodes = kwargs.get("nodes", None)
        self.label = kwargs.get("label", None)
        self.sequence = kwargs.get("sequence", None)
        self.weight = kwargs.get("weight", None)
        self.color = kwargs.get("color", None)


class DeflexGraph:
    """
    The deflex model graph with a networkx representation.

    The sum of the variables are addedcan be used as weight


    Parameters
    ----------
    results : dict
        Deflex results dictionary.

    Other Parameters
    ----------------
    default_node_color : str
        The default color as a dictionary with the keys "fg" for the
        foreground color (font color) and "bg" for the background color
        (fill color). The color has to be a hexadecimal string. The default
        color is used if no other color is set.
        (default: {"bg": "#6a6a72", "fg": "#000000"}")
    default_edge_color : str
        The default edge color as a hexadecimal string. The default color
        is used if no other color is set.
        (default: "#000000"")

    Attributes
    ----------
    nodes : list
        All nodes of the deflex energy system graph.
    edges : list
        All edges of the deflex energy system graph.
    default_node_color : dict
        The default color for nodes with the keys `bg` for the background
        color and `fg` for text color (foreground).
    default_edge_color : dict
        The default color for edges with the keys `bg` for the background
        color and `fg` for text color (foreground).

    Examples
    --------
    >>> import os
    >>> from deflex import fetch_test_files
    >>> from deflex import restore_results
    >>> from deflex import DeflexGraph
    >>> fn = fetch_test_files("de03_fictive.dflx")
    >>> my_results = restore_results(fn)
    >>> dflx_graph = DeflexGraph(my_results)
    >>> len(dflx_graph.nodes)
    226
    >>> sorted(dflx_graph.nodes)[5].label
    Label(cat='chp plant', tag='other', subtag='other', region='DE01')
    >>> len(dflx_graph.edges)
    323
    >>> dflx_graph.edges[5].label
    'chp-plant_lignite_lignite_DE01 -> heat_district_all_DE01'
    >>> type(dflx_graph.edges[5])
    <class 'deflex.postprocessing.graph.Edge'>
    >>> dflx_graph.edges[5].weight
    136524.0
    >>> nx_graph = dflx_graph.nxgraph()
    >>> nx.number_of_nodes(nx_graph)
    226
    >>> nx.number_weakly_connected_components(nx_graph)
    1
    """

    def __init__(self, results, **kwargs):
        self._results = results
        self._graph = None
        self.default_node_color = kwargs.get(
            "default_node_color", {"bg": "#6a6a72", "fg": "#000000"}
        )
        self.default_edge_color = kwargs.get("default_edge_color", "#000000")
        self.nodes = self._fetch_nodes()
        self.edges = self._fetch_edges()

    def _fetch_edges(self):
        """
        Fetch all edges from the results dictionary and create Edge objects.
        """
        edges = []
        for n in self._results["main"]:
            if n[1] is not None:
                seq = self._results["main"][n]["sequences"]["flow"]
                edges.append(
                    Edge(
                        nodes=n,
                        label="{0} -> {1}".format(
                            label2str(n[0].label), label2str(n[1].label)
                        ),
                        weight=seq.sum(),
                        color=self.default_edge_color,
                        sequence=seq,
                    )
                )
        return edges

    def _fetch_nodes(self):
        """Fetch all nodes from the results dictionary."""
        nodes = [n[0] for n in self._results["main"].keys()]
        nodes.extend(
            [n[1] for n in self._results["main"].keys() if n[1] is not None]
        )
        return list(set(nodes))

    def group_nodes_by_type(self, use_name=False):
        """
        Group all nodes by types returning a dictionary with the types or the
        name of the types as keys and the list of nodes as value.

        The keys of the returning dictionary are the classes (or name of the
        classes) the values are lists with nodes of the corresponding class.

        Parameters
        ----------
        use_name : bool
            Use the name of the class instead of the class as key.

        Returns
        -------
        All nodes sorted by their type : dict

        Examples
        --------
        >>> from deflex import fetch_test_files
        >>> from deflex import restore_results
        >>> from deflex import DeflexGraph
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> my_results = restore_results(fn)
        >>> dflx_graph = DeflexGraph(my_results)
        >>> sorted(dflx_graph.group_nodes_by_type(use_name=True))
        ['Bus', 'GenericStorage', 'Sink', 'Source', 'Transformer']
        >>> list(dflx_graph.group_nodes_by_type(use_name=False))[0].__mro__[-2]
        <class 'oemof.network.network.Node'>
        >>> sources = dflx_graph.group_nodes_by_type(use_name=True)["Source"]
        >>> sorted(sources)[-1].label
        Label(cat='source', tag='volatile', subtag='wind', region='DE03')
        """
        node_groups = {}
        node_types = set([type(n) for n in sorted(self.nodes)])
        for node_type in node_types:
            if use_name is True:
                name = node_type.__name__
            else:
                name = node_type
            node_groups[name] = [
                n for n in self.nodes if isinstance(n, node_type)
            ]
        return node_groups

    def color_nodes_by_type(self, colors, use_name=True):
        """
        Color all nodes in a specific color according to their class.

        Use the :py:meth:`group_nodes_by_type` method to get all existing
        types. Now a color can be assigned to every type using a color
        dictionary. If no color is defined for an existing class the default
        color is used. By default the name of each class is used.

        Parameters
        ----------
          colors : dict
            The dictionary needs to have the class (name of class) as keys and
            a color dictionary as value. The color dictionary has two keys,
            "fg" for the foreground color (font color) and "bg" for the
            background color (fill color) and the color as value. The color has
            to be in the hexadecimal style.
        use_name : bool
            Use the name of the class instead of the class as key. If the class
            is used, the classes also have to be used for the colors as key.

        Examples
        --------
        >>> from deflex import fetch_test_files
        >>> from deflex import restore_results
        >>> from deflex import DeflexGraph
        >>> from oemof import solph
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> my_results = restore_results(fn)
        >>> dflx_graph = DeflexGraph(my_results)
        >>> my_colors = {
        ...     "Bus": {"bg": "#00ff11", "fg": "#000000"},
        ...     "GenericStorage": {"bg": "#efb507", "fg": "#000000"},
        ...     "Transformer": {"bg": "#94221d", "fg": "#000000"},
        ...     "Source": {"bg": "#996967", "fg": "#000000"},
        ...     "Sink": {"bg": "#31306e", "fg": "#ffffff"},
        ... }
        >>> dflx_graph.color_nodes_by_type(my_colors)
        >>> bus = [a for a in dflx_graph.nodes if isinstance(a, solph.Bus)][0]
        >>> getattr(bus, "bgcolor")
        '#00ff11'
        >>> sorted(set([a.bgcolor for a in dflx_graph.nodes]))
        ['#00ff11', '#31306e', '#94221d', '#996967', '#efb507']
        >>> sorted(set([a.fgcolor for a in dflx_graph.nodes]))
        ['#000000', '#ffffff']
        >>> my_colors = {
        ...     solph.Bus: {"bg": "#00ff11", "fg": "#000000"},
        ...     "GenericStorage": {"bg": "#efb507", "fg": "#000000"},
        ...     "Transformer": {"bg": "#94221d", "fg": "#000000"},
        ...     solph.Source: {"bg": "#996967", "fg": "#000000"},
        ...     solph.Sink: {"bg": "#31306e", "fg": "#ffffff"},
        ... }
        >>> dflx_graph.color_nodes_by_type(my_colors, use_name=False)
        >>> bus = [a for a in dflx_graph.nodes if isinstance(a, solph.Bus)][0]
        >>> getattr(bus, "bgcolor")
        '#00ff11'
        >>> sorted(set([a.bgcolor for a in dflx_graph.nodes]))
        ['#00ff11', '#31306e', '#6a6a72', '#996967']
        >>> sorted(set([a.fgcolor for a in dflx_graph.nodes]))
        ['#000000', '#ffffff']
        """
        groups = self.group_nodes_by_type(use_name)
        for ntype, nodes in groups.items():
            type_color = colors.get(ntype, self.default_node_color)
            for n in nodes:
                n.bgcolor = type_color["bg"]
                n.fgcolor = type_color["fg"]
        self._graph = None

    def color_nodes_by_substring(self, colors):
        """
        Color all nodes in a specific color according to a given substring. A
        color can be assigned to every substring using a dictionary with the
        substrings as key an the color dictionary as value. The color
        dictionary needs to have the keys "fg" for the foreground color (font
        color) and "bg" for the background color (fill color). The color has to
        be in the hexadecimal style. Each substring key will be compared with
        the label of the node as string. If no substring match
        the default node color is used. If more than one substring is within
        a label the last match will overwrite the previous matches.

        Parameters
        ----------
        colors : dict
            The dictionary needs to have the substring as keys and a color
            dictionary as value. The color dictionary has two keys, "fg" for
            the foreground color (font color) and "bg" for the background color
            (fill color) and the color as value. The color has to be in the
            hexadecimal style.

        Examples
        --------
        >>> from deflex import fetch_test_files
        >>> from deflex import restore_results
        >>> from deflex import DeflexGraph
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> my_results = restore_results(fn)
        >>> dflx_graph = DeflexGraph(my_results)
        >>> my_colors = {
        ...     "H2": {"bg": "#00ff11", "fg": "#000000"},
        ...     "electricity": {"bg": "#efb507", "fg": "#000000"},
        ...     "bioenergy": {"bg": "#063313", "fg": "#ffffff"},
        ... }
        >>> dflx_graph.color_nodes_by_substring(my_colors)
        >>> mynode = [n for n in dflx_graph.nodes if "bioenergy" in n.label][0]
        >>> getattr(mynode, "bgcolor")
        '#063313'
        >>> sorted(set([n.bgcolor for n in dflx_graph.nodes]))
        ['#00ff11', '#063313', '#6a6a72', '#efb507']
        >>> sorted(set([n.fgcolor for n in dflx_graph.nodes]))
        ['#000000', '#ffffff']

        """
        for node in self.nodes:
            node.bgcolor = self.default_node_color["bg"]
            node.fgcolor = self.default_node_color["fg"]
        for substring, color in colors.items():
            nodes = [n for n in self.nodes if substring in str(n.label)]
            for node in nodes:
                node.bgcolor = color["bg"]
                node.fgcolor = color["fg"]
        self._graph = None

    def color_edges_by_weight(self, cmap="cool", max_weight=None):
        """
        Color all edges by their weight using a matplotlib color map (cmap). If
        no maximum weight is give the highest weight is used.

        Parameters
        ----------
        cmap : str
            Name of the matplotlib color map.
        max_weight : numeric
            The maximum for the normalisation of the weights. All number above
            the max_weight will get the color of the maximum. If no value is
            given the maximum weight of all edges will used.

        Examples
        --------
        >>> from deflex import fetch_test_files
        >>> from deflex import restore_results
        >>> from deflex import DeflexGraph
        >>> from matplotlib.cm import get_cmap
        >>>
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> my_results = restore_results(fn)
        >>> dflx_graph = DeflexGraph(my_results)
        >>> dflx_graph.color_edges_by_weight(cmap="rainbow", max_weight=80)
        >>> edges = dflx_graph.edges
        >>> bus = [edg for edg in edges if "wind" in edg.nodes[0].label][0]
        >>> getattr(bus, "color")
        '#ff0000'
        >>> w = bus.weight
        >>> int(w)
        336973
        >>> rgb2hex(get_cmap("rainbow")(w))
        '#ff0000'
        """
        cmap = get_cmap(cmap)
        if max_weight is None:
            max_weight = self._max_edge_weight()
        norm = Normalize(vmin=0.0, vmax=max_weight)
        for e in self.edges:
            e.color = rgb2hex(cmap(norm(e.weight)))
        self._graph = None

    def _max_edge_weight(self):
        return pd.Series([e.weight for e in self.edges]).max()

    def _create_di_graph(self, weight_exponent=0):
        r"""Create a networkx.DiGraph()."""
        graph = nx.DiGraph()
        for n in self.nodes:
            graph.add_node(
                n.label,
                label=label2str(n.label),
                bg_color=getattr(n, "bgcolor", self.default_node_color["bg"]),
                fg_color=getattr(n, "fgcolor", self.default_node_color["fg"]),
                type=n.__class__.__name__,
            )

        for e in self.edges:
            graph.add_edge(
                e.nodes[0].label,
                e.nodes[1].label,
                label="{0} -> {1}".format(
                    label2str(e.nodes[0].label), label2str(e.nodes[1].label)
                ),
                weigth=format(e.weight * 10 ** weight_exponent, ".1f"),
                color=getattr(e, "color", self.default_edge_color),
            )
        return graph

    def write(self, filename, **kwargs):
        """
        Write the graph into a .graphml file.

        Parameters
        ----------
        filename : str
            Path of the output file e.g. /my/special/path/mygraph.graphml

        Other Parameters
        ----------------
        weight_exponent : int
            The parameter will be passed to the :py:meth:`create_di_graph`
            method.

        Examples
        --------
        >>> import os
        >>> from deflex import fetch_test_files
        >>> from deflex import restore_results
        >>> from deflex import DeflexGraph
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> my_results = restore_results(fn)
        >>> dflx_graph = DeflexGraph(my_results)
        >>> fn_out = fn.replace(".dflx", "_graph.graphml")
        >>> dflx_graph.write(fn_out, weight_exponent=-3)
        >>> os.stat(fn_out).st_size > 0
        True
        >>> os.remove(fn_out)
        """
        nx.write_graphml(self.nxgraph(**kwargs), filename)

    def nxgraph(self, **kwargs):
        r"""
        Get a networkx.DiGraph() from the deflex results.

        Some labels will be added to the edges and nodes.

        Node
        * label: label of the Node as string
        * bg_color: background color of the node for plots or exports
        * fg_color: text color of the node for plots or exports
        * type: name of the node class

        Edge
        * weight: sum of the flow variable
        * color: color of the edge depending of the weight

        Other Parameters
        ----------
        weight_exponent : int
            Shift the decimal point:
            :math:`weight = weight\cdot10^{weight\_exponent}`

        Examples
        --------
        >>> import os
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
        >>> my_results = dflx.restore_results(fn)
        >>> dflx_graph = dflx.DeflexGraph(my_results)
        >>> type(dflx_graph.nxgraph(weight_exponent=-3))
        <class 'networkx.classes.digraph.DiGraph'>
        >>> edges_data = dflx_graph.nxgraph().edges.data()
        >>> wind2bus = [e[2] for e in edges_data if
        ...     e[0].subtag == "wind" and
        ...     e[0].region == "DE01"
        ... ][0]
        >>> wind2bus["label"]
        'source_volatile_wind_DE01 -> electricity_all_all_DE01'
        >>> wind2bus["weigth"], wind2bus["color"]
        ('337.0', '#000000')
        >>> dflx_graph.color_edges_by_weight()
        >>> edges_data = dflx_graph.nxgraph(weight_exponent=-3).edges.data()
        >>> wind2bus = [e[2] for e in edges_data if
        ...     e[0].subtag == "wind" and
        ...     e[0].region == "DE01"
        ... ][0]
        >>> wind2bus["weigth"], wind2bus["color"]
        ('337.0', '#09f6ff')
        >>> nodes_data = dflx_graph.nxgraph().nodes.data()
        >>> wind_node = [n[1] for n in nodes_data if
        ...     n[0].subtag == "wind" and
        ...     n[0].region == "DE01"
        ... ][0]
        >>> wind_node["label"]
        'source_volatile_wind_DE01'
        >>> wind_node['bg_color']
        '#6a6a72'
        >>> wind_node["type"]
        'Source'
        >>> my_colors = {"Source": {"bg": "#996967", "fg": "#000000"}}
        >>> dflx_graph.color_nodes_by_type(my_colors)
        >>> nodes_data = dflx_graph.nxgraph().nodes.data()
        >>> wind_node = [n[1] for n in nodes_data if
        ...     n[0].subtag == "wind" and
        ...     n[0].region == "DE01"
        ... ][0]
        >>> wind_node['bg_color']
        '#996967'
        """
        if (
            self._graph is None
            or kwargs.get("weight_exponent", None) is not None
        ):
            self._graph = self._create_di_graph(
                weight_exponent=kwargs.get("weight_exponent", 0)
            )
        return self._graph
