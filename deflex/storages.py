# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os

# External libraries
import pandas as pd
import numpy as np
from shapely.geometry import Point

# internal modules
import reegis_tools.config as cfg
import reegis_tools.geometries
import deflex.geometries


def lat_lon2point(df):
    """Create shapely point object of latitude and longitude."""
    return Point(df['Wikipedia', 'longitude'], df['Wikipedia', 'latitude'])


def pumped_hydroelectric_storage():
    phes_raw = pd.read_csv(os.path.join(cfg.get('paths', 'static_sources'),
                                        cfg.get('storages', 'hydro_storages')),
                           header=[0, 1]).sort_index(1)

    phes = phes_raw['dena'].copy()

    # add geometry from wikipedia
    phes_raw = phes_raw[phes_raw['Wikipedia', 'longitude'].notnull()]
    phes['geom'] = (phes_raw.apply(lat_lon2point, axis=1))

    # add energy from ZFES because dena values seem to be corrupted
    phes['energy'] = phes_raw['ZFES', 'energy']
    phes['name'] = phes_raw['ZFES', 'name']

    # TODO: 0.75 should come from config file
    phes['efficiency'] = phes['efficiency'].fillna(0.75)

    # remove storages that do not have an entry for energy capacity
    phes = phes[phes.energy.notnull()]

    # create a GeoDataFrame with geom column
    gphes = reegis_tools.geometries.Geometry(name='phes', df=phes)
    gphes.create_geo_df()

    # get model region polygons
    region_name = '{0}_region'.format(cfg.get('init', 'map'))
    deflex_regions = deflex.geometries.deflex_regions()

    gphes.gdf = reegis_tools.geometries.spatial_join_with_buffer(
        gphes, deflex_regions, name=region_name)

    # create turbine and pump efficiency from overall efficiency (square root)
    # multiply the efficiency with the capacity to group with "sum()"
    gphes.gdf['pump_eff'] = np.sqrt(gphes.gdf.efficiency) * gphes.gdf.pump
    gphes.gdf['turbine_eff'] = (
            np.sqrt(gphes.gdf.efficiency) * gphes.gdf.turbine)

    phes = gphes.gdf.groupby(region_name).sum()

    # divide by the capacity to get the efficiency and remove overall
    # efficiency
    phes['pump_eff'] = phes.pump_eff / phes.pump
    phes['turbine_eff'] = phes.turbine_eff / phes.turbine
    del phes['efficiency']

    return phes


if __name__ == "__main__":
    print(pumped_hydroelectric_storage())
