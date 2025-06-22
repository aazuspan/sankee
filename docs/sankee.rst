API
================

Premade Datasets
~~~~~~~~~~~~~~~~

.. currentmodule:: sankee.datasets

Supported Datasets
^^^^^^^^^^^^^^^^^^

:code:`sankee` uses :class:`Dataset` objects to define the parameters for commonly used collections of classified imagery.
The following premade datasets are included:

+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| Dataset                                                                                                                  | Name                                                                           | Extent                | Years                 |
+==========================================================================================================================+================================================================================+=======================+=======================+
| `MODIS_LC_TYPE1 <https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1>`_                        | MODIS Land Cover - Type 1                                                      | Global                | 2001-2023 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `MODIS_LC_TYPE2 <https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1>`_                        | MODIS Land Cover - Type 2                                                      | Global                | 2001-2023 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `MODIS_LC_TYPE3 <https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD12Q1>`_                        | MODIS Land Cover - Type 3                                                      | Global                | 2001-2023 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `CGLS_LC100 <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global>`_  | Copernicus Global Land Cover                                                   | Global                | 2015-2019 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `GLC_FCS30D_FINE <https://gee-community-catalog.org/projects/glc_fcs/>`_                                                 | Global 30-meter Land Cover Change Dataset - Fine Classification System         | Global                | 1985-2022 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `GLC_FCS30D_LEVEL1 <https://gee-community-catalog.org/projects/glc_fcs/>`_                                               | Global 30-meter Land Cover Change Dataset - Level 1 Validation System          | Global                | 1985-2022 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `GLC_FCS30D_BASIC <https://gee-community-catalog.org/projects/glc_fcs/>`_                                                | Global 30-meter Land Cover Change Dataset - Basic Classification System        | Global                | 1985-2022 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `LCMS_LC <https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5>`_                          | Landscape Change Monitoring System - Land Cover                                | CONUS + SE AK         | 1985-2024 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `LCMS_LU <https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_LCMS_v2020-5>`_                          | Landscape Change Monitoring System - Land Use                                  | CONUS + SE AK         | 1985-2024 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `NLCD <https://developers.google.com/earth-engine/datasets/catalog/USGS_NLCD_RELEASES_2019_REL_NLCD>`_                   | National Land Cover Database                                                   | CONUS                 | 2001-2019 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `LCMAP <https://gee-community-catalog.org/projects/lcmap/>`_                                                             | Landscape Change Monitoring, Assessment, and Projection                        | CONUS                 | 1985-2021 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `CCAP_LC30 <https://gee-community-catalog.org/projects/ccap_mlc/>`_                                                      | NOAA Coastal Change Analysis Program 30m                                       | CONUS (wetlands)      | 1975-2016 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `CORINE <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_CORINE_V20_100m>`_                       | Coordination of Information on the Environment                                 | Europe (partial)      | 1986-2017 (irregular) |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+
| `CA_FOREST_LC <https://gee-community-catalog.org/projects/ca_lc/>`_                                                      | High-Resolution Annual Forest Land Cover Maps for Canada's Forested Ecosystems | Canada (forests)      | 1984-2022 (annual)    |
+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------+-----------------------+-----------------------+

Dataset methods
^^^^^^^^^^^^^^^

Datasets have some helpful properties and methods:

.. autoclass:: Dataset
    :members:
    :exclude-members: sankify


Sankifying a Premade Dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a Sankey diagram from a dataset, use :meth:`Dataset.sankify`.

.. automethod:: Dataset.sankify

Example
^^^^^^^

For example, the code below creates a Sankey diagram from 2 years of LCMS Land Use data:

.. code-block:: python

    import sankee
    import ee

    ee.Initialize()

    dataset = sankee.datasets.LCMS_LU
    aoi = ee.Geometry.Point([-115.184978, 35.964608]).buffer(1000)
    dataset.sankify(years=[1985, 2020], region=aoi, max_classes=3)


Custom Datasets
~~~~~~~~~~~~~~~

.. currentmodule:: sankee

If you want to use classified data not included with :code:`sankee`, you can use :func:`sankify` instead. Parameters are similar to 
using a premade dataset, but you will have to manually specify the images, labels, and palette that are automatically included with 
premade datasets. 

.. autofunction:: sankify

Example
^^^^^^^

Here's an example creating a Sankey diagram from two `Dynamic World <https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1>`_ 
scenes, acquired immediately before and after the 2020 Beachie Creek fire in western Oregon, USA.

.. code-block:: python

    import sankee
    import ee

    ee.Initialize()

    # Load two images
    pre = ee.Image("GOOGLE/DYNAMICWORLD/V1/20200904T185921_20200904T190750_T10TEQ")
    post = ee.Image("GOOGLE/DYNAMICWORLD/V1/20201009T190319_20201009T190349_T10TEQ")
    aoi = ee.Geometry.Point([-122.30239918572622, 44.802882471354316]).buffer(1000)

    # Define the band name and the class labels and colors corresponding to each pixel value.
    band = "label"

    labels = {
        0: "water",
        1: "trees",
        2: "grass",
        3: "flooded_vegetation",
        4: "crops",
        5: "shrub_and_scrub",
        6: "built",
        7: "bare",
        8: "snow_and_ice"
    }

    palette = {
        0: "#419BDF",
        1: "#397D49",
        2: "#88B053",
        3: "#7A87C6",
        4: "#E49635",
        5: "#DFC35A",
        6: "#C4281B",
        7: "#A59B8F",
        8: "#B39FE1"
    }

    # Generate the Sankey diagram from the two images
    sankee.sankify(
        image_list=[pre, post], 
        region=aoi, 
        band=band, 
        labels=labels,
        palette=palette,
    )

Themes
~~~~~~

Custom and built-in themes can be used to customize the appearance of Sankey diagrams. :meth:`datasets.Dataset.sankify` and :func:`sankify` 
both accept a :code:`theme` parameter that can be used to specify the name of a built-in theme (see :code:`sankee.themes.THEMES.keys()`) or 
a custom :class:`Theme` object.

.. autoclass:: Theme
    :members: