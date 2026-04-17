# FreeEEG128-alpha — Peripheral Inventory & Firmware-Rewrite Targets

Audit of the existing NeuroIDSS alpha board (KiCAD + `.ioc` + `main.c`) so we
know every chip that needs firmware support and every subsystem the rewrite
must own. Source of truth before touching `firmware-stm32cubeide-1.5.1/`.

Audit based on:
- `firmware-freeeeg128-alpha/KiCAD/*.kicad_sch` (schematic hierarchy)
- `firmware-stm32cubeide-1.5.1/STM32H743ZI_ads131_80MHz.ioc` (STM32CubeMX config)
- `firmware-stm32cubeide-1.5.1/Src/main.c` (peripheral init + runtime code)

---

## 1. Chip-level inventory (from schematics)

### 1.1 Compute

| Ref         | Part                | Notes                                                      |
| ----------- | ------------------- | ---------------------------------------------------------- |
| MCU         | **STM32H743ZITx**   | Cortex-M7 @ 480 MHz, 2 MB flash, 1 MB RAM, DP-FPU, L1 cache |
| HSE crystal | 16 MHz              | High-speed external clock for the MCU                     |
| LSE crystal | 32.768 kHz          | RTC / low-speed domain                                     |
| ADC clock   | FXO-SM7 (SMD7050)   | External oscillator — almost certainly the shared master clock for all 16 ADS131M08s |

### 1.2 Analog front-end (isolated side)

| Ref   | Part                     | Qty | Role                                              |
| ----- | ------------------------ | --- | -------------------------------------------------- |
| ADC   | **TI ADS131M08**         | 16  | 8-ch, 24-bit, simultaneous-sampling Δ-Σ + differential amp. Per-ADC DRDY, per-ADC RESET (suggested by legacy `reset_ports[]` array in `main.c:262`), daisy-chained or per-CS SPI. |
| VREF  | **TI REF2025**           | 1   | Dual 2.5 V / VCOM precision reference (sets ADS131 Vref; the `µV = raw * 1.25e6/((2^23−1)*32)` formula uses Vref 1.25 V because gain 32 halves the input-referred range) |
| PREF  | **ADR4525**              | 1   | 2.5 V precision reference, ±0.02 %, 1.5 µVpp noise. Separate ref tree (likely for bias/REF_IN on ADS or a separate rail).  |

### 1.3 Isolation barrier (this is a medically-isolated design — do not break it)

| Ref        | Part                 | Purpose                                                        |
| ---------- | -------------------- | -------------------------------------------------------------- |
| ISO_USB    | **ADuM3160**         | USB 1.1 (Full-Speed) digital isolator — isolates D+/D- between host and MCU |
| ISO_UART   | **ADuM1402BRWZ**     | Quad digital isolator for an isolated UART channel           |
| ISO_SPI    | **ISO7341C**         | 3-ch digital isolator on the SPI path to (some of) the ADCs  |
| ISO1       | **ISO7341C**         | Second 3-ch isolator (additional SPI / control lines)        |
| POWER      | **SN6505B**          | Push-pull transformer driver for isolated DC-DC               |
| POWER      | **Würth 750315371**  | Transformer for the SN6505 isolated supply                    |
| USB ESD    | SP0503BAHTG          | ESD protection on USB data lines                              |

### 1.4 Power tree

| Ref   | Part                  | Output  | Purpose                                 |
| ----- | --------------------- | ------- | --------------------------------------- |
| AVDD  | **LP5907**            | low-noise analog | ADS131M08 analog supply                 |
| VDD   | **LP5907**            | low-noise        | ADS131M08 / reference digital logic supply |
| IOVDD | **LP5907**            | low-noise        | ADS131M08 IO supply                     |
| —     | **ADP7118AUJZ-3.3**   | 3.3 V           | Secondary regulator (likely MCU-side or USB-side) |

Three **LP5907** ultra-low-noise LDOs plus the ADP7118 gives a very clean analog rail.
Rails are referenced across the isolation barrier — expect separate grounds (AGND_ISO, DGND_ISO, GND_HOST).

### 1.5 Motion / auxiliary

