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
import warnings

# External libraries
import pandas as pd
from workalendar.europe import Germany

# oemof libraries
from oemof.tools import logger
import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles

# internal modules
import reegis.config as cfg
import reegis.entsoe
import reegis.bmwi
import reegis.geometries
import reegis.openego
import reegis.heat_demand

import deflex.geometries
import deflex.inhabitants


def renpass_demand_share():
    demand_share = os.path.join(cfg.get('paths', 'data_deflex'),
                                cfg.get('static_sources',
                                        'renpass_demand_share'))
    return pd.read_csv(
            demand_share, index_col='region_code', squeeze=True)


def openego_demand_share(overwrite=False, rmap=None):
    demand_reg = prepare_ego_demand(overwrite=overwrite, rmap=rmap)[
        'consumption']
    demand_sum = demand_reg.sum()
    return demand_reg.div(demand_sum)


def deflex_profile_from_entsoe(year, share, annual_demand=None,
                               overwrite=False):
    load_file = os.path.join(cfg.get('paths', 'entsoe'),
                             cfg.get('entsoe', 'load_file'))

    if not os.path.isfile(load_file) or overwrite:
        reegis.entsoe.split_timeseries_file(overwrite)

    # Fetch de load profile from entsoe
    de_load_profile = reegis.entsoe.get_entsoe_load(year).DE_load_

    load_profile = pd.DataFrame(index=de_load_profile.index)
    regions = pd.read_csv(
        os.path.join(
            cfg.get('paths', 'geo_deflex'),
            cfg.get('geometry', 'deflex_polygon')).format(
            map=cfg.get('init', 'map'), type='polygon', suffix='reegis'),
        index_col=[0])

    for region in regions.index:
        region = 'DE{:02}'.format(region)
        if region not in share:
            share[region] = 0
        load_profile[region] = de_load_profile.multiply(float(share[region]))

    if annual_demand is not None:
        load_profile = load_profile.div(load_profile.sum().sum()).multiply(
            annual_demand)
    return load_profile


def prepare_ego_demand(rmap=None, overwrite=False):
    if rmap is None:
        rmap = cfg.get('init', 'map')
    egofile_deflex = os.path.join(
        cfg.get('paths', 'demand'),
        cfg.get('demand', 'ego_file_deflex')).format(map=rmap)

    if os.path.isfile(egofile_deflex) and not overwrite:
        ego_demand_deflex = pd.read_hdf(egofile_deflex, 'demand')
    else:
        ego_demand_df = reegis.openego.get_ego_demand(
            overwrite=overwrite)
        # Create GeoDataFrame from ego demand file.
        ego_demand = reegis.geometries.create_geo_df(ego_demand_df)

        # Load region polygons
        deflex_regions = deflex.geometries.deflex_regions()

        # Add column with region id
        ego_demand = reegis.geometries.spatial_join_with_buffer(
            ego_demand, deflex_regions, name=rmap + '_region')

        # Overwrite Geometry object with its DataFrame, because it is not
        # needed anymore.
        ego_demand_deflex = pd.DataFrame(ego_demand)

        # Delete the geometry column, because spatial grouping will be done
        # only with the region column.
        del ego_demand_deflex['geometry']

        # Write out file (hdf-format).
        ego_demand_deflex.to_hdf(egofile_deflex, 'demand')

    return ego_demand_deflex.groupby('{0}_region'.format(rmap)).sum()


def create_deflex_slp_profile(year, outfile):
    demand_deflex = prepare_ego_demand()

    cal = Germany()
    holidays = dict(cal.holidays(year))

    deflex_profile = pd.DataFrame()

    for region in demand_deflex.index:
        annual_demand = demand_deflex.loc[region]

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

        deflex_profile[region] = elec_demand.sum(1).resample('H').mean()
    deflex_profile.to_csv(outfile)


def get_deflex_slp_profile(year, annual_demand=None, overwrite=False):
    outfile = os.path.join(
        cfg.get('paths', 'demand'),
        cfg.get('demand', 'ego_profile_pattern').format(
            year=year, map=cfg.get('init', 'map')))
    if not os.path.isfile(outfile) or overwrite:
        create_deflex_slp_profile(year, outfile)

    deflex_profile = pd.read_csv(
        outfile, index_col=[0], parse_dates=True).multiply(1000)

    if annual_demand is not None:
        deflex_profile = deflex_profile.div(deflex_profile.sum().sum()
                                            ).multiply(annual_demand)

    return deflex_profile


