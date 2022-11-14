from typing import Dict, List, Union

import ee
import pandas as pd
import plotly.graph_objects as go

from sankee.plotting import sankify


class Dataset:
    def __init__(
        self,
        name: str,
        id: str,
        band: str,
        labels: Dict[int, str],
        palette: Dict[int, str],
        years: List[int],
        nodata: Union[None, int] = None,
    ):
        """
        Parameters
        ----------
        name : str
            The name of the dataset.
        id : str
            The :code:`system:id` of the :code:`ee.ImageCollection` representing the dataset.
        band : str
            The name of the image band that contains class values.
        labels : dict
            A dictionary matching class values to their corresponding labels.
        palette : dict
            A dictionary matching class values to their corresponding hex colors.
        years : List[int]
            All years available in this dataset.
        nodata : int
            An optional no-data value to automatically remove when plotting.
        """
        self.name = name
        self.id = id
        self.band = band
        self.labels = labels
        self.palette = palette
        self.years = years
        self.nodata = nodata

        if sorted(labels.keys()) != sorted(palette.keys()):
            raise ValueError("Labels and palette must have the same keys.")

    def __repr__(self) -> str:
        return f"<Dataset: {self.name}>"

    @property
    def keys(self) -> List[int]:
        """Return the label keys of the dataset."""
        return list(self.labels.keys())

    @property
    def df(self) -> pd.DataFrame:
        """Return a Pandas dataframe describing the dataset parameters."""
        return pd.DataFrame(
            {"id": self.keys, "label": self.labels.values(), "color": self.palette.values()}
        )

    @property
    def collection(self) -> ee.ImageCollection:
        """The :code:`ee.ImageCollection` representing the dataset."""
        return ee.ImageCollection(self.id)

    def get_year(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. Set the metadata properties for visualization."""
        if year not in self.years:
            raise ValueError(
                f"This dataset does not include year `{year}`. Choose from {self.years}."
            )

        img = self.collection.filterDate(str(year), str(year + 1)).first()
        img = self.set_visualization_properties(img)

        if self.nodata is not None:
            img = img.updateMask(img.neq(self.nodata))

        return img.select(self.band)

    def set_visualization_properties(self, image: ee.Image) -> ee.Image:
        """Set the properties used by Earth Engine to automatically assign a palette to an image
        from this dataset."""
        return image.set(
            f"{self.band}_class_values",
            list(self.labels.keys()),
            f"{self.band}_class_palette",
            [c.replace("#", "") for c in self.palette.values()],
        )

    def list_years(self) -> ee.List:
        """Get an ee.List of all years in the collection."""
        return (
            self.collection.aggregate_array("system:time_start")
            .map(lambda ms: ee.Date(ms).get("year"))
            .distinct()
        )

    def sankify(
        self,
        years: List[int],
        region: ee.Geometry,
        max_classes: Union[None, int] = None,
        n: int = 500,
        title: Union[str, None] = None,
        scale: Union[int, None] = None,
        seed: int = 0,
        exclude: None = None,
        label_type: str = "class",
    ) -> go.Figure:
        """
        Generate an interactive Sankey plot showing land cover change over time from a series of
        years in the dataset.

        Parameters
        ----------
        years : List[int]
            The years to include in the plot. Select at least two unique years.
        region : ee.Geometry
            A region to generate samples within. The region must overlap all images.
        exclude : list[int], default None
            An optional list of pixel values to exclude from the plot. Excluded values must be raw
            pixel values rather than class labels. This can be helpful if the region is dominated by
            one or more unchanging classes and the goal is to visualize changes in smaller classes.
            No-data classes are always excluded automatically.
        max_classes : int, default None
            If a value is provided, small classes will be removed until max_classes remain. Class
            size is calculated based on total times sampled in the time series.
        n : int, default 500
            The number of sample points to randomly generate for characterizing all images. More
            samples will provide more representative data but will take longer to process.
        title : str, default None
            An optional title that will be displayed above the Sankey plot.
        scale : int, default None
            The scale in image units to perform sampling at. If none is provided, GEE will attempt
            to use the image's nominal scale, which may cause errors depending on the image
            projection.
        seed : int, default 0
            The seed value used to generate repeatable results during random sampling.
        exclude : None
            Unused parameter that will be removed in a future release.
        label_type : str, default "class"
            The type of label to display for each link, one of "class", "percent", or "count". Selecting
            "class" will use the class label, "percent" will use the proportion of sampled pixels in each
            class, and "count" will use the number of sampled pixels in each class.

        Returns
        -------
        plotly.graph_objs._figure.Figure
            An interactive Sankey plot.
        """
        if len(years) < 2:
            raise ValueError("Select at least two years.")
        if len(set(years)) != len(years):
            raise ValueError("Duplicate years found. Make sure all years are unique.")
        years = sorted(years)

        imgs = [self.get_year(year) for year in years]

        labels = self.labels.copy()
        palette = self.palette.copy()
        if self.nodata is not None:
            labels.pop(self.nodata)
            palette.pop(self.nodata)

        return sankify(
            image_list=imgs,
            label_list=years,
            labels=labels,
            band=self.band,
            palette=palette,
            region=region,
            max_classes=max_classes,
            n=n,
            title=title,
            scale=scale,
            seed=seed,
            label_type=label_type,
        )


class LCMS_Dataset(Dataset):
    def get_year(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. LCMS splits up each year into two images: CONUS
        and SEAK. This merges those into a single image."""
        super().get_year(year)

        collection = self.collection.filter(ee.Filter.eq("year", year))
        merged = collection.mosaic().select(self.band).clip(collection.geometry())

        props = collection.first().propertyNames().remove("study_area")
        merged = ee.Image(ee.Element.copyProperties(merged, collection.first(), props))

        merged = merged.setDefaultProjection("EPSG:5070")
        return merged


class CCAP_Dataset(Dataset):
    def get_year(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. C-CAP splits up each year into multiple images,
        so merge those and set the class value and palette metadata to allow automatic
        visualization."""
        super().get_year(year)

        imgs = self.collection.filterDate(str(year), str(year + 1))

        img = (
            imgs.mosaic()
            .set(
                {
                    "system:time_start": imgs.first().get("system:time_start"),
                    "system:time_end": imgs.first().get("system:time_end"),
                }
            )
            .clip(imgs.geometry())
            .setDefaultProjection("EPSG:5070")
        )

        img = self.set_visualization_properties(img)

        return img


LCMS_LU = LCMS_Dataset(
    name="LCMS LU - Land Change Monitoring System Land Use",
    id="USFS/GTAC/LCMS/v2021-7",
    band="Land_Use",
    labels={
        1: "Agriculture",
        2: "Developed",
        3: "Forest",
        4: "Non-Forest Wetland",
        5: "Other",
        6: "Rangeland or Pasture",
        7: "No Data",
    },
    palette={
        1: "#efff6b",
        2: "#ff2ff8",
        3: "#1b9d0c",
        4: "#97ffff",
        5: "#a1a1a1",
        6: "#c2b34a",
        7: "#1B1716",
    },
    years=tuple(range(1985, 2022)),
    nodata=7,
)

# https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5
LCMS_LC = LCMS_Dataset(
    name="LCMS LC - Land Change Monitoring System Land Cover",
    id="USFS/GTAC/LCMS/v2021-7",
    band="Land_Cover",
    labels={
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
        15: "No Data",
    },
    palette={
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
    },
    years=tuple(range(1985, 2022)),
    nodata=15,
)

NLCD = Dataset(
    name="NLCD - National Land Cover Database",
    id="USGS/NLCD_RELEASES/2019_REL/NLCD",
    band="landcover",
    labels={
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
    palette={
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
    },
    years=(2001, 2004, 2006, 2008, 2011, 2013, 2016, 2019),
    nodata=1,
)

# Kept for backwards compatibility with older `geemap` versions
NLCD2016 = NLCD

MODIS_LC_TYPE1 = Dataset(
    name="MCD12Q1 - MODIS Global Land Cover Type 1",
    id="MODIS/006/MCD12Q1",
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
        17: "Water",
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
    },
    years=tuple(range(2001, 2021)),
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE2 = Dataset(
    name="MCD12Q1 - MODIS Global Land Cover Type 2",
    id="MODIS/006/MCD12Q1",
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
    },
    years=tuple(range(2001, 2021)),
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE3 = Dataset(
    name="MCD12Q1 - MODIS Global Land Cover Type 3",
    id="MODIS/006/MCD12Q1",
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
        10: "Urban",
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
        10: "#a5a5a5",
    },
    years=tuple(range(2001, 2021)),
)

# https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
CGLS_LC100 = Dataset(
    name="CGLS - Copernicus Global Land Cover",
    id="COPERNICUS/Landcover/100m/Proba-V-C3/Global",
    band="discrete_classification",
    labels={
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
    palette={
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
    },
    years=tuple(range(2015, 2020)),
    nodata=0,
)

# https://samapriya.github.io/awesome-gee-community-datasets/projects/ccap_mlc/
CCAP_LC30 = CCAP_Dataset(
    name="C-CAP - NOAA Coastal Change Analysis Program 30m",
    id="projects/sat-io/open-datasets/NOAA/ccap_30m",
    band="b1",
    labels={
        1: "Unclassified (Cloud,Shadow etc)",
        2: "Impervious",
        3: "Developed Open Space",
        4: "Developed Open Space",
        5: "Developed Open Space",
        6: "Cultivated Land",
        7: "Pasture/Hay",
        8: "Grassland/Herbaceous",
        9: "Deciduous Forest",
        10: "Evergreen Forest",
        11: "Mixed Forest",
        12: "Scrub/Shrub",
        13: "Palustrine Forested Wetland",
        14: "Palustrine Scrub/Shrub Wetland",
        15: "Palustrine Emergent Wetland",
        16: "Estuarine Forested Wetland",
        17: "Estuarine Scrub/Shrub Wetland",
        18: "Estuarine Emergent Wetland",
        19: "Unconsolidated Shore",
        20: "Bare Land",
        21: "Open Water",
        22: "Palustrine Aquatic Bed",
        23: "Estuarine Aquatic Bed",
        24: "Tundra",
        25: "Snow/Ice",
    },
    palette={
        1: "#000000",
        2: "#f2f2f2",
        3: "#a899a8",
        4: "#8e757c",
        5: "#c1cc38",
        6: "#542100",
        7: "#c1a04f",
        8: "#f2ba87",
        9: "#00f200",
        10: "#003a00",
        11: "#07a03a",
        12: "#6d6d00",
        13: "#005b5b",
        14: "#f26d00",
        15: "#f200f2",
        16: "#3d003d",
        17: "#6d006d",
        18: "#af00af",
        19: "#00f2f2",
        20: "#f2f200",
        21: "#000077",
        22: "#0000f2",
        23: "#161616",
        24: "#161616",
        25: "#191919",
    },
    years=(1975, 1985, 1992, 1996, 2001, 2006, 2010, 2016),
    nodata=1,
)

# https://samapriya.github.io/awesome-gee-community-datasets/projects/ca_lc/
CA_FOREST_LC = Dataset(
    name="Canada Forested Ecosystem Land Cover",
    id="projects/sat-io/open-datasets/CA_FOREST_LC_VLCE2",
    band="b1",
    labels={
        0: "Unclassified",
        20: "Water",
        31: "Snow/Ice",
        32: "Rock/Rubble",
        33: "Exposed/Barren land",
        40: "Bryoids",
        50: "Shrubs",
        80: "Wetland",
        81: "Wetland-treed",
        100: "Herbs",
        210: "Coniferous",
        220: "Broadleaf",
        230: "Mixedwood",
    },
    palette={
        0: "#686868",
        20: "#3333ff",
        31: "#ccffff",
        32: "#cccccc",
        33: "#996633",
        40: "#ffccff",
        50: "#ffff00",
        80: "#993399",
        81: "#9933cc",
        100: "#ccff33",
        210: "#006600",
        220: "#00cc00",
        230: "#cc9900",
    },
    years=tuple(range(1984, 2020)),
    nodata=0,
)

LCMAP = Dataset(
    name="LCMAP - Landscape Change Monitoring, Assessment, and Projection",
    id="projects/sat-io/open-datasets/LCMAP/LCPRI",
    band="b1",
    labels={
        1: "Developed",
        2: "Cropland",
        3: "Grass/Shrub",
        4: "Tree Cover",
        5: "Water",
        6: "Wetland",
        7: "Ice/Snow",
        8: "Barren",
    },
    palette={
        1: "#E60000",
        2: "#A87000",
        3: "#E3E3C2",
        4: "#1D6330",
        5: "#476BA1",
        6: "#BAD9EB",
        7: "#FFFFFF",
        8: "#B3B0A3",
    },
    years=tuple(range(1985, 2021)),
)

CORINE = Dataset(
    name="CORINE - Coordination of Information on the Environment",
    id="COPERNICUS/CORINE/V20/100m",
    band="landcover",
    # Note: Labels are shortened for display
    labels={
        111: "Continuous urban",
        112: "Discontinuous urban",
        121: "Industrial/Commercial",
        122: "Road/Rail",
        123: "Ports",
        124: "Airports",
        131: "Mines",
        132: "Dump sites",
        133: "Construction",
        141: "Green urban",
        142: "Sport/Leisure facilities",
        211: "Non-irrigated arable",
        212: "Permanently irrigated",
        213: "Rice fields",
        221: "Vineyards",
        222: "Fruit plantations",
        223: "Olive groves",
        231: "Pastures",
        241: "Annual crops",
        242: "Complex cultivation",
        243: "Agriculture/Natural",
        244: "Agro-forestry",
        311: "Broad-leaved forest",
        312: "Coniferous forest",
        313: "Mixed forest",
        321: "Natural grasslands",
        322: "Moors and heathland",
        323: "Sclerophyllous vegetation",
        324: "Transitional woodland-shrub",
        331: "Beaches, dunes, sand",
        332: "Bare rocks",
        333: "Sparsely vegetated",
        334: "Burnt",
        335: "Glaciers/Perpetual snow",
        411: "Inland marshes",
        412: "Peat bogs",
        421: "Salt marshes",
        422: "Salines",
        423: "Intertidal flats",
        511: "Water courses",
        512: "Water bodies",
        521: "Coastal lagoons",
        522: "Estuaries",
        523: "Sea/Ocean",
    },
    palette={
        111: "#E6004D",
        112: "#FF0000",
        121: "#CC4DF2",
        122: "#CC0000",
        123: "#E6CCCC",
        124: "#E6CCE6",
        131: "#A600CC",
        132: "#A64DCC",
        133: "#FF4DFF",
        141: "#FFA6FF",
        142: "#FFE6FF",
        211: "#FFFFA8",
        212: "#FFFF00",
        213: "#E6E600",
        221: "#E68000",
        222: "#F2A64D",
        223: "#E6A600",
        231: "#E6E64D",
        241: "#FFE6A6",
        242: "#FFE64D",
        243: "#E6CC4D",
        244: "#F2CCA6",
        311: "#80FF00",
        312: "#00A600",
        313: "#4DFF00",
        321: "#CCF24D",
        322: "#A6FF80",
        323: "#A6E64D",
        324: "#A6F200",
        331: "#E6E6E6",
        332: "#CCCCCC",
        333: "#CCFFCC",
        334: "#000000",
        335: "#A6E6CC",
        411: "#A6A6FF",
        412: "#4D4DFF",
        421: "#CCCCFF",
        422: "#E6E6FF",
        423: "#A6A6E6",
        511: "#00CCF2",
        512: "#80F2E6",
        521: "#00FFA6",
        522: "#A6FFE6",
        523: "#E6F2FF",
    },
    years=(1986, 1999, 2005, 2011, 2017),
)


datasets = [
    LCMS_LC,
    LCMS_LU,
    NLCD,
    MODIS_LC_TYPE1,
    MODIS_LC_TYPE2,
    MODIS_LC_TYPE3,
    CGLS_LC100,
    CCAP_LC30,
    CA_FOREST_LC,
    LCMAP,
    CORINE,
]
