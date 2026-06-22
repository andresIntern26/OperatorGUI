import sys
import os
import threading 

# Ensure the parent directory is in the system path so Python can find the 'resources' package 
# even if executed from different working directories.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtCore import Qt  # <--- FIXED: Correct Core Namespace Import
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, 
                             QMdiArea, QMdiSubWindow, QLabel)

# --- MODULAR COMPONENT IMPORT ---
# Imports your isolated 3D view module directly from the resources subfolder
from resources.render_3d import ThreeDSphereWidget


# ==========================================
#  WIDGET COMPONENTS
# ==========================================

class VideoFeedWidget(QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # OpenCV/GStreamer player here
        self.label = QLabel(f"[VIDEO STAGE] {name}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: #111; color: #0fa; font-family: monospace;")
        
        layout.addWidget(self.label)

class DataReadoutWidget(QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.label = QLabel(f"{name}\n0.00")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: #221111; font-weight: bold; color: #ff5555; border: 1px solid #ff3333;")
        
        layout.addWidget(self.label)

#==========================================
#THREADING ...
#===========================================

def thread_windows(): 
    

#threading.Thread()


# ==========================================
#  FACTORY / CONFIGURATION LAYER
# ==========================================

class SubWindowFactory:
    """Handles the unique configurations and logic for creating each sub-window type."""
    
    @staticmethod
    def create(name: str) -> QMdiSubWindow:
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle(name)

        # Map windows to their correct internal functional widget type
        if name in ["Status Info", "HPA Display"]:
            sub_window.setWidget(DataReadoutWidget(name))
        elif name == "3D Model":
            # Pass our decoupled modular 3D engine class directly into this target panel
            sub_window.setWidget(ThreeDSphereWidget())
        else:
            sub_window.setWidget(VideoFeedWidget(name))
            
        return sub_window

# ==========================================
#  MAIN APP CONTROL 
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Window Command Dashboard")
        self.setGeometry(50, 50, 1300, 850) 

        # Master layout setups
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # MDI Workspace Setup
        self.mdi_area = QMdiArea()
        self.mdi_area.setStyleSheet("background-color: #1a1a1a;") 
        self.main_layout.addWidget(self.mdi_area)

        # Navigation Bar Layout
        self.button_layout = QHBoxLayout()
        self.window_references = {} 

        # Define window names and layout dictionary profile
        # Structure: "Window Name": (X_pos, Y_pos, Width, Height)
        self.layout_profile = {
            "Live Map":     (10, 10, 310, 360),     # Top Left
            "3D Model":     (10, 380, 310, 360),    # Under Live Map on the Left
            
            "Status Info":  (330, 10, 620, 110),    # Top Center 
            "Main Video":   (330, 130, 620, 460),   # Front and Center
            "HPA Display":  (330, 600, 620, 140),   # Bottom of everything
            
            "WFOV Video":   (960, 10, 300, 230),    # Top Right
            "UWFOV Video":  (960, 250, 300, 230),   # Middle Right
            "Color Video":  (960, 490, 300, 230)    # Bottom Right
        }

        self.build_dashboard(list(self.layout_profile.keys()))

    def build_dashboard(self, window_names):
        """Assembles dashboard and positions windows using the layout profile."""
        for name in window_names:
            # Create Navigation Button
            btn = QPushButton(name)
            btn.clicked.connect(self.handle_button_click)
            self.button_layout.addWidget(btn)

            # Generate structured Sub-Window via Factory
            sub_window = SubWindowFactory.create(name)

            # Register to MDI ecosystem
            self.mdi_area.addSubWindow(sub_window)
            self.window_references[name] = sub_window
            
            # --- APPLY SHAPE AND LOCATION ---
            if name in self.layout_profile:
                x, y, w, h = self.layout_profile[name]
                sub_window.setGeometry(x, y, w, h)
            
            sub_window.show()
            
            # Forces the child widgets to instantly refresh their rendering pipeline
            if sub_window.widget():
                sub_window.widget().update()

        # Mount bottom navbar layout
        self.main_layout.addLayout(self.button_layout)
        
        
    def handle_button_click(self):
        clicked_button = self.sender()
        if not clicked_button:
            return
            
        target_window = self.window_references.get(clicked_button.text())
        if target_window:
            # If minimized or hidden, restore it to its configured geometry
            if target_window.isMinimized() or not target_window.isVisible():
                target_window.showNormal()
            
            target_window.setFocus()
            self.mdi_area.setActiveSubWindow(target_window)


if __name__ == "__main__":
    # Compatibility configuration flags forcing the graphics drivers to grant legacy support
    from PyQt6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

    #TODO: 
    #get video input / stream set up - DONE 
    #Find out what type of data as input - DONE
    #Fix GUI layout - DONE 
    #Set up for video modules to handle h.264/UTP video input - DONE 

    #Set up git or github - DO LATER 

    #Imp. multithreading - later after data gotten