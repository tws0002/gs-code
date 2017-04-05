__author__ = 'adamb'
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

## HACK replace this with proper global vars
RES = os.path.join(os.environ['GSBRANCH'],'gs', 'python', 'launcher','res')

class GSTitleBar(QFrame):

    def __init__(self, parent, title=""):

        super(GSTitleBar, self).__init__(parent)

        self.title = title
        self.setMouseTracking(True)
        self.offset = False
        self.stop = True
        self.closeOn = False
        self.doClose = False
        self.doMinimize = False 
        self.pinOn = False
        self.doPin = False

    def mousePressEvent(self, event):
        self.stop = False
        self.doMinimize = False
        if event.button() == Qt.LeftButton:
            if self.closeRect.contains( event.pos() ):
                self.stop = True
                self.doClose = True
            elif self.pinRect.contains(event.pos()):
                self.stop = True
                self.doPin = not self.doPin
            elif self.minimizeRect.contains(event.pos()):
                self.stop = True
                self.doMinimize = True
            else:
                self.offset = event.globalPos() - self.parent().pos()

    def mouseReleaseEvent(self, event):
        super(GSTitleBar, self).mouseReleaseEvent(event)
        self.stop = True
        if self.doClose and self.closeOn:
            self.parent().close_event(event=None)
            self.parent().close()
        elif self.pinOn:
            if self.doPin:
                print "pin"
                self.parent().setWindowFlags( self.parent().windowFlags() | Qt.WindowStaysOnTopHint )
                self.parent().show()
            else:
                print "unpin"
                self.parent().setWindowFlags(self.parent().windowFlags() & ~Qt.WindowStaysOnTopHint )
                self.parent().show()
        elif self.doMinimize:
            self.parent().showMinimized()

    def mouseMoveEvent(self, event):
        super(GSTitleBar, self).mouseMoveEvent(event)

        self.closeOn = False
        self.pinOn = False

        if self.closeRect.contains(event.pos()):
            self.closeOn = True
            self.update()
        elif self.pinRect.contains(event.pos()):
            self.pinOn = True
            self.update()
        else:
            self.closeOn = False
            self.pinOn = False
            self.update()

        if not self.stop:

            x=event.globalX()
            y=event.globalY()

            if self.offset:
                x_w = self.offset.x()
                y_w = self.offset.y()

                resultX = x - x_w
                resultY = y - y_w

                self.parent().move( resultX, resultY )


    def paintEvent(self, event):
        super(GSTitleBar, self).paintEvent(event)

        painter = QPainter(self)
        painter.setBrush(QColor(35,35,36))
        painter.setPen(QColor(35,35,36))

        rect = QRect(0,0,self.width(), 25)
        #painter.drawRect(rect)
        self.topBarRect = rect

        painter.setBrush(QColor(160,160,165))
        painter.setPen(QColor(160,160,165))

        font = painter.font()
        #font.setWeight(QFont.Bold)
        font.setPixelSize(14)
        painter.setFont(font)

        #painter.drawText(QPoint(20,20),self.title)
        self.logo = QImage(os.path.join(RES,"title_logo.png"))
        rect = self.rect().topLeft() + QPoint(20, 20)
        painter.drawImage(rect, self.logo)

        self.closeImage = QImage(os.path.join(RES,"close.png"))
        self.pinImage = QImage(os.path.join(RES,"pinOff.png"))
        self.minimizeImage = QImage(os.path.join(RES,"minimiseIcon.png"))

        if self.underMouse():
            if self.closeOn:
                self.closeImage.invertPixels()

        if self.pinOn or self.doPin:
            self.pinImage = QImage(os.path.join(RES,"pin.png"))
            self.pinImage.invertPixels()

        #self.closeImage = self.closeImage.scaled(40,20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pinImage = self.pinImage.scaled(30,30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.minimizeImage = self.minimizeImage.scaled(30,30, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        rect = self.rect().topRight() - QPoint(self.closeImage.width() + 30, -18)
        pinRect = self.rect().topRight() - QPoint(self.closeImage.width() + self.pinImage.width() + 35,-18)
        minimizeRect = self.rect().topRight() - QPoint(self.closeImage.width() + self.pinImage.width() + self.minimizeImage.width() + 40, -18)


        painter.drawImage(rect, self.closeImage)
        painter.drawImage(pinRect, self.pinImage)
        painter.drawImage(minimizeRect, self.minimizeImage)
        self.closeRect = QRect(rect,QSize(self.closeImage.width(), self.closeImage.height()))
        self.pinRect = QRect(pinRect,QSize(self.pinImage.width(), self.pinImage.height()))
        self.minimizeRect = QRect(minimizeRect, QSize(self.minimizeImage.width(), self.minimizeImage.height()))

