# -*- coding: utf-8 -*-

"""
Example, which shows two different ways of solving a deflex scenario.

SPDX-FileCopyrightText: 2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""


import logging
import os
from zipfile import ZipFile
import pytz
from datetime import datetime, timedelta
import pandas as pd
from oemof.tools import logger
from matplotlib import pyplot as plt
from deflex import main, postprocessing, scenario, tools
from matplotlib.dates import DateFormatter, HourLocator

OPSD_URL = (
    "https://data.open-power-system-data.org/index.php?package="
    "time_series&version=2019-06-05&action=customDownload&resource=3"
    "&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bfrom%5D="
    "2005-01-01&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bto%5D"
    "=2019-05-01&filter%5BRegion%5D%5B%5D=DE&filter%5BVariable%5D%5B"
    "%5D=price_day_ahead&downloadCSV=Download+CSV"
)


def get_price_from_opsd(path):
    """Get day ahead prices from opsd time series."""
    fn = os.path.join(path, "opsd_day_ahead_prices.csv")
    tools.download(fn, OPSD_URL)

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


url = (
    "https://files.de-1.osf.io/v1/resources/a5xrj/providers/osfstorage"
    "/605c566be12b600065aa635f?action=download&direct&version=1"
)

# !!! ADAPT THE PATH !!!
path = "/home/uwe/"

# Set logger
logger.define_logging()

# # Download and unzip scenarios (if zip-file does not exist)
# os.makedirs(path, exist_ok=True)
# fn = os.path.join(path, "deflex_scenario_examples_v03.zip")
# if not os.path.isfile(fn):
#     tools.download(fn, url)
# with ZipFile(fn, "r") as zip_ref:
#     zip_ref.extractall(path)
# logging.info("All v0.3.x scenarios examples extracted to %s.", path)

# Look in your folder above. You should see some scenario files. The csv and
# the xlsx scenarios are the same. The csv-directories cen be read faster by
# the computer but the xlsx-files are easier to read for humans because all
# sheets are in one file.

# NOTE: Large models will need up to 24 GB of RAM, so start with small models
# and increase the size step by step. You can also use large models with less
# time steps but you have to adapt the annual limits.

# Now choose one example. We will start with a small one:
file = "deflex_2014_de02_no-heat_no-co2-costs_no-var-costs_3_month_test.xlsx"
fn = os.path.join(path, file)


# *** Long version ***

# Create a scenario object
sc = scenario.DeflexScenario()

# Read the input data. Use the right method (csv/xlsx) for your file type.
# sc.read_csv(fn)
sc.read_xlsx(fn)

# Create the LP model and solve it.
sc.compute()

# Dump the results to a sub-dir named "results_cbc".
# dump_file = file.replace("_csv", ".dflx")
dump_file = file.replace(".xlsx", ".dflx")
dump_path = os.path.join(path, dump_file)
sc.dump(dump_path)

results = tools.restore_results(dump_path)

kv = postprocessing.calculate_key_values(results)

mcp = pd.DataFrame()

# Download Entsoe day ahead prices from OPSD
opsd = get_price_from_opsd(path)

winter = opsd[0:744]
spring = opsd[2159:2879]
summer = opsd[4343:5087]
opsd = pd.concat([winter, spring, summer], axis=0)

kv.set_index(opsd.index, inplace=True)

# Add opsd day ahead prices to table
mcp["Entsoe"] = opsd
mcp["de02"] = kv["marginal costs"]

mcp.tz_localize(None).to_excel("/home/uwe/mcp_neu.xlsx")
mcp = pd.read_excel("/home/uwe/mcp_neu.xlsx", parse_dates=True, index_col=0)

f, ax = plt.subplots(3, 1, sharey=True, figsize=(15, 5))

year = str(mcp.index[0].year)
iv = [("8.1.", "25.1."), ("8.4.", "25.4."), ("8.7.", "25.7.")]

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

sc = list(mcp.columns)
ax[2].legend(
    sc, bbox_to_anchor=(1.1, 1), loc="upper right",
)

plt.subplots_adjust(right=0.90, left=0.06, bottom=0.09, top=0.98)
plt.show()
out_file = file.replace(".", "_results.")
out_path = os.path.join(path, out_file)
tools.dict2file(postprocessing.get_all_results(results), out_path)


# *** short version ***

# main.model_scenario(fn, file_type="csv")
