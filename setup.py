from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "earthengine-api>=0.1.230",
    "numpy",
    "pandas",
    "plotly>=5.2.2",
    "ipywidgets",
]
doc_requirements = ["nbsphinx", "sphinx", "sphinx_rtd_theme"]
test_requirements = ["pytest", "coverage", "pytest-cov", "httplib2"]
dev_requirements = (
    [
        "pre-commit",
        "mypy",
        "black",
        "isort",
        "bumpversion",
        "twine",
    ]
    + doc_requirements
    + test_requirements
)

extras_requirements = {
    "doc": doc_requirements,
    "dev": dev_requirements,
    "test": test_requirements,
}


setup(
    name="sankee",
    version="0.2.0",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="sankey land cover visualization",
    packages=find_packages(include=["sankee", "sankee."]),
    python_requires=">=3.7",
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require=extras_requirements,
    project_urls={
        "Bug Reports": "https://github.com/aazuspan/sankee/issues",
        "Source": "https://github.com/aazuspan/sankee/",
    },
)
