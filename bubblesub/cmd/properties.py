# bubblesub - ASS subtitle editor
# Copyright (C) 2018 Marcin Kurczewski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""File properties command."""

from collections import OrderedDict
import typing as T

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import bubblesub.api
import bubblesub.ui.util
from bubblesub.api.cmd import BaseCommand


def _rescale_styles(api: bubblesub.api.Api, factor: float) -> None:
    for style in api.subs.styles:
        style.scale(factor)


class _OptionsGropuBox(QtWidgets.QGroupBox):
    def __init__(
            self,
            api: bubblesub.api.Api,
            parent: QtWidgets.QWidget
    ) -> None:
        super().__init__('Options:', parent)
        self._api = api

        self.res_x_edit = QtWidgets.QSpinBox(self)
        self.res_x_edit.setMinimum(0)
        self.res_x_edit.setMaximum(99999)
        self.res_y_edit = QtWidgets.QSpinBox(self)
        self.res_y_edit.setMinimum(0)
        self.res_y_edit.setMaximum(99999)

        get_resolution_button = QtWidgets.QPushButton('Take from video', self)
        get_resolution_button.clicked.connect(
            self._on_get_resolution_button_click
        )

        self.ycbcr_matrix_combo_box = QtWidgets.QComboBox(self)
        for value in [
                'TV.601', 'PC.601', 'TV.709', 'PC.709',
                'TV.FCC', 'PC.FCC', 'TV.240M', 'PC.240M',
        ]:
            self.ycbcr_matrix_combo_box.addItem(value, userData=value)

        self.wrap_mode_combo_box = QtWidgets.QComboBox(self)
        for key, value in {
                '0': 'Smart wrapping, top line is wider',
                '1': 'End-of-line word wrapping, only \\N breaks',
                '2': 'No word wrapping, both \\n and \\N break',
                '3': 'Smart wrapping, bottom line is wider',
        }.items():
            self.wrap_mode_combo_box.addItem(value, userData=key)

        self.scale_check_box = QtWidgets.QCheckBox(
            'Scale borders and shadows', self
        )

        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        layout.addWidget(QtWidgets.QLabel('Resolution:', self), 0, 0)
        sublayout = QtWidgets.QHBoxLayout()
        sublayout.addWidget(self.res_x_edit)
        sublayout.addWidget(self.res_y_edit)
        sublayout.addWidget(get_resolution_button)
        layout.addLayout(sublayout, 0, 1)

        layout.addWidget(QtWidgets.QLabel('YCbCr matrix:', self), 1, 0)
        layout.addWidget(self.ycbcr_matrix_combo_box, 1, 1)

        layout.addWidget(QtWidgets.QLabel('Wrap style:', self), 2, 0)
        layout.addWidget(self.wrap_mode_combo_box, 2, 1)

        layout.addWidget(self.scale_check_box, 3, 1)

    def _on_get_resolution_button_click(self) -> None:
        self.res_x_edit.setValue(self._api.media.video.width or 0)
        self.res_y_edit.setValue(self._api.media.video.height or 0)


class _MetadataGroupBox(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__('Meta data:', parent)
        self.model = QtGui.QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(['Key', 'Value'])

        self._table_view = QtWidgets.QTableView(self)
        self._table_view.setModel(self.model)
        self._table_view.setTabKeyNavigation(False)

        self._table_view.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        self._table_view.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )

        self._table_view.verticalHeader().setSectionsMovable(True)
        self._table_view.verticalHeader().setDragEnabled(True)
        self._table_view.verticalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.InternalMove
        )

        self._table_view.verticalHeader().setDefaultSectionSize(
            self._table_view.fontMetrics().height() * 1.8
        )

        strip = QtWidgets.QWidget(self)
        add_row_button = QtWidgets.QPushButton('Add new row', strip)
        del_rows_button = QtWidgets.QPushButton('Remove selected rows', strip)
        layout = QtWidgets.QHBoxLayout(strip)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(add_row_button)
        layout.addWidget(del_rows_button)
        layout.addStretch()

        add_row_button.clicked.connect(self._on_add_button_click)
        del_rows_button.clicked.connect(self._on_delete_rows_button_click)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._table_view)
        layout.addWidget(strip)

    def get_data(self) -> T.Dict[str, str]:
        metadata: T.Dict[str, str] = OrderedDict()
        for y in range(self.model.rowCount()):
            visual_y = self._table_view.verticalHeader().visualIndex(y)
            key = self.model.item(visual_y, 0).text().strip()
            value = self.model.item(visual_y, 1).text().strip()
            if key and value:
                metadata[key] = value
        return metadata

    def _on_add_button_click(self) -> None:
        self.model.appendRow([
            QtGui.QStandardItem(''),
            QtGui.QStandardItem(''),
        ])

    def _on_delete_rows_button_click(self) -> None:
        rows = set(
            index.row()
            for index in self._table_view.selectionModel().selectedIndexes()
        )
        for row in sorted(rows, reverse=True):
            self.model.removeRow(row)


