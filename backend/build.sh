#!/bin/bash
set -e

echo "Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing dependencies (prefer binary wheels)..."
# Try to install using prebuilt wheels first
pip install --no-cache-dir --prefer-binary -r requirements.txt || {
	echo "Prefer-binary install failed, falling back to default install (may attempt to compile)."
	pip install --no-cache-dir -r requirements.txt
}

echo "Dependencies installed successfully!"
