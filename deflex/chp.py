# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import logging

# External libraries
import pandas as pd

# oemof libraries
import oemof.tools.logger as logger

# Internal libraries
import reegis.config as cfg
import reegis.energy_balance
import reegis.powerplants

import deflex.inhabitants


def reshape_conversion_balance(year):
    # get conversion balance for the federal states
    eb = reegis.energy_balance.get_conversion_balance(year)

    # create empty DataFrame to take the conversion balance for the regions
    my_index = pd.MultiIndex(levels=[[], [], []], labels=[[], [], []])
    eb21 = pd.DataFrame(index=my_index, columns=eb.columns)

    # Use the number of inhabitants to reshape the balance to the new regions
    logging.info("Fetching inhabitants table.")
    inhabitants = deflex.inhabitants.get_ew_by_deflex_subregions(year)
    inhabitants_by_state = inhabitants.groupby('state').sum()

    # Calculate the share of inhabitants of a state that is within a specific
    # model region.
    logging.info(
        "Rearrange state table of the conversion balance to the deflex"
        "regions")
    for subregion in inhabitants.index:
        inhabitants.loc[subregion, 'share_state'] = float(
            inhabitants.loc[subregion, 'ew'] /
            inhabitants_by_state.loc[inhabitants.loc[subregion, 'state']])

    # Loop over the deflex regions
    for deflex_region in sorted(inhabitants.region.unique()):
        # Get all states that intersects with the current deflex-region
        states = inhabitants.loc[inhabitants.region == deflex_region].state

        # Sum up the fraction of each state-table to get the new region table
        for idx in eb.loc[states[0]].index:
            eb21.loc[deflex_region, idx[0], idx[1]] = 0
            for state in states:
                share = inhabitants.loc[
                    (inhabitants['region'] == deflex_region) &
                    (inhabitants['state'] == state)]['share_state']
                eb21.loc[deflex_region, idx[0], idx[1]] += (
                    eb.loc[state, idx[0], idx[1]] * float(share))
    eb21.rename(columns={'re': cfg.get('chp', 'renewable_source')},
                inplace=True)
    return eb21


def get_chp_share_and_efficiency(year):
    conversion_blnc = reshape_conversion_balance(year)
    return reegis.powerplants.calculate_chp_share_and_efficiency(
        conversion_blnc)


if __name__ == "__main__":
    logger.define_logging()
    import pprint as pp
    pp.pprint(get_chp_share_and_efficiency(2014))
    # pp.pprint(reegis.powerplants.get_chp_share_and_efficiency_states(
    #     2014)['BE'])
