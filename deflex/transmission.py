# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


# Python libraries
import os

# External libraries
import pandas as pd
import math

# internal modules
from deflex import config as cfg

from deflex import geometries


def get_grid_capacity(grid, plus, minus):
    """Read the grid capacity from a given region pair from the renpass db."""
    tmp_grid = grid.query(
        "plus_region_id == {:0d} & ".format(plus)
        + "minus_region_id == {:1d} & ".format(minus)
        + "scenario_name == 'status_quo_2012_distance'"
    )

    if len(tmp_grid) > 0:
        capacity = tmp_grid.capacity_calc.sum()
        distance = tmp_grid.distance.iloc[0]
    else:
        capacity = 0
        distance = 0
    return capacity, distance


def add_reverse_direction(df):
    """
    Duplicate all entries of a DataFrame with a reverse index. The index must
    contain a dash between two sub-strings.
    """
    values = df.copy()

    def id_inverter(name):
        """Swap the sub-parts of a string left and right of a dash."""
        return "-".join([name.split("-")[1], name.split("-")[0]])

    df.index = df.index.map(id_inverter)

    return pd.DataFrame(pd.concat([values, df]))


def get_electrical_transmission_default(
    rmap=None, power_lines=None, both_directions=False
):
    """
    Creates a default set of transmission capacities, distance and efficiency.
    The map of the lines must exist in the geometries directory. The default
    values are infinity for the capacity, nan for the distance and 1 for the
    efficiency.

    Parameters
    ----------
    rmap : str
        The name of the transmission line map, that is part of deflex.
    power_lines : iterable[str]
        A list of names of transmission lines. All name must contain a dash
        between the id of the regions (FromRegion-ToRegion).
    both_directions : bool
        If True any line will be replicated in the reverse direction.

    Returns
    -------
    pd.DataFrame
        Transmission capacity, distance and efficiency between regions

    Examples
    --------
    >>> df=get_electrical_transmission_default('de21')
    >>> df.loc['DE10-DE12', 'capacity']
    inf
    >>> df.loc['DE10-DE12', 'distance']
    nan
    >>> df.loc['DE10-DE12', 'efficiency']
    1.0
    >>> len(df)
    39
    >>> len(get_electrical_transmission_default('de22'))
    40
    >>> len(get_electrical_transmission_default('de17'))
    31
    >>> len(get_electrical_transmission_default('de02'))
    1
    >>> my_lines=['reg1-reg2', 'reg2-reg3']
    >>> df=get_electrical_transmission_default(power_lines=my_lines)
    >>> df.loc['reg1-reg2', 'capacity']
    inf
    >>> df=get_electrical_transmission_default(power_lines=my_lines,
    ...                                          both_directions=True)
    >>> df.loc['reg2-reg1', 'capacity']
    inf

    """
    if power_lines is None:
        power_lines = pd.DataFrame(geometries.deflex_power_lines(rmap)).index

    df = pd.DataFrame()
    for l in power_lines:
        df.loc[l, "capacity"] = float("inf")
        df.loc[l, "distance"] = float("nan")
        df.loc[l, "efficiency"] = 1

    if both_directions is True:
        df = add_reverse_direction(df)
    return df


def get_electrical_transmission_renpass(both_directions=False):
    """
    Prepare the transmission capacity and distance between de21 regions from
    the renpass database. The original table of the reegis database is
    transferred to a csv file, which is part of the reegis package. As renpass
    is deprecated it will not change in the future. The index uses the format
    'region1-region2'. The distance is taken from centroid to centroid. By
    default every region pair exists only once. It is possible to get an entry
    in both directions if the parameter `both_directions` is set True.

    The capacity calculation is taken from the description of the renpass
    package [1]_. The data is taken from the renpass database [2]_.

    This function is only valid for the original renpass region set.

    Parameters
    ----------
    both_directions : bool
        If True any line will be replicated in the reverse direction.

    Returns
    -------
    pd.DataFrame
        Transmission capacity and distance between regions

    References
    ----------
    .. [1] Wiese, Frauke (2015). „Renewable Energy Pathways Simulation
        System – Open Source as an approach to meet challenges in energy
        modeling“. Diss. University of Flensburg. URL :
        https://www.reiner-lemoine-stiftung.de/pdf/dissertationen/Dissertation_Frauke_Wiese.pdf.
        (page 49)
    .. [2] Wiese, F.: Renpass - Renewable Energy Pathways Simulation System,
        https://github.com/fraukewiese/renpass

    Examples
    --------
    >>> df=get_electrical_transmission_renpass()
    >>> int(df.loc['DE11-DE17', 'capacity'])
    2506
    >>> int(df.loc['DE18-DE17', 'distance'])
    119
    >>> df.loc['DE08-DE06']
    capacity    7519.040402
    distance     257.000000
    Name: DE08-DE06, dtype: float64
    >>> df=get_electrical_transmission_renpass(both_directions=True)
    >>> int(df.loc['DE11-DE17', 'capacity'])
    2506
    >>> int(df.loc['DE17-DE11', 'capacity'])
    2506
    """
    f_security = cfg.get("transmission", "security_factor")
    current_max = cfg.get("transmission", "current_max")

    grid = pd.read_csv(
        os.path.join(
            cfg.get("paths", "data_deflex"),
            cfg.get("transmission", "transmission_renpass"),
        )
    )

    grid["capacity_calc"] = (
        grid.circuits
        * current_max
        * grid.voltage
        * f_security
        * math.sqrt(3)
        / 1000
    )

    pwr_lines = pd.DataFrame(geometries.deflex_power_lines())

    for l in pwr_lines.index:
        split = l.split("-")
        a = int("110{0}".format(split[0][2:]))
        b = int("110{0}".format(split[1][2:]))
        # print(a, b)
        cap1, dist1 = get_grid_capacity(grid, a, b)
        cap2, dist2 = get_grid_capacity(grid, b, a)

        if cap1 == 0 and cap2 == 0:
            pwr_lines.loc[l, "capacity"] = 0
            pwr_lines.loc[l, "distance"] = 0
        elif cap1 == 0:
            pwr_lines.loc[l, "capacity"] = cap2
            pwr_lines.loc[l, "distance"] = dist2
        elif cap2 == 0:
            pwr_lines.loc[l, "capacity"] = cap1
            pwr_lines.loc[l, "distance"] = dist1

    # plot_grid(pwr_lines)
    df = pwr_lines[["capacity", "distance"]]

    if both_directions is True:
        df = add_reverse_direction(df)

    return df


if __name__ == "__main__":
    pass
