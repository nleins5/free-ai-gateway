#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Building frontend..."
cd ui
npm install
npm run build
cd ..

echo "Build complete."
