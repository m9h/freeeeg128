# FreeEEG128 wire protocol — framed packet format v1

This is the **alpha→beta carry-over artifact**. The same packet format
that the STM32H743 firmware emits over USB-CDC (alpha) is what the
STM32H743 emits to the Raspberry Pi Zero 2W companion over USB-CDC in
the beta, and what the Pi re-emits over LSL / WebSocket to downstream
hosts. Protocol version is decoupled from firmware or board revision.

**Status**: v1 draft, 2026-04-19. Not yet running on hardware.

## Design goals

- **Self-describing**: a receiver that has never seen the device can parse
  a stream without out-of-band knowledge; capability info rides on the
  stream.
- **Byte-stream friendly**: USB-CDC is a byte stream, not a packet
  abstraction. Packets must be recoverable after a resync.
- **Per-packet integrity**: CRC32 on every packet so drops / bit-flips
  surface immediately.
- **Device-side timestamping**: every packet carries a 64-bit µs counter
  from the STM32 so latency jitter on the host side doesn't pollute
  event alignment.
- **Drop detection**: monotonic 32-bit sequence counter; host infers drops.
- **Forward-compatible**: `VERSION` field + TLV-style optional fields
  let later revisions extend the packet without breaking older parsers.
- **Byte-order fixed**: all multi-byte header fields are **little-endian**
  (native STM32 order). ADC sample bytes are **big-endian** int24
  (native ADS131M08 order — saves a swap in firmware).

## Stream framing

```
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬───────┐
│ MAGIC  │ TYPE   │ VER    │ HDRLEN │ PKTLEN │  SEQ   │ TS_US  │ PAYLD │ CRC32
│ 2B     │ 1B     │ 1B     │ 2B     │ 4B     │ 4B     │ 8B     │ n B   │ 4B
└────────┴────────┴────────┴────────┴────────┴────────┴────────┴───────┘
 0        2        3        4        6        10       14       22      22+PKTLEN
```

Fixed part is always **22 bytes**. Total packet size = `22 + PKTLEN + 4`.

| Field    | Size | Offset | Endian | Meaning |
| -------- | ---- | ------ | ------ | ------- |
| `MAGIC`  | 2    | 0      | LE     | `0x4546` = ASCII `"FE"` (FreeEEG) — stream-resync marker |
| `TYPE`   | 1    | 2      | —      | packet type, see §Packet types |
| `VER`    | 1    | 3      | —      | protocol version, currently `0x01` |
| `HDRLEN` | 2    | 4      | LE     | header length including MAGIC..TS_US — **22 for v1**; future versions may extend |
| `PKTLEN` | 4    | 6      | LE     | payload length in bytes (excludes header and CRC) |
| `SEQ`    | 4    | 10     | LE     | monotonic packet counter; wraps at 2^32 |
| `TS_US`  | 8    | 14     | LE     | device µs timestamp; source = STM32 RTC+TIM cascade |
| `PAYLD`  | PKTLEN | 22   | mixed  | type-specific payload |
| `CRC32`  | 4    | 22+PKTLEN | LE | CRC-32/ISO-HDLC of everything from MAGIC through end of PAYLD |

### Why not a shorter magic / no magic

USB-CDC does not frame for us — the OS hands bytes to userspace in
arbitrary chunks. After any error the parser needs to resync by
scanning for the magic. A 2-byte magic at ~10^4 packets/s produces a
false-positive rate of ~1 ch/s of random data; combined with the
validate-CRC check, misframing is self-correcting within 1-2 packets.

## Packet types

| TYPE | Name | Direction | PKTLEN | Cadence |
| ---- | ---- | --------- | ------ | ------- |
| `0x01` | `EEG_FRAME` | device→host | variable | sample-rate (e.g. 250 Hz) |
| `0x02` | `IMU_FRAME` | device→host | 28 | ~104 Hz |
| `0x03` | `STATUS`    | device→host | variable | 1 Hz or on-event |
| `0x04` | `IMPEDANCE` | device→host | variable | on `LEAD_OFF_START` |
| `0x05` | `LOG`       | device→host | variable | on event |
| `0x10` | `COMMAND`   | host→device | variable | see command-protocol.md |
| `0x11` | `COMMAND_ACK` | device→host | variable | response to `0x10` |
| `0x20` | `CAPABILITIES` | device→host | variable | boot + on-request |
| `0x7F` | `BOOT_BANNER` | device→host | variable | once at boot |

