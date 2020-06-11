from deflex import main
from oemof.tools import logger
import os

# years = [2014, 2013, 2012]
# # rmaps = ['de21', 'de22', 'de17', 'de02']
# rmaps = ['de22']
#
logger.define_logging()
#
# for year in years:
#     for rmap in rmaps:
#         if rmap == 'de22':
#             ex_reg = ['DE22']
#         else:
#             ex_reg = None
#         main.main(year, rmap, extra_regions=ex_reg)

base_path = "/home/uwe/reegis/scenarios/deflex"
year = 2014
name = "deflex_2014_de21_heat_reg-merit_csv"

csv_path = os.path.join(base_path, str(year), name)
main.model_scenario(csv_path=csv_path, year=year, rmap="de21", plot_graph=True)
