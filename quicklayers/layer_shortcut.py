# Project
from quicklayers.__about__ import __title__

# Misc
from typing import Dict, List

# qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsDefaultValue, QgsProject, Qgis, QgsMapLayerProxyModel, QgsMapLayer, QgsMessageLog
from qgis.utils import iface

# PyQt
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import QShortcut,QApplication, QAction
from qgis.PyQt.QtXml import QDomDocument, QDomElement

class LayerShortcut(QObject):

    validChanged = pyqtSignal(bool)

    def __init__(self, parent, widget, shortcut_str: str, map_lyr: QgsMapLayer):

        super().__init__(parent)

        # QgsMessageLog.logMessage(f"Template's parent class is: {self.parent().__class__.__name__}", tag=__title__, level=Qgis.Info)

        # Register shortcut
        self.shortcut = QShortcut(QKeySequence(), widget)
        self.shortcut.activated.connect(self.shortcut_pressed)
        self.set_shortcut(shortcut_str)

        self.valid = False

        self.map_lyr = None
        self.set_map_lyr(map_lyr)

        self.destroyed.connect(self.confirm_deletion)

    def shortcut_pressed(self):

        if self.is_valid():
            # QgsMessageLog.logMessage(f"Shortcut pressed! for " + self.map_lyr_name(), tag=__title__, level=Qgis.Info)

            # Get layer's node from the layer tree
            layer_tree_node = QgsProject.instance().layerTreeRoot().findLayer(self.map_lyr.id())

            # If valid, set toggle its visibility
            if layer_tree_node:
                layer_tree_node.setItemVisibilityChecked(not layer_tree_node.isVisible())


    def set_map_lyr(self, map_lyr):

        if map_lyr:
            # QgsMessageLog.logMessage(f"Loaded map layer '{map_lyr.name()}'", tag=__title__, level=Qgis.Info)
            self.map_lyr = map_lyr
            self.map_lyr.willBeDeleted.connect(self.remove_map_lyr)

        else:
            # QgsMessageLog.logMessage(f"Removed map layer'", tag=__title__, level=Qgis.Info)
            if self.map_lyr is not None:
                self.map_lyr.willBeDeleted.disconnect(self.remove_map_lyr)
                self.map_lyr = None

        self.check_validity()

    def remove_map_lyr(self):

        self.set_map_lyr(None)

    def get_map_lyr(self) -> QgsMapLayer:

        return self.map_lyr

    def map_lyr_name(self) -> str:

        if self.map_lyr:
            return self.map_lyr.name()
        else:
            return 'None'

    def is_valid(self) -> bool:

        return self.valid

    def check_validity(self) -> bool:

        valid = True
        if self.map_lyr is None:
            #QgsMessageLog.logMessage(f"Feature template '{self.get_name()}' invalid: no Map layer", tag=__title__, level=Qgis.Warning)
            valid = False

        self.set_validity(valid)

        return valid

    def set_validity(self, value):

        if value:
            if not self.valid:
                self.valid = True
                self.validChanged.emit(True)
        else:
            if self.valid:
                self.valid = False
                self.validChanged.emit(False)

    def set_shortcut(self, value) -> bool:

        if value:

            # Get list of existing shortcuts
            existing_shortcuts = []
            for widget in QApplication.topLevelWidgets():
                shortcut_keys = [shortcut.key() for shortcut in widget.findChildren(QShortcut)]
                action_keys = [action.shortcut() for action in widget.findChildren(QAction)]
                existing_shortcuts.extend(shortcut_keys)
                existing_shortcuts.extend(action_keys)

            # Check if shortcut already exists
            for sc in existing_shortcuts:
                if sc.toString() and value == sc:
                    iface.messageBar().pushMessage("Shortcut keys",
                                                   f"The shortcut keys '{value}' is already being used",
                                                   level=Qgis.Warning)
                    return False

        self.shortcut.setKey(QKeySequence(value))
        return True

    def delete_shortcut(self) -> None:

        self.shortcut.setParent(None)
        self.shortcut.deleteLater()

    def get_shortcut_str(self) -> str:

        str = self.shortcut.key().toString()
        if str == '':
            str = 'None'
        return str


    def to_xml(self, doc: QDomDocument) -> QDomElement:
    
        template_elem = doc.createElement('layer_shortcut')

        template_elem.setAttribute('map_lyr', self.map_lyr_name())
        template_elem.setAttribute('shortcut', self.get_shortcut_str())

        return template_elem

    @staticmethod
    def confirm_deletion(self):

        # QgsMessageLog.logMessage(f"Confirm deletion!", tag=__title__, level=Qgis.Info)
        ...

    def delete(self):

        self.delete_shortcut()
        self.setParent(None)
        self.deleteLater()
