#!/bin/sh

# Run this script once to tell Git where to find hooks.

echo "Setting git hooks directory..."
# Set the hooks directory
git config core.hooksPath .git-hooks

echo "Git hooks directory set successfully!"