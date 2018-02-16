import pandas as pd
# import scenario_tools as sc
import os
import logging
from oemof.tools import logger
import reegis_tools.config as cfg
import reegis_tools.commodity_sources
import reegis_tools.bmwi
import de21.powerplants
import de21.feedin
import de21.demand
import de21.storages
import de21.transmission


# from shapely.wkt import loads as wkt_loads
# import powerplants as pp





def create_scenario(year, round_values):
    table_collection = {'transmission': scenario_transmission(),
                        'storages': scenario_storages()}
    table_collection = powerplants(
        table_collection, year, round_values)
    table_collection = add_attributes2sources(
        year, table_collection)
    table = scenario_feedin(year)
    table_collection['time_series'] = scenario_demand(
        year, table)
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


def scenario_demand(year, table):
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


def commodity_sources(round_nominal_value=True):
    """

    Parameters
    ----------
    round_nominal_value : boolean
        Will round the nominal_value entry to integer. Should be set to False
        if the nominal_values are small.

    Returns
    -------
    list : List of local commodity sources
    """
    # variable_costs = {
    #     'biomass_and_biogas': 27.73476,
    #     'hard_coal': 45.86634,
    #     'hydro': 0.0000,
    #     'lignite': 27.5949,
    #     'natural_gas': 54.05328,
    #     'nuclear': 5.961744,
    #     'oil': 86.86674,
    #     'other_fossil_fuels': 27.24696,
    #     'waste': 30.0000,
    # }
    commoditybuses = dict()

    def add_commodity_sources(fuel_type, reg, val):
        fuel_type = fuel_type.lower().replace(" ", "_")
        label = '{0}_resodurce_{1}'.format(reg, fuel_type)
        source = '{0}_resource_{1}'.format(reg, fuel_type)
        target_bus = '{0}_bus_{1}'.format(reg, fuel_type)
        idx = ('Source', label, source, target_bus)
        columns = ['nominal_value', 'summed_max', 'variable_costs',
                   'sort_index']
        if val.limit == float('inf'):
            val.limit = ''
            val.summed_max = ''
        else:
            if round_nominal_value:
                val.limit = round(float(val.limit))
            val.summed_max = 1.0

        values = [val.limit, val.summed_max, val.costs, '{0}_1'.format(region)]
        de21.add_parameters(idx, columns, values)

    # global commodity sources
    globalfile = os.path.join(cfg.get('paths', 'scenario_path'),
                              'commodity_sources_global.csv')
    if os.path.isfile(globalfile):
        global_sources = pd.read_csv(globalfile, index_col=[0])
        region = 'DE00'
        for fuel, value in global_sources.iterrows():
            add_commodity_sources(fuel, region, value)
        commoditybuses['global'] = [
            x.lower().replace(" ", "_") for x in global_sources.index]
    else:
        commoditybuses['global'] = list()

    # local commodity sources
    localfile = os.path.join(cfg.get('paths', 'scenario_path'),
                             'commodity_sources_local.csv')
    if os.path.isfile(localfile):
        local_sources = pd.read_csv(localfile, index_col=[0], header=[0, 1])
        local_fuel_types = local_sources.columns.get_level_values(0).unique()
        for fuel in local_fuel_types:
            for region, value in local_sources[fuel].iterrows():
                add_commodity_sources(fuel, region, value)
        local_sources.columns.get_level_values(0).unique()

        commoditybuses['local'] = [
            x.lower().replace(" ", "_") for x in local_fuel_types]
    else:
        commoditybuses['local'] = list()

    return commoditybuses


def powerplantsr(year, round_nominal_value=True, ignore_errors=False):
    """
    Add transformer and connect them to their source bus.

    Use local_bus=True to connect the transformers to local buses. If you
    want to connect some transformers to local buses and some to global buses
    you have to call this function twice with different subsets of your
    DataFrame.
    """
    # Get power plants
    my_df = de21.powerplants.get_de21_pp_by_year(year, overwrite_capacity=True)

    logging.info("Adding power plants to your scenario.")

    my_df['energy_source_level_2'].replace(cfg.get_dict('source_groups'),
                                           inplace=True)
    my_df['model_classes'] = my_df['energy_source_level_2'].replace(
        cfg.get_dict('model_classes'))

    my_df = my_df.groupby(
        ['model_classes', 'de21_region', 'energy_source_level_2']).sum()[
        ['capacity', 'capacity_in']]

    # my_df['energy_source_level_2'].unique()
    for model_class in my_df.index.get_level_values(level=0).unique():
        if model_class == 'transformer':
            self.scenario[model_class] = transformer(my_df.loc[model_class])
        elif model_class == 'controllable_source':
            pass
        elif model_class == 'volatile_source':
            pass
        else:
            if not ignore_errors:
                raise ValueError(
                    "The model class {0} is unknown.\n"
                    "Please check the model_classes in your ini-file.")

    logging.info('Done')
    exit(0)
    print(cfg.get_dict('source_groups'))
    neu = my_df.groupby(by=cfg.get_dict('source_groups')).sum()
    print(neu)
    exit(0)
    print(my_df.index.get_level_values(level=1).unique())
    print(my_df)
    exit()


