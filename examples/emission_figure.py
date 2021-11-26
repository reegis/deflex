import pandas as pd
import datetime
from deflex import tools, postprocessing
import oemof_visio
from matplotlib import pyplot as plt

my_results = tools.restore_results("/home/uwe/deflex_2014_de02_heat.dflx")
rn = {
    "geothermal": "renewable",
    "hydro": "renewable",
    "solar": "renewable",
    "wind": "renewable",
    "bioenergy": "renewable",
    "oil": "other",
    "waste": "other",
    "all": "demand",
    "phes": "storage",
}


df = postprocessing.get_combined_bus_balance(my_results, tag="electricity")
print(df["in", "source", "ee"].sum())
c2 = {str(v): str(v.split("_0")[0]) for v in df.columns.levels[3]}
df.rename(columns=c2, inplace=True)
c3 = {v: v.replace("_", " ") for v in df.columns.levels[3] if "_" in v}
print(c3)
df.rename(columns=c3, inplace=True)
df = df.groupby(level=[0, 1, 3], axis=1).sum()
df.drop(["line", "shortage", "excess"], axis=1, level=1, inplace=True)
df.columns = df.columns.droplevel(1)
df.rename(columns=rn, inplace=True)
df = df.groupby(level=[0, 1], axis=1).sum()
for c in df.columns:
    print(c)
startdate = datetime.datetime(2014, 8, 4, 0, 0, 0)
enddate = datetime.datetime(2014, 8, 26, 0, 0, 0)
print(df.sum())
df = df.loc[startdate:enddate]
inorder = ["lignite", "nuclear", "hard coal", "natural gas", "other", "renewable", "storage"]
outorder = ["demand", "storage"]
oemof_visio.plot.io_plot(
    df_in=df["in"], df_out=df["out"], smooth=True, inorder=inorder, outorder=outorder
)
plt.show()