def get_deflex_profile(year, kind, annual_demand=None, overwrite=False):
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
        return get_deflex_slp_profile(year, annual_demand, overwrite)

    # Use the renpass demand share values to divide the national entsoe profile
    # into 18 regional profiles.
    elif kind == 'renpass':
        return deflex_profile_from_entsoe(year, renpass_demand_share(),
                                          annual_demand, overwrite)

    # Use the openEgo proposal to calculate the demand share values and use
    # them to divide the national entsoe profile.
    elif kind == 'openego_entsoe':
        return deflex_profile_from_entsoe(year, openego_demand_share(),
                                          annual_demand, overwrite)

    else:
        logging.error('Method "{0}" not found.'.format(kind))


def elec_demand_tester(year):
    oe = get_deflex_profile(year, 'openego') * 1000000
    # rp = get_deflex_profile(year, 'renpass') * 1000000
    ege = get_deflex_profile(year, 'openego_entsoe') * 1000000

    netto = reegis.bmwi.get_annual_electricity_demand_bmwi(year)

    oe_s = get_deflex_profile(year, 'openego', annual_demand=netto)
    # rp_s = get_deflex_profile(year, 'renpass', annual_demand=netto)
    ege_s = get_deflex_profile(year, 'openego_entsoe', annual_demand=netto)

    print('[TWh] original    scaled (BMWI)')
    print(' oe:  ', int(oe.sum().sum() / 1e+12), '       ',
          int(oe_s.sum().sum()))
    # print(' rp:  ', int(rp.sum().sum() / 1e+12), '       ',
    #       int(rp_s.sum().sum()))
    print('ege:  ', int(ege.sum().sum() / 1e+12), '       ',
          int(ege_s.sum().sum()))
    # print(ege_s)


def get_heat_profiles_by_state(year=None, weather_year=None):
    if weather_year is None:
        heat_demand_state_file = os.path.join(
                cfg.get('paths', 'demand'),
                cfg.get('demand', 'heat_profile_state').format(year=year))
    else:
        heat_demand_state_file = os.path.join(
                cfg.get('paths', 'demand'),
                cfg.get('demand', 'heat_profile_state_var').format(
                    year=year, weather_year=weather_year))

    # Load demand heat profiles by state
    if os.path.isfile(heat_demand_state_file):
        logging.info("Demand profiles by state exist. Reading file.")
        demand_state = pd.read_csv(heat_demand_state_file, index_col=[0],
                                   parse_dates=True, header=[0, 1, 2])
        demand_state = demand_state.tz_localize('UTC').tz_convert(
            'Europe/Berlin')
    else:
        demand_state = reegis.heat_demand.get_heat_profiles_by_state(
            year, to_csv=True, weather_year=weather_year)

    return demand_state


