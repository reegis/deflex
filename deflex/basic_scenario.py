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
import reegis_tools.bmwi
import deflex.powerplants
import deflex.feedin
import deflex.demand
import deflex.storages
import deflex.transmission
import deflex.chp
import deflex.scenario_tools

import oemof.tools.logger as logger


def create_scenario(year, round_values):
    table_collection = {}

    logging.info('BASIC SCENARIO - STORAGES')
    table_collection['storages'] = scenario_storages()

    logging.info('BASIC SCENARIO - POWER PLANTS')
    table_collection = powerplants_scenario(
        table_collection, year, round_values)

    logging.info('BASIC SCENARIO - TRANSMISSION')
    table_collection['transmission'] = scenario_transmission(table_collection)

    logging.info('BASIC SCENARIO - CHP PLANTS')
    table_collection = chp_scenario(table_collection, year)

    logging.info('BASIC SCENARIO - DECENTRALISED HEAT')
    table_collection['decentralised_heating'] = decentralised_heating()

    logging.info('BASIC SCENARIO - SOURCES')
    table_collection = commodity_sources(year, table_collection)
    table = scenario_feedin(year)

    logging.info('BASIC SCENARIO - DEMAND')
    table_collection['time_series'] = scenario_demand(
        year, table)
    return table_collection


def scenario_transmission(table_collection):
    vs = table_collection['volatile_source']
    offshore_regions = ['DE19', 'DE20', 'DE21']

    elec_trans = deflex.transmission.get_electrical_transmission_deflex()

    # Set transmission capacity of offshore power lines to installed capacity
    # Multiply the installed capacity with 1.1 to get a buffer of 10%.
    for offreg in offshore_regions:
        elec_trans.loc[elec_trans.index.str.contains(offreg), 'capacity'] = (
            vs[offreg].sum().sum() * 1.1)

    elec_trans = (
        pd.concat([elec_trans], axis=1, keys=['electrical']).sort_index(1))
    general_efficiency = cfg.get('transmission', 'general_efficiency')
    if general_efficiency is not None:
        elec_trans['electrical', 'efficiency'] = general_efficiency
    else:
        msg = ("The calculation of the efficiency by distance is not yet "
               "implemented")
        raise NotImplementedError(msg)
    return elec_trans


def scenario_storages():
    stor = deflex.storages.pumped_hydroelectric_storage().transpose()
    return pd.concat([stor], axis=1, keys=['phes']).swaplevel(0, 1, 1)


def add_pp_limit(table_collection, year):
    if len(cfg.get_dict('limited_transformer').keys()) > 0:
        repp = reegis_tools.bmwi.bmwi_re_energy_capacity()
        trsf = table_collection['transformer']
        for limit_trsf in cfg.get_dict('limited_transformer').keys():
            trsf = table_collection['transformer']
            try:
                limit = repp.loc[year, (limit_trsf, 'energy')]
            except KeyError:
                msg = "Cannot calculate limit for {0} in {1}."
                raise ValueError(msg.format(limit_trsf, year))
            cap_sum = trsf.loc[
                'capacity', (slice(None), slice(limit_trsf))].sum()
            for region in trsf.columns.get_level_values(level=0).unique():
                trsf.loc['limit_elec_pp', (region, limit_trsf)] = round(
                    trsf.loc['capacity', (region, limit_trsf)] /
                    cap_sum * limit + 0.5)

        trsf.loc['limit_elec_pp'] = trsf.loc['limit_elec_pp'].fillna(
            float('inf'))

        table_collection['transformer'] = trsf
    return table_collection


def commodity_sources(year, table_collection):
    commodity_src = scenario_commodity_sources(year)
    commodity_src = commodity_src.swaplevel().unstack()

    msg = ("The unit for {0} of the source is '{1}'. "
           "Will multiply it with {2} to get '{3}'.")

    converter = {'costs': ['costs', 'EUR/J', 1e+9 * 3.6, 'EUR/MWh'],
                 'emission': ['emission', 'g/J', 1e+6 * 3.6, 'kg/MWh']}

    transformer_list = (
        table_collection['transformer'].columns.get_level_values(
            level=1).unique())

    # Delete unused sources
    for col in commodity_src.columns:
        if col not in transformer_list:
            del commodity_src[col]

    # convert units
    for key in converter.keys():
        commodity_src.loc[key] = commodity_src.loc[key].multiply(
            converter[key][2])
        logging.warning(msg.format(*converter[key]))

    # Add region level to be consistent to other tables
    commodity_src.columns = pd.MultiIndex.from_product(
        [['DE'], commodity_src.columns])

    table_collection['commodity_source'] = commodity_src
    return table_collection


def scenario_commodity_sources(year, use_znes_2014=True):
    cs = reegis_tools.commodity_sources.get_commodity_sources()
    rename_cols = {key.lower(): value for key, value in
                   cfg.get_dict('source_names').items()}
    cs = cs.rename(columns=rename_cols)
    cs_year = cs.loc[year]
    if use_znes_2014:
        before = len(cs_year[cs_year.isnull()])
        cs_year = cs_year.fillna(cs.loc[2014])
        after = len(cs_year[cs_year.isnull()])
        if before - after > 0:
            logging.warning("Values were replaced with znes2014 data.")
    cs_year.sort_index(inplace=True)
    return cs_year


