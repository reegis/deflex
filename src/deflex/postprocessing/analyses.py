# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
from math import ceil

import pandas as pd
from networkx import simple_cycles as nx_simple_cycles
from oemof import solph

from deflex.tools import dict2file

from .graph import DeflexGraph


def label2str(label):
    """
    Convert a label of type `namedtuple` to a simple `string`.

    By default the string representation of a `namedtuple` contains the
    field name and the value names. This function will return a string with
    only the values separated by an underscore. Whitespaces are replaced by
    dashes. This allows it to use it a human readable key.
    """
    return "_".join(map(str, label._asdict().values())).replace(" ", "-")


class Cycles:
    """
    Detect all simple cycles and get the flows of each cycle as
    pandas.DataFrame. For a large number of cycles getting the values may take
    a while so it is possible to skip this step setting the `no_values`
    parameter to True.

    Parameters
    ----------
    results
    storages
    lines
    digits
    no_values

    Examples
    --------
    >>> from deflex.tools import restore_results, fetch_test_files
    >>> fn = fetch_test_files("de03_fictive.dflx")
    >>> c = Cycles(restore_results(fn), storages=True, lines=True)
    >>> len(list(c.simple_cycles))
    9
    >>> c = Cycles(restore_results(fn), storages=False, lines=True)
    >>> len(list(c.simple_cycles))
    7
    >>> c = Cycles(restore_results(fn), storages=False, lines=False)
    >>> len(list(c.simple_cycles))
    2
    """

    def __init__(
        self, results, storages=True, lines=True, digits=10, no_values=False
    ):
        self.name = results["Input data"]["general"]["name"]
        self.storages = storages
        self.lines = lines
        self.simple_cycles = None
        self._detect_simple_cycles(results)
        if no_values is False:
            self.cycles = self._get_cycle_values(results)
        else:
            self.cycles = None
        self.digits = digits

    @property
    def used_cycles(self):
        return self.drop_unused_cycles()

    @property
    def suspicious_cycles(self):
        return self.drop_unsuspicious_cycles()

    def filter_simple_cycles(self):
        if self.storages is False:
            self.simple_cycles = [
                simple_cycle
                for simple_cycle in self.simple_cycles
                if len([c for c in simple_cycle if c.cat != "storage"])
                == len(simple_cycle)
            ]
        if self.lines is False:
            self.simple_cycles = [
                simple_cycle
                for simple_cycle in self.simple_cycles
                if len([c for c in simple_cycle if c.cat != "line"])
                != len(simple_cycle) / 2
            ]

    def _detect_simple_cycles(self, results):
        """
        Detect simple cycles within the directed graph.

        Use a filter to remove know cycles such as storages or power lines.
        e.g. cycle_filter=["storage", "line"]

        Returns
        -------
        generator
        """
        dflx_graph = DeflexGraph(results)
        self.simple_cycles = list(nx_simple_cycles(dflx_graph.get()))
        self.filter_simple_cycles()

    def _get_cycle_values(self, results):
        """
        Get the sum of each flow variable of each cycle as a DataFrame.

        Use a filter to remove know cycles such as storages or power lines.
        e.g. cycle_filter=["storage", "line"]

        Set drop_unused to True to get only cycles where the sum of each flow
        variable is greater zero.
        """
        flows = [f for f in results["main"] if f[1] is not None]

        usages = []
        noc = len(self.simple_cycles)
        noc_base = noc
        if noc_base > 500:
            logging.warning(
                "{} cycles have been found. Getting the flows for all cycles"
                " may take a while. Use the filter function or skip this step"
                " by setting the `no_values` parameter to True.".format(
                    noc_base
                )
            )
        for cycle in self.simple_cycles:
            if noc % ceil(noc_base / 10) == 0:
                if noc_base > 500:
                    print(100 - int(round(noc / (noc_base / 100))), "%")
            noc -= 1
            usage = {}
            for n in range(len(cycle)):
                flow = [
                    f
                    for f in flows
                    if (f[0].label, f[1].label) == (cycle[n - 1], cycle[n])
                ][0]
                name = "{0}_from_{1}".format(n, label2str(flow[0].label))
                usage[name] = results["main"][flow]["sequences"]["flow"]
            usages.append(pd.DataFrame(usage))
        return usages

    def drop_unused_cycles(self):
        """
        Drop cycles that are not used as cycles from a list of cycles.

        Cycles are not in use if one flow of the cycle is zero for all time
        steps.
        """
        if self.cycles is not None:
            return [
                c
                for c in self.cycles
                if not (c.sum().round(self.digits) == 0).any()
            ]
        else:
            return None

    def drop_unsuspicious_cycles(self):
        """
        Drop cycles that are unsuspicious from a list of cycles.

        Suspicious cycles are cycles that have a non-zero value in all flows
        within one time step.

        One can detect all cycles and drop the unsuspicious cycles to get only
        the suspicious ones. A suspicious cycle indicates a problem in the
        model design, so one should have a closer look at all these cycles. A
        typical example for such cycles are storages that a charged and
        discharged in one time step. In some rare cases suspicious cycles are
        fine.
        """

        def rows(frame):
            return frame.loc[(frame.round(self.digits) != 0).all(axis=1)]

        if self.cycles is not None:
            return [c for c in self.cycles if len(rows(c)) > 0]
        else:
            return None

    def detect_suspicious_cycle_rows(self, **kwargs):
        """
        Detect the time steps of a cycle in which all flows are non-zero.

        Set path and filetype to store the results to a file. See
        :func:`~tools.files.dict2file` for more information.
        """
        frames = []
        for frame in self.suspicious_cycles:
            frames.append(
                frame.loc[(frame.round(self.digits) != 0).all(axis=1)]
            )
        if kwargs.get("path") is not None and len(frames) > 0:
            dict2file({str(v.columns[0])[:31]: v for v in frames}, **kwargs)
        else:
            dict2file({"no_suspicious_cycle_found": pd.DataFrame()}, **kwargs)
        return frames

    def __str__(self):
        number = {}
        for p in [
            (self.simple_cycles, "sic"),
            (self.used_cycles, "uc"),
            (self.suspicious_cycles, "suc"),
        ]:
            if p[0] is None:
                number[p[1]] = None
            else:
                number[p[1]] = len(p[0])

        output = "*** Cycle object of scenario: {0} ***\n\n"
        output += "Number of cycles: {0}\n".format(number["sic"])
        output += "Number of used cycles: {0}\n".format(number["uc"])
        output += "Number of critical cycles: {0}\n".format(number["suc"])
        return output.format(self.name)

    def details(self):
        print("**** DETAILS ***************************")
        print()
        if self.cycles is None or len(self.cycles) == 0:
            print("No details available!")
            print()
        else:
            for sc in self.cycles:
                for k, v in sc.items():
                    print(
                        str(k).replace("_from", ""),
                        "->",
                        int(v.sum() / 1000),
                        "->",
                    )
                print()
                print("************************************")
                print("")


