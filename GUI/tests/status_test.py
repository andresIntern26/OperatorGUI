import socket
import struct
import time

# --- MATCH TARGET CONFIGURATION ---
TARGET_IP = "127.0.0.1"  # Localhost
TIS_STATUS_PORT = 6063
MSG_EOM_MARKER = 0x5A5A
MSG_ID_TIS_PAS_STATUS = 1707

# --- STRUCT FORMATS (Matching TIS_NetIo.h) ---
HEADER_FORMAT = "<hhhhi"                  # sLength (12 bytes)
STATUS_DATA_FORMAT = "IIIIIIIIIII320s16s" # TIS_StatusData (368 bytes) -> 13 items total
GIMBAL_FORMAT = "iiiiiiiiiiii"            # TIS_GimbalCenteredData (48 bytes)

# Base format string up to the ending components
BASE_FORMAT = HEADER_FORMAT + STATUS_DATA_FORMAT + GIMBAL_FORMAT

def run_simulator():
    # Set up UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Calculate exact lengths
    base_size = struct.calcsize(BASE_FORMAT)
    # Total packet includes the trailing footer structure: short sId, short sEom (4 bytes)
    total_packet_length = base_size + 4 

    print(f"Starting TIS Mock Transmitter...")
    print(f"Targeting: {TARGET_IP}:{TIS_STATUS_PORT} | Struct Size: {total_packet_length} bytes")

    # Mock variables we can increment over time
    packet_num = 0
    gimbal_x = 120
    gimbal_y = -45
    error_count = 0

    try:
        while True:
            packet_num += 1
            gimbal_x += 2   # Simulate target drifting
            gimbal_y += 1
            
            # Switch states occasionally for visual confirmation
            sys_state = 1 if (packet_num % 10 < 7) else 2  # Alternate between TRACKING and COOLDOWN
            input_type = 2  # WEIBEL RADAR
            target_id_str = f"TGT-{1000 + packet_num // 5}".encode('ascii')

            # 1. Pack Header (MESG_HEADER) -> 5 items
            # sLength, sId, sVersion, sSpare, iCount
            header_bytes = struct.pack(HEADER_FORMAT, total_packet_length, MSG_ID_TIS_PAS_STATUS, 1, 0, packet_num)

            # 2. Pack Status Data (TIS_StatusData) -> 13 items
            unique_ntspi_ids = b"\x00" * 320 # Clear structural array padding block
            ntspi_target_id = target_id_str.ljust(16, b"\x00") # Pad target string out to 16 bytes cleanly

            # --- TRACKING CODES ARGUMENT COUNT VERIFICATION ---
            # 11 Integers (I) + 1 String Buffer (320s) + 1 String Buffer (16s) = 13 Total Items
            status_bytes = struct.pack(
                STATUS_DATA_FORMAT,
                packet_num,       # 1: packetNum
                22,               # 2: day
                7,                # 3: hour
                30,               # 4: min
                0,                # 5: sec
                sys_state,        # 6: tisState
                input_type,       # 7: inputType
                1,                # 8: selectedTarget (e.g. tracking index 1)
                packet_num,       # 9: packetCount
                packet_num,       # 10: dummy value or extra track parameter to hit index 11
                error_count,      # 11: errorCount
                unique_ntspi_ids, # 12: uniqueNTSPIids (320s)
                ntspi_target_id   # 13: ntspiTargetID (16s)
            )

            # 3. Pack Gimbal Positions (TIS_GimbalCenteredData) -> 12 items
            # 12 items: gimbalX, gimbalY, gimbalZ, gimbalVx...
            gimbal_bytes = struct.pack(
                GIMBAL_FORMAT,
                gimbal_x, gimbal_y, 500,  # X, Y, Z
                10, 5, 0,                 # Velocities
                0, 0, 0, 0, 0, 0          # Target 2 padding placeholders
            )

            # 4. Pack Footer (MESG_FOOTER) -> 2 items
            # short sId, short sEom
            footer_bytes = struct.pack("<HH", MSG_ID_TIS_PAS_STATUS, MSG_EOM_MARKER)

            # Assemble byte segments into raw UDP frame payload
            full_packet = header_bytes + status_bytes + gimbal_bytes + footer_bytes

            # Transmit onto network buffer pipeline
            sock.sendto(full_packet, (TARGET_IP, TIS_STATUS_PORT))
            
            print(f"[{packet_num}] Transmitted Frame -> ID: {target_id_str.decode()}, State: {sys_state}, Pos: ({gimbal_x},{gimbal_y})")
            time.sleep(0.5) # Send updates twice every second (2 Hz)

    except KeyboardInterrupt:
        print("\nTransmitter halted cleanly.")
    finally:
        sock.close()

if __name__ == "__main__":
    run_simulator()