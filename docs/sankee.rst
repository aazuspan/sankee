API
================

Sankey Plots
~~~~~~~~~~~~
Most of the functionality of the :code:`sankee` package is contained by one function that creates Sankey plots from Earth Engine data: :code:`sankee.sankify`.

.. autofunction:: sankee.core.sankify


Datasets
~~~~~~~~

Premade Datasets
^^^^^^^^^^^^^^^^
For convenience, :code:`sankee` packages most of the common land cover datasets available in Google Earth Engine. You can use the methods below
to find, access, and modify premade datasets.

.. autoclass:: sankee.datasets
    :members:

Custom Datasets
^^^^^^^^^^^^^^^
If you want to use a dataset not packaged with :code:`sankee`, you can use the :code:`Dataset` class to define your own dataset.

.. autoclass:: sankee.datasets.Dataset
    :members:

    .. automethod:: __init__

