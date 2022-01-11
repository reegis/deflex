# -*- coding: utf-8 -*-

"""
Example, which shows two different ways of solving a deflex scenario.

SPDX-FileCopyrightText: 2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

from oemof.tools import logger

from deflex import main

# !!! ADAPT THE PATH !!!
path = "/home/uwe/deflex_new/"

# Set logger
logger.define_logging()

# Fetch files
files = main.fetch_scenarios_from_dir(path, xlsx=True, csv=False)

for file in files:
    main.model_scenario(file, file_type="xlsx")