### 0x01 — `EEG_FRAME`

Payload for a single 128-channel sample at 250 Hz:

```
┌────────┬────────┬────────┬────────┬────────────────┬────────────────┐
│ N_CH   │ N_SMP  │ FLAGS  │ SR_HZ  │ ADC_STATUS     │   SAMPLES      │
│ 2B LE  │ 2B LE  │ 2B LE  │ 2B LE  │ 16 × 1B        │ N_CH×N_SMP×3B  │
└────────┴────────┴────────┴────────┴────────────────┴────────────────┘
  0        2        4        6        8                24 (for 128 ch, 1 smp)
```

| Field | Size | Meaning |
| ----- | ---- | ------- |
| `N_CH` | 2B LE | number of EEG channels in this packet (normally 128) |
| `N_SMP` | 2B LE | samples per channel in this packet (normally 1 for low-latency; may be >1 for batched streams) |
| `FLAGS` | 2B LE | bit 0 = ADC_FAULT, bit 1 = DRDY_MISS, bit 2 = BUFFER_OVERRUN, bit 3 = TEST_MODE |
| `SR_HZ` | 2B LE | nominal sample rate (e.g. 250) |
| `ADC_STATUS` | 16B | one byte per ADS131M08; bit 7 = CRC_FAIL this sample, bits 0-6 = lower 7 bits of chip's STATUS register |
| `SAMPLES` | N_CH × N_SMP × 3B | channel-major: `ch0_smp0, ch0_smp1, …, ch1_smp0, …` — each sample is int24 big-endian (native ADS131M08 output order), two's complement |

For N_CH=128, N_SMP=1: payload = 24 + 128*3 = **408 B**.
Total on-wire packet: 22 + 408 + 4 = **434 B**.
At 250 Hz: **108.5 kB/s** — well within USB-FS 12 Mbps.

Converting a sample to microvolts (matches the alpha-firmware formula):

```
µV = raw_int24 × (1_250_000 / ((2^23 − 1) × gain))
```

With the alpha's default gain of 32 and Vref 1.25 V.

### 0x02 — `IMU_FRAME`

Payload for one LSM6DSOX sample:

| Field | Size | Meaning |
| ----- | ---- | ------- |
| `ACC_X`,Y,Z | 3 × 2B LE | int16 raw accel |
| `GYR_X`,Y,Z | 3 × 2B LE | int16 raw gyro |
| `TEMP` | 2B LE | int16 raw temperature |
| `FLAGS` | 2B LE | bit 0 = FREEFALL, bit 1 = TAP, ... |
| `ODR_HZ` | 2B LE | IMU sample rate (e.g. 104) |

Total payload = 14 B. Packet = 22 + 14 + 4 = 40 B. At 104 Hz = 4.2 kB/s.

### 0x03 — `STATUS`

Periodic telemetry from the device:

```
uint32 seq_drops              // packets firmware failed to emit since boot
uint32 sd_bytes_written       // total bytes written to SD this session
uint16 vbus_mv                // host-side VBUS in mV
uint16 viso_mv                // isolated-side rail in mV (from an ADC sample)
int16  temp_mcu_decic         // STM32 internal temp sensor, 0.1 °C
uint8  iwdg_resets            // watchdog resets since boot
uint8  _reserved
```

Payload = 16 B.

### 0x04 — `IMPEDANCE`

Emitted on `LEAD_OFF_START`. Contains per-channel impedance in kΩ:

```
uint16 n_channels
uint16 flags               // bit 0 = valid (measurement complete)
uint16 drive_hz            // lead-off drive frequency
uint16 drive_na            // lead-off drive current in nanoamps
uint16 z_kohm[n_channels]  // impedance estimate per channel, saturates at 0xFFFF
```

At n_channels = 128, payload = 8 + 256 = 264 B.

### 0x20 — `CAPABILITIES`

Self-description, emitted at boot and on `GET_CAPS`:

