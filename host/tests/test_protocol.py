"""Round-trip tests for the framed-packet protocol and synthetic source."""

from __future__ import annotations

import pytest

from freeeeg128 import protocol, synthetic


def test_magic_and_header_size():
    assert protocol.MAGIC == b"FE"
    assert protocol.HDRLEN_V1 == 22


def test_packet_roundtrip_eeg():
    # Fake 128-ch, 1-sample EEG frame
    n_ch, n_smp = 128, 1
    samples_u24 = bytes((i & 0xFF) for i in range(n_ch * n_smp * 3))
    payload = protocol.encode_eeg_frame(samples_u24, n_ch=n_ch, n_smp=n_smp, sr_hz=250)

    raw = protocol.encode(protocol.PacketType.EEG_FRAME, seq=42, ts_us=123_456_789, payload=payload)
    assert raw[:2] == protocol.MAGIC
    assert raw[2] == int(protocol.PacketType.EEG_FRAME)

    parser = protocol.PacketParser()
    pkts = parser.feed(raw)
    assert len(pkts) == 1
    p = pkts[0]
    assert p.ptype == protocol.PacketType.EEG_FRAME
    assert p.seq == 42
    assert p.ts_us == 123_456_789
    assert p.payload == payload
    assert parser.drop_count == 0


def test_packet_streamed_byte_by_byte():
    """Parser survives arbitrary byte-chunking of the stream."""
    payload = protocol.encode_eeg_frame(b"\x00" * (128 * 3), n_ch=128, n_smp=1, sr_hz=250)
    raw = protocol.encode(1, 0, 0, payload) + protocol.encode(1, 1, 1000, payload)
    parser = protocol.PacketParser()
    got = []
    for b in raw:
        got.extend(parser.feed(bytes([b])))
    assert len(got) == 2
    assert [p.seq for p in got] == [0, 1]
    assert parser.drop_count == 0


def test_resync_after_garbage():
    """Injected garbage in the byte stream is skipped and CRC passes on the next packet."""
    payload = protocol.encode_eeg_frame(b"\x11" * (128 * 3), n_ch=128, n_smp=1, sr_hz=250)
    good = protocol.encode(1, 5, 9999, payload)
    garbage = b"\x99\xAB\xCD" * 10
    parser = protocol.PacketParser()
    pkts = parser.feed(garbage + good + garbage + good)
    # Both packets recovered
    assert len(pkts) == 2
    assert pkts[0].seq == 5
    assert pkts[1].seq == 5
    assert parser.drop_count > 0  # should have flagged resync events


def test_crc_failure_is_rejected():
    payload = protocol.encode_eeg_frame(b"\x00" * (128 * 3), n_ch=128, n_smp=1, sr_hz=250)
    raw = bytearray(protocol.encode(1, 0, 0, payload))
    raw[50] ^= 0xFF  # corrupt one payload byte
    parser = protocol.PacketParser()
    pkts = parser.feed(bytes(raw))
    assert pkts == []
    assert parser.drop_count > 0


def test_int24_roundtrip():
    vals = [0, 1, -1, 42, -42, (1 << 23) - 1, -(1 << 23), 0x123456, -0x123456]
    b = protocol.int32_to_samples_u24(vals)
    assert len(b) == len(vals) * 3
    back = protocol.samples_u24_to_int32(b)
    assert back == vals


def test_raw_to_uv_matches_alpha_firmware_formula():
    # full-scale positive = 1.25 V / 32 = 39062.5 µV
    fs_uv = protocol.raw_to_uv((1 << 23) - 1, gain=32, vref_v=1.25)
    assert abs(fs_uv - 39062.495) < 1.0
    assert protocol.raw_to_uv(0) == 0.0


def test_synthetic_source_produces_parseable_stream():
    src = synthetic.SyntheticSource(n_channels=128, sample_rate_hz=250)
    parser = protocol.PacketParser()
    for _ in range(500):
        parser.feed(src.next_packet())
    # Should have 500 EEG packets, no drops
    assert parser.packet_count == 500
    assert parser.drop_count == 0


def test_command_roundtrip():
    payload = protocol.encode_command(protocol.CmdId.SET_RATE, cmd_seq=7,
                                       args=(500).to_bytes(2, "little"))
    raw = protocol.encode(protocol.PacketType.COMMAND, seq=0, ts_us=0, payload=payload)
    parser = protocol.PacketParser()
    [pkt] = parser.feed(raw)
    cmd_id, cmd_seq, args = protocol.decode_command(pkt.payload)
    assert cmd_id == protocol.CmdId.SET_RATE
    assert cmd_seq == 7
    assert int.from_bytes(args, "little") == 500
