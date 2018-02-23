# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

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
from workalendar.europe import Germany

# oemof libraries
from oemof.tools import logger
import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles

# internal modules
import reegis_tools.config as cfg
import reegis_tools.entsoe
import reegis_tools.bmwi
import reegis_tools.geometries
import reegis_tools.energy_balance
import reegis_tools.coastdat

import de21.geometries
import de21.inhabitants


def renpass_demand_share():
    demand_share = os.path.join(cfg.get('paths', 'data_de21'),
                                cfg.get('static_sources',
                                        'renpass_demand_share'))
    return pd.read_csv(
            demand_share, index_col='region_code', squeeze=True)


def openego_demand_share():
    demand_reg = prepare_ego_demand()['sector_consumption_sum']
    demand_sum = demand_reg.sum()
    return demand_reg.div(demand_sum)


def de21_profile_from_entsoe(year, share, annual_demand=None, overwrite=False):
    load_file = os.path.join(cfg.get('paths', 'entsoe'),
                             cfg.get('entsoe', 'load_file'))

    if not os.path.isfile(load_file) or overwrite:
        reegis_tools.entsoe.split_timeseries_file(overwrite)

    # start = datetime.datetime(year, 1, 1, 0, 0)
    # end = datetime.datetime(year, 12, 31, 23, 0)

    entsoe = reegis_tools.entsoe.get_entsoe_load(year)
    # entsoe = entsoe.tz_localize('UTC').tz_convert('Europe/Berlin')
    de_load_profile = entsoe.DE_load_

    load_profile = pd.DataFrame(index=de_load_profile.index)
    for i in range(21):
        region = 'DE{:02.0f}'.format(i + 1)
        if region not in share:
            share[region] = 0
        load_profile[region] = de_load_profile.multiply(float(share[region]))

    if annual_demand is not None:
        load_profile = load_profile.div(load_profile.sum().sum()).multiply(
            annual_demand)
    return load_profile


def prepare_ego_demand(overwrite=False):
    egofile = os.path.join(cfg.get('paths', 'demand'),
                           cfg.get('demand', 'ego_file'))

    if os.path.isfile(egofile) and not overwrite:
        ego_demand = pd.read_hdf(egofile, 'demand')
    else:
        # Create GeoDataFrame from ego demand file.
        ego_demand = reegis_tools.geometries.Geometry(name='ego demand')
        ego_demand.load_csv(cfg.get('paths', 'data_de21'),
                            cfg.get('demand', 'ego_input_file'))
        ego_demand.create_geo_df(wkt_column='st_astext')

        # Load region polygons
        de21_regions = de21.geometries.de21_regions()

        # Add column with region id
        ego_demand.gdf = reegis_tools.geometries.spatial_join_with_buffer(
            ego_demand, de21_regions)

        # Copy results form geoDataFrame to DataFrame
        ego_demand.gdf2df()

        # Delete the geometry column, because spatial grouping will be done
        # only with the region column.
        del ego_demand.df['geometry']

        # Write out file (hdf-format).
        ego_demand.df.to_hdf(egofile, 'demand')
        ego_demand = ego_demand.df
    return ego_demand.groupby('de21_regions').sum()


def create_de21_slp_profile(year, outfile):
    demand_de21 = prepare_ego_demand()

    cal = Germany()
    holidays = dict(cal.holidays(year))

    de21_profile = pd.DataFrame()

    for region in demand_de21.index:
        annual_demand = demand_de21.loc[region]

        annual_electrical_demand_per_sector = {
            'g0': annual_demand.sector_consumption_retail,
            'h0': annual_demand.sector_consumption_residential,
            'l0': annual_demand.sector_consumption_agricultural,
            'i0': annual_demand.sector_consumption_industrial}
        e_slp = bdew.ElecSlp(year, holidays=holidays)

        elec_demand = e_slp.get_profile(annual_electrical_demand_per_sector)

        # Add the slp for the industrial group
        ilp = profiles.IndustrialLoadProfile(e_slp.date_time_index,
                                             holidays=holidays)

        elec_demand['i0'] = ilp.simple_profile(
            annual_electrical_demand_per_sector['i0'])

        de21_profile[region] = elec_demand.sum(1).resample('H').mean()
    de21_profile.to_csv(outfile)


