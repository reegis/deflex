# -*- coding: utf-8 -*-

"""
Reegis geometry tools.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import os
import warnings
from collections import namedtuple

try:
    import geopandas as gpd
except ModuleNotFoundError:
    gpd = None

from deflex import config as cfg


def deflex_regions(rmap=None, rtype="polygons"):
    """

    Parameters
    ----------
    rmap : str
        Name of the deflex map.
    rtype : str
        Type of the deflex map ('polygon', 'labels').

    Returns
    -------
    GeoDataFrame

    Examples
    --------
    >>> my_regions=deflex_regions('de17')
    >>> len(my_regions)
    17
    >>> my_regions.geometry.iloc[0].geom_type
    'MultiPolygon'
    >>> l=deflex_regions('de21', 'labels').loc['DE04', 'geometry']
    >>> l.geom_type
    'Point'
    >>> l.x
    13.2
    >>> l.y
    51.1
    >>> cfg.tmp_set('init', 'map', 'de22')
    >>> deflex_regions().name
    'de22'
    >>> list(deflex_regions('de02').index)
    ['DE01', 'DE02']
    """
    if gpd is not None:
        if rmap is None:
            rmap = cfg.get("init", "map")
        name = os.path.join(
            os.path.dirname(__file__),
            "data",
            "geometries",
            cfg.get("geometry", "deflex_polygon").format(
                suffix=".geojson", map=rmap, type=rtype
            ),
        )
        regions = gpd.read_file(name)
        regions.set_index("region", inplace=True)
        regions.name = rmap
    else:
        msg = ("\nTo read a deflex map you need to install 'geopandas' "
               "\n\n pip install geopandas\n")
        warnings.warn(msg, UserWarning)
        regions = None
    return regions


def deflex_power_lines(rmap=None, rtype="lines"):
    """

    Parameters
    ----------
    rmap : str
        Name of the deflex powerline map.
    rtype : str
        Type of the deflex powerline map ('lines', 'labels').

    Returns
    -------

    Examples
    --------
    >>> my_lines=deflex_power_lines('de17')
    >>> my_lines.geometry.iloc[0].geom_type
    'LineString'
    >>> len(my_lines)
    31
    >>> deflex_power_lines('de02').index[0]
    'DE01-DE02'
    >>> cfg.tmp_set('init', 'map', 'de21')
    >>> deflex_power_lines().name
    'de21'
    """
    if gpd is not None:
        if rmap is None:
            rmap = cfg.get("init", "map")
        name = os.path.join(
            os.path.dirname(__file__),
            "data",
            "geometries",
            cfg.get("geometry", "powerlines").format(
                map=rmap, type=rtype, suffix=".geojson"
            ),
        )
        lines = gpd.read_file(name)
        lines.set_index("name", inplace=True)
        lines.name = rmap
    else:
        msg = ("\nTo read a deflex map you need to install 'geopandas' "
               "\n\n pip install geopandas\n")
        warnings.warn(msg, UserWarning)
        lines = None
    return lines


def divide_off_and_onshore(regions):
    """
    Sort regions into onshore and offshore regions. A namedtuple with two list
    of regions ids will be returned. Fetch the `onshore` and `offshore`
    attribute of the named tuple to get the list.

    Parameters
    ----------
    regions : GeoDataFrame
        A region set with the region id in the index.

    Returns
    -------
    named tuple

    Examples
    --------
    >>> reg=deflex_regions('de02')
    >>> divide_off_and_onshore(reg).onshore
    ['DE01']
    >>> reg=deflex_regions('de21')
    >>> divide_off_and_onshore(reg).offshore
    ['DE19', 'DE20', 'DE21']
    """
    region_type = namedtuple("RegionType", "offshore onshore")
    regions_centroid = regions.copy()
    regions_centroid.geometry = regions_centroid.to_crs(
        epsg=25832
    ).centroid.to_crs(epsg="4326")

    germany_onshore = gpd.read_file(
        os.path.join(
            os.path.dirname(__file__),
            "data",
            "geometries",
            cfg.get("geometry", "germany_polygon"),
        )
    )

    gdf = gpd.sjoin(regions_centroid, germany_onshore, how="left", op="within")

    onshore = list(gdf.loc[~gdf.gid.isnull()].index)
    offshore = list(gdf.loc[gdf.gid.isnull()].index)

    return region_type(offshore=offshore, onshore=onshore)
