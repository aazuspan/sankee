#!/bin/bash

echo "Removing previous builds..."
rm -rf dist
rm -rf builds
rm -rf *.egg-info

echo "Building binaries and wheel..."
pipenv run python setup.py sdist bdist_wheel

echo "Uploading to PyPI"
pipenv run twine upload

exit 0