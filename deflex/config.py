# -*- coding: utf-8 -*-

"""
Reegis config reader.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

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
