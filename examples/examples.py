import datetime
import logging
import math
import os
import warnings
from collections import namedtuple
from pprint import pprint
from time import sleep
from zipfile import ZipFile

import pandas as pd
import pytz
from oemof import solph
from oemof.tools import logger

from deflex import analyses
from deflex import config as cfg
from deflex import geometries
from deflex import main
from deflex import results
from deflex import tools

try:
    from lmfit.models import LinearModel
except ModuleNotFoundError:
    LinearModel = None
try:
    from oemof_visio.plot import io_plot
    from oemof_visio.plot import set_datetime_ticks
except ModuleNotFoundError:
    io_plot = None

try:
    from matplotlib import patches
    from matplotlib import patheffects
    from matplotlib import pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.dates import DateFormatter
    from matplotlib.dates import HourLocator
except ModuleNotFoundError:
    plt = None


MISSING_MODULES = []

OPSD_URL = (
    "https://data.open-power-system-data.org/index.php?package="
    "time_series&version=2019-06-05&action=customDownload&resource=3"
    "&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bfrom%5D="
    "2005-01-01&filter%5B_contentfilter_cet_cest_timestamp%5D%5Bto%5D"
    "=2019-05-01&filter%5BRegion%5D%5B%5D=DE&filter%5BVariable%5D%5B"
    "%5D=price_day_ahead&downloadCSV=Download+CSV"
)

EXAMPLE_URL = (
    "https://files.de-1.osf.io/v1/resources/a5xrj/providers/"
    "osfstorage/5fdc7e0bf0df5405452ef6f0/?zip="
)

GITHUB_BASE_URL = "https://raw.githubusercontent.com/reegis/deflex/master/{0}"

BASEPATH = os.path.join(os.path.expanduser("~"), "deflex_examples")

IMAGETYPE = "png"  # svg, pdf, png, eps


def download_example_scenarios(path):
    """Download example data from OSF and other files."""

    # Examples from OSF
    os.makedirs(path, exist_ok=True)
    fn_zip = os.path.join(path, "software_x_scenario_examples.zip")
    tools.download(fn_zip, EXAMPLE_URL)

    # plot.ini from github
    url = GITHUB_BASE_URL.format("examples/plot.ini")
    fn_ini = os.path.join(path, "plot.ini")
    tools.download(fn_ini, url)

    with ZipFile(fn_zip, "r") as zip_ref:
        zip_ref.extractall(path)
    logging.info("All SoftwareX scenarios extracted to {}".format(path))


def get_price_from_opsd(path):
    """Get day ahead prices from opsd time series."""
    fn = os.path.join(path, "opsd_day_ahead_prices.csv")
    tools.download(fn, OPSD_URL)

    de_ts = pd.read_csv(
        fn,
        index_col="utc_timestamp",
        parse_dates=True,
        date_parser=lambda col: pd.to_datetime(col, utc=True),
    )
    de_ts.index = de_ts.index.tz_convert("Europe/Berlin")
    de_ts.index.rename("cet_timestamp", inplace=True)
    berlin = pytz.timezone("Europe/Berlin")
    start_date = berlin.localize(datetime.datetime(2014, 1, 1, 0, 0, 0))
    end_date = berlin.localize(datetime.datetime(2014, 12, 31, 23, 0, 0))
    return de_ts.loc[start_date:end_date, "DE_price_day_ahead"]


def get_scenario(path):
    """
    Search for result files in the given directory and return them
    as a list (ls) or a numbered dictionary (dc).
    """
    d = namedtuple("sc", ("ls", "dc"))
    s = results.search_results(path)
    sc_dict = {k: v for v, k in zip(sorted(s), range(len(s)))}
    pprint(sc_dict)
    return d(ls=sorted(s), dc=sc_dict)


