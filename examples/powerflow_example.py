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


# url = (
#     "https://files.de-1.osf.io/v1/resources/a5xrj/providers/osfstorage"
#     "/605c566be12b600065aa635f?action=download&direct&version=1"
# )
#
# # !!! ADAPT THE PATH !!!
# path = "/home/uwe/"
#
# # Set logger
# logger.define_logging()
#
# # # Download and unzip scenarios (if zip-file does not exist)
# # os.makedirs(path, exist_ok=True)
# # fn = os.path.join(path, "deflex_scenario_examples_v03.zip")
# # if not os.path.isfile(fn):
# #     tools.download(fn, url)
# # with ZipFile(fn, "r") as zip_ref:
# #     zip_ref.extractall(path)
# # logging.info("All v0.3.x scenarios examples extracted to %s.", path)
#
# # Look in your folder above. You should see some scenario files. The csv and
# # the xlsx scenarios are the same. The csv-directories cen be read faster by
# # the computer but the xlsx-files are easier to read for humans because all
# # sheets are in one file.
#
# # NOTE: Large models will need up to 24 GB of RAM, so start with small models
# # and increase the size step by step. You can also use large models with less
# # time steps but you have to adapt the annual limits.
#
# # Now choose one example. We will start with a small one:
# file = "deflex_2014_de02_no-heat_no-co2-costs_no-var-costs_3_month_test.xlsx"
# fn = os.path.join(path, file)
#
#
# # *** Long version ***
#
# # Create a scenario object
# sc = scenario.DeflexScenario()
#
# # Read the input data. Use the right method (csv/xlsx) for your file type.
# # sc.read_csv(fn)
# sc.read_xlsx(fn)
#
# # Create the LP model and solve it.
# sc.compute()
#
# # Dump the results to a sub-dir named "results_cbc".
# # dump_file = file.replace("_csv", ".dflx")
# dump_file = file.replace(".xlsx", ".dflx")
# dump_path = os.path.join(path, dump_file)
# sc.dump(dump_path)

results = tools.restore_results(
    "/home/uwe/deflex_2014_de21_no-heat_transmission.dflx"
)

flowkeys = [f for f in results["main"].keys() if f[1] is not None]

powerlinekeys = [
    k
    for k in flowkeys
    if k[1].label.cat == "line"
    and k[1].label.subtag not in ["DE21", "DE20", "DE19"]
    and k[1].label.region not in ["DE21", "DE20", "DE19"]
]

# df = pd.DataFrame(index=pd.MultiIndex(levels=[[], []], codes=[[], []]))
dc = {}
for k in powerlinekeys:
    d1 = (k[1].label.subtag, k[1].label.region)
    d2 = (k[1].label.region, k[1].label.subtag)
    if d1 not in dc and d2 not in dc:
        print(k[1].label.subtag, k[1].label.region)
        backflowkey = [
            b
            for b in flowkeys
            if b[1].label.subtag == k[1].label.region
            and b[1].label.region == k[1].label.subtag
        ]
        outflow = [o for o in flowkeys if o[0] == k[1]][0]
        dc[d1] = (
            results["main"][k]["sequences"]["flow"]
            + results["main"][backflowkey[0]]["sequences"]["flow"]
        )
        temp = dc[d1] / results["param"][outflow]["scalars"]["nominal_value"]
        print(len(temp[temp > 0.9]) / 87.60)
df = pd.DataFrame(dc)
print(df.sum())
exit(0)
