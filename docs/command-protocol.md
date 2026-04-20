# FreeEEG128 host command protocol v1

Commands sent from host → device. Responses are `COMMAND_ACK` packets
(TYPE 0x11) echoing the command ID and carrying a result code plus any
command-specific reply payload.

**Status**: v1 draft, 2026-04-19. Companion to
[`packet-format.md`](packet-format.md).

## Command packet structure

A `COMMAND` packet (TYPE `0x10`) has this payload:

```
uint16 cmd_id               // see table below
uint16 cmd_seq              // host-assigned; echoed in ACK so host can match response
uint8  argc                 // number of arguments
uint8  _reserved
uint8  args[...]            // command-specific, packed little-endian
```

ACK packet (TYPE `0x11`) payload:

```
uint16 cmd_id               // echoed from request
uint16 cmd_seq              // echoed from request
uint16 result               // 0 = OK; non-zero = error code (see §Error codes)
uint16 reply_len            // length of optional reply block
uint8  reply[reply_len]     // optional per-command data
```

The ACK rides in the normal framed-packet stream, so normal CRC/seq
machinery applies.

## Command table (v1)

| ID    | Name             | Args                                  | Reply | Notes |
| ----- | ---------------- | ------------------------------------- | ----- | ----- |
| `0x01` | `START`         | —                                     | —     | begin EEG streaming |
| `0x02` | `STOP`          | —                                     | —     | stop streaming; flush buffers |
| `0x03` | `GET_CAPS`      | —                                     | `CAPABILITIES` packet content | re-emit capability descriptor |
| `0x04` | `SET_RATE`      | `uint16 sr_hz`                        | —     | e.g. 250, 500, 1000, 2000, 4000 |
| `0x05` | `SET_GAIN`      | `uint8 ch`, `uint8 gain_code`         | —     | per-channel gain (ADS131M08: 1,2,4,8,16,32,64,128) |
| `0x06` | `SET_MUX`       | `uint8 ch`, `uint8 mux_code`          | —     | normal / test signal / shorted / VCM |
| `0x07` | `LEAD_OFF_START`| `uint16 drive_hz`, `uint16 drive_na`  | —     | begin impedance measurement |
| `0x08` | `LEAD_OFF_STOP` | —                                     | —     | end impedance measurement |
| `0x09` | `SET_IMU_RATE`  | `uint16 odr_hz`                       | —     | IMU output rate (0 = disable) |
| `0x0A` | `SD_BEGIN`      | `uint8 filename_len`, filename        | —     | start SD logging (dual-sink with USB) |
| `0x0B` | `SD_END`        | —                                     | —     | close SD file cleanly |
| `0x0C` | `SET_TRIGGER_MODE` | `uint8 mode`                       | —     | 0=off, 1=rising, 2=falling, 3=both |
| `0x0D` | `GET_STATUS`    | —                                     | `STATUS` packet content | on-demand telemetry |
| `0x0E` | `SYNC_TIME`     | `uint64 host_us`                      | `uint64 device_us_at_apply` | clock sync handshake |
| `0x0F` | `SELF_TEST`     | —                                     | bitmask | run BIST: ADC loopback, IMU comms, SD, CRC unit |
| `0x80` | `REBOOT`        | —                                     | — (no ack expected) | soft reset via NVIC |
| `0x81` | `REBOOT_DFU`    | —                                     | — (no ack expected) | jump to STM32 system bootloader for USB DFU flashing |
| `0xFF` | `NOP`           | —                                     | —     | round-trip test |

## Error codes

| Code | Name | Meaning |
| ---- | ---- | ------- |
| `0x0000` | OK | success |
| `0x0001` | UNKNOWN_CMD | `cmd_id` not recognized |
| `0x0002` | BAD_ARG | argument out of range |
| `0x0003` | NOT_READY | device busy (streaming, measuring impedance, etc.) |
| `0x0004` | HW_FAULT | hardware error (e.g. ADC didn't respond) |
| `0x0005` | NOT_SUPPORTED | valid command but this firmware build doesn't support it |
| `0x0006` | SD_ERROR | card not present, write failed, etc. |
| `0x0007` | CRC_MISMATCH | CRC on incoming command failed (this ACK goes back with a fake seq=0) |

## Protocol flow — typical session

```
HOST                                DEVICE
  │                                   │
  │                         BOOT_BANNER (0x7F)
  │                         CAPABILITIES (0x20)
  │                           …stream silent until START…
  │                                   │
  ├── GET_CAPS (0x03) ───────────────▶│
  │◀── ACK + CAPABILITIES reply ───────│
  ├── SET_RATE(250) (0x04) ──────────▶│
  │◀── ACK OK ────────────────────────│
  ├── SET_GAIN per channel (loop) ───▶│
  │◀── ACK OK ────────────────────────│
  ├── LEAD_OFF_START(31.25Hz,6nA) ───▶│
  │◀── ACK OK ────────────────────────│
  │                        IMPEDANCE (0x04) packet streamed
  ├── LEAD_OFF_STOP ─────────────────▶│
  │◀── ACK OK ────────────────────────│
  ├── SD_BEGIN("sess001.bin") ───────▶│
  │◀── ACK OK ────────────────────────│
  ├── START (0x01) ──────────────────▶│
  │◀── ACK OK ────────────────────────│
  │                         EEG_FRAME × N (streaming)
  │                         IMU_FRAME × M
  │                         STATUS × K
  ├── STOP ──────────────────────────▶│
  │◀── ACK OK ────────────────────────│
  ├── SD_END ────────────────────────▶│
  │◀── ACK OK ────────────────────────│
```

## Clock sync handshake (command `SYNC_TIME`, 0x0E)

Host sends its own µs timestamp in the command; device stamps the time at
which it applies the command and includes its device-µs in the reply. Host
can now compute offset = `host_us_sent - device_us_at_apply - RTT/2`. LSL
time correction uses a similar protocol; this gives us a native backup
that doesn't depend on LSL.

## Capability discovery on first connect

1. Host opens CDC serial.
2. Waits up to 500 ms for a `BOOT_BANNER` packet.
3. If not seen, host sends `GET_CAPS` (idempotent; boot-time emission may
   have been missed).
4. Host parses `CAPABILITIES` and configures itself for device's reported
   `n_eeg_channels`, `sr_default_hz`, channel labels, and feature flags.
5. Host sends session-setup commands (`SET_RATE`, `SET_GAIN`, etc.).
6. Host sends `START`.

## Error recovery

- **Lost ACK**: host retransmits after 200 ms timeout using the same `cmd_seq`. Device ignores duplicates (tracks `last_seen_cmd_seq`).
- **Device reboot mid-session**: host sees `BOOT_BANNER` + new
  `CAPABILITIES` with `chip_uid` possibly different (different board).
  Host aborts current session gracefully.
- **USB disconnect**: host closes serial; reopens on next enumeration;
  waits for `BOOT_BANNER`.

## Wire byte-order reminder

Same as EEG payload: all multi-byte integers little-endian in command
headers and args, except where explicitly noted (ADS131M08 sample data is
big-endian int24 in EEG_FRAME).

## Reference implementation

Parser/emitter is in `host/freeeeg128/protocol.py` (`encode_command`,
`decode_ack`). The sync client wrapper `host/freeeeg128/client.py` (to be
written) implements the retry / timeout / reboot-detect state machine
above.
