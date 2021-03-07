#!/bin/sh

# This script will be called automatically by Git hooks.

# Exit 1 if any tests fail
set -e

cd "${0%/*}/.."

echo 'Running tests...'
pipenv run python -m tests.test

exit 0