class _FilePropertiesDialog(QtWidgets.QDialog):
    def __init__(
            self,
            api: bubblesub.api.Api,
            main_window: QtWidgets.QMainWindow
    ) -> None:
        super().__init__(main_window)
        self._main_window = main_window
        self._api = api

        self._metadata_group_box = _MetadataGroupBox(self)

        strip = QtWidgets.QDialogButtonBox(self)
        strip.setOrientation(QtCore.Qt.Horizontal)
        strip.addButton('OK', strip.AcceptRole)
        apply_button = strip.addButton('Apply', strip.ApplyRole)
        apply_button.clicked.connect(self._commit)
        strip.addButton('Cancel', strip.RejectRole)
        strip.accepted.connect(self.accept)
        strip.rejected.connect(self.reject)

        self._options_group_box = _OptionsGropuBox(api, self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._options_group_box)
        layout.addWidget(self._metadata_group_box)
        layout.addWidget(strip)

        self.accepted.connect(self._commit)

        self._load()
        self.setWindowTitle('File properties')
        self.resize(600, 600)
        self.exec_()

    def _load(self) -> None:
        self._options_group_box.res_x_edit.setValue(
            int(self._api.subs.info.get('PlayResX', '0'))
        )
        self._options_group_box.res_y_edit.setValue(
            int(self._api.subs.info.get('PlayResY', '0'))
        )

        self._options_group_box.ycbcr_matrix_combo_box.setCurrentIndex(
            self._options_group_box.ycbcr_matrix_combo_box.findData(
                self._api.subs.info.get('YCbCr Matrix')
            )
        )

        self._options_group_box.wrap_mode_combo_box.setCurrentIndex(
            self._options_group_box.wrap_mode_combo_box.findData(
                self._api.subs.info.get('WrapStyle')
            )
        )

        self._options_group_box.scale_check_box.setChecked(
            self._api.subs.info.get('ScaledBorderAndShadow', '1') == 'yes'
        )

        for key, value in self._api.subs.info.items():
            if key not in [
                    'PlayResX',
                    'PlayResY',
                    'YCbCr Matrix',
                    'WrapStyle',
                    'ScaledBorderAndShadow',
                    'ScriptType',
            ]:
                self._metadata_group_box.model.appendRow([
                    QtGui.QStandardItem(key),
                    QtGui.QStandardItem(value),
                ])

    def _commit(self) -> None:
        self._api.subs.info.clear()

        self._api.subs.info.update({
            'ScriptType': 'v4.00+',
            'PlayResX': str(self._options_group_box.res_x_edit.value()),
            'PlayResY': str(self._options_group_box.res_y_edit.value()),
            'YCbCr Matrix': (
                self._options_group_box.ycbcr_matrix_combo_box.currentData()
            ),
            'WrapStyle': (
                self._options_group_box.wrap_mode_combo_box.currentData()
            ),
            'ScaledBorderAndShadow': (
                ['no', 'yes']
                [self._options_group_box.scale_check_box.isChecked()]
            ),
        })

        self._api.subs.info.update(self._metadata_group_box.get_data())


class FilePropertiesCommand(BaseCommand):
    """Opens up the metadata editor dialog."""

    name = 'file/properties'
    menu_name = '&Properties...'

    async def run(self) -> None:
        """Carry out the command."""
        await self.api.gui.exec(self._run_with_gui)

    async def _run_with_gui(self, main_window: QtWidgets.QMainWindow) -> None:
        with self.api.undo.capture():
            old_res = int(self.api.subs.info.get('PlayResY', 0))
            _FilePropertiesDialog(self.api, main_window)
            new_res = int(self.api.subs.info.get('PlayResY', 0))
            if old_res != new_res and old_res and new_res and \
                    bubblesub.ui.util.ask(
                            'The resolution was changed. '
                            'Do you want to rescale all the styles now?'
                    ):
                _rescale_styles(self.api, new_res / old_res)


def register(cmd_api: bubblesub.api.cmd.CommandApi) -> None:
    """
    Register commands in this file into the command API.

    :param cmd_api: command API
    """
    cmd_api.register_core_command(FilePropertiesCommand)