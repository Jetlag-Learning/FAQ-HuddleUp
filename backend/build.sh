#!/bin/bash
set -e

echo "Installing dependencies with binary wheels..."
pip install --no-cache-dir --prefer-binary -q wheel setuptools
pip install --no-cache-dir --prefer-binary --no-build-isolation -r requirements.txt

echo "Dependencies installed successfully!"
