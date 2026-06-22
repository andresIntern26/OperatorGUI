# cameras.py
import sys
import cv2
import ffmpeg
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

# Modern raw OpenGL bindings for PyQt6
from OpenGL.GL import *

class CameraStreamWorker(QThread):
    """Background worker that continuously pulls video frames from an RTSP stream 
    without blocking the primary GUI loop."""
    frame_received = pyqtSignal(QImage)

    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self._running = True

    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        
        while self._running:
            ret, frame = cap.read()
            if not ret:
                self.msleep(100) # Graceful pause before trying to re-read
                continue
                
            # Convert OpenCV matrix format (BGR) to PyQt compatible format (RGB)
            height, width, channel = frame.shape
            bytes_per_line = channel * width
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            self.frame_received.emit(qt_image.copy()) # Thread-safe deep copy emission

        cap.release()

    def stop(self):
        self._running = False
        if not self.terminate(3000):
            self.terminate()
        self.wait()


class CameraDisplay(QOpenGLWidget): 
    """Hardware accelerated OpenGL display dedicated strictly to rendering 
    the raw, unfiltered incoming video stream sequence."""
    def __init__(self, rtsp_url=None):
        super().__init__()
        self.current_frame = None
        self.texture_id = None

        if rtsp_url:
            self.worker = CameraStreamWorker(rtsp_url)
            self.worker.frame_received.connect(self.update_live_frame)
            self.worker.start()

    @pyqtSlot(QImage)
    def update_live_frame(self, image):
        self.current_frame = image
        self.update() # Triggers paintGL hardware repaint request

    def initializeGL(self): 
        glClearColor(0.0, 0.0, 0.0, 1.0) 
        glEnable(GL_TEXTURE_2D)
        
    def resizeGL(self, b_width, b_height):
        # Set viewport to occupy the absolute entirety of the container bounds
        glViewport(0, 0, max(1, b_width), max(1, b_height))
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # Flat 2D projection normalized mapping coordinates from -1 to 1
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self): 
        glClearColor(0.0, 0.0, 0.0, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
 
        # --- Draw Pure Stream Video ---
        if self.current_frame:
            glEnable(GL_TEXTURE_2D)
            if self.texture_id is None:
                self.texture_id = glGenTextures(1)
            
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            ptr = self.current_frame.bits()
            ptr.setsize(3 * self.current_frame.width() * self.current_frame.height())
            
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.current_frame.width(), self.current_frame.height(), 
                         0, GL_RGB, GL_UNSIGNED_BYTE, ptr.asstring())

            # Draw the clean frame mapping across the complete vertex quad array range
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, -1.0)
            glTexCoord2f(1.0, 1.0); glVertex2f(1.0, -1.0)
            glTexCoord2f(1.0, 0.0); glVertex2f(1.0, 1.0)
            glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, 1.0)
            glEnd()
            glDisable(GL_TEXTURE_2D)
        else:
            # Standby solid color state when stream drops or loads
            glClearColor(0.05, 0.05, 0.07, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def closeEvent(self, event):
        if hasattr(self, 'worker'):
            self.worker.stop()
        super().closeEvent(event)

    """def typeconverter(self, rtsp_url): 
        pass """

if __name__ == '__main__':
    from PyQt6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    rtsp_url = "rtsp://192.168.4.101/axis-media/media.3gp"
    window = CameraDisplay(rtsp_url=rtsp_url)
    window.resize(800, 600)
    window.setWindowTitle("Live Stream")
    window.show()
    sys.exit(app.exec())