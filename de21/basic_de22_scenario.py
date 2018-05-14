# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"

# Python libraries
import os
import logging

# External libraries
import pandas as pd

# internal modules
import reegis_tools.config as cfg
import reegis_tools.commodity_sources
import reegis_tools.scenario_tools
import reegis_tools.coastdat
import reegis_tools.heat_demand
import reegis_tools.powerplants
import reegis_tools.openego
import reegis_tools.entsoe
import reegis_tools.bmwi

import de21.powerplants
import de21.feedin
import de21.demand
import de21.storages
import de21.transmission
import de21.chp
import de21.scenario_tools

import oemof.tools.logger as logger


CT = pd.DataFrame(columns=['DE_orig', 'DE01_orig', 'BE', 'DE01_new', 'DE_new'])


def create_de22_scenario(year, region='DE01'):

    logging.info('BASIC SCENARIO - LOAD de21')
    de = load_de21_scenario(year)

    logging.info('BASIC SCENARIO - STORAGES')
    de = scenario_storages(de, region)

    logging.info('BASIC SCENARIO - TRANSMISSION')
    de = add_transmission_line(de, region)

    # logging.info('BASIC SCENARIO - CHP PLANTS')
    # table_collection = chp_scenario(table_collection, year)

    logging.info('BASIC SCENARIO - VOLATILE SOURCES')
    de = scenario_volatile_sources(year, de, region)

    logging.info('BASIC SCENARIO - HEAT DEMAND')
    de = scenario_heat_demand(year, de, region)

    logging.info('BASIC SCENARIO - POWER PLANTS')
    de = powerplants_scenario(year, de, region)

    logging.info('BASIC SCENARIO - ELECTRICITY DEMAND')
    de = scenario_elec_demand(year, de, region)

    return de.table_collection


def load_de21_scenario(year):
    logging.info("Read scenarios from excel-sheet.".format())

    # de21
    de = de21.Scenario(name='basic', year=2014)
    de_path = os.path.join(cfg.get('paths', 'scenario'), 'basic', '{year}',
                           'csv')
    de.load_csv(de_path.format(year=year))
    de.check_table('time_series')
    return de


def scenario_heat_demand(year, de, region):

    global CT

    # TODO Check units (s. below)

    # Demand of all district heating systems
    df = reegis_tools.heat_demand.get_heat_profiles_by_state(
        year, state=['BE'])['BE']

    berlin_heat = df.groupby(level=1, axis=1).sum().div(0.0036)

    berlin_district_heating = berlin_heat['district heating']

    berlin_district_heating.index = de.table_collection['time_series'].index

    CT.loc['district heating', 'DE01_orig'] = round(
        de.table_collection['time_series'][region, 'district_heating'].sum())
    CT.loc['district heating', 'BE'] = round(
        berlin_district_heating.sum())

    de.table_collection['time_series'][region, 'district_heating'] -= (
        berlin_district_heating)

    de.table_collection['time_series']['DE22', 'district_heating'] = (
        berlin_district_heating)

    CT.loc['district heating', 'DE01_new'] = round(
        de.table_collection['time_series'][region, 'district_heating'].sum())

    de.table_collection['berlin_district_heating'] = (
        berlin_heat['district heating'])

    return de


def scenario_elec_demand(year, de, region):

    global CT

    # Electricity demand
    ego = reegis_tools.openego.get_ego_demand().groupby('federal_states').sum()
    ego = ego['sector_consumption_sum']
    ego_sum = ego.sum()
    ego = ego.div(ego_sum)

    netto = reegis_tools.bmwi.get_annual_electricity_demand_bmwi(year)

    entsoe = reegis_tools.entsoe.get_entsoe_load(year)['DE_load_']
    factor = float(netto * 1000000 / entsoe.sum())
    entsoe = entsoe * factor

    berlin_elec_demand = entsoe * ego['BE']

    berlin_elec_demand.index = de.table_collection['time_series'].index

    CT.loc['electricity demand', 'DE01_orig'] = round(
        de.table_collection['time_series'][region, 'electrical_load'].sum())

    CT.loc['electricity demand', 'BE'] = float(round(berlin_elec_demand.sum()))

    de.table_collection['time_series'][region, 'electrical_load'] -= (
        berlin_elec_demand)

    de.table_collection['time_series']['DE22', 'electrical_load'] = (
        berlin_elec_demand)

    CT.loc['electricity demand', 'DE01_new'] = round(
        de.table_collection['time_series'][region, 'electrical_load'].sum())
    return de


