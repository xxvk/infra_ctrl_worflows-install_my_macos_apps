#!/bin/bash
# adb-pixel.sh — recover the Pixel wireless ADB connection and pin it to a fixed port.
# Part of the macomrade engine (scripts/). Machine-specific values (phone IP,
# mDNS serial) come from environment overrides with engine defaults.
#
# Usage:  adb-pixel.sh [--once]
#   --once            run a single recovery attempt (no daemon loop)
#
# Device identity is machine-specific and MUST NOT live in this file -- this
# repository is public. Values are read, in order, from the environment and
# then from Private/pixel-device.json (gitignored):
#
#   MACOMRADE_PIXEL_IP       phone LAN IP           (Private key: "ip")
#   MACOMRADE_PIXEL_SERIAL   phone mDNS serial name (Private key: "serial")
#   MACOMRADE_PIXEL_PORT     fixed adb TCP port     (Private key: "port", default 5555)
#
# Private/pixel-device.json:
#   { "ip": "192.168.1.50", "serial": "adb-XXXXXXXXXXXXX-YYYYYY", "port": 5555 }
#
# The IP is only a fast path; it goes stale whenever the phone changes network
# (verified 2026-08-22). mDNS discovery below is the network-agnostic fallback.
#
# Design: `adb tcpip 5555` is runtime-only and resets on phone reboot; this
# script is the durable recovery path. Order: fixed port first, then mDNS
# discovery (port-agnostic), then switch adbd to the fixed port.
# Pairing (`adb pair`) is one-time per phone and not automated here.

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ADB="$(command -v adb)"
PRIVATE_DEVICE="${MACOMRADE_PIXEL_DEVICE_FILE:-$(dirname "$0")/../Private/pixel-device.json}"

# Read a key out of the private device file, empty if the file is absent.
priv() {
  [ -f "$PRIVATE_DEVICE" ] || return 0
  /usr/bin/python3 -c 'import json,sys
try:
    d=json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
v=d.get(sys.argv[2])
print("" if v is None else v)' "$PRIVATE_DEVICE" "$1" 2>/dev/null
}

IP="${MACOMRADE_PIXEL_IP:-$(priv ip)}"
PORT="${MACOMRADE_PIXEL_PORT:-$(priv port)}"
PORT="${PORT:-5555}"
SERIAL="${MACOMRADE_PIXEL_SERIAL:-$(priv serial)}"

if [ -z "$IP" ] && [ -z "$SERIAL" ]; then
  echo "adb-pixel.sh: no device identity configured." >&2
  echo "  Set MACOMRADE_PIXEL_IP / MACOMRADE_PIXEL_SERIAL, or create" >&2
  echo "  $PRIVATE_DEVICE with {\"ip\": ..., \"serial\": ...}" >&2
  exit 2
fi
LOG="${MACOMRADE_PIXEL_LOG:-/tmp/adb-pixel.log}"

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }

is_connected() {
  [ -n "$IP" ] || return 1
  "$ADB" devices | awk -v t="$IP:$PORT" '$1==t && $2=="device" {found=1} END {exit !found}'
}

if is_connected; then
  exit 0  # already on the fixed port
fi

log "not connected to $IP:$PORT, attempting recovery..."

# 1) Fixed port directly (adbd may still be alive; only adb server forgot)
if [ -n "$IP" ]; then
  "$ADB" connect "$IP:$PORT" >/dev/null 2>&1
fi
if is_connected; then
  log "reconnected via $IP:$PORT"
  exit 0
fi

# 2) mDNS discovery by service name (wireless debugging random port)
for svc in ${SERIAL:+"${SERIAL}._adb-tls-connect._tcp" "${SERIAL}._adb._tcp"}; do
  "$ADB" connect "$svc" >/dev/null 2>&1
  if "$ADB" devices | awk -v t="$svc" '$1==t && $2=="device" {found=1} END {exit !found}'; then
    log "discovered via $svc"
    # 3) switch adbd to the fixed port
    if "$ADB" -s "$svc" tcpip "$PORT" >/dev/null 2>&1; then
      log "tcpip $PORT OK"
      sleep 3
      "$ADB" connect "$IP:$PORT" >/dev/null 2>&1
      is_connected && log "now connected via $IP:$PORT"
      exit 0
    fi
  fi
  # drop failed mDNS connections to avoid stale offline entries
  "$ADB" disconnect "$svc" >/dev/null 2>&1
done

log "recovery failed (is the phone's wireless debugging on and on the same Wi-Fi?)"
exit 1
