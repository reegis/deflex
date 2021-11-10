from deflex.tools import dict2file, restore_results
from oemof.tools import logger
from deflex.postprocessing import Cycles, calculate_product_fuel_balance
logger.define_logging()

# import os
#
# allocate_fuel("finnish", eta_e=0.3, eta_th=0.5)
# # print(finnish_method(0.3, 0.5, 0.5, 0.9))
# exit(0)

my_fn = "/home/uwe/.deflex/pedro/2018-DE02-Agora4.dflx"
# my_fn = "/home/uwe/.deflex/pedro/2030-DE02-Agora9.dflx"
# my_fn = "/home/uwe/.deflex/pedro/2050-DE02-Agora6.dflx"

my_results = restore_results(my_fn)
# test_print_cycles(my_results)
my_cycles = Cycles(my_results)
my_cycles.print(details=False)
my_cycles.add_filter("storage")
my_cycles.print(details=False)
print(my_cycles.filter)
my_cycles.add_filter(["line", "commodity"])
my_cycles.print(details=True)
print(my_cycles.filter)

my_cycles.digits = 100
my_cycles.detect_suspicious_cycle_rows(path="/home/uwe/00asdf.xlsx")
# exit()

filename2 = my_fn.replace(".dflx", "_results_emission.xlsx")

my_tables = calculate_product_fuel_balance(
    my_results,
    "finnish",
    eta_e=0.3,
    eta_th=0.5,
    eta_e_ref=0.5,
    eta_th_ref=0.9,
)
print("Store file to {}".format(filename2))
dict2file(my_tables, filename2, drop_empty_columns=False)
# # for table in all_results._fields:
# #     print("\n\n***************** " + table + " ****************\n")
# #     print(getattr(all_results, table))
