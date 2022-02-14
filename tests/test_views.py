from oemof import solph

from deflex import fetch_test_files, reshape_bus_view, restore_results


class TestCycles:
    @classmethod
    def setup_class(cls):
        fn = fetch_test_files("de02_heat.dflx")
        print(fn)
        results1 = restore_results(fn)
        results2 = restore_results(fn)
        buses1 = list(
            set(
                [
                    flow[0]
                    for flow in results1["main"].keys()
                    if isinstance(flow[0], solph.Bus)
                    and flow[0].label.cat == "electricity"
                ]
            )
        )
        buses2 = list(
            set(
                [
                    flow[0]
                    for flow in results2["main"].keys()
                    if isinstance(flow[0], solph.Bus)
                    and flow[0].label.cat == "electricity"
                ]
            )
        )
        agg = [
            ("cat", "power plant", "tag", "all"),
            ("cat", "chp plant", "tag", "all"),
            ("cat", "line", "subtag", "all"),
        ]
        df_agg = reshape_bus_view(results1, buses1, aggregate=agg)
        df = reshape_bus_view(results2, buses2)
        cls.df_agg = df_agg.groupby(level=[1, 2, 3, 4], axis=1).sum()
        cls.df = df.groupby(level=[1, 2, 3, 4], axis=1).sum()
        cls.buses = (len(buses1) + len(buses2)) / 2

    def test_number_of_buses(self):
        assert self.buses == 2

    def test_aggregated_lines(self):
        assert list(self.df_agg["in", "line", "electricity"].columns[:5]) == [
            "all"
        ]
        assert list(self.df["in", "line", "electricity"].columns[:5]) == [
            "DE01",
            "DE02",
        ]

    def test_aggregated_power_plants(self):
        assert (
            list(
                self.df_agg.loc[
                    (slice(None)),
                    ("in", "power plant", slice(None), "natural gas"),
                ]
                .sum()
                .index.get_level_values(2)
            )
            == ["all"]
        )
        assert sorted(
            list(
                self.df.loc[
                    (slice(None)),
                    ("in", "power plant", slice(None), "natural gas"),
                ]
                .sum()
                .index.get_level_values(2)
            )
        )[:4] == [
            "natural gas_018",
            "natural gas_029",
            "natural gas_03",
            "natural gas_031",
        ]

    def test_overall_sum(self):
        assert int(self.df_agg.sum().sum()) == 5160991
        assert int(self.df.sum().sum()) == 5160991
