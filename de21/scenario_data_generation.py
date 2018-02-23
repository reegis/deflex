
import os
import pprint
import pandas as pd
import numpy as np
import logging
import configuration as config
import demand
from oemof.tools import logger


def check_fraction(dic):
    """pass"""
    s = round(sum(dic.values()), 15)
    if s != 1:
        fdict = pprint.pformat(dic)
        raise ValueError('The sum of the values does not equal one. ' +
                         'Got {0} instead. \n {1}'.format(s, fdict))


def create_subdict_from_config_dict(conf, names):
    dc = {name: conf[name] for name in names}
    check_fraction(dc)
    return dc


def initialise_scenario():
    c = config.get_configuration()

    c.paths['scenario_path'] = os.path.join(
        c.paths['scenario_data'], c.general['name']).replace(' ', '_').lower()
    if not os.path.isdir(c.paths['scenario_path']):
        os.mkdir(c.paths['scenario_path'])
    return c


def prepare_transformer(c):
    logging.info('Prepare transformer...({0})'.format(c.general['year']))
    tpp = pd.read_csv(os.path.join(c.paths['powerplants'],
                                   c.files['transformer']),
                      index_col=[0, 1, 2])

    cols = pd.MultiIndex(levels=[[], []], labels=[[], []], names=['', ''])
    idx = tpp.index.get_level_values(2).unique().sort_values()
    transformer = pd.DataFrame(columns=cols, index=idx)

    try:
        for col in tpp.index.get_level_values(0).unique().sort_values():
            # get values for the given year
            df = tpp.loc[col, c.general['year']]

            # write values into new DataFrame
            transformer[(col, 'capacity')] = df.capacity
            transformer[(col, 'capacity')].fillna(0, inplace=True)
            transformer[(col, 'efficiency')] = df.efficiency
            idx = df.efficiency.notnull()
            w_avg = np.average(df[idx].efficiency, weights=df[idx].capacity)
            transformer[(col, 'efficiency')].fillna(w_avg, inplace=True)
            transformer.to_csv(os.path.join(c.paths['scenario_path'],
                                            'transformer.csv'))
    except TypeError:
        logging.error("Cannot prepare transformer for {0}".format(
            c.general['year']))


def prepare_sources(c):
    logging.info('Prepare sources...({0}, weather: {1})'.format(
        c.general['year'], c.general['weather_year']))
    spp = pd.read_csv(os.path.join(c.paths['powerplants'],
                                   c.files['sources']),
                      index_col=[0, 1, 2])

    cols = spp.index.get_level_values(0).unique().sort_values()
    idx = spp.index.get_level_values(2).unique().sort_values()
    sources = pd.DataFrame(index=idx)

    try:
        for col in cols:
            sources[col.lower().replace(" ", "_")] = spp.loc[col,
                                                             c.general['year']]
            sources[col.lower().replace(" ", "_")].fillna(0, inplace=True)

        sources.to_csv(os.path.join(c.paths['scenario_path'],
                                    'sources_capacity.csv'))
    except TypeError:
        logging.error("Cannot prepare sources for {0}".format(
            c.general['year']))

    # ************ wind ******
    # read wind feedin time series (feedin_wind)
    try:
        feedin_wind = pd.read_csv(
            os.path.join(c.paths['feedin'], 'wind', 'de21',
                         c.pattern['feedin_de21'].format(
                             year=c.general['weather_year'], type='wind')),
            index_col=0)

        # add type level to wind DataFrame
        feedin_wind.columns = pd.MultiIndex.from_product(
            [feedin_wind.columns, ['wind']])
    except FileNotFoundError:
        feedin_wind = pd.DataFrame()
        logging.error("Cannot prepare wind feedin for {0}".format(
            c.general['year']))

    # ************ hydro ******
    # read hydro feedin time series (feedin_hydro)
    try:
        feedin_hydro = pd.read_csv(
            os.path.join(c.paths['feedin'], 'hydro', 'de21',
                         c.pattern['feedin_de21'].format(
                            year=c.general['weather_year'], type='hydro')),
            index_col=0)

        # add type level to hydro DataFrame
        feedin_hydro.columns = pd.MultiIndex.from_product(
            [feedin_hydro.columns, ['hydro']])
    except FileNotFoundError:
        feedin_hydro = pd.DataFrame()
        logging.error("Cannot prepare hydro feedin for {0}".format(
            c.general['year']))

    # ************ geotherm ******
    # read hydro feedin time series to get the structure and overwrite it
    # with geotherm value
    try:
        feedin_geotherm = pd.read_csv(
            os.path.join(c.paths['feedin'], 'hydro', 'de21',
                         c.pattern['feedin_de21'].format(
                             year=c.general['weather_year'], type='hydro')),
            index_col=0)
        feedin_geotherm[feedin_geotherm.columns] = 0.5

        # add type level to geotherm DataFrame
        feedin_geotherm.columns = pd.MultiIndex.from_product(
            [feedin_geotherm.columns, ['geothermal']])
    except FileNotFoundError:
        feedin_geotherm = pd.DataFrame()
        logging.error("Cannot prepare geothermal feedin for {0}".format(
            c.general['year']))

    # ************ combine wind, hydro, geotherm ******
    feedin = pd.DataFrame(
        pd.concat([feedin_wind, feedin_hydro, feedin_geotherm], axis=1))

    # ************ pv ******
    # read solar feedin time series (feedin_solar)
    try:
        feedin_solar = pd.read_csv(
            os.path.join(
                c.paths['feedin'], 'solar', 'de21',
                c.pattern['feedin_de21'].format(year=c.general['weather_year'],
                                                type='solar')),
            index_col=0, header=[0, 1, 2])

        # combine different pv-sets to one feedin time series
        module_inverter_sets = create_subdict_from_config_dict(
            c.pv, c.pv['module_inverter_types'])
        orientation_sets = create_subdict_from_config_dict(
            c.pv, c.pv['orientation_types'])

        orientation_fraction = pd.Series(orientation_sets)

        feedin_solar.sort_index(1, inplace=True)
        orientation_fraction.sort_index(inplace=True)

        for reg in feedin_solar.columns.levels[0]:
            feedin[reg, 'solar'] = 0
            for mset in module_inverter_sets.keys():
                feedin[reg, 'solar'] += feedin_solar[reg, mset].multiply(
                    orientation_fraction).sum(1).multiply(
                        module_inverter_sets[mset])

        feedin.sort_index(1).to_csv(os.path.join(c.paths['scenario_path'],
                                                 'sources_timeseries.csv'))
    except FileNotFoundError:
        logging.error("Cannot prepare solar feedin for {0}".format(
            c.general['year']))


