from PyQt4.QtCore import *
from PyQt4.QtGui import *

class StylesheetWatcher(object):
    """
    A utility class for live-reloading Qt stylesheets.

    When watched, all changes made to a .css file automatically
    propagate to any running apps with live stylesheets.
    """

    def __init__(self, ):
        self.widget_sheet_map = {} # One-to-many map of stylesheets to their widgets
        self.watcher = None

    def watch(self, widget, stylesheet_path):

        if stylesheet_path not in self.widget_sheet_map:
            self.widget_sheet_map[stylesheet_path] = []
        self.widget_sheet_map[stylesheet_path].append(widget)

        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(stylesheet_path)
        self.watcher.fileChanged.connect(self.update)

        self.update()

    def update(self):
        print ("Updating Stylesheet")
        for stylesheet_path, widgets in self.widget_sheet_map.iteritems():
            with open(stylesheet_path, "r") as fid:
                raw_stylesheet = fid.read()

            for widget in widgets:
                widget.setStyleSheet(raw_stylesheet)