#!/bin/bash
# SVG -> PNG (2x) using headless Chrome. usage: render_svg.sh in.svg [out.png]
set -e
IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="${2:-${IN%.svg}.png}"
W=$(grep -oE 'width="[0-9]+"' "$IN" | head -1 | grep -oE '[0-9]+')
H=$(grep -oE 'height="[0-9]+"' "$IN" | head -1 | grep -oE '[0-9]+')
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMP=$(mktemp -d)
printf '<html><body style="margin:0"><img src="file://%s" width="%s" height="%s"></body></html>' "$IN" "$W" "$H" > "$TMP/p.html"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --force-device-scale-factor=2 --window-size="$W,$H" --screenshot="$OUT" "file://$TMP/p.html" >/dev/null 2>&1
rm -rf "$TMP"
echo "$OUT"