def get_key_values_from_results(result):
    """
    Extract key values from a list of solph results dictionaries.

    emissions_average: The average emissions per time step
    emissions_mcp: The emissions of the most expensive running power plant
    mcp: Market Clearing Price (MCP), the costs of the most expensive running
         power plant.

    Parameters
    ----------
    result : list
        A list of solph results dictionaries.

    Returns
    -------
    pandas.DataFrame : Key values for each result dictionary.
    """
    kv = pd.DataFrame(columns=pd.MultiIndex(levels=[[], []], codes=[[], []]))
    for r in result:
        name = r["meta"]["scenario"]["name"]
        flow_res = analyses.get_flow_results(r)
        if "chp" in flow_res["cost", "specific", "trsf"].columns:
            kv["mcp", name] = flow_res.drop(
                ("cost", "specific", "trsf", "chp"), axis=1
            )["cost", "specific"].max(axis=1)
        else:
            kv["mcp", name] = flow_res["cost", "specific"].max(axis=1)
        mcp_id = flow_res["cost", "specific"].idxmax(axis=1)
        emissions = flow_res["emission", "specific"]
        kv["emissions_average", name] = (
            flow_res["emission", "absolute"]
            .sum(axis=1)
            .div(flow_res["values", "absolute"].sum(axis=1))
        )
        kv["emissions_mcp", name] = pd.Series(
            emissions.lookup(*zip(*pd.DataFrame(data=mcp_id).to_records()))
        )
    return kv


def plot_power_lines(
    data,
    key,
    cmap_lines=None,
    cmap_bg=None,
    direction=True,
    vmax=None,
    label_min=None,
    label_max=None,
    unit="GWh",
    size=None,
    ax=None,
    legend=True,
    unit_to_label=False,
    divide=1,
    decimal=0,
    exist=None,
):
    """
    Parameters
    ----------
    data
    key
    cmap_lines
    cmap_bg
    direction
    vmax
    label_min
    label_max
    unit
    size
    ax
    legend
    unit_to_label
    divide
    decimal
    exist

    Returns
    -------

    """
    if size is None and ax is None:
        ax = plt.figure(figsize=(5, 5)).add_subplot(1, 1, 1)
    elif size is not None and ax is None:
        ax = plt.figure(figsize=size).add_subplot(1, 1, 1)

    if unit_to_label is True:
        label_unit = unit
    else:
        label_unit = ""
    lines = geometries.deflex_power_lines("de21")
    polygons = geometries.deflex_regions("de21")
    if lines is None:
        msg = (
            "\nTo plot a map you need to install 'geopandas', 'descartes' and "
            "'pygeos'\n\n pip install geopandas descartes pygeos\n"
        )
        raise ModuleNotFoundError(msg)

    lines = lines.merge(data.div(divide), left_index=True, right_index=True)
    lines["centroid"] = lines.to_crs(epsg=25832).centroid.to_crs(epsg="4326")

    if cmap_bg is None:
        cmap_bg = LinearSegmentedColormap.from_list(
            "mycmap", [(0, "#aed8b4"), (1, "#bddce5")]
        )

    if cmap_lines is None:
        cmap_lines = LinearSegmentedColormap.from_list(
            "mycmap",
            [(0, "#aaaaaa"), (0.0001, "green"), (0.5, "yellow"), (1, "red")],
        )

    offshore = geometries.divide_off_and_onshore(polygons).offshore
    polygons["color"] = 0
    polygons.loc[offshore, "color"] = 1

    lines["reverse"] = lines[key] < 0

    # if direction is False:
    lines.loc[lines["reverse"], key] = lines.loc[lines["reverse"], key] * -1

    if vmax is None:
        vmax = lines[key].max()

    if label_min is None:
        label_min = vmax * 0.5

    if label_max is None:
        label_max = float("inf")

    ax = polygons.plot(
        edgecolor="#9aa1a9",
        cmap=cmap_bg,
        column="color",
        ax=ax,
        aspect="equal",
    )
    if exist is not None:
        lines = lines.loc[lines[exist] == 1]

    ax = lines.plot(
        cmap=cmap_lines,
        legend=legend,
        ax=ax,
        column=key,
        vmin=0,
        vmax=vmax,
        aspect="equal",
    )
    for i, v in lines.iterrows():
        x1 = v["geometry"].coords[0][0]
        y1 = v["geometry"].coords[0][1]
        x2 = v["geometry"].coords[1][0]
        y2 = v["geometry"].coords[1][1]

        value_relative = v[key] / vmax
        mc = cmap_lines(value_relative)

        orient = math.atan(abs(x1 - x2) / abs(y1 - y2))

        if (y1 > y2) & (x1 > x2) or (y1 < y2) & (x1 < x2):
            orient *= -1

        if v["reverse"]:
            orient += math.pi

        if v[key] == 0 or not direction:
            polygon = patches.RegularPolygon(
                (v["centroid"].x, v["centroid"].y),
                4,
                0.15,
                orientation=orient,
                color=(0, 0, 0, 0),
                zorder=10,
            )
        else:
            polygon = patches.RegularPolygon(
                (v["centroid"].x, v["centroid"].y),
                3,
                0.15,
                orientation=orient,
                color=mc,
                zorder=10,
            )
        ax.add_patch(polygon)

        if decimal == 0:
            value = int(round(v[key]))
        else:
            value = round(v[key], decimal)

        if label_min <= value <= label_max:
            if v["reverse"] is True and direction is False:
                value *= -1
            ax.text(
                v["centroid"].x,
                v["centroid"].y,
                "{0} {1}".format(value, label_unit),
                color="#000000",
                fontsize=11,
                zorder=15,
                path_effects=[
                    patheffects.withStroke(linewidth=3, foreground="w")
                ],
            )

    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    ax.axis("off")

    polygons.apply(
        lambda x: ax.annotate(
            x.name, xy=x.geometry.centroid.coords[0], ha="center"
        ),
        axis=1,
    )
    return ax


