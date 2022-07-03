import unittest

import ee
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import sankee

ee.Initialize()


TEST_REGION = ee.Geometry.Polygon(
    [
        [
            [-130.07633697303308, 55.018689630077546],
            [-130.07633697303308, 54.340663930662444],
            [-128.81565582068933, 54.340663930662444],
            [-128.81565582068933, 55.018689630077546],
        ]
    ]
)
TEST_IMG_LIST = [ee.Image("MODIS/006/MCD12Q1/2001_01_01"), ee.Image("MODIS/006/MCD12Q1/2010_01_01")]
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
    17: "Water",
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
TEST_DATA = pd.DataFrame(
    {
        "start": [1, 1, 1, 2, 2, 4],
        "end": [1, 1, 1, 2, 3, 4],
    }
)

THREE_PERIOD_TEST_DATA = pd.DataFrame(
    {
        "start": [1, 1, 1, 2, 2, 4],
        "mid": [3, 3, 1, 1, 2, 4],
        "end": [1, 1, 1, 2, 3, 4],
    }
)


class TestUtils(unittest.TestCase):
    def test_drop_small_classes(self):
        """
        Test that the classes with the fewest observations are dropped by drop_small_classes
        """
        dropped = sankee.utils.drop_small_classes(TEST_DATA, keep_classes=1)
        target = pd.DataFrame({"start": [1, 1, 1], "end": [1, 1, 1]})
        assert_frame_equal(dropped, target)

    def test_get_missing_keys(self):
        """
        Test that a missing key is found from a dictionary.
        """
        test_dict = {"a": 0, "b": 1, "c": 2}
        test_keys = ["a", "b", "c", "d"]
        missing_keys = sankee.utils.get_missing_keys(test_keys, test_dict)
        self.assertListEqual(missing_keys, ["d"])

    def test_normalize_change_sum_is_correct(self):
        """
        Test that the sum of normalized changes is equal to the number of input classes.
        """
        test_data = pd.DataFrame(
            {
                "source": [0, 1, 1, 2, 3, 4, 4],
                "target": [5, 6, 7, 7, 8, 9, 10],
                "value": [1, 2, 1, 3, 1, 5, 9],
            }
        )

        num_classes = test_data.source.unique().size
        normalized_values = sankee.utils.normalized_change(test_data, "source", "value").values
        self.assertAlmostEqual(num_classes, normalized_values.sum())


