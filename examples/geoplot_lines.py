# -*- coding: utf-8 -*-

"""
Example of plotting data with lines.

* Map data to a line plot, using polygons as background.
* Use of a self-defined color map (can be replaced by predefined color maps)
  https://matplotlib.org/stable/tutorials/colors/colormaps.html
* Add description for values > 70

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import random

import pandas as pd
from matplotlib import patheffects
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from deflex import geometries

my_aspect = "equal"  # try "auto" instead

# Define figure
if my_aspect == "equal":
    size = (9, 6)
else:
    size = (6.5, 7)
ax = plt.figure(figsize=size).add_subplot(1, 1, 1)

# Fetch geometries
de21 = geometries.deflex_geo("de21")

# Plot background
regions = geometries.divide_off_and_onshore(de21.polygons)
ax = de21.polygons.loc[regions.onshore].plot(
    color="#aed8b4", edgecolor="#9aa1a9", ax=ax, aspect=my_aspect
)
ax = de21.polygons.loc[regions.offshore].plot(
    color="#bddce5", edgecolor="#9aa1a9", ax=ax, aspect=my_aspect
)

# Create Series with random data (replace this with your own data)
ratio = pd.Series(dtype="float64")
n = 0
for li in de21.lines.index:
    n += 1
    ratio[li] = random.random() * 100
    if n % 10 == 0:
        ratio[li] = 0
ratio.name = "value"

# Merge geometry and data
de21_lines = pd.concat([de21.lines, ratio], axis=1)

# Define color map
cmap_lines = LinearSegmentedColormap.from_list(
    "mycmap",
    [(0, "#aaaaaa"), (0.0001, "green"), (0.5, "yellow"), (1, "red")],
)

# Plot lines
ax = de21_lines.plot(
    "value", ax=ax, aspect=my_aspect, cmap=cmap_lines, legend=True
)

# Add labels for critical lines (> 70%)
for i, v in de21_lines.iterrows():
    if v["value"] > 70:
        ax.text(
            v["geometry"].centroid.x,
            v["geometry"].centroid.y,
            "{0} {1}".format(int(v["value"]), "%"),
            color="#000000",
            fontsize=9.5,
            ma="center",
            path_effects=[patheffects.withStroke(linewidth=3, foreground="w")],
        )

# Adjust and show plot
ax.axis("off")
plt.title("Percentage of something with random (!) data.")
plt.subplots_adjust(right=1.0, left=0.0, bottom=0.02, top=0.99)
plt.show()
