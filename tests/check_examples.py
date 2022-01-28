import datetime
import os
import warnings

import matplotlib
from matplotlib import pyplot as plt
from termcolor import colored

warnings.filterwarnings("ignore", "", UserWarning)
matplotlib.use("Agg")

debug = False  # If True script will stop if error is raised

fullpath = os.path.join(os.getcwd(), os.pardir, "examples")
checker = {}
number = 0

examples_start = datetime.datetime.now()

for root, dirs, files in sorted(os.walk(fullpath)):
    for name in sorted(files):
        print(name)
        if name[-3:] == ".py":
            fn = os.path.join(root, name)
            os.chdir(root)
            number += 1
            if debug:
                print(fn)
                exec(open(fn).read())
            else:
                try:
                    exec(open(fn).read())
                    checker[name] = "okay"
                except Exception:
                    checker[name] = "failed"
        plt.close()


print("******* TEST RESULTS ***********************************")

print(
    "\n{0} examples tested in {1}.\n".format(
        number, datetime.datetime.now() - examples_start
    )
)

for k, v in checker.items():
    if v == "failed":
        print(k, colored(v, "red"))
    else:
        print(k, colored(v, "green"))