def get_de21_slp_profile(year, annual_demand=None, overwrite=False):
    outfile = os.path.join(
        cfg.get('paths', 'demand'),
        cfg.get('demand', 'ego_profile_pattern').format(year=year))
    if not os.path.isfile(outfile) or overwrite:
        create_de21_slp_profile(year, outfile)

    de21_profile = pd.read_csv(
        outfile, index_col=[0], parse_dates=True).multiply(1000)

    if annual_demand is not None:
        de21_profile = de21_profile.div(de21_profile.sum().sum()).multiply(
            annual_demand)

    return de21_profile


def get_annual_demand_bmwi(year):
    """Returns the annual demand for the given year from the BMWI Energiedaten
    in Wh (Watthours). Will return None if data for the given year is not
    available.
    """
    infile = reegis_tools.bmwi.get_bmwi_energiedaten_file()

    table = pd.read_excel(infile, '21', skiprows=7, index_col=[0])
    try:
        return table.loc['   zusammen', year] * 1e+12
    except KeyError:
        return None


def get_de21_profile(year, kind, annual_demand=None, overwrite=False):
    """

    Parameters
    ----------
    year : int
        The year of the profile. The year is passed to the chosen function.
        Make sure the function can handle the given year.
    kind : str
        Name of the method to create the profile
    annual_demand : float
        The annual demand for the profile. By default the original annual
        demand is used.
    overwrite :
        Be aware that some results are stored to speed up the calculations. Set
        overwrite to True or remove the stored files if you are not sure.

    Returns
    -------

    """
    # Use the openEgo proposal to calculate annual demand and standardised
    # load profiles to create profiles.
    if kind == 'openego':
        return get_de21_slp_profile(year, annual_demand, overwrite)

    # Use the renpass demand share values to divide the national entsoe profile
    # into 18 regional profiles.
    elif kind == 'renpass':
        return de21_profile_from_entsoe(year, renpass_demand_share(),
                                        annual_demand, overwrite)

    # Use the openEgo proposal to calculate the demand share values and use
    # them to divide the national entsoe profile.
    elif kind == 'openego_entsoe':
        return de21_profile_from_entsoe(year, openego_demand_share(),
                                        annual_demand, overwrite)

    else:
        logging.error('Method "{0}" not found.'.format(kind))


def elec_demand_tester(year):
    oe = get_de21_profile(year, 'openego') * 1000000
    rp = get_de21_profile(year, 'renpass') * 1000000
    ege = get_de21_profile(year, 'openego_entsoe') * 1000000

    netto = get_annual_demand_bmwi(year)

    oe_s = get_de21_profile(year, 'openego', annual_demand=netto)
    rp_s = get_de21_profile(year, 'renpass', annual_demand=netto)
    ege_s = get_de21_profile(year, 'openego_entsoe', annual_demand=netto)

    print('[TWh] original    scaled (BMWI)')
    print(' oe:  ', int(oe.sum().sum() / 1e+12), '       ',
          int(oe_s.sum().sum() / 1e+12))
    print(' rp:  ', int(rp.sum().sum() / 1e+12), '       ',
          int(rp_s.sum().sum() / 1e+12))
    print('ege:  ', int(ege.sum().sum() / 1e+12), '       ',
          int(ege_s.sum().sum() / 1e+12))
    print(ege_s)


