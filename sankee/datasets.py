from __future__ import annotations

from warnings import warn

import ee
import pandas as pd

from sankee import themes
from sankee.plotting import SankeyPlot, sankify


class Dataset:
    def __init__(
        self,
        name: str,
        id: str,
        band: str,
        labels: dict[int, str],
        palette: dict[int, str],
        years: list[int],
        nodata: None | int = None,
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
    def keys(self) -> list[int]:
        """Return the label keys of the dataset."""
        return list(self.labels.keys())

    @property
    def df(self) -> pd.DataFrame:
        """Return a Pandas dataframe describing the dataset parameters."""
        return pd.DataFrame(
            {
                "id": self.keys,
                "label": self.labels.values(),
                "color": self.palette.values(),
            }
        )

    @property
    def collection(self) -> ee.ImageCollection:
        """The :code:`ee.ImageCollection` representing the dataset."""
        return ee.ImageCollection(self.id)

    def _fetch_year_image(self, year: int) -> ee.Image:
        """
        Get one year's image from the dataset.

        Datasets that don't store one time-stamped image per year should override this method.
        """
        return self.collection.filterDate(str(year), str(year + 1)).first()

    def get_year(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. Set the metadata properties for visualization."""
        img = self._fetch_year_image(year)
        img = self._set_visualization_properties(img)
        if self.nodata is not None:
            img = img.updateMask(img.neq(self.nodata))

        return img.select(self.band)

    def _set_visualization_properties(self, image: ee.Image) -> ee.Image:
        """Set the properties used by Earth Engine to automatically assign a palette to an image
        from this dataset."""
        return image.set(
            f"{self.band}_class_values",
            list(self.labels.keys()),
            f"{self.band}_class_palette",
            [c.replace("#", "") for c in self.palette.values()],
        )

    def _list_years(self) -> ee.List:
        """Get an ee.List of all years in the collection."""
        return (
            self.collection.aggregate_array("system:time_start")
            .map(lambda ms: ee.Date(ms).get("year"))
            .distinct()
        )

    def sankify(
        self,
        years: list[int],
        region: ee.Geometry,
        max_classes: None | int = None,
        n: int = 500,
        title: str | None = None,
        scale: int | None = None,
        seed: int = 0,
        exclude: None = None,
        label_type: str = "class",
        theme: str | themes.Theme = themes.DEFAULT,
    ) -> SankeyPlot:
        """
        Generate an interactive Sankey plot showing land cover change over time from a series of
        years in the dataset.

        Parameters
        ----------
        years : List[int]
            The years to include in the plot. Select at least two unique years.
        region : ee.Geometry
            A region to generate samples within. The region must overlap all images.
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
        label_type : str, default "class"
            The type of label to display for each link, one of "class", "percent", or "count".
            Selecting "class" will use the class label, "percent" will use the proportion of
            sampled pixels in each class, and "count" will use the number of sampled pixels in each
            class.
        theme : str or Theme
            The theme to apply to the Sankey diagram. Can be the name of a built-in theme
            (e.g. "d3") or a custom `sankee.Theme` object.

        Returns
        -------
        SankeyPlot
            An interactive Sankey plot widget.
        """
        if exclude is not None:
            warn(
                "The `exclude` parameter is unused and will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )
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

        try:
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
                theme=theme,
            )
        except Exception as e:
            # Note that we handle missing years as a runtime error rather than validating against
            # the dataset years, since the list may be outdated.
            missing_years = set(years) - set(self.years)
            if missing_years:
                raise ValueError(
                    f"This dataset does not include the year(s) {sorted(list(missing_years))}. "
                    f"Choose from {list(self.years)}."
                ) from None

            # If the error is unrelated to a missing year, re-raise it
            raise e


class _LCMS_Dataset(Dataset):
    def _fetch_year_image(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. LCMS splits up each year into two images: CONUS
        and AK. This merges those into a single image."""
        collection = self.collection.filter(ee.Filter.eq("year", year))
        return collection.mosaic().clip(collection.geometry()).setDefaultProjection("EPSG:5070")


class _CCAP_Dataset(Dataset):
    def _fetch_year_image(self, year: int) -> ee.Image:
        """Get one year's image from the dataset. C-CAP splits up each year into multiple images.
        This merges those into a single image."""
        collection = self.collection.filterDate(str(year), str(year + 1))
        return collection.mosaic().clip(collection.geometry()).setDefaultProjection("EPSG:5070")


class _GLC_FCS30D_Dataset(Dataset):
    def __init__(
        self,
        name: str,
        id: dict[str, str],
        band: str,
        labels: dict[int, str],
        palette: dict[int, str],
        years: list[int],
        nodata: None | int = None,
    ):
        """
        Parameters
        ----------
        name : str
            The name of the dataset.
        id : dict
            The dictionary of :code:`system:id`s of the two :code:`ee.ImageCollection`s
            representing the annual and five-yearly datasets.
            keys: five-year, annual
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

        Change from parent class
        ------------------------
            GLC FCS30D uses 2 :code:`system:id`s, one for the annual dataset from 2000 to 2022 and
            one for the 5 yearly dataset from 1985 to 1995.
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

    @property
    def collection(self) -> ee.ImageCollection:
        """
        The :code:`ee.ImageCollection` representing the dataset.

        Change from parent class
        ------------------------
        GLC FCS30D uses 2 separate :code:`ee.ImageCollection`s. Each collection contains 2 images.
        Each image contains 1 band for each year of the dataset.

        This function:
            1. Mosaics them
            2. Resets the projection to match the initial image
            3. Renames the bands to the corresponding years
            4. Combines all bands into 1 image
            5. Returns an image collection with 1 image per year with `system:time_start` set to
            Jan 1 of that year
        """
        five_year = ee.ImageCollection(self.id["five_year"])
        five_year = (
            five_year.mosaic()
            .setDefaultProjection(five_year.first().projection())
            .rename(ee.List.sequence(1985, 1995, 5).map(lambda x: ee.Number(x).format("%04d")))
        )

        annual = ee.ImageCollection(self.id["annual"])
        annual = (
            annual.mosaic()
            .setDefaultProjection(annual.first().projection())
            .rename(ee.List.sequence(2000, 2022).map(lambda x: ee.Number(x).format("%04d")))
        )

        all_years = ee.Image.cat(five_year, annual)

        def bands_to_imgs(band_name: str) -> ee.Image:
            """
            Mapper to rename the band to classes and set `system:start_time` to Jan 1 of that
            year
            """
            return (
                all_years.select([band_name])
                .rename(["classes"])
                .set({"system:time_start": ee.Date(band_name)})
            )

        return ee.ImageCollection(all_years.bandNames().map(bands_to_imgs))


LCMS_LU = _LCMS_Dataset(
    name="LCMS LU - Land Change Monitoring System Land Use",
    id="USFS/GTAC/LCMS/v2024-10",
    band="Land_Use",
    labels={
        1: "Agriculture",
        2: "Developed",
        3: "Forest",
        4: "Other",
        5: "Rangeland or Pasture",
        6: "No Data",
    },
    palette={
        1: "#efff6b",
        2: "#ff2ff8",
        3: "#1b9d0c",
        4: "#a1a1a1",
        5: "#c2b34a",
        6: "#1B1716",
    },
    years=tuple(range(1985, 2025)),
    nodata=6,
)

# https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5
LCMS_LC = _LCMS_Dataset(
    name="LCMS LC - Land Change Monitoring System Land Cover",
    id="USFS/GTAC/LCMS/v2024-10",
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
    years=tuple(range(1985, 2025)),
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
    id="MODIS/061/MCD12Q1",
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
    years=tuple(range(2001, 2024)),
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE2 = Dataset(
    name="MCD12Q1 - MODIS Global Land Cover Type 2",
    id="MODIS/061/MCD12Q1",
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
    years=tuple(range(2001, 2024)),
)

# https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1
MODIS_LC_TYPE3 = Dataset(
    name="MCD12Q1 - MODIS Global Land Cover Type 3",
    id="MODIS/061/MCD12Q1",
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
    years=tuple(range(2001, 2024)),
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
CCAP_LC30 = _CCAP_Dataset(
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
    years=tuple(range(1984, 2023)),
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
    years=tuple(range(1985, 2022)),
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

GLC_FCS30D_FINE = _GLC_FCS30D_Dataset(
    name="""
        GLC_FCS30D - Global 30-meter Land Cover Change Dataset (1985-2022)
        - Fine Classification System
        """,
    id={
        "five_year": "projects/sat-io/open-datasets/GLC-FCS30D/five-years-map",
        "annual": "projects/sat-io/open-datasets/GLC-FCS30D/annual",
    },
    band="classes",
    labels={
        10: "Rainfed cropland",
        11: "Herbaceous cover cropland",
        12: "Tree or shrub cover cropland",
        20: "Irrigated cropland",
        51: "Closed evergreen broadleaved forest",
        52: "Open evergreen broadleaved forest",
        61: "Closed deciduous broadleaved forest",
        62: "Open deciduous broadleaved forest",
        71: "Closed evergreen needleleaved forest",
        72: "Open evergreen needleleaved forest",
        81: "Closed deciduous needleleaved forest",
        82: "Open deciduous needleleaved forest",
        91: "Closed mixed-leaf forest",
        92: "Open mixed-leaf forest",
        120: "Shrubland",
        121: "Evergreen shrubland",
        122: "Deciduous shrubland",
        130: "Grassland",
        140: "Lichens and mosses",
        150: "Sparse vegetation",
        152: "Sparse shrubland",
        153: "Sparse herbaceous cover",
        181: "Swamp",
        182: "Marsh",
        183: "Flooded flat",
        184: "Saline",
        185: "Mangrove",
        186: "Salt marsh",
        187: "Tidal flat",
        190: "Impervious surface",
        200: "Bare areas",
        201: "Consolidated bare areas",
        202: "Unconsolidated bare areas",
        210: "Water body",
        220: "Permanent snow and ice",
    },
    palette={
        10: "#ffff64",
        11: "#ffff64",
        12: "#ffff00",
        20: "#aaf0f0",
        51: "#4c7300",
        52: "#006400",
        61: "#aac800",
        62: "#00a000",
        71: "#005000",
        72: "#003c00",
        81: "#286400",
        82: "#285000",
        91: "#a0b432",
        92: "#788200",
        120: "#966400",
        121: "#964b00",
        122: "#966400",
        130: "#ffb432",
        140: "#ffdcd2",
        150: "#ffebaf",
        152: "#ffd278",
        153: "#ffebaf",
        181: "#00a884",
        182: "#73ffdf",
        183: "#9ebbd7",
        184: "#828282",
        185: "#f57ab6",
        186: "#66cdab",
        187: "#444f89",
        190: "#c31400",
        200: "#fff5d7",
        201: "#dcdcdc",
        202: "#fff5d7",
        210: "#0046c8",
        220: "#ffffff",
    },
    years=tuple(range(1985, 2000, 5)) + tuple(range(2000, 2023)),
)

GLC_FCS30D_LEVEL1 = _GLC_FCS30D_Dataset(
    name="""
        GLC_FCS30D - Global 30-meter Land Cover Change Dataset (1985-2022)
         - Level 1 Validation System
        """,
    id={
        "five_year": "projects/sat-io/open-datasets/GLC-FCS30D/five-years-map",
        "annual": "projects/sat-io/open-datasets/GLC-FCS30D/annual",
    },
    band="classes",
    labels={
        10: "Rainfed cropland",
        11: "Rainfed cropland",
        12: "Rainfed cropland",
        20: "Irrigated cropland",
        51: "Evergreen broadleaved forest",
        52: "Evergreen broadleaved forest",
        61: "Deciduous broadleaved forest",
        62: "Deciduous broadleaved forest",
        71: "Evergreen needleleaved forest",
        72: "Evergreen needleleaved forest",
        81: "Deciduous needleleaved forest",
        82: "Deciduous needleleaved forest",
        91: "Mixed-leaf forest",
        92: "Mixed-leaf forest",
        120: "Shrubland",
        121: "Shrubland",
        122: "Shrubland",
        130: "Grassland",
        140: "Lichens and mosses",
        150: "Sparse vegetation",
        152: "Sparse vegetation",
        153: "Sparse vegetation",
        181: "Inland wetland",
        182: "Inland wetland",
        183: "Inland wetland",
        184: "Inland wetland",
        185: "Coastal wetland",
        186: "Coastal wetland",
        187: "Coastal wetland",
        190: "Impervious surface",
        200: "Bare areas",
        201: "Bare areas",
        202: "Bare areas",
        210: "Water body",
        220: "Permanent snow and ice",
    },
    palette={
        10: "#ffff64",
        11: "#ffff64",
        12: "#ffff64",
        20: "#aaf0f0",
        51: "#4c7300",
        52: "#4c7300",
        61: "#aac800",
        62: "#aac800",
        71: "#005000",
        72: "#005000",
        81: "#286400",
        82: "#286400",
        91: "#a0b432",
        92: "#a0b432",
        120: "#966400",
        121: "#966400",
        122: "#966400",
        130: "#ffb432",
        140: "#ffdcd2",
        150: "#ffebaf",
        152: "#ffebaf",
        153: "#ffebaf",
        181: "#00a884",
        182: "#00a884",
        183: "#00a884",
        184: "#00a884",
        185: "#f57ab6",
        186: "#f57ab6",
        187: "#f57ab6",
        190: "#c31400",
        200: "#fff5d7",
        201: "#fff5d7",
        202: "#fff5d7",
        210: "#0046c8",
        220: "#ffffff",
    },
    years=tuple(range(1985, 2000, 5)) + tuple(range(2000, 2023)),
)

GLC_FCS30D_BASIC = _GLC_FCS30D_Dataset(
    name="""GLC_FCS30D - Global 30-meter Land Cover Change Dataset (1985-2022)
        - Basic Classification System
        """,
    id={
        "five_year": "projects/sat-io/open-datasets/GLC-FCS30D/five-years-map",
        "annual": "projects/sat-io/open-datasets/GLC-FCS30D/annual",
    },
    band="classes",
    labels={
        10: "Cropland",
        11: "Cropland",
        12: "Cropland",
        20: "Cropland",
        51: "Forest",
        52: "Forest",
        61: "Forest",
        62: "Forest",
        71: "Forest",
        72: "Forest",
        81: "Forest",
        82: "Forest",
        91: "Forest",
        92: "Forest",
        120: "Shrubland",
        121: "Shrubland",
        122: "Shrubland",
        130: "Grassland",
        140: "Tundra",
        150: "Bare areas",
        152: "Bare areas",
        153: "Bare areas",
        181: "Wetland",
        182: "Wetland",
        183: "Wetland",
        184: "Wetland",
        185: "Wetland",
        186: "Wetland",
        187: "Wetland",
        190: "Impervious surface",
        200: "Bare areas",
        201: "Bare areas",
        202: "Bare areas",
        210: "Water body",
        220: "Permanent snow and ice",
    },
    palette={
        10: "#ffff64",
        11: "#ffff64",
        12: "#ffff64",
        20: "#ffff64",
        51: "#4c7300",
        52: "#4c7300",
        61: "#4c7300",
        62: "#4c7300",
        71: "#4c7300",
        72: "#4c7300",
        81: "#4c7300",
        82: "#4c7300",
        91: "#4c7300",
        92: "#4c7300",
        120: "#966400",
        121: "#966400",
        122: "#966400",
        130: "#ffb432",
        140: "#ffdcd2",
        150: "#ffebaf",
        152: "#ffebaf",
        153: "#ffebaf",
        181: "#00a884",
        182: "#00a884",
        183: "#00a884",
        184: "#00a884",
        185: "#00a884",
        186: "#00a884",
        187: "#00a884",
        190: "#c31400",
        200: "#ffebaf",
        201: "#ffebaf",
        202: "#ffebaf",
        210: "#0046c8",
        220: "#ffffff",
    },
    years=tuple(range(1985, 2000, 5)) + tuple(range(2000, 2023)),
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
    GLC_FCS30D_FINE,
    GLC_FCS30D_LEVEL1,
    GLC_FCS30D_BASIC,
]
