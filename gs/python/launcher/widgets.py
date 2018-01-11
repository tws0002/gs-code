__author__ = 'adamb'

import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from settings import *

class CustomSortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent, title=""):
        super(CustomSortFilterProxyModel, self).__init__(parent)

        self.filter_parents = False

    def filterAcceptsRow(self, row_num, source_parent):
        ''' Overriding the parent function '''
        # Check if the current row matches
        if self.filter_accepts_row_itself(row_num, source_parent):
            return True
        # Traverse up all the way to root and check if any of them match
        #if self.filter_accepts_any_parent(source_parent):
        #   return True
        # Finally, check if any of the children match
        return self.has_accepted_children(row_num, source_parent)

    def filter_accepts_row_itself(self, row_num, parent):
        return super(CustomSortFilterProxyModel, self).filterAcceptsRow(row_num, parent)

    def filter_accepts_any_parent(self, parent):
        ''' Traverse to the root node and check if any of the
            ancestors match the filter
        '''
        result = False
        if self.filter_parents == True:
            while parent.isValid():
                if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                    result = True
                parent = parent.parent()
        else:
            result = False
        return result

    def has_accepted_children(self, row_num, parent):
        ''' Starting from the current node as root, traverse all
            the descendants and test if any of the children match
        '''
        model = self.sourceModel()
        source_index = model.index(row_num, 0, parent)
     
        children_count =  model.rowCount(source_index)
        for i in xrange(children_count):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False

class LchrTitlebar(QFrame):

    def __init__(self, parent, title=""):

        super(LchrTitlebar, self).__init__(parent)

        self.title = title
        self.setMouseTracking(True)
        self.offset = False
        self.sizeStart = False
        self.stop = True
        self.closeOn = False
        self.doClose = False
        self.doMinimize = False 
        self.pinOn = False
        self.doPin = False
        self.closeRect = QRect()
        self.pinRect = QRect()
        self.minimizeRect = QRect()
        self.rsrect_br = QRect()
        self.visibleRect = QRect()

        self.isMoving = False
        self.isResizing = False

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
            if self.rsrect_br.contains(event.pos()):
                self.isResizing = True
                self.offset = event.globalPos() - self.parent().pos()
                self.sizeStart = self.parent().size()
            # if not within button rects, do a move 
            elif self.visibleRect.contains(event.pos()):
                self.isMoving = True
                self.offset = event.globalPos() - self.parent().pos()
                self.sizeStart = self.parent().size()
            else:
                self.isMoving = False
                self.isResizing = False


    def mouseReleaseEvent(self, event):
        super(LchrTitlebar, self).mouseReleaseEvent(event)
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
        self.isMoving = False
        self.isResizing = False

    def mouseMoveEvent(self, event):
        super(LchrTitlebar, self).mouseMoveEvent(event)

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
                #print ("offset x={0} offset y={1}".format((x - x_w),(y - y_w)))

                if self.isResizing:
                    resultX = self.sizeStart.width() + (x - (x_w + self.parent().pos().x()))
                    resultY = self.sizeStart.height() + (y - (y_w + self.parent().pos().y()))
                    self.parent().resize(resultX, resultY)
                elif self.isMoving:
                    resultX = x - x_w
                    resultY = y - y_w
                    self.parent().move(resultX, resultY)
                else:
                    pass


    def paintEvent(self, event):
        super(LchrTitlebar, self).paintEvent(event)

        rsoff = 20

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
        self.visibleRect = QRect(self.parent().rect().topLeft()+QPoint(3,3),QSize(self.parent().rect().width()-rsoff,self.parent().rect().height()-rsoff))

        # define the resize border rectangles
        
        rsw = 20
        self.rsrect_br = QRect(self.rect().bottomRight()-QPoint(rsw,rsw)-QPoint(rsoff,rsoff),QSize(rsw,rsw))


