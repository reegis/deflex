# -*- coding: utf-8 -*-

"""
A short way to model different scenarios. It is possible to model all scenarios
in a row, which is recommended for large models and/or small computers. It is
also possible to model the scenarios (partly) in parallel. Keep in mind that
the limit could be the available memory.

SPDX-FileCopyrightText: 2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

from oemof.tools import logger

import deflex.tools.files
from deflex import main

# !!! ADAPT THE PATH !!!
path = "your/path"

# Set logger
logger.define_logging()

# Fetch files
# Searching for xlsx-files and directories ending with "_csv". Make sure you do
# not have other files xlsx-files in the given path. You can exclude a specific
# pattern if you have input and e.g. result files in the given path and the
# string "result" is part of the name of the result files.
files = deflex.tools.files.search_input_scenarios(
    path, xlsx=True, csv=True, exclude="result"
)

# Modelling scenarios in a row
for file in files:
    main.model_scenario(file)

# Modelling scenarios in parallel
# main.model_multi_scenarios(files, cpu_fraction=0.5)