def scenario_demand(year, time_series):
    time_series = scenario_elec_demand(year, time_series)
    time_series = scenario_heat_demand(year, time_series)
    return time_series


def scenario_heat_demand(year, table):
    idx = table.index  # Use the index of the existing time series
    table = pd.concat([table, deflex.demand.get_heat_profiles_deflex(year,
                                                                     idx)],
                      axis=1)
    return table.sort_index(1)


def scenario_elec_demand(year, table):
    annual_demand = cfg.get('electricity_demand', 'annual_demand')
    demand_method = cfg.get('electricity_demand', 'demand_method')

    if annual_demand == 'bmwi':
        annual_demand = reegis_tools.bmwi.get_annual_electricity_demand_bmwi(
            year)
        msg = ("Unit of BMWI electricity demand is 'TWh'. "
               "Will multiply it with {0} to get 'MWh'")
        converter = 1e+6
        annual_demand = annual_demand * 1e+6
        logging.warning(msg.format(converter))

    df = deflex.demand.get_deflex_profile(
        year, demand_method, annual_demand=annual_demand)
    df = pd.concat([df], axis=1, keys=['electrical_load']).swaplevel(0, 1, 1)
    df = df.reset_index(drop=True).set_index(table.index)
    return pd.concat([table, df], axis=1).sort_index(1)


def scenario_feedin(year):
    # pv feedin
    my_index = pd.MultiIndex(
            levels=[[], []], labels=[[], []],
            names=['region', 'type'])
    feedin = scenario_feedin_pv(year, my_index)
    feedin = scenario_feedin_wind(year, feedin)
    for feedin_type in ['hydro', 'geothermal']:
        df = deflex.feedin.get_deflex_feedin(year, feedin_type)
        df = pd.concat([df], axis=1, keys=[feedin_type]).swaplevel(0, 1, 1)
        feedin = pd.DataFrame(pd.concat([feedin, df], axis=1)).sort_index(1)
    return feedin


def scenario_feedin_wind(year, feedin_ts):
    wind = deflex.feedin.get_deflex_feedin(year, 'wind')
    for reg in wind.columns.levels[0]:
        feedin_ts[reg, 'wind'] = wind[
            reg, 'coastdat_{0}_wind_ENERCON_127_hub135_pwr_7500'.format(year),
            'E_126_7500']
    return feedin_ts.sort_index(1)


def scenario_feedin_pv(year, my_index):
    pv_types = cfg.get_dict('pv_types')
    pv_orientation = cfg.get_dict('pv_orientation')
    pv = deflex.feedin.get_deflex_feedin(year, 'solar')

    # combine different pv-sets to one feedin time series
    feedin_ts = pd.DataFrame(columns=my_index, index=pv.index)
    orientation_fraction = pd.Series(pv_orientation)

    pv.sort_index(1, inplace=True)
    orientation_fraction.sort_index(inplace=True)
    base_set_column = 'coastdat_{0}_solar_{1}'.format(year, '{0}')
    for reg in pv.columns.levels[0]:
        feedin_ts[reg, 'solar'] = 0
        for mset in pv_types.keys():
            set_col = base_set_column.format(mset)
            feedin_ts[reg, 'solar'] += pv[reg, set_col].multiply(
                orientation_fraction).sum(1).multiply(
                    pv_types[mset])
            # feedin_ts[reg, 'solar'] = rt
    # print(f.sum())
    # from matplotlib import pyplot as plt
    # f.plot()
    # plt.show()
    # exit(0)
    return feedin_ts.sort_index(1)


def decentralised_heating():
    filename = os.path.join(cfg.get('paths', 'data_deflex'),
                            cfg.get('heating', 'table'))
    return pd.read_csv(filename, header=[0, 1], index_col=[0])


def chp_scenario(table_collection, year):

    # values from heat balance
    heat_b = deflex.chp.get_chp_share_and_efficiency(year)

    heat_demand = deflex.demand.get_heat_profiles_deflex(year)
    return chp_table(heat_b, heat_demand, table_collection)


