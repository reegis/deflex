from deflex import main
from oemof.tools import logger

years = [2014, 2013, 2012]
# rmaps = ['de21', 'de22', 'de17', 'de02']
rmaps = ['de22']

logger.define_logging()

for year in years:
    for rmap in rmaps:
        if rmap == 'de22':
            ex_reg = ['DE22']
        else:
            ex_reg = None
        main.main(year, rmap, extra_regions=ex_reg)

