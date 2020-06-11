from deflex import basic_scenario, config as cfg
from oemof.tools import logger


years = [2014, 2013, 2012]
# years = [2013]
rmaps = ['de21', 'de22', 'de17', 'de02']
# rmaps = ['de02']
logger.define_logging()

for year in years:
    for rmap in rmaps:
        for heat in [True, False]:
            for group in [True, False]:
                cfg.tmp_set("basic", "heat", heat)
                cfg.tmp_set("basic", "group_transformer", group)
                basic_scenario.create_basic_scenario(year, rmap)