def get_heat_profiles_deflex(year, time_index=None, keep_unit=False,
                             weather_year=None, separate_regions=None,
                             combine_fuels=None, region_fuels=None):

    # separate_regions = keep all demand connected to the region
    if separate_regions is None:
        separate_regions = ['DE22']

    # add second fuel to first
    if combine_fuels is None:
        combine_fuels = [('natural gas', 'gas')]

    # fuels to be dissolved per region
    if region_fuels is None:
        region_fuels = ['district heating']

    demand_state = get_heat_profiles_by_state(year, weather_year)

    four_level_columns = pd.MultiIndex(levels=[[], [], [], []],
                                       labels=[[], [], [], []])

    demand_region = pd.DataFrame(index=demand_state.index,
                                 columns=four_level_columns)

    logging.info("Fetching inhabitants table.")
    my_ew = deflex.inhabitants.get_ew_by_deflex_subregions(year)

    state_ew = my_ew.groupby('state').sum()
    for region in my_ew.index:
        my_ew.loc[region, 'share_state'] = float(
            my_ew.loc[region, 'ew'] / state_ew.loc[my_ew.loc[region, 'state']])

    logging.info("Convert demand profile...")

    fuels = demand_state.columns.get_level_values(2).unique()
    sectors = demand_state.columns.get_level_values(1).unique()
    demand_state = demand_state.swaplevel(2, 0, axis=1)

    # Recalculate the demand of states to the demand of regions using the
    #  number inhabitants
    for subregion in my_ew.index:
        state = my_ew.loc[subregion, 'state']
        region = my_ew.loc[subregion, 'region']
        share = my_ew.loc[subregion, 'share_state']
        for sector in sectors:
            for fuel in fuels:
                demand_region[
                    region, fuel, sector, subregion] = (
                        demand_state[fuel, sector, state] * share)
    demand_region.sort_index(1, inplace=True)

    demand_region = demand_region.groupby(level=[0, 1], axis=1).sum()

    # Decentralised demand is combined to a nation-wide demand if not part
    # of region_fuels.
    regions = list(set(demand_region.columns.get_level_values(0).unique()) -
                   set(separate_regions))

    for fuel in fuels:
        demand_region['DE_demand', fuel] = 0

    for region in regions:
        for f in combine_fuels:
            demand_region[region, f[0]] += demand_region[region, f[1]]
            demand_region.drop((region, f[1]), axis=1, inplace=True)
        cols = list(set(demand_region[region].columns) - set(region_fuels))
        for col in cols:
            demand_region['DE_demand', col] += demand_region[region, col]
            demand_region.drop((region, col), axis=1, inplace=True)

    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    if len(demand_region) > 8760 and not leap_year:
        # If a non-leap year is combined with a leap weather year one day has
        # to be removed to get the same index length. It is possible to remove
        # February 29th but this may lead to sudden temperature and wind speed
        # changes. Therefore, it might be better to remove the last day.
        msg = ("To combine a leap weather year with a non-leap year one day"
               "has to be removed from the heat demand time series.")
        logging.warning(msg)
        # deflex_demand = deflex_demand.reset_index(drop=True).drop(
        #     range(1416, 1440), axis=0)
        if len(demand_region.iloc[8760:]) > 24:
            msg = ("{0} hours removed. This is more than a day! Check the "
                   "input data.")
            warnings.warn(msg.format(len(demand_region.iloc[8760:])),
                          RuntimeWarning)
        demand_region = demand_region.reset_index(drop=True).iloc[:8760]

    if time_index is not None:
        demand_region.index = time_index

    if not keep_unit:
        msg = ("The unit of the source is 'TJ'. "
               "Will be divided by {0} to get 'MWh'.")
        converter = 0.0036
        demand_region = demand_region.div(converter)
        demand_state = demand_state.div(converter)
        logging.warning(msg.format(converter))

    demand_region.sort_index(1, inplace=True)

    for c in demand_region.columns:
        if demand_region[c].sum() == 0:
            demand_region.drop(c, axis=1, inplace=True)

    if int(demand_region.sum().sum()) != int(demand_state.sum().sum()):
        logging.error("Something went wrong: {0} != {1}".format(
            int(demand_region.sum().sum()), int(demand_state.sum().sum())))

    return demand_region


if __name__ == "__main__":
    logger.define_logging(screen_level=logging.ERROR,
                          file_level=logging.ERROR)
    get_heat_profiles_deflex(2014)

    # egofile_deflex = os.path.join(
    #     cfg.get('paths', 'demand'),
    #     cfg.get('demand', 'ego_file_deflex')).format(map='de22')
    # ego_demand_deflex = pd.read_hdf(egofile_deflex, 'demand')
    # print(ego_demand_deflex['de22_region'].unique())
    # exit(0)
    cfg.tmp_set('init', 'map', 'de22')
    net = reegis.bmwi.get_annual_electricity_demand_bmwi(2014)
    dem22 = get_deflex_profile(2014, 'openego_entsoe', annual_demand=net).sum()
    cfg.tmp_set('init', 'map', 'de21')
    dem21 = get_deflex_profile(2014, 'openego_entsoe', annual_demand=net).sum()
    print(round(dem21-dem22, 2))
    print(round(dem21, 2))
    print(round(dem22, 2))
    # print(get_deflex_profile(2014, 'renpass', annual_demand=net).sum())
    exit(0)
    # print(openego_demand_share())
    # exit(0)
    # elec_demand_tester(2013)
    # prepare_ego_demand()
    # exit(0)
    for y in [2014]:
        df = reegis.heat_demand.get_heat_profiles_by_state(
            y, state=['BE'])['BE']
        print(df.groupby(level=1, axis=1).sum())
        # df = df.swaplevel(axis=1)
        # df = df['district heating'].sum(axis=1)
        # print(df)
        # df.copy().to_csv('/home/uwe/test.csv')
        # exit(0)
        print(get_heat_profiles_deflex(y))
        # print(heat_demand(y).loc['BE'].sum().sum() / 3.6)
    logging.info("Done!")
