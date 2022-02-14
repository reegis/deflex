# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
from math import ceil, isnan

import pandas as pd
from networkx import simple_cycles as nx_simple_cycles
from oemof import solph

from deflex.postprocessing.graph import DeflexGraph
from deflex.scenario_tools.helpers import label2str
from deflex.tools.chp import allocate_fuel_deflex


class Cycles:
    """
    Detect all simple cycles in the directed graph.

    Furthermore, get the flows of each cycle as pandas.DataFrame. For a large
    number of cycles getting the values may take a while so check the
    `simple_cycles` attribute first and consider setting `storages` and `lines`
    to `False`.

    Cycles are a list of nodes with a flow between one node and the following
    node in the list and a flow from the last node of the lsit to the first
    node. Therefore, the number of nodes equals the number of flows.

    Parameters
    ----------
    results : dict
        A valid deflex results dictionary.
    storages : bool
        Storages are always cycles and you may want to exclude them from the
        results setting `storages=False`. Nevertheless, sometimes storages are
        charged and discharged in one time step, which indicates a modelling
        problem. To detect such behaviour `storages` should be `True`.
        (default: True)
    lines : bool
        Transmission lines will create multiple cycles especially in models
        with a high number of regions and line. Setting `lines` to `False` will
        exclude cycles that are caused by lines. Cycles with e.g. an
        electrolyses in one region and a H2 power plant in another will cause
        a hydrogen-electricity cycle. In this cycle is a transmission line
        include but this cycle will not(!) be excluded if `lines=False`.
        (default: True)
    digits : int
        To detect used or critical cycles the flows are rounded to avoid a
        detection for very small flow values. Use `digits` to define the number
        of digits to be rounded. A high number will make the detection very
        sensitive. (default: 10)

    Attributes
    ----------
    name : str
        Name of the cycle object.
    simple_cycles: list of lists
        A list of all cycles. Each cycle is a list of nodes.

    Examples
    --------
    >>> from deflex import restore_results, fetch_test_files
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

    def __init__(self, results, storages=True, lines=True, digits=10):
        self.name = results["Input data"]["general"]["name"]
        self.simple_cycles = list(
            nx_simple_cycles(DeflexGraph(results).nxgraph())
        )
        self._filter_simple_cycles(storages, lines)
        self._main_results = results["main"]
        self._cycles = None
        self._digits = digits

    @property
    def cycles(self):
        """
        Get all cycles of the model.

        Cycles are a list of nodes with a flow between one node and the
        following node in the list and a flow from the last node of the lsit
        to the first node. Therefore, the number of nodes equals the number of
        flows.

        Returns
        -------
        list of pandas.DataFrame

        Examples
        --------
        >>> from deflex import restore_results, fetch_test_files, Cycles
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> cy = Cycles(restore_results(fn), storages=True, lines=True)
        >>> len(cy.cycles)
        9
        >>> len(cy.used_cycles)
        2
        >>> type(cy.used_cycles[0])
        <class 'pandas.core.frame.DataFrame'>
        """
        if self._cycles is None:
            self._cycles = self._get_cycle_values()
        return self._cycles

    @property
    def used_cycles(self):
        """
        Get all cycles from a list of cycles that are used.

        Cycles are not in use if one flow of the cycle is zero for all time
        steps.

        Returns
        -------
        list of pandas.DataFrame

        Examples
        --------
        >>> from deflex import restore_results, fetch_test_files, Cycles
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> cy = Cycles(restore_results(fn), storages=True, lines=True)
        >>> len(cy.cycles)
        9
        >>> len(cy.used_cycles)
        2
        >>> type(cy.used_cycles[0])
        <class 'pandas.core.frame.DataFrame'>
        """
        return [
            c
            for c in self.cycles
            if not (c.sum().round(self._digits) == 0).any()
        ]

    @property
    def suspicious_cycles(self):
        """
        Get all cycles from a list of cycles that are suspicious.

        Suspicious cycles are cycles that have a non-zero value in all flows
        within one time step.

        One can detect all cycles and drop the unsuspicious cycles to get only
        the suspicious ones. A suspicious cycle indicates a problem in the
        model design, so one should have a closer look at all these cycles. A
        typical example for such cycles are storages that a charged and
        discharged in one time step. In some rare cases suspicious cycles are
        fine.

        Examples
        --------
        >>> from deflex import restore_results, fetch_test_files, Cycles
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> cy = Cycles(restore_results(fn), storages=True, lines=True)
        >>> len(list(cy.simple_cycles))
        9
        >>> len(cy.suspicious_cycles)
        0
        """

        def rows(frame):
            return frame.loc[(frame.round(self._digits) != 0).all(axis=1)]

        return [c for c in self.cycles if len(rows(c)) > 0]

    def get_suspicious_time_steps(self):
        """
        Detect the time steps of a cycle in which all flows are non-zero.

        Returns
        -------
        One table for each cycle with all suspicious rows.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de03_suspicious_modelling.dflx")
        >>> my_results = dflx.restore_results(fn)
        >>> c = Cycles(my_results)
        >>> len(list(c.simple_cycles))
        7
        >>> len(c.used_cycles)
        1
        >>> len(c.suspicious_cycles)
        1
        >>> c.get_suspicious_time_steps()[0].iloc[5]
        0_from_storage_electricity_battery_DE01    317596.81
        1_from_electricity_all_all_DE01            289581.37
        Name: 2022-01-01 05:00:00, dtype: float64

        """
        frames = []
        for frame in self.suspicious_cycles:
            frames.append(
                frame.loc[(frame.round(self._digits) != 0).all(axis=1)]
            )
        return frames

    def print(self):
        """
        Print an overview of the cycles.

        Examples
        --------
        >>> from deflex import restore_results, fetch_test_files, Cycles
        >>> fn = fetch_test_files("de03_fictive.dflx")
        >>> cy = Cycles(restore_results(fn), storages=True, lines=True)
        >>> cy.print()
        *** Cycle object of scenario: de03_fictive_test ***
        <BLANKLINE>
        Number of cycles: 9
        Number of used cycles: 2
        Number of critical cycles: 0
        <BLANKLINE>
        """
        print(self)

    def details(self):
        """Print out a more detailed overview over the existing cycles."""
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

    def __str__(self):
        number = {}
        for p in [
            (self.cycles, "sic"),
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

    def _filter_simple_cycles(self, storages, lines):
        """
        Use a filter to remove know cycles such as storages or power lines.
        """
        if storages is False:
            self.simple_cycles = [
                simple_cycle
                for simple_cycle in self.simple_cycles
                if len([c for c in simple_cycle if c.cat != "storage"])
                == len(simple_cycle)
            ]
        if lines is False:
            self.simple_cycles = [
                simple_cycle
                for simple_cycle in self.simple_cycles
                if len([c for c in simple_cycle if c.cat != "line"])
                != len(simple_cycle) / 2
            ]

    def _get_cycle_values(self):
        """
        Get the time series of each flow variable of each cycle as a DataFrame.

        Use a filter to remove know cycles such as storages or power lines.
        e.g. cycle_filter=["storage", "line"]

        Set drop_unused to True to get only cycles where the sum of each flow
        variable is greater zero.

        Returns
        -------
        list of pandas.DataFrame
        """
        flows = [f for f in self._main_results if f[1] is not None]

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

            # Sort the list to find the first object of a sorted list and find
            # the postion of this object in the unsorted list. Then rotate the
            # list, so that this object is on the first position. This makes
            # the results persistent.
            first = sorted(cycle, key=lambda x: str(x))[0]
            idx_first = cycle.index(first)
            cycle = cycle[idx_first:] + cycle[:idx_first]

            if noc % ceil(noc_base / 10) == 0:
                if noc_base > 500:
                    print(100 - int(round(noc / (noc_base / 100))), "%")
            noc -= 1
            usage = {}
            for n in range(len(cycle)):
                logging.warning((cycle[n - 1], cycle[n]))
                flow = [
                    f
                    for f in flows
                    if (f[0].label, f[1].label) == (cycle[n - 1], cycle[n])
                ][0]
                name = "{0}_from_{1}".format(n, label2str(flow[0].label))
                usage[name] = self._main_results[flow]["sequences"]["flow"]
            usages.append(pd.DataFrame(usage))
        return usages


def _allocate_outflows(eta_e, eta_th):
    method = "finnish"
    if isnan(eta_e):
        method = "heat"
    if isnan(eta_th):
        method = "electricity"
    allocation = allocate_fuel_deflex(method, eta_e, eta_th)._asdict()
    allocation["method"] = method
    return allocation


def fetch_converter_parameters(results, transformer, remove_null_columns=True):
    """
    Fetch relevant parameters of every Transformer of the energy system.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> power_plants = [
    ...     bk[1] for bk in my_results["main"].keys()
    ...     if bk[1] is not None
    ...     and bk[1].label.subtag == "natural gas"
    ...     and isinstance(bk[1], solph.Transformer)
    ... ]
    >>> table = fetch_converter_parameters(my_results, power_plants)
    >>> power_plant = table.iloc[5].dropna()
    >>> power_plant.name = power_plant.pop("label_str")
    >>> power_plant
    allocation method                    electricity
    category                             power plant
    efficiency, electricity                    0.311
    emission, fuel                             0.201
    fuel                             natural gas, DE
    specific_costs_electricity             89.041801
    specific_emission_electricity           0.646302
    variable costs, fuel                      27.692
    Name: power-plant_natural-gas_031_natural-gas_DE01, dtype: object
    >>> power_plant = table.iloc[0].dropna()
    >>> power_plant.name = power_plant.pop("label_str")
    >>> power_plant
    allocation method                        finnish
    category                               chp plant
    efficiency, electricity                     0.25
    efficiency, heat                            0.41
    emission, fuel                             0.201
    fuel                             natural gas, DE
    specific_costs_electricity                 57.96
    specific_costs_heat                         32.2
    specific_emission_electricity           0.420698
    specific_emission_heat                  0.233721
    variable costs, fuel                      27.692
    Name: chp-plant_natural-gas_natural-gas_DE01, dtype: object
    """
    # ToDO: Split this very large function!

    # Create dictionary with all converters and their in- and outflows.
    df = pd.DataFrame()
    commodities = fetch_attributes_of_commodity_sources(results)
    for t in transformer:
        # Get flows of the Transformer
        inflow = [k for k in results["main"].keys() if k[1] == t][0]
        outflows = [k for k in results["main"].keys() if k[0] == t]

        # Get catgeory
        df.loc[t, "category"] = t.label.cat
        df.loc[t, "label_str"] = label2str(t.label)

        # Get parameter of the resource of the Transformer
        fuel_parameter = commodities.loc[commodities.to_node == inflow[0]]

        if len(fuel_parameter) > 0:
            df.loc[t, "variable costs, fuel"] = float(
                fuel_parameter.get("variable_costs", 0)
            )
            df.loc[t, "emission, fuel"] = float(
                fuel_parameter.get("emission", 0)
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
        df.loc[t, "emission, inflow"] = results["param"][inflow][
            "scalars"
        ].get("emission", 0)

        # Get parameter of outflows
        for outflow in outflows:
            sector = outflow[1].label.cat
            key = "{0}, {1}"
            df.loc[t, key.format("variable costs", sector)] = results["param"][
                outflow
            ]["scalars"].variable_costs
            df.loc[t, key.format("emission", sector)] = results["param"][
                outflow
            ]["scalars"].get("emission", 0)
            df.loc[t, "efficiency, {0}".format(sector)] = results["param"][
                (t, None)
            ]["scalars"][
                "conversion_factors_{}".format(label2str(outflow[1].label))
            ]

        fuel_factor = _allocate_outflows(
            eta_e=df.loc[t].get("efficiency, {0}".format("electricity"), 1),
            eta_th=df.loc[t].get("efficiency, {0}".format("heat"), 1),
        )

        # Calculate specific values for outflow sectors
        for outflow in outflows:
            sector = outflow[1].label.cat
            key = "{0}, {1}"
            df.loc[t, "allocation method"] = fuel_factor["method"]
            if sector in ["heat", "electricity"]:
                f = fuel_factor[sector]
            else:
                f = 1 / df.loc[t, "efficiency, {0}".format(sector)]
            df.loc[t, "specific_costs_{0}".format(sector)] = (
                (
                    df.loc[t, "variable costs, inflow"]
                    + df.loc[t, "variable costs, fuel"]
                )
                * f
            ) + df.loc[t, key.format("variable costs", sector)]
            df.loc[t, "specific_emission_{0}".format(sector)] = (
                (df.loc[t, "emission, inflow"] + df.loc[t, "emission, fuel"])
                * f
            ) + df.loc[t, key.format("emission", sector)]
    df = df.loc[:, (df.fillna(0).sum(axis=0) != 0)]
    return df.sort_index(axis=1)


def fetch_attributes_of_commodity_sources(results):
    """
    Get the attributes of the commodity sources.

    Transformers like power plants are connected to commodity buses. This
    function can be used to get specific emission or the variable costs of the
    connected commodity source. Use the `to_node` column to find the data row
    of the commodity Bus of the Transformer.

    Parameters
    ----------
    results : dict
        Deflex results dictionary.

    Returns
    -------
    The attributes of all commodities : pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> cdf = dflx.fetch_attributes_of_commodity_sources(my_results)
    >>> hard_coal = cdf.loc["hard coal", "DE"]
    >>> hard_coal.pop("from_node").label
    Label(cat='source', tag='commodity', subtag='hard coal', region='DE')
    >>> hard_coal.pop("to_node").label
    Label(cat='commodity', tag='all', subtag='hard coal', region='DE')
    >>> hard_coal
    emission                    0.337
    nominal_value                 NaN
    summed_max                    NaN
    max                           1.0
    min                           0.0
    negative_gradient_costs       0.0
    positive_gradient_costs       0.0
    variable_costs             19.944
    Name: (hard coal, DE), dtype: object
    >>> flow_to_power_plant = [
    ...     bk for bk in my_results["main"].keys()
    ...     if bk[1] is not None
    ...     and bk[1].label.cat == "power plant"
    ...     and bk[1].label.subtag == "natural gas"
    ... ][0]
    >>> float(cdf.loc[cdf.to_node == flow_to_power_plant[0]].emission)
    0.201
    """
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
            else:
                parameter.loc[
                    (c[0].label.subtag, c[0].label.region), "from_node"
                ] = c[0]
                parameter.loc[
                    (c[0].label.subtag, c[0].label.region), "to_node"
                ] = c[1]
    return parameter


def _calculate_marginal_costs(df):
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

    df["emission"] = df["emission, fuel"] * (
        1 / df["efficiency, electricity"]
        - df["efficiency, heat"]
        / (df["efficiency, electricity"] * df["efficiency, hp_ref"])
    )
    return df


def _fetch_electricity_flows(results):
    """
    Blabla

    Parameters
    ----------
    results : dict
        Deflex results dictionary.
    """
    return pd.DataFrame(
        {
            k[0]: v["sequences"]["flow"]
            for k, v in results["main"].items()
            if isinstance(k[0], solph.Transformer)
            and k[0].label.cat != "line"
            and k[1].label.cat == "electricity"
        }
    )


def calculate_key_values(results):
    """
    Get time series of typical key values.

     * marginal costs
     * highest emission
     * lowest emission
     * marginal costs power plant
     * emission

    Parameters
    ----------
    results : dict
        Deflex results dictionary.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> df = calculate_key_values(my_results)
    >>> list(df.columns)[:3]
    ['marginal costs', 'highest emission', 'lowest emission']
    >>> row = df.iloc[24]
    >>> row.pop("marginal costs power plant").label
    Label(cat='chp plant', tag='bioenergy', subtag='bioenergy', region='DE01')
    >>> row
    marginal costs      47.573824
    highest emission         1.01
    lowest emission           0.0
    emission             0.016992
    Name: 2022-01-02 00:00:00, dtype: object
    >>> min_mc = df["marginal costs"].min()
    >>> max_mc = df["marginal costs"].max()
    >>> print("{0} - {1}".format(round(min_mc, 2), round(max_mc, 2)))
    47.57 - 65.35
    """
    # Select all converters (class Transformer excluding lines)
    flows = _fetch_electricity_flows(results)
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

    converter_parameters = fetch_converter_parameters(
        results, transformer, remove_null_columns=False
    )
    flow_status = flows.div(flows).fillna(0)

    converter_parameters = _calculate_marginal_costs(converter_parameters)

    kv = pd.DataFrame()

    kv["marginal costs"] = flow_status.mul(
        converter_parameters["marginal costs"]
    ).max(1)
    kv["highest emission"] = flow_status.mul(
        converter_parameters["emission"]
    ).max(1)
    kv["lowest emission"] = flow_status.mul(
        converter_parameters["emission"]
    ).min(1)

    kv["marginal costs power plant"] = flow_status.mul(
        converter_parameters["marginal costs"]
    ).idxmax(1)
    kv = pd.merge(
        kv,
        converter_parameters["emission"],
        "left",
        left_on="marginal costs power plant",
        right_index=True,
    )
    return kv


def get_combined_bus_balance(
    results, cat=None, tag=None, subtag=None, region=None
):
    """
    Combine different buses of the same type.

    The combined buses can be restricted by the label fields (cat, tag, subtag,
    region). Only buses with the same label fields will be combined.

    Parameters
    ----------
    results : dict
        Deflex results dictionary.
    cat : str
        Category of the buses.
    tag : str
        Tag of the buses.
    subtag : str
        Subtag of the buses.
    region : str
        Region of the buses

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> get_combined_bus_balance(my_results, cat="electricity")["out"].columns
    MultiIndex([('decentralised heat',    'heat pump',   'heat pump', 'DE02'),
                ('electricity demand',  'electricity',         'all', 'DE01'),
                ('electricity demand',  'electricity',         'all', 'DE02'),
                (            'excess',  'electricity',         'all', 'DE01'),
                (            'excess',  'electricity',         'all', 'DE02'),
                (            'excess',  'electricity',         'all', 'DE03'),
                (    'fuel converter',  'electricity', 'electricity', 'DE01'),
                (    'fuel converter',  'electricity', 'electricity', 'DE02'),
                (              'line',  'electricity',        'DE01', 'DE02'),
                (              'line',  'electricity',        'DE01', 'DE03'),
                (              'line',  'electricity',        'DE02', 'DE01'),
                (              'line',  'electricity',        'DE02', 'DE03'),
                (              'line',  'electricity',        'DE03', 'DE01'),
                (              'line',  'electricity',        'DE03', 'DE02'),
                (   'other converter', 'Electrolysis', 'electricity',   'DE'),
                (           'storage',  'electricity',     'battery', 'DE01'),
                (           'storage',  'electricity',        'phes', 'DE01')],
               )
    >>> get_combined_bus_balance(
    ...     my_results, cat="electricity", region="DE03")["out"].columns
    MultiIndex([('excess', 'electricity',  'all', 'DE03'),
                (  'line', 'electricity', 'DE03', 'DE01'),
                (  'line', 'electricity', 'DE03', 'DE02')],
               )
    """

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
        outflows = [
            f
            for f in results["Main"].keys()
            if f[0] == bus and f[1] is not None
        ]
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
    """
    Combine different buses of the same type.

    The combined buses can be restricted by the label fields (cat, tag, subtag,
    region). Only buses with the same label fields will be combined.

    Parameters
    ----------
    results : dict
        Deflex results dictionary.
    cat : str
        Category of the buses.
    tag : str
        Tag of the buses.
    subtag : str
        Subtag of the buses.
    region : str
        Region of the buses

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de03_fictive.dflx")
    >>> my_results = dflx.restore_results(fn)
    >>> hc49 = get_converter_balance(
    ...     my_results, cat="power plant", tag="hard coal_049").sum()
    >>> round(float((hc49["out"] / hc49["in"])), 2)
    0.49
    """
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
