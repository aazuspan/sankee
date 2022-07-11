from typing import List, Union

import ee
import pandas as pd

from sankee import utils


def collect_sankey_data(
    *,
    image_list: List[ee.Image],
    image_labels: List[str],
    region: ee.Geometry,
    band: str,
    n: int = 500,
    scale: Union[None, int] = None,
    seed: int = 0,
    include: Union[None, List[int]] = None,
    max_classes: Union[None, int] = None,
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
        features = [feat["properties"] for feat in samples.toList(samples.size()).getInfo()]
    except ee.EEException as e:
        if band in str(e):
            shared_bands = utils.get_shared_bands(image_list)
            raise ValueError(
                f"The band `{band}` was not found in all images. Choose from " f"{shared_bands}"
            ) from None
        elif "'count' must be positive" in str(e) and region.getInfo().get("type") == "Point":
            raise ValueError("The `region` must be a 2D geometry, not a Point.") from None
        else:
            raise e

    data = pd.DataFrame.from_dict(features).dropna()

    for image in image_labels:
        if image not in data.columns:
            raise ValueError(
                f"Valid samples were not found for image `{image}`. Check that the"
                " image overlaps the sampling region."
            )

    if include is not None:
        data = data[data.isin(include).all(axis=1)]

    if max_classes is not None:
        class_counts = data.melt().value.value_counts()
        keep_classes = class_counts[:max_classes].index.tolist()
        data = data[data.isin(keep_classes).all(axis=1)]

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