| Ref  | Part                  | Purpose                                                              |
| ---- | --------------------- | -------------------------------------------------------------------- |
| IMU  | **ST LSM6DS3TR**      | 6-axis accel/gyro over I²C (artifact/motion capture — currently initialized but not published in the paper's capture software) |

### 1.6 Connectors & external IO

| Ref         | Part                   | Notes                                                        |
| ----------- | ---------------------- | ------------------------------------------------------------- |
| microSD     | Molex **473521001**    | push-push microSD socket → SDMMC1                             |
| USB_DATA    | USB-B Micro            | host data link (isolated via ADuM3160)                        |
| USB_POWER   | USB-B Micro            | separate power input (not carrying data)                      |
| 2×3 header  | `Conn_02x03`           | ISO_SPI debug / programming header                             |
| 2×3 header  | `Conn_02x03`           | ISO_UART header                                                |
| 2×4 header  | `Conn_02x04`           | additional ISO1 header                                          |

### 1.7 Misc

- Schottky diodes (D_Schottky) on USB power path
- DA2303 symbol (part unclear — verify in BOM; possibly an LDO or protection device)
- Numerous 100 nF decoupling + 10 µF / 22 µF bulk caps per block

---

## 2. STM32H743 peripherals in use (from `.ioc`)

| STM32 IP        | Allocated to                                                                 | DMA?                                       |
| --------------- | ---------------------------------------------------------------------------- | ------------------------------------------ |
| **CORTEX_M7**   | ICache **on**, **DCache OFF**, MPU = NULL                                    | —                                          |
| **SPI1**        | ADS131M08 group (CS bank)                                                     | no DMA requests listed                      |
| **SPI2**        | ADS131M08 group                                                               | DMA1 Stream 0 (RX), Stream 1 (TX)           |
| **SPI3**        | ADS131M08 group                                                               | DMA1 Stream 3 (RX), Stream 5 (TX)           |
| **SPI4**        | ADS131M08 group                                                               | DMA2 Stream 2 (RX), Stream 3 (TX)           |
| **SPI5**        | ADS131M08 group                                                               | DMA2 Stream 5 (RX), Stream 6 (TX)           |
| **SPI6**        | ADS131M08 group (BDMA candidate; no D1/D2 DMA stream allocated)                | no                                          |
| **USART1**      | isolated UART over ADuM1402 (currently just `HAL_UART_Transmit` debug/print)  | no                                          |
| **I2C1**        | LSM6DS3TR IMU (most likely)                                                   | no                                          |
| **I2C2**        | spare / second I2C bus                                                        | no                                          |
| **SDMMC1**      | microSD + FatFS                                                               | handled by SDMMC internal                   |
| **USB_DEVICE**  | CDC device (**labeled `VS_USB_DEVICE_CDC_HS`** in the `.ioc`)                 | —                                           |
| **USB_OTG_HS**  | allocated in IPs, but PB14/PB15 are `Device_Only_FS` — conflict to resolve    | —                                           |
| **TIM1**        | paced sample-clock generator: `TRGO` feeds DMA1_Stream7 (CIRCULAR, M→P); `UP` feeds DMA2_Stream1 (CIRCULAR, M→P). Typical pattern for GPIO-toggle / CS pulse arrays synchronized to the sample clock. | TIM1_TRIG, TIM1_UP |
| **TIM8**        | master clock, combined reset+trigger mode. `TRGO` feeds DMA1_Stream4 (CIRCULAR). TIM8 is the outer cascade driving TIM1. | TIM8_TRIG |
| **FATFS**       | via SDIO VS pin                                                               | —                                           |
| **DMA1 + DMA2** | both enabled; used by SPI2/3/4/5 + TIM1/TIM8 trigger streams                   | —                                           |
| **NVIC**        | custom priorities for DRDY / DMA complete                                     | —                                           |

### Notable gaps in current firmware

- `ad7779.c` / `ad7779.h` still in `Src/Inc` — **legacy from FreeEEG32 (AD7779 ADCs)**. Likely dead code; delete on rewrite.
- `//#include "W5500/..."` + `//W5500_Select(...)` blocks — commented-out WIZnet Ethernet-over-SPI bring-up. If we want network streaming we can revive this (SPI + CS pin already wired to a header).
- No IWDG / WWDG configured — **watchdog absent** despite long sessions.
- No RTC use despite LSE 32.768 kHz crystal being populated.
- No DFU / bootloader handoff code.

---

## 3. What the firmware rewrite must own

Grouped by subsystem. Anything marked **new** is not in the current codebase.

### 3.1 ADS131M08 array (16 chips, 128 channels)

- 6-SPI-bus layout, up to 3 ADCs per bus via per-CS selection.
- Master clock from FXO-SM7 → all 16 ADCs (off-chip, not our problem).
- **SYNC / RESET**: legacy code references `AD*_RESET_GPIO_Port`. Enumerate every reset + SYNC line in current pinout; modern firmware must issue a simultaneous SYNC across all 16 to start a 128-channel epoch cleanly.
- **DRDY**: `flag_nDRDY_INTERRUPT` exists — one (or more) shared nDRDY line drives an EXTI; firmware must count DRDYs per epoch and detect drops.
- **CRC**: ADS131M08 ships per-sample CRC — forward it to the host stream (current firmware discards it).
- **Config**: expose per-channel OSR, gain, mux, lead-off detection, GPIO, and bias drive over host command protocol (currently all hardcoded).
- **Sample rate**: make `fMOD / OSR` configurable. 250 Hz is firmware-chosen — chip supports up to ~32 kSPS.
- **TIM1/TIM8 cascade**: current trick generates CS pulse patterns at sample rate via DMA-driven GPIO writes. Document it and keep it, or replace with SPI-NSS hardware.

### 3.2 USB CDC link (host interface)

- Decide **FS vs HS** (both configured, conflict in .ioc). ADuM3160 is a **Full-Speed-only isolator** (12 Mbps) — HS cannot pass through it. Lock firmware to FS.
- Budget: 128 ch × 3 bytes × 250 Hz = **96 kB/s raw**. FS (~1 MB/s usable) is ample even at 4 kSPS. HS is unnecessary and would require re-fabbing the isolator.
- **new** Packet framing: length, sequence counter, device timestamp, per-ADC status, end-of-frame CRC. Current stream is raw integers, paper notes save-to-disk took "a few 1000s recordings" to stabilise.
- **new** Host→device command channel (configure channels, start/stop, request status).
- **new** USB re-enumeration / stall recovery.

### 3.3 Isolated UART (USART1 via ADuM1402)

- Currently just a `printf` path. Reclaim for:
  - **new** digital trigger/marker input from the **Labstreamer** (TTL on the isolated side — we stay inside the barrier).
  - **new** auxiliary debug console that doesn't interfere with CDC.
- One spare ADuM1402 channel could be a dedicated trigger line if we wire it to a board-edge header.

### 3.4 microSD (SDMMC1 + FatFS)

- Wired and initialized in current firmware — usage in `main.c` via `sd_diskio.c`, `fatfs.c` — but paper's capture flow doesn't use it.
- **new** Dual-sink streaming: CDC to host + SD log in parallel, with sector-write retries and time-stamped file rotation. Matters for unattended / battery-powered captures.
- **new** On-device session metadata (timestamp, channel map, config) written as a sidecar JSON per file.

### 3.5 IMU (LSM6DS3TR, I²C1)

- **Currently initialized, not published in the data stream.**
- **new** Sample at (say) 104 Hz, low-pass, and interleave an IMU packet into the CDC stream for motion-artifact flags.
- **new** Expose tap / wake-up interrupts — useful as auto-start trigger.

### 3.6 RTC + LSE

- LSE 32.768 kHz populated but RTC not configured.
- **new** Enable RTC for device-side timestamping of SD-logged files (essential when the device streams without a host).

### 3.7 Power & isolation supervision

- No supervisor/PG signals surfaced in .ioc. Verify via schematic whether SN6505/LP5907 have PG pins routed to MCU GPIOs; if so, expose as a health telemetry field.
- **new** Under-voltage / brown-out handling: on rail dip, stop SPI DMAs cleanly and re-SYNC on recovery.

### 3.8 Watchdog + recovery

- **new** IWDG with 2–5 s timeout around the main loop; pet from the USB / SD flush path.
- **new** Reset-cause reporting in a boot banner packet.

### 3.9 Bootloader / firmware update

- **new** Expose a "reboot to DFU" command on the CDC control channel — STM32H7 has a built-in USB DFU bootloader. Avoids the ST-Link/JTAG ritual for updates.
- Current firmware writes directly to flash with no bootloader partitioning.

### 3.10 Ethernet option (revival)

- Commented W5500 code in `main.c` points to a SPI-Ethernet pathway using one of the spare SPI buses + the 2×3 or 2×4 header on the isolated side.
- If wired: **new** LSL-over-UDP outlet from the device itself. Decide whether to invest; USB FS is fine for 128 ch × ≤4 kSPS.

### 3.11 Cache & MPU

- DCache is **disabled** — classic workaround for "DMA buffers in cached memory become stale." The rewrite should:
  - Put DMA buffers in a dedicated non-cacheable region via MPU, or
  - Use `SCB_CleanInvalidateDCache_by_Addr` around buffer swaps, and
  - Re-enable DCache — meaningful speed win for DSP and per-packet CRC.

---

## 4. Modern acquisition-device services to add

Feature list for the new firmware so the board can be used as a first-class
research device (not just a research prototype):

| Service                                 | Status       | Notes                                                                                                                         |
| --------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| CDC-ACM streaming with framed packets   | rewrite      | seq counter, µs device timestamp, ADC-status, CRC                                                                              |
| Host command protocol                   | new          | start/stop, sample rate, per-channel gain/mux, lead-off, IMU on/off, SD logging on/off                                         |
| LSL outlet (device-side over Ethernet)  | optional     | only if we revive W5500                                                                                                        |
| Trigger input                           | new          | via isolated UART (ADuM1402 spare channel) or a dedicated GPIO routed through an isolator on a rev                              |
| Impedance check                         | new          | ADS131M08 lead-off current sources + mag/phase sweep                                                                           |
| Motion publishing                       | new          | LSM6DS3 packets alongside EEG                                                                                                   |
| On-device SD logging                    | rewrite      | dual-sink; continues across USB disconnects                                                                                    |
| Device-side timestamping (RTC)          | new          | monotonic µs counter + RTC wall-clock                                                                                          |
| OTA / DFU mode                          | new          | CDC command → jump to ST system bootloader                                                                                     |
| Watchdog + reset-cause reporting        | new          | IWDG + a boot banner                                                                                                           |
| Per-channel / per-sample CRC forwarding | rewrite      | ADS131M08 already emits CRC; forward it                                                                                        |
| Built-in self-test                      | new          | ADS131M08 internal test pattern + loopback verification on boot                                                                |

---

## 5. Known issues / cleanups for the rewrite

1. **Dead code** — purge `ad7779.c/h`, W5500 Ethernet blocks if we're not reviving them, and commented-out LCD code (`LCD_SWRESET`).
2. **DCache disabled** — replace with MPU-backed non-cacheable DMA region.
3. **USB HS vs FS conflict** in `.ioc` — lock to FS (isolator is FS-only).
4. **No watchdog** — long-session reliability will suffer.
5. **No RTC** despite populated LSE crystal.
6. **No DFU handoff** — painful update path for an alpha unit.
7. **Hardcoded 250 Hz** — make configurable.
8. **Channel map is firmware-internal** — publish it in a capability descriptor over the USB control pipe so hosts don't hardcode it.
9. **Raw-only output** — host has to re-derive µV and has no CRC; add framing + status fields.
10. **Alpha firmware predates STM32Cube HAL v1.10+** — re-bootstrap `.ioc` on a current CubeMX so we track modern STM32H7 HAL bug fixes (DMA, SDMMC, USB).
11. **Paper reports "first few 1000s recordings save took longer"** — current save path has no flow control; rewrite needs back-pressure and drop counters.

---

## 6. Pinout / channel-map audit tasks

Before any firmware change, do these sanity checks:

- [ ] Enumerate every GPIO listed in `Mcu.Pin*` against the `MCU.kicad_sch` to label function (ADC_CSn, ADC_DRDYn, ADC_RESETn, IMU_INT, SD_DETECT, LED, button, etc.).
- [ ] Confirm the ADC-to-SPI mapping: which of SPI1/2/3/4/5/6 owns which of the 16 ADS131M08 chips (the paper's "ADC1..ADC16" numbering does not necessarily match SPI instance numbering).
- [ ] Validate that the ADC↔channel-label table in `HARDWARE.md` §2 matches the firmware's `ADCn → channel[0..7]` array (`main.c` and `ads131m0x.c`).
- [ ] Identify whether the ISO_UART spare channels expose a **host-side TTL trigger input** routable to the Labstreamer.
- [ ] Identify power-good / fault pins on the LP5907s and SN6505 that could be tied to MCU GPIOs for telemetry.
