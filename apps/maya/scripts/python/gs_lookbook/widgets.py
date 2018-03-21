__author__ = 'adamb'

import os
from Pyside2.QtCore import *
from PySide2.QtGui import *
from Pyside2.QtWidgets import *


class GSLblGroupBox(QGroupBox):
    def __init__(self, parent=None):
        super(GSLblGroupBox, self).__init__(parent)


class GSListWidgetItem(QListWidgetItem):
    def __init__(self, parent=None):
        super(GSListWidgetItem, self).__init__(parent)    


class GSToolButton(QToolButton):

    def __init__(self, label, pixmap, pixmapHover=None, parent=None, textRight="", textLeft="", colorRight=None, colorLeft=None):

        super(PicButton, self).__init__(parent)
        self.label = label
        self.pixmap = pixmap
        self.pixmapHover = pixmapHover
        self.hover = False
        self.textRight = textRight
        self.textLeft = textLeft
        self.colorRight = colorRight
        self.colorLeft = colorLeft

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.hover and self.pixmapHover:
            if isinstance(self.pixmapHover, QPixmap):
                painter.drawPixmap(self.pixmap.rect(), self.pixmapHover)
            else:
                #### paint selection rectangle
                painter.setBrush(QColor(53,53,53,196))
                painter.setPen(QColor(53,53,53,196))
                painter.drawRect(event.rect())
                #### paint Image on top
                painter.drawPixmap(self.pixmap.rect(), self.pixmap)
        else:
            painter.drawPixmap(self.pixmap.rect(), self.pixmap)

        rect = event.rect().adjusted(4,4,-4,-4)
        if self.colorRight:
            painter.setPen(self.colorRight)

        if self.colorLeft:
            painter.setPen(self.colorLeft)

        painter.drawText(rect, Qt.AlignRight | Qt.AlignBottom, self.textRight)
        painter.setPen(QColor(255,255,255))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignBottom, self.label)


    def sizeHint(self):
        if isinstance(self.pixmapHover, QPixmap):
            size = self.pixmap.size()
        else:
            size = self.pixmap.size() + QSize(0,17)
        return size

    def select(self,hover):
        self.hover = hover
        self.update()


class HoverButton(PicButton):

    def __init__(self, pixmap, pixmapHover=None, parent=None):
        super(HoverButton, self).__init__(pixmap, pixmapHover, parent)
        self.setMouseTracking(True)

    def enterEvent(self,event):
        self.hover = True
        super(HoverButton,self).enterEvent(event)

    def leaveEvent(self,event):
        self.hover = False
        super(HoverButton,self).leaveEvent(event)



class LIgnoreValidator(QValidator):
    def validate(self, string, pos):
        #super(LIgnoreValidator, self).validate(string, pos)
        #string.replace(pos-1, string.count()-pos, '')
        #print ("ingoring validity")
        return QValidator.Invalid, pos

# validator for Initials (uppsercase 2 letters only)
class LRegExpValidator(QRegExpValidator):
    def validate(self, string, pos):
        result = super(LRegExpValidator, self).validate(string, pos)

        #return QValidator.Acceptable, string.toUpper(), pos
        # for old code still using QString, use this instead
        string.replace(0, string.count(), string.toUpper())
        return result[0], pos

class LListWidgetItem(QListWidgetItem):
    def __init__(self, parent=None):
        super(LListWidgetItem, self).__init__(text, parent)
        # ...
        self.innercolor = QColor(200,0,20)

    def setcolor(self,value): self.innercolor = value
    def getcolor(self): return self.innercolor
    color = Property(QColor,getcolor,setcolor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(),self.color)
        # ...
        p.end()

