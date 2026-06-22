from PyQt6.QtCore import QCoreApplication, QEvent, Qt
from PyQt6.QtGui import QMouseEvent, QPainter
from PyQt6.QtWidgets import QWidget


class QtEnum:
    class QEvent:
        class Type:
            MouseButtonPress = QEvent.Type.MouseButtonPress
            MouseMove = QEvent.Type.MouseMove
            WindowStateChange = QEvent.Type.WindowStateChange

        class WindowType:
            FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    class Qt:
        class Edge:
            LeftEdge = Qt.Edge.LeftEdge
            RightEdge = Qt.Edge.RightEdge
            TopEdge = Qt.Edge.TopEdge
            BottomEdge = Qt.Edge.BottomEdge
        class WindowState:
            WindowNoState = Qt.WindowState.WindowNoState
        class CursorShape:
            SizeFDiagCursor = Qt.CursorShape.SizeFDiagCursor
            SizeBDiagCursor = Qt.CursorShape.SizeBDiagCursor
            SizeVerCursor = Qt.CursorShape.SizeVerCursor
            SizeHorCursor = Qt.CursorShape.SizeHorCursor
            ArrowCursor = Qt.CursorShape.ArrowCursor
        class WindowType:
            FramelessWindowHint = Qt.WindowType.FramelessWindowHint
        class MouseButton:
            LeftButton = Qt.MouseButton.LeftButton
            RightButton = Qt.MouseButton.RightButton
            MiddleButton = Qt.MouseButton.MiddleButton
            NoButton = Qt.MouseButton.NoButton

        class BrushStyle:
            SolidPattern = Qt.BrushStyle.SolidPattern
            NoBrush = Qt.BrushStyle.NoBrush
        class PenStyle:
            SolidLine = Qt.PenStyle.SolidLine
            NoPen = Qt.PenStyle.NoPen
    class QPainter:
        class RenderHint:
            Antialiasing = QPainter.RenderHint.Antialiasing
            SmoothPixmapTransform = QPainter.RenderHint.SmoothPixmapTransform
