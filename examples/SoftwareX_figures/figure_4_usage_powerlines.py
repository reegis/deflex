import pandas as pd
from matplotlib import patheffects
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from deflex import geometries, tools


def plot_power_lines(geo, data, plot_file):
    """Plot line geometry with data"""
    plt.rcParams.update({"font.size": 12})
    data.name = "value"
    my_aspect = "equal"  # try "auto" instead

    # Define figure
    if my_aspect == "equal":
        size = (9, 6)
    else:
        size = (6.5, 7)
    ax = plt.figure(figsize=size).add_subplot(1, 1, 1)

    # Plot background
    regions = geometries.divide_off_and_onshore(geo.polygons)
    ax = geo.polygons.loc[regions.onshore].plot(
        color="#aed8b4", edgecolor="#9aa1a9", ax=ax, aspect=my_aspect
    )
    ax = geo.polygons.loc[regions.offshore].plot(
        color="#bddce5", edgecolor="#9aa1a9", ax=ax, aspect=my_aspect
    )

    # Add labels for polygons
    for i, v in geo.labels.iterrows():
        ax.text(
            v["geometry"].centroid.x,
            v["geometry"].centroid.y,
            str(i),
            color="#000000",
            fontsize=9.5,
            ma="center",
        )

    # Merge geometry and data
    de21_lines = pd.concat([geo.lines, data], axis=1)

    # Define color map
    cmap_lines = LinearSegmentedColormap.from_list(
        "mycmap",
        [(0, "#aaaaaa"), (0.0001, "green"), (0.5, "yellow"), (1, "red")],
    )

    # Plot lines
    ax = de21_lines.plot(
        "value", ax=ax, aspect=my_aspect, cmap=cmap_lines, legend=True
    )

    # Add labels for lines (> 0.1%)
    for i, v in de21_lines.iterrows():
        if v["value"] > 0.1:
            ax.text(
                v["geometry"].centroid.x,
                v["geometry"].centroid.y,
                "{0}".format(int(v["value"])),
                color="#000000",
                fontsize=12,
                ma="center",
                path_effects=[
                    patheffects.withStroke(linewidth=3, foreground="w")
                ],
            )

    # Adjust and show plot
    ax.axis("off")
    # plt.title("Hours of the year in which usage of the line is over 95%.")
    plt.subplots_adjust(right=1.0, left=0.0, bottom=0.02, top=0.99)
    plt.savefig(plot_file)
    plt.show()


def get_power_line_usage(geo, results):
    """Get specific usage of power line"""

    # Filter all flows
    flowkeys = {k: v for k, v in results["main"].items() if k[1] is not None}

    # Filter all power lines
    powerlines = {
        "{0}-{1}".format(k[1].label.subtag, k[1].label.region): v
        for k, v in flowkeys.items()
        if k[1].label.cat == "line"
    }

    # Get data for each power line
    data = pd.Series(dtype="float64")
    for idx in geo.lines.index:
        idx_values = idx.split("-")
        reverse_idx = "{1}-{0}".format(*idx_values)
        df = (
            powerlines[idx]["sequences"]["flow"]
            + powerlines[reverse_idx]["sequences"]["flow"]
        )
        outflow = [
            o
            for o in flowkeys
            if o[0].label.cat == "line"
            and o[0].label.subtag == idx_values[0]
            and o[0].label.region == idx_values[1]
        ][0]
        try:
            temp = df / results["param"][outflow]["scalars"]["nominal_value"]
        except KeyError:
            temp = df * 0
        data[idx] = round(len(temp[temp > 0.9]))
    return data


import os

de21 = geometries.deflex_geo("de21")
p = "/home/uwe/.deflex/deflex_softwareX_2022/results_cbc/final"
fn_p = "deflex_2014_de21_heat_transmission_{0}.dflx"
for t in ["master", "dev"]:
    fn = os.path.join(p, fn_p.format(t))
    plot_fn = fn.replace(".dflx", ".png")
    scenario = tools.restore_scenario(fn)
    # tools.dict2file(
    #     scenario.input_data, fn.replace(".dflx", "_csv"), "csv"
    # )
    my_data = get_power_line_usage(de21, scenario.results)
    plot_power_lines(de21, my_data, plot_fn)
