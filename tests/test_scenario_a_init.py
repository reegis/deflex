import os
import requests
from deflex import config as cfg


def test_downloaf_pp_from_osf():
    """Download pp-file from osf."""
    url = 'https://osf.io/qtc56/download'
    path = cfg.get('paths', 'powerplants')
    file = 'de21_pp.h5'
    filename = os.path.join(path, file)

    if not os.path.isfile(filename):
        req = requests.get(url)
        with open(filename, 'wb') as fout:
            fout.write(req.content)
