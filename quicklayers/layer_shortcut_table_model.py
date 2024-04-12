# Project
from quicklayers.layer_shortcut import LayerShortcut
from quicklayers.__about__ import __title__

# Misc
from typing import List
from pathlib import Path
import json

# qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsProject, QgsMapLayerProxyModel, QgsMessageLog, Qgis

# PyQt
from qgis.PyQt.QtCore import QModelIndex, Qt, QAbstractTableModel, QVariant, QSize, pyqtSlot
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QItemDelegate, QStyledItemDelegate, QDialog, QPushButton
from qgis.PyQt.QtXml import QDomElement


class LayerShortcutTableModel(QAbstractTableModel):

    header_labels = [
        "Shortcut",
        "Layer",
        "Remove",
    ]

    def __init__(self, parent):
        super().__init__(parent)

        self.layer_shortcuts = []

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            header_name = self.header_labels[section]
            return header_name

        return super().headerData(section, orientation, role)

    def rowCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.layer_shortcuts)

    def columnCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.header_labels)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        row = index.row()
        column = index.column()
        column_header_label = self.header_labels[column]

        if row >= len(self.layer_shortcuts):
            return QVariant()

        layer_shortcut = self.layer_shortcuts[row]

        if (role == Qt.DisplayRole) & (column_header_label == "Shortcut"):

            return layer_shortcut.get_shortcut_str()

        if role == Qt.ForegroundRole:
            if not layer_shortcut.is_valid():
                return QColor(180, 180, 180)

            if column_header_label == "Shortcut":
                if layer_shortcut.shortcut.key().toString() == "":
                    return QColor(180, 180, 180)

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        column_header_label = self.header_labels[index.column()]
        layer_shortcut = self.layer_shortcuts[index.row()]

        if column_header_label == 'Layer' and role == Qt.EditRole:
            layer_shortcut.set_map_lyr(value)
            self.dataChanged.emit(index, index)
            return True

        if column_header_label == 'Shortcut':
            if value == "":
                value = None
            return layer_shortcut.set_shortcut(value)


    def add_layer_shortcuts(self, layer_shortcuts: List[LayerShortcut]) -> None:
        row = self.rowCount()

        self.beginInsertRows(QModelIndex(), row, row + len(layer_shortcuts) - 1)

        for layer_shortcut in layer_shortcuts:

            self.layer_shortcuts.append(layer_shortcut)

            layer_shortcut.validChanged.connect(self.refresh_layer_shortcut)

        self.endInsertRows()

    @pyqtSlot()
    def refresh_layer_shortcut(self) -> None:
        # QgsMessageLog.logMessage(f"Loaded map layer '{self.sender()}'", tag=__title__, level=Qgis.Info)
        row = self.layer_shortcuts.index(self.sender())

        index1 = self.createIndex(row, 0)
        index2 = self.createIndex(row, self.columnCount())

        self.dataChanged.emit(index1, index2)


    def remove_layer_shortcut(self, layer_shortcut: LayerShortcut) -> None:
        try:
            row = self.layer_shortcuts.index(layer_shortcut)

            self.beginRemoveRows(QModelIndex(), row, row)

            layer_shortcut.delete()

            self.layer_shortcuts.remove(layer_shortcut)

            self.endRemoveRows()

        except ValueError:
            print(f'Layer Shortcut not found')

    def clear_layer_shortcuts(self):
        if len(self.layer_shortcuts) > 0:

            self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)

            for layer_shortcut in self.layer_shortcuts:
                layer_shortcut.delete()

            self.layer_shortcuts.clear()

            self.endRemoveRows()

    def get_layer_shortcuts(self):
        return self.layer_shortcuts

    def from_json(self, path: Path):
        self.clear_layer_shortcuts()

        layer_shortcuts = []

        qgs_project = QgsProject().instance()

        with open(path) as f:
            data = json.load(f)

        for d in data:
            map_lyr = map_lyr_by_name(qgs_project, d['map_lyr_name'])

            layer_shortcut = LayerShortcut(
                parent=self,
                widget=self.parent(),
                shortcut_str=d['shortcut_str'],
                map_lyr=map_lyr
            )

            layer_shortcuts.append(layer_shortcut)

        self.add_layer_shortcuts(layer_shortcuts)

    def to_json(self, path: Path):
        layer_shortcuts = self.get_layer_shortcuts()

        out_list = []

        for layer_shortcut in layer_shortcuts:

            layer_shortcut_json = {
                'map_lyr_name': layer_shortcut.map_lyr.name(),
                'shortcut_str': layer_shortcut.get_shortcut_str()
            }

            out_list.append(layer_shortcut_json)

        json_object = json.dumps(out_list, indent=4)

        with open(path, "w") as outfile:
            outfile.write(json_object)


    def from_xml(self, elem: QDomElement):
        self.clear_layer_shortcuts()

        layer_shortcuts = []

        qgs_project = QgsProject().instance()

        child_nodes = elem.childNodes()

        for i in range(child_nodes.length()):

            layer_shortcut_elem = child_nodes.item(i)
            layer_shortcut_attr = layer_shortcut_elem.attributes()

            shortcut_str = layer_shortcut_attr.namedItem('shortcut').nodeValue()
            map_lyr_name = layer_shortcut_attr.namedItem('map_lyr').nodeValue()

            # QgsMessageLog.logMessage(f"Template '{name}' has {default_value_elems.length()} default values", tag=__title__, level=Qgis.Warning)

            map_lyr = map_lyr_by_name(qgs_project, map_lyr_name)

            layer_shortcut = LayerShortcut(
                parent=self,
                widget=self.parent(),
                shortcut_str=shortcut_str,
                map_lyr=map_lyr
            )

            layer_shortcuts.append(layer_shortcut)

        self.add_layer_shortcuts(layer_shortcuts)


class QgsMapLayerComboDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QgsMapLayerComboBox(parent)
        #editor.setFilters(QgsMapLayerProxyModel.VectorLayer)
        editor.setAllowEmptyLayer(True)
        editor.layerChanged.connect(lambda: self.closeEditor.emit(editor))
        return editor

    def setEditorData(self, editor, index):
        map_lyr = index.model().layer_shortcuts[index.row()].map_lyr
        editor.setLayer(map_lyr)

    def setModelData(self, editor, model, index):
        data = editor.currentLayer()
        model.setData(index, data)


class RemoveDelegate(QItemDelegate):

    def __init__(self, parent, delete_icon):
        super().__init__(parent)
        self.delete_icon = delete_icon

    def createEditor(self, parent, option, index):
        model = index.model()
        template = model.layer_shortcuts[index.row()]
        editor = QPushButton(parent)
        editor.setIcon(self.delete_icon)
        editor.setIconSize(QSize(20, 20))
        editor.clicked.connect(lambda: model.remove_layer_shortcut(template))
        # editor.setWindowFlags(Qt.Popup)
        return editor

    def setModelData(self, editor, model, index):
        model.setData(index, True)


def map_lyr_by_name(qgs_project: QgsProject, name):

    map_lyr = None

    # Get all map layers with this name
    map_lyrs = qgs_project.mapLayersByName(name)

    # Return first layer if multiple layers have the same name
    if len(map_lyrs) > 0:
        map_lyr = map_lyrs[0]

    return map_lyr
