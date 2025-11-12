#!/usr/bin/env bash
set -e

# ANNCSU SDK Publishing Script
#
# This script builds and publishes the ANNCSU SDK to PyPI using uv.
#
# Prerequisites:
# - uv installed (https://github.com/astral-sh/uv)
# - PYPI_TOKEN environment variable set
#
# Usage:
#   export PYPI_TOKEN="your-pypi-token"
#   ./scripts/publish.sh
#
# Or in CI/CD:
#   PYPI_TOKEN=${{ secrets.PYPI_TOKEN }} ./scripts/publish.sh

# Check if PYPI_TOKEN is set
if [ -z "${PYPI_TOKEN}" ]; then
    echo "Error: PYPI_TOKEN environment variable is not set"
    echo "Usage: PYPI_TOKEN=your-token ./scripts/publish.sh"
    exit 1
fi

echo "🔨 Building package with uv..."
uv build

echo "📦 Publishing to PyPI..."
uv publish --token "${PYPI_TOKEN}"

echo "✅ Package published successfully!"
