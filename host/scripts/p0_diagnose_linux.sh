#!/usr/bin/env bash
# P0.1 — FreeEEG128 / FreeEEG32 USB enumeration diagnostic (Linux).
#
# Linux analogue of p0_diagnose.sh (macOS version).  Reports:
#
#   1. /dev/ttyACM* and /dev/ttyUSB*
#   2. STMicro / STM32 (VID 0483) entries in lsusb
#   3. Full lsusb tree
#   4. Last 20 lines of dmesg filtered for usb / cdc_acm
#
# Then prints a one-line verdict.
#
# Usage:
#     host/scripts/p0_diagnose_linux.sh            # one-shot
#     host/scripts/p0_diagnose_linux.sh --watch    # loop every 2 s

set -u

watch_mode=0
[[ "${1:-}" == "--watch" ]] && watch_mode=1

banner() { printf "\n\033[1;36m── %s ──\033[0m\n" "$1"; }
ok()     { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
warn()   { printf "  \033[1;33m!\033[0m %s\n" "$*"; }
bad()    { printf "  \033[1;31m✗\033[0m %s\n" "$*"; }
info()   { printf "  %s\n" "$*"; }

run_once() {
  printf '\n\033[1m[%s]  FreeEEG USB diagnostic (Linux)\033[0m\n' "$(date +%H:%M:%S)"

  banner "1. /dev/ttyACM* and /dev/ttyUSB* serial devices"
  local tty
  tty=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true)
  if [[ -z "$tty" ]]; then
    bad "no USB serial devices in /dev/ttyACM*  /dev/ttyUSB*"
  else
    while IFS= read -r d; do ok "$d"; done <<<"$tty"
  fi

  banner "2. STMicro / STM32 devices in lsusb (VID 0483)"
  local st
  st=$(lsusb 2>/dev/null | grep -iE '0483:|STMicro|STM|NeuroIDSS|Free.?EEG' || true)
  if [[ -z "$st" ]]; then
    bad "no STMicro device on the bus"
  else
    while IFS= read -r line; do ok "$line"; done <<<"$st"
    if echo "$st" | grep -qE '0483:5740'; then
      ok "→ 0483:5740 = STM32 Virtual COM Port (CDC app)"
    fi
    if echo "$st" | grep -qE '0483:df11'; then
      warn "→ 0483:df11 = STM32 DFU BOOTLOADER — firmware not running"
    fi
  fi

  banner "3. Full lsusb (filtered, no hubs / audio)"
  lsusb 2>/dev/null \
    | grep -vE 'Linux Foundation.*root hub|Linux.*Hub|Intel .* (PCH|Camera|Integrated|Bluetooth|Audio)|Realtek.*Hub|Generic Hub' \
    | sed 's/^/  /' | head -25

  banner "4. dmesg USB activity (last 20 USB/CDC lines)"
  local dm
  if command -v journalctl >/dev/null 2>&1; then
    dm=$(sudo journalctl -k --since "2 minutes ago" 2>/dev/null \
         | grep -iE 'usb|cdc_acm|stm32' | tail -20)
  fi
  if [[ -z "${dm:-}" ]]; then
    dm=$(dmesg 2>/dev/null | grep -iE 'usb|cdc_acm|stm32' | tail -20 || true)
  fi
  if [[ -z "${dm:-}" ]]; then
    warn "dmesg unavailable (try: sudo dmesg -T | grep -i usb | tail -20)"
  else
    printf '%s\n' "$dm" | sed 's/^/  /'
  fi

  banner "Verdict"
  if [[ -n "$tty" ]]; then
    ok "CDC device present — proceed to the sniffer."
    info "Run: python3 host/scripts/p0_sniff.py $(echo "$tty" | head -1)"
  elif [[ -n "$st" ]] && echo "$st" | grep -qE '0483:df11'; then
    warn "Board is in DFU bootloader.  Power-cycle with no button held."
  elif [[ -n "$st" ]]; then
    warn "STM32 present on bus but not CDC.  Firmware may be stuck."
  else
    bad "Board not visible on the USB bus at all."
    info "Likely causes:"
    info "  a) Cables in wrong ports — swap Mac/host vs battery between the two Micro-B."
    info "  b) Battery bank idle cutoff — try a wall charger or the host PC's other USB port."
    info "  c) Mac/host cable is charge-only — test it on any known Micro-B device."
    info "  d) USB port on host is misbehaving — try a different port."
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
