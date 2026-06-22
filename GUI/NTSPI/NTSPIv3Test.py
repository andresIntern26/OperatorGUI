# NTSPIv3Test
#
# @Purpose:
#   - This python script can be used to test building and parsing an NTSPI v3 packet
#
# @Author: Matt Grimes
#          mgrimes@zygosconsulting.com
#
# @Date: 06/01/2026
#
# @ChangeLog:
# 06/01/2026 - Initial Version
#

# Example quick test
if __name__ == "__main__":
    # Build a packet using build_ntspi_v3_packet() and parse it:
    try:
        from NTSPIv3Builder import set_sensor_location, set_ntspiv3_unique_id, build_ntspi_v3_packet, geodetic_to_ecef  
    except Exception:
        build_ntspi_v3_packet = None

    try:
        from NTSPIv3Parser import parse_ntspi_v3_packet 
    except Exception:
        parse_ntspi_v3_packet = None

    if build_ntspi_v3_packet:
        # configure sensor and unique id
        set_sensor_location(33.12345, -106.54321, 2100.0)
        set_ntspiv3_unique_id("WSMR_RADAR_1")

        pkt = build_ntspi_v3_packet(geodetic_to_ecef(32.0, -106.0, 6000))
        
        parsed = parse_ntspi_v3_packet(pkt)
        # print a few fields to verify
        print("Unique ID:", parsed["payload"]["unique_id"])
        print("Site ID:", parsed["payload"]["site_id"])
        print("Packet seq:", parsed["payload"]["packet_sequence_count"])
        print("Target ECEF X:", parsed["payload"]["target"]["position"]["x"])
        print("Target ECEF Y:", parsed["payload"]["target"]["position"]["y"])
        print("Target ECEF Z:", parsed["payload"]["target"]["position"]["z"])

