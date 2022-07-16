import ee
import pytest

import sankee.sampling

from .data import TEST_DATASET, TEST_IMAGE_LABELS, TEST_IMAGE_LIST, TEST_REGION


def test_sample_data():
    """Test that the correct number of rows and columns are sampled."""
    n = 10
    data, samples = sankee.sampling.generate_sample_data(
        image_list=TEST_IMAGE_LIST,
        image_labels=TEST_IMAGE_LABELS,
        region=TEST_REGION,
        band=TEST_DATASET.band,
        scale=100,
        n=10,
    )

    assert len(data) == n
    assert data.columns.tolist() == TEST_IMAGE_LABELS
    assert samples.size().getInfo() == n


def test_sample_data_bad_band():
    """Test that an error is thrown when sampling an invalid band."""
    with pytest.raises(ValueError, match="band `foo` was not found"):
        sankee.sampling.generate_sample_data(
            image_list=TEST_IMAGE_LIST,
            image_labels=TEST_IMAGE_LABELS,
            region=TEST_REGION,
            band="foo",
            scale=100,
            n=10,
        )


def test_sample_data_bad_region():
    """Test that an error is thrown when sampling occurs outside the dataset."""
    with pytest.raises(ValueError, match="samples were not found"):
        sankee.sampling.generate_sample_data(
            image_list=TEST_IMAGE_LIST,
            image_labels=TEST_IMAGE_LABELS,
            region=ee.Geometry.Point(0, 0).buffer(100),
            band=TEST_DATASET.band,
            scale=100,
            n=10,
        )


def test_sample_data_point():
    """Test that an error is thrown when sampling occurs on an empty FeatureCollection."""
    with pytest.raises(ValueError, match="pass a 2D `region`"):
        sankee.sampling.generate_sample_data(
            image_list=TEST_IMAGE_LIST,
            image_labels=TEST_IMAGE_LABELS,
            region=ee.Geometry.Point([0, 0]),
            band=TEST_DATASET.band,
            scale=100,
        )
