import os

import pandas as pd

from deflex import Cycles, fetch_test_files, restore_results


class TestCycles:
    @classmethod
    def setup_class(cls):
        result_fn = fetch_test_files("de03_fictive.dflx")
        cls.results = restore_results(result_fn)

        cycle_path = os.path.dirname(
            fetch_test_files("used_cycle_1.csv", "cycles")
        )
        files = os.listdir(cycle_path)
        cycles = []
        for file in files:
            cycles.append(
                pd.read_csv(
                    os.path.join(cycle_path, file),
                    index_col=[0],
                    parse_dates=True,
                )
            )
        cls.cycles = cycles

    def test_cycle_from_results(self, capsys):
        c = Cycles(self.results)
        print(c)
        captured = capsys.readouterr()
        expected_string = (
            "*** Cycle object of scenario: de03_fictive_test ***\n\nNumber of "
            "cycles: 9\nNumber of used cycles: 2\nNumber of critical cycles: "
            "0\n\n"
        )
        assert captured.out == expected_string

    def test_storage_filter(self):
        c = Cycles(self.results, storages=False)
        assert len(c.simple_cycles) == 7

    def test_power_line_filter(self):
        c = Cycles(self.results, lines=False)
        assert len(c.simple_cycles) == 4

    def test_suspicious_cycles(self):
        c = Cycles(self.results)
        c._cycles = self.cycles
        assert len(c.used_cycles) == 4
        assert len(c.suspicious_cycles) == 2

    def test_details_output(self, capsys):
        c = Cycles(self.results)
        c._cycles = self.cycles
        c.details()
        captured = capsys.readouterr()
        expected_string = (
            "Node 1 -> 0 ->\n"
            "Node 2 -> 0 ->\n"
            "Node 3 -> 0 ->\n"
            "Node 4 -> 46 ->\n"
            "Node 5 -> 46 ->\n"
            "Node 6 -> 0 ->\n\n"
            "************************************\n\n"
        )
        assert expected_string in captured.out
