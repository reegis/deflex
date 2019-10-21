# -*- coding: utf-8 -*-

"""Main script.

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


# Python libraries
import os
import logging
from datetime import datetime
import time
import traceback

# oemof packages
from oemof.tools import logger

# internal modules
import reegis.config as cfg
import deflex


def stopwatch():
    if not hasattr(stopwatch, 'start'):
        stopwatch.start = datetime.now()
    return str(datetime.now() - stopwatch.start)[:-7]


def main(year, plot_graph=False):
    stopwatch()
    name = '{0}_{1}_{2}'.format('deflex', year, cfg.get('init', 'map'))
    meta = {'year': year,
            'model_base': 'deflex',
            'map': cfg.get('init', 'map'),
            'solver': cfg.get('general', 'solver'),
            'start_time': datetime.now()}
    sc = deflex.Scenario(name=name, year=2014, meta=meta)
    path = os.path.join(cfg.get('paths', 'scenario'), 'deflex', str(year))
    csv_dir = name + '_csv'
    csv_path = os.path.join(path, csv_dir)
    excel_path = os.path.join(path, name + '.xls')

    if not os.path.isdir(csv_path):
        fn = deflex.basic_scenario.create_basic_scenario(year, path=path,
                                                         csv_dir=csv_dir)
        if csv_path != fn.csv:
            msg = ("\n{0}\n{1}\nThe wrong path is checked. This will recreate "
                   "the scenario every time!".format(csv_path, fn.csv))
            logging.error(msg)
    logging.info("Read scenario from csv collection: {0}".format(stopwatch()))
    # sc.load_csv(csv_path)
    sc.load_excel(excel_path)

    logging.info("Add nodes to the EnergySystem: {0}".format(stopwatch()))
    sc.table2es()

    # Save energySystem to '.graphml' file if plot_graph is True
    if plot_graph:
        sc.plot_nodes(filename=os.path.join(path, name),
                      remove_nodes_with_substrings=['bus_cs'])

    logging.info("Create the concrete model: {0}".format(stopwatch()))
    sc.create_model()

    logging.info("Solve the optimisation model: {0}".format(stopwatch()))
    sc.solve()

    logging.info("Solved. Dump results: {0}".format(stopwatch()))
    res_path = os.path.join(path, 'results_{0}'.format(
        cfg.get('general', 'solver')))
    os.makedirs(res_path, exist_ok=True)
    out_file = os.path.join(res_path, name + '.esys')
    logging.info("Dump file to {0}".format(out_file))
    sc.meta['end_time'] = datetime.now()
    sc.dump_es(out_file)

    logging.info("All done. deflex finished without errors: {0}".format(
        stopwatch()))


if __name__ == "__main__":
    logger.define_logging(screen_level=logging.DEBUG)
    for y in [2014, 2013, 2012]:
        for my_rmap in ['de02', 'de17', 'de21']:
            cfg.tmp_set('init', 'map', my_rmap)
            main(y, plot_graph=True)
            exit(0)
            try:
                main(y)
            except Exception as e:
                logging.error(traceback.format_exc())
                time.sleep(0.5)
                logging.error(e)
                time.sleep(0.5)
