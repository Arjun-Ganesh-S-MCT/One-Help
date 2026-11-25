#!/usr/bin/env bash
# Copy the crop model made by tools/get_model.py into the mobile app.
set -e
mkdir -p "$(dirname "$0")/../www/models"
cp models/crop_model.onnx models/crop_labels.json "$(dirname "$0")/../www/models/"
echo "Model copied. Rebuild the APK (or redeploy the website) to include it."
