# NTSPIv3Parser
#
# @Purpose:
#   - This python script can be used to parse NTSPI v3 packets
#
# @Author: Matt Grimes
#          mgrimes@zygosconsulting.com
#
# @Date: 06/01/2026
#
# @ChangeLog:
# 06/01/2026 - Initial Version
#

import struct
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

# Constants
_NTSPI_V3_LEN = 504
_ENDIAN = "!"  # network / big-endian

def _read_ascii_str(buf: bytes, offset: int, length: int) -> str:
    raw = buf[offset:offset+length]
    # strip trailing NULs and ignore non-ascii
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")

def _read_uint8(buf: bytes, offset: int) -> int:
    return struct.unpack_from(_ENDIAN + "B", buf, offset)[0]

def _read_uint16(buf: bytes, offset: int) -> int:
    return struct.unpack_from(_ENDIAN + "H", buf, offset)[0]

def _read_uint32(buf: bytes, offset: int) -> int:
    return struct.unpack_from(_ENDIAN + "I", buf, offset)[0]

def _read_double(buf: bytes, offset: int) -> float:
    return struct.unpack_from(_ENDIAN + "d", buf, offset)[0]

def _parse_inet_header(buf: bytes) -> Dict[str, Any]:
    # offsets per ICD
    # Byte 0: first byte contains MessageVersion (4 bits) and OptionWordCount (4 bits)
    first_byte = _read_uint8(buf, 0)
    message_version = (first_byte >> 4) & 0xF
    option_word_count = first_byte & 0xF
    reserved = _read_uint8(buf, 1)
    message_flags = _read_uint16(buf, 2)
    message_definition_id = _read_uint32(buf, 4)
    message_seq = _read_uint32(buf, 8)
    message_length = _read_uint32(buf, 12)
    acquisition_seconds = _read_uint32(buf, 16)
    acquisition_nanos = _read_uint32(buf, 20)
    acquisition_ts = datetime.fromtimestamp(acquisition_seconds + acquisition_nanos / 1e9, tz=timezone.utc)
    return {
        "MessageVersion": message_version,
        "OptionWordCount": option_word_count,
        "Reserved": reserved,
        "MessageFlags": message_flags,
        "MessageDefinitionID": message_definition_id,
        "MessageDefinitionSequenceNumber": message_seq,
        "MessageLength": message_length,
        "AcquisitionTimestamp": {
            "seconds": acquisition_seconds,
            "nanoseconds": acquisition_nanos,
            "datetime_utc": acquisition_ts,
        },
    }

def _parse_inet_package_header(buf: bytes) -> Dict[str, Any]:
    package_def_id = _read_uint32(buf, 24)
    package_length = _read_uint16(buf, 28)
    status_flags = _read_uint16(buf, 30)
    acquisition_timedelta = _read_uint32(buf, 32)
    return {
        "PackageDefinitionID": package_def_id,
        "PackageLength": package_length,
        "StatusFlags": status_flags,
        "AcquisitionTimeDelta": acquisition_timedelta,
    }

def _parse_packet_time(buf: bytes, offset: int) -> Dict[str, Any]:
    # year(uint16), month(uint8), day(uint8), seconds(uint32), nanoseconds(uint32)
    year = _read_uint16(buf, offset)
    month = _read_uint8(buf, offset + 2)
    day = _read_uint8(buf, offset + 3)
    seconds_since_midnight = _read_uint32(buf, offset + 4)
    nanos = _read_uint32(buf, offset + 8)
    # convert to datetime (UTC) if year>0
    dt = None
    if year != 0:
        try:
            # seconds_since_midnight -> hours/min/sec
            hours = seconds_since_midnight // 3600
            minutes = (seconds_since_midnight % 3600) // 60
            seconds = seconds_since_midnight % 60
            dt = datetime(year, month, day, hours, minutes, seconds, int(nanos/1000), tzinfo=timezone.utc)
        except Exception:
            dt = None
    return {
        "year": year,
        "month": month,
        "day": day,
        "seconds_since_midnight": seconds_since_midnight,
        "nanoseconds": nanos,
        "datetime_utc": dt,
    }

def _parse_event_times(buf: bytes, base_offset: int) -> Dict[str, Any]:
    # Event types at offsets 156..159 (4 bytes)
    event_types = [ _read_uint8(buf, base_offset + i) for i in range(4) ]
    # Event times: 4 blocks of 12 bytes each starting at base_offset+4
    times = {}
    t_off = base_offset + 4
    for i in range(4):
        times[f"event_{i}_time"] = _parse_packet_time(buf, t_off + i*12)
    return {"event_types": event_types, "event_times": times}

