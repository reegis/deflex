# -*- coding: utf-8 -*-

"""
Reegis geometry tools.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

__all__ = ["deflex_geo", "divide_off_and_onshore"]

import os
from collections import namedtuple

import geopandas as gpd

from deflex import config as cfg


def deflex_geo(rmap):
    """
    Fetch default deflex geometries as a named tuple with the following fields:
     * polygons
     * lines
     * labels
     * line_labels

    Note that some fields might be None for some region sets.

    ----------
    rmap : str
        Name of the deflex map. Possible values are: de01, de02, de17, de21,
        de22

    Returns
    -------
    namedtuple

    Examples
    --------
    >>> de02 = deflex_geo("de02")
    >>> list(de02.polygons.index)
    ['DE01', 'DE02']
    >>> p = de02.labels.loc["DE01"].geometry
    >>> p.x, p.y
    (10.0, 51.6)
    >>> de02.lines.index
    Index(['DE01-DE02'], dtype='object', name='name')
    >>> de02.line_labels.iloc[0]
    gid                        246
    rotation                   -42
    geometry    POINT (7.61 53.78)
    Name: DE01-DE02, dtype: object
    >>> de01 = deflex_geo("de01")
    >>> print(de01.lines)
    None
    """
    geo = namedtuple(
        "geometry", ["polygons", "lines", "labels", "line_labels"]
    )
    polygons = deflex_regions(rmap, rtype="polygons")
    labels = deflex_regions(rmap, rtype="labels")
    lines = deflex_power_lines(rmap, rtype="lines")
    line_labels = deflex_power_lines(rmap, rtype="labels")
    return geo(
        polygons=polygons, labels=labels, lines=lines, line_labels=line_labels
    )


def deflex_regions(rmap=None, rtype="polygons"):
    """
    Get the geometries of deflex example regions.

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
    >>> deflex_regions(rmap="de22").name
    'de22'
    >>> list(deflex_regions('de02').index)
    ['DE01', 'DE02']
    >>> print(deflex_regions("de05"))
    None
    """
    name = os.path.join(
        os.path.dirname(__file__),
        "data",
        "geometries",
        cfg.get("geometry", "deflex_polygon").format(
            suffix=".geojson", map=rmap, type=rtype
        ),
    )

    if os.path.isfile(name):
        regions = gpd.read_file(name)
        regions.set_index("region", inplace=True)
        regions.name = rmap
    else:
        regions = None

    return regions


def deflex_power_lines(rmap=None, rtype="lines"):
    """
    Get the geometries of deflex example power lines.

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
    >>> deflex_power_lines(rmap="de21").name
    'de21'
    >>> print(deflex_regions("de05"))
    None
    """
    name = os.path.join(
        os.path.dirname(__file__),
        "data",
        "geometries",
        cfg.get("geometry", "powerlines").format(
            map=rmap, type=rtype, suffix=".geojson"
        ),
    )
    if os.path.isfile(name):
        lines = gpd.read_file(name)
        lines.set_index("name", inplace=True)
        lines.name = rmap
    else:
        lines = None

    return lines


def divide_off_and_onshore(regions):
    """
    Sort regions into onshore and offshore regions (Germany).

    A namedtuple with two list
    of regions ids will be returned. Fetch the `onshore` and `offshore`
    attribute of the named tuple to get the list.

    Parameters
    ----------
    regions : GeoDataFrame
        A region set with the region id in the index.

    Returns
    -------
    namedtuple

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

    gdf = gpd.sjoin(
        regions_centroid, germany_onshore, how="left", predicate="within"
    )

    onshore = list(gdf.loc[~gdf.gid.isnull()].index)
    offshore = list(gdf.loc[gdf.gid.isnull()].index)

    return region_type(offshore=offshore, onshore=onshore)
