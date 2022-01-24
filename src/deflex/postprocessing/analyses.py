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
    def __init__(self, results, cycle_filter=None):
        """
        Detect all simple cycles.

        This is the main function

        """
        self._filter = None
        self.simple_cycles = list(self._detect_simple_cycles(results))
        self.cycles = self._get_cycle_values(results)
        self.digits = 10

    @property
    def used_cycles(self):
        return self.drop_unused_cycles()

    @property
    def suspicious_cycles(self):
        return self.drop_unsuspicious_cycles()

    @property
    def filter(self):
        return self._filter

    def add_filter(self, cycle_filter):
        if isinstance(cycle_filter, str):
            cycle_filter = [cycle_filter]
        if self._filter is not None:
            self._filter.extend(cycle_filter)
        else:
            self._filter = cycle_filter
        for phrase in cycle_filter:
            self.simple_cycles = [
                c for c in self.simple_cycles if phrase not in str(c)
            ]
            self.cycles = [
                c for c in self.cycles if phrase not in str(c.columns)
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
        if self._filter is None:
            cycle_filter = []
        else:
            cycle_filter = self._filter
        cycles = simple_cycles(dflx_graph.get())
        for phrase in cycle_filter:
            cycles = [c for c in cycles if phrase not in str(c)]
        return cycles

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
        for cycle in self.simple_cycles:
            usage = pd.DataFrame()
            for n in range(len(cycle)):
                flow = [
                    f
                    for f in flows
                    if (f[0].label, f[1].label) == (cycle[n - 1], cycle[n])
                ][0]
                name = "{0}_from_{1}".format(n, label2str(flow[0].label))
                usage[name] = results["main"][flow]["sequences"]["flow"]
            usages.append(usage)
        return usages

    def drop_unused_cycles(self):
        """
        Drop cycles that are not used as cycles from a list of cycles.

        Cycles are not in use if one flow of the cycle is zero for all time steps.
        """
        return [
            c
            for c in self.cycles
            if not (c.sum().round(self.digits) == 0).any()
        ]

    def drop_unsuspicious_cycles(self):
        """
        Drop cycles that are unsuspicious from a list of cycles.

        Suspicious cycles are cycles that have a non-zero value in all flows within
        one time step.

        One can detect all cycles and drop the unsuspicious cycles to get only the
        suspicious ones. A suspicious cycle indicates a problem in the model
        design, so one should have a closer look at all these cycles. A typical
        example for such cycles are storages that a charged and discharged in one
        time step. In some rare cases suspicious cycles are fine.
        """

        def rows(frame):
            return frame.loc[(frame.round(self.digits) != 0).all(axis=1)]

        return [c for c in self.cycles if len(rows(c)) > 0]

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

    def print(self, details=False):
        print("**** OVERVIEW **************************")
        print()
        print("Number of cycles:", len(self.cycles))
        print("Number of used cycles:", len(self.used_cycles))
        print("Number of critical cycles:", len(self.suspicious_cycles))
        print()
        if details:
            print("**** DETAILS ***************************")
            print()
            if len(self.cycles) == 0:
                print("No details available!")
                print()
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


def old_Stuff(results):
    dflx_graph = DeflexGraph(results)
    s_cycles = simple_cycles(dflx_graph.get())
    t_flows = [
        f for f in results["main"] if isinstance(f[0], solph.Transformer)
    ]
    buses = set([f[0] for f in results["main"] if isinstance(f[0], solph.Bus)])
    e_buses = [b.label for b in buses if b.label.cat == "electricity"]
    for bus in e_buses:
        print(repr(bus))
    for sc in s_cycles:
        print("QQQQQ", sc)
        for n in sc:
            print(n)
    # for tf in t_flows:
    #     # print(results["param"][(tf[0], None)])
    #     # print(results["param"][tf])
    #     print(tf[0])
    #     for k in tf[0].conversion_factors.keys():
    #         if k == tf[1]:
    #             print("Key exists")
    #             print(hash(k) == hash(tf[1]))
    #     if tf[1] in tf[0].conversion_factors:
    #         print("Key in keys")
    #     else:
    #         print("Key not in keys")
    #     print(hash(tf[1]))
    #     print("*********************next step")
    #     # print(tf[0].conversion_factors[tf[1]][0])
    # exit(0)
    flows = [k for k in results["main"].keys() if k[1] is not None]
    cvf = list()
    for c in s_cycles:
        # print(set(c))
        # print(set(e_buses))
        print(set(c).intersection(set(e_buses)))
        print("######################")
        if "cat='storage'" not in str(c) and "cat='line'" not in str(c):
            # if 1 == 1:
            # print(c)
            if len(set(c).intersection(set(e_buses))) > 0:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            for a in range(len(c)):
                flow = [
                    f
                    for f in flows
                    if (f[0].label, f[1].label) == (c[a - 1], c[a])
                ][0]
                if getattr(flow[0], "conversion_factors", None) is not None:
                    print("******", flow[0], "********")
                    inflow = [
                        k for k in results["main"].keys() if k[1] == flow[0]
                    ][0]
                    print(results["main"][inflow]["sequences"]["flow"].sum())
                    print(results["param"][(flow[0], None)]["scalars"])
                    label_name = "_".join(
                        map(str, flow[1].label._asdict().values())
                    ).replace(" ", "-")
                    temp = results["param"][(flow[0], None)]["scalars"][
                        "conversion_factors_{0}".format(label_name)
                    ]
                    print(temp)
                    cvf.append(temp)
                    print(results["main"][flow]["sequences"]["flow"].sum())
    print("§§§§§")
    print(cvf)
    print(reduce(operator.mul, cvf, 1))


def get_all_nodes_from_results(results):
    keys = sorted(list(results["main"].keys()))
    unique_nodes = []
    for nodes in keys:
        unique_nodes.append(nodes[0])
        if nodes[1] is not None:
            unique_nodes.append(nodes[1])
    return set(unique_nodes)


def nodes2table(results):
    """
    Get a table with all nodes (class, category, tag, subtag, region) from a
    results dictionary.

    Parameters
    ----------
    results : dict

    Returns
    -------
    Table with all nodes : pandas.DataFrame

    Examples
    --------
    >>> from deflex import tools
    >>> from deflex import postprocessing
    >>> fn = tools.fetch_test_files("de03_fictive.dflx")
    >>> my_results = postprocessing.restore_results(fn)
    >>> all_nodes = nodes2table(my_results)
    >>> len(all_nodes)
    238
    >>> all_nodes.to_csv("your/path/file.csv")  # doctest: +SKIP


    """
    unique_nodes = get_all_nodes_from_results(results)
    df = pd.DataFrame()
    n = 0
    for node in unique_nodes:
        solph_class = type(node)
        label = node.label
        n += 1
        df.loc[n, "class"] = str(solph_class).split(".")[-1].replace("'>", "")
        df.loc[n, "cat"] = label.cat
        df.loc[n, "tag"] = label.tag
        df.loc[n, "subtag"] = label.subtag
        df.loc[n, "region"] = label.region
    df.sort_values(by=list(df.columns), inplace=True)
    return df.reset_index(drop=True)


def get_resource_parameter(results, bus):
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
        fuel_parameter = get_resource_parameter(results, inflow[0])
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


def fetch_volatile_electricity_sources(results):
    """

    Parameters
    ----------
    results

    Returns
    -------
    pandas.DataFrame

    """
    volatile_sources = [
        k
        for k in results["main"].keys()
        if isinstance(k[0], solph.Source) and k[0].label.tag == "volatile"
    ]
    sources = pd.DataFrame(
        columns=pd.MultiIndex(levels=[[], []], codes=[[], []])
    )

    for src in volatile_sources:
        sources[src[0].label.subtag, src[0].label.region] = results["main"][
            src
        ]["sequences"]["flow"]
    return sources


def _calculate_emissions_from_energy_table(table, emissions, sector):
    emission_table = table["in"].mul(emissions)
    emission_table = pd.concat([emission_table], axis=1, keys=["in"])
    emission_table["out", sector] = emission_table["in"].sum(axis=1)
    table = pd.concat(
        [table, emission_table],
        axis=1,
        keys=["energy", "emission"],
    )
    table.sort_index(axis=1, inplace=True)
    for column in table["energy", "out"].columns:
        emissions[(sector, column[1])] = table[
            "emission", "out", sector
        ] / table["energy", "out"].sum(axis=1)

    return table


def _add_emissions2emissions_table():
    pass


def _add_volatiles_to_electricity_table(tables, results):
    # Add volatile source to electricity table
    volatile_output_by_region = (
        fetch_volatile_electricity_sources(results)
        .groupby(level=1, axis=1)
        .sum()
    )

    for region in volatile_output_by_region.columns:
        if ("out", ("electricity", region)) in tables["electricity"]:
            tables["electricity"][
                "out", ("electricity", region)
            ] += volatile_output_by_region[region]
        else:
            tables["electricity"][
                "out", ("electricity", region)
            ] = volatile_output_by_region[region]
        tables["electricity"][
            "in", ("volatiles", region)
        ] = volatile_output_by_region[region]
    return tables


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
    # df.to_excel("/home/uwe/0000000000000_temp.xlsx")
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
    em_max = flow_status.mul(converter_parameters["emissions"]).max(1)

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


def energy_balance_by_sector(results, chp_method, **kwargs):
    from matplotlib import pyplot as plt

    # Create a dictionary of empty tables (pandas.DataFrame) for all sectors
    tables = {}
    mcol = pd.MultiIndex(levels=[[], []], codes=[[], []])
    time_index = get_time_index(results)
    for f in transformer:
        for k1 in f["out"].keys():
            tables.setdefault(
                k1[0], pd.DataFrame(columns=mcol, index=time_index)
            )
            tables[k1[0]]["out", k1] = 0
            for k2 in f["in"].keys():
                tables[k1[0]]["in", k2] = 0

    # Assign inflows to cumulated product flows (fill empty tables from above)
    for f in transformer:
        if len(f["out"]) == 1:
            fuel_factors = None
        else:
            fuel_factors = allocate_fuel(method=chp_method, **kwargs)

        for sector, outflow in f["out"].items():
            tables[sector[0]]["out", sector] += results["main"][outflow][
                "sequences"
            ]["flow"]
            for fuel, inflow in f["in"].items():
                tables[sector[0]]["in", fuel] += results["main"][inflow][
                    "sequences"
                ]["flow"] * getattr(fuel_factors, sector[0], 1)

    tables = _add_volatiles_to_electricity_table(tables, results)
    return tables


def calculate_product_fuel_balance(
    results, chp_method, sectors=None, **kwargs
):
    tables = energy_balance_by_sector(results, chp_method, **kwargs)

    time_index = get_time_index(results)

    # get a series with the emissions of each commodity
    emissions = fetch_parameter_of_commodity_sources(results)["emission"]
    emissions.index = emissions.index.to_flat_index()
    emission_series = (
        pd.DataFrame(index=time_index, columns=emissions.index)
        .fillna(1)
        .mul(emissions)
    )

    # calculate the emissions of the electricity sector first to use it
    # in the other sectors e.g. heat from electricity
    if sectors is None:
        sectors = ["electricity"]

    sectors.extend([k for k in tables.keys() if k not in sectors])

    for sector in sectors:
        tables[sector] = _calculate_emissions_from_energy_table(
            tables[sector], emission_series, sector
        )

    tables["emissions"] = emissions.reindex(emissions.index)

    return tables


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
