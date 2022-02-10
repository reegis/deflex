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
path = os.path.join(os.path.expanduser("~"), ".deflex", "my_scenarios")

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

# Modelling scenarios in a row
for file in files:
    dflx.model_scenario(file)

# Modelling scenarios in parallel
# model_multi_scenarios(files, cpu_fraction=0.5)
