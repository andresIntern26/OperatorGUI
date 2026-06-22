import socket
import time
import json
import math

# Target Address configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# WSMR Baseline Coordinates
CENTER_LAT = 32.5
CENTER_LON = -106.3

# Standard WGS84 Geodetic to ECEF Conversion
def geodetic_to_ecef(lat, lon, alt):
    rad_lat = math.radians(lat)
    rad_lon = math.radians(lon)
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = f * (2.0 - f)
    
    N = a / math.sqrt(1.0 - e2 * (math.sin(rad_lat) ** 2))
    
    x = (N + alt) * math.cos(rad_lat) * math.cos(rad_lon)
    y = (N + alt) * math.cos(rad_lat) * math.sin(rad_lon)
    z = (N * (1.0 - e2) + alt) * math.sin(rad_lat)
    return x, y, z

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[SIMULATOR]: Transmitting mock telemetry packets to {UDP_IP}:{UDP_PORT}...")
    print("Press Ctrl+C to terminate data stream.")
    
    frame_count = 0
    angle = 0.0

    try:
        while True:
            frame_count += 1
            angle += 0.02  # Controls movement speed
            
            # --- ASSET 1: Fast Flying Drone (Circular Orbit Pattern) ---
            drone_lat = CENTER_LAT + (0.15 * math.sin(angle))
            drone_lon = CENTER_LON + (0.15 * math.cos(angle))
            drone_alt = 5500.0 + (500.0 * math.sin(angle * 2)) # Altitude fluctuating
            
            x1, y1, z1 = geodetic_to_ecef(drone_lat, drone_lon, drone_alt)
            pkt1 = {
                "payload": {
                    "unique_id": "MQ9_DRONE_TARGET",
                    "site_id": 101,
                    "packet_sequence_count": frame_count,
                    "target": {"position": {"x": x1, "y": y1, "z": z1}}
                }
            }
            sock.sendto(json.dumps(pkt1).encode('utf-8'), (UDP_IP, UDP_PORT))

            # --- ASSET 2: Ground Tracking Vehicle (Linear Southern Patrol) ---
            truck_lat = CENTER_LAT - 0.2 + (0.005 * math.sin(angle * 0.5))
            truck_lon = CENTER_LON - 0.1 + (0.01 * math.cos(angle * 0.3))
            truck_alt = 1200.0 # Standard terrain altitude
            
            x2, y2, z2 = geodetic_to_ecef(truck_lat, truck_lon, truck_alt)
            pkt2 = {
                "payload": {
                    "unique_id": "WSMR_MOBILE_RADAR_04",
                    "site_id": 102,
                    "packet_sequence_count": frame_count,
                    "target": {"position": {"x": x2, "y": y2, "z": z2}}
                }
            }
            sock.sendto(json.dumps(pkt2).encode('utf-8'), (UDP_IP, UDP_PORT))

            # Stream at 10 Hz rate (10 frames per second)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[SIMULATOR]: Stream stopped cleanly.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()