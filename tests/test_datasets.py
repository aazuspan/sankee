import re

import pytest
from numpy.testing import assert_equal
from pandas.testing import assert_series_equal

import sankee

from .data import TEST_REGION


def test_get_year_nlcd():
    dataset = sankee.datasets.NLCD
    img = dataset.get_year(2016)
    assert img.get("system:id").getInfo() == "USGS/NLCD_RELEASES/2019_REL/NLCD/2016"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_LCMS_LC():
    dataset = sankee.datasets.LCMS_LC
    img = dataset.get_year(2016)
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_LCMS_LU():
    dataset = sankee.datasets.LCMS_LU
    img = dataset.get_year(2016)
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
        assert img.get("system:id").getInfo() == "MODIS/061/MCD12Q1/2016_01_01"
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
        == "projects/sat-io/open-datasets/LCMAP/LCPRI/LCMAP_CU_2016_V13_LCPRI"
    )
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_CORINE():
    dataset = sankee.datasets.CORINE
    img = dataset.get_year(2011)
    # CORINE year ranges are confusing. The asset with the 2011 start
    # date is named 2012.
    assert img.get("system:id").getInfo() == "COPERNICUS/CORINE/V20/100m/2012"
    assert img.bandNames().getInfo() == [dataset.band]


def test_get_year_GLC_FCS30D():
    dataset_fine = sankee.datasets.GLC_FCS30D_FINE
    dataset_level1 = sankee.datasets.GLC_FCS30D_LEVEL1
    dataset_basic = sankee.datasets.GLC_FCS30D_BASIC
    img_fine = dataset_fine.get_year(2011)
    img_level1 = dataset_level1.get_year(2011)
    img_basic = dataset_basic.get_year(2011)
    assert img_fine.bandNames().getInfo() == [dataset_fine.band]
    assert img_level1.bandNames().getInfo() == [dataset_level1.band]
    assert img_basic.bandNames().getInfo() == [dataset_basic.band]


@pytest.mark.parametrize("dataset", sankee.datasets.datasets, ids=lambda d: d.name)
def test_years(dataset):
    """Check that the hard-coded dataset years match the Earth Engine catalog years."""
    assert dataset.years == tuple(dataset._list_years().getInfo())


def test_get_unsupported_year():
    """Test that unsupported years raise when the plot is generated."""
    expected = re.escape("This dataset does not include the year(s) [1850, 2150]")
    with pytest.raises(ValueError, match=expected):
        sankee.datasets.NLCD.sankify(years=[1850, 2150], region=TEST_REGION, n=1)


def test_get_invalid_years():
    """Single or duplicate years should raise errors."""
    with pytest.raises(ValueError, match="at least two years"):
        sankee.datasets.LCMS_LU.sankify(years=[2017], region=None)
    with pytest.raises(ValueError, match="Duplicate years"):
        sankee.datasets.LCMS_LU.sankify(years=[2017, 2017, 2018], region=None)


@pytest.mark.parametrize("dataset", sankee.datasets.datasets, ids=lambda d: d.name)
def test_nodata_is_valid(dataset):
    """Check that the nodata value, if present, has corresponding label and palette entries."""
    if dataset.nodata is not None:
        assert dataset.nodata in dataset.labels, f"The nodata value {dataset.nodata} has no label."
        assert (
            dataset.nodata in dataset.palette
        ), f"The nodata value {dataset.nodata} has no palette."


def test_sankify():
    """Make sure that sankify returns the same results whether called directly or from a Dataset."""
    dataset = sankee.datasets.LCMS_LC
    sankey1 = dataset.sankify(years=[1985, 2010], region=TEST_REGION, n=10, title="My plot!")

    img_list = [
        dataset.get_year(1985),
        dataset.get_year(2010),
    ]
    sankey2 = sankee.sankify(
        image_list=img_list,
        label_list=["1985", "2010"],
        band=dataset.band,
        region=TEST_REGION,
        n=10,
        labels=dataset.labels,
        palette=dataset.palette,
        title="My plot!",
    )

    params1 = sankey1._generate_plot_parameters()
    params2 = sankey2._generate_plot_parameters()

    for p1, p2 in zip(params1, params2):
        assert_series_equal(p1, p2)

    plot_data1 = sankey1.plot.data[0]
    plot_data2 = sankey2.plot.data[0]
    # Remove the unique IDs before testing equality
    plot_data1.pop("uid")
    plot_data2.pop("uid")

    assert_equal(plot_data1, plot_data2)
