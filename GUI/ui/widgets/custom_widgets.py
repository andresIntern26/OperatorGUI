# app/ui/widgets/custom_assets.py
import sys
import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF

class PanTiltControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Highlight states for individual arrows: [North, East, South, West]
        self.active_arrows = [False, False, False, False]

    def update_joystick(self, pan, tilt):
        """
        Accepts raw joystick inputs (pan and tilt values between -1.0 and 1.0).
        """
        # Threshold deadzone
        threshold = 0.3
        
        # In standard screen coordinates, negative tilt is Up (North)
        north = tilt < -threshold
        south = tilt > threshold
        east  = pan > threshold
        west  = pan < -threshold

        self.active_arrows = [north, east, south, west]
        self.update()  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate geometric centers
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        # Structural layout sizing constants
        circle_radius = 40.0
        arrow_distance = 70.0  # Pixels away from center to tip
        arrow_size = 18.0      # Size of arrowhead profile

        #  Dark/Orange 
        orange_dim = QColor(220, 100, 0, 60)      # Faded orange trace when idle
        orange_bright = QColor(255, 140, 0, 255)   # True bright orange when active
        housing_gray = QColor(50, 53, 55, 255)

        # =====================================================================
        # 1. CORE INNER HOUSING CENTER CIRCLE
        # =====================================================================
        circle_pen = QPen(housing_gray)
        circle_pen.setWidth(3)
        painter.setPen(circle_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        painter.drawEllipse(QRectF(
            center_x - circle_radius, 
            center_y - circle_radius, 
            circle_radius * 2, 
            circle_radius * 2
        ))

        # =====================================================================
        #  CONTROL ARROWS
        # =====================================================================
        # Up (North) = -90 deg, Right (East) = 0 deg, Down (South) = 90 deg, Left (West) = 180 deg
        directions = [
            -math.pi / 2,  # North Index 0
            0.0,           # East  Index 1
            math.pi / 2,   # South Index 2
            math.pi        # West  Index 3
        ]

        for i, angle in enumerate(directions):
            # Resolve exact layout vector points
            tip_x = center_x + arrow_distance * math.cos(angle)
            tip_y = center_y + arrow_distance * math.sin(angle)
            tip_point = QPointF(tip_x, tip_y)

            # Generate backing wedge flaps
            left_wing = QPointF(
                tip_x - arrow_size * math.cos(angle - math.pi / 6),
                tip_y - arrow_size * math.sin(angle - math.pi / 6)
            )
            right_wing = QPointF(
                tip_x - arrow_size * math.cos(angle + math.pi / 6),
                tip_y - arrow_size * math.sin(angle + math.pi / 6)
            )

            # Construct geometry
            arrow_poly = QPolygonF([tip_point, left_wing, right_wing])

            # Select brush colors dynamically matching input telemetry maps
            if self.active_arrows[i]:
                painter.setPen(QPen(orange_bright, 2))
                painter.setBrush(orange_bright)
            else:
                painter.setPen(QPen(orange_dim, 1.5))
                painter.setBrush(orange_dim)
                
            painter.drawPolygon(arrow_poly)

        painter.end()


# =====================================================================
#  TESTING SUITE
# =====================================================================
def main():
    app = QApplication(sys.argv)
    
    widget = PanTiltControlWidget()
    widget.setWindowTitle("Joystick Cardinal Map Simulator")
    widget.resize(450, 450)
    widget.setStyleSheet("background-color: #141619;")  # Dark UI backdrop console

   
    time_accumulator = 0.0
    
    def simulate_joystick_sweeps():
        nonlocal time_accumulator
        time_accumulator += 0.03
        
        # Calculate coordinate sweeps out to maximum extents (-1.0 to 1.0)
        simulated_pan = math.cos(time_accumulator)
        simulated_tilt = math.sin(time_accumulator)
        
        # Push variables down into the tracking pipeline
        widget.update_joystick(simulated_pan, simulated_tilt)

    timer = QTimer()
    timer.timeout.connect(simulate_joystick_sweeps)
    timer.start(20)  # High performance 50Hz update cycle
    # -----------------------------------

    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


#TODO: 
#make arrows be able to control the gimbal manually
#