def show_transmission(path, name=None, number=0):
    """

    Parameters
    ----------
    path
    name
    number

    Returns
    -------

    """
    global MISSING_MODULES
    if name is not None:
        sc = [s for s in get_scenario(path).ls if name in s][0]
    else:
        sc = get_scenario(path).dc[number]

    res = results.restore_results(sc)
    r = res["Main"]
    p = res["Param"]

    flows = [
        k for k in r.keys() if k[1] is not None and k[0].label.cat == "line"
    ]
    transmission = pd.DataFrame()
    trk = pd.DataFrame()

    lines = geometries.deflex_power_lines("de21")

    if lines is None:
        lines = pd.DataFrame(index=["DE13-DE15", "DE08-DE09"])

    for flow in flows:
        name = "-".join([flow[0].label.subtag, flow[1].label.region])
        if name in lines.index:
            try:
                capacity = p[flow]["scalars"].nominal_value
            except AttributeError:
                capacity = -1

            back_flow = [
                x
                for x in flows
                if x[0].label.subtag == flow[1].label.region
                and x[1].label.region == flow[0].label.subtag
            ][0]
            transmission[name] = (
                r[flow]["sequences"]["flow"]
                - r[back_flow]["sequences"]["flow"]
            )
            if capacity > 0:
                trk.loc[name, "exist"] = True
                trk.loc[name, "max_fraction"] = (
                    transmission[name].abs().max() / capacity * 100
                )
                trk.loc[name, "hours_90_prz"] = (
                    transmission[name]
                    .loc[transmission[name].abs().div(capacity) > 0.9]
                    .count()
                )
                trk.loc[name, "hours_90_prz_frac"] = (
                    trk.loc[name, "hours_90_prz"] / len(transmission) * 100
                )
                trk.loc[name, "avg_fraction"] = (
                    transmission[name].abs().sum()
                    / (capacity * len(transmission))
                    * 100
                )
            elif capacity == 0 and transmission[name].max() > 0:
                raise ValueError("Something odd happend")
            else:
                trk.loc[name, "exist"] = False
                trk.loc[name, "max_fraction"] = -1
                trk.loc[name, "avg_fraction"] = -1
                trk.loc[name, "hours_90_prz_frac"] = 0
                trk.loc[name, "hours_90_prz"] = -1
            trk.loc[name, "max"] = transmission[name].abs().max()
            trk.loc[name, "avg"] = transmission[name].abs().mean()
            trk.loc[name, "sum"] = transmission[name].abs().sum()

    if plt is not None:
        f, ax = plt.subplots(1, 1, sharex=True, figsize=(8, 5))
        plt.rcParams.update({"font.size": 11})
        try:
            plot_power_lines(
                trk,
                "hours_90_prz_frac",
                direction=False,
                vmax=25,
                label_min=1,
                unit_to_label=True,
                unit="%",
                ax=ax,
                exist="exist",
            )
        except ModuleNotFoundError:
            MISSING_MODULES.extend(["geopandas", "descartes", "pygeos"])
            msg = (
                "'geopandas', 'descartes' and 'pygeos' are missing. To show "
                "the plot use:\n pip install geopandas descartes pygeos"
            )
            ax.text(0.2, 0.5, msg, fontsize=12)
        plt.subplots_adjust(right=1, left=0, bottom=0.02, top=0.98)
        figure_path = os.path.join(BASEPATH, "figures")
        os.makedirs(figure_path, exist_ok=True)
        plt.savefig(
            os.path.join(figure_path, "transmission.{}".format(IMAGETYPE))
        )
        plt.show()
    else:
        print(
            "Fraction of time [%] in which the use of the line is greater "
            "than 90%"
        )
        print(trk["hours_90_prz_frac"].round(1).sort_values())
        sleep(1)
        MISSING_MODULES.extend(
            ["matplotlib", "geopandas", "descartes", "pygeos"]
        )
        msg = (
            "\nTo see the mcp plot you need to install 'matplotlib' "
            "\n\n pip install matplotlib\n"
        )
        warnings.warn(msg, UserWarning)


