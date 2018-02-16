# -*- coding: utf-8 -*-

import pandas as pd
import os
import logging
import de21.basic_scenario


class Scenario:
    def __init__(self, year):
        self.table_collection = None
        self.year = year
        self.ignore_errors = False
        self.round_values = 0
        self.filename = '/home/uwe/PythonExport.xlsx'
        self.path = None

    def create_basic_scenario(self, year=None, round_values=None):
        if year is not None:
            self.year = year
        if round_values is not None:
            self.round_values = round_values
        self.table_collection = de21.basic_scenario.create_scenario(
            self.year, self.round_values)

    def to_excel(self, filename=None):
        if filename is not None:
            self.filename = filename
        writer = pd.ExcelWriter(self.filename)
        for name, df in self.table_collection.items():
            df.to_excel(writer, name)
        writer.save()

    def to_csv(self, path):
        if path is not None:
            self.path = path
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        logging.info("Dump scenario as csv-collection to {0}".format(
            self.path))
        for name, df in self.table_collection.items():
            name = name.replace(' ', '_') + '.csv'
            filename = os.path.join(self.path, name)
            df.to_csv(filename)
