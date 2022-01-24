from deflex.postprocessing import get_all_results
from deflex.tools import dict2file, restore_results

my_fn = "/home/uwe/.deflex/pedro/2018-DE02-Agora4.dflx"
# my_fn = "/home/uwe/.deflex/pedro/2030-DE02-Agora9.dflx"
# my_fn = "/home/uwe/.deflex/pedro/2050-DE02-Agora6.dflx"

my_results = restore_results(my_fn)
all_results = get_all_results(my_results)
dict2file(all_results, "/home/uwe/00_tester.xlsx")
