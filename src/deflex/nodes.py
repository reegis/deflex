# -*- coding: utf-8 -*-

"""Creating solph nodes from input data.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
from collections import namedtuple

from oemof import solph


class Label(namedtuple("solph_label", ["cat", "tag", "subtag", "region"])):
    """A label for deflex components."""

    __slots__ = ()

    def __str__(self):
        return "_".join(map(str, self._asdict().values()))


def create_solph_nodes_from_data(input_data, nodes):
    """
    Creating solph nodes from input data.

    Parameters
    ----------
    input_data
    nodes

    Returns
    -------

    """
    # Electricity demand
    add_electricity_demand(input_data, nodes)

    # Volatile sources
    add_volatile_sources(input_data, nodes)

    # Power plants
    add_power_plants(input_data, nodes)

    # Decentralised heating systems
    if "decentralised heat" in input_data:
        add_decentralised_heating_systems(input_data, nodes)

    # District heating demand
    if "heat demand series" in input_data:
        add_district_heating_demand(input_data, nodes)

    # Add chp plants and heat plants for gird-bound heat
    if "heat-chp plants" in input_data:
        add_heat_and_chp_plants(input_data, nodes)

    # Electricity storages
    if "electricity storages" in input_data:
        add_electricity_storages(input_data, nodes)

    # Mobility
    if "mobility" in input_data and "mobility demand series" in input_data:
        add_mobility(input_data, nodes)

    # Connect electricity buses with transmission
    if "power lines" in input_data:
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
    fuel = fuel.replace("_", " ")
    cs_data = input_data["commodity sources"].loc[region, fuel]
    bus_label = Label("bus", "commodity", fuel, region)
    if bus_label not in nodes:
        nodes[bus_label] = solph.Bus(label=bus_label)

    cs_label = Label("source", "commodity", fuel, region)

    co2_price = float(input_data["general"]["co2 price"])

    variable_costs = cs_data["emission"] / 1000 * co2_price + cs_data["costs"]

    if cs_data.get("annual limit", float("inf")) != float("inf"):
        if cs_label not in nodes:
            nodes[cs_label] = solph.Source(
                label=cs_label,
                outputs={
                    nodes[bus_label]: solph.Flow(
                        variable_costs=variable_costs,
                        emission=cs_data["emission"],
                        nominal_value=cs_data["annual limit"],
                        summed_max=1,
                    )
                },
            )

    else:
        if cs_label not in nodes:
            nodes[cs_label] = solph.Source(
                label=cs_label,
                outputs={
                    nodes[bus_label]: solph.Flow(
                        variable_costs=variable_costs,
                        emission=cs_data["emission"],
                    )
                },
            )


def create_electricity_bus(nodes, region):
    """Create an electricity bus for a given region."""
    bus_label = Label("bus", "electricity", "all", region)
    if bus_label not in nodes:
        nodes[bus_label] = solph.Bus(label=bus_label)


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


def add_decentralised_heating_systems(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add decentralised_heating_systems to nodes dictionary.")
    dts = table_collection["heat demand series"]
    dh = table_collection["decentralised heat"]

    demand_sets = [c for c in dts.columns if "district heating" not in str(c)]

    for demand_set in demand_sets:
        region_name = demand_set[0]
        fuel = demand_set[1].replace("_", " ")

        src = dh.loc[demand_set, "source"].replace("_", " ")

        if src == "electricity":
            cs_bus_label = Label("bus", "electricity", "all", region_name)
            if cs_bus_label not in nodes:
                create_electricity_bus(nodes, region_name)
        else:
            cs_bus_label = Label("bus", "commodity", src, region_name)
            if cs_bus_label not in nodes:
                create_fuel_bus_with_source(
                    nodes, src, region_name, table_collection
                )

        # Create heating bus as Bus
        heat_bus_label = Label("bus", "heat", fuel, region_name)
        nodes[heat_bus_label] = solph.Bus(label=heat_bus_label)

        # Create heating system as Transformer
        trsf_label = Label("trsf", "heat", fuel, region_name)

        efficiency = float(dh.loc[demand_set, "efficiency"])

        nodes[trsf_label] = solph.Transformer(
            label=trsf_label,
            inputs={nodes[cs_bus_label]: solph.Flow()},
            outputs={nodes[heat_bus_label]: solph.Flow()},
            conversion_factors={nodes[heat_bus_label]: efficiency},
        )

        # Create demand as Sink
        d_heat_demand_label = Label("demand", "heat", fuel, region_name)
        nodes[d_heat_demand_label] = solph.Sink(
            label=d_heat_demand_label,
            inputs={
                nodes[heat_bus_label]: solph.Flow(
                    fix=dts[demand_set],
                    nominal_value=1,
                )
            },
        )


def add_electricity_demand(input_data, nodes):
    """

    Parameters
    ----------
    input_data
    nodes

    Returns
    -------

    """
    logging.debug("Add local electricity demand to nodes dictionary.")

    for idx, series in input_data["electricity demand series"].items():
        region = idx[0]
        demand_name = idx[1]
        if series.sum() > 0:
            bus_label = Label("bus", "electricity", "all", region)
            if bus_label not in nodes:
                create_electricity_bus(nodes, region)
            elec_demand_label = Label(
                "demand", "electricity", demand_name, region
            )
            nodes[elec_demand_label] = solph.Sink(
                label=elec_demand_label,
                inputs={
                    nodes[bus_label]: solph.Flow(
                        fix=series,
                        nominal_value=1,
                    )
                },
            )


def add_district_heating_demand(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    logging.debug("Add district heating systems to nodes dictionary.")
    dts = table_collection["heat demand series"]

    demand_sets = [c for c in dts.columns if "district heating" in str(c)]

    for demand_set in demand_sets:
        region = demand_set[0]
        if dts[demand_set].sum() > 0:
            bus_label = Label("bus", "heat", "district", region)
            if bus_label not in nodes:
                nodes[bus_label] = solph.Bus(label=bus_label)
            heat_demand_label = Label("demand", "heat", "district", region)
            nodes[heat_demand_label] = solph.Sink(
                label=heat_demand_label,
                inputs={
                    nodes[bus_label]: solph.Flow(
                        fix=dts[demand_set],
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
    power_lines = table_collection["power lines"]
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


def check_in_out_buses(nodes, table, input_data):
    sources = table[["fuel", "source region"]].apply(tuple, axis=1).unique()
    for source in sources:
        fuel = source[0]
        region = source[1]
        if Label("bus", "commodity", fuel, region) not in nodes:
            create_fuel_bus_with_source(nodes, fuel, region, input_data)

    for region in table.index.get_level_values(0).unique():
        if Label("bus", "electricity", "all", region) not in nodes:
            create_electricity_bus(nodes, region)


def add_power_plants(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    pp = table_collection["power plants"]

    check_in_out_buses(nodes, pp, table_collection)

    for idx, params in pp.iterrows():
        region = idx[0]

        # Create label for in and out bus:
        fuel_bus = Label(
            "bus", "commodity", params.fuel, params["source region"]
        )
        bus_elec = Label("bus", "electricity", "all", region)

        # Create power plants as 1x1 Transformer if capacity > 0
        if params.capacity > 0:
            # if downtime_factor is in the parameters, use it
            if hasattr(params, "downtime_factor"):
                params.capacity *= 1 - params["downtime_factor"]

            # Define output flow with or without summed_max attribute
            if params.get("annual_limit_electricity", float("inf")) == float(
                "inf"
            ):
                outflow = solph.Flow(nominal_value=params.capacity)
            else:
                smax = params.annual_limit_electricity / params.capacity
                outflow = solph.Flow(
                    nominal_value=params.capacity, summed_max=smax
                )

            # if variable costs are defined add them to the outflow
            if hasattr(params, "variable_costs"):
                vc = params.variable_costs
                outflow.variable_costs = solph.sequence(vc)

            plant_name = idx[1].replace(" - ", "_").replace(".", "")

            trsf_label = Label("trsf", "pp", plant_name, region)

            nodes[trsf_label] = solph.Transformer(
                label=trsf_label,
                inputs={nodes[fuel_bus]: solph.Flow()},
                outputs={nodes[bus_elec]: outflow},
                conversion_factors={nodes[bus_elec]: params.efficiency},
            )


def add_heat_and_chp_plants(table_collection, nodes):
    chp_heat_plants = table_collection["heat-chp plants"]

    check_in_out_buses(nodes, chp_heat_plants, table_collection)

    for idx, params in chp_heat_plants.iterrows():
        region = idx[0]

        bus_fuel = Label(
            "bus", "commodity", params.fuel, params["source region"]
        )
        bus_elec = Label("bus", "electricity", "all", region)
        bus_heat = Label("bus", "heat", "district", region)

        # Create chp plants as 1x2 Transformer
        if (
            hasattr(params, "capacity_heat_chp")
            and params["capacity_heat_chp"] > 0
        ):
            chp_label = Label(
                "trsf", "chp", params.fuel.replace(" ", "_"), region
            )

            smax = (params.limit_heat_chp / params.efficiency_heat_chp) / (
                params["capacity_heat_chp"] / params.efficiency_heat_chp
            )

            nodes[chp_label] = solph.Transformer(
                label=chp_label,
                inputs={
                    nodes[bus_fuel]: solph.Flow(
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
            hp_label = Label(
                "trsf", "hp", params.fuel.replace(" ", "_"), region
            )
            smax = params.limit_hp / params.capacity_hp

            nodes[hp_label] = solph.Transformer(
                label=hp_label,
                inputs={nodes[bus_fuel]: solph.Flow()},
                outputs={
                    nodes[bus_heat]: solph.Flow(
                        nominal_value=params.capacity_hp, summed_max=smax
                    )
                },
                conversion_factors={nodes[bus_heat]: params.efficiency_hp},
            )


def add_electricity_storages(table_collection, nodes):
    """

    Parameters
    ----------
    table_collection
    nodes

    Returns
    -------

    """
    for idx, params in table_collection["electricity storages"].iterrows():
        region = idx[0]
        name = idx[1]
        storage_label = Label("storage", "electricity", name, region)
        bus_label = Label("bus", "electricity", "all", region)
        nodes[storage_label] = solph.components.GenericStorage(
            label=storage_label,
            inputs={
                nodes[bus_label]: solph.Flow(
                    nominal_value=params["charge capacity"]
                )
            },
            outputs={
                nodes[bus_label]: solph.Flow(
                    nominal_value=params["discharge capacity"]
                )
            },
            nominal_storage_capacity=params["energy content"],
            loss_rate=params["loss rate"],
            initial_storage_level=None,
            inflow_conversion_factor=params["charge efficiency"],
            outflow_conversion_factor=params["discharge efficiency"],
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
    mseries = table_collection["mobility demand series"]
    mtable = table_collection["mobility"]
    for region in mseries.columns.get_level_values(0).unique():
        for fuel in mseries[region].columns:
            source = mtable.loc[(region, fuel), "source"]
            source_region = mtable.loc[(region, fuel), "source region"]
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
