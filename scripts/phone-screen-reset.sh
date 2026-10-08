#!/bin/sh
# Restore the phone to its default portrait output.
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
wlr-randr --output DSI-1 --transform normal --scale 3 2>&1
echo "reset applied: transform=normal scale=3 -> logical 360x760"