class LchrTreeList(QWidget):
    ''' Creates a TreeView as well as a line edit that filters the internal model and proxy model
        Also uses a custom proxy model class that allows for searches to work with heirarchies
    '''

    sm = None
    pm = None
    le = None
    tvw = None

    qlyt = None



    # remapped signals
    selectionChanged = None

    def __init__(self, parent=None):
        super(LchrTreeList, self).__init__(parent)

        # config flags
        self.alwaysExpand = True
        self.showFirstColOnly = True


        self.qlyt = QVBoxLayout(self)
        self.qtblyt = QHBoxLayout()
        self.qtblyt.setContentsMargins(0,0,0,0)

        self.title = QLabel('')
        self.le = QLineEdit()
        self.tvw = QTreeView()
        model = QStandardItemModel(self.tvw)
        self.titlebtn1 = QPushButton('New')
        #self.titlebtn2 = QPushButton('Config')

        self.qtblyt.addWidget(self.title)
        self.qtblyt.setStretchFactor(self.title,1)
        self.qtblyt.addWidget(self.titlebtn1)
        #self.qtblyt.addWidget(self.titlebtn2)
        self.qlyt.addLayout(self.qtblyt)
        self.qlyt.addWidget(self.le)
        self.qlyt.addWidget(self.tvw)

        self.le.setObjectName('LchrListFilter')
        self.title.setObjectName('LchrListLabel')
        self.le.setPlaceholderText('Search')
        self.tvw.setUniformRowHeights(True)
        self.tvw.setIndentation(8)
        self.tvw.setRootIsDecorated(False)
        self.tvw.setExpandsOnDoubleClick(True)
        self.tvw.setHeaderHidden(True)
        self.tvw.setItemsExpandable(True)
        self.tvw.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setModel(model)

        # map signal functions
        self.selectionChanged = self.tvw.selectionModel().selectionChanged

        # connect internal signals
        self.le.textChanged.connect(self.filterListEditChanged)

    def sourceModel(self):
        return self.sm

    def proxyModel(self):
        return self.pm

    def treeView(self):
        return self.tvw

    def lineEdit(self):
        return self.le

    def setTitle(self,title):
        self.title.setText(title)

    def setFilterParents(self,state):
        self.pm.filter_parents = state

    def setModel(self, stdItemModel):
        self.sm = stdItemModel
        # create an internal proxy model and connect that instead
        self.pm = CustomSortFilterProxyModel(self.tvw)
        self.pm.setSourceModel(self.sm)
        self.pm.setDynamicSortFilter(False)
        self.pm.setFilterRegExp(QRegExp(''))
        self.tvw.setModel(self.pm)
        #super(LchrTreeList, self).__init__(self.pm)

    def setFilterRegExpStr(self, regExpStr):
        self.tvw.clearSelection()
        qregex = QRegExp(regExpStr)
        self.pm.setFilterRegExp(qregex)
        self.tvw.expandAll()
  		

    def filterListEditChanged(self):
        regstr = self.le.text()
        if len(regstr) < 3 and len(regstr) > 0:
            regstr = '^{0}'.format(regstr)

        self.setFilterRegExpStr(regstr)

    def getSelectedItems (self):
        items = []
        for index in self.tvw.selectionModel().selectedIndexes():
            # index of selectedModel is for the proxy filter model only, we have to map to the source model to get valid item
            src_index = self.pm.mapToSource(index)
            item = self.sm.itemFromIndex(src_index)
            items.append(item)
        return items

    def expandItem(self, qStandardItem):
        try:
            index = self.sm.indexFromItem(qStandardItem)
            index = self.pm.mapFromSource(index)
            self.tvw.setExpanded(index,True)   
        except:
            pass

    def procLoadDictToQItem(self, parent_item, headers_list, modelDict):

        for key in sorted(modelDict):
            subitem_list = []
            for header in headers_list:
                qsubitem = None
                if header in modelDict[key]:
                    qsubitem = QStandardItem(str(modelDict[key][header]))
                else:
                    qsubitem = QStandardItem('')
                subitem_list.append(qsubitem)

            parent_item.appendRow(subitem_list)
            if self.alwaysExpand:
                self.expandItem(parent_item)

                
            # recurse on any children dictionaries
            if 'children' in modelDict[key]:
                self.procLoadDictToQItem(subitem_list[0],headers_list,modelDict[key]['children'])



    def loadViewModelFromDict(self, modelDict):
        ''' given a dictionary, parse through each key and fill the item model with the data
            this is a quickway to set lots of data with minimal QT CustomSortFilterProxyModel
        '''
        self.sm.clear()
        #print(modelDict)
        # get list of headers
        headers_list = ['name']
        for grp in sorted(modelDict):
            if 'children' in modelDict[grp]:
                #item = sorted(modelDict[grp]['children'])
                for item in sorted(modelDict[grp]['children']):
                    for header in sorted(modelDict[grp]['children'][item]):
                        if header not in headers_list and header != 'children':
                            headers_list.append(header)
            for header in sorted(modelDict[grp]):
                if header not in headers_list and header != 'children':
                    headers_list.append(header)


        #print ("HEADERS LIST = {0}".format(headers_list))
        # recursively load the dict and any children items
        item_list = self.procLoadDictToQItem(self.sm,headers_list,modelDict)

        self.sm.setHorizontalHeaderLabels(headers_list)

        if self.showFirstColOnly:
            for col in range(1,len(headers_list),1):
                self.tvw.setColumnHidden(col,True)
