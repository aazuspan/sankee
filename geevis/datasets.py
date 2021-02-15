class Dataset:
    def __init__(self, band, labels, palette):
        """
        :param str band: The name of the image band that contains class values.
        :param dict labels: A dictionary matching class values to their corresponding labels.
        :param dict palette: A dictioanry matching class values to their corresponding hex colors.
        """
        self.band = band
        self.labels = labels
        self.palette = palette

    def __repr__(self):
        return self.band


nlcd2016 = Dataset(
    band="landcover",
    labels={
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
        95: "Emergent herbaceous wetlands"
    },
    palette={
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
        95: "#6c9fb8"
    }
)

modis_LC_Type1 = Dataset(
    band="LC_Type1",
    labels={
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
    },
    palette={
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

modis_LC_Type2 = Dataset(
    band="LC_Type2",
    labels={
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
    palette={
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

modis_LC_Type3 = Dataset(
    band="LC_Type3",
    labels={
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
        10: "Urban"
    },
    palette={
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
        10: "#a5a5a5"
    }
)
