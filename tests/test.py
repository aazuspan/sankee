import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import unittest
import sankee
import ee

ee.Initialize()


TEST_REGION = ee.Geometry.Polygon([[[-130.07633697303308, 55.018689630077546],
                                    [-130.07633697303308, 54.340663930662444],
                                    [-128.81565582068933, 54.340663930662444],
                                    [-128.81565582068933, 55.018689630077546]]])
TEST_IMG_LIST = [ee.Image("MODIS/006/MCD12Q1/2001_01_01"), ee.Image(
    "MODIS/006/MCD12Q1/2010_01_01")]
TEST_LABEL_LIST = ["2001", "2010"]
TEST_DATASET = sankee.datasets.MODIS_LC_TYPE1
TEST_BAND = "LC_Type1"
TEST_LABELS = {
    1: "Evergreen conifer forest",
    2: "Evergreen broadleaf forest",
    3: "Deciduous conifer forest",
    4: "Deciduous broadleaf forest",
    5: "Mixed forest",
    6: "Closed shrubland",
    7: "Open shrubland",
    8: "Woody savanna",
    9: "Savanna",
    10: "Grassland",
    11: "Permanent wetland",
    12: "Cropland",
    13: "Urban",
    14: "Cropland and natural vegetation",
    15: "Permanent snow and ice",
    16: "Barren",
    17: "Water"
}
TEST_PALETTE = {
    1: "#086a10",
    2: "#dcd159",
    3: "#54a708",
    4: "#78d203",
    5: "#009900",
    6: "#c6b044",
    7: "#dcd159",
    8: "#dade48",
    9: "#fbff13",
    10: "#b6ff05",
    11: "#27ff87",
    12: "#c24f44",
    13: "#a5a5a5",
    14: "#ff6d4c",
    15: "#69fff8",
    16: "#f9ffa4",
    17: "#1c0dff",
}


class TestSankee(unittest.TestCase):
    def test_dropna(self):
        """
        Test that NA values will be dropped by _clean
        """
        test_input = pd.DataFrame({0: [0.0, np.nan], 1: [1, 2]})
        cleaned = sankee.core._clean(test_input, dropna=True)
        target = pd.DataFrame({0: [0.0], 1: [1]})

        assert_frame_equal(cleaned, target)

    def test_exclude(self):
        """
        Test that values are correctly excluded by _clean
        """
        test_input = pd.DataFrame({0: [0, 3], 1: [1, 2]})
        cleaned = sankee.core._clean(test_input, exclude=[3])
        target = pd.DataFrame({0: [0], 1: [1]})

        assert_frame_equal(cleaned, target)

    def test_max_classes(self):
        """
        Test that small classes are removed to match max_classes by _clean
        """
        test_input = pd.DataFrame({0: [0, 0, 1, 1, 2], 1: [0, 0, 1, 1, 2]})
        cleaned = sankee.core._clean(
            test_input, max_classes=2).reset_index(drop=True)
        target = pd.DataFrame(
            {0: [0, 0, 1, 1], 1: [0, 0, 1, 1]}).reset_index(drop=True)
        assert_frame_equal(cleaned, target)

    def test_missing_band(self):
        """
        If no dataset or band is provided, a ValueError should be raised.
        """
        with self.assertRaises(ValueError):
            sankee.core.sankify(TEST_IMG_LIST, TEST_REGION, TEST_LABEL_LIST,
                                dataset=None, band=None, labels=TEST_LABELS, palette=TEST_PALETTE)

    def test_missing_label(self):
        """
        If no dataset or label is provided, a ValueError should be raised.
        """
        with self.assertRaises(ValueError):
            sankee.core.sankify(TEST_IMG_LIST, TEST_REGION, TEST_LABEL_LIST,
                                dataset=None, band=TEST_BAND, labels=None, palette=TEST_PALETTE)

    def test_missing_palette(self):
        """
        If no dataset or palette is provided, a ValueError should be raised.
        """
        with self.assertRaises(ValueError):
            sankee.core.sankify(TEST_IMG_LIST, TEST_REGION, TEST_LABEL_LIST,
                                dataset=None, band=TEST_BAND, labels=TEST_LABELS, palette=None)

# TODO:
# Test uneven target and source classes
# Test reformatting using an example data input


if __name__ == "__main__":
    unittest.main()