def prepare_storages(c):
    logging.info('Prepare storages...(no year!)')
    phes = pd.read_csv(os.path.join(c.paths['storages'],
                                    c.files['hydro_storages_de21']),
                       index_col='region')

    rename_columns = {
        'energy': 'capacity',
        'pump': 'max_in',
        'turbine': 'max_out',
        'pump_eff': 'efficiency_in',
        'turbine_eff': 'efficiency_out'}
    phes.rename(columns=rename_columns, inplace=True)
    phes.to_csv(os.path.join(c.paths['scenario_path'], 'storages.csv'))


def prepare_transmission_lines(c):
    logging.info('Prepare transmission lines...(no year!)')
    grid = pd.read_csv(os.path.join(c.paths['transmission'],
                                    c.files['transmission_de21']))

    # Remove duplicate lines (keep only one direction)
    grid['name'] = grid.name.apply(lambda x: '-'.join(sorted(x.split('-'))))
    grid.drop_duplicates('name', inplace=True)
    grid.set_index('name', drop=True, inplace=True)

    mind = grid.distance[grid.distance > 0].min()
    divd = (grid.distance.max() - mind) / 2 * 100

    # vary grid efficiency between 0.98 and 0.96
    grid['efficiency'] = 0.98 - (grid.distance - mind) / divd
    grid.loc[grid.distance == 0, 'efficiency'] = 0

    del grid['distance']

    grid.to_csv(os.path.join(c.paths['scenario_path'], 'transmission.csv'))


def prepare_demand(c):
    logging.info('Prepare demand...({0})'.format(c.general['demand_year']))
    elec_demand = demand.get_demand_by_region(c.general['demand_year'], c)
    if len(elec_demand) < 8760:
        logging.error("Cannot prepare electrical demand for {0}".format(
            c.general['year']))
    elec_demand.to_csv(os.path.join(c.paths['scenario_path'], 'demand.csv'))


def prepare_commodity_sources(c):
    logging.info('Prepare commodity sources...({})'.format(
        c.general['year']))
    transformer = pd.read_csv(
        os.path.join(c.paths['scenario_path'], 'transformer.csv'),
        index_col=[0], header=[0, 1])

    # create empty DataFrame for local sources
    cols = pd.MultiIndex(levels=[[], []], labels=[[], []], names=['', ''])
    local_sources = pd.DataFrame(columns=cols, index=transformer.index)

    # get list of transformer that will have a local commodity source
    local = c.general['local_sources']

    # get commodity sources
    com_src = pd.read_csv(os.path.join(c.paths['commodity'],
                                       c.files['commodity_sources']),
                          header=[0, 1], index_col=[0])

    # create DataFrame for global sources with all data sets from com_src
    global_sources = com_src.loc[c.general['year']].unstack()[
        [c.general['optimisation_target'], 'limit']]

    for l in local:
        s = transformer[l, 'capacity'].sum()
        local_sources[l, 'limit'] = (transformer[l, 'capacity'] / s *
                                     global_sources.loc[l, 'limit'])
        local_sources[l, 'costs'] = global_sources.loc[l, 'costs']
        global_sources.drop(l, inplace=True)

    local_sources.to_csv(
        os.path.join(c.paths['scenario_path'], 'commodity_sources_local.csv'))
    global_sources.to_csv(
        os.path.join(c.paths['scenario_path'], 'commodity_sources_global.csv'))


if __name__ == "__main__":
    logger.define_logging()
    cfg = initialise_scenario()
    prepare_transformer(cfg)
    prepare_sources(cfg)
    prepare_storages(cfg)
    prepare_demand(cfg)
    prepare_transmission_lines(cfg)
    prepare_commodity_sources(cfg)

    # fossil_sources(cfg)
    # TODO suche nach Wert falls Wert nan
    # year = 2000
    # ary = src.loc[src.index >= year, ('biomass', 'costs')]
    # mask = np.isnan(ary)
    # print(mask)
    # ary[mask] = np.interp(np.flatnonzero(mask),
    #                       np.flatnonzero(~mask), ary[~mask])
    # print(ary)
