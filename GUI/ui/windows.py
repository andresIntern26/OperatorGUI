# ui/windows.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMdiSubWindow
from resources.cameras import CameraDisplay

# ==========================================
#  FALLBACK COMPONENT WIDGETS (REDESIGNED)
# ==========================================
try:
    from resources.status import SystemStatusPanelWidget 
except ImportError:
    class SystemStatusPanelWidget(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            
            lbl = QLabel("[ SYSTEM STATUS PANEL CRITICAL FALLBACK ]")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #1a1518; 
                color: #ff5555; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                border: 1px solid #ff3333;
                border-radius: 4px;
            """)
            layout.addWidget(lbl)

try: 
    from resources.HPA_display import HPAdisplay
except ImportError: 
    class HPAdisplay(QWidget): 
        def __init__(self): 
            super().__init__()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            
            lbl = QLabel("[ HPA TELEMETRY ENGINE FALLBACK ]")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #121815; 
                color: #00ff66; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                border: 1px solid #00aa44;
                border-radius: 4px;
            """)
            layout.addWidget(lbl)

try:
    from resources.render_3d import ThreeDSphereWidget
except ImportError:
    class ThreeDSphereWidget(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            
            lbl = QLabel("[ 3D SPHERE MATRIX WIREFRAME ]")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #11141a; 
                color: #3399ff; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                border: 2px solid #2266bb;
                border-radius: 4px;
            """)
            layout.addWidget(lbl)

# --- NTSPI Map Tracker Fallback Layer ---
try:
    from resources.ntspi_map import LiveNTSPITracker
except ImportError:
    class LiveNTSPITracker(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            
            lbl = QLabel("[ NTSPI SATELLITE MAP ENGINE OFFLINE ]\nVerify: resources/ntspi_map.py")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #111618; 
                color: #00e5ff; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                border: 1px dashed #00b3cc;
                border-radius: 4px;
            """)
            layout.addWidget(lbl)


class VideoFeedWidget(QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(f"⌖ SIGNAL LOSS // FEED: {name.upper()}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            background-color: #0d0d0d; 
            color: #85929E; 
            font-family: 'Consolas', 'Courier New', monospace; 
            font-size: 11px;
            letter-spacing: 1px;
            border: none;
        """)
        layout.addWidget(self.label)


# ==========================================
#  FACTORY LAYER (STRICT DESIGN UNCHANGED)
# ==========================================
class SubWindowFactory:
    @staticmethod
    def create(name: str) -> QMdiSubWindow:
        sub_window = QMdiSubWindow()
        sub_window.setWindowFlags(Qt.WindowType.CustomizeWindowHint)
        sub_window.setWindowTitle(name)
        sub_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        if name == "Status Info":
            sub_window.setWidget(SystemStatusPanelWidget())
        elif name == "HPA Display":
            sub_window.setWidget(HPAdisplay())
        elif name == "3D Model":
            sub_window.setWidget(ThreeDSphereWidget())
        elif name == "Live Map":
            sub_window.setWidget(LiveNTSPITracker())
        elif name == "Main Video":
            rtsp_main = "rtsp://192.168.0.101/axis-media/media.3gp"
            sub_window.setWidget(CameraDisplay(rtsp_url=rtsp_main))
        elif name == "Ultra Wide FOV":
            rtsp_wide = "rtsp://192.168.0.101/axis-media/media.3gp"
            sub_window.setWidget(CameraDisplay(rtsp_url=rtsp_wide))
        elif name == "Color Video":
            rtsp_color = "rtsp://192.168.0.101/axis-media/media.3gp"
            sub_window.setWidget(CameraDisplay(rtsp_url=rtsp_color))
        else:
            sub_window.setWidget(VideoFeedWidget(name))
            
        return sub_window


# ==========================================
#  TACTICAL THEME STYLESHEET PROFILE CONFIGS
# ==========================================
APP_STYLESHEET = """
    QMainWindow { 
        background-color: #0a0b0d; 
    }
    QPushButton { 
        background-color: #1c1f24; 
        color: #d1d5db; 
        padding: 6px 12px; 
        border: 1px solid #2d3139; 
        border-radius: 4px; 
        font-family: "Segoe UI", sans-serif;
        font-size: 11px;
        font-weight: 600; 
    }
    QPushButton:hover { 
        background-color: #242930; 
        color: #ffffff;
        border: 1px solid #00f0ff; 
    }
    QPushButton:pressed {
        background-color: #0f1115;
    }
    QStatusBar { 
        color: #64748b; 
        background-color: #0f1115; 
        border-top: 1px solid #1e222b; 
        font-family: "Consolas", monospace;
        font-size: 11px;
    }
    
    CameraDisplay { 
        border: 2px solid #1c1f24; 
        background-color: #000000;
    }
    VideoFeedWidget { 
        border: 2px solid #1c1f24; 
        background-color: #000000;
    }
"""

MDI_AREA_STYLESHEET = """
    QMdiArea { 
        background-color: #070809; 
        border: none;
    }
    QMdiSubWindow { 
        border: 1px solid #20242c; 
        background-color: #101216; 
    }
    /* Modernizes the custom top window title bars */
    QMdiSubWindow > QWidget {
        background-color: #101216;
    }
    QMdiSubWindow::title {
        background-color: #161920;
        padding-left: 8px;
        padding-top: 4px;
        padding-bottom: 4px;
        color: #8f9cae;
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #20242c;
    }
    QMdiSubWindow::title:active {
        background-color: #1c212b;
        color: #00f0ff;
        border-bottom: 1px solid #2b3344;
    }
"""

# Hardcoded absolute coordinate metrics safely preserved for engine execution
LAYOUT_PROFILE = {
    "Live Map":           (10, 10, 320, 415),   
    "3D Model":           (10, 475, 320, 425),    
    "Status Info":        (340, 10, 965, 100),    
    "Main Video":         (340, 125, 965, 450),   
    "Ultra Wide FOV":     (1310, 10, 310, 330),    
    "Color Video":        (1310, 350, 310, 225),   
    "HPA Display":        (340, 650, 1280, 240), 
}