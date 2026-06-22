# main.py
import sys
import os

# ==========================================
#  FORCE HARDWARE COHESION BEFORE QT LOADS
# ==========================================
# Strips Direct3D 11 compositing overrides and binds all widgets
# (including QWebEngineView and ThreeDSphereWidget) to a shared OpenGL context.
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_OPENGL"] = "desktop"

# ==========================================
#  FORCE-INJECT SYSTEM SEARCH PATHS
# ==========================================
current_file_dir = os.path.dirname(os.path.abspath(__file__))

if current_file_dir not in sys.path:
    sys.path.insert(0, current_file_dir)

dod_admin_fallback = r"C:\Users\DoD_Admin\Desktop\project\GUI"
if os.path.exists(dod_admin_fallback) and dod_admin_fallback not in sys.path:
    sys.path.insert(0, dod_admin_fallback)

ui_dir = os.path.join(current_file_dir, 'ui')
if os.path.exists(ui_dir) and ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)

parent_dir = os.path.abspath(os.path.join(current_file_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# ==========================================
#  CRITICAL PATH VALIDATION
# ==========================================
try:
    from resources.cameras import CameraDisplay
except ModuleNotFoundError as e:
    print("\n" + "="*60)
    print("CRITICAL PATH ERROR DETECTED")
    print(f"Python looked in these directories: {sys.path[:3]}")
    print(f"Is cameras.py inside: {current_file_dir} ?")
    print("="*60 + "\n")
    raise e

# Import windows.py safely from the "ui" sub-folder directory
from ui import windows

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMdiArea


# ==========================================
#  MAIN APP CONTROL
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Window Command Dashboard")
        self.setGeometry(30, 30, 1650, 920) 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) 

        self.mdi_area = QMdiArea()
        
        # Enables the parent frame to render frameless elements neatly
        self.mdi_area.setOption(QMdiArea.AreaOption.DontMaximizeSubWindowOnActivation, True)
        self.mdi_area.setStyleSheet(windows.MDI_AREA_STYLESHEET) 
        self.main_layout.addWidget(self.mdi_area)

        self.window_references = {} 
        self.build_dashboard(list(windows.LAYOUT_PROFILE.keys()))

    def build_dashboard(self, window_names):
        for name in window_names:
            self.create_and_place_subwindow(name)

    def create_and_place_subwindow(self, name):
        sub_window = windows.SubWindowFactory.create(name)
        sub_window.destroyed.connect(lambda: self.clear_window_reference(name))
        
        self.mdi_area.addSubWindow(sub_window)
        self.window_references[name] = sub_window
        
        if name in windows.LAYOUT_PROFILE:
            x, y, w, h = windows.LAYOUT_PROFILE[name]
            sub_window.setGeometry(x, y, w, h)
        
        sub_window.show()
        if sub_window.widget():
            sub_window.widget().update()
        return sub_window

    def clear_window_reference(self, name):
        if name in self.window_references:
            self.window_references[name] = None

    def closeEvent(self, event):
        print("[SHUTDOWN] Terminating tracking streams gracefully...")
        for window in self.mdi_area.subWindowList():
            if isinstance(window.widget(), CameraDisplay):
                window.widget().close()
            elif type(window.widget()).__name__ == 'CameraDisplay':
                window.widget().close()
        event.accept()

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    
    # Enforce native desktop engine composition bindings via application attributes
    app.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL, True)
    app.setStyleSheet(windows.APP_STYLESHEET)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())