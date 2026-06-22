# coding:utf-8
from PyQt6.QtCore import QCoreApplication, QEvent, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget

from ..titlebar import TitleBar
from ..utils.enum import QtEnum
from ..utils.linux_utils import LinuxMoveResize
from .window_effect import LinuxWindowEffect


class LinuxFramelessWindow(QWidget):
    """ Frameless window for Linux system """

    BORDER_WIDTH = 5

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.windowEffect = LinuxWindowEffect(self)
        self.titleBar = TitleBar(self)
        self._isResizeEnabled = True

        self.updateFrameless()
        QCoreApplication.instance().installEventFilter(self)

        self.titleBar.raise_()
        self.resize(500, 500)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.titleBar.resize(self.width(), self.titleBar.height())

    def updateFrameless(self):
        self.setWindowFlags(self.windowFlags() | QtEnum.Qt.WindowType.FramelessWindowHint)

    def setTitleBar(self, titleBar):
        """ set custom title bar

        Parameters
        ----------
        titleBar: TitleBar
            title bar
        """
        self.titleBar.deleteLater()
        self.titleBar.hide()
        self.titleBar = titleBar
        self.titleBar.setParent(self)
        self.titleBar.raise_()

    def setResizeEnabled(self, isEnabled: bool):
        """ set whether resizing is enabled """
        self._isResizeEnabled = isEnabled

    def eventFilter(self, obj, event):
        et = event.type()
        if et != QtEnum.QEvent.Type.MouseButtonPress and et != QtEnum.QEvent.Type.MouseMove or not self._isResizeEnabled:
            return False

        edges = Qt.Edge(0)
        pos = event.globalPosition().toPoint() - self.pos()
        if pos.x() < self.BORDER_WIDTH:
            edges |= QtEnum.Qt.Edge.LeftEdge
        if pos.x() >= self.width()-self.BORDER_WIDTH:
            edges |= QtEnum.Qt.Edge.RightEdge
        if pos.y() < self.BORDER_WIDTH:
            edges |= QtEnum.Qt.Edge.TopEdge
        if pos.y() >= self.height()-self.BORDER_WIDTH:
            edges |= QtEnum.Qt.Edge.BottomEdge

        # change cursor
        if et == QtEnum.QEvent.Type.MouseMove and self.windowState() == QtEnum.Qt.WindowState.WindowNoState:
            if edges in (QtEnum.Qt.Edge.LeftEdge | QtEnum.Qt.Edge.TopEdge, QtEnum.Qt.Edge.RightEdge | QtEnum.Qt.Edge.BottomEdge):
                self.setCursor(QtEnum.Qt.CursorShape.SizeFDiagCursor)
            elif edges in (QtEnum.Qt.Edge.RightEdge | QtEnum.Qt.Edge.TopEdge, QtEnum.Qt.Edge.LeftEdge | QtEnum.Qt.Edge.BottomEdge):
                self.setCursor(QtEnum.Qt.CursorShape.SizeBDiagCursor)
            elif edges in (QtEnum.Qt.Edge.TopEdge, QtEnum.Qt.Edge.BottomEdge):
                self.setCursor(QtEnum.Qt.CursorShape.SizeVerCursor)
            elif edges in (QtEnum.Qt.Edge.LeftEdge, QtEnum.Qt.Edge.RightEdge):
                self.setCursor(QtEnum.Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(QtEnum.Qt.CursorShape.ArrowCursor)

        elif obj in (self, self.titleBar) and et == QtEnum.QEvent.Type.MouseButtonPress and edges:
            LinuxMoveResize.starSystemResize(self, event.globalPosition(), edges)

        return super().eventFilter(obj, event)
