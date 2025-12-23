# ///////////////////////////////////////////////////////////////
#
# BY: David Rosewater
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

from PyQt5 import QtCore, QtGui, QtWidgets 

class CustomGrip(QtWidgets.QWidget):
    def __init__(self, parent, position, disable_color = False):

        # SETUP UI
        QtWidgets.QWidget.__init__(self)
        self.parent = parent
        self.setParent(parent)
        self.wi = Widgets()

        # SHOW TOP GRIP
        if position == QtCore.Qt.TopEdge:
            self.wi.top(self)
            self.setGeometry(0, 0, self.parent.width(), 10)
            self.setMaximumHeight(10)

            # GRIPS
            top_left = QtWidgets.QSizeGrip(self.wi.top_left)
            top_right = QtWidgets.QSizeGrip(self.wi.top_right)

            # RESIZE TOP
            def resize_top(event):
                delta = event.pos()
                height = max(self.parent.minimumHeight(), self.parent.height() - delta.y())
                geo = self.parent.geometry()
                geo.setTop(geo.bottom() - height)
                self.parent.setGeometry(geo)
                event.accept()
            self.wi.top.mouseMoveEvent = resize_top

            # ENABLE COLOR
            if disable_color:
                self.wi.top_left.setStyleSheet("background: transparent")
                self.wi.top_right.setStyleSheet("background: transparent")
                self.wi.top.setStyleSheet("background: transparent")

        # SHOW BOTTOM GRIP
        elif position == QtCore.Qt.BottomEdge:
            self.wi.bottom(self)
            self.setGeometry(0, self.parent.height() - 10, self.parent.width(), 10)
            self.setMaximumHeight(10)

            # GRIPS
            self.bottom_left = QtWidgets.QSizeGrip(self.wi.bottom_left)
            self.bottom_right = QtWidgets.QSizeGrip(self.wi.bottom_right)

            # RESIZE BOTTOM
            def resize_bottom(event):
                delta = event.pos()
                height = max(self.parent.minimumHeight(), self.parent.height() + delta.y())
                self.parent.resize(self.parent.width(), height)
                event.accept()
            self.wi.bottom.mouseMoveEvent = resize_bottom

            # ENABLE COLOR
            if disable_color:
                self.wi.bottom_left.setStyleSheet("background: transparent")
                self.wi.bottom_right.setStyleSheet("background: transparent")
                self.wi.bottom.setStyleSheet("background: transparent")

        # SHOW LEFT GRIP
        elif position == QtCore.Qt.LeftEdge:
            self.wi.left(self)
            self.setGeometry(0, 10, 10, self.parent.height())
            self.setMaximumWidth(10)

            # RESIZE LEFT
            def resize_left(event):
                delta = event.pos()
                width = max(self.parent.minimumWidth(), self.parent.width() - delta.x())
                geo = self.parent.geometry()
                geo.setLeft(geo.right() - width)
                self.parent.setGeometry(geo)
                event.accept()
            self.wi.leftgrip.mouseMoveEvent = resize_left

            # ENABLE COLOR
            if disable_color:
                self.wi.leftgrip.setStyleSheet("background: transparent")

        # RESIZE RIGHT
        elif position == QtCore.Qt.RightEdge:
            self.wi.right(self)
            self.setGeometry(self.parent.width() - 10, 10, 10, self.parent.height())
            self.setMaximumWidth(10)

            def resize_right(event):
                delta = event.pos()
                width = max(self.parent.minimumWidth(), self.parent.width() + delta.x())
                self.parent.resize(width, self.parent.height())
                event.accept()
            self.wi.rightgrip.mouseMoveEvent = resize_right

            # ENABLE COLOR
            if disable_color:
                self.wi.rightgrip.setStyleSheet("background: transparent")


    def mouseReleaseEvent(self, event):
        self.mousePos = None

    def resizeEvent(self, event):
        if hasattr(self.wi, 'container_top'):
            self.wi.container_top.setGeometry(0, 0, self.width(), 10)

        elif hasattr(self.wi, 'container_bottom'):
            self.wi.container_bottom.setGeometry(0, 0, self.width(), 10)

        elif hasattr(self.wi, 'leftgrip'):
            self.wi.leftgrip.setGeometry(0, 0, 10, self.height() - 20)

        elif hasattr(self.wi, 'rightgrip'):
            self.wi.rightgrip.setGeometry(0, 0, 10, self.height() - 20)