def scenario_volatile_sources(year, de, region):

    global CT

    de_be = {
        'natural gas': 'gas',
        'hard coal': 'coal',
        'wind': 'Wind',
        'solar': 'Solar',
        'oil': 'oil',
        'geothermal': 'Geothermal',
        'hydro': 'Hydro',
    }

    pp = reegis_tools.powerplants.get_pp_by_year(year, overwrite_capacity=True)
    re = pd.DataFrame()
    for pp_type in ['Wind', 'Solar']:
        re.loc['capacity', pp_type] = round(pp.loc[
            (pp.federal_states == 'BE') &
            (pp.energy_source_level_2 == pp_type)].sum().capacity, 1)
    re.columns = pd.MultiIndex.from_product([['BE'], re.columns])

    # Volatile Sources
    vs_berlin = list(re['BE'].columns)
    for col in de.table_collection['volatile_source'][region].columns:
        CT.loc['re_' + col, 'DE01_orig'] = round(float(
            de.table_collection['volatile_source'][region, col]))
        de.table_collection['volatile_source'][region, col] -= (
            re.get(('BE', de_be[col]), 0))
        if float(re.get(('BE', de_be[col]), 0)) > 0:
            de.table_collection['volatile_source']['DE22', col] = (
                re.get(('BE', de_be[col]), 0))
            de.table_collection['time_series']['DE22', col] = (
                de.table_collection['time_series'][region, col])
        CT.loc['re_' + col, 'BE'] = round(float(
            re.get(('BE', de_be[col]), 0)))

        if de_be.get(col) in vs_berlin:
            vs_berlin.remove(de_be.get(col))

        CT.loc['re_' + col, 'DE01_new'] = round(float(
            de.table_collection['volatile_source'][region, col]))

    for col in vs_berlin:
        CT.loc['re_' + col, 'BE'] = round(float(re.get(('BE', de_be[col]), 0)))
    return de


def scenario_storages(de, region):
    """Elec. Storages"""
    if de.table_collection['storages'].get(region) is None:
        logging.info("No Storages. Skipped!")
    else:
        logging.error("Storage exist but not implemented.")
    return de


def powerplants_scenario(year, de, region):

    global CT

    sub = pd.DataFrame(
        columns=['DE_orig', 'DE01_orig', 'BE', 'DE01_new', 'DE_new'])

    # Create heat_demand for BE and new heat_demand for DE01
    heat_demand_de = de21.demand.get_heat_profiles_de21(year)

    berlin_district_heating = de.table_collection.pop(
        'berlin_district_heating')
    heat_demand_be = pd.DataFrame(berlin_district_heating).rename(
        columns={'district heating': 'district_heating'})
    heat_demand_be = (
        pd.concat([heat_demand_be], axis=1, keys=['BE']).sort_index(1))

    heat_demand_de['DE01', 'district_heating'] -= (
          heat_demand_be['BE', 'district_heating'].values)

    # Create conversion balance for BE and new balance for DE01
    eb, eb21 = de21.chp.diff_conversion_balance(year)

    heat_b_be = reegis_tools.powerplants.calculate_chp_share_and_efficiency(eb)
    heat_b_de = reegis_tools.powerplants.calculate_chp_share_and_efficiency(
        eb21)

    # Create power plants table for BE and new table for DE01
    pp_be = reegis_tools.powerplants.get_pp_by_year(
        year, overwrite_capacity=True, capacity_in=True)

    table_collect_be = de21.basic_scenario.powerplants(
        pp_be, {}, year, region_column='federal_states')

    pp_de = de21.powerplants.get_de21_pp_by_year(year, overwrite_capacity=True)
    table_collect_de = de21.basic_scenario.powerplants(pp_de, {}, year)

    for col in table_collect_de['transformer']['DE01'].columns:
        table_collect_de['transformer']['DE01', col] -= (
            table_collect_be['transformer']['BE', col])

    table_collect_be = de21.basic_scenario.chp_table(
        heat_b_be, heat_demand_be, table_collect_be, regions=['BE'])

    table_collect_de = de21.basic_scenario.chp_table(
        heat_b_de, heat_demand_de, table_collect_de, regions=['DE01'])

    print(table_collect_be['transformer']['BE'])
    print(table_collect_de['transformer']['DE01'])
    del de.table_collection['transformer']['DE01']
    for col in table_collect_de['transformer']['DE01'].columns:
        de.table_collection['transformer']['DE01', col] = (
            table_collect_de['transformer']['DE01', col])
        de.table_collection['transformer']['BE', col] = (
            table_collect_be['transformer']['BE', col])
    # exit(0)

    # # non-efficiency rows
    # rows = [r for r in de.table_collection['transformer'].index
    #         if 'efficiency' not in r]
    #
    # # efficiency rows
    # eff_rows = [r for r in de.table_collection['transformer'].index
    #             if 'efficiency' in r]
    #
    # sub['BE'] = (table_collect['transformer'].loc[rows, 'BE']).sum(axis=1)
    #
    # sub['DE01_orig'] = de.table_collection['transformer'].loc[
    #     rows, region].sum(axis=1)
    #
    # asd = de.table_collection['transformer'].loc[
    #     rows, region]
    # bsd = table_collect['transformer'].loc[rows, 'BE']
    #
    # for col in de.table_collection['transformer'][region].columns:
    #     de.table_collection['transformer'].loc[rows, (region, col)] -= (
    #             table_collect['transformer'].loc[rows, ('BE', col)])
    #     de.table_collection['transformer'].loc[rows, ('DE22', col)] = (
    #             table_collect['transformer'].loc[rows, ('BE', col)])
    #     de.table_collection['transformer'].loc[rows, (region, col)].fillna(
    #         float('inf'), inplace=True)
    #
    #     # copy efficiency
    #     de.table_collection['transformer'].loc[eff_rows, ('DE22', col)] = (
    #         de.table_collection['transformer'].loc[eff_rows, (region, col)])
    #
    # sub['DE01_new'] = de.table_collection['transformer'].loc[rows, region].sum(
    #     axis=1)
    # csd = de.table_collection['transformer'].loc[
    #     rows, region]
    # pd.concat([asd, bsd, csd]).to_excel(os.path.join(
    #     cfg.get('paths', 'messages'), 'summery_embedded_powerplants_22.xls'))
    # CT = pd.concat([CT, sub])

    return de


