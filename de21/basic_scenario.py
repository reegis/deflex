import pandas as pd
import logging
import reegis_tools.config as cfg
import reegis_tools.commodity_sources
import reegis_tools.bmwi
import de21.powerplants
import de21.feedin
import de21.demand
import de21.storages
import de21.transmission


def create_scenario(year, round_values):
    table_collection = {}

    logging.info('BASIC SCENARIO - TRANSMISSION')
    table_collection['transmission'] = scenario_transmission()

    logging.info('BASIC SCENARIO - STORAGES')
    table_collection['storages'] = scenario_storages()

    logging.info('BASIC SCENARIO - POWER PLANTS')
    table_collection = powerplants(
        table_collection, year, round_values)

    logging.info('BASIC SCENARIO - SOURCES')
    table_collection = add_attributes2sources(
        year, table_collection)
    table = scenario_feedin(year)

    logging.info('BASIC SCENARIO - DEMAND')
    table_collection['time_series'] = scenario_demand(
        year, table)
    print(table_collection['time_series'])
    return table_collection


def scenario_transmission():
    elec_trans = de21.transmission.get_electrical_transmission_de21()
    return pd.concat([elec_trans], axis=1, keys=['electrical']).sort_index(1)


def scenario_storages():
    stor = de21.storages.pumped_hydroelectric_storage().transpose()
    return pd.concat([stor], axis=1, keys=['phes']).swaplevel(0, 1, 1)


def set_limit_by_energy_production(year, fuels):
    """Calculate the limit based on the bmwi energy/capacity table.
    The elements of fuels, have to be in this table.
    """
    dc = {}
    repp = reegis_tools.bmwi.bmwi_re_energy_capacity()

    pp = de21.powerplants.get_de21_pp_by_year(year, overwrite_capacity=True)
    pp21 = pp.groupby(['energy_source_level_2', 'de21_region']).sum()
    for fuel in fuels:
        try:
            df = pp21.loc[fuel.capitalize(), ['capacity', 'capacity_in']].sum()
            w_avg = (df['capacity'] / df['capacity_in'])
            dc[fuel] = repp.loc[year, (fuel, 'energy')] / w_avg
        except KeyError:
            logging.error("Cannot calculate limit for {0} in {1}.".format(
                fuel, year))
            dc[fuel] = None
    return dc


def add_attributes2sources(year, table_collection):
    commodity_source = scenario_commodity_sources(year)

    cs = table_collection['controllable_source']

    cs_list = cs.columns.get_level_values(level=1).unique()

    limit = set_limit_by_energy_production(year, cs_list)
    for ctrl_src in cs_list:
        cap_sum = cs.loc['capacity', (slice(None), slice(ctrl_src))].sum()
        for region in cs.columns.get_level_values(level=0).unique():
            cs.loc['limit', (region, ctrl_src)] = (
                cs.loc['capacity', (region, ctrl_src)]
                / cap_sum * limit[ctrl_src])

        for attribute in ['emission', 'costs']:
            cs.loc[attribute, (slice(None), slice(ctrl_src))] = (
                commodity_source[ctrl_src, attribute])

    table_collection['controllable_source'] = cs

    commodity_source = commodity_source.swaplevel().unstack()
    transformer_list = (
        table_collection['transformer'].columns.get_level_values(
            level=1).unique())

    for col in commodity_source.columns:
        if col not in transformer_list:
            del commodity_source[col]

    # Add region level to be consistent to other tables
    commodity_source.columns = pd.MultiIndex.from_product(
        [['DE'], commodity_source.columns])

    table_collection['commodity_source'] = commodity_source

    return table_collection


def scenario_commodity_sources(year, use_znes_2014=True):
    cs = reegis_tools.commodity_sources.get_commodity_sources()
    rename_cols = {key.lower(): value for key, value in
                   cfg.get_dict('source_groups').items()}
    cs = cs.rename(columns=rename_cols)
    cs_year = cs.loc[year]
    if use_znes_2014:
        before = len(cs_year[cs_year.isnull()])
        cs_year = cs_year.fillna(cs.loc[2014])
        after = len(cs_year[cs_year.isnull()])
        if before - after > 0:
            logging.warning("Values were replaced with znes2014 data.")
    return cs_year