def get_all_nodes_from_results(results):
    keys = sorted(list(results["main"].keys()))
    unique_nodes = []
    for nodes in keys:
        unique_nodes.append(nodes[0])
        if nodes[1] is not None:
            unique_nodes.append(nodes[1])
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
    >>> from deflex import tools
    >>> fn = tools.fetch_test_files("de03_fictive.dflx")
    >>> my_results = tools.files.restore_results(fn)
    >>> all_nodes = nodes2table(my_results)
    >>> len(all_nodes)
    226
    >>> all_nodes.to_csv("your/path/file.csv")  # doctest: +SKIP


    """
    unique_nodes = get_all_nodes_from_results(results)
    nodes = []
    for node in unique_nodes:
        dc = {}
        solph_class = type(node)
        label = node.label
        dc["class"] = str(solph_class).split(".")[-1].replace("'>", "")
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


def get_resource_parameters(results, bus):
    """
    Get the parameters of a commodity bus.

    Transformers like power plants are connected to commodity buses. This
    function can be used to get specific emission or the variable costs of the
    connected commodity source.

    Parameters
    ----------
    results : dict
        Deflex results dictionary.
    bus : solph.Bus
        A commodity Bus object.

    Examples
    --------
    >>> from deflex import tools
    >>> fn = tools.fetch_test_files("de03_fictive.dflx")
    >>> my_results = tools.files.restore_results(fn)
    >>> flow_to_power_plant = [
    ...     b for b in my_results["main"].keys()
    ...     if b[1] is not None
    ...     and b[1].label.cat == "power plant"
    ...     and b[1].label.subtag == "natural gas"
    ... ][0]
    >>> get_resource_parameters(my_results, flow_to_power_plant[0]
    ...     )["scalars"].emission
    0.201
    """
    inflow = [
        k
        for k in results["main"].keys()
        if k[1] == bus
        and k[0].label.tag == "commodity"
        and k[0].label.cat == "source"
    ]
    if len(inflow) > 1:
        print("Something went wrong for Bus {0}".format(bus.label))
    if len(inflow) < 1:
        return None
    return results["param"][inflow[0]]


def fetch_converter_parameters(results, transformer):
    """
    Fetch relevant parameters of every Transformer of the energy system.

    Returns
    -------
    pandas.DataFrame
    """

    # Create dictionary with all converters and their in- and outflows.
    df = pd.DataFrame()
    for t in transformer:
        # Get flows of the Transformer
        inflow = [k for k in results["main"].keys() if k[1] == t][0]
        outflows = [k for k in results["main"].keys() if k[0] == t]

        # Get catgeory
        df.loc[t, "category"] = t.label.cat

        # Get parameter of the resource of the Transformer
        fuel_parameter = get_resource_parameters(results, inflow[0])
        if fuel_parameter is not None:
            df.loc[t, "variable costs, fuel"] = fuel_parameter["scalars"].get(
                "variable_costs", 0
            )
            df.loc[t, "emissions, fuel"] = fuel_parameter["scalars"].get(
                "emission", 0
            )

        # Define fuel sector
        fuel = inflow[0].label.subtag
        if fuel == "all":
            df.loc[t, "fuel"] = "{0}, {1}".format(
                inflow[0].label.cat, inflow[0].label.region
            )
        else:
            df.loc[t, "fuel"] = "{0}, {1}".format(fuel, inflow[0].label.region)

        # Get parameter of inflow
        df.loc[t, "variable costs, inflow"] = results["param"][inflow][
            "scalars"
        ].variable_costs
        df.loc[t, "emissions, inflow"] = results["param"][inflow][
            "scalars"
        ].get("emission", float("nan"))

        # Get parameter of outflows
        for outflow in outflows:
            sector = outflow[1].label.cat
            # converter[t]["outflows"][sector] = outflow
            key = "{0}, {1}"
            df.loc[t, key.format("variable costs", sector)] = results["param"][
                outflow
            ]["scalars"].variable_costs
            df.loc[t, key.format("emission", sector)] = results["param"][
                outflow
            ]["scalars"].get("emission", float("nan"))
            df.loc[t, "efficiency, {0}".format(sector)] = results["param"][
                (t, None)
            ]["scalars"][
                "conversion_factors_{}".format(label2str(outflow[1].label))
            ]

    # # Fetch efficiency of heat plants as reference efficiency for chp.
    # for i, row in df.loc[df.category == "chp plant"].iterrows():
    #     df.loc[i, "efficiency, hp_ref"] = df.loc[
    #         (df.fuel == row.fuel) & (df.category == "heat plant"),
    #         "efficiency, heat",
    #     ].mean()
    return df.sort_index(axis=1)


def get_time_index(results):
    key = list(results["main"].keys())[0]
    return results["main"][key]["sequences"].index


def fetch_parameter_of_commodity_sources(results):
    commodity_sources = [
        k
        for k in results["main"].keys()
        if isinstance(k[0], solph.Source)
        and k[0].label.tag == "commodity"
        and k[0].label.cat != "shortage"
    ]

    parameter = pd.DataFrame(
        index=pd.MultiIndex(levels=[[], []], codes=[[], []])
    )
    for c in commodity_sources:
        for k, v in results["param"][c]["scalars"].items():
            if k != "label":
                parameter.loc[(c[0].label.subtag, c[0].label.region), k] = v
    return parameter


def calculate_marginal_costs(df):
    """
    Kosten und Emissionen für jeden Stromtransformer aufstellen.

    Bei CHP müssen die Opportunitätskosten aufgestellt werden.
    1. Die Gesamtkosten auf den Strom abwälzen.
    2. Die als "Abfall" entstanden Wärme pro Stromeinheit berechnen
    3. Die Kosten für eine getrennt Erzeugung von dieser Wärmemenge
       berechnen.
    4. Diese Kosten von den Gesamtkosten abziehen.

    marginal_costs_chp =
    costs_fuel * (1/eta_elec - eta_th/(eta_elec*eta_th_ref))

    Parameters
    ----------
    df

    Returns
    -------

    """
    try:
        df["efficiency, hp_ref"].fillna(1, inplace=True)
    except KeyError:
        df["efficiency, hp_ref"] = 1

    try:
        df["efficiency, heat"].fillna(0, inplace=True)
    except KeyError:
        df["efficiency, heat"] = 0

    df["marginal costs"] = df["variable costs, fuel"] * (
        1 / df["efficiency, electricity"]
        - df["efficiency, heat"]
        / (df["efficiency, electricity"] * df["efficiency, hp_ref"])
    )

    df["emissions"] = df["emissions, fuel"] * (
        1 / df["efficiency, electricity"]
        - df["efficiency, heat"]
        / (df["efficiency, electricity"] * df["efficiency, hp_ref"])
    )
    return df


def fetch_electricity_flows(results):
    return pd.DataFrame(
        {
            k[0]: v["sequences"]["flow"]
            for k, v in results["main"].items()
            if isinstance(k[0], solph.Transformer)
            and k[0].label.cat != "line"
            and k[1].label.cat == "electricity"
        }
    )
    # flow_status = flows.div(flows).fillna(0)


def calculate_key_values(results):
    """

    Returns
    -------

    """
    # Select all converters (class Transformer excluding lines)
    flows = fetch_electricity_flows(results)
    transformer = list(
        set(
            [
                k[0]
                for k in results["main"].keys()
                if isinstance(k[0], solph.Transformer)
                and k[0].label.cat != "line"
            ]
        )
    )

    converter_parameters = fetch_converter_parameters(results, transformer)
    flow_status = flows.div(flows).fillna(0)

    converter_parameters = calculate_marginal_costs(converter_parameters)
    # em_max = flow_status.mul(converter_parameters["emissions"]).max(1)

    kv = pd.DataFrame()

    kv["marginal costs"] = flow_status.mul(
        converter_parameters["marginal costs"]
    ).max(1)
    kv["highest emissions"] = flow_status.mul(
        converter_parameters["emissions"]
    ).max(1)
    kv["lowest emissions"] = flow_status.mul(
        converter_parameters["emissions"]
    ).min(1)

    kv["marginal costs power plant"] = flow_status.mul(
        converter_parameters["marginal costs"]
    ).idxmax(1)
    kv = pd.merge(
        kv,
        converter_parameters["emissions"],
        "left",
        left_on="marginal costs power plant",
        right_index=True,
    )
    return kv


def get_combined_bus_balance(
    results, cat=None, tag=None, subtag=None, region=None
):
    buses = set(
        [r[0] for r in results["Main"].keys() if isinstance(r[0], solph.Bus)]
    )
    if cat is not None:
        buses = [b for b in buses if b.label.cat == cat]
    if tag is not None:
        buses = [b for b in buses if b.label.tag == tag]
    if subtag is not None:
        buses = [b for b in buses if b.label.subtag == subtag]
    if region is not None:
        buses = [b for b in buses if b.label.region == region]
    dc = {}
    for bus in buses:
        inflows = [f for f in results["Main"].keys() if f[1] == bus]
        outflows = [f for f in results["Main"].keys() if f[0] == bus]
        for i in inflows:
            label = i[0].label
            dc[
                ("in", label.cat, label.tag, label.subtag, label.region)
            ] = results["Main"][i]["sequences"]["flow"]
        for i in outflows:
            label = i[1].label
            dc[
                ("out", label.cat, label.tag, label.subtag, label.region)
            ] = results["Main"][i]["sequences"]["flow"]
    return pd.DataFrame(dc).sort_index(axis=1)


def get_converter_balance(
    results, cat=None, tag=None, subtag=None, region=None
):
    converters = set(
        [
            r[0]
            for r in results["Main"].keys()
            if isinstance(r[0], solph.Transformer)
        ]
    )
    if cat is not None:
        converters = [b for b in converters if b.label.cat == cat]
    if tag is not None:
        converters = [b for b in converters if b.label.tag == tag]
    if subtag is not None:
        converters = [b for b in converters if b.label.subtag == subtag]
    if region is not None:
        converters = [b for b in converters if b.label.region == region]
    dc = {}
    for cnv in converters:
        inflows = [f for f in results["Main"].keys() if f[1] == cnv]
        outflows = [f for f in results["Main"].keys() if f[0] == cnv]
        label = cnv.label
        for i in inflows:
            dc[
                ("in", label.cat, label.tag, label.subtag, label.region)
            ] = results["Main"][i]["sequences"]["flow"]
        for o in outflows:
            dc[
                ("out", label.cat, label.tag, label.subtag, label.region)
            ] = results["Main"][o]["sequences"]["flow"]
    return pd.DataFrame(dc).sort_index(axis=1)


if __name__ == "__main__":
    pass
