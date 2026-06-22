import sys
import math
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QGridLayout
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QPainter, QColor, QFont

from OpenGL.GL import (glClearColor, glClear, glEnable, glDisable, glScissor,
                       glViewport, glMatrixMode, glLoadIdentity, glOrtho,
                       glBegin, glEnd, glVertex2f, glColor3f, glLineWidth,
                       GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, 
                       GL_DEPTH_TEST, GL_SCISSOR_TEST, GL_PROJECTION, 
                       GL_MODELVIEW, GL_LINES, GL_LINE_LOOP)  


# Azimuth / elevation boundaries
azmuthLimits = [-90, 90]
elevationLimits = [-90, 90]
total_width = 180
total_height = 150

# For horizon boundary calcs.
antenna_height_meters = 30


class HPAdisplayBackground: 
    def __init__(self, azmuth=0, elevation=0, cam_direction=0, target_V_angle=0, target_H_angle=0):
        self.azmuth = azmuth 
        self.elevation_val = elevation
        self.cam_direction = cam_direction 
        self.target_V_angle = target_V_angle
        self.target_H_angle = target_H_angle

    def azmuth_calc(self, cam_direction, azmuth):
        reference_point = 0 
        self.azmuth = reference_point - cam_direction

    def update_elevation(self): 
        pass

    def target_angle(self): 
        pass

    def conv_3D(self, b_height, b_width, target_azimuth, target_elevation):
        Xpixel = ((target_azimuth - azmuthLimits[0]) / (azmuthLimits[1] - azmuthLimits[0])) * b_width
        Ypixel = b_height - (((target_elevation - elevationLimits[0]) / (elevationLimits[1] - elevationLimits[0])) * b_height)
        return Xpixel, Ypixel


def calculate_horizon_elevation(antenna_height_meters, target_range_meters):
    R_earth = 6371000  
    R_effective = (4 / 3) * R_earth  

    d_horizon = math.sqrt(2 * R_effective * antenna_height_meters)
    
    if target_range_meters <= d_horizon:
        min_elevation = 0.0
    else:
        dip_angle_rad = (target_range_meters - d_horizon) / R_effective
        min_elevation = -math.degrees(dip_angle_rad)
        
    return min_elevation


