# -*- coding: utf-8 -*-

"""
Example of plotting data with lines.

* Map data to a region (polygon) plot
* Use of a predefined color map
  https://matplotlib.org/stable/tutorials/colors/colormaps.html
* Add description for values > 0

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import random

import pandas as pd
from matplotlib import patheffects
from matplotlib import pyplot as plt

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

# Create Series with random data (replace this with your own data)
ratio = pd.Series(dtype="float64")
n = 0
for li in de21.polygons.index:
    n += 1
    ratio[li] = random.random() * 100
    if n % 10 == 0:
        ratio[li] = 0
ratio.name = "value"

# Merge geometry and data
de21_poly = pd.concat([de21.polygons, ratio], axis=1)

# Colormaps (cmap):
# https://matplotlib.org/stable/tutorials/colors/colormaps.html

# Plot polygons
ax = de21_poly.plot(
    "value",
    edgecolor="#9aa1a9",
    ax=ax,
    aspect=my_aspect,
    legend=True,
    cmap="coolwarm",
)

# Add labels for regions > 30%
for i, v in de21_poly.iterrows():
    if v["value"] > 0:
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
