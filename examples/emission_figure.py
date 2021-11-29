import datetime
import os

import oemof_visio
from matplotlib import pyplot as plt

from deflex import postprocessing, tools


plot_colors = {
    "bioenergy": "#163e16",
    "hydro": "#14142c",
    "pv": "#ffde32",
    "solar": "#ffde32",
    "wind": "#335a8a",
    "natural gas": "#555555",
    "demand": "#800060",
    "hard coal": "#000000",
    "lignite": "#6c3012",
    "other": "#312473",
    "storage": "#09516c",
    "nuclear": "#deff00",
    "renewable": "#f47c3b",
    "waste": "#547969",
}

# my_path = "/home/uwe/.deflex/deflex_examples/results_cbc"
# my_path = "/home/uwe/.deflex/v03/results_cbc/"
my_path = "/home/uwe/deflex_temp_test/results_cbc/"
# my_file = "deflex_2014_de02_heat.dflx"
# my_file = "deflex_2014_de02_heat_no-co2-costs_no-var-costs.dflx"
# my_file = "deflex_2014_de02_no-heat.dflx"
my_file = "deflex_2014_de02_no-heat_no-co2-costs_no-var-costs.dflx"
my_results = tools.restore_results(os.path.join(my_path, my_file))
df3 = postprocessing.get_converter_balance(my_results, cat="power plant")
# df3["in"].groupby(level=2, axis=1).sum().plot()
print(df3["in"].groupby(level=2, axis=1).sum())
print(df3["in"].groupby(level=2, axis=1).sum().sum())
emissions = postprocessing.fetch_parameter_of_commodity_sources(my_results)["emission"]
emissions.index = emissions.index.droplevel(1)
print(emissions)
total_emissions = df3["in"].groupby(level=2, axis=1).sum().mul(emissions).sum(axis=1)
total_electricity_converter = df3["out"].sum(axis=1)


rn = {
    "geothermal": "renewable",
    "hydro": "renewable",
    "solar": "renewable",
    "wind": "renewable",
    "bioenergy": "other",
    "oil": "other",
    "waste": "waste",
    "all": "demand",
    "phes": "storage",
}

df2 = postprocessing.calculate_key_values(my_results)
df = postprocessing.get_combined_bus_balance(my_results, cat="electricity")

total_electricity = df["out"]['electricity demand']
total_electricity.columns = total_electricity.columns.droplevel([1, 2])
print(total_electricity)
print(total_emissions)
avg = total_emissions/total_electricity["electricity"]
print(avg)
avg.plot()
plt.show()
exit(0)
# exit(0)
# exit(0)
c2 = {str(v): str(v.split("_0")[0]) for v in df.columns.levels[2]}
df.rename(columns=c2, inplace=True)
# c3 = {v: v.replace("_", " ") for v in df.columns.levels[3] if "_" in v}
# print(c3)
# df.rename(columns=c3, inplace=True)

df = df.groupby(level=[0, 1, 3], axis=1).sum()
df.drop(["line", "shortage", "excess"], axis=1, level=1, inplace=True)
print(df.columns)
df.columns = df.columns.droplevel(1)
print(df.columns)
df.rename(columns=rn, inplace=True)
df = df.groupby(level=[0, 1], axis=1).sum()
for c in df.columns:
    print(c)
startdate = datetime.datetime(2014, 8, 4, 0, 0, 0)
enddate = datetime.datetime(2014, 8, 27, 0, 0, 0)

interval = ("5.8.", "26.8.")
year = str(2014)
start_year = datetime.datetime(2014, 1, 1)
start = datetime.datetime.strptime(interval[0] + year, "%d.%m.%Y")
start += datetime.timedelta(hours=12)
start = (start - start_year).days * 24
end = datetime.datetime.strptime(interval[1] + year, "%d.%m.%Y")
end += datetime.timedelta(hours=12)
end = (end - start_year).days * 24

print(df.loc[startdate:enddate].sum())
idx = df.index
inorder = [
    "waste",
    "bioenergy",
    "lignite",
    "nuclear",
    "hard coal",
    "natural gas",
    "other",
    "renewable",
    # "waste",
    "storage",
]
outorder = ["demand", "storage"]
f, ax = plt.subplots(2, 1, sharex=True, figsize=(15, 6))

ioplot = oemof_visio.plot.io_plot(
    df_in=df["in"],
    df_out=df["out"],
    smooth=True,
    inorder=inorder,
    outorder=outorder,
    cdict=plot_colors,
    ax=ax[1],
)

ax[1] = oemof_visio.plot.set_datetime_ticks(
    ax[1], idx, tick_distance=96, offset=12, date_format="%b-%d %H:%M"
)

ax[1].set_ylabel("Power [GW]")
# ioplot["ax"] = shape_tuple_legend(reverse=False, up=0.8, **ioplot)
ax[1].set_xlim(start, end)
df2["emissions"].reset_index(drop=True).loc[start:end].plot(ax=ax[0], legend=True)
plt.legend(bbox_to_anchor=(1, 1.1), loc="upper left")
plt.show()
