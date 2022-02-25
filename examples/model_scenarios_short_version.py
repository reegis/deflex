# -*- coding: utf-8 -*-

"""
A short way to model different scenarios. It is possible to model all scenarios
in a row, which is recommended for large models and/or small computers. It is
also possible to model the scenarios (partly) in parallel. Keep in mind that
the limit could be the available memory.

SPDX-FileCopyrightText: 2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import os

from oemof.tools import logger

import deflex as dflx

# !!! ADAPT THE PATH !!!
path = os.path.join(os.path.expanduser("~"), "deflex", "my_scenarios")

# Download and unzip scenarios (if zip-file does not exist)
dflx.fetch_full_examples(path)

# Set logger
logger.define_logging()

# Fetch files
# Searching for xlsx-files and directories ending with "_csv". Make sure you do
# not have other files xlsx-files in the given path. You can exclude a specific
# pattern if you have input and e.g. result files in the given path and the
# string "result" is part of the name of the result files.
files = dflx.search_input_scenarios(
    path, xlsx=True, csv=True, exclude="result"
)

# Modelling all scenarios in a row (this will take several hours)
# The `files` variable is a list of filenames. This list can be filtered to
# reduce the number of scenarios or to get just one scenario.
for file in files:
    dflx.model_scenario(file)

# Modelling all scenarios in parallel
# Note: In most case the limit is the available RAM.
# model_multi_scenarios(files, cpu_fraction=0.5)
