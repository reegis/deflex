# -*- coding: utf-8 -*-

"""Analyses of deflex.

SPDX-FileCopyrightText: 2016-2020 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import os
from collections import namedtuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from deflex import config as cfg
from deflex import geometries
from deflex import powerplants as dp
from reegis import commodity_sources
from reegis.tools import download_file

TRANS = {
    "Abfall": "waste",
    "Kernenergie": "nuclear",
    "Braunkohle": "lignite",
    "Steinkohle": "hard coal",
    "Erdgas": "natural gas",
    "GuD": "natural gas",
    "Gasturbine": "natural gas gt",
    "Öl": "oil",
    "Sonstige": "other fossil fuels",
    "Emissionszertifikatspreis": "co2_price",
}

# Kostenannahmen von EWI
# https://www.ewi.uni-koeln.de/de/news/ewi-merit-order-tool-2019/
COSTS_CO2 = 25  # 25 €/tCO2 (aktueller Wert)
COSTS_EWI = {
    "hard coal": 11.28,
    "lignite": 3.1,
    "natural gas": 22.78,
    "oil": 32.92,
    "nuclear": 5.5,
    "waste": 0,
    "other fossil fuels": 32.92,
}


EMISSIONS_EWI = {
    "hard coal": 0.336,
    "lignite": 0.378,
    "natural gas": 0.202,
    "oil": 0.263,
    "nuclear": 0,
}


def download_ewi_data():
    """

    Returns
    -------
    namedtuple
    """
    # Download file
    url = (
        "https://www.ewi.uni-koeln.de/cms/wp-content/uploads/2019/12"
        "/EWI_Merit_Order_Tool_2019_1_4.xlsm"
    )
    fn = "/home/uwe/ewi.xlsm"
    download_file(fn, url)

    # Creat named tuple with all sub tables
    ewi_tables = {
        "fuel_costs": {"skiprows": 7, "usecols": "C:F", "nrows": 7},
        "transport_costs": {"skiprows": 21, "usecols": "C:F", "nrows": 7},
        "other_var_costs": {"skiprows": 31, "usecols": "C:F", "nrows": 8},
        "downtime": {"skiprows": 31, "usecols": "H:K", "nrows": 8},
        "emission": {"skiprows": 31, "usecols": "M:P", "nrows": 7},
        "co2_price": {"skiprows": 17, "usecols": "C:F", "nrows": 1},
    }
    ewi_data = {}
    ewi = namedtuple("ewi_data", list(ewi_tables.keys()))
    cols = ["fuel", "value", "unit", "source"]
    xls = pd.ExcelFile(fn)
    for table in ewi_tables.keys():
        tmp = xls.parse("Start", header=[0], **ewi_tables[table]).replace(
            TRANS
        )
        tmp.drop_duplicates(tmp.columns[0], keep="first", inplace=True)
        tmp.columns = cols
        ewi_data[table] = tmp.set_index("fuel")
    return ewi(**ewi_data)


def get_costs_and_emissions(source="ewi"):
    re_sources = ["geothermal", "solar", "wind", "hydro"]
    zeros = np.zeros(shape=(len(re_sources), 2))
    re = pd.DataFrame(zeros, columns=["costs", "emission"], index=re_sources)
    cs = commodity_sources.get_commodity_sources().loc[2014].unstack()
    converter = {
        "costs": ["costs", "EUR/J", 1e9 * 3.6, "EUR/MWh"],
        "emission": ["emission", "g/J", 1e6 * 3.6, "kg/MWh"],
    }
    for key in converter.keys():
        cs[key] = cs[key].multiply(converter[key][2])
    cs = pd.concat([re, cs])

    # Add region level to be consistent to other tables
    cs.columns = pd.MultiIndex.from_product([["reegis"], cs.columns])
    cs["ewi", "costs"] = pd.Series(COSTS_EWI)
    cs["ewi", "emission"] = pd.Series(EMISSIONS_EWI).multiply(1000)
    print(cs)
    if source == "all":
        return cs
    else:
        return cs[source]


def get_merit_order_ewi():
    fn = os.path.join(
        cfg.get("paths", "analyses"), "data", "merit_order_ewi.csv"
    )
    pp = pd.read_csv(fn, header=[0], index_col=[0])
    pp = pp.replace(TRANS)
    return pp


def get_merit_order_ewi_raw():
    fn = os.path.join(
        cfg.get("paths", "analyses"), "data", "merit_order_ewi_raw.csv"
    )
    pp = pd.read_csv(fn, header=[0], index_col=[0])
    pp = pp.replace(TRANS)
    print(pp.columns)
    pp["capacity"] = pp["capacity_net"]
    pp["costs_total"] = pp.costs_limit.multiply(pp.efficiency)

    print(pp["costs_total"])
    pp.sort_values(["costs_total", "capacity"], inplace=True)
    pp["capacity_cum"] = pp.capacity.cumsum().div(1000)

    return pp


def get_merit_order_reegis(year=2018):
    fn = os.path.join(
        cfg.get("paths", "analyses"), "data", "merit_order_reegis_base.csv"
    )
    if not os.path.isfile(fn):
        get_reegis_pp_for_merit_order("de01", year)
    pp = pd.read_csv(fn, header=[0], index_col=[0])
    ewi = download_ewi_data()
    ewi_table = pd.DataFrame(index=ewi.fuel_costs.index)
    for table in [
        "fuel_costs",
        "transport_costs",
        "other_var_costs",
        "downtime",
        "emission",
    ]:
        ewi_table[table] = getattr(ewi, table).value
    pp = pp.merge(ewi_table, left_on="fuel", right_index=True)
    pp = pp.loc[pp.fillna(0).capacity != 0]
    pp = pp.loc[pp.capacity >= 100]
    pp["capacity"] = pp.capacity.multiply(1-pp.downtime.div(100))
    pp["costs_total"] = (
        pp.fuel_costs + pp.transport_costs + pp.emission * float(ewi.co2_price["value"])).div(pp.efficiency) + pp.other_var_costs
    print(pp["costs_total"])
    pp.sort_values(["costs_total", "capacity"], inplace=True)
    pp["capacity_cum"] = pp.capacity.cumsum().div(1000)
    return pp


def get_reegis_pp_for_merit_order(name, year, aggregated=None, zero=False):
    """pass"""
    filename = os.path.join(
        cfg.get("paths", "analyses"), "data", "deflex_pp.hdf"
    )
    get_merit_order_ewi()
    if aggregated is None:
        aggregated = ["Solar", "Wind", "Bioenergy", "Hydro", "Geothermal"]
    regions = geometries.deflex_regions("de01")
    pp = dp.get_deflex_pp_by_year(regions, year, name, True, filename=filename)
    pp.drop(
        [
            "chp",
            "com_month",
            "com_year",
            "comment",
            "decom_month",
            "decom_year",
            "efficiency",
            "energy_source_level_1",
            "energy_source_level_3",
            "geometry",
            "technology",
            "thermal_capacity",
            "de01",
            "federal_states",
        ],
        axis=1,
        inplace=True,
    )
    pp["count"] = 1
    pp_agg = (
        pp.groupby("energy_source_level_2").sum().loc[aggregated].reset_index()
    )
    pp_agg.index = [x + pp.index[-1] + 1 for x in range(len(pp_agg))]
    pp = pp.loc[~pp.energy_source_level_2.isin(aggregated)]
    if zero is True:
        pp = pd.concat([pp, pp_agg], sort=False)
    pp["efficiency"] = pp.capacity.div(pp.capacity_in)
    pp.drop(["capacity_in"], axis=1, inplace=True)
    pp.rename({"energy_source_level_2": "fuel"}, inplace=True, axis=1)
    pp = pp.loc[~pp.fuel.isin(["Storage"])]
    pp.loc[
        pp.fuel == "unknown from conventional", "fuel"
    ] = "Other fossil fuels"
    pp.loc[pp.fuel == "Other fuels", "fuel"] = "Other fossil fuels"
    pp["fuel"] = pp.fuel.str.lower()
    fn = os.path.join(
        cfg.get("paths", "analyses"), "data", "merit_order_reegis_base.csv"
    )
    pp.to_csv(fn)


def plot_merit_order(pp, ax):
    cdict = {
        "nuclear": "#DDF45B",
        "hard coal": "#141115",
        "lignite": "#8D6346",
        "natural gas": "#4C2B36",
        "oil": "#C1A5A9",
        "bioenergy": "#163e16",
        "hydro": "#14142c",
        "solar": "#ffde32",
        "wind": "#335a8a",
        "other fossil fuels": "#312473",
        "waste": "#547969",
        "geothermal": "#f32eb7",
    }
    print(pp.fuel.unique())

    for src in pp.fuel.unique():
        pp[src] = pp.costs_total
        pp.loc[pp.fuel != src, src] = np.nan
        pp[src].fillna(method="bfill", limit=1, inplace=True)
        ax.fill_between(
            pp["capacity_cum"], pp[src], step="pre", color=cdict[src]
        )
    pp.set_index("capacity_cum")[pp.fuel.unique()].plot(ax=ax, alpha=0)
    # pp.to_csv("/home/uwe/probe2.csv")
    # ax.xlabel("Kummulierte Leistung [GW]")
    # ax.ylabel("Brennstoffkosten [EUR/MWh]")
    # ax.ylim(0)
    # ax.xlim(0, pp["capacity_cum"].max())
    ax.legend(loc=2)
    for leg in ax.get_legend().legendHandles:
        leg.set_color(cdict[leg.get_label()])
        leg.set_linewidth(4.0)
        leg.set_alpha(1)


if __name__ == "__main__":
    f, ax_ar = plt.subplots(2, 2, figsize=(15, 10))
    print(download_ewi_data())
    my_pp = get_merit_order_reegis()
    plot_merit_order(my_pp, ax_ar[0, 0])
    plt.show()
    exit(0)
    # my_pp = get_merit_order_ewi_raw()
    # plot_merit_order(my_pp)
    # plt.title("EWI raw")
    # plt.savefig("/home/uwe/mo_ewi_raw.png")
    # plt.show()
    # my_pp = get_merit_order_ewi()
    # plot_merit_order(my_pp)
    # plt.title("EWI")
    # plt.savefig("/home/uwe/mo_ewi.png")
    # plt.show()
    my_pp = get_reegis_pp_for_merit_order("de01", 2018)
    plot_merit_order(my_pp, ax_ar[0, 0])
    my_pp = get_merit_order_ewi_raw()
    plot_merit_order(my_pp, ax_ar[0, 1])
    plt.ylim(0)
    plt.xlim(0)
    plt.ylabel("Brennstoffkosten [EUR/MWh]")
    plt.xlabel("Kummulierte Leistung [GW]")
    plt.savefig("/home/uwe/mo_reegis.png")
    plt.show()