class GSLblGroupBox(QGroupBox):
    def __init__(self, parent=None):
        super(GSLblGroupBox, self).__init__(parent)

class GridLayout(QGridLayout):

    def __init__(self, cols=0, rows=0):

        if cols:
            self.cols = True
            self.n = cols
        elif rows:
            self.cols = False
            self.n = rows

        self.i = 0
        self.j = 0

        super(GridLayout,self).__init__()

    def inc( self):

        self.i = self.i+1
        if self.i==self.n:
            self.i=0
            self.j=self.j+1

    def addWidgetAuto( self, widget):

        if not self.cols:
            super(GridLayout,self).addWidget( widget, self.i, self.j)
        else:
            super(GridLayout,self).addWidget( widget, self.j, self.i)

        self.inc()

    def removeWidgetAuto(self, widget):

        super(GridLayout,self).removeWidget( widget)

        self.i = self.i-1
        if self.i==-1:
            self.i=self.n-1
            self.j=self.j-1

    def removeLayoutAuto(self, widget):

        super(GridLayout,self).removeItem( widget)

        self.i = self.i-1
        if self.i==-1:
            self.i=self.n-1
            self.j=self.j-1

    def addLayoutAuto( self, widget):

        if not self.cols:
            super(GridLayout,self).addLayout( widget, self.i, self.j)
        else:
            super(GridLayout,self).addLayout( widget, self.j, self.i)

        self.inc()


class AppLayout(QVBoxLayout):

    def __init__(self, name, parent):

        self.name = name
        self.parent = parent

        super(AppLayout,self).__init__()

        self.setup()

    def setup( self):

        iconpath = os.path.join( RES, "{0}.png".format(self.name))
        pixmap = QPixmap( iconpath)

        self.button = PicButton(pixmap, pixmapHover=True, textRight="", textLeft="")
        self.button.clicked.connect( lambda clicked, name=self.name: self.parent.selectApp(name))
        self.addWidget( self.button)

    def select( self, selected):
        self.button.select( selected)

    def update(self, version, status):

        self.button.textLeft = version
        self.button.textRight = status
        self.button.colorRight = [QColor(255,0,0), QColor(6,244,47)][status=='OK']



class PicButton(QToolButton):

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

# combo box that selects all text when editing
class LComboBox(QComboBox):
    def __init__(self, parent=None):
        super(LComboBox, self).__init__(parent)
        #l = LIgnoreValidator()
        #self.setValidator(l)

    #def mousePressEvent(self, e):
    #    super(LComboBox, self).mousePressEvent(e)
    #    self.lineEdit().selectAll()
    #    # connect up signals
    #    #self.lineEdit().focusInEvent.connect(self.lineEditTextEdit)
    #def focusInEvent(self, e):
    #    #super(LComboBox, self).focusInEvent(e)
    #    print ("focus in event")
    #    self.lineEdit().selectAll()


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

#class LListWidgetItem(QListWidgetItem):
#    def __init__(self, parent=None):
#        super(LListWidgetItem, self).__init__(text, parent)
#        # ...
#        self.innercolor = QColor(200,0,20)
#
#    def setcolor(self,value): self.innercolor = value
#    def getcolor(self): return self.innercolor
#    color = Property(QColor,getcolor,setcolor)
#
#    def paintEvent(self, event):
#        p = QPainter(self)
#        p.fillRect(self.rect(),self.color)
#        # ...
#        p.end()