def transformerb(transf, round_nominal_value=True):
    for region in transf.index.get_level_values(0).unique():
        for fuel in transf.index.get_level_values(0).unique():
            print(region, fuel)
            fuel_type = fuel.lower().replace(" ", "_")
            if fuel_type in com_buses['local']:
                busid = reg
            else:
                busid = 'DE00'
            label = '{0}_pp_{1}'.format(reg, fuel_type)
            source_bus = '{0}_bus_{1}'.format(busid, fuel_type)
            target_bus = '{0}_bus_el'.format(reg)
            idx1 = ('LinearTransformer', label, label, target_bus)
            idx2 = ('LinearTransformer', label, source_bus, label)
            cols1 = ['conversion_factors', 'nominal_value', 'sort_index']
            cols2 = ['sort_index']
            if round_nominal_value:
                values['capacity'] = round(values['capacity'])
            values1 = [round(values['efficiency'], 2),
                       values['capacity'],
                       '{0}_1_{1}a'.format(reg, fuel_type[:5])]
            values2 = '{0}_1_{1}b'.format(reg, fuel_type[:5])
            if values['capacity'] > 0:
                de21.add_parameters(idx1, cols1, values1)
                de21.add_parameters(idx2, cols2, values2)


def renewable_sources(round_nominal_value=True):
    """
    Add renewable sources.

    You have to pass the capacities (region, type) and the normalised feedin
    series (type, region)
    """
    seq = pd.read_csv(os.path.join(cfg.get('paths', 'scenario_path'),
                                   'sources_timeseries.csv'),
                      index_col=[0], header=[0, 1], parse_dates=True)
    seq.index = seq.index.tz_localize('UTC').tz_convert('Europe/Berlin')

    cap = pd.read_csv(os.path.join(cfg.get('paths', 'scenario_path'),
                                   'sources_capacity.csv'),
                      index_col=[0])

    for reg in cap.index:
        for vtype in cap.columns:
            vtype = vtype.lower().replace(" ", "_")
            capacity = float(cap.loc[reg, vtype])
            if round_nominal_value:
                capacity = round(capacity)
            label = '{0}_{1}'.format(reg, vtype)
            target = '{0}_bus_el'.format(reg)
            idx = ('Source', label, label, target)
            cols = ['nominal_value', 'actual_value', 'fixed', 'sort_index']
            values = [capacity, 'seq', 1, '{0}_2'.format(reg)]
            if capacity > 0:
                de21.add_parameters(idx, cols, values)
                idx = ['Source', label, label, target, 'actual_value']
                de21.add_sequences(idx, seq[reg, vtype])


def demand_sinks(round_nominal_value=True):
    """
    Add demand sinks.

    You have to pass the the time series for each region.
    """
    df = pd.read_csv(os.path.join(cfg.get('paths', 'scenario_path'),
                                  'demand.csv'),
                     index_col=[0], parse_dates=True)
    df.index = df.index.tz_localize('UTC').tz_convert('Europe/Berlin')

    for reg in df.columns:
        max_demand = df[reg].max()
        if round_nominal_value:
            max_demand = round(max_demand)
        label = '{0}_{1}'.format(reg, 'load')
        source = '{0}_bus_el'.format(reg)
        idx = ('Sink', label, source, label)
        cols = ['nominal_value', 'actual_value', 'fixed', 'sort_index']
        values = [max_demand, 'seq', 1, '{0}_3'.format(reg)]
        if max_demand > 0:
            de21.add_parameters(idx, cols, values)
            idx = ['Sink', label, source, label, 'actual_value']
            de21.add_sequences(idx, df[reg] / max_demand)


def storages(round_nominal_value=True):
    """Storages """
    df = pd.read_csv(os.path.join(cfg.get('paths', 'scenario_path'),
                                  'storages.csv'),
                     index_col=[0], parse_dates=True)
    for reg, values in df.iterrows():
        label = '{0}_storage'.format(reg)
        bus = '{0}_bus_el'.format(reg)
        idx1 = ('Storage', label, label, bus)
        idx2 = ('Storage', label, bus, label)
        cols1 = ['nominal_value', 'nominal_capacity',
                 'inflow_conversion_factor',
                 'outflow_conversion_factor', 'sort_index']
        cols2 = ['nominal_value', 'sort_index']
        if round_nominal_value:
            values['capacity'] = round(values['capacity'])
            values['max_in'] = round(values['max_in'])
            values['max_out'] = round(values['max_out'])
        values1 = [values.max_in, values.capacity,
                   round(values.efficiency_in, 2),
                   round(values.efficiency_out, 2),
                   '{0}_4a'.format(reg)]
        values2 = [values.max_out, '{0}_4b'.format(reg)]
        if values.capacity > 0:
            de21.add_parameters(idx1, cols1, values1)
            de21.add_parameters(idx2, cols2, values2)


