# -*- coding: utf-8 -*-

"""Creating solph nodes from input data.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
from collections import namedtuple

import pandas as pd
from oemof import solph


class Label(namedtuple("solph_label", ["cat", "tag", "subtag", "region"])):
    """A label for deflex components."""

    __slots__ = ()

    def __str__(self):
        return "_".join(map(str, self._asdict().values()))


def create_solph_nodes_from_data(input_data, nodes, extra_regions=None):
    """
    Creating solph nodes from input data.

    Parameters
    ----------
    input_data
    nodes
    extra_regions

    Returns
    -------

    """

    # Local volatile sources
    add_volatile_sources(input_data, nodes)

    # Decentralised heating systems
    if "decentralised heat" in input_data:
        add_decentralised_heating_systems(input_data, nodes, extra_regions)

    # Local electricity demand
    add_electricity_demand(input_data, nodes)

    # Local district heating demand
    add_district_heating_systems(input_data, nodes)

    # Local power plants as Transformer and ExtractionTurbineCHP (chp)
    add_power_and_heat_plants(input_data, nodes, extra_regions)

    # Storages
    if "storages" in input_data:
        add_storages(input_data, nodes)

    if "mobility" in input_data:
        add_mobility(input_data, nodes)

    # Connect electricity buses with transmission
    add_transmission_lines_between_electricity_nodes(input_data, nodes)

    # Add shortage excess to every bus
    add_shortage_excess(nodes)
    return nodes


def create_fuel_bus_with_source(nodes, fuel, region, input_data):
    """

    Parameters
    ----------
    nodes
    fuel
    region
    input_data

    Returns
    -------

    """
    cs_table = input_data["commodity sources"].loc["DE"]
    bus_label = Label("bus", "commodity", fuel.replace(" ", "_"), region)
    if bus_label not in nodes:
        nodes[bus_label] = solph.Bus(label=bus_label)

    cs_label = Label("source", "commodity", fuel.replace(" ", "_"), region)

    co2_price = float(input_data["general"].get("co2 price", 0))

    variable_costs = (
        cs_table.loc[fuel.replace("_", " "), "emission"] / 1000 * co2_price
        + cs_table.loc[fuel.replace("_", " "), "costs"]
    )

    if cs_label not in nodes:
        nodes[cs_label] = solph.Source(
            label=cs_label,
            outputs={
                nodes[bus_label]: solph.Flow(
                    variable_costs=variable_costs,
                    emission=cs_table.loc[fuel.replace("_", " "), "emission"],
                )
            },
        )


def add_volatile_sources(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add volatile sources to nodes dictionary.")
    vs = table_collection["volatile plants"]

    for region in vs.index.get_level_values(0).unique():
        for vs_type in vs.loc[region].index:
            vs_label = Label("source", "ee", vs_type, region)
            capacity = vs.loc[(region, vs_type), "capacity"]
            try:
                feedin = table_collection["volatile series"][region, vs_type]
            except KeyError:
                if capacity > 0:
                    msg = "Missing time series for {0} (capacity: {1}) in {2}."
                    raise ValueError(msg.format(vs_type, capacity, region))
                feedin = [0]
            bus_label = Label("bus", "electricity", "all", region)
            if bus_label not in nodes:
                nodes[bus_label] = solph.Bus(label=bus_label)
            if capacity * sum(feedin) > 0:
                nodes[vs_label] = solph.Source(
                    label=vs_label,
                    outputs={
                        nodes[bus_label]: solph.Flow(
                            fix=feedin,
                            nominal_value=capacity,
                            emission=0,
                        )
                    },
                )


def add_decentralised_heating_systems(table_collection, nodes, extra_regions):
    """

    Parameters
    ----------
    table_collection
    nodes
    extra_regions

    Returns
    -------

    """
    logging.debug("Add decentralised_heating_systems to nodes dictionary.")
    dts = table_collection["demand series"]
    dh = table_collection["decentralised heat"]
    demand_regions = list({"DE_demand"}.union(set(extra_regions)))

    for d_region in demand_regions:
        region_name = d_region.replace("_demand", "")

        if region_name not in dh.index:
            data_name = "DE_demand"
        else:
            data_name = d_region

        fuels = [f for f in dh.loc[data_name].index if f in dts[d_region]]
        for fuel in fuels:
            src = dh.loc[(data_name, fuel), "source"]
            bus_label = Label(
                "bus", "commodity", src.replace(" ", "_"), region_name
            )

            # Check if source bus exists
            if bus_label not in nodes:
                create_fuel_bus_with_source(
                    nodes, src, region_name, table_collection
                )

            # Create heating bus as Bus
            heat_bus_label = Label(
                "bus", "heat", fuel.replace(" ", "_"), region_name
            )
            nodes[heat_bus_label] = solph.Bus(label=heat_bus_label)

            # Create heating system as Transformer
            trsf_label = Label(
                "trsf", "heat", fuel.replace(" ", "_"), region_name
            )

            efficiency = float(dh.loc[(data_name, fuel), "efficiency"])

            nodes[trsf_label] = solph.Transformer(
                label=trsf_label,
                inputs={nodes[bus_label]: solph.Flow()},
                outputs={nodes[heat_bus_label]: solph.Flow()},
                conversion_factors={nodes[heat_bus_label]: efficiency},
            )

            # Create demand as Sink
            d_heat_demand_label = Label(
                "demand", "heat", fuel.replace(" ", "_"), region_name
            )
            nodes[d_heat_demand_label] = solph.Sink(
                label=d_heat_demand_label,
                inputs={
                    nodes[heat_bus_label]: solph.Flow(
                        fix=dts[d_region, fuel],
                        nominal_value=1,
                    )
                },
            )


def add_electricity_demand(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add local electricity demand to nodes dictionary.")
    dts = table_collection["demand series"]
    dts.columns = dts.columns.swaplevel()
    for region in dts["electrical_load"].columns:
        if dts["electrical_load"][region].sum() > 0:
            bus_label = Label("bus", "electricity", "all", region)
            if bus_label not in nodes:
                nodes[bus_label] = solph.Bus(label=bus_label)
            elec_demand_label = Label("demand", "electricity", "all", region)
            nodes[elec_demand_label] = solph.Sink(
                label=elec_demand_label,
                inputs={
                    nodes[bus_label]: solph.Flow(
                        fix=dts["electrical_load", region],
                        nominal_value=1,
                    )
                },
            )


def add_district_heating_systems(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add district heating systems to nodes dictionary.")
    dts = table_collection["demand series"]
    if "district heating" in dts:
        for region in dts["district heating"].columns:
            if dts["district heating"][region].sum() > 0:
                bus_label = Label("bus", "heat", "district", region)
                if bus_label not in nodes:
                    nodes[bus_label] = solph.Bus(label=bus_label)
                heat_demand_label = Label("demand", "heat", "district", region)
                nodes[heat_demand_label] = solph.Sink(
                    label=heat_demand_label,
                    inputs={
                        nodes[bus_label]: solph.Flow(
                            fix=dts["district heating", region],
                            nominal_value=1,
                        )
                    },
                )


def add_transmission_lines_between_electricity_nodes(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add transmission lines to nodes dictionary.")
    power_lines = table_collection["power lines"]["electrical"]
    for idx, values in power_lines.iterrows():
        b1, b2 = idx.split("-")
        lines = [(b1, b2), (b2, b1)]
        for line in lines:
            line_label = Label("line", "electricity", line[0], line[1])
            bus_label_in = Label("bus", "electricity", "all", line[0])
            bus_label_out = Label("bus", "electricity", "all", line[1])
            if bus_label_in not in nodes:
                raise ValueError(
                    "Bus {0} missing for power line from {0} to {1}".format(
                        bus_label_in, bus_label_out
                    )
                )
            if bus_label_out not in nodes:
                raise ValueError(
                    "Bus {0} missing for power line from {0} to {1}".format(
                        bus_label_out, bus_label_in
                    )
                )
            if values.capacity != float("inf"):
                logging.debug(
                    "Line %s has a capacity of %s", line_label, values.capacity
                )
                nodes[line_label] = solph.Transformer(
                    label=line_label,
                    inputs={nodes[bus_label_in]: solph.Flow()},
                    outputs={
                        nodes[bus_label_out]: solph.Flow(
                            nominal_value=values.capacity
                        )
                    },
                    conversion_factors={
                        nodes[bus_label_out]: values.efficiency
                    },
                )
            else:
                logging.debug("Line %s has no capacity limit", line_label)
                nodes[line_label] = solph.Transformer(
                    label=line_label,
                    inputs={nodes[bus_label_in]: solph.Flow()},
                    outputs={nodes[bus_label_out]: solph.Flow()},
                    conversion_factors={
                        nodes[bus_label_out]: values.efficiency
                    },
                )


def add_power_and_heat_plants(table_collection, nodes, extra_regions):
    """

    Parameters
    ----------
    table_collection
    nodes
    extra_regions

    Returns
    -------

    """
    trsf = table_collection["power plants"]
    if "chp_hp" in table_collection:
        chp_hp = table_collection["chp-heat plants"]
        chp_hp_index = chp_hp.index.get_level_values(0).unique()
    else:
        chp_hp = None
        chp_hp_index = []

    regions = set(trsf.index.get_level_values(0).unique()).union(
        set(chp_hp_index)
    )

    for region in regions:
        bus_heat = Label("bus", "heat", "district", region)
        bus_elec = Label("bus", "electricity", "all", region)

        if bus_heat not in nodes:
            nodes[bus_heat] = solph.Bus(label=bus_heat)

        if region in chp_hp_index:
            chp_hp_fuels = set(chp_hp.loc[region, "fuel"].unique())
            chp_hp_regions = chp_hp.loc[region].index
        else:
            chp_hp_fuels = set()
            chp_hp_regions = []

        if region in trsf.index:
            trsf_fuels = set(trsf.loc[region, "fuel"].unique())
            trsf_regions = trsf.loc[region].index
        else:
            trsf_fuels = set()
            trsf_regions = []

        fuels = trsf_fuels.union(chp_hp_fuels)

        for fuel in fuels:
            # Connect to global fuel bus if not defined as extra region
            if region in extra_regions:
                bus_fuel = Label(
                    "bus", "commodity", fuel.replace(" ", "_"), region
                )
                if bus_fuel not in nodes:
                    create_fuel_bus_with_source(
                        nodes, fuel.replace(" ", "_"), region, table_collection
                    )
            else:
                bus_fuel = Label(
                    "bus", "commodity", fuel.replace(" ", "_"), "DE"
                )
                if bus_fuel not in nodes:
                    create_fuel_bus_with_source(
                        nodes, fuel.replace(" ", "_"), "DE", table_collection
                    )

        for plant in trsf_regions:
            idx = set(trsf.loc[region, plant].index).difference(("fuel",))
            trsf.loc[(region, plant), idx] = pd.to_numeric(
                trsf.loc[(region, plant), idx]
            )
            params = trsf.loc[region, plant]

            # Create power plants as 1x1 Transformer if capacity > 0
            if params.capacity > 0:
                # if downtime_factor is in the parameters, use it
                if hasattr(params, "downtime_factor"):
                    params.capacity *= 1 - params["downtime_factor"]

                # Define output flow with or without summed_max attribute
                if params.limit_elec_pp == float("inf"):
                    outflow = solph.Flow(nominal_value=params.capacity)
                else:
                    smax = params.limit_elec_pp / params.capacity
                    outflow = solph.Flow(
                        nominal_value=params.capacity, summed_max=smax
                    )

                # if variable costs are defined add them to the outflow
                if hasattr(params, "variable_costs"):
                    vc = params.variable_costs
                    outflow.variable_costs = solph.sequence(vc)

                plant_name = (
                    plant.replace(" - ", "_")
                    .replace(" ", "_")
                    .replace(".", "")
                )

                trsf_label = Label("trsf", "pp", plant_name, region)

                fuel_bus = Label(
                    "bus", "commodity", params.fuel.replace(" ", "_"), "DE"
                )

                nodes[trsf_label] = solph.Transformer(
                    label=trsf_label,
                    inputs={nodes[fuel_bus]: solph.Flow()},
                    outputs={nodes[bus_elec]: outflow},
                    conversion_factors={nodes[bus_elec]: params.efficiency},
                )

        for plant in chp_hp_regions:
            idx = set(chp_hp.loc[region, plant].index).difference(("fuel",))
            chp_hp.loc[(region, plant), idx] = pd.to_numeric(
                chp_hp.loc[(region, plant), idx]
            )
            params = chp_hp.loc[region, plant]

            fuel_bus = Label(
                "bus", "commodity", params.fuel.replace(" ", "_"), "DE"
            )

            # Create chp plants as 1x2 Transformer
            if (
                hasattr(params, "capacity_heat_chp")
                and params["capacity_heat_chp"] > 0
            ):
                trsf_label = Label(
                    "trsf", "chp", params.fuel.replace(" ", "_"), region
                )

                smax = (params.limit_heat_chp / params.efficiency_heat_chp) / (
                    params["capacity_heat_chp"] / params.efficiency_heat_chp
                )

                nodes[trsf_label] = solph.Transformer(
                    label=trsf_label,
                    inputs={
                        nodes[fuel_bus]: solph.Flow(
                            nominal_value=(
                                params["capacity_heat_chp"]
                                / params.efficiency_heat_chp
                            ),
                            summed_max=smax,
                        )
                    },
                    outputs={
                        nodes[bus_elec]: solph.Flow(),
                        nodes[bus_heat]: solph.Flow(),
                    },
                    conversion_factors={
                        nodes[bus_elec]: params.efficiency_elec_chp,
                        nodes[bus_heat]: params.efficiency_heat_chp,
                    },
                )

            # Create heat plants as 1x1 Transformer
            if hasattr(params, "capacity_hp") and params.capacity_hp > 0:
                trsf_label = Label(
                    "trsf", "hp", params.fuel.replace(" ", "_"), region
                )
                smax = params.limit_hp / params.capacity_hp

                nodes[trsf_label] = solph.Transformer(
                    label=trsf_label,
                    inputs={nodes[fuel_bus]: solph.Flow()},
                    outputs={
                        nodes[bus_heat]: solph.Flow(
                            nominal_value=params.capacity_hp, summed_max=smax
                        )
                    },
                    conversion_factors={nodes[bus_heat]: params.efficiency_hp},
                )


def add_storages(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    storages = table_collection["storages"]
    storages.index = storages.index.swaplevel()
    for region in storages.loc["phes"].index:
        storage_label = Label("storage", "electricity", "phes", region)
        bus_label = Label("bus", "electricity", "all", region)
        params = storages.loc["phes", region]
        nodes[storage_label] = solph.components.GenericStorage(
            label=storage_label,
            inputs={nodes[bus_label]: solph.Flow(nominal_value=params.pump)},
            outputs={
                nodes[bus_label]: solph.Flow(nominal_value=params.turbine)
            },
            nominal_storage_capacity=params.energy,
            loss_rate=0,
            initial_storage_level=None,
            inflow_conversion_factor=params.pump_eff,
            outflow_conversion_factor=params.turbine_eff,
        )


def add_mobility(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    mseries = table_collection["mobility series"]
    mtable = table_collection["mobility"]
    for region in mseries.columns.get_level_values(0).unique():
        for fuel in mseries[region].columns:
            source = mtable.loc[(region, fuel), "source"]
            source_region = mtable.loc[(region, fuel), "source_region"]
            if mseries[region, fuel].sum() > 0:
                fuel_transformer = Label("process", "fuel", fuel, region)
                fuel_demand = Label("demand", "mobility", fuel, region)
                bus_label = Label("bus", "mobility", fuel, region)
                if fuel != "electricity":
                    com_bus_label = Label(
                        "bus", "commodity", source, source_region
                    )
                else:
                    com_bus_label = Label(
                        "bus", "electricity", "all", source_region
                    )
                if bus_label not in nodes:
                    nodes[bus_label] = solph.Bus(label=bus_label)
                if com_bus_label not in nodes:
                    nodes[com_bus_label] = solph.Bus(label=com_bus_label)
                cf = mtable.loc[(region, fuel), "efficiency"]
                nodes[fuel_transformer] = solph.Transformer(
                    label=fuel_transformer,
                    inputs={nodes[com_bus_label]: solph.Flow()},
                    outputs={nodes[bus_label]: solph.Flow()},
                    conversion_factors={nodes[bus_label]: cf},
                )
                fix_value = mseries[region, fuel]
                nodes[fuel_demand] = solph.Sink(
                    label=fuel_demand,
                    inputs={
                        nodes[bus_label]: solph.Flow(
                            nominal_value=1, fix=fix_value
                        )
                    },
                )
    return nodes


def add_shortage_excess(nodes):
    """

    Parameters
    ----------
    nodes

    Returns
    -------

    """
    bus_keys = [key for key in nodes.keys() if "bus" in key.cat]
    for key in bus_keys:
        excess_label = Label("excess", key.tag, key.subtag, key.region)
        nodes[excess_label] = solph.Sink(
            label=excess_label, inputs={nodes[key]: solph.Flow()}
        )
        shortage_label = Label("shortage", key.tag, key.subtag, key.region)
        nodes[shortage_label] = solph.Source(
            label=shortage_label,
            outputs={nodes[key]: solph.Flow(variable_costs=900)},
        )


if __name__ == "__main__":
    pass
