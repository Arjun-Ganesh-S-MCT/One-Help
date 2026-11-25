#!/usr/bin/env bash
# Install the built app for the current user (no root needed):
#   tar xzf oru-udhavi-linux-x86_64.tar.gz && cd oru-udhavi && ./install-local.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/.local/opt/oru-udhavi"
mkdir -p "$dest" "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/512x512/apps"
cp -r "$here"/. "$dest"/
ln -sf "$dest/oru-udhavi" "$HOME/.local/bin/oru-udhavi"
cp "$here/oru-udhavi.png" "$HOME/.local/share/icons/hicolor/512x512/apps/oru-udhavi.png"
sed "s|^Exec=.*|Exec=$dest/oru-udhavi|" "$here/oru-udhavi.desktop" > "$HOME/.local/share/applications/oru-udhavi.desktop"
echo "Installed. Find 'Oru Udhavi' in your app menu."
