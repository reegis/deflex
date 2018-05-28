# -*- coding: utf-8 -*-

"""Main script.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os
import logging
from datetime import datetime
import time
import traceback

# oemof packages
from oemof.tools import logger

# internal modules
import reegis_tools.config as cfg
import deflex


def stopwatch():
    if not hasattr(stopwatch, 'start'):
        stopwatch.start = datetime.now()
    return str(datetime.now() - stopwatch.start)[:-7]


def main(year):
    stopwatch()
    name = 'basic_{0}'.format(cfg.get('init', 'map'))
    sc = deflex.Scenario(name=name, year=2014)
    scenario_path = os.path.join(cfg.get('paths', 'scenario'), str(year))
    csv_path = os.path.join(scenario_path, 'csv', name)

    if not os.path.isdir(csv_path):
        deflex.basic_scenario.create_basic_scenario(year)

    logging.info("Read scenario from csv collection: {0}".format(stopwatch()))
    sc.load_csv(csv_path)

    logging.info("Add nodes to the EnergySystem: {0}".format(stopwatch()))
    sc.add_nodes2solph()

    # Save energySystem to '.graphml' file.
    fn = 'deflex_{0}_{1}'.format(year, cfg.get('init', 'map'))
    sc.plot_nodes(filename=os.path.join(scenario_path, fn),
                  remove_nodes_with_substrings=['bus_cs'])

    logging.info("Create the concrete model: {0}".format(stopwatch()))
    sc.create_model()

    logging.info("Solve the optimisation model: {0}".format(stopwatch()))
    sc.solve()

    logging.info("Solved. Dump results: {0}".format(stopwatch()))
    out_file = os.path.join(scenario_path, 'results', fn + '.esys')
    logging.info("Dump file to {0}".format(out_file))
    sc.dump_es(out_file)

    logging.info("All done. deflex finished without errors: {0}".format(
        stopwatch()))


if __name__ == "__main__":
    logger.define_logging()
    for y in [2014]:
        for my_rmap in ['de21', 'de22']:
            cfg.tmp_set('init', 'map', my_rmap)
            deflex.basic_scenario.create_basic_scenario(y, rmap=my_rmap)
            try:
                main(y)
            except Exception as e:
                logging.error(traceback.format_exc())
                time.sleep(0.5)
                logging.error(e)
                time.sleep(0.5)
