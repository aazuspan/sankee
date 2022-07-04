from typing import List, Union

import ee
import pandas as pd


def collect_sankey_data(
    *,
    image_list: List[ee.Image],
    image_labels: List[str],
    region: ee.Geometry,
    band: str,
    n: int = 500,
    scale: Union[None, int] = None,
    seed: int = 0,
) -> pd.DataFrame:
    """Collect all the data needed to generate a Sankey diagram from a list of images.

    The resulting dataframe has one column for each image and one row for each sample point.
    """
    points = ee.FeatureCollection.randomPoints(region=region, points=n, seed=seed)
    samples = _extract_values(
        image_list=image_list,
        image_labels=image_labels,
        sample_points=points,
        band=band,
        scale=scale,
    )

    try:
        data = pd.DataFrame.from_dict(
            [feat["properties"] for feat in samples.toList(samples.size()).getInfo()]
        ).dropna()
    except ee.EEException as e:
        if band in str(e):
            raise ValueError(f"The band `{band}` was not found in all images.") from None
        else:
            raise e

    for image in image_labels:
        if image not in data.columns:
            raise ValueError(
                f"Valid samples were not found for image `{image}`. Check that the"
                " image overlaps the sampling region."
            )

    return data


def _extract_values(
    *,
    image_list: List[ee.Image],
    image_labels: List[str],
    sample_points: ee.FeatureCollection,
    band: str,
    scale: int,
) -> ee.FeatureCollection:
    """Take a list of images and a collection of sample points and extract image values to each
    sample point. The image values will be stored in a property based on the image label.
    """

    def extract_values_at_point(pt):
        for img, label in zip(image_list, image_labels):
            cover = img.reduceRegion(
                reducer=ee.Reducer.first(), geometry=pt.geometry(), scale=scale
            ).get(band)
            pt = ee.Feature(pt).set(label, cover)

        return pt

    return sample_points.map(extract_values_at_point)