def heat_demand(year):
    eb = reegis_tools.energy_balance.get_states_balance(year)
    eb.sort_index(inplace=True)

    # get fraction of domestic and retail from the german energy balance
    share = reegis_tools.energy_balance.get_domestic_retail_share(year)

    # Use 0.5 for both sectors if no value is given
    share.fillna(0.5, inplace=True)

    # Divide domestic and retail by the value of the german energy balance if
    # the sum of domestic and retail does not equal the value given in the
    # local energy balance.
    check_value = True
    for state in eb.index.get_level_values(0).unique():
        for col in eb.columns:
            check = (eb.loc[(state, 'domestic'), col] +
                     eb.loc[(state, 'retail'), col] -
                     eb.loc[(state, 'domestic and retail'), col]).round()
            if check < 0:
                for sector in ['domestic', 'retail']:
                    eb.loc[(state, sector), col] = (
                        eb.loc[(state, 'domestic and retail'), col] *
                        share.loc[col, sector])

                check = (eb.loc[(state, 'domestic'), col] +
                         eb.loc[(state, 'retail'), col] -
                         eb.loc[(state, 'domestic and retail'), col]).round()

                if check < 0:
                    logging.error("In {0} the {1} sector results {2}".format(
                        state, col, check))
                    check_value = False
    if check_value:
        logging.debug("Divides 'domestic and retail' without errors.")

    # Reduce energy balance to the needed columns and group by fuel groups.
    eb = eb.loc[(slice(None), ['industrial', 'domestic', 'retail']), ]

    eb = eb.groupby(by=cfg.get_dict('FUEL_GROUPS_HEAT_DEMAND'), axis=1).sum()

    # Remove empty columns
    for col in eb.columns:
        if not (eb.loc[(slice(None), 'domestic'), col].sum() > 0 or
                eb.loc[(slice(None), 'retail'), col].sum() > 0 or
                eb.loc[(slice(None), 'industrial'), col].sum() > 0):
            del eb[col]

    # The use of electricity belongs to the electricity sector. It is possible
    # to connect it to the heating sector for future scenarios.
    del eb['electricity']
    del eb['total']  # if electricity is removed total is not correct anymore.

    # get fraction of mechanical energy use and subtract it from the balance to
    # get the use of heat only.
    share_mech = share_of_mechanical_energy_bmwi(year)
    for c in share_mech.columns:
        for i in share_mech.index:
            eb.loc[(slice(None), c), i] -= (
                eb.loc[(slice(None), c), i] * share_mech.loc[i, c])
    eb.sort_index(inplace=True)

    return eb


def share_of_mechanical_energy_bmwi(year):
    mech = pd.DataFrame()
    fs = reegis_tools.bmwi.read_bmwi_sheet_7()
    fs.sort_index(inplace=True)
    sector = 'Industrie'
    total = float(fs.loc[(sector, 'gesamt'), year])
    mech[sector] = fs.loc[(sector, 'mechanische Energie'), year].div(
        total).round(3)

    fs = reegis_tools.bmwi.read_bmwi_sheet_7(a=True)
    fs.sort_index(inplace=True)
    for sector in fs.index.get_level_values(0).unique():
        total = float(fs.loc[(sector, 'gesamt'), year])
        mech[sector] = fs.loc[(sector, 'mechanische Energie'), year].div(
            total).astype(float).round(3)
    mech.drop(' - davon Strom', inplace=True)
    mech.drop('mechanische Energie', inplace=True)
    ren_col = {
        'Industrie': 'industrial',
        'Gewerbe, Handel, Dienstleistungen ': 'retail',
        'private Haushalte': 'domestic', }
    ren_index = {
        ' - davon Öl': 'oil',
        ' - davon Gas': 'natural gas', }
    del mech.index.name
    mech.rename(columns=ren_col, inplace=True)
    mech.rename(index=ren_index, inplace=True)
    mech.fillna(0, inplace=True)
    return mech


