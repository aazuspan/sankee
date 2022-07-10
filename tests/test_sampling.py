import ee
import pytest

import sankee.sampling

from .data import TEST_DATASET, TEST_IMAGE_LABELS, TEST_IMAGE_LIST, TEST_REGION

ee.Initialize()


def test_collect_sankey_data():
    """Test that the correct number of rows and columns are sampled."""
    n = 10

    data = sankee.sampling.collect_sankey_data(
        image_list=TEST_IMAGE_LIST,
        image_labels=TEST_IMAGE_LABELS,
        region=TEST_REGION,
        band=TEST_DATASET.band,
        n=n,
    )

    assert len(data) == n
    assert data.columns.tolist() == TEST_IMAGE_LABELS


def test_collect_sankey_data_bad_band():
    """Test that an error is thrown when sampling an invalid band."""
    with pytest.raises(ValueError, match="band `foo` was not found"):
        sankee.sampling.collect_sankey_data(
            image_list=TEST_IMAGE_LIST,
            image_labels=TEST_IMAGE_LABELS,
            region=TEST_REGION,
            band="foo",
            n=10,
        )


def test_collect_sankey_data_bad_region():
    """Test that an error is thrown when sampling occurs outside the dataset."""
    with pytest.raises(ValueError, match="samples were not found"):
        sankee.sampling.collect_sankey_data(
            image_list=TEST_IMAGE_LIST,
            image_labels=TEST_IMAGE_LABELS,
            region=ee.Geometry.Point(0, 0).buffer(100),
            band=TEST_DATASET.band,
            n=10,
        )
