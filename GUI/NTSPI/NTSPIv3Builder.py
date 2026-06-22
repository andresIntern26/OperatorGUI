# NTSPIv3Builder
#
# @Purpose:
#   - This python script can be used to build NTSPI v3 packets
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
from math import cos, sin, sqrt, radians

# WGS84 constants for ECEF conversion
_A = 6378137.0  # semi-major axis meters
_F = 1.0 / 298.257223563
_E2 = _F * (2 - _F)

# Sequence counter for NTSPI packets (increment per packet)
_NTSPI_SEQUENCE = 0
_NTSPI_PACKET_SEQ = 0  # packet sequence count in package header

_SENSOR_LATITUDE = 32.0
_SENSOR_LONGITUDE = -106.0
_SENSOR_ALTITUDE = 2000 # meters
_UNIQUE_ID = "Example Unique"


# Public API: allow callers to set sensor geodetic location and unique id
def set_sensor_location(latitude: float, longitude: float, altitude_m: float) -> None:
    """
    Set the sensor geodetic location used when building NTSPI v3 packets.

    Parameters
    ----------
    latitude : float
        Latitude in decimal degrees (-90..90).
    longitude : float
        Longitude in decimal degrees (-180..180).
    altitude_m : float
        Altitude in meters above WGS84 ellipsoid.

    Notes
    -----
    The builder converts this geodetic location to ECEF for the Sensor location
    fields (offsets 368/376/384) when building packets.
    """
    global _SENSOR_LATITUDE, _SENSOR_LONGITUDE, _SENSOR_ALTITUDE
    # Basic validation
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError("latitude must be between -90 and 90 degrees")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError("longitude must be between -180 and 180 degrees")
    _SENSOR_LATITUDE = float(latitude)
    _SENSOR_LONGITUDE = float(longitude)
    _SENSOR_ALTITUDE = float(altitude_m)


def get_sensor_location() -> tuple[float, float, float]:
    """
    Return the currently configured sensor geodetic location as (lat, lon, alt_m).
    """
    return (_SENSOR_LATITUDE, _SENSOR_LONGITUDE, _SENSOR_ALTITUDE)


def set_ntspiv3_unique_id(unique_id: str) -> None:
    """
    Set the Unique ID string used in the NTSPI payload (16-byte field).

    The ICD defines Unique ID as a string up to 15 characters (stored in 16 bytes).
    This function will truncate to 15 ASCII characters and ignore non-ASCII.
    """
    global _UNIQUE_ID
    if unique_id is None:
        raise ValueError("unique_id must be a non-empty string")
    # Ensure ASCII and max 15 characters (ICD: up to 15 chars, stored in 16 bytes)
    u = str(unique_id).encode("ascii", errors="ignore")[:15].decode("ascii", errors="ignore")
    if len(u) == 0:
        raise ValueError("unique_id must contain at least one ASCII character")
    _UNIQUE_ID = u


def get_ntspiv3_unique_id() -> str:
    """
    Return the currently configured Unique ID string.
    """
    return _UNIQUE_ID


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float):
    """
    Convert geodetic (lat, lon in degrees, altitude in meters) to ECEF (meters).
    Returns (x, y, z) in meters.
    """
    lat = radians(lat_deg)
    lon = radians(lon_deg)
    sin_lat = sin(lat)
    cos_lat = cos(lat)
    N = _A / sqrt(1.0 - _E2 * sin_lat * sin_lat)
    x = (N + alt_m) * cos_lat * cos(lon)
    y = (N + alt_m) * cos_lat * sin(lon)
    z = (N * (1 - _E2) + alt_m) * sin_lat
    return x, y, z


def _next_ntspi_sequence():
    global _NTSPI_SEQUENCE
    _NTSPI_SEQUENCE = (_NTSPI_SEQUENCE + 1) & 0xFFFFFFFF
    return _NTSPI_SEQUENCE


def _next_packet_seq():
    global _NTSPI_PACKET_SEQ
    _NTSPI_PACKET_SEQ = (_NTSPI_PACKET_SEQ + 1) & 0xFFFFFFFF
    return _NTSPI_PACKET_SEQ


def set_ntspiv3_uniqueId(unique_id: str):
    _UNIQUE_ID = unique_id


