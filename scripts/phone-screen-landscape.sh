#!/bin/sh
# Rotate the phone into landscape with a lower output scale so desktop / Electron
# apps (which assume a wide canvas) stop being squished in portrait.
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
OUT=DSI-1
wlr-randr --output "$OUT" --transform 90 --scale 2 2>&1
echo "landscape applied: transform=90 scale=2 -> logical 1140x540 (DSI-1)"
