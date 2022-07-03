import ee

import sankee

ee.Initialize()

TEST_DATASET = sankee.datasets.LCMS_LU
TEST_IMAGE_LIST = [
    TEST_DATASET.get_year(1985),
    TEST_DATASET.get_year(2010),
]
TEST_IMAGE_LABELS = ["1985", "2010"]
TEST_REGION = ee.Geometry.Point([-122.192688, 46.25917]).buffer(1000)
