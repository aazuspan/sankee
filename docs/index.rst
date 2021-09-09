sankee
==================================

:code:`sankee` provides a dead-simple API that combines the power of `GEE <https://github.com/google/earthengine-api>`_ and 
`Plotly <https://github.com/plotly/plotly.py>`_ to visualize changes in land cover, plant health, burn severity, or any 
other classified imagery over a time series in a region of interst using interactive Sankey plots. Use a library of built-in 
datasets like NLCD, MODIS Land Cover, or CGLS for convenience or define your own custom datasets for flexibility.

:code:`sankee` works by randomly sampling points in a time series of classified imagery to visualize how cover types changed over time.

Installation
------------
.. code-block:: bash

   pip install sankee

.. code-block:: bash

   conda install -c conda-forge sankee

Contents
--------

.. toctree::
   :maxdepth: 2

   sankee
   examples


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
