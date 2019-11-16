from nose.tools import eq_, assert_raises_regexp
from deflex import basic_scenario, geometries, powerplants, config as cfg


class TestScenarioPowerplantsAndCHP:
    @classmethod
    def setUpClass(cls):
        cls.regions = geometries.deflex_regions(rmap='de21')
        cls.pp = basic_scenario.scenario_powerplants(
            dict(), cls.regions, 2014, 'de21', 1)

    def test_01_deflex_power_plants_by_year(self):
        pp = powerplants.get_deflex_pp_by_year(self.regions, 2014, 'de21',
                                               overwrite_capacity=True)
        eq_(int(pp['capacity'].sum()), 181489)

    def scenario_pp_test(self):
        eq_(float(self.pp['volatile_source']['DE03', 'wind']), 3052.8)
        eq_(float(self.pp['transformer'].loc['capacity', ('DE03', 'lignite')]),
            1135.6)

    def test_scenario_transmission(self):
        lines = basic_scenario.scenario_transmission(
            self.pp, self.regions, 'de22')
        eq_(int(lines.loc['DE07-DE05', ('electrical', 'capacity')]), 1978)
        eq_(int(lines.loc['DE07-DE05', ('electrical', 'distance')]), 199)
        eq_(float(lines.loc['DE07-DE05', ('electrical', 'efficiency')]), 0.9)
        lines = basic_scenario.scenario_transmission(
            self.pp, self.regions, 'de22', copperplate=True)
        eq_(float(lines.loc['DE07-DE05', ('electrical', 'capacity')]),
            float('inf'))
        eq_(str(lines.loc['DE07-DE05', ('electrical', 'distance')]), 'nan')
        eq_(float(lines.loc['DE07-DE05', ('electrical', 'efficiency')]), 1.0)

    def test_scenario_transmisson_error(self):
        old_value = cfg.get('transmission', 'general_efficiency')
        cfg.tmp_set('transmission', 'general_efficiency', 'None')
        msg = "The calculation of the efficiency by distance is not yet"
        with assert_raises_regexp(NotImplementedError, msg):
            basic_scenario.scenario_transmission(
                self.pp, self.regions, 'de22')
        cfg.tmp_set('transmission', 'general_efficiency', old_value)

    def test_scenario_commodity_sources(self):
        src = basic_scenario.scenario_commodity_sources(
            self.pp, 2013)['commodity_source']
        eq_(round(src.loc['costs', ('DE', 'hard coal')], 2), 9.71)
        eq_(round(src.loc['emission',  ('DE', 'natural gas')], 2), 201.24)

    def test_chp(self):
        eq_(int(self.pp['transformer'].loc['capacity', ('DE01', 'hard coal')]),
            1291)
        transf = basic_scenario.scenario_chp(
            self.pp, self.regions, 2014, 'de21')['transformer']
        eq_(int(transf.loc['capacity', ('DE01', 'hard coal')]), 485)
        eq_(int(transf.loc['capacity_elec_chp', ('DE01', 'hard coal')]), 806)
