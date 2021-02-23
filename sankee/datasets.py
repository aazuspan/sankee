from enum import Enum


class Dataset:
    def __init__(self, title, band, labels, palette):
        """
        :param str band: The name of the image band that contains class values.
        :param dict labels: A dictionary matching class values to their corresponding labels.
        :param dict palette: A dictioanry matching class values to their corresponding hex colors.
        """
        self.title = title
        self.band = band
        self.labels = labels
        self.palette = palette

        assert self.labels.keys() == self.palette.keys(
        ), "Label keys must match palette keys!"

    def __repr__(self):
        return f"\n{self.title}\n{''.join(['-' for i in range(len(self.title))])}" \
            f"\nBand: {self.band}" \
            f"\nKeys: {self.keys()}" \
            f"\nLabels: {self.labels}" \
            f"\nPalette: {self.palette}"

    def keys(self):
        return list(self.labels.keys())

    def get_color(self, label):
        """
        Take a label and return the associated color from the palette.
        """
        label_key = [k for k, v in self.labels.items() if v == label][0]
        return self.palette[label_key]


class datasets(Dataset, Enum):
    NLCD2016 = ("NLCD 2016",
                "landcover", {
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
                }, {
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
                })

    MODIS_LC_TYPE1 = ("MODIS LC Type 1",
                      "LC_Type1",
                      {
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
                      {
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

    MODIS_LC_TYPE2 = ("MODIS LC Type 2",
                      "LC_Type2",
                      {
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
                      {
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

    MODIS_LC_TYPE3 = ("MODIS LC Type 3",
                      "LC_Type3",
                      {
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
                      {
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

    @classmethod
    def names(cls):
        """
        Return string names of all datasets.
        """
        return [e.name for e in cls]

    @classmethod
    def get(cls, i=None):
        """
        Return object at a given index i or return all if i is none. 
        """
        if i is not None:
            return list(cls)[i]

        return [e for e in cls]
