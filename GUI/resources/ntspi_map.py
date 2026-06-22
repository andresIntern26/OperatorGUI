import sys
import socket
import struct
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import pyqtSignal, QObject, QThread
from math import atan2, sqrt, degrees, radians, sin, cos

# =====================================================================
# IF USING EXTERNAL NTSPI DIRECTORY, UNCOMMENT THESE IMPORTS:
# from NTSPIv3Parser import parse_ntspi_v3_packet
# =====================================================================

# WGS84 Constants for ECEF to Geodetic conversion
_A = 6378137.0  
_F = 1.0 / 298.257223563
_B = _A * (1.0 - _F)  
_E2 = _F * (2.0 - _F)
_E_PRIME2 = (_A**2 - _B**2) / (_B**2)

def ecef_to_geodetic(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Convert ECEF (meters) to Geodetic Degrees (Lat, Lon, Alt) via Bowring's method."""
    p = sqrt(x**2 + y**2)
    if p < 1e-6:
        lon = 0.0
        lat = 90.0 if z > 0 else -90.0
        alt = abs(z) - _B
        return lat, lon, alt

    theta = atan2(z * _A, p * _B)
    lon = atan2(y, x)
    lat = atan2(z + _E_PRIME2 * _B * (sin(theta)**3), p - _E2 * _A * (cos(theta)**3))
    N = _A / sqrt(1.0 - _E2 * (sin(lat)**2))
    alt = (p / cos(lat)) - N
    return degrees(lat), degrees(lon), alt


class TelemetrySignals(QObject):
    """Signals data to the main UI window thread."""
    packet_parsed = pyqtSignal(str, float, float, float, int)


class NTSPINetworkWorker(QThread):
    """Background thread that captures live telemetry strings or binary arrays."""
    def __init__(self, ip="0.0.0.0", port=5005):
        super().__init__()
        self.ip = ip
        self.port = port
        self.running = True
        self.signals = TelemetrySignals()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576) # 1MB OS buffer sizing
        
        try:
            sock.bind((self.ip, self.port))
            print(f"[NTSPI LIVE TRACKER]: Listening for incoming telemetry on {self.ip}:{self.port}...")
        except Exception as e:
            print(f"[NETWORK ERROR]: Binding failure: {e}")
            self.running = False

        while self.running:
            try:
                # Accept data from network socket
                data, addr = sock.recvfrom(2048)
                
                # =====================================================================
                # SIMULATED / EXTERNAL PARSER BRIDGE
                # =====================================================================
                parsed = self.mock_internal_parser_fallback(data)
                if not parsed:
                    continue
                
                # Extract identifiers from structural payload mapping
                unique_id = parsed["payload"]["unique_id"]
                seq_count = parsed["payload"]["packet_sequence_count"]
                
                # Extract exact position metrics
                tx = parsed["payload"]["target"]["position"]["x"]
                ty = parsed["payload"]["target"]["position"]["y"]
                tz = parsed["payload"]["target"]["position"]["z"]
                
                # Convert standard range map spaces down into visual map units
                lat, lon, alt = ecef_to_geodetic(tx, ty, tz)
                
                # Dispatch safely across thread boundary
                self.signals.packet_parsed.emit(unique_id, lat, lon, alt, seq_count)
                
            except Exception as err:
                print(f"[NTSPI PARSE ERROR]: Packet processing fault: {err}")
                
        sock.close()

    def mock_internal_parser_fallback(self, data):
        """Emergency schema factory if handling arbitrary input payload formats."""
        try:
            # If your packet arrived via json or string telemetry builder configurations
            decoded_str = data.decode('utf-8', errors='ignore')
            if "payload" in decoded_str:
                return json.loads(decoded_str)
        except:
            pass
        return None

    def stop(self):
        self.running = False
        self.wait()


class LiveNTSPITracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NTSPI v3 Live Satellite Range Display")
        self.resize(1100, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Map Default Focus (WSMR Region baseline center initialization)
        self.start_lat = 32.5
        self.start_lng = -106.3

        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        layout.addWidget(self.browser)

        self.load_satellite_map_engine()

        # Connect background operations thread
        self.network_thread = NTSPINetworkWorker(ip="0.0.0.0", port=5005)
        self.network_thread.signals.packet_parsed.connect(self.update_map_marker)
        self.network_thread.start()

    def load_satellite_map_engine(self):
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body, html, #map {{ margin: 0; padding: 0; height: 100%; width: 100%; background: #0b0d0f; }}
                .leaflet-container {{ background: #0b0d0f !important; }}
                .custom-popup .leaflet-popup-content-wrapper {{
                    background: rgba(20, 25, 30, 0.9);
                    color: #ffffff;
                    font-family: 'Courier New', Courier, monospace;
                    border: 1px solid #00ffcc;
                    border-radius: 4px;
                }}
                .custom-popup .leaflet-popup-tip {{ background: rgba(20, 25, 30, 0.9); }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Initialize map instance
                var map = L.map('map', {{ zoomControl: true }}).setView([{self.start_lat}, {self.start_lng}], 9);
                
                // Load Esri World Imagery Satellite Tiles
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    attribution: ''
                }}).addTo(map);

                // Add standard tracking crosshairs asset icon reference
                var droneIcon = L.icon({{
                    iconUrl: 'https://commons.wikimedia.org/wiki/File:Black_airplane_3_icon.png',
                    iconSize: [36, 36],
                    iconAnchor: [18, 18]
                }});

                // Dynamic target dictionary tracking registry mapping object array 
                var activeTracks = {{}};

                function setTargetLocation(id, lat, lng, alt, seq) {{
                    var nextCoordinates = new L.LatLng(lat, lng);
                    
                    // Create object dynamically if it doesn't exist yet inside registry
                    if (!activeTracks[id]) {{
                        activeTracks[id] = L.marker(nextCoordinates, {{icon: droneIcon}}).addTo(map);
                        activeTracks[id].bindPopup("", {{className: 'custom-popup'}});
                    }}
                    
                    // Route spatial tracking position changes dynamically
                    activeTracks[id].setLatLng(nextCoordinates);
                    
                    // Update metadata configuration windows seamlessly on-the-fly
                    var uiMetadataCard = 
                        "<div style='font-size: 11px; line-height: 14px;'>" +
                        "<b style='color:#00ffcc;'>ID: " + id + "</b><br>" +
                        "<hr style='border:0.5px solid #334455; margin:4px 0;'>" +
                        "<b>LAT :</b> " + lat.toFixed(6) + "<br>" +
                        "<b>LON :</b> " + lng.toFixed(6) + "<br>" +
                        "<b>ALT :</b> " + alt.toFixed(1) + " m<br>" +
                        "<b>SEQ :</b> " + seq +
                        "</div>";
                        
                    activeTracks[id].setPopupContent(uiMetadataCard);
                }}
            </script>
        </body>
        </html>
        """
        self.browser.setHtml(map_html)

    def update_map_marker(self, unique_id, lat, lng, alt, seq_count):
        """Passes target parameters straight to the Leaflet Engine registry structure."""
        js_invocation = f"setTargetLocation('{unique_id}', {lat}, {lng}, {alt}, {seq_count});"
        self.browser.page().runJavaScript(js_invocation)

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()


if __name__ == "__main__": 
    app = QApplication(sys.argv)
    window = LiveNTSPITracker()
    window.show()
    sys.exit(app.exec())