def scenario_demand(year, time_series):
    time_series = scenario_elec_demand(year, time_series)
    time_series = scenario_heat_demand(year, time_series)
    return time_series


def scenario_heat_demand(year, table):
    idx = table.index  # Use the index of the existing time series
    table = pd.concat([table, de21.demand.get_heat_profiles_de21(year, idx)],
                      axis=1)
    return table.sort_index(1)


def scenario_elec_demand(year, table):
    # Todo: config: scaled?, method
    scaled_by_bmwi = True
    demand_method = 'openego_entsoe'

    if scaled_by_bmwi:
        annual_demand = de21.demand.get_annual_demand_bmwi(year)
    else:
        annual_demand = None

    df = de21.demand.get_de21_profile(
        year, demand_method, annual_demand=annual_demand)
    df = pd.concat([df], axis=1, keys=['electrical_load']).swaplevel(0, 1, 1)
    df = df.reset_index().set_index(table.index)
    return pd.concat([table, df], axis=1).sort_index(1)


def scenario_feedin(year):
    # pv feedin
    my_index = pd.MultiIndex(
            levels=[[], []], labels=[[], []],
            names=['region', 'type'])
    feedin = scenario_feedin_pv(year, my_index)
    feedin = scenario_feedin_wind(year, feedin)
    for feedin_type in ['hydro', 'geothermal']:
        df = de21.feedin.get_de21_feedin(year, feedin_type)
        df = pd.concat([df], axis=1, keys=[feedin_type]).swaplevel(0, 1, 1)
        feedin = pd.DataFrame(pd.concat([feedin, df], axis=1)).sort_index(1)
    return feedin


def scenario_feedin_wind(year, feedin_ts):
    wind = de21.feedin.get_de21_feedin(year, 'wind')
    for reg in wind.columns.levels[0]:
        feedin_ts[reg, 'wind'] = wind[
            reg, 'coastdat_2012_wind_ENERCON_127_hub135_pwr_7500',
            'E_126_7500']
    return feedin_ts.sort_index(1)


def scenario_feedin_pv(year, my_index):
    pv_types = cfg.get_dict('pv_types')
    pv_orientation = cfg.get_dict('pv_orientation')
    try:
        pv = de21.feedin.get_de21_feedin(year, 'solar')
    except FileNotFoundError:
        logging.error("Cannot prepare solar feedin for {0}".format(year))
        return None
    # combine different pv-sets to one feedin time series
    feedin_ts = pd.DataFrame(columns=my_index, index=pv.index)
    orientation_fraction = pd.Series(pv_orientation)

    pv.sort_index(1, inplace=True)
    orientation_fraction.sort_index(inplace=True)

    for reg in pv.columns.levels[0]:
        feedin_ts[reg, 'solar'] = 0
        for mset in pv_types.keys():
            feedin_ts[reg, 'solar'] += pv[reg, mset].multiply(
                orientation_fraction).sum(1).multiply(
                    pv_types[mset])
            # feedin_ts[reg, 'solar'] = rt
    # print(f.sum())
    # from matplotlib import pyplot as plt
    # f.plot()
    # plt.show()
    # exit(0)
    return feedin_ts.sort_index(1)


def powerplants(table_collection, year, round_values=None):
    """
    """
    # Get power plants for the scenario year.
    pp = de21.powerplants.get_de21_pp_by_year(year, overwrite_capacity=True)
    logging.info("Adding power plants to your scenario.")

    pp['energy_source_level_2'].replace(cfg.get_dict('source_groups'),
                                        inplace=True)
    pp['model_classes'] = pp['energy_source_level_2'].replace(
        cfg.get_dict('model_classes'))

    pp = pp.groupby(
        ['model_classes', 'de21_region', 'energy_source_level_2']).sum()[
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
    return table_collection
