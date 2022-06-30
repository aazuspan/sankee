from enum import Enum
import ee
import pandas as pd
import numpy as np
from sankee import utils


class Dataset:
    def __init__(self, collection_name, band, labels, palette):
        """
        Parameters
        ----------
        collection_name : str
            The :code:`system:id` of the :code:`ee.ImageCollection` representing the dataset.
        band : str 
            The name of the image band that contains class values.
        labels : dict 
            A dictionary matching class values to their corresponding labels.
        palette : dict 
            A dictionary matching class values to their corresponding hex colors.
        """
        self.collection_name = collection_name
        self.band = band
        self.labels = labels
        self.palette = palette

        if sorted(labels.keys()) != sorted(palette.keys()):
            raise ValueError("Labels and palette must have the same keys.")

    @property
    def keys(self):
        """Return the label keys of the dataset.
        """
        return list(self.labels.keys())

    @property
    def df(self):
        """Return a Pandas dataframe describing the dataset parameters.
        """
        return pd.DataFrame({"id": self.keys, "label": self.labels.values(), "color": self.palette.values()})

    @property
    def collection(self):
        """The :code:`ee.ImageCollection` representing the dataset.
        """
        return ee.ImageCollection(self.collection_name)

    def get_color(self, label):
        """Take a label and return the associated color from the dataset's palette.

        Parameters
        ----------
        label : str
            The label of a class in the dataset.

        Returns
        -------
        str
            The color associated with the label.
        """
        label_key = [k for k, v in self.labels.items() if v == label][0]
        return self.palette[label_key]

    def get_images(self, max_images=20):
        """
        List the names of the first n images in the dataset collection up to :code:`max_images`.

        Parameters
        ----------
        max_images : int, default 20
            The number of images to return.

        Returns
        -------
        List[str]
            A list of :code:`system:id` values for the first n images.
        """
        img_list = []
        for img in self.collection.toList(max_images).getInfo():
            try:
                img_list.append(img["id"])
            except KeyError:
                pass

        if len(img_list) == max_images:
            img_list.append("...")
        return img_list

    def check_is_complete(self):
        """
        Run tests to ensure parameters are complete. Raise exceptions if not.
        """
        if not self.band:
            raise ValueError("Provide dataset or band.")
        if not self.labels:
            raise ValueError("Provide dataset or labels.")
        if not self.palette:
            raise ValueError("Provide dataset or palette.")
        return 0

    def check_data_is_compatible(self, data):
        """
        Check for values that are present in data and are not present in labels or palette and raise an error if any are
        found.
        """
        missing_keys = []

        for _, col in data.iteritems():
            missing_keys += utils.get_missing_keys(col, self.labels)

        if missing_keys:
            raise Exception(
                f"The following values are present in the data and undefined in the labels and palette: {np.unique(missing_keys)}"
            )


def convert_NLCD1992_to_2016(img):
    """
    Reclassify NLCD 1992 data to match the NLCD 2016 legend. Direct comparisons between NLCD 1992 and later years
    should still be done with caution due to differences in the classification method, but make classes roughly
    comparable.

    Parameters
    ----------
    img : ee.Image
        An NLCD 1992 Land Cover image.

    Returns
    -------
    ee.Image
        The input images with values cross-walked to the NLCD 2016 key.

    References
    ----------
    See USGS Open-File Report 2008-1379 for a detailed discussion and for the crosswalk table used.
    https://pubs.usgs.gov/of/2008/1379/pdf/ofr2008-1379.pdf
    """
    img = img.select("landcover")

    img = (img
        .where(img.eq(85), 21)
        .where(img.eq(21), 22)
        .where(img.eq(22), 23)
        .where(img.eq(23), 24)
        .where(img.eq(32), 31)
        .where(img.eq(33), 31)
        .where(img.eq(42), 42)
        .where(img.eq(51), 52)
        .where(img.eq(61), 82)
        .where(img.eq(83), 82)
        .where(img.eq(84), 82)
        .where(img.eq(91), 90)
        .where(img.eq(92), 95)
    )

    return img


# https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5
LCMS_LU = Dataset(
    collection_name="USFS/GTAC/LCMS/v2021-7",
    band="Land_Use",
    labels = {
            1: "Agriculture",
            2: "Developed",
            3: "Forest",
            4: "Non-Forest Wetland",
            5: "Other",
            6: "Rangeland or Pasture",
            7: "No Data"
        },
    palette = {
            1: "#efff6b",
            2: "#ff2ff8", 
            3: "#1b9d0c",
            4: "#97ffff",
            5: "#a1a1a1",
            6: "#c2b34a",
            7: "#1B1716",
        }
)

# https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5
LCMS_LC = Dataset(
    collection_name="USFS/GTAC/LCMS/v2021-7",
    band="Land_Cover",
    labels = {
            1: "Trees",
            2: "Tall Shrubs & Trees Mix",
            3: "Shrubs & Trees Mix",
            4: "Grass/Forb/Herb & Trees Mix",
            5: "Barren & Trees Mix",
            6: "Tall Shrubs",
            7: "Shrubs",
            8: "Grass/Forb/Herb & Shrubs Mix",
            9: "Barren & Shrubs Mix",
            10: "Grass/Forb/Herb",
            11: "Barren & Grass/Forb/Herb Mix",
            12: "Barren or Impervious",
            13: "Snow or Ice",
            14: "Water",
            15: "No Data"
        },
    palette = {
            1: "#005e00", 
            2: "#008000", 
            3: "#00cc00", 
            4: "#b3ff1a", 
            5: "#99ff99", 
            6: "#b30088", 
            7: "#e68a00", 
            8: "#ffad33", 
            9: "#ffe0b3", 
            10: "#ffff00", 
            11: "#AA7700", 
            12: "#d3bf9b", 
            13: "#ffffff", 
            14: "#4780f3", 
            15: "#1B1716", 
        }
)

