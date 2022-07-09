import ee
import pytest

import sankee

ee.Initialize()


def test_get_year_nlcd():
    dataset = sankee.datasets.NLCD
    img = dataset.get_year(2016)
    assert img.get("system:id").getInfo() == "USGS/NLCD_RELEASES/2019_REL/NLCD/2016"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_LCMS_LC():
    dataset = sankee.datasets.LCMS_LC
    img = dataset.get_year(2016)
    assert img.get("system:id").getInfo() == "USFS/GTAC/LCMS/v2021-7/LCMS_CONUS_v2021-7_2016"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_LCMS_LU():
    dataset = sankee.datasets.LCMS_LU
    img = dataset.get_year(2016)
    assert img.get("system:id").getInfo() == "USFS/GTAC/LCMS/v2021-7/LCMS_CONUS_v2021-7_2016"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_CGLS():
    dataset = sankee.datasets.CGLS_LC100
    img = dataset.get_year(2016)
    assert img.get("system:id").getInfo() == "COPERNICUS/Landcover/100m/Proba-V-C3/Global/2016"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_MODIS():
    datasets = [
        sankee.datasets.MODIS_LC_TYPE1,
        sankee.datasets.MODIS_LC_TYPE2,
        sankee.datasets.MODIS_LC_TYPE3,
    ]

    for dataset in datasets:
        img = dataset.get_year(2016)
        assert img.get("system:id").getInfo() == "MODIS/006/MCD12Q1/2016_01_01"
        assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_CCAP():
    dataset = sankee.datasets.CCAP_LC30
    img = dataset.get_year(2016)
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_CA_FOREST():
    dataset = sankee.datasets.CA_FOREST_LC
    img = dataset.get_year(2016)
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_LCMAP():
    dataset = sankee.datasets.LCMAP
    img = dataset.get_year(2016)
    assert (
        img.get("system:id").getInfo()
        == "projects/sat-io/open-datasets/LCMAP/LCPRI/LCMAP_CU_2016_V12_LCPRI"
    )
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_CORINE():
    dataset = sankee.datasets.CORINE
    img = dataset.get_year(2011)
    # CORINE year ranges are confusing. The asset with the 2011 start
    # date is named 2012.
    assert img.get("system:id").getInfo() == "COPERNICUS/CORINE/V20/100m/2012"
    assert img.bandNames().getInfo() == [dataset.band]


def test_years():
    for dataset in sankee.datasets.datasets:
        assert dataset.years == tuple(dataset.list_years().getInfo())


def test_get_unsupported_year():
    with pytest.raises(ValueError, match="does not include year"):
        sankee.datasets.NLCD.get_year(2017)


def test_get_invalid_years():
    """Single or duplicate years should raise errors."""
    with pytest.raises(ValueError, match="at least two years"):
        sankee.datasets.LCMS_LU.sankify(years=[2017], region=None)
    with pytest.raises(ValueError, match="Duplicate years"):
        sankee.datasets.LCMS_LU.sankify(years=[2017, 2017, 2018], region=None)