def share_houses_flats(key=None):
    """

    Parameters
    ----------
    key str
        Valid keys are: 'total_area', 'avg_area', 'share_area', 'total_number',
         'share_number'.

    Returns
    -------
    dict or pd.DataFrame
    """
    size = pd.Series([1, 25, 50, 70, 90, 110, 130, 150, 170, 190, 210])
    infile = os.path.join(
        cfg.get('paths', 'data_de21'),
        cfg.get('general_sources', 'zensus_flats'))
    whg = pd.read_csv(infile, delimiter=';', index_col=[0], header=[0, 1],
                      skiprows=5)
    whg = whg.loc[whg['Insgesamt', 'Insgesamt'].notnull()]
    new_index = []
    states = cfg.get_dict('STATES')
    for i in whg.index:
        new_index.append(states[i[3:-13]])
    whg.index = new_index

    flat = {'total_area': pd.DataFrame(),
            'total_number': pd.DataFrame(),
            }
    for f in whg.columns.get_level_values(0).unique():
        df = pd.DataFrame(whg[f].values * size.values, columns=whg[f].columns,
                          index=whg.index)
        flat['total_area'][f] = df.sum(1) - df['Insgesamt']
        flat['total_number'][f] = df['Insgesamt']
    flat['total_area']['1 + 2 Wohnungen'] = (
        flat['total_area']['1 Wohnung'] + flat['total_area']['2 Wohnungen'])
    flat['total_number']['1 + 2 Wohnungen'] = (
        flat['total_number']['1 Wohnung'] +
        flat['total_number']['2 Wohnungen'])

    flat['avg_area'] = flat['total_area'].div(flat['total_number'])
    flat['share_area'] = (flat['total_area'].transpose().div(
        flat['total_area']['Insgesamt'])).transpose().round(3)
    flat['share_number'] = (flat['total_number'].transpose().div(
        flat['total_number']['Insgesamt'])).transpose().round(3)

    if key is None:
        return flat
    elif key in flat:
        return flat[key].sort_index()
    else:
        logging.warning(
            "'{0}' is an invalid key for function 'share_houses_flats'".format(
                key))
    return None


def get_heat_profile_from_demandlib(temperature, annual_demand, sector, year,
                                    build_class=1):
    cal = Germany()
    holidays = dict(cal.holidays(year))

    if 'efh' in sector:
        shlp_type = 'EFH'
    elif 'mfh' in sector:
        shlp_type = 'MFH'
    elif 'domestic' in sector:
        shlp_type = 'MFH'
    elif 'retail' in sector:
        shlp_type = 'ghd'
        build_class = 0
    elif 'industrial' in sector:
        shlp_type = 'ghd'
        build_class = 0
    else:
        raise AttributeError('"{0}" is an unknown sector.'.format(sector))
    return bdew.HeatBuilding(
        temperature.index, holidays=holidays, temperature=temperature,
        shlp_type=shlp_type, wind_class=0, building_class=build_class,
        annual_heat_demand=annual_demand, name=sector, ww_incl=True
        ).get_bdew_profile()


def get_heat_profiles_by_state(year, to_csv=False, divide_domestic=False):
    building_class = {}
    for (k, v) in cfg.get_dict('building_class').items():
        for s in v.split(', '):
            building_class[s] = int(k)

    house_flats = share_houses_flats('share_area')
    demand_state = heat_demand(year).sort_index()

    if divide_domestic:
        for state in demand_state.index.get_level_values(0).unique():
            dom = demand_state.loc[state, 'domestic']
            demand_state.loc[(state, 'domestic_efh'), ] = (
                dom * house_flats.loc[state, '1 + 2 Wohnungen'])
            demand_state.sort_index(0, inplace=True)
            dom = demand_state.loc[state, 'domestic']
            demand_state.loc[(state, 'domestic_mfh'), ] = (
                dom * house_flats.loc[state, '3 und mehr Wohnungen'])
            demand_state.sort_index(0, inplace=True)

        demand_state.sort_index(inplace=True)
        demand_state.drop('domestic', level=1, inplace=True)

    temperatures = reegis_tools.coastdat.federal_state_average_weather(
        year, 'temp_air')

    temperatures = temperatures.tz_localize('UTC').tz_convert('Europe/Berlin')

    my_columns = pd.MultiIndex(levels=[[], [], []], labels=[[], [], []])
    heat_profiles = pd.DataFrame(columns=my_columns)

    for region in demand_state.index.get_level_values(0).unique():
        logging.info("Creating heat profile for {}".format(region))
        tmp = demand_state.loc[region].groupby(level=0).sum()
        temperature = temperatures[region] - 273
        for fuel in tmp.columns:
            logging.debug("{0} - {1} ({2})".format(
                region, fuel, building_class[region]))
            for sector in tmp.index:
                heat_profiles[(region, sector, fuel)] = (
                    get_heat_profile_from_demandlib(
                        temperature, tmp.loc[sector, fuel], sector, year,
                        building_class[region]))
    heat_profiles.sort_index(1, inplace=True)
    if to_csv:
        heat_profiles.to_csv(os.path.join(
            cfg.get('paths', 'demand'),
            cfg.get('demand', 'heat_profile_state').format(year=year)))
    return heat_profiles


