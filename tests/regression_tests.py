from nose.tools import eq_
from deflex import geometries


def test_prevent_mutable_region_object():
    reg = geometries.deflex_regions('de21')
    eq_(reg.geometry.iloc[0].geom_type, 'MultiPolygon')
    eq_(geometries.divide_off_and_onshore(reg).offshore,
        ['DE19', 'DE20', 'DE21'])
    eq_(reg.geometry.iloc[0].geom_type, 'MultiPolygon')