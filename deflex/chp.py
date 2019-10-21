# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


# Internal libraries
import reegis.config as cfg
import reegis.energy_balance
import reegis.powerplants


def reshape_conversion_balance(year, geo):
    # get conversion balance for the federal states
    cb = reegis.energy_balance.get_conversion_balance_by_region(year, geo)
    cb.rename(columns={'re': cfg.get('chp', 'renewable_source')}, inplace=True)
    return cb


def get_chp_share_and_efficiency(year, geo):
    conversion_blnc = reshape_conversion_balance(year, geo)
    return reegis.powerplants.calculate_chp_share_and_efficiency(
        conversion_blnc)


if __name__ == "__main__":
    pass
