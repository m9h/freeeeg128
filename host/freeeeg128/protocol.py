"""Wire-protocol encode/decode for FreeEEG128 framed packets.

Implements docs/packet-format.md v1.  Pure Python — no dependencies beyond
the standard library.  Designed so the same code parses synthetic streams
today and the real STM32H743 firmware's USB-CDC stream tomorrow.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum

MAGIC = b"\x46\x45"  # "FE"
HDRLEN_V1 = 22
PROTO_VERSION = 0x01


class PacketType(IntEnum):
    EEG_FRAME    = 0x01
    IMU_FRAME    = 0x02
    STATUS       = 0x03
    IMPEDANCE    = 0x04
    LOG          = 0x05
    TRIGGER      = 0x06   # reserved for future
    COMMAND      = 0x10
    COMMAND_ACK  = 0x11
    CAPABILITIES = 0x20
    BOOT_BANNER  = 0x7F


class CmdId(IntEnum):
    START             = 0x01
    STOP              = 0x02
    GET_CAPS          = 0x03
    SET_RATE          = 0x04
    SET_GAIN          = 0x05
    SET_MUX           = 0x06
    LEAD_OFF_START    = 0x07
    LEAD_OFF_STOP     = 0x08
    SET_IMU_RATE      = 0x09
    SD_BEGIN          = 0x0A
    SD_END            = 0x0B
    SET_TRIGGER_MODE  = 0x0C
    GET_STATUS        = 0x0D
    SYNC_TIME         = 0x0E
    SELF_TEST         = 0x0F
    REBOOT            = 0x80
    REBOOT_DFU        = 0x81
    NOP               = 0xFF


# ---------------------------------------------------------------------------
# Framing
# ---------------------------------------------------------------------------

_HDR_STRUCT = struct.Struct("<2sBBHIIQ")  # magic, type, ver, hdrlen, pktlen, seq, ts_us
assert _HDR_STRUCT.size == HDRLEN_V1


@dataclass(frozen=True)
class Packet:
    """A fully framed and validated packet."""
    ptype: int
    version: int
    seq: int
    ts_us: int
    payload: bytes

    def to_bytes(self) -> bytes:
        pktlen = len(self.payload)
        hdr = _HDR_STRUCT.pack(
            MAGIC, self.ptype, self.version, HDRLEN_V1, pktlen, self.seq, self.ts_us,
        )
        body = hdr + self.payload
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return body + struct.pack("<I", crc)


def encode(ptype: int, seq: int, ts_us: int, payload: bytes,
           version: int = PROTO_VERSION) -> bytes:
    """Encode one framed packet."""
    return Packet(ptype, version, seq, ts_us, payload).to_bytes()


class ParseError(Exception):
    pass


class PacketParser:
    """Streaming byte-oriented parser that recovers from resync events.

    Feed bytes via ``feed()``; it yields complete ``Packet`` instances as
    they become available.  Tracks a ``drop_count`` incremented on any CRC
    failure or sequence-number gap.
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self._expected_seq: int | None = None
        self.drop_count = 0
        self.byte_count = 0
        self.packet_count = 0

    def feed(self, data: bytes) -> list[Packet]:
        """Append bytes; return any complete packets recovered."""
        self._buf.extend(data)
        self.byte_count += len(data)
        out: list[Packet] = []
        while True:
            pkt = self._try_one()
            if pkt is None:
                break
            out.append(pkt)
        return out

    def _try_one(self) -> Packet | None:
        buf = self._buf
        # Need at least a header to make progress
        while len(buf) >= HDRLEN_V1 and buf[:2] != MAGIC:
            # Scan forward until we find the magic
            idx = buf.find(MAGIC[0:1], 1)
            if idx < 0:
                # No MAGIC[0] anywhere; discard everything but keep the last byte in case
                # it's the start of a future MAGIC
                del buf[:-1]
                return None
            # Drop everything before the candidate MAGIC[0]
            del buf[:idx]
            self.drop_count += 1
        if len(buf) < HDRLEN_V1:
            return None

        try:
            magic, ptype, version, hdrlen, pktlen, seq, ts_us = _HDR_STRUCT.unpack_from(buf, 0)
        except struct.error:
            return None

        if magic != MAGIC:
            # shouldn't happen after the scan above, but be defensive
            del buf[:1]
            self.drop_count += 1
            return None

        if hdrlen != HDRLEN_V1:
            # future protocol version we don't understand — skip the byte and resync
            del buf[:1]
            self.drop_count += 1
            return None

        total_len = HDRLEN_V1 + pktlen + 4
        if len(buf) < total_len:
            return None  # need more bytes

        body = bytes(buf[:HDRLEN_V1 + pktlen])
        crc_bytes = bytes(buf[HDRLEN_V1 + pktlen : total_len])
        got_crc, = struct.unpack("<I", crc_bytes)
        want_crc = zlib.crc32(body) & 0xFFFFFFFF
        if got_crc != want_crc:
            # CRC fail: drop the first byte and try to resync
            del buf[:1]
            self.drop_count += 1
            return None

        # CRC ok: consume the full packet
        del buf[:total_len]
        payload = body[HDRLEN_V1:]

        if self._expected_seq is not None and seq != self._expected_seq:
            gap = (seq - self._expected_seq) & 0xFFFFFFFF
            self.drop_count += gap
        self._expected_seq = (seq + 1) & 0xFFFFFFFF

        self.packet_count += 1
        return Packet(ptype=ptype, version=version, seq=seq, ts_us=ts_us, payload=payload)