def show_relation(mcp, name="deflex_2014_de02"):
    """Show relation between OPSD price and scenario prices."""
    if LinearModel is not None and plt is not None:
        mean = mcp["opsd"].mean()
        mcp = mcp.groupby("opsd").mean().loc[0:90]

        model = LinearModel()
        result = model.fit(mcp[name], x=mcp.index)
        ax = result.plot_fit()
        ax.set_xlabel("price from opsd data")
        ax.set_ylabel("price from {0} data".format(name))

        # line x=y to get an orientation
        x = pd.Series([0, 40, 100])
        ax.plot(x, x)

        # mean price of opsd data
        g1 = pd.Series([mean, mean])
        g2 = pd.Series([0, 100])
        ax.plot(g1, g2)
        figure_path = os.path.join(BASEPATH, "figures")
        os.makedirs(figure_path, exist_ok=True)
        plt.savefig(
            os.path.join(
                figure_path, "mcp_comparison_detailed.{}".format(IMAGETYPE)
            )
        )
        plt.show()
    else:
        global MISSING_MODULES
        if plt is None:
            MISSING_MODULES.append("matplotlib")
        if LinearModel is None:
            MISSING_MODULES.append("lmfit")

        msg = (
            "\nTo see the relation plot you need to install 'matplotlib' "
            "and lmfit.\n\n pip install matplotlib lmfit\n"
        )
        warnings.warn(msg, UserWarning)


def fetch_mcp(path):
    file = os.path.join(path, "key_values.xls")
    if not os.path.isfile(file):
        res = results.restore_results(get_scenario(path).ls)
        s = get_key_values_from_results(res)
        mcp = pd.DataFrame(s["mcp"])
        opsd = get_price_from_opsd(path)
        mcp["opsd"] = opsd.reset_index(drop=True)
        mcp.set_index(opsd.index, drop=True, inplace=True)
        mcp.tz_localize(None).to_excel(file)
    else:
        mcp = pd.read_excel(file, index_col=0, header=0)
    return mcp