# https://developers.google.com/earth-engine/datasets/catalog/USGS_NLCD_RELEASES_2019_REL_NLCD
NLCD = Dataset(
    collection_name="USGS/NLCD_RELEASES/2019_REL/NLCD",
    band="landcover",
    labels = {
            1: "No data",
            11: "Open water",
            12: "Perennial ice/snow",
            21: "Developed, open space",
            22: "Developed, low intensity",
            23: "Developed, medium intensity",
            24: "Developed, high intensity",
            31: "Barren land (rock/sand/clay)",
            41: "Deciduous forest",
            42: "Evergreen forest",
            43: "Mixed forest",
            51: "Dwarf scrub",
            52: "Shrub/scrub",
            71: "Grassland/herbaceous",
            72: "Sedge/herbaceous",
            73: "Lichens",
            74: "Moss",
            81: "Pasture/hay",
            82: "Cultivated crops",
            90: "Woody wetlands",
            95: "Emergent herbaceous wetlands",
    },
    palette = {
            1: "#000000",
            11: "#466b9f",
            12: "#d1def8",
            21: "#dec5c5",
            22: "#d99282",
            23: "#eb0000",
            24: "#ab0000",
            31: "#b3ac9f",
            41: "#68ab5f",
            42: "#1c5f2c",
            43: "#b5c58f",
            51: "#af963c",
            52: "#ccb879",
            71: "#dfdfc2",
            72: "#d1d182",
            73: "#a3cc51",
            74: "#82ba9e",
            81: "#dcd939",
            82: "#ab6c28",
            90: "#b8d9eb",
            95: "#6c9fb8",
    }
)

# TODO: Deprecate this somehow
NLCD2016 = NLCD

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE1 = Dataset(
    collection_name="MODIS/006/MCD12Q1",
    band="LC_Type1",
    labels = {
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
    },
    palette = {
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
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE2 = Dataset(
    collection_name="MODIS/006/MCD12Q1",
    band="LC_Type2",
    labels = {
        0: "Water",
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
        15: "Barren",
    },
    palette = {
        0: "#1c0dff",
        1: "#05450a",
        2: "#086a10",
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
        15: "#f9ffa4",
    }
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE3 = Dataset(
    collection_name="MODIS/006/MCD12Q1",
    band="LC_Type3",
    labels = {
        0: "Water",
        1: "Grassland",
        2: "Shrubland",
        3: "Crops",
        4: "Savannas",
        5: "Evergreen broadleaf",
        6: "Deciduous broadleaf",
        7: "Evergreen conifer",
        8: "Deciduous conifer",
        9: "Barren",
        10: "Urban",
    },
    palette = {
        0: "#1c0dff",
        1: "#b6ff05",
        2: "#dcd159",
        3: "#c24f44",
        4: "#fbff13",
        5: "#086a10",
        6: "#78d203",
        7: "#05450a",
        8: "#54a708",
        9: "#f9ffa4",
        10: "#a5a5a5",
    }
)

# https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
CGLS_LC100 = Dataset(
    collection_name="COPERNICUS/Landcover/100m/Proba-V-C3/Global",
    band="discrete_classification",
    labels = {
        0: "Unknown",
        20: "Shrubs",
        30: "Herbaceous vegetation",
        40: "Cultivated",
        50: "Urban",
        60: "Bare",
        70: "Snow and ice",
        80: "Water body",
        90: "Herbaceous wetland",
        100: "Moss and lichen",
        111: "Closed forest, evergreen conifer",
        112: "Closed forest, evergreen broad leaf",
        113: "Closed forest, deciduous conifer",
        114: "Closed forest, deciduous broad leaf",
        115: "Closd forest, mixed",
        116: "Closed forest, other",
        121: "Open forest, evergreen conifer",
        122: "Open forest, evergreen broad leaf",
        123: "Open forest, deciduous conifer",
        124: "Open forest, deciduous broad leaf",
        125: "Open forest, mixed",
        126: "Open forest, other",
        200: "Ocean",
    },
    palette = {
        0: "#282828",
        20: "#FFBB22",
        30: "#FFFF4C",
        40: "#F096FF",
        50: "#FA0000",
        60: "#B4B4B4",
        70: "#F0F0F0",
        80: "#0032C8",
        90: "#0096A0",
        100: "#FAE6A0",
        111: "#58481F",
        112: "#009900",
        113: "#70663E",
        114: "#00CC00",
        115: "#4E751F",
        116: "#007800",
        121: "#666000",
        122: "#8DB400",
        123: "#8D7400",
        124: "#A0DC00",
        125: "#929900",
        126: "#648C00",
        200: "#000080",
    }
)

_all = [
    LCMS_LC,
    LCMS_LU,
    NLCD,
    MODIS_LC_TYPE1,
    MODIS_LC_TYPE2,
    MODIS_LC_TYPE3,
    CGLS_LC100,
]

# For backwards compatibility
names = lambda : [d.collection_name for d in _all]