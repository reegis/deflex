# -*- coding: utf-8 -*-

"""
Reegis config reader.

Based on Steffen (https://github.com/steffenGit)
Copyright (c) 2016-2018 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


# Python libraries
import os
from reegis.config import *


_loaded = False
if not _loaded:
    init(paths=[os.path.dirname(__file__)])
    _loaded = True