def add_transmission_line(de, region):
    name = '{0}-{1}'.format(region, 'DE22')

    parameter = {
        'capacity': 999999,
        'distance': 0,
        'efficiency': cfg.get('transmission', 'general_efficiency')}

    for key, value in parameter.items():
        de.table_collection['transmission'].loc[name, ('electrical', key)] = (
            value)
    return de


def clean_time_series(table_collection):
    ts = table_collection['time_series']
    vs = table_collection['volatile_source']

    regions = list(ts.columns.get_level_values(0).unique())
    regions.remove('DE_demand')
    for reg in regions:
        for load in ['district_heating', 'electrical_load']:
            if ts[reg].get(load) is not None:
                if ts[reg, load].sum() == 0:
                    del ts[reg, load]
        for t in ['hydro', 'solar', 'wind', 'geothermal']:
            rm = False
            # if the column does not exist or is 0 the corresponding column
            # of the time_series table can be removed.
            if vs[reg].get(t) is None or vs[reg].get(t).sum() == 0:
                rm = True
            if (ts[reg].get(t) is not None) & rm:
                del ts[reg, t]

    for table in table_collection.keys():
        table_collection[table].sort_index(axis=1, inplace=True)
        try:
            if table_collection[table].lt(0).sum().sum() > 0:
                neg = {}
                for col in table_collection[table].columns:
                    if table_collection[table][col].lt(0).sum() > 0:
                        neg[col] = {}
                        for p in table_collection[table].index[
                                    table_collection[table][col].lt(0)]:
                            neg[col][p] = table_collection[table].loc[p, col]
                            table_collection[table].loc[p, col] = 0
                msg = "Negative value detected in table '{0}'."
                logging.warning(msg.format(table))
                msg = "The following parameters are set to Null: {0}"
                logging.warning(msg.format(neg))
        except TypeError:
            logging.info(
                "Table '{0}' not tested for negative values.".format(table))

    return table_collection


def create_basic_scenario(year):
    table_collection = create_de22_scenario(year)
    table_collection = clean_time_series(table_collection)
    sce = de21.scenario_tools.Scenario(table_collection=table_collection,
                                       name='basic_de22', year=2014)
    path = os.path.join(cfg.get('paths', 'scenario'), 'basic_de22', str(year))
    sce.to_excel(os.path.join(path, '_'.join([sce.name, str(year)]) + '.xls'))
    sce.to_csv(os.path.join(path, 'csv'))

    CT.to_excel(os.path.join(
        cfg.get('paths', 'messages'), 'summery_embedded_model_22.xls'))


if __name__ == "__main__":
    logger.define_logging()
    for yr in [2014, 2013, 2012]:
        create_basic_scenario(yr)
        exit(0)
    # print(scenario_commodity_sources(2014, use_znes_2014=True))
    # print(scenario_elec_demand(2014, pd.DataFrame())) return csv_path
