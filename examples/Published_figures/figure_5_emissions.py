# -*- coding: utf-8 -*-

"""
Plotting the emissions of the most expensive power plant and the average
emissions. The most expensive power plant would be expelled by an additional
capacity (e.g. PV, wind power plant). The second plot illustrates the power
plant mix, which makes it easier to understand the emission values.

Change the `FORCE_COMPUTING` parameter to True to compute the scenario on your
computer. This enables you to change the input data, compute the model and see
how the plot changes (e.g. change the specific emissions of the commodity
sources).

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import datetime
import os

import oemof_visio
import pandas as pd
from matplotlib import pyplot as plt
from oemof.tools import logger

import deflex as dflx

EXAMPLES_URL = (
    "https://files.de-1.osf.io/v1/resources/9krgp/providers/osfstorage"
    "/61def8c4bc925b00fed4b1d7?action=download&direct&version=1"
)

BASIC_PATH = os.path.join(os.path.expanduser("~"), "deflex", "figures")
INPUT_FILE = "deflex_2014_de02_august_test.xlsx"
FORCE_COMPUTING = False  # Use True to compute the model (small model, fast)

# Basic parameters
plot_colors = {
    "bioenergy": "#163e16",
    "hydro": "#14142c",
    "pv": "#ffde32",
    "solar": "#ffde32",
    "wind": "#335a8a",
    "natural gas": "#555555",
    "demand": "#800060",
    "hard coal": "#000000",
    "lignite": "#6c3012",
    "other": "#312473",
    "storage": "#09516c",
    "nuclear": "#deff00",
    "renewable": "#f47c3b",
    "waste": "#547969",
}

electricity_groups = {
    "geothermal": "renewable",
    "hydro": "renewable",
    "solar": "renewable",
    "wind": "renewable",
    "bioenergy": "other",
    "oil": "other",
    "waste": "waste",
    "all": "demand",
    "phes": "storage",
    "natural gas": "natural gas",
}


logger.define_logging()
os.makedirs(BASIC_PATH, exist_ok=True)
dflx.fetch_published_figures_example_files(BASIC_PATH)

files = {"input": INPUT_FILE}

files["dump"] = files["input"].replace(".xlsx", ".dflx")
files["out"] = files["input"].replace(".xlsx", "_results.xlsx")
files["plot"] = files["input"].replace(".xlsx", ".png")

files = {k: os.path.join(BASIC_PATH, v) for k, v in files.items()}

# Define plots
fontsize = 18
f, ax = plt.subplots(2, 1, sharex=True, figsize=(15, 6))
plt.rcParams.update({"font.size": fontsize})

logger.define_logging()

if not os.path.isfile(files["dump"]) or FORCE_COMPUTING:
    dflx.scripts.model_scenario(files["input"], "xlsx", files["dump"])

# restore the results from file
my_results = dflx.restore_results(files["dump"])

# fetch commodity parameter
commodity = dflx.fetch_attributes_of_commodity_sources(my_results)
commodity.index = commodity.index.droplevel(1)

# fetch power plant in an out flows (fix datetime index)
pp = dflx.get_converter_balance(my_results, cat="power plant")
pp.set_index(
    pd.to_datetime(pp.index.values) + pd.Timedelta(hours=5088), inplace=True
)

# calculate total emissions of all power plants
total_emissions = (
    pp["in"]
    .groupby(level=2, axis=1)
    .sum()
    .mul(commodity["emission"])
    .sum(axis=1)
)

# calculate total electricity production of all power plants
total_electricity_converter = pp["out"].sum(axis=1)

# fetch emissions of most expensive power plant (fix datetime index)
key_values = dflx.calculate_key_values(my_results)
key_values.set_index(
    pd.to_datetime(key_values.index.values) + pd.Timedelta(hours=5088),
    inplace=True,
)

# fetch all in- and outflows of the electricity buses (fix datetime index)
ebus = dflx.get_combined_bus_balance(my_results, cat="electricity")
ebus.set_index(
    pd.to_datetime(ebus.index.values) + pd.Timedelta(hours=5088), inplace=True
)

# calculate average emissions
average_emissions = (
    total_emissions
    / ebus["out"]["electricity demand"][("electricity", "all", "DE01")]
)
average_emissions.name = "average"

# reshape the bus balance
ebus = ebus.groupby(level=[0, 1, 3], axis=1).sum()
ebus.drop(["line", "shortage", "excess"], axis=1, level=1, inplace=True)
ebus.columns = ebus.columns.droplevel(1)
ebus.rename(columns=electricity_groups, inplace=True)
ebus = ebus.groupby(level=[0, 1], axis=1).sum()

# define time interval for the plot
interval = ("5.8.", "26.8.")
year = str(2014)
start_year = datetime.datetime(2014, 8, 1)
start = datetime.datetime.strptime(interval[0] + year, "%d.%m.%Y")
start += datetime.timedelta(hours=12)
start = (start - start_year).days * 24
end = datetime.datetime.strptime(interval[1] + year, "%d.%m.%Y")
end += datetime.timedelta(hours=12)
end = (end - start_year).days * 24

# define order of the in- and outflows.
inorder = [
    "waste",
    "lignite",
    "bioenergy",
    "nuclear",
    "hard coal",
    "natural gas",
    "other",
    "renewable",
    "storage",
]
outorder = ["demand", "storage"]

# plot the emissions
key_values = pd.concat([key_values, average_emissions], axis=1)
key_values["most expensive"] = key_values["emission"]
ax[0] = (
    key_values[["most expensive", "average"]]
    .reset_index(drop=True)
    .loc[start:end]
    .div(1000)
    .plot(ax=ax[0], legend=True, fontsize=fontsize)
)

# plot the stacked i/o plot
ioplot = oemof_visio.plot.io_plot(
    df_in=ebus["in"].div(1000),
    df_out=ebus["out"].div(1000),
    smooth=True,
    inorder=inorder,
    outorder=outorder,
    cdict=plot_colors,
    ax=ax[1],
    line_kwa={"fontsize": fontsize},
)

# shape the plots (axis, legend)
ioplot.pop("ax")
ax[1] = oemof_visio.plot.set_datetime_ticks(
    ax[1],
    ebus.index,
    tick_distance=96,
    offset=12,
    date_format="%b-%d %H:%M",
)
ax[0].set_ylabel("Emissions [kg/kWh]", fontsize=fontsize)
ax[1].set_ylabel("Power [GW]", fontsize=fontsize)
ax[1].set_xlim(start, end)
ax[0].legend(bbox_to_anchor=(1, 1.05), loc="upper left")
ax[1].legend(bbox_to_anchor=(1, 1.4), loc="upper left", **ioplot)
plt.subplots_adjust(
    right=0.798, left=0.055, bottom=0.06, top=0.99, hspace=0.03
)

# Write out the results
if not os.path.isfile(files["out"]) or FORCE_COMPUTING:
    dflx.dict2file(dflx.get_all_results(my_results), files["out"])

# Show and save the plot
plt.savefig(files["plot"])
plt.show()
