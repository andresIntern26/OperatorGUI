import sys
import socket
import struct
from PyQt6.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QGridLayout, QLabel, QVBoxLayout

# --- NETWORK CONFIGURATION ---
TIS_STATUS_PORT = 6063
MSG_EOM_MARKER = 0x5A5A

# Mappings sourced directly from TIS_NetIo.h
INPUT_TYPE_MAP = {
    1: "PAS RADAR",
    2: "WEIBEL RADAR",
    3: "MMR RADAR",
    4: "NTSPI RADAR",
    5: "MOTR PAS",
    6: "CTC RADAR",
    7: "DSSS RADAR",
    8: "NMEA GPS"
}

SYS_STATE_MAP = {
    0: "STANDBY",
    1: "TRACKING",
    2: "COOLDOWN",
    3: "TEST MODE"
}

# --- TIS BINARY STRUCT PACKING ALIGNMENT (FIXED) ---
# Combined continuous string with no literal spaces or duplicate endian tags
HEADER_FORMAT = "<hhhhi"                     # sLength, sId, sVersion, sSpare, iCount
STATUS_DATA_FORMAT = "IIIIIIIIIII320s16s"    # packetNum, day, hour, min, sec, tisState, inputType, selectedTarget, packetCount, errorCount, uniqueNTSPIids, ntspiTargetID
GIMBAL_FORMAT = "iiiiiiiiiiii"               # 12 pieces of 32-bit integer spatial coordinates

TIS_PARSE_STREAM_FORMAT = HEADER_FORMAT + STATUS_DATA_FORMAT + GIMBAL_FORMAT


class TISNetworkWorker(QThread):
    """Asynchronous background socket listener thread for incoming telemetry frames."""
    data_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind cleanly to catch broad network telemetry interface traffic
        sock.bind(("0.0.0.0", TIS_STATUS_PORT))
        
        expected_size = struct.calcsize(TIS_PARSE_STREAM_FORMAT)

        while self.running:
            try:
                # Buffer max capacity matches LARGE_MSG_SIZE (560)
                data, _ = sock.recvfrom(560)
                if len(data) >= expected_size:
                    # Unpack slice corresponding strictly to header, status, and gimbal regions
                    raw_slice = data[:expected_size]
                    unpacked = struct.unpack(TIS_PARSE_STREAM_FORMAT, raw_slice)
                    
                    # Extract target footprint data safely out of raw bytes arrays
                    ntspi_id_raw = unpacked[17] 
                    ntspi_target_id = ntspi_id_raw.split(b'\x00')[0].decode('ascii', errors='ignore').strip()
                    
                    # Validate EOM trailing word sequence at the very end of the packet payload length
                    eom_check = struct.unpack("<H", data[len(data)-2:])[0]
                    
                    # Package metrics payload for safe UI signal transmission
                    telemetry_payload = {
                        "msg_id": unpacked[1],
                        "sys_state": unpacked[10],   
                        "input_type": unpacked[11],   
                        "error_count": unpacked[15],  
                        "target_id": ntspi_target_id if ntspi_target_id else "UNLOCKED",
                        "gimbal_x": unpacked[18],     
                        "gimbal_y": unpacked[19],    
                        "is_valid_eom": (eom_check == MSG_EOM_MARKER)
                    }
                    
                    if telemetry_payload["is_valid_eom"]:
                        self.data_received.emit(telemetry_payload)
            except Exception as net_err:
                print(f"Network processing exception: {net_err}")

    def stop(self):
        self.running = False
        self.wait()

class SystemStatusPanelWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #15171c; border: none;")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(15)
        
        # Grid 1: Tracking Metrics
        grid1 = QGridLayout()
        grid1.setSpacing(6)
        
        self.til_lbl = QLabel("TARGET ID:")
        self.til_val = QLabel("UNLOCKED")
        self.til_val.setStyleSheet("color: #ff5555; font-weight: bold;")
        
        self.laser_lbl = QLabel("GIMBAL POS X/Y:")
        self.laser_val = QLabel("0 , 0")
        self.laser_val.setStyleSheet("color: #3df3ff; font-family: monospace; font-weight: bold;")
        
        self.mode_lbl = QLabel("SYS STATE:")
        self.mode_val = QLabel("0 (STANDBY)")
        self.mode_val.setStyleSheet("color: #ffaa00; font-weight: bold;")
        
        grid1.addWidget(self.til_lbl, 0, 0)
        grid1.addWidget(self.til_val, 0, 1)
        grid1.addWidget(self.laser_lbl, 1, 0)
        grid1.addWidget(self.laser_val, 1, 1)
        grid1.addWidget(self.mode_lbl, 2, 0)
        grid1.addWidget(self.mode_val, 2, 1)
        
        # Grid 2: Data Link Health & Stream Config
        grid2 = QGridLayout()
        grid2.setSpacing(6)
        
        self.c45_lbl = QLabel("INPUT SOURCE:")
        self.c45_val = QLabel("NONE")
        self.c45_val.setStyleSheet(
            "background-color: #1a1d24; color: #8a94a6; font-weight: bold; "
            "border: 1px solid #22252c; border-radius: 3px; padding: 2px 6px;"
        )
        self.c45_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.shot_lbl = QLabel("LINK ERRORS:")
        self.shot_val = QLabel("0")
        self.shot_val.setStyleSheet("color: #00ff00; font-family: monospace; font-weight: bold; font-size: 14px;")
        
        grid2.addWidget(self.c45_lbl, 0, 0)
        grid2.addWidget(self.c45_val, 0, 1)
        grid2.addWidget(self.shot_lbl, 1, 0)
        grid2.addWidget(self.shot_val, 1, 1)
        
        # Right VBox Block: Master UTC NTP Clock Viewport
        clock_layout = QVBoxLayout()
        clock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        utc_title = QLabel("TELEMETRY CLOCK (NTP/UTC)")
        utc_title.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        utc_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.utc_time_display = QLabel("00:00:00.000 UTC")
        self.utc_time_display.setStyleSheet(
            "color: #00ff00; font-family: monospace; font-size: 18px; "
            "font-weight: bold; background-color: #0a0b0d; padding: 6px; "
            "border: 1px solid #22252c; border-radius: 4px;"
        )
        self.utc_time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        clock_layout.addWidget(utc_title)
        clock_layout.addWidget(self.utc_time_display)
        
        # Global Layout Composition Assembly
        main_layout.addLayout(grid1, stretch=1)
        main_layout.addLayout(clock_layout, stretch=1)
        main_layout.addLayout(grid2, stretch=1)
        
        for lbl in [self.til_lbl, self.laser_lbl, self.mode_lbl, self.c45_lbl, self.shot_lbl]:
            lbl.setStyleSheet("color: #8a94a6; font-size: 11px; font-weight: bold;")

        # Time Engine Sync initialization
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.refresh_utc_clock)
        self.clock_timer.start(33) 
        self.refresh_utc_clock()

        # --- SPAWN NETWORK STREAM LISTENER ---
        self.net_thread = TISNetworkWorker()
        self.net_thread.data_received.connect(self.process_incoming_telemetry)
        self.net_thread.start()

    def refresh_utc_clock(self):
        current_utc = QDateTime.currentDateTimeUtc()
        self.utc_time_display.setText(current_utc.toString("hh:mm:ss.zzz t").upper())

    def process_incoming_telemetry(self, data: dict):
        """Thread-safe slot callback executing immediately on new network frame packet reception."""
        # Update Target Identifier
        t_id = data["target_id"]
        self.til_val.setText(t_id)
        if t_id == "UNLOCKED":
            self.til_val.setStyleSheet("color: #ff5555; font-weight: bold;")
        else:
            self.til_val.setStyleSheet("color: #55ff55; font-weight: bold;")

        # Update Gimbal positions
        self.laser_val.setText(f"{data['gimbal_x']} , {data['gimbal_y']}")

        # Map System State Enum values
        state_code = data["sys_state"]
        state_str = SYS_STATE_MAP.get(state_code, f"{state_code} (UNKNOWN)")
        self.mode_val.setText(f"{state_code} ({state_str})")

        # Map Network Source Inputs
        src_code = data["input_type"]
        self.c45_val.setText(INPUT_TYPE_MAP.get(src_code, "UNKNOWN"))

        # Render network health tracking status updates
        err_count = data["error_count"]
        self.shot_val.setText(str(err_count))
        if err_count > 0:
            self.shot_val.setStyleSheet("color: #ff3333; font-family: monospace; font-weight: bold; font-size: 14px;")
        else:
            self.shot_val.setStyleSheet("color: #00ff00; font-family: monospace; font-weight: bold; font-size: 14px;")

    def closeEvent(self, event):
        """Clean close intercept hook ensuring child threads exit cleanly before application death."""
        self.net_thread.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemStatusPanelWidget()
    window.resize(850, 140)
    window.setWindowTitle("HPA Display System Matrix Overlay")
    window.show()
    sys.exit(app.exec())