class TestSankee(unittest.TestCase):
    def test_dropna(self):
        """
        Test that NA values will be dropped by _clean_data
        """
        test_input = pd.DataFrame({0: [0.0, np.nan, 2.0], 1: [1, 2, 3]})
        cleaned = sankee.core._clean_data(test_input)
        target = pd.DataFrame({0: [0.0, 2.0], 1: [1, 3]})

        self.assertTrue(np.array_equal(cleaned, target))

    def test_exclude(self):
        """
        Test that values are correctly excluded by _clean_data
        """
        cleaned = sankee.core._clean_data(TEST_DATA, exclude=[2])
        target = pd.DataFrame(
            {
                "start": [1, 1, 1, 4],
                "end": [1, 1, 1, 4],
            }
        )

        self.assertTrue(np.array_equal(cleaned, target))

    def test_max_classes(self):
        """
        Test that small classes are removed to match max_classes by _clean_data
        """
        cleaned = sankee.core._clean_data(TEST_DATA, max_classes=2)
        target = pd.DataFrame(
            {
                "start": [1, 1, 1, 2],
                "end": [1, 1, 1, 2],
            }
        )

        self.assertTrue(np.array_equal(cleaned, target))

    def test_mismatched_label_list(self):
        """
        If the label list is a different length than the image list, a ValueError should be raised.
        """
        with self.assertRaisesRegex(ValueError, "number of labels must match"):
            sankee.sankify(
                image_list=TEST_IMG_LIST,
                region=TEST_REGION,
                label_list=["2001", "2010", "2020"],
                band=TEST_BAND,
                labels=TEST_LABELS,
                palette=TEST_PALETTE,
            )
        with self.assertRaisesRegex(ValueError, "number of labels must match"):
            sankee.sankify(
                image_list=TEST_IMG_LIST,
                region=TEST_REGION,
                label_list=["2001"],
                band=TEST_BAND,
                labels=TEST_LABELS,
                palette=TEST_PALETTE,
            )

    def test_duplicate_label_list(self):
        """
        Duplicate values in the label list should raise an error
        """
        with self.assertRaisesRegex(ValueError, "must be unique"):
            sankee.sankify(
                image_list=TEST_IMG_LIST,
                region=TEST_REGION,
                label_list=["2001", "2001"],
                band=TEST_BAND,
                labels=TEST_LABELS,
                palette=TEST_PALETTE,
            )

    def test_bad_band(self):
        """
        If a band name is passed to _collect_sample_data and it's not in the image, a ValueError should be raised.
        """
        labeled = sankee.core._label_images(TEST_IMG_LIST, TEST_LABEL_LIST)
        with self.assertRaises(ValueError):
            sankee.core._collect_sample_data(
                labeled, region=TEST_REGION, band="bad_band", label_list=TEST_LABEL_LIST
            )

    def test_format_for_sankey_with_two_periods(self):
        """
        Test that mock table data for a two-period time series is correctly reformatted for Sankey plotting.
        """
        (
            node_labels,
            link_labels,
            node_palette,
            link_palette,
            label,
            source,
            target,
            value,
        ) = sankee.core._format_for_sankey(TEST_DATA, TEST_LABELS, TEST_PALETTE)

        self.assertEqual(node_labels, ["start", "start", "start", "end", "end", "end", "end"])
        self.assertEqual(
            link_labels,
            [
                r"100% of Evergreen conifer forest remained Evergreen conifer forest",
                r"50% of Evergreen broadleaf forest remained Evergreen broadleaf forest",
                r"50% of Evergreen broadleaf forest became Deciduous conifer forest",
                r"100% of Deciduous broadleaf forest remained Deciduous broadleaf forest",
            ],
        )
        self.assertEqual(
            node_palette,
            ["#086a10", "#dcd159", "#78d203", "#086a10", "#dcd159", "#54a708", "#78d203"],
        )
        self.assertEqual(link_palette, ["#086a10", "#dcd159", "#dcd159", "#78d203"])
        self.assertEqual(
            label,
            [
                "Evergreen conifer forest",
                "Evergreen broadleaf forest",
                "Deciduous broadleaf forest",
                "Evergreen conifer forest",
                "Evergreen broadleaf forest",
                "Deciduous conifer forest",
                "Deciduous broadleaf forest",
            ],
        )
        self.assertEqual(source, [0, 1, 1, 2])
        self.assertEqual(target, [3, 4, 5, 6])
        self.assertEqual(value, [3, 1, 1, 1])

    def test_format_for_sankey_with_three_periods(self):
        """
        Test that mock table data for a three-period time series is correctly reformatted for Sankey plotting.
        """
        (
            node_labels,
            link_labels,
            node_palette,
            link_palette,
            label,
            source,
            target,
            value,
        ) = sankee.core._format_for_sankey(THREE_PERIOD_TEST_DATA, TEST_LABELS, TEST_PALETTE)

        self.assertEqual(
            node_labels,
            ["start", "start", "start", "mid", "mid", "mid", "mid", "end", "end", "end", "end"],
        )
        self.assertEqual(
            link_labels,
            [
                "33% of Evergreen conifer forest remained Evergreen conifer forest",
                "67% of Evergreen conifer forest became Deciduous conifer forest",
                "50% of Evergreen broadleaf forest became Evergreen conifer forest",
                "50% of Evergreen broadleaf forest remained Evergreen broadleaf forest",
                "100% of Deciduous broadleaf forest remained Deciduous broadleaf forest",
                "50% of Evergreen conifer forest remained Evergreen conifer forest",
                "50% of Evergreen conifer forest became Evergreen broadleaf forest",
                "100% of Evergreen broadleaf forest became Deciduous conifer forest",
                "100% of Deciduous conifer forest became Evergreen conifer forest",
                "100% of Deciduous broadleaf forest remained Deciduous broadleaf forest",
            ],
        )
        self.assertEqual(
            node_palette,
            [
                "#086a10",
                "#dcd159",
                "#78d203",
                "#54a708",
                "#086a10",
                "#dcd159",
                "#78d203",
                "#086a10",
                "#dcd159",
                "#54a708",
                "#78d203",
            ],
        )
        self.assertEqual(
            link_palette,
            [
                "#086a10",
                "#086a10",
                "#dcd159",
                "#dcd159",
                "#78d203",
                "#086a10",
                "#086a10",
                "#dcd159",
                "#54a708",
                "#78d203",
            ],
        )
        self.assertEqual(
            label,
            [
                "Evergreen conifer forest",
                "Evergreen broadleaf forest",
                "Deciduous broadleaf forest",
                "Deciduous conifer forest",
                "Evergreen conifer forest",
                "Evergreen broadleaf forest",
                "Deciduous broadleaf forest",
                "Evergreen conifer forest",
                "Evergreen broadleaf forest",
                "Deciduous conifer forest",
                "Deciduous broadleaf forest",
            ],
        )
        self.assertEqual(source, [0, 0, 1, 1, 2, 4, 4, 5, 3, 6])
        self.assertEqual(target, [4, 3, 4, 5, 6, 7, 8, 9, 7, 10])
        self.assertEqual(value, [1, 2, 1, 1, 1, 1, 1, 1, 2, 1])

    def test_build_labels(self):
        """
        The _build_labels function should not allow duplicate labels within periods
        but should allow duplicate labels between periods.
        """
        data = pd.DataFrame(
            {
                "source": [0, 0, 1, 2],
                "source_label": ["zero", "zero", "one", "two"],
                "target": [3, 3, 4, 5],
                "target_label": ["zero", "zero", "four", "five"],
            }
        )

        labels = sankee.core._build_labels(data)

        self.assertListEqual(labels, ["zero", "one", "two", "zero", "four", "five"])

    def test_build_link_label(self):
        """
        Test that descriptive link labels are built correctly whether classes
        changed or remained the same.
        """
        change_df = pd.DataFrame(
            {"source_label": ["a", "a"], "target_label": ["b", "a"], "change": [0.8, 0.2]}
        )
        link_labels = sankee.core._build_link_labels(change_df)

        self.assertEqual(link_labels[0], "80% of a became b")
        self.assertEqual(link_labels[1], "20% of a remained a")

    def test_build_node_labels(self):
        """
        The _build_node_labels function should return one period label for each
        unique value in the source and target fields.
        """
        data = pd.DataFrame(
            {
                "source": [0, 0, 0, 0],
                "source_period": ["start", "start", "start", "start"],
                "target": [1, 2, 3, 4],
                "target_period": ["end", "end", "end", "end"],
            }
        )
        node_labels = sankee.core._build_node_labels(data)
        self.assertListEqual(node_labels, ["start", "end", "end", "end", "end"])


if __name__ == "__main__":
    unittest.main()
