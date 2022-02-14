# -*- coding: utf-8 -*-

"""
Example, which shows two different ways of solving a deflex scenario.

SPDX-FileCopyrightText: 2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""


import os

from oemof.tools import logger

import deflex as dflx

url = (
    "https://files.de-1.osf.io/v1/resources/a5xrj/providers/osfstorage"
    "/605c566be12b600065aa635f?action=download&direct&version=1"
)

# !!! ADAPT THE PATH !!!
path = "/home/uwe/deflex_temp_test/"

# Set logger
logger.define_logging()

# Download and unzip scenarios (if zip-file does not exist)
dflx.download_full_examples(path)

# Look in your folder above. You should see some scenario files. The csv and
# the xlsx scenarios are the same. The csv-directories can be read faster by
# the computer but the xlsx-files are easier to read for humans because all
# sheets are in one file.

# NOTE: Large models will need up to 24 GB of RAM and up to one hour, so start
# with small models and increase the size step by step. You can also use large
# models with less time steps but you have to adapt the annual limits.

# Now choose one example. We will start with a small one:
file = "scenarios/de02_no-heat.xlsx"
fn = os.path.join(path, file)

# *** Long version ***

# Create a scenario object
sc = dflx.DeflexScenario()

# Read the input data. Use the right method (csv/xlsx) for your file type.
# sc.read_csv(fn)
sc.read_xlsx(fn)

# It can be useful to write the xlsx using pandas. This version is very
# should be used to share it with others because it is faster to read than
# a manual created xlsx-file.
sc.to_xlsx(fn)

# Create the LP model and solve it.
sc.compute()

# Dump the results to a sub-dir named "results_cbc".
# dump_file = file.replace("_csv", ".dflx")
dump_file = file.replace(".xlsx", ".dflx")
dump_path = os.path.join(path, "results_cbc", dump_file)
sc.dump(dump_path)
