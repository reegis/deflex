# -*- coding: utf-8 -*-

"""Analyses of deflex.

SPDX-FileCopyrightText: 2016-2020 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from deflex import powerplants as dp
from deflex import geometries
from reegis import commodity_sources


TRANS = {
        'Abfall': "waste",
        'Kernenergie': "nuclear",
        'Braunkohle': "lignite",
        'Steinkohle': "hard coal",
        'Erdgas': "natural gas",
        'GuD': "natural gas",
        'Gasturbine': "natural gas",
        'Öl': "oil",
        'Sonstige': "other fossil fuels",
    }

# Kostenannahmen von EWI
# https://www.ewi.uni-koeln.de/de/news/ewi-merit-order-tool-2019/
COSTS_CO2 = 25  # 25 €/tCO2 (aktueller Wert)
COSTS_EWI = {
    "hard coal": 11.28,
    "lignite": 3.1,
    "natural gas": 22.78,
    "oil": 33,
    "nuclear": 5.5
}

EMISSIONS_EWI = {
    "hard coal": 0.336,
    "lignite": 0.378,
    "natural gas": 0.202,
    "oil": 0.263,
    "nuclear": 0,
}


def get_merit_order_ewi():
    pp = pd.read_csv("/home/uwe/merit_order_ewi.csv", header=[0],
                     index_col=[0])
    pp = pp.replace(TRANS)
    return pp


def get_merit_order_ewi_raw():
    pp = pd.read_csv("/home/uwe/merit_order_ewi_raw.csv", header=[0],
                     index_col=[0])
    pp = pp.replace(TRANS)
    pp["capacity"] = pp["capacity_net"]
    pp["costs_total"] = pp.costs_fuel.div(pp.efficiency)
    pp.sort_values(["costs_total", "capacity"], inplace=True)
    pp["capacity_cum"] = pp.capacity.cumsum().div(1000)

    return pp


def get_merit_order_reegis(filename, name, year, aggregated=None, zero=False):
    """pass"""
    get_merit_order_ewi()
    if aggregated is None:
        aggregated = ["Solar", "Wind", "Bioenergy", "Hydro"]
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
    pp.rename({"energy_source_level_2": "source"}, inplace=True, axis=1)
    pp = pp.loc[~pp.source.isin(["Storage"])]
    pp.loc[
        pp.source == "unknown from conventional", "source"
    ] = "Other fossil fuels"
    pp.loc[pp.source == "Other fuels", "source"] = "Other fossil fuels"
    pp["source"] = pp.source.str.lower()

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
    pp = pp.merge(cs, left_on="source", right_index=True)
    pp = pp.loc[pp.fillna(0).capacity != 0]
    pp["costs_total"] = pp.costs.div(pp.efficiency)
    pp.sort_values(["costs_total", "capacity"], inplace=True)
    pp["capacity_cum"] = pp.capacity.cumsum().div(1000)
    return pp


def plot_merit_order(pp):
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
    for src in pp.source.unique():
        pp[src] = pp.costs_total
        pp.loc[pp.source != src, src] = np.nan
        pp[src].fillna(method='bfill', limit=1, inplace=True)
        plt.fill_between(pp["capacity_cum"], pp[src], step="pre",
                         color=cdict[src])
    pp.to_csv("/home/uwe/probe2.csv")
    plt.xlabel("Kummulierte Leistung [GW]")
    plt.ylabel("Brennstoffkosten [EUR/MWh]")
    plt.ylim(0)
    plt.xlim(0, pp["capacity_cum"].max())
    # plt.show()


if __name__ == "__main__":
    my_pp = get_merit_order_ewi_raw()
    plot_merit_order(my_pp)
    plt.title("EWI raw")
    plt.savefig("/home/uwe/mo_ewi_raw.png")
    plt.show()
    my_pp = get_merit_order_ewi()
    plot_merit_order(my_pp)
    plt.title("EWI")
    plt.savefig("/home/uwe/mo_ewi.png")
    plt.show()
    my_pp = get_merit_order_reegis("/home/uwe/test_temp.hdf", "de01", 2015)
    plot_merit_order(my_pp)
    plt.title("reegis")
    plt.savefig("/home/uwe/mo_reegis.png")
    plt.show()