def parse_ntspi_v3_packet(packet: bytes) -> Dict[str, Any]:
    """
    Parse a 504-byte NTSPI v3 packet into a dictionary.
    Raises ValueError if packet length is incorrect or sync/version mismatch.
    """
    if not isinstance(packet, (bytes, bytearray)):
        raise TypeError("packet must be bytes or bytearray")
    if len(packet) != _NTSPI_V3_LEN:
        raise ValueError(f"NTSPI v3 packet must be {_NTSPI_V3_LEN} bytes, got {len(packet)}")

    buf = bytes(packet)  # ensure immutable bytes for struct

    # iNET header (0..23)
    inet_header = _parse_inet_header(buf)

    # iNET package header (24..35)
    inet_package = _parse_inet_package_header(buf)

    # NTSPI payload starts at offset 36
    sync = _read_ascii_str(buf, 36, 4)
    if sync != "NTSP":
        raise ValueError(f"Invalid sync constant: expected 'NTSP', got {sync!r}")

    package_format_version = _read_uint32(buf, 40)
    if package_format_version != 0x0003:
        # still parse but warn via field
        version_ok = False
    else:
        version_ok = True

    # IDs (16 bytes each)
    unique_id = _read_ascii_str(buf, 44, 16)
    site_id = _read_ascii_str(buf, 60, 16)
    other_id = _read_ascii_str(buf, 76, 16)
    mission_id = _read_ascii_str(buf, 92, 16)
    group_id = _read_ascii_str(buf, 108, 16)
    case_id = _read_ascii_str(buf, 124, 16)

    # Packet Sequence Count (140..143)
    packet_seq = _read_uint32(buf, 140)

    # Packet Time (144..155)
    packet_time = _parse_packet_time(buf, 144)

    # Event types/times (156..195)
    events = _parse_event_times(buf, 156)

    # Target Data Category (208), Target Fields In Use (209)
    target_data_category = _read_uint8(buf, 208)
    target_fields_in_use = _read_uint8(buf, 209)

    # Event Generation (210..213)
    event_generation = _read_uint32(buf, 210)

    # Target position/velocity/acc/orientation etc per ICD offsets
    def _d(off: int) -> float:
        return _read_double(buf, off)

    target = {
        "position": {
            "x": _d(216),
            "y": _d(224),
            "z": _d(232),
        },
        "velocity": {
            "x": _d(240),
            "y": _d(248),
            "z": _d(256),
        },
        "acceleration": {
            "x": _d(264),
            "y": _d(272),
            "z": _d(280),
        },
        "orientation_deg": {
            "psi": _d(288),
            "theta": _d(296),
            "phi": _d(304),
        },
        "angular_velocity_deg_per_s": {
            "x": _d(312),
            "y": _d(320),
            "z": _d(328),
        },
        "angular_acceleration_deg_per_s2": {
            "x": _d(336),
            "y": _d(344),
            "z": _d(352),
        },
    }

    # Sensor fields in use (360), reserved (361..367)
    sensor_fields_in_use = _read_uint8(buf, 360)
    sensor = {
        "fields_in_use": sensor_fields_in_use,
        "location": {
            "x": _d(368),
            "y": _d(376),
            "z": _d(384),
        },
        "azimuth_deg": _d(392),
        "elevation_deg": _d(400),
        "range_m": _d(408),
        "roll_deg": _d(416),
    }

    # Test data 0..7 (424..452) each uint32
    test_data = {}
    for i in range(8):
        off = 424 + i*4
        test_data[f"test_data_{i}"] = _read_uint32(buf, off)

    data_flag = _read_uint8(buf, 456)
    local_recorder_on = _read_uint8(buf, 457)

    # Track Mode etc (458..463)
    track_mode = _read_uint8(buf, 458)
    sense_mode = _read_uint8(buf, 459)
    gating_mode = _read_uint8(buf, 460)
    manual_event_data = _read_uint8(buf, 461)
    bomb_tone = _read_uint8(buf, 462)
    moving_target = _read_uint8(buf, 463)

    pulse_width_ns = _read_uint32(buf, 464)

    # Error flags (468..471)
    az_err_flag = _read_uint8(buf, 468)
    el_err_flag = _read_uint8(buf, 469)
    range_err_flag = _read_uint8(buf, 470)
    agc_err_flag = _read_uint8(buf, 471)

    # Errors and AGC doubles
    azimuth_error_deg = _d(472)
    elevation_error_deg = _d(480)
    range_error_yards = _d(488)
    agc = _d(496)

    parsed = {
        "inet_header": inet_header,
        "inet_package_header": inet_package,
        "payload": {
            "sync": sync,
            "package_format_version": package_format_version,
            "package_format_version_ok": version_ok,
            "unique_id": unique_id,
            "site_id": site_id,
            "other_id": other_id,
            "mission_id": mission_id,
            "group_id": group_id,
            "case_id": case_id,
            "packet_sequence_count": packet_seq,
            "packet_time": packet_time,
            "events": events,
            "target_data_category": target_data_category,
            "target_fields_in_use": target_fields_in_use,
            "event_generation": event_generation,
            "target": target,
            "sensor": sensor,
            "test_data": test_data,
            "data_flag": data_flag,
            "local_recorder_on": local_recorder_on,
            "track_mode": track_mode,
            "sense_mode": sense_mode,
            "gating_mode": gating_mode,
            "manual_event_data": manual_event_data,
            "bomb_tone": bomb_tone,
            "moving_target": moving_target,
            "pulse_width_ns": pulse_width_ns,
            "error_flags": {
                "azimuth_error_flag": az_err_flag,
                "elevation_error_flag": el_err_flag,
                "range_error_flag": range_err_flag,
                "agc_error_flag": agc_err_flag,
            },
            "errors": {
                "azimuth_error_deg": azimuth_error_deg,
                "elevation_error_deg": elevation_error_deg,
                "range_error_yards": range_error_yards,
                "agc": agc,
            },
        },
    }

    return parsed

