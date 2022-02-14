# -*- coding: utf-8 -*-

"""
Plotting the Market Clearing Price (MCP) from the model and the day ahead price
from the Entso-e transparency platform (downloaded from OPSD[1]).

Change the `FORCE_COMPUTING` parameter to True to compute the scenario on your
computer. This enables you to change the input data, compute the model and see
how the plot changes (e.g. add a CO2 price).

[1] OPSD: https://open-power-system-data.org

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import pytz
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator

import deflex as dflx

OPSD_URL = (
    "https://data.open-power-system-data.org/index.php?package="
    "time_series&version=2019-06-05&action=customDownload&resource=3"
    "&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bfrom%5D="
    "2005-01-01&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bto%5D"
    "=2019-05-01&filter%5BRegion%5D%5B%5D=DE&filter%5BVariable%5D%5B"
    "%5D=price_day_ahead&downloadCSV=Download+CSV"
)

BASIC_PATH = os.path.join(os.path.expanduser("~"), "deflex", "figures")
INPUT_FILE = "deflex_2014_de02_3_month_test.xlsx"
FORCE_COMPUTING = False  # Use True to compute the model (small model, fast)


def get_price_from_opsd(path):
    """Get day ahead prices from opsd time series."""
    fn = os.path.join(path, "opsd_day_ahead_prices.csv")
    dflx.download(fn, OPSD_URL)

    de_ts = pd.read_csv(
        fn,
        index_col="utc_timestamp",
        parse_dates=True,
        date_parser=lambda col: pd.to_datetime(col, utc=True),
    )
    de_ts.index = de_ts.index.tz_convert("Europe/Berlin")
    de_ts.index.rename("cet_timestamp", inplace=True)
    berlin = pytz.timezone("Europe/Berlin")
    start_date = berlin.localize(datetime(2014, 1, 1, 0, 0, 0))
    end_date = berlin.localize(datetime(2014, 12, 31, 23, 0, 0))
    return de_ts.loc[start_date:end_date, "DE_price_day_ahead"]


dflx.use_logging()
plt.rcParams.update({"font.size": 18})
os.makedirs(BASIC_PATH, exist_ok=True)
dflx.fetch_published_figures_example_files(BASIC_PATH)

# Define the filenames
files = {"input": INPUT_FILE}
files["dump"] = files["input"].replace(".xlsx", ".dflx")
files["out"] = files["input"].replace(".xlsx", "_results.xlsx")
files["plot"] = files["input"].replace(".xlsx", ".png")
files = {k: os.path.join(BASIC_PATH, v) for k, v in files.items()}

# Compute the model if the dump file does not exist or computing is forced
if not os.path.isfile(files["dump"]) or FORCE_COMPUTING:
    dflx.model_scenario(files["input"], "xlsx", files["dump"])

# Restore dumped file to create the plot
results = dflx.restore_results(files["dump"])

kv = dflx.calculate_key_values(results)

# Download Entsoe day ahead prices from OPSD
opsd = get_price_from_opsd(BASIC_PATH)

winter = opsd[0:744]
spring = opsd[2159:2879]
summer = opsd[4343:5087]
opsd = pd.concat([winter, spring, summer], axis=0)

kv.set_index(opsd.index, inplace=True)

# Add opsd day ahead prices to table
mcp = pd.DataFrame()
mcp["Entsoe"] = opsd
mcp["de02"] = kv["marginal costs"]


dual = dflx.fetch_dual_results(results)
dual.set_index(opsd.index, inplace=True)
electricity_bus = [
    b
    for b in dual.columns
    if b.label.cat == "electricity" and b.label.region == "DE01"
][0]
mcp["duals"] = dual[electricity_bus]

mcp.tz_localize(None).to_excel("/home/uwe/mcp_neu.xlsx")
mcp = pd.read_excel("/home/uwe/mcp_neu.xlsx", parse_dates=True, index_col=0)

f, ax = plt.subplots(3, 1, sharey=True, figsize=(15, 5))

year = str(mcp.index[0].year)
iv = [("8.1.", "25.1."), ("8.4.", "25.4."), ("8.7.", "25.7.")]

# Create subplots for each date interval
n = 0
for interval in iv:
    start = datetime.strptime(interval[0] + year, "%d.%m.%Y")
    start += timedelta(hours=12)
    end = datetime.strptime(interval[1] + year, "%d.%m.%Y")
    end += timedelta(hours=12)
    mcp[start:end].plot(ax=ax[n], legend=False, x_compat=True)
    ax[n].set_xlim(start, end)
    ax[n].xaxis.set_major_locator(HourLocator(interval=72))
    ax[n].xaxis.set_major_formatter(DateFormatter("%b-%d %H:%M"))
    ax[n].tick_params(axis="x", rotation=0)
    [
        label.set_horizontalalignment("center")
        for label in ax[n].xaxis.get_ticklabels()
    ]
    ax[n].set_ylabel("[EUR/MWh]")
    ax[n].set_xlabel("")
    n += 1

# Create legend
sc = list(mcp.columns)
ax[2].legend(
    sc,
    bbox_to_anchor=(1.156, 1),
    loc="upper right",
)
# Adjust plot
plt.subplots_adjust(right=0.88, left=0.06, bottom=0.09, top=0.98, hspace=0.3)

if not os.path.isfile(files["out"]) or FORCE_COMPUTING:
    dflx.dict2file(dflx.get_all_results(results), files["out"])

plt.savefig(files["plot"])
plt.show()
