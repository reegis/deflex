# -*- coding: utf-8 -*-

"""
Test power plants and chp.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from nose.tools import eq_, assert_raises_regexp
from deflex import geometries, powerplants, config as cfg


# class TestScenarioPowerplantsAndCHP:
#     @classmethod
#     def setup_class(cls):
#         cls.regions = geometries.deflex_regions(rmap="de21")
#         cls.pp = basic_scenario.scenario_powerplants(
#             dict(), cls.regions, 2014, "de21",
#         )
#
#     def test_01_deflex_power_plants_by_year(self):
#         pp = powerplants.get_deflex_pp_by_year(
#             self.regions, 2014, "de21", overwrite_capacity=True
#         )
#         eq_(int(pp["capacity"].sum()), 181489)
#
#     def test_scenario_pp(self):
#         eq_(
#             float(
#                 self.pp["volatile_source"].loc[("DE03", "wind"), "capacity"]
#             ),
#             3052.8,
#         )
#         eq_(
#             float(self.pp["transformer"].loc[("DE03", "lignite"), "capacity"]),
#             1135.6,
#         )
#
#     def test_scenario_transmission(self):
#         cfg.tmp_set("init", "map", "de22")
#         lines = basic_scenario.scenario_transmission(
#             self.pp, self.regions, "de22"
#         )
#         line = "DE07-DE05"
#         eq_(int(lines.loc[line, ("electrical", "capacity")]), 1978)
#         eq_(int(lines.loc[line, ("electrical", "distance")]), 199)
#         eq_(float(lines.loc[line, ("electrical", "efficiency")]), 0.9)
#         cfg.tmp_set("basic", "copperplate", True)
#         lines = basic_scenario.scenario_transmission(
#             self.pp, self.regions, "de22"
#         )
#         cfg.tmp_set("basic", "copperplate", False)
#         eq_(
#             float(lines.loc["DE07-DE05", ("electrical", "capacity")]),
#             float("inf"),
#         )
#         eq_(str(lines.loc["DE07-DE05", ("electrical", "distance")]), "nan")
#         eq_(float(lines.loc["DE07-DE05", ("electrical", "efficiency")]), 1.0)
#
#     def test_scenario_transmisson_error(self):
#         old_value = cfg.get("transmission", "general_efficiency")
#         cfg.tmp_set("transmission", "general_efficiency", "None")
#         msg = "The calculation of the efficiency by distance is not yet"
#         with assert_raises_regexp(NotImplementedError, msg):
#             basic_scenario.scenario_transmission(self.pp, self.regions, "de22")
#         cfg.tmp_set("transmission", "general_efficiency", old_value)
#
#     def test_scenario_commodity_sources(self):
#         src = basic_scenario.scenario_commodity_sources(2013)
#         eq_(round(src.loc[("DE", "hard coal"), "costs"], 2), 12.53)
#         eq_(round(src.loc[("DE", "natural gas"), "emission"], 2), 201.0)
#
#     def test_chp(self):
#         eq_(
#             int(self.pp["transformer"].loc[("DE01", "hard coal"), "capacity"]),
#             1291,
#         )
#         tables = basic_scenario.scenario_chp(
#             self.pp, self.regions, 2014, "de21"
#         )
#         transf = tables["transformer"]
#         chp = tables["chp_hp"]
#         eq_(int(transf.loc[("DE01", "hard coal"), "capacity"]), 623)
#         eq_(int(chp.loc[("DE01", "hard coal"), "capacity_elec_chp"]), 667)
