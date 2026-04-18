#!/usr/bin/env bash
# P0.1 — FreeEEG128 USB enumeration diagnostic (macOS).
#
# Run this after plugging the board into the Mac (USB_DATA face) and
# applying battery-bank power (USB_POWER face).  Reports three things:
#
#   1. What's visible in /dev/cu.*
#   2. Whether any STMicro device (VID 0x0483) is on the USB bus
#   3. A list of every USB device the Mac sees, so you can spot
#      anything unexpected
#
# Then prints a one-line verdict and suggests the next action.
#
# Usage:
#     host/scripts/p0_diagnose.sh           # one-shot
#     host/scripts/p0_diagnose.sh --watch   # loop every 2 s (Ctrl-C to stop)

set -u

watch_mode=0
[[ "${1:-}" == "--watch" ]] && watch_mode=1

banner() { printf "\n\033[1;36m── %s ──\033[0m\n" "$1"; }
ok()     { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
warn()   { printf "  \033[1;33m!\033[0m %s\n" "$*"; }
bad()    { printf "  \033[1;31m✗\033[0m %s\n" "$*"; }
info()   { printf "  %s\n" "$*"; }

run_once() {
  printf '\n\033[1m[%s]  FreeEEG128 USB diagnostic\033[0m\n' "$(date +%H:%M:%S)"

  banner "1. /dev/cu.* serial devices"
  local cu
  cu=$(ls /dev/cu.usbmodem* /dev/cu.usbserial* 2>/dev/null || true)
  if [[ -z "$cu" ]]; then
    bad "no USB serial devices in /dev/cu.usbmodem*  /dev/cu.usbserial*"
    info "(Bluetooth entries like /dev/cu.BLTH are ignored — they don't count.)"
  else
    while IFS= read -r d; do ok "$d"; done <<<"$cu"
    ok "→ CDC device present; run: python3 host/scripts/p0_sniff.py"
  fi

  banner "2. STMicro / STM32 USB devices (VID 0x0483)"
  local st
  st=$(system_profiler SPUSBDataType 2>/dev/null | \
       awk 'BEGIN{RS=""} /STM|STMicroelectronics|0x0483|Virtual.*COM|VCOM|NeuroIDSS|Free.*EEG/ {print; print ""}')
  if [[ -z "$st" ]]; then
    bad "no STMicro-branded USB device on the bus"
  else
    printf '%s' "$st"
    # Classify common ST product IDs
    if echo "$st" | grep -qE '0x5740'; then
      ok "→ 0x5740 detected: STM32 Virtual COM Port (CDC application)"
    fi
    if echo "$st" | grep -qE '0xdf11'; then
      warn "→ 0xdf11 detected: STM32 DFU BOOTLOADER — firmware not running"
      warn "  Reset the board without holding any button to exit DFU."
    fi
  fi

  banner "3. Summary of all USB devices visible to macOS"
  system_profiler SPUSBDataType 2>/dev/null \
    | grep -E '^\s+[A-Z].*:$' \
    | grep -v -E 'USB 3.0|USB 3.1|Root Hub|Host Controller' \
    | head -20 \
    | sed 's/^/  /'

  banner "Verdict"
  if [[ -n "$cu" ]] && echo "$cu" | grep -q usbmodem; then
    ok "Board enumerated as CDC — proceed to the sniffer."
  elif [[ -n "$st" ]] && echo "$st" | grep -q 0xdf11; then
    warn "Board is in DFU bootloader.  Power-cycle with no button held."
  elif [[ -n "$st" ]]; then
    warn "STM32 present on bus but not CDC.  Firmware may be stuck."
    info "Try: power-cycle the board; verify you're using the DATA port (ADUM3160 face)."
  else
    bad "Board not visible on the USB bus at all."
    info "Likely causes, in order:"
    info "  a) Cables swapped: Mac → DATA (ADUM3160 face); battery → POWER (SN6505 face)."
    info "  b) Battery bank in idle cutout: try a wall USB charger instead."
    info "  c) Mac cable is charge-only: swap for a known data-rated cable."
  fi
  printf '\n'
}

if [[ "$watch_mode" == 1 ]]; then
  trap 'printf "\n\033[1;36mstopped\033[0m\n"; exit 0' INT
  while true; do
    clear
    run_once
    sleep 2
  done
else
  run_once
fi
