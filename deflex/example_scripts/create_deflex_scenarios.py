from deflex import basic_scenario
from oemof.tools import logger

# years = [2014, 2013, 2012]
years = [2014]
rmaps = ['de21', 'de22', 'de17', 'de02']

logger.define_logging()

for year in years:
    for rmap in rmaps:
        basic_scenario.create_basic_scenario(year, rmap)