def get_heat_profiles_de21(year, time_index=None):
    heat_demand_state_file = os.path.join(
            cfg.get('paths', 'demand'),
            cfg.get('demand', 'heat_profile_state').format(year=year))
    if os.path.isfile(heat_demand_state_file):
        logging.info("Demand profiles by state exist. Reading file.")
        demand_state = pd.read_csv(heat_demand_state_file, index_col=[0],
                                   parse_dates=True, header=[0, 1, 2])
        demand_state = demand_state.tz_localize('UTC').tz_convert(
            'Europe/Berlin')
    else:
        demand_state = get_heat_profiles_by_state(year, to_csv=True)

    my_index = demand_state.index
    my_columns1 = pd.MultiIndex(levels=[[], []], labels=[[], []])
    demand_region = pd.DataFrame(index=my_index, columns=my_columns1)

    my_columns2 = pd.MultiIndex(levels=[[], [], [], []],
                                labels=[[], [], [], []])
    district_heat_region = pd.DataFrame(index=my_index, columns=my_columns2)

    logging.info("Fetching inhabitants table.")
    my_ew = de21.inhabitants.get_ew_by_de21_subregions(year)
    my_ew = my_ew.replace({'state': cfg.get_dict('STATES')})

    state_ew = my_ew.groupby('state').sum()
    for region in my_ew.index:
        my_ew.loc[region, 'share_state'] = float(
            my_ew.loc[region, 'ew'] / state_ew.loc[my_ew.loc[region, 'state']])

    logging.info("Convert demand profile...")

    fuels = demand_state.columns.get_level_values(2).unique()
    sectors = demand_state.columns.get_level_values(1).unique()
    demand_state = demand_state.swaplevel(2, 0, axis=1)
    district_heat_state = None
    for fuel in fuels:
        if fuel != 'district heating':
            demand_region['DE_demand', fuel] = demand_state[fuel].sum(axis=1)
        else:
            district_heat_state = demand_state[fuel]

    for subregion in my_ew.index:
        state = my_ew.loc[subregion, 'state']
        region = my_ew.loc[subregion, 'region']
        share = my_ew.loc[subregion, 'share_state']
        for sector in sectors:
            district_heat_region[
                region, 'district_heating', sector, subregion] = (
                    district_heat_state[sector, state] * share)
    district_heat_region.sort_index(1, inplace=True)
    # print(district_heat_region)
    district_heat_region = district_heat_region.groupby(
        level=[0, 1], axis=1).sum()
    de21_demand = pd.concat([district_heat_region, demand_region], axis=1)

    if time_index is not None:
        de21_demand.index = time_index

    return de21_demand


if __name__ == "__main__":
    logger.define_logging()
    # elec_demand_tester(2013)
    for y in [2012, 2013]:
        get_heat_profiles_de21(y)
        print(heat_demand(y).loc['BE'].sum().sum() / 3.6)
    logging.info("Done!")
