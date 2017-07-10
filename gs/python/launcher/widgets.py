__author__ = 'adamb'

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class CustomSortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent, title=""):
        super(CustomSortFilterProxyModel, self).__init__(parent)

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
        while parent.isValid():
            if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()
        return False

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


class LchrTreeList(QWidget):
	''' Creates a TreeView as well as a line edit that filters the internal model and proxy model
		Also uses a custom proxy model class that allows for searches to work with heirarchies
	'''

	sm = None
	pm = None
	le = None
	tvw = None

	qlyt = None

	# config flags
	alwaysExpand = True

	# remapped signals
	selectionChanged = None

	def __init__(self, parent=None):
		super(LchrTreeList, self).__init__(parent)

		self.qlyt = QVBoxLayout(self)
		self.le = QLineEdit(self.qlyt)
		self.tvw = QTreeView(self.qlyt)
		model = QStandardItemModel(self.tvw)

        self.tvw.setUniformRowHeights(True)
        self.tvw.setIndentation(8)
        self.tvw.setRootIsDecorated(False)
        self.tvw.setHeaderHidden(True)

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

    def setModel(self, stdItemModel):
    	self.sm = stdItemModel
    	# create an internal proxy model and connect that instead
    	self.pm = CustomSortFilterProxyModel(self.tvw)
    	self.pm.setSourceModel(self.sm)
    	self.pm.setDynamicSortFilter(True)
    	self.pm.setFilterRegExp(QRegExp(''))
    	super(LchrTreeList, self).__init__(self.pm)

    def setFilterRegExpStr(self, regExpStr):
    	self.tvw.clearSelection()
    	qregex = QRegExp(regExpStr)
    	self.pm.setFilterRegExp(qregex)

    	# expand the parents to show children
    	if alwaysExpand:
	        # go through each item in the model, if it has children expand it

	        index = self.sm.indexFromItem(self.ui['wdgt']['proj_cat']['Recent'])
	        index = self.pm.mapFromSource(index)
	        self.tvw.setExpanded(index,True)
	        index = sm.indexFromItem(self.ui['wdgt']['proj_cat']['Az'])
	        index = pm.mapFromSource(index)
	        self.tvw.setExpanded(index,True)    		

    def filterListEditChanged(self):
    	regstr = self.le.text()
        if len(regstr) < 2:
            regstr = '^{0}'.format(regstr)

    	self.setFilterRegExpStr(regstr)

    def getSelectedItems (self):
    	items = []
    	for index in self.tvw.SelectionModel().selectedIndexes():
        	# index of selectedModel is for the proxy filter model only, we have to map to the source model to get valid item
            src_index = self.pm.mapToSource(index)
            item = self.sm.itemFromIndex(src_index)
            items.append(item)
        return items
