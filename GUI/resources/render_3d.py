import sys
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QSurfaceFormat

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("Please install PyOpenGL inside your virtual environment: pip install PyOpenGL")

class ThreeDSphereWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_rot = 22 
        self.y_rot = 0
        self.pulse = 0.0
        
        # Smooth render tick loop (~60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(16)

    def initializeGL(self):
        """Pre-configures realistic hardware GPU lighting profiles."""
        glClearColor(0.04, 0.04, 0.06, 1.0)   # Midnight velvet dark background
        glEnable(GL_DEPTH_TEST)               # Hardware depth testing
        
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)                   # Ambient terrestrial wrap light
        glEnable(GL_COLOR_MATERIAL) 
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Primary Moonlit/Star-source Directional Array
        glLightfv(GL_LIGHT0, GL_POSITION, [12.0, 18.0, 8.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.95, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.12, 0.12, 0.18, 1.0])

        # Soft Earth-Glow / Ambient Fill
        glLightfv(GL_LIGHT1, GL_POSITION, [-12.0, -4.0, -12.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.08, 0.08, 0.12, 1.0])

    def resizeGL(self, w, h):
        if h == 0: h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(38.0, float(w) / float(h), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """Primary graphics pass engine rendering the observatory layout."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
     
        # Global Scene Placement Camera Layout Offset
        glTranslatef(0.0, -1.1, -7.8)
        glRotatef(self.x_rot, 1.0, 0.0, 0.0)
        
        self.draw_ground_grid(size=9.0, subdivisions=18)
        
        # Concrete Base Foundation Pad
        glColor3f(0.28, 0.3, 0.32)
        self.draw_cylinder(radius=1.9, length=0.08, segments=48)

        # Outer Enclosure Base Wall
        glPushMatrix()
        glTranslatef(0.0, 0.08, 0.0)
        glColor3f(0.55, 0.57, 0.6) 
        self.draw_cylinder(radius=1.55, length=0.85, segments=48)
        
        # Outer Access/Hatch Entry Bay Door (Static face pointing forward)
        glTranslatef(0.0, 0.15, 1.53)
        glColor3f(0.2, 0.23, 0.26)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-0.22, 0.0, 0.0)
        glVertex3f(0.22, 0.0, 0.0)
        glVertex3f(0.22, 0.55, 0.0)
        glVertex3f(-0.22, 0.55, 0.0)
        glEnd()
        glPopMatrix()

        # --- ROTATING PLATFORM MATRIX BOUNDS ---
        glPushMatrix()
        glRotatef(self.y_rot, 0.0, 1.0, 0.0) 

        # 1. Separated Vibration-Isolated Central Mount Pier
        glPushMatrix()
        glTranslatef(0.0, 0.08, 0.0)
        glColor3f(0.35, 0.37, 0.4) 
        self.draw_cylinder(radius=0.4, length=1.2, segments=24) 
        glPopMatrix()

        # 2. Dome Assembly (With Shiny Metallic Reflective Rules)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 0.95, 1.0])
        glMateriali(GL_FRONT, GL_SHININESS, 96) 
        
        glPushMatrix()
        glTranslatef(0.0, 0.93, 0.0) 
        glColor3f(0.88, 0.9, 0.93)   
        self.draw_observatory_dome(radius=1.5, segments=40)
        glPopMatrix()

        # Reset shiny materials for inner mechanisms
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
        glMateriali(GL_FRONT, GL_SHININESS, 16)

        # 3. Composite Optical Telescope
        glPushMatrix()
        glTranslatef(0.0, 1.28, 0.0)             
        glRotatef(16, 4.0, 1.0, -4.0) 
        glRotatef(-35, 0.0, 0.0, 2.0) # Angled forward into the opening path 


        # Structural Mount Head Fork Bracket
        glColor3f(0.18, 0.2, 0.24)
        self.draw_cylinder(radius=0.32, length=0.2, segments=24)
        
        # Primary Instrument Optical Backplane Cell Casing
        glTranslatef(0.0, 0.2, 0.0)
        glColor3f(0.1, 0.12, 0.15) 
        self.draw_cylinder(radius=0.48, length=0.35, segments=32)
        
        # Open Structural Optical Carbon Fiber Truss Spiders
        glTranslatef(0.0, 0.35, 0.0)
        glColor3f(0.22, 0.22, 0.22)
        self.draw_truss_framework(radius=0.45, length=0.85, segments=8)
        
        # Secondary Deflector Deflection Top Mirror Unit
        glTranslatef(0.0, 0.85, 0.0)
        glColor3f(0.78, 0.8, 0.83)
        self.draw_cylinder(radius=0.48, length=0.18, segments=32)
        
        # Central Core Secondary Optical Housing Mirror
        glTranslatef(0.0, -0.06, 0.0)
        glColor3f(0.08, 0.08, 0.08)
        self.draw_cylinder(radius=0.16, length=0.1, segments=16)
        
        # High-Speed Data Output Unit (Rear Focus Plane Assembly)
        glTranslatef(0.0, -1.34, 0.0)
        glColor3f(0.15, 0.35, 0.55) 
        self.draw_cylinder(radius=0.22, length=0.25, segments=24)
        
        # Telemetry Sync Visual Port Beacon
        glDisable(GL_LIGHTING)
        if math.sin(self.pulse * 4.5) > 0:
            glColor3f(0.0, 1.0, 0.7) 
        else:
            glColor3f(0.0, 0.35, 0.25)
        glPointSize(6.5)
        glBegin(GL_POINTS)
        glVertex3f(0.0, -0.02, 0.23)
        glEnd()
        glEnable(GL_LIGHTING)
        
        glPopMatrix() # End telescope matrix pop
        glPopMatrix() # End global synchronization rotation stack pop

    def draw_observatory_dome(self, radius, segments):
        """Generates a hemispherical dome with a precise shutter window cut-out facing 0 degrees."""
        half_segments = segments // 2
        shutter_gap_angle = (2.0 * math.pi) * (2.0 / segments) 

        for i in range(half_segments, segments):
            lat0 = math.pi * (-0.5 + float(i) / segments)
            z0 = math.sin(lat0) * radius
            r0 = math.cos(lat0) * radius

            lat1 = math.pi * (-0.5 + float(i + 1) / segments)
            z1 = math.sin(lat1) * radius
            r1 = math.cos(lat1) * radius

            glBegin(GL_QUAD_STRIP)
            for j in range(segments + 1):
                lng = 2.0 * math.pi * float(j) / segments
                
                if (lng < shutter_gap_angle or lng > (2.0 * math.pi - shutter_gap_angle)) and i > (half_segments + 1):
                    glEnd()
                    glBegin(GL_QUAD_STRIP)
                    continue

                x = math.cos(lng)
                y = math.sin(lng)

                glNormal3f(x * math.cos(lat0), math.sin(lat0), y * math.cos(lat0))
                glVertex3f(x * r0, z0, y * r0)

                glNormal3f(x * math.cos(lat1), math.sin(lat1), y * math.cos(lat1))
                glVertex3f(x * r1, z1, y * r1)
            glEnd()

    def draw_cylinder(self, radius, length, segments):
        """Generates a solid surface normal cylinder along the Y vertical plane."""
        glBegin(GL_QUAD_STRIP)
        for i in range(segments + 1):
            angle = 2.0 * math.pi * float(i) / segments
            x = math.cos(angle)
            z = math.sin(angle)

            glNormal3f(x, 0.0, z)
            glVertex3f(x * radius, 0.0, z * radius)
            glVertex3f(x * radius, length, z * radius)
        glEnd()

        # Bottom Cap
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(segments + 1):
            angle = 2.0 * math.pi * float(i) / segments
            glVertex3f(math.cos(angle) * radius, 0.0, math.sin(angle) * radius)
        glEnd()

        # Top Cap
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, length, 0.0) 
        for i in range(segments + 1):
            angle = 2.0 * math.pi * float(i) / segments
            glVertex3f(math.cos(angle) * radius, length, math.sin(angle) * radius)
        glEnd()

    def draw_truss_framework(self, radius, length, segments):
        """Draws open structural tubular skeleton rails typical of custom research telescopes."""
        glLineWidth(2.5)
        glBegin(GL_LINES)
        for i in range(segments):
            angle0 = 2.0 * math.pi * float(i) / segments
            angle1 = 2.0 * math.pi * float(i + 1) / segments
            
            x0, z0 = math.cos(angle0) * radius, math.sin(angle0) * radius
            x1, z1 = math.cos(angle1) * radius, math.sin(angle1) * radius

            glNormal3f(math.cos(angle0), 0.0, math.sin(angle0))
            glVertex3f(x0, 0.0, z0)
            glVertex3f(x0, length, z0)

            glVertex3f(x0, 0.0, z0)
            glVertex3f(x1, length, z1)
            glVertex3f(x1, 0.0, z1)
            glVertex3f(x0, length, z0)
        glEnd()
        glLineWidth(1.0)

    def draw_ground_grid(self, size, subdivisions):
        glDisable(GL_LIGHTING)
        glColor3f(0.12, 0.2, 0.3) 
        glBegin(GL_LINES)
        step = size / subdivisions
        half_size = size / 2.0
        for i in range(subdivisions + 1):
            pos = -half_size + (i * step)
            glVertex3f(pos, 0.0, -half_size)
            glVertex3f(pos, 0.0, half_size)
            glVertex3f(-half_size, 0.0, pos)
            glVertex3f(half_size, 0.0, pos)
        glEnd()
        glEnable(GL_LIGHTING)

    def update_scene(self):
        self.y_rot += 0.25   
        self.pulse += 0.016
        self.update()

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

# ==============================================================================
# RUNTIME LAUNCHER
# ==============================================================================
if __name__ == "__main__":
    
    fmt = QSurfaceFormat()
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    test_window = ThreeDSphereWidget()
    test_window.setWindowTitle("Astronomical Observatory Render Window")
    test_window.resize(700, 700)
    test_window.show()
    sys.exit(app.exec())