def shortage_sources(shortage_regions, var_costs=1000):
    """Shortage sources"""
    for reg in shortage_regions:
        label = '{0}_{1}'.format(reg, 'shortage')
        idx = ('Source', label, label, '{0}_bus_el'.format(reg))
        cols = ['variable_costs', 'sort_index']
        values = [var_costs, '{0}_5a'.format(reg)]
        de21.add_parameters(idx, cols, values)


def excess_sinks(excess_regions):
    """Shortage sources"""
    for reg in excess_regions:
        label = '{0}_{1}'.format(reg, 'excess')
        idx = ('Sink', label, '{0}_bus_el'.format(reg), label)
        cols = ['sort_index']
        values = '{0}_5b'.format(reg)
        de21.add_parameters(idx, cols, values)


def powerlines(round_nominal_value=True):
    """Grid"""
    powerlinefile = os.path.join(cfg.get('paths', 'scenario_path'),
                                 'transmission.csv')

    if os.path.isfile(powerlinefile):
        df = pd.read_csv(powerlinefile, index_col=[0])

        de21.add_comment_line('POWERLINES', 'P_DE00_DE00_0')
        for line, value in df.iterrows():
            if round_nominal_value:
                value['capacity'] = round(value['capacity'])
            reg1, reg2 = line.split('-')
            connections = [(reg1, reg2), (reg2, reg1)]
            for from_reg, to_reg in connections:
                label = '{0}_{1}_powerline'.format(from_reg, to_reg)
                source_bus = '{0}_bus_el'.format(from_reg)
                target_bus = '{0}_bus_el'.format(to_reg)
                idx1 = ('LinearTransformer', label, label, target_bus)
                idx2 = ('LinearTransformer', label, source_bus, label)
                cols1 = ['conversion_factors', 'nominal_value', 'sort_index']
                cols2 = ['sort_index']
                values1 = [round(value.efficiency, 3),
                           value['capacity'],
                           'P_{0}_1a'.format(line)]
                values2 = 'P_{0}_1b'.format(line)
                if value['capacity'] > 0:
                    de21.add_parameters(idx1, cols1, values1)
                    de21.add_parameters(idx2, cols2, values2)


def create_objects_from_dataframe_collection():
    # Add objects to scenario tables
    de21.create_tables()
    logging.info("Add objects to scenario tables.")

    # Add comment lines to get a better overview
    de21.add_comment_line('GLOBAL RESOURCES', '0000_0')
    for r in regions:  # One comment line for every region
        de21.add_comment_line('{0}'.format(r), '{0}_0'.format(r))

    # Add objects
    commodity_buses = commodity_sources()
    transformer(commodity_buses)
    renewable_sources()
    demand_sinks()
    storages()
    shortage_sources(regions)
    excess_sinks(regions)
    powerlines()
    # Sort table and store it.
    logging.info("Sort and store files.")
    if write_table:
        de21.write_tables()


# Define default logger
logger.define_logging()
sc = Scenario(2012)
sc.create_basic_scenario()
sc.to_excel()
sc.to_csv('/home/uwe/csv_test')

exit(0)
read_only = cfg.get('csv', 'read_only')
write_table = cfg.get('csv', 'write_table')
solver = cfg.get('general', 'solver')

cfg.set('paths', 'scenario_path', os.path.join(
    cfg.get('paths', 'scenario_data'),
    cfg.get('general', 'name').replace(' ', '_').lower()))

# Set path name and year for the basic scenario
my_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                       'my_scenarios')

my_name = 'de21_basic_uwe'
year = cfg.get('general', 'year')
datetime_index = pd.date_range('{0}-01-01 00:00:00'.format(year),
                               '{0}-12-31 23:00:00'.format(year),
                               freq='60min', tz='Europe/Berlin')
logging.info("Creating basic scenario '{0}' for {1} in {2}".format(
    my_name, year, my_path))

# Get list of regions from csv-file
regions = pd.read_csv(os.path.join(
    cfg.get('paths', 'geometry'),
    cfg.get('geometry', 'region_polygon_simple'))).gid

# Initialise scenario add empty tables
de21 = sc.SolphScenario(path=my_path, name=my_name, timeindex=datetime_index)

if read_only:
    logging.info("Reading scenario tables.")
else:
    create_objects_from_dataframe_collection()

logging.info("Creating nodes.")

de21.create_nodes()

logging.info("Creating OperationalModel")

om = OperationalModel(de21)

logging.info('OM created. Starting optimisation using {0}'.format(solver))

om.receive_duals()

om.solve(solver=solver, solve_kwargs={'tee': True})

logging.info('Optimisation done.')

results = ResultsDataFrame(energy_system=de21)

if not os.path.isdir('results'):
    os.mkdir('results')
date = '2017_03_21'
file_name = ('scenario_' + de21.name + date + '_' +
             'results_complete.csv')

results_path = 'results'

results.to_csv(os.path.join(results_path, file_name))
logging.info("Results stored to {0}".format(
    os.path.join(results_path, file_name)))
logging.info("Done")
