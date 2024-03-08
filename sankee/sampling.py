from __future__ import annotations

import ee
import pandas as pd

from sankee import utils


class SamplingError(ValueError):
    """Error related to data sampling in Earth Engine."""


def handle_sampling_error(e: ee.EEException, band: str, image_list: list[ee.Image]) -> None:
    """Handle Earth Engine errors that occur during sampling by raising more specific errors."""
    msg = None

    if band in str(e):
        shared_bands = utils.get_shared_bands(image_list)
        msg = f"The band `{band}` was not found in all images. Choose from {shared_bands}."

    elif "Region must not be empty" in str(e):
        msg = (
            "The sample region is empty. Make sure to pass a valid geometry, feature, or "
            "non-empty collection."
        )

    if msg:
        raise SamplingError(msg) from None

    raise e


def generate_sample_data(
    *,
    image_list: list[ee.Image],
    image_labels: list[str],
    region: ee.Geometry,
    band: str,
    n: int = 500,
    scale: None | int = None,
    seed: int = 0,
    include: None | list[int] = None,
    max_classes: None | int = None,
) -> tuple[pd.DataFrame, ee.FeatureCollection]:
    """Take a list of images extract image values to each to random points. The image values will be
    stored in a property based on the image label. Then, the samples will be returned as a formated
    dataframe with one column for each image and one row for each sample point.
    """

    def extract_values_at_point(pt):
        for img, label in zip(image_list, image_labels):
            cover = img.reduceRegion(
                reducer=ee.Reducer.first(), geometry=pt.geometry(), scale=scale
            ).get(band)
            pt = ee.Feature(pt).set(label, cover)

        return pt

    points = ee.FeatureCollection.randomPoints(region=region, points=n, seed=seed)
    samples = points.map(extract_values_at_point)

    try:
        features = [feat["properties"] for feat in samples.toList(samples.size()).getInfo()]
    except ee.EEException as e:
        handle_sampling_error(e, band, image_list)

    data = pd.DataFrame.from_dict(features).dropna().astype(int)

    for image in image_labels:
        if image not in data.columns:
            raise SamplingError(
                f"Valid samples were not found for image `{image}`. Check that the"
                " image overlaps the sampling region."
            )

    # EE data gets sorted alpha, so re-sort columns to the image order. Run this after the column
    # check because this can add columns that were missing.
    data = data.reindex(image_labels, axis=1)

    if include is not None:
        data = data[data.isin(include).all(axis=1)]

    if max_classes is not None:
        class_counts = data.melt().value.value_counts()
        keep_classes = class_counts[:max_classes].index.tolist()
        data = data[data.isin(keep_classes).all(axis=1)]

    return data, samples
