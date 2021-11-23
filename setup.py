from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="sankee",
    version="0.0.6",
    description="Visualize classified time series data with interactive Sankey plots in Google Earth Engine.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aazuspan/sankee",
    author="Aaron Zuspan",
    author_email="aa.zuspan@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="sankey land cover visualization",
    packages=find_packages(include=["sankee", "sankee."]),
    python_requires=">=3.6",
    install_requires=["earthengine-api>=0.1.230", "ipykernel", "nbformat>=4.2.0", "numpy", "pandas", "plotly",],
    project_urls={
        "Bug Reports": "https://github.com/aazuspan/sankee/issues",
        "Source": "https://github.com/aazuspan/sankee/",
    },
)