def compare_different_mcp(mcp):
    res_dict = {
        k: v for v, k in zip(sorted(mcp.columns), range(len(mcp.columns)))
    }

    s = [
        "deflex_2014_de02",
        # "deflex_2014_de17_heat",
        # "deflex_2014_de21_copperplate",
        # "deflex_2014_de21_transmission-losses",
        "opsd",
    ]

    choice = [v for k, v in res_dict.items() if v in s]
    mcp = mcp[choice]
    year = str(mcp.index[0].year)

    iv = [("8.1.", "25.1."), ("8.4.", "25.4."), ("8.7.", "25.7.")]

    if plt is not None:
        plt.rcParams.update({"font.size": 16})
        f, ax = plt.subplots(3, 1, sharey=True, figsize=(15, 6))
        n = -1
        for interval in iv:
            n += 1
            start = datetime.datetime.strptime(interval[0] + year, "%d.%m.%Y")
            start += datetime.timedelta(hours=12)
            end = datetime.datetime.strptime(interval[1] + year, "%d.%m.%Y")
            end += datetime.timedelta(hours=12)
            mcp[start:end].plot(ax=ax[n], legend=False, x_compat=True)
            ax[n].set_xlim(start, end)
            ax[n].xaxis.set_major_locator(HourLocator(interval=72))
            ax[n].xaxis.set_major_formatter(DateFormatter("%b-%d %H:%M"))
            ax[n].tick_params(axis="x", rotation=0)
            [
                label.set_horizontalalignment("center")
                for label in ax[n].xaxis.get_ticklabels()
            ]
            ax[n].set_ylabel("[EUR/MWh]")
        sc = []
        # ax[0].set_title(
        #     "The Market Clearing Price (MCP) in different periods in 2014"
        # )
        for c in mcp.columns:
            c = c.replace("deflex_2014_", "")
            c = c.replace("_no-heat_reg-merit_no-co2-costs_no-var-costs", "")
            c = c.replace("_no-heat_reg-merit_no-co2-prices_no-var-costs", "")
            c = c.replace("copperplate", "cp")
            c = c.replace("opsd", "Entsoe")
            sc.append(c)
        ax[n].legend(sc, bbox_to_anchor=(1.135, 1), loc="upper right")
        plt.subplots_adjust(
            right=0.892, left=0.045, hspace=0.22, bottom=0.06, top=0.99
        )
    print("*****Standard deviation of the MCP ***************************")
    print(mcp.std())
    print("**************************************************************")
    print()
    print("*****Average MCP *********************************************")
    print(mcp.mean())
    print("**************************************************************")
    print()
    values = mcp["opsd"]
    diff = mcp.sub(values, axis=0)
    print("*****Standard deviation of difference (Entsoe - Scenario *******")
    print(diff.std())
    print("**************************************************************")

    if plt is not None:
        figure_path = os.path.join(BASEPATH, "figures")
        os.makedirs(figure_path, exist_ok=True)
        plt.savefig(os.path.join(figure_path, "mcp.{}".format(IMAGETYPE)))
        plt.show()
    else:
        global MISSING_MODULES
        MISSING_MODULES.append("matplotlib")
        msg = (
            "\nTo see the mcp plot you need to install 'matplotlib' "
            "\n\n pip install matplotlib\n"
        )
        warnings.warn(msg, UserWarning)


def compare_emission_types(path, name=None, number=0):
    if name is not None:
        sc = [s for s in get_scenario(path).ls if name in s][0]
    else:
        sc = get_scenario(path).dc[number]
    logging.info("Scenario to compare emissions: {}".format(sc))
    res = results.restore_results(sc)
    kv = get_key_values_from_results([res])
    if plt is not None:
        emission_multiplot(res, kv)
    else:
        global MISSING_MODULES
        MISSING_MODULES.append("matplotlib")
        msg = (
            "\nTo see the mcp plot you need to install 'matplotlib' "
            "\n\n pip install matplotlib\n"
        )
        warnings.warn(msg, UserWarning)


