import datetime
import os

import oemof_visio
import pandas as pd
from matplotlib import pyplot as plt
from oemof.tools import logger

from deflex import postprocessing, scenario, tools

# if the model is solved and dump you can skip the solver to show the plots
# faster.
skip_computing = True

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

fontsize = 18

f, ax = plt.subplots(2, 1, sharex=True, figsize=(15, 6))
plt.rcParams.update({"font.size": fontsize})

basic_path = "/home/uwe/"
in_file = "deflex_2014_de02_no-heat_no-co2-costs_no-var-costs_august_test.xlsx"
dump_file = in_file.replace(".xlsx", ".dflx")

logger.define_logging()

if skip_computing is False:
    # create a scenario object
    sc = scenario.DeflexScenario()

    # read the input data. Use the right method (csv/xlsx) for your file type.
    sc.read_xlsx(os.path.join(basic_path, in_file))

    # create the LP model and solve it.
    sc.compute()

    # dump the results to file
    sc.dump(os.path.join(basic_path, dump_file))

# restore the results from file
my_results = tools.restore_results(os.path.join(basic_path, dump_file))

# fetch commodity parameter
commodity = postprocessing.fetch_parameter_of_commodity_sources(my_results)
commodity.index = commodity.index.droplevel(1)

# fetch power plant in an out flows (fix datetime index)
pp = postprocessing.get_converter_balance(my_results, cat="power plant")
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
key_values = postprocessing.calculate_key_values(my_results)
key_values.set_index(
    pd.to_datetime(key_values.index.values) + pd.Timedelta(hours=5088),
    inplace=True,
)

# fetch all in- and outflows of the electricity buses (fix datetime index)
ebus = postprocessing.get_combined_bus_balance(my_results, cat="electricity")
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
key_values["most expensive"] = key_values["emissions"]
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
# plt.show()
plt.savefig("/home/uwe/deflex_emission_plot.pdf")
