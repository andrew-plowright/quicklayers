# Project
from quicklayers.__about__ import __title__
from quicklayers.quick_layers_widget import QuickLayersWidget

# qgis
from qgis.gui import QgisInterface
from qgis.utils import showPluginHelp

# PyQT
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget


class QuickLayersPlugin:

    def __init__(self, iface: QgisInterface):
        self.dock_widget = None
        self.iface = iface

    def initGui(self):

        # Load Dock Widget
        self.dock_widget = QDockWidget(__title__, self.iface.mainWindow())
        self.dock_widget.setWidget(QuickLayersWidget(self.iface.mainWindow()))
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def unload(self):

        # Clean up templates
        self.dock_widget.widget().clean_up()

        # Clean up dock widget
        self.dock_widget.hide()
        self.iface.removeDockWidget(self.dock_widget)
        self.dock_widget.deleteLater()