def chp_table(heat_b, heat_demand, table_collection, regions=None):
    trsf = table_collection['transformer']
    trsf = trsf.fillna(0)

    rows = ['Heizkraftwerke der allgemeinen Versorgung (nur KWK)',
            'Heizwerke']
    if regions is None:
        regions = sorted(heat_b.keys())

    logging.info('start')
    for region in regions:
        eta_hp = round(heat_b[region]['sys_heat'] * heat_b[region]['hp'], 2)
        eta_heat_chp = round(
            heat_b[region]['sys_heat'] * heat_b[region]['heat_chp'], 2)
        eta_elec_chp = round(heat_b[region]['elec_chp'], 2)

        # Remove 'district heating' and 'electricity' and spread the share
        # to the remaining columns.
        share = pd.DataFrame(columns=heat_b[region]['fuel_share'].columns)
        for row in rows:
            tmp = heat_b[region]['fuel_share'].loc[region, :, row]
            tot = float(tmp['total'])

            d = float(tmp['district heating'] + tmp['electricity'])
            tmp = tmp + tmp / (tot - d) * d
            tmp = tmp.reset_index(drop=True)
            share.loc[row] = tmp.loc[0]
        del share['district heating']
        del share['electricity']

        # Remove the total share
        del share['total']

        max_val = float(heat_demand[region]['district_heating'].max())
        sum_val = float(heat_demand[region]['district_heating'].sum())

        for fuel in share.columns:
            if fuel == 'gas':
                src = 'natural gas'
            else:
                src = fuel

            # CHP
            trsf.loc['limit_heat_chp', (region, src)] = round(
                    sum_val * share.loc[rows[0], fuel] + 0.5)
            cap_heat_chp = round(
                    max_val * share.loc[rows[0], fuel] + 0.005, 2)
            trsf.loc['capacity_heat_chp', (region, src)] = cap_heat_chp
            cap_elec = (cap_heat_chp / eta_heat_chp *
                        eta_elec_chp)
            trsf.loc['capacity_elec_chp', (region, src)] = round(cap_elec, 2)
            trsf[region] = trsf[region].fillna(0)
            trsf.loc['capacity', (region, src)] = round(
                trsf.loc['capacity', (region, src)] - cap_elec)

            # HP
            trsf.loc['limit_hp', (region, src)] = round(
                sum_val * share.loc[rows[1], fuel] + 0.5)
            trsf.loc['capacity_hp', (region, src)] = round(
                max_val * share.loc[rows[1], fuel] + 0.005, 2)
            if trsf.loc['capacity_hp', (region, src)] > 0:
                trsf.loc['efficiency_hp', (region, src)] = eta_hp
            if cap_heat_chp * cap_elec > 0:
                trsf.loc['efficiency_heat_chp', (region, src)] = eta_heat_chp
                trsf.loc['efficiency_elec_chp', (region, src)] = eta_elec_chp

    logging.info('Done')

    trsf.sort_index(axis=1, inplace=True)
    for col in trsf.sum().loc[trsf.sum() == 0].index:
        del trsf[col]
    trsf[trsf < 0] = 0

    table_collection['transformer'] = trsf
    return table_collection


def powerplants_scenario(table_collection, year, round_values=None):
    """Get power plants for the scenario year
    """
    pp = deflex.powerplants.get_deflex_pp_by_year(year,
                                                  overwrite_capacity=True)
    region_column = '{0}_region'.format(cfg.get('init', 'map'))
    return powerplants(pp, table_collection, year, region_column,
                       round_values)


def powerplants(pp, table_collection, year, region_column='deflex_region',
                round_values=None):
    """This function works for all power plant tables with an equivalent
    structure e.g. power plants by state or other regions."""
    logging.info("Adding power plants to your scenario.")

    replace_names = cfg.get_dict('source_names')
    replace_names.update(cfg.get_dict('source_groups'))

    pp['energy_source_level_2'].replace(replace_names, inplace=True)

    pp['model_classes'] = pp['energy_source_level_2'].replace(
        cfg.get_dict('model_classes'))

    pp = pp.groupby(
        ['model_classes', region_column, 'energy_source_level_2']).sum()[
        ['capacity', 'capacity_in']]

    for model_class in pp.index.get_level_values(level=0).unique():
        pp_class = pp.loc[model_class]
        if model_class != 'volatile_source':
            pp_class['efficiency'] = (pp_class['capacity'] /
                                      pp_class['capacity_in'] * 100)
        del pp_class['capacity_in']
        if round_values is not None:
            pp_class = pp_class.round(round_values)
        if 'efficiency' in pp_class:
            pp_class['efficiency'] = pp_class['efficiency'].div(100)
        pp_class = pp_class.transpose()
        pp_class.index.name = 'parameter'
        table_collection[model_class] = pp_class
    table_collection = add_pp_limit(table_collection, year)
    return table_collection


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

    return table_collection


def create_basic_scenario(year, rmap=None, round_values=None):
    if rmap is not None:
        cfg.tmp_set('init', 'map', rmap)
    table_collection = deflex.basic_scenario.create_scenario(year,
                                                             round_values)
    table_collection = clean_time_series(table_collection)
    name = 'basic_{0}'.format(cfg.get('init', 'map'))
    sce = deflex.scenario_tools.Scenario(table_collection=table_collection,
                                         name=name, year=year)
    path = os.path.join(cfg.get('paths', 'scenario'), 'basic', str(year))
    sce.to_excel(os.path.join(path, '_'.join([sce.name, str(year)]) + '.xls'))
    sce.to_csv(os.path.join(path, 'csv'))


if __name__ == "__main__":
    logger.define_logging()
    # print(cfg.get('init', 'map'))
    # cfg.tmp_set('init', 'map', 'de23')
    # print(cfg.get('init', 'map'))
    # exit(0)
    for y in [2014]:
        for my_rmap in ['de21', 'de22']:
            create_basic_scenario(y, rmap=my_rmap)
    # print(scenario_commodity_sources(2014, use_znes_2014=True))
    # print(scenario_elec_demand(2014, pd.DataFrame()))