class Widgets(object):
    def top(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.container_top = QtWidgets.QFrame(Form)
        self.container_top.setObjectName(u"container_top")
        self.container_top.setGeometry(QtCore.QRect(0, 0, 500, 10))
        self.container_top.setMinimumSize(QtCore.QSize(0, 10))
        self.container_top.setMaximumSize(QtCore.QSize(16777215, 10))
        self.container_top.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.container_top.setFrameShadow(QtWidgets.QFrame.Raised)
        self.top_layout = QtWidgets.QHBoxLayout(self.container_top)
        self.top_layout.setSpacing(0)
        self.top_layout.setObjectName(u"top_layout")
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_left = QtWidgets.QFrame(self.container_top)
        self.top_left.setObjectName(u"top_left")
        self.top_left.setMinimumSize(QtCore.QSize(10, 10))
        self.top_left.setMaximumSize(QtCore.QSize(10, 10))
        self.top_left.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
        self.top_left.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.top_left.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.top_left.setFrameShadow(QtWidgets.QFrame.Raised)
        self.top_layout.addWidget(self.top_left)
        self.top = QtWidgets.QFrame(self.container_top)
        self.top.setObjectName(u"top")
        self.top.setCursor(QtGui.QCursor(QtCore.Qt.SizeVerCursor))
        self.top.setStyleSheet(u"background-color: rgb(85, 255, 255);")
        self.top.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.top.setFrameShadow(QtWidgets.QFrame.Raised)
        self.top_layout.addWidget(self.top)
        self.top_right = QtWidgets.QFrame(self.container_top)
        self.top_right.setObjectName(u"top_right")
        self.top_right.setMinimumSize(QtCore.QSize(10, 10))
        self.top_right.setMaximumSize(QtCore.QSize(10, 10))
        self.top_right.setCursor(QtGui.QCursor(QtCore.Qt.SizeBDiagCursor))
        self.top_right.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.top_right.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.top_right.setFrameShadow(QtWidgets.QFrame.Raised)
        self.top_layout.addWidget(self.top_right)

    def bottom(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.container_bottom = QtWidgets.QFrame(Form)
        self.container_bottom.setObjectName(u"container_bottom")
        self.container_bottom.setGeometry(QtCore.QRect(0, 0, 500, 10))
        self.container_bottom.setMinimumSize(QtCore.QSize(0, 10))
        self.container_bottom.setMaximumSize(QtCore.QSize(16777215, 10))
        self.container_bottom.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.container_bottom.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bottom_layout = QtWidgets.QHBoxLayout(self.container_bottom)
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setObjectName(u"bottom_layout")
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_left = QtWidgets.QFrame(self.container_bottom)
        self.bottom_left.setObjectName(u"bottom_left")
        self.bottom_left.setMinimumSize(QtCore.QSize(10, 10))
        self.bottom_left.setMaximumSize(QtCore.QSize(10, 10))
        self.bottom_left.setCursor(QtGui.QCursor(QtCore.Qt.SizeBDiagCursor))
        self.bottom_left.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.bottom_left.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.bottom_left.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom_left)
        self.bottom = QtWidgets.QFrame(self.container_bottom)
        self.bottom.setObjectName(u"bottom")
        self.bottom.setCursor(QtGui.QCursor(QtCore.Qt.SizeVerCursor))
        self.bottom.setStyleSheet(u"background-color: rgb(85, 170, 0);")
        self.bottom.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.bottom.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom)
        self.bottom_right = QtWidgets.QFrame(self.container_bottom)
        self.bottom_right.setObjectName(u"bottom_right")
        self.bottom_right.setMinimumSize(QtCore.QSize(10, 10))
        self.bottom_right.setMaximumSize(QtCore.QSize(10, 10))
        self.bottom_right.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
        self.bottom_right.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.bottom_right.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.bottom_right.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom_right)

    def left(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.leftgrip = QtWidgets.QFrame(Form)
        self.leftgrip.setObjectName(u"left")
        self.leftgrip.setGeometry(QtCore.QRect(0, 10, 10, 480))
        self.leftgrip.setMinimumSize(QtCore.QSize(10, 0))
        self.leftgrip.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
        self.leftgrip.setStyleSheet(u"background-color: rgb(255, 121, 198);")
        self.leftgrip.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.leftgrip.setFrameShadow(QtWidgets.QFrame.Raised)

    def right(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(500, 500)
        self.rightgrip = QtWidgets.QFrame(Form)
        self.rightgrip.setObjectName(u"right")
        self.rightgrip.setGeometry(QtCore.QRect(0, 0, 10, 500))
        self.rightgrip.setMinimumSize(QtCore.QSize(10, 0))
        self.rightgrip.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
        self.rightgrip.setStyleSheet(u"background-color: rgb(255, 0, 127);")
        self.rightgrip.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.rightgrip.setFrameShadow(QtWidgets.QFrame.Raised)