def emission_multiplot(res, kv):
    plt.rcParams.update({"font.size": 16})
    name = res["meta"]["scenario"]["name"]
    f, ax = plt.subplots(2, 1, sharex=True, figsize=(15, 6))
    region = "all"
    buses = results.search_nodes(res, solph.Bus, tag="electricity")
    interval = ("5.8.", "26.8.")
    year = str(2014)
    start_year = datetime.datetime(2014, 1, 1)
    start = datetime.datetime.strptime(interval[0] + year, "%d.%m.%Y")
    start += datetime.timedelta(hours=12)
    start = (start - start_year).days * 24
    end = datetime.datetime.strptime(interval[1] + year, "%d.%m.%Y")
    end += datetime.timedelta(hours=12)
    end = (end - start_year).days * 24
    am = [
        ("cat", "line", "all"),
        ("tag", "ee", "all"),
        ("tag", "chp", "all"),
    ]

    if "no-reg-merit" not in name:
        am.append(("tag", "pp", -1))

    kv["emissions_mcp"][name].div(1000).plot(ax=ax[0])
    kv["emissions_average"][name].div(1000).plot(ax=ax[0], legend=True)
    ax[0].set_xlim(start, end)
    ax[0].set_ylim(0, 1.8)
    ax[0].set_xticks([])
    ax[0].set_ylabel("CO2-Emission [tons/MWh]")
    ax[0].legend(
        ["most expensive", "average"],
        bbox_to_anchor=(1, 0.8),
        loc="center left",
    )
    ax[0].set_ylabel("Emissions [tons/MWh]")

    am = [
        ("cat", "line", "all"),
        ("tag", "ee", "all"),
        ("tag", "chp", "all"),
    ]

    if "no-reg-merit" not in name:
        am.append(("tag", "pp", -1))

    df = results.reshape_bus_view(res, buses, aggregate=am)
    idx = df.index

    if region == "all":
        df = df.groupby(level=[1, 2, 3, 4], axis=1).sum()
    else:
        df = df[(region,)]
        df = df.groupby(level=[0, 1, 2, 3], axis=1).sum()

    if region == "all":
        df["out", "line", "electricity", "losses"] = (
            df["out", "line", "electricity", "all"]
            - df["in", "line", "electricity", "all"]
        )
        keys = [
            ("in", "line", "electricity", "all"),
            ("out", "line", "electricity", "all"),
        ]
        df.drop(keys, axis=1, inplace=True)

    in_order = [
        ("trsf", "pp", "lignite"),
        ("trsf", "pp", "nuclear"),
        ("trsf", "pp", "hard_coal"),
        ("trsf", "pp", "natural_gas"),
        ("trsf", "pp", "oil"),
        ("trsf", "pp", "other"),
        ("trsf", "pp", "waste"),
        ("trsf", "pp", "bioenergy"),
        ("trsf", "pp", "all"),
        ("trsf", "chp", "all"),
        ("storage", "electricity", "phes"),
        ("storage", "electricity", "all"),
        ("source", "ee", "geothermal"),
        ("source", "ee", "hydro"),
        ("source", "ee", "solar"),
        ("source", "ee", "wind"),
        ("source", "ee", "all"),
        ("line", "electricity", "all"),
        ("shortage", "electricity", "all"),
    ]
    out_order = [
        ("demand", "electricity", "all"),
        # ("excess", "electricity", "all"),
        ("storage", "electricity", "phes"),
        # ("line", "electricity", "all"),
        # ("line", "electricity", "losses"),
    ]

    cd = get_cdict_df(df["in"])
    cd.update(get_cdict_df(df["out"]))

    if io_plot is not None:
        ioplot = io_plot(
            df_in=df["in"].div(1000),
            df_out=df["out"].div(1000),
            inorder=in_order,
            outorder=out_order,
            smooth=True,
            ax=ax[1],
            cdict=cd,
        )
        ax[1].set_xlim(start, end)
        ax[1] = set_datetime_ticks(
            ax[1], idx, tick_distance=96, offset=12, date_format="%b-%d %H:%M"
        )
        ax[1].set_ylabel("Power [GW]")
        ioplot["ax"] = shape_tuple_legend(reverse=False, up=0.8, **ioplot)
        ax[1].set_xlim(start, end)
    else:
        x = start + 100
        msg = (
            " oemof_visio is missing. To show the plot use:\n pip install "
            "https://github.com/oemof/oemof_visio/archive/master.zip"
        )
        ax[1].text(x, 0.5, msg, fontsize=12)
    plt.subplots_adjust(
        right=0.817, left=0.05, hspace=0.08, bottom=0.06, top=0.98
    )
    figure_path = os.path.join(BASEPATH, "figures")
    os.makedirs(figure_path, exist_ok=True)
    plt.savefig(os.path.join(figure_path, "emissions.{}".format(IMAGETYPE)))
    plt.show()