# ---------------------------------------------------------------------------
# EEG frame payload
# ---------------------------------------------------------------------------

_EEG_HDR = struct.Struct("<HHHH16s")  # n_ch, n_smp, flags, sr_hz, adc_status[16]


def encode_eeg_frame(samples_u24: bytes, n_ch: int, n_smp: int,
                     sr_hz: int, flags: int = 0,
                     adc_status: bytes = b"\x00" * 16) -> bytes:
    """Pack an EEG_FRAME payload from raw big-endian int24 samples.

    ``samples_u24`` must be channel-major: ch0_smp0, ch0_smp1, …, ch1_smp0, …
    with each sample as 3 big-endian bytes (ADS131M08 native order).
    """
    if len(adc_status) != 16:
        raise ValueError("adc_status must be 16 bytes")
    expected = n_ch * n_smp * 3
    if len(samples_u24) != expected:
        raise ValueError(f"samples_u24 length {len(samples_u24)} != n_ch×n_smp×3 = {expected}")
    hdr = _EEG_HDR.pack(n_ch, n_smp, flags, sr_hz, adc_status)
    return hdr + samples_u24


def decode_eeg_frame(payload: bytes) -> tuple[int, int, int, int, bytes, bytes]:
    """Unpack an EEG_FRAME payload.

    Returns ``(n_ch, n_smp, flags, sr_hz, adc_status, samples_u24)``.
    """
    if len(payload) < _EEG_HDR.size:
        raise ParseError("EEG_FRAME payload too short for header")
    n_ch, n_smp, flags, sr_hz, adc_status = _EEG_HDR.unpack_from(payload, 0)
    samples_u24 = payload[_EEG_HDR.size :]
    if len(samples_u24) != n_ch * n_smp * 3:
        raise ParseError(
            f"EEG_FRAME samples length {len(samples_u24)} != n_ch×n_smp×3 = {n_ch*n_smp*3}"
        )
    return n_ch, n_smp, flags, sr_hz, adc_status, samples_u24


def samples_u24_to_int32(samples_u24: bytes) -> list[int]:
    """Decode N big-endian int24 samples into a list of signed Python ints."""
    out = []
    for i in range(0, len(samples_u24), 3):
        b0, b1, b2 = samples_u24[i], samples_u24[i + 1], samples_u24[i + 2]
        v = (b0 << 16) | (b1 << 8) | b2
        if v & 0x800000:
            v -= 0x1000000
        out.append(v)
    return out


def int32_to_samples_u24(values: list[int] | tuple[int, ...]) -> bytes:
    """Encode signed ints as big-endian int24 bytes."""
    out = bytearray()
    for v in values:
        u = v & 0xFFFFFF
        out.append((u >> 16) & 0xFF)
        out.append((u >> 8) & 0xFF)
        out.append(u & 0xFF)
    return bytes(out)


# ---------------------------------------------------------------------------
# ADC raw → µV (matches alpha firmware formula)
# ---------------------------------------------------------------------------

def raw_to_uv(raw: int, gain: int = 32, vref_v: float = 1.25) -> float:
    """Convert a raw ADS131M08 int24 sample to microvolts."""
    fullscale = (1 << 23) - 1
    return raw * (vref_v * 1_000_000.0) / (fullscale * gain)


# ---------------------------------------------------------------------------
# COMMAND / COMMAND_ACK
# ---------------------------------------------------------------------------

_CMD_HDR = struct.Struct("<HHBB")  # cmd_id, cmd_seq, argc, _reserved
_ACK_HDR = struct.Struct("<HHHH")  # cmd_id, cmd_seq, result, reply_len


def encode_command(cmd_id: int, cmd_seq: int, args: bytes = b"") -> bytes:
    """Build a COMMAND packet payload (does not frame — use encode() for that)."""
    return _CMD_HDR.pack(cmd_id, cmd_seq, len(args), 0) + args


def decode_command(payload: bytes) -> tuple[int, int, bytes]:
    cmd_id, cmd_seq, argc, _ = _CMD_HDR.unpack_from(payload, 0)
    args = payload[_CMD_HDR.size :]
    if len(args) < argc:
        raise ParseError("COMMAND argc mismatch")
    return cmd_id, cmd_seq, args


def encode_command_ack(cmd_id: int, cmd_seq: int, result: int, reply: bytes = b"") -> bytes:
    return _ACK_HDR.pack(cmd_id, cmd_seq, result, len(reply)) + reply


def decode_command_ack(payload: bytes) -> tuple[int, int, int, bytes]:
    cmd_id, cmd_seq, result, reply_len = _ACK_HDR.unpack_from(payload, 0)
    reply = payload[_ACK_HDR.size : _ACK_HDR.size + reply_len]
    return cmd_id, cmd_seq, result, reply