class HPAdisplay(QOpenGLWidget): 
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        # DEFINE MARGINS (in pixels) around your grid box
        self.left_margin = 70
        self.right_margin = 40
        self.top_margin = 40
        self.bottom_margin = 60

    def initializeGL(self): 
        # Default fallback global clear color
        glClearColor(0.0, 0.0, 0.0, 1.0) 
        glEnable(GL_DEPTH_TEST) 
        
    def resizeGL(self, b_width, b_height):
        # Enforce minimum dimension boundaries
        inner_width = max(1, b_width - self.left_margin - self.right_margin)
        inner_height = max(1, b_height - self.top_margin - self.bottom_margin)

        # Shift the OpenGL Viewport context physically inside the margin box
        glViewport(self.left_margin, self.bottom_margin, inner_width, inner_height)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(azmuthLimits[0], azmuthLimits[1], elevationLimits[0], elevationLimits[1], -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self): 
        glClearColor(0.0, 0.0, 0.0, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
 
        width = self.width()
        height = self.height()
        
        inner_w = max(1, width - self.left_margin - self.right_margin)
        inner_h = max(1, height - self.top_margin - self.bottom_margin)

        # --- 2. Color the Inner Grid Area ---
        # Enable Scissor Testing to target ONLY the bounded inner grid box region
        glEnable(GL_SCISSOR_TEST)
        glScissor(self.left_margin, self.bottom_margin, inner_w, inner_h)
        
        #inner grid color 
        glClearColor(0.0, 0.4, 0.0, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT) # Performs clear specifically on the scissor window area
        
        glDisable(GL_SCISSOR_TEST) # Turn it back off so line drawings work cleanly

        # Set standard Viewport inside the margins for core layout asset drawing
        glViewport(self.left_margin, self.bottom_margin, inner_w, inner_h)

        # --- 3. Draw Inner Layout Elements ---
        # Draw Outer Box Border 
        glLineWidth(2.0)
        glColor3f(1.0, 1.0, 1.0) 
        glBegin(GL_LINE_LOOP)
        glVertex2f(azmuthLimits[0], elevationLimits[0])
        glVertex2f(azmuthLimits[1], elevationLimits[0])
        glVertex2f(azmuthLimits[1], elevationLimits[1])
        glVertex2f(azmuthLimits[0], elevationLimits[1])
        glEnd()

        # Draw Primary Core Axis Lines (0,0 center references)
        glLineWidth(0.5)
        glColor3f(0.0, 0.7, 0.0)
        glBegin(GL_LINES)
        # Vertical 0-line
        glVertex2f(0.0, elevationLimits[0])
        glVertex2f(0.0, elevationLimits[1])
        # Horizontal 0-line
        glVertex2f(azmuthLimits[0], 0.0)
        glVertex2f(azmuthLimits[1], 0.0)
        glEnd()

        # Draw Inner Grid Subdivisions
        glLineWidth(0.5)
        glColor3f(0.0, 0.5, 0.0) # Subtle green layout structure lines
        glBegin(GL_LINES)
        for az in range(azmuthLimits[0] + 10, azmuthLimits[1], 10):
            if az != 0:
                glVertex2f(az, elevationLimits[0])
                glVertex2f(az, elevationLimits[1])
        # Elevation lines every 10 deg
        for el in range(elevationLimits[0] + 10, elevationLimits[1], 10):
            if el != 0:
                glVertex2f(azmuthLimits[0], el)
                glVertex2f(azmuthLimits[1], el)
        glEnd()

        # --- Reset Viewport Context for QPainter Compatibility ---
        glViewport(0, 0, width, height)

        # --- 4. Render Text Labels via QPainter Over the Margins ---
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        # Correct mapping logic factoring in the window offsets
        def get_x_pixel(az_deg):
            ratio = (az_deg - azmuthLimits[0]) / (azmuthLimits[1] - azmuthLimits[0])
            return int(self.left_margin + (ratio * inner_w))
            
        def get_y_pixel(el_deg):
            ratio = (el_deg - elevationLimits[0]) / (elevationLimits[1] - elevationLimits[0])
            # QPainter is inverted on Y, 0 is at the absolute top of widget window
            return int(self.top_margin + ((1 - ratio) * inner_h))

        # Render X-Axis (Azimuth) ticks cleanly below the box border
        y_text_pos = get_y_pixel(elevationLimits[0]) + 20 
        for az in range(azmuthLimits[0], azmuthLimits[1] + 1, 30):
            x_pos = get_x_pixel(az)
            painter.drawText(x_pos - 15, y_text_pos, f"{az}°")
            
        # Render Y-Axis (Elevation) ticks safely into the left margin space
        x_text_pos = self.left_margin - 48 
        for el in range(elevationLimits[0], elevationLimits[1] + 1, 30):
            y_pos = get_y_pixel(el)
            painter.drawText(x_text_pos, y_pos + 5, f"{el}°")

        # Static Ambient labels for Axis titles
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        # Draw "AZIMUTH" centered beneath the box
        painter.drawText(int(self.left_margin + (inner_w / 2) - 40), height - 15, "AZIMUTH")
        # Draw "ELEVATION" rotated/positioned near the left edge
        painter.save()
        painter.translate(18, int(self.top_margin + (inner_h / 2) + 40))
        painter.rotate(-90)
        painter.drawText(0, 0, "ELEVATION")
        painter.restore()
            
        painter.end()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HPAdisplay()
    window.resize(800, 600)
    window.setWindowTitle("HPA Display System Matrix Overlay")
    window.show()
    sys.exit(app.exec())