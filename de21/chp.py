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
import reegis_tools.config as cfg
import reegis_tools.energy_balance

import de21.inhabitants


def reshape_conversion_balance(year):
    # get conversion balance for the federal states
    eb = reegis_tools.energy_balance.get_conversion_balance(year)

    # create empty DataFrame to take the conversion balance for the regions
    my_index = pd.MultiIndex(levels=[[], [], []], labels=[[], [], []])
    eb21 = pd.DataFrame(index=my_index, columns=eb.columns)

    # Use the number of inhabitants to reshape the balance to the new regions
    logging.info("Fetching inhabitants table.")
    inhabitants = de21.inhabitants.get_ew_by_de21_subregions(year)
    inhabitants = inhabitants.replace({'state': cfg.get_dict('STATES')})

    inhabitants_by_state = inhabitants.groupby('state').sum()

    # Calculate the share of inhabitants of a state that is within a specific
    # model region.
    logging.info(
        "Rearrange state table of the conversion balance to the de21 regions")
    for subregion in inhabitants.index:
        inhabitants.loc[subregion, 'share_state'] = float(
            inhabitants.loc[subregion, 'ew'] /
            inhabitants_by_state.loc[inhabitants.loc[subregion, 'state']])

    # Loop over the de21 regions
    for de21_region in sorted(inhabitants.region.unique()):
        # Get all states that intersects with the current de21-region
        states = inhabitants.loc[inhabitants.region == de21_region].state

        # Sum up the fraction of each state-table to get the new region table
        for idx in eb.loc[states[0]].index:
            eb21.loc[de21_region, idx[0], idx[1]] = 0
            for state in states:
                share = inhabitants.loc[
                    (inhabitants['region'] == de21_region) &
                    (inhabitants['state'] == state)]['share_state']
                eb21.loc[de21_region, idx[0], idx[1]] += (
                    eb.loc[state, idx[0], idx[1]] * float(share))
    eb21.rename(columns={'re': cfg.get('chp', 'renewable_source')},
                inplace=True)
    return eb21


def calculate_efficiency(eb):
    row_chp = 'Heizkraftwerke der allgemeinen Versorgung (nur KWK)'
    row_hp = 'Heizwerke'
    row_total = 'Umwandlungsausstoß insgesamt'

    regions = ['DE{num:02d}'.format(num=n+1) for n in range(18)]
    eta = {}
    rows = ['Heizkraftwerke der allgemeinen Versorgung (nur KWK)',
            'Heizwerke']

    for region in regions:
        eta[region] = {}
        in_chp = eb.loc[region, 'input', row_chp]
        in_hp = eb.loc[region, 'input', row_hp]
        elec_chp = eb.loc[(region, 'output', row_chp), 'electricity']
        heat_chp = eb.loc[(region, 'output', row_chp),
                          'district heating']
        heat_hp = eb.loc[(region, 'output', row_hp),
                         'district heating']
        heat_total = eb.loc[(region, 'output', row_total),
                            'district heating']
        end_total_heat = eb.loc[(region, 'usage', 'Endenergieverbrauch'),
                                'district heating']
        eta[region]['sys_heat'] = end_total_heat / heat_total

        eta[region]['hp'] = float(heat_hp / in_hp.total)
        eta[region]['heat_chp'] = heat_chp / in_chp.total
        eta[region]['elec_chp'] = elec_chp / in_chp.total

        eta[region]['fuel_share'] = eb.loc[region, 'input', rows].div(
            eb.loc[region, 'input', rows].total.sum(), axis=0)

    return eta


def get_efficiency(year):
    return calculate_efficiency(reshape_conversion_balance(year).loc[year])


if __name__ == "__main__":
    logger.define_logging()
    import pprint as pp
    pp.pprint(get_efficiency(2014))
