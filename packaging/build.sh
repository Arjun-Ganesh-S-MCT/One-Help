#!/usr/bin/env bash
# Build a standalone Linux folder with PyInstaller:  ./packaging/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install --upgrade pip pyinstaller -r requirements.txt
pyinstaller --noconfirm --clean --name oru-udhavi \
  --add-data "assets:assets" \
  --add-data "oru/data:oru/data" \
  --add-data "oru/fonts:oru/fonts" \
  --add-data "models:models" \
  --hidden-import gtts --hidden-import speech_recognition \
  --collect-data speech_recognition \
  main.py
cp packaging/oru-udhavi.desktop dist/oru-udhavi/
cp assets/icon.png dist/oru-udhavi/oru-udhavi.png
cp packaging/install-local.sh dist/oru-udhavi/
tar -C dist -czf dist/oru-udhavi-linux-x86_64.tar.gz oru-udhavi
echo "Built dist/oru-udhavi-linux-x86_64.tar.gz"
