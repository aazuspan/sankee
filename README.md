# sankee

![](https://img.shields.io/conda/vn/conda-forge/sankee?style=flat-square)
![](https://img.shields.io/pypi/v/sankee?style=flat-square)
![](https://img.shields.io/github/license/aazuspan/sankee?style=flat-square)

Visualize changes in classified time series data with interactive Sankey plots in Google Earth Engine

![Sankee example showing grassland expansion in the Nile Delta](examples/demo.gif)

## Contents

- [Description](https://github.com/aazuspan/sankee#Description)
- [Installation](https://github.com/aazuspan/sankee#Installation)
  - [Using Pip](https://github.com/aazuspan/sankee#Using-Pip)
  - [Using Conda](https://github.com/aazuspan/sankee#Using-Conda)
- [Requirements](https://github.com/aazuspan/sankee#Requirements)
- [Quick Start](https://github.com/aazuspan/sankee#Quick-Start)
  - [Using a Premade Dataset](https://github.com/aazuspan/sankee#Using-a-Premade-Dataset)
  - [Using a Custom Dataset](https://github.com/aazuspan/sankee#Using-a-Custom-Dataset)
- [Features](https://github.com/aazuspan/sankee#Features)
  - [Modular Datasets](https://github.com/aazuspan/sankee#Modular-Datasets)
  - [Flexible Time Series](https://github.com/aazuspan/sankee#Flexible-Time-Series)
  - [Integration with geemap](https://github.com/aazuspan/sankee#Integration-with-geemap)
- [API](https://github.com/aazuspan/sankee#API)
- [Contributing](https://github.com/aazuspan/sankee#Contributing)

## Description

`sankee` provides a dead-simple API that combines the power of [GEE](https://github.com/google/earthengine-api) and [Plotly](https://github.com/plotly/plotly.py) to visualize changes in land cover, plant health, burn severity, or any other classified imagery over a time series in a region of interst using interactive Sankey plots. Use a library of built-in datasets like NLCD, MODIS Land Cover, or CGLS for convenience or define your own custom datasets for flexibility.

`sankee` works by randomly sampling points in a time series of classified imagery to visualize how cover types changed over time.

## Installation

### Using Pip

```sh
pip install sankee
```

### Using Conda

`sankee` can be downloaded through conda-forge within a Conda environment.

```sh
conda create -n sankee
conda activate sankee
conda install -c conda-forge sankee
```

## Requirements

- An authenticated GEE Python environment ([offical guide](https://developers.google.com/earth-engine/guides/python_install))

## Quick Start

### Using a Premade Dataset

Datasets in `sankee` are used to apply labels and colors to classified imagery (eg. a value of 42 in an NLCD 2016 image should be labeled "Evergeen forest" and colored green). `sankee` includes premade `Dataset` objects for common classified datasets in GEE like NLCD, MODIS land cover, and CGLS. See [datasets](https://github.com/aazuspan/sankee#Modular-Datasets) for a detailed explanation.

```python
import ee
import sankee

ee.Initialize()

# Choose a premade dataset object that contains band, label, and palette information for NLCD
dataset = sankee.datasets.NLCD2016

# Build a list of images
img_list = [ee.Image(f"USGS/NLCD/NLCD2001"), ee.Image(f"USGS/NLCD/NLCD2016")]
# Build a matching list of labels for the images (optional)
label_list = ["2001", "2016"]

# Define an area of interest
vegas = ee.Geometry.Polygon(
        [[[-115.4127152226893, 36.29589873319828],
          [-115.4127152226893, 36.12082334399102],
          [-115.3248245976893, 36.12082334399102],
          [-115.3248245976893, 36.29589873319828]]])

# Choose a title to display over your plot (optional)
title = "Las Vegas Urban Sprawl, 2001 - 2016"

# Generate your Sankey plot
plot = sankee.sankify(img_list, vegas, label_list, dataset, max_classes=4, title=title)
plot
```

[![NLCD Las Vegas urbanization example Sankey plot](examples/NLCD.png)](https://htmlpreview.github.io/?https://github.com/aazuspan/sankee/main/examples/NLCD.html)

### Using a Custom Dataset

Datasets can also be manually defined for custom images. In this example, we'll classify 1-year and 5-year post-fire Landsat imagery using NDVI and visualize plant recovery using `sankee`.

```python
import ee
import sankee

ee.Initialize()

# Load fire perimeters from MTBS data
fires = ee.FeatureCollection("users/aazuspan/fires/mtbs_1984_2018")
# Select the 2014 Happy Camp Complex fire perimeter in California
fire = fires.filterMetadata("Fire_ID", "equals", "CA4179612337420140814")

# Load imagery 1 year after fire and 5 years after fire
immediate = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_045031_20150718")
recovery = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_046031_20200807")

# Calculate NDVI
immediate_NDVI = immediate.normalizedDifference(["B5", "B4"])
recovery_NDVI = recovery.normalizedDifference(["B5", "B4"])

# Reclassify continuous NDVI values into classes of plant health
immediate_class = ee.Image(1) \
  .where(immediate_NDVI.lt(0.3), 0) \
  .where(immediate_NDVI.gt(0.5), 2) \
  .rename("health")

recovery_class = ee.Image(1) \
  .where(recovery_NDVI.lt(0.3), 0) \
  .where(recovery_NDVI.gt(0.5), 2) \
  .rename("health")

# Specify the band name for the image
band = "health"

# Assign labels to the pixel values defined above
labels = {
    0: "Unhealthy",
    1: "Moderate",
    2: "Healthy"
}
# Assign colors to the pixel values defined above
palette = {
    0: "#e5f5f9",
    1: "#99d8c9",
    2: "#2ca25f"
}

# Define the images to use and create labels to describe them
img_list = [immediate_class, recovery_class]
label_list = ["Immediate", "Recovery"]

# Generate your Sankey plot
plot = sankee.sankify(img_list, fire, label_list, band=band, labels=labels, palette=palette, scale=20)
plot
```

[![NDVI post-fire recovery example Sankey plot](examples/NDVI.png)](https://htmlpreview.github.io/?https://github.com/aazuspan/sankee/main/examples/NDVI.html)

## Features

### Modular Datasets

Datasets in `sankee` define how classified image values are labeled and colored when plotting. `label` and `palette` arguments for `sankee` functions can be manually provided as dictionaries where pixel values are keys and labels and colors are values. Every value in the image **must** have a corresponding color and label. Datasets also define the `band` name in the image in which classified values are found.

Any classified image can be visualized by manually defining a band, palette, and label. However, premade datasets are included for convenience in the `sankee.datasets` module. To access a dataset, use its name, such as `sankee.datasets.NLCD2016`. To get a list of all dataset names, run `sankee.datasets.names()`. Datasets can also be accessed using `sankee.datasets.get()` which returns a list of `Dataset` objects that can be selecting by indexing.

```python
# List all sankee built-in datasets
sankee.datasets.names()

>> ['NLCD2016',
    'MODIS_LC_TYPE1',
    'MODIS_LC_TYPE2',
    'MODIS_LC_TYPE3',
    'CGLS_LC100']

# Preview a list of available images belonging to one dataset
sankee.datasets.CGLS_LC100.get_images(3)

>> ['COPERNICUS/Landcover/100m/Proba-V-C3/Global/2015',
    'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2016',
    'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017',
    '...']
```

### Flexible Time Series

`sankee` can handle any length of time series. The number of images will determine the number of time steps in the series. The example below shows a three-image time series.

[![MODIS glacier loss example Sankey plot](examples/MODIS.png)](https://htmlpreview.github.io/?https://github.com/aazuspan/sankee/main/examples/MODIS.html)

### Integration with geemap

[geemap](https://github.com/giswqs/geemap) is a great tool for exploring changes in GEE imagery before creating plots with `sankee`. Integration is quick and easy. Just use `geemap` like you normally would, and pass the images and feature geometries to `sankee` for plotting. The example at the top of the page shows `sankee` can be used with `geemap`.

# API

## Core function

### sankee.sankify(image*list, region, \_label_list, dataset, band, labels, palette, exclude, max_classes, n, title, scale, seed, dropna*)

Generate `n` random samples points within a `region` and extract classified pixel values from each image in an `image list`. Arrange the sample data into a Sankey plot that can be used to visualize changes in image classifications.

**Arguments**

- image_list (list)
  - An ordered list of images representing a time series of classified data. Each image will be sampled to generate the Sankey plot. Any length of list is allowed, but lists with more than 3 or 4 images may produce unusable plots.
- region (ee.Geometry)
  - A region to generate samples within.
- _label_list (list, default: None)_
  - An list of labels corresponding to the images. The list must be the same length as `image_list`. If none is provided, sequential numeric labels will be automatically assigned starting at 0.
- _dataset (sankee.datasets.Dataset, default: None)_
  - A premade dataset that defines the band, labels, and palette for all images in `image_list`. If a custom dataset is being used, provide `band`, `labels`, and `palette` instead.
- _band (str, default: None)_
  - The name of the band in all images of `image_list` that contains classified data. If none is provided, `dataset` must be provided instead.
- _labels (dict, default: None)_

  - The labels associated with each value of all images in `image_list`. Every value in the images must be included as a key in the `labels` dictionary. If none is provided, `dataset` must be provided instead.

- _palette (dict, default: None)_

  - The colors associated with each value of all images in `image_list`. Every value in the images must be included as a key in the `palette` dictionary. If none is provided, `dataset` must be provided instead. Colors must be supported by `Plotly`.

- _exclude (list, default: None)_
  - An optional list of pixel values to exclude from the plot. Excluded values must be raw pixel values rather than class labels. This can be helpful if the region is dominated by one or more unchanging classes and the goal is to visualize changes in smaller classes.
- _max_classes (int, default: None)_
  - If a value is provided, small classes will be removed until `max_classes` remain. Class size is calculated based on total times sampled in the time series.
- _n (int, default: 100)_
  - The number of samples points to randomly generate for characterizing all images. More samples will provide more representative data but will take longer to process.
- _title (str, default: None)_
  - An optional title that will be displayed above the Sankey plot.
- _scale (int, default: None)_
  - The scale in image units to perform sampling at. If none is provided, GEE will attempt to use the image's nominal scale, which may cause errors depending on the image projection.
- _seed (int, default: 0)_
  - The seed value used to generate repeatable results during random sampling.
- _dropna (bool, default: True)_
  - If the `region` extends into areas that contain no data in any image, some samples may have null values. If `dropna` is True, those samples will be dropped. This may lead to fewer samples being returned than were requested by `n`.

**Returns**

- A `Plotly` Sankey plot object.

---

## Dataset functions

### sankee.datasets.names()

Get a list of supported dataset names. Names can be used to access datasets using `sankee.datasets.{dataset_name}`.

**Arguments**

- None

**Returns** (list)

- A list of strings for supported dataset names.

**Example**

```python
sankee.datasets.names()

>> ['NLCD2016', 'MODIS_LC_TYPE1', 'MODIS_LC_TYPE2', 'MODIS_LC_TYPE3', 'CGLS_LC100']
```

### sankee.datasets.get(_i_)

Get a list of supported `sankee.datasets.Dataset` objects.  
**Arguments**

- _i (int, default: None)_
  - An optional index to retrieve a specific dataset.

**Returns** (list)

- A list of supported `sankee.datasets.Dataset` objects. If `i` is provided, only one object is returned.

**Example**

```python
# Get the first Dataset object
sankee.datasets.get(0)

>> <sankee.datasets.Dataset> NLCD: USGS National Land Cover Database
```

### sankee.datasets.Dataset.get*images(\_max_images*)

Get a list of image names in the collection of a specific dataset.  
**Arguments**

- _max_images (int, default: 20)_
  - The max number of images to return.

**Returns** (list)

- A list of image names that can be used to load `ee.Image` objects.

**Example**

```python
sankee.datasets.NLCD2016.get_images(3)

>> ['USGS/NLCD/NLCD1992', 'USGS/NLCD/NLCD2001', 'USGS/NLCD/NLCD2001_AK', '...']
```

---

## Dataset properties and attributes

### sankee.datasets.Dataset.collection

- Return the image collection associated with the dataset.

### sankee.datasets.Dataset.df

- Return a Pandas dataframe describing the classes, labels, and colors associated with the dataset.

### sankee.datasets.Dataset.id

- Return the system ID of the image collection.

## Contributing

If you find bugs or have feature requests, please open an issue!

---

[Top](https://github.com/aazuspan/sankee#sankee)
