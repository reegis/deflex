# -*- coding: utf-8 -*-

"""
Plotting typical region maps of deflex.

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import os

from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import deflex.geometries
from deflex import geometries

# >>>> Change values here
file_format = "png"  # png, pdf, svg
plot_path = os.path.join(os.path.expanduser("~"), "deflex", "softwarex")
plot_file = "regions.{0}"
my_aspect = "equal"  # try "auto" instead
font_size = 16
# <<<<<< End

# Create directory if it does not exist
os.makedirs(plot_path, exist_ok=True)

# Define figure
plt.rcParams.update({"font.size": 16})

if my_aspect == "equal":
    size = (9, 6)
else:
    size = (6.5, 7)

f, ax = plt.subplots(1, 3, figsize=(15, 4))
cmap = LinearSegmentedColormap.from_list(
    "mycmap", [(0, "#a5bfdd"), (0.5, "red"), (1, "#badd69")]
)

geo = {}
i = 0
for name in ["de02", "de17", "de21"]:
    # Fetch geometries
    geo[name] = geometries.deflex_geo(name).polygons
    location = deflex.geometries.divide_off_and_onshore(geo[name])
    geo[name].loc[location.offshore, "color"] = 0
    geo[name].loc[location.onshore, "color"] = 1

    # Plot polygons
    geo[name].plot(
        "color",
        edgecolor="#9aa1a9",
        ax=ax[i],
        aspect=my_aspect,
        legend=False,
        cmap=cmap,
    )
    ax[i].axis("off")
    ax[i].set_title(name)
    i += 1

# Adjust save and show plot
plt.subplots_adjust(right=1.0, left=0.0, bottom=0.0, top=0.92, wspace=0)
plt.savefig(os.path.join(plot_path, plot_file.format(file_format)))
plt.show()