```
uint32 magic                 // 0x46454547 "FEEG"
uint32 fw_version            // major<<16 | minor<<8 | patch
uint32 hw_revision           // 0x0100 = alpha, 0x0200 = beta
uint32 chip_uid[3]           // STM32 96-bit unique ID
uint16 n_eeg_channels        // e.g. 128
uint16 adc_resolution_bits   // 24
uint16 sr_default_hz         // e.g. 250
uint16 sr_max_hz             // e.g. 4000
uint32 flags                 // bit 0 = HAS_IMU, bit 1 = HAS_SD, bit 2 = HAS_IMPEDANCE,
                             // bit 3 = HAS_TRIGGER_IN, bit 4 = HAS_RTC, bit 5 = HAS_DFU
char   device_name[32]       // e.g. "FreeEEG128-beta"
char   board_serial[16]
uint8  channel_labels_len    // length of following block in bytes
char   channel_labels[...]   // ASCII '\n'-separated 10-5 labels, e.g. "FP1\nFPz\nFP2\n…"
```

Channel labels ride on the stream so a downstream host doesn't hardcode
the 128 names — when the cap changes, the firmware can update the labels
in one place.

### 0x7F — `BOOT_BANNER`

Once on device reset, first packet emitted:

```
uint32 boot_reason          // from STM32 RCC_CSR
uint32 fw_build_epoch       // compile-time unix epoch
char   git_hash[12]         // short git hash of firmware commit
char   build_flags[16]      // e.g. "RELEASE" / "DEBUG"
```

Payload = 32 B.

## Resync on byte-stream corruption

The host's parser state machine:

1. **SCAN**: read bytes until `MAGIC` pair found (`0x46 0x45`).
2. **HDR**: read 20 more bytes to complete the header.
3. **PAYLD**: read PKTLEN bytes.
4. **CRC**: read 4 bytes, compute CRC32 over bytes 0..(22+PKTLEN-1), compare.
5. If CRC matches → dispatch packet; advance `expected_seq = SEQ + 1`.
6. If CRC mismatches or SEQ ≠ expected_seq → increment `drop_counter`; go back to SCAN. Do not trust PKTLEN from a bad packet.

**Expected overhead**: misframes self-correct within 1-2 packets, typically. At 434 B/packet, a single missed byte is recovered in <10 ms of stream.

## CRC32 definition

ISO-HDLC / CRC-32/ISO-HDLC:

- Polynomial: `0xEDB88320` (reversed `0x04C11DB7`)
- Init: `0xFFFFFFFF`
- Reflected: yes on input and output
- XorOut: `0xFFFFFFFF`

Python reference: `zlib.crc32(packet_bytes[:22+PKTLEN])`
C reference: stock STM32 HAL CRC-32 peripheral, configured per ISO-HDLC.

## Sample stream math

At the alpha's 250 Hz default:

- 250 `EEG_FRAME` packets/sec × 434 B = **108.5 kB/s**
- 104 `IMU_FRAME` packets/sec × 40 B = **4.2 kB/s**
- 1 `STATUS` packet/sec × 20 B = **0.02 kB/s**
- Total ≈ **113 kB/s** — 0.9 Mbps — plenty of margin under USB-FS 12 Mbps

At a 1 kHz sample rate: **434 kB/s ≈ 3.5 Mbps** — still fits USB-FS.
At 4 kHz (chip max at gain 32): **~14 Mbps** — would exceed FS, need HS
(not our plan) or channel batching (`N_SMP > 1`).

## Batching option (future)

For sample rates >1 kHz, firmware can set `N_SMP > 1`. Example: at 2 kHz,
`N_SMP = 4` → 500 packets/sec × (24 + 128×4×3) = 1552 B/packet =
**776 kB/s**. Lower packet rate reduces USB transaction overhead and
host-side wakeup cost.

## Reference implementation

Pure-Python parser/emitter: `host/freeeeg128/protocol.py`. Tests in
`host/tests/`. Synthetic data source (replaces BrainFlow's
`SYNTHETIC_BOARD` for aarch64 since that wheel is broken): `host/freeeeg128/synthetic.py`.

## Open design questions

- Should we add an optional per-sample CRC forwarded from the ADS131M08
  chip's own SPI-frame CRC (the chip provides it natively)? Currently
  rolled into `ADC_STATUS[i] bit 7`. Pro: cheaper on STM32. Con: loses the
  exact-sample identification when one ADC burps mid-packet.
- Should `EEG_FRAME` optionally carry a trigger-channel byte per sample
  for Labstreamer TTL markers? Or should triggers get their own packet
  type (`0x06 TRIGGER`) with µs-precise timestamp? **Lean toward separate
  packet** so precision isn't bounded by EEG sample rate.
- `0x20 CAPABILITIES` boot-time emission — should host be allowed to
  request re-emission without a reset? Currently yes via `GET_CAPS`
  command (see command-protocol.md).