def get_cdict_df(df):
    my_colors = cfg.get_dict_list("plot_colors", string=True)
    color_dict = {}
    for col in df.columns:
        n = 0
        color_keys = list(my_colors.keys())
        try:
            while color_keys[n] not in str(col).lower():
                n += 1
            if len(my_colors[color_keys[n]]) > 1:
                color = "#{0}".format(my_colors[color_keys[n]].pop(0))
            else:
                color = "#{0}".format(my_colors[color_keys[n]][0])
            color_dict[col] = color
        except IndexError:
            color_dict[col] = "#ff00f0"
    return color_dict


def shape_tuple_legend(reverse=False, up=1.0, **kwargs):
    rm_list = ["source", "trsf", "electricity"]
    handels = kwargs["handles"]
    labels = kwargs["labels"]
    axes = kwargs["ax"]
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace("(", "")
        label = label.replace(")", "")
        label = label.replace("ee", "renewable")
        label = label.replace(", all", "")
        label = [x for x in label.split(", ") if x not in rm_list]
        label = ", ".join(label)
        new_labels.append(label)
    labels = new_labels

    parameter["bbox_to_anchor"] = kwargs.get("bbox_to_anchor", (1, 0 + up))
    parameter["loc"] = kwargs.get("loc", "center left")
    parameter["ncol"] = kwargs.get("ncol", 1)
    plotshare = kwargs.get("plotshare", 1)

    if reverse:
        handels.reverse()
        labels.reverse()

    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

    parameter["handles"] = handels
    parameter["labels"] = labels
    axes.legend(**parameter)
    return axes


def main_deflex(path, name=None):
    logger.define_logging()
    scenarios = main.fetch_scenarios_from_dir(path, xls=True)
    if name is not None:
        scenarios = [s for s in scenarios if name in s]
    print(scenarios)
    for scenario in scenarios:
        n = "de" + str(scenario.split("_de")[-1].split(".")[0])
        main.plot_scenario(
            scenario, graphml_file="{0}/mob_{1}.graphml".format(path, n)
        )
        main.model_scenario(scenario)


def check_modules():
    mm = set(MISSING_MODULES)
    if len(mm) > 0:
        print("\nMissing modules:")
        pip = "\nUse: pip install"
        for m in mm:
            print(" * {0}".format(m))
            pip += " {0}".format(m)
        print(pip)

    if io_plot is None:
        print(
            "\nTo see the balance plot you additionally need to install "
            "oemof visio:\npip install "
            "https://github.com/oemof/oemof_visio/archive/master.zip"
        )


if __name__ == "__main__":
    logger.define_logging()
    my_path = BASEPATH  # change the BASEPATH at the top of the file
    download_example_scenarios(my_path)
    # main_deflex(my_path, name="de02")
    my_mcp = fetch_mcp(my_path)
    show_relation(my_mcp, name="deflex_2014_de02")
    compare_different_mcp(my_mcp)
    compare_emission_types(my_path, name="deflex_2014_de02")
    show_transmission(my_path, name="de21_transmission-losses")
    check_modules()