# ---------------------------
# NTSPI v3 builder (504 bytes)
# ---------------------------
def build_ntspi_v3_packet(track_ecef: tuple[float, float, float] | None = None) -> bytes:
    """
    Build a 504-byte NTSPI v3 packet per the ICD.
    Many fields are filled with defaults or derived values:
      - iNET header (MessageDefinitionID=1003)
      - Package header (PackageDefinitionID=1003)
      - Sync "NTSP", Version 0x0003
      - Unique ID, Site ID, Other ID, Mission ID, Group ID, Case ID (padded strings)
      - Packet Sequence Count increments
      - Packet Time = current UTC (year, month, day, seconds since midnight, nanoseconds)
      - Target Position (ECEF) filled from the latest received track if available
      - Target Velocity/Acc/orientation zeros
      - Sensor location filled from the latest received track if available
      - Sensor Azimuth/Elevation zeros
      - Some flags set: Target Fields In Use set to include position and velocity (0x03)
    The final packet length is 504 bytes.
    """
    total_len = 504
    pkt = bytearray(total_len)

    # -----------------------
    # iNET Packet Header (offset 0, 24 bytes)
    # Fields: MessageVersion(4), OptionWordCount(4), Reserved(8), MessageFlags(16),
    # MessageDefinitionID(32)=1003, MessageDefinition SequenceNumber(32), MessageLength(32),
    # Acquisition Timestamp (64) -> seconds (uint32) + nanoseconds (uint32)
    # -----------------------
    # First 4 bytes: [MessageVersion(4)|OptionWordCount(4)] [Reserved(8)] [MessageFlags(16)]
    message_version = 0x1
    option_word_count = 0x0
    reserved_byte = 0x00
    message_flags = 0x0000
    first_byte = ((message_version & 0xF) << 4) | (option_word_count & 0xF)
    pkt[0] = first_byte
    pkt[1] = reserved_byte
    pkt[2:4] = struct.pack("!H", message_flags)

    # MessageDefinitionID = 1003
    struct.pack_into("!I", pkt, 4, 1003)
    # Sequence number for message definition
    seq = _next_ntspi_sequence()
    struct.pack_into("!I", pkt, 8, seq)
    # MessageLength = total_len
    struct.pack_into("!I", pkt, 12, total_len)
    # Acquisition timestamp: seconds + nanoseconds (use PTP-like epoch approximated by unix time)
    # now = datetime.utcnow()
    now = datetime.now(timezone.utc)
    seconds = int(now.timestamp())
    nanos = int((now.timestamp() - seconds) * 1e9)
    struct.pack_into("!I", pkt, 16, seconds)
    struct.pack_into("!I", pkt, 20, nanos)

    # -----------------------
    # iNET Package Header (offset 24, 12 bytes)
    # PackageDefinitionID (4) = 1003
    # PackageLength (2) = total_len - 24
    # StatusFlags (2) = 0
    # Acquisition TimeDelta (4) = 0
    # -----------------------
    package_length = total_len - 24  # includes package header and payload
    struct.pack_into("!I", pkt, 24, 1003)
    struct.pack_into("!H", pkt, 28, package_length)
    struct.pack_into("!H", pkt, 30, 0)
    struct.pack_into("!I", pkt, 32, 0)

    # -----------------------
    # NTSPI Package Payload starts at offset 36
    # Sync Constant "NTSP" (4)
    # Package Format Version (4) = 0x0003
    # Unique ID (16), Site ID (16), Other ID (16), Mission ID (16), Group ID (16), Case ID (16)
    # Packet Sequence Count (4)
    # Packet Time (12): year(uint16), month(uint8), day(uint8), seconds(uint32), nanoseconds(uint32)
    # Event types (4), Event times (4*12), Target Data Category (1), Target Fields In Use (1), Event Generation (4), Reserved (2)
    # Then Target Position/Velocity/Acc/orientation etc at offsets described in ICD.
    # -----------------------
    offset = 36
    pkt[offset:offset+4] = b"NTSP"; offset += 4
    struct.pack_into("!I", pkt, offset, 0x0003); offset += 4

    def _put_str16(s: str, dest_offset: int):
        b = s.encode("ascii", errors="ignore")[:15]
        b = b.ljust(16, b"\x00")
        pkt[dest_offset:dest_offset+16] = b

    # Unique ID, Site ID, Other ID, Mission ID, Group ID, Case ID
    _put_str16(_UNIQUE_ID, offset); offset += 16
    _put_str16("SITE_1", offset); offset += 16
    _put_str16("", offset); offset += 16
    _put_str16("", offset); offset += 16
    _put_str16("", offset); offset += 16
    _put_str16("", offset); offset += 16

    # Packet Sequence Count
    packet_seq = _next_packet_seq()
    struct.pack_into("!I", pkt, offset, packet_seq); offset += 4

    # Packet Time: year(uint16), month(uint8), day(uint8), seconds(uint32), nanoseconds(uint32)
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month
    day = now.day
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    nanos = int(now.microsecond * 1000)
    struct.pack_into("!H B B I I", pkt, offset, year, month, day, seconds_since_midnight, nanos)
    offset += 12

    # Event types (4 bytes) and Event times (4 * 12 bytes) -> leave zeros
    offset += 4  # Event 0-3 types (1 byte each)
    offset += 12 * 4  # Event times (4 * 12 bytes)

    # Target Data Category (1), Target Fields In Use (1)
    # Set Target Fields In Use to include Position and Velocity (bits 0 and 1 -> 0x03)
    struct.pack_into("!B", pkt, offset, 0)  # Target Data Category (0 = Live)
    offset += 1
    struct.pack_into("!B", pkt, offset, 0x03)  # Target Fields In Use: position + velocity present
    offset += 1

    # Event Generation (4), Reserved (2)
    offset += 4  # Event Generation
    offset += 2  # Reserved

    # At this point offset should be 216 (per ICD)
    # Fill Target Position X/Y/Z doubles at offsets 216,224,232
    # Use latest received track location if available
    if track_ecef is not None:
        tx, ty, tz = track_ecef
    else:
        lat = float(_SENSOR_LATITUDE)
        lon = float(_SENSOR_LONGITUDE)
        alt = float(_SENSOR_ALTITUDE)
        tx, ty, tz = geodetic_to_ecef(lat, lon, alt)

    struct.pack_into("!d", pkt, 216, float(tx))
    struct.pack_into("!d", pkt, 224, float(ty))
    struct.pack_into("!d", pkt, 232, float(tz))

    # Target Velocity X/Y/Z doubles at 240,248,256 -> zeros (not provided)
    struct.pack_into("!d", pkt, 240, 0.0)
    struct.pack_into("!d", pkt, 248, 0.0)
    struct.pack_into("!d", pkt, 256, 0.0)

    # Target Acc X/Y/Z doubles at 264,272,280 -> zeros
    struct.pack_into("!d", pkt, 264, 0.0)
    struct.pack_into("!d", pkt, 272, 0.0)
    struct.pack_into("!d", pkt, 280, 0.0)

    # Orientation psi/theta/phi at 288,296,304 -> zeros
    struct.pack_into("!d", pkt, 288, 0.0)
    struct.pack_into("!d", pkt, 296, 0.0)
    struct.pack_into("!d", pkt, 304, 0.0)

    # Angular velocity X/Y/Z at 312,320,328 -> zeros
    struct.pack_into("!d", pkt, 312, 0.0)
    struct.pack_into("!d", pkt, 320, 0.0)
    struct.pack_into("!d", pkt, 328, 0.0)

    # Angular acceleration X/Y/Z at 336,344,352 -> zeros
    struct.pack_into("!d", pkt, 336, 0.0)
    struct.pack_into("!d", pkt, 344, 0.0)
    struct.pack_into("!d", pkt, 352, 0.0)

    # Sensor Fields In Use (offset 360, 1 byte) -> set location present (bit0)
    struct.pack_into("!B", pkt, 360, 0x01)
    # Reserved 7 bytes at 361..367 left zero
    # Sensor location ECEF doubles at 368,376,384 -> use same sensor location as the current target track
    struct.pack_into("!d", pkt, 368, float(tx))
    struct.pack_into("!d", pkt, 376, float(ty))
    struct.pack_into("!d", pkt, 384, float(tz))

    # Sensor Azimuth (double) at 392, Sensor Elevation at 400, Sensor-to-Target Range at 408, Sensor Roll at 416
    struct.pack_into("!d", pkt, 392, 0.0)  # sensor azimuth
    struct.pack_into("!d", pkt, 400, 0.0)  # sensor elevation
    struct.pack_into("!d", pkt, 408, 0.0)  # sensor-to-target range
    struct.pack_into("!d", pkt, 416, 0.0)  # sensor roll

    # Test Data 0..7 (offsets 424..452) -> zeros (4 bytes each)
    # Data (offset 456) and Local Recorder On (457)
    struct.pack_into("!B", pkt, 456, 1)  # Data = 1 (Acquiring Data)
    struct.pack_into("!B", pkt, 457, 0)  # Local Recorder On = 0

    # Track Mode (458), Sense Mode (459), Gating Mode (460), Manual Event Data (461), Bomb Tone (462), Moving Target (463)
    struct.pack_into("!B", pkt, 458, 2)  # Track Mode = 2 (Tracking) default
    struct.pack_into("!B", pkt, 459, 0)  # Sense Mode = 0 (Skin)
    struct.pack_into("!B", pkt, 460, 0)  # Gating Mode
    struct.pack_into("!B", pkt, 461, 0)  # Manual Event Data
    struct.pack_into("!B", pkt, 462, 0)  # Bomb Tone
    struct.pack_into("!B", pkt, 463, 0)  # Moving Target

    # Pulse Width (offset 464, uint32) -> 0
    struct.pack_into("!I", pkt, 464, 0)

    # Error flags at 468..471 -> zeros
    struct.pack_into("!B", pkt, 468, 0)
    struct.pack_into("!B", pkt, 469, 0)
    struct.pack_into("!B", pkt, 470, 0)
    struct.pack_into("!B", pkt, 471, 0)

    # Azimuth Error (double) at 472, Elevation Error at 480, Range Error at 488 (double), AGC at 496 (double)
    struct.pack_into("!d", pkt, 472, 0.0)
    struct.pack_into("!d", pkt, 480, 0.0)
    struct.pack_into("!d", pkt, 488, 0.0)
    struct.pack_into("!d", pkt, 496, 0.0)

    # Done. Ensure length
    assert len(pkt) == total_len
    return bytes(pkt)