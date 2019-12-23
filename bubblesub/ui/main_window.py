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

import asyncio
import enum

from PyQt5 import QtCore, QtGui, QtWidgets

from bubblesub.api import Api
from bubblesub.cfg.hotkeys import HotkeyContext
from bubblesub.cfg.menu import MenuContext
from bubblesub.data import ROOT_DIR
from bubblesub.ui.audio import Audio
from bubblesub.ui.console import Console
from bubblesub.ui.editor import Editor
from bubblesub.ui.hotkeys import HotkeyManager
from bubblesub.ui.menu import setup_menu
from bubblesub.ui.statusbar import StatusBar
from bubblesub.ui.subs_grid import SubtitlesGrid
from bubblesub.ui.themes import ThemeManager
from bubblesub.ui.util import build_splitter
from bubblesub.ui.video import Video
from bubblesub.ui.views import ViewManager


class ClosingState(enum.IntEnum):
    Ready = 1
    WaitingForConfirmation = 2
    Confirmed = 3


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, api: Api) -> None:
        super().__init__()

        self._closing_state = ClosingState.Ready
        self._api = api
        self._update_title()

        self.theme_mgr = ThemeManager(api, self)

        self.video = Video(api, self)
        self.audio = Audio(api, self.theme_mgr, self)
        self.editor = Editor(api, self.theme_mgr, self)
        self.subs_grid = SubtitlesGrid(api, self.theme_mgr, self)
        self.status_bar = StatusBar(api, self)
        self.console = Console(api, self.theme_mgr, self)

        self.view_manager = ViewManager(api, self)

        self.editor_splitter = build_splitter(
            self,
            [(4, self.audio), (1, self.editor)],
            orientation=QtCore.Qt.Vertical,
        )

        self.top_bar = build_splitter(
            self,
            [(1, self.video), (1, self.editor_splitter)],
            orientation=QtCore.Qt.Horizontal,
        )

        self.console_splitter = build_splitter(
            self,
            [(2, self.subs_grid), (1, self.console)],
            orientation=QtCore.Qt.Horizontal,
        )

        self.main_splitter = build_splitter(
            self,
            [(1, self.top_bar), (5, self.console_splitter)],
            orientation=QtCore.Qt.Vertical,
        )

        self.video.layout().setContentsMargins(0, 0, 2, 0)
        self.editor_splitter.setContentsMargins(2, 0, 0, 0)

        self.main_wrapper = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.main_wrapper)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.main_splitter)

        self.setCentralWidget(self.main_wrapper)
        self.setStatusBar(self.status_bar)

        self.setWindowIcon(
            QtGui.QIcon(str(ROOT_DIR / "bubblesub-icon-64.png"))
        )

        self.subs_grid.setFocus()
        self.subs_grid.restore_grid_columns()
        self.view_manager.restore_view()
        self._restore_fonts()
        self._restore_splitters()
        self._setup_menu()

        HotkeyManager(
            api,
            {
                HotkeyContext.Global: self,
                HotkeyContext.Spectrogram: self.audio,
                HotkeyContext.SubtitlesGrid: self.subs_grid,
            },
        )

        api.gui.terminated.connect(self._store_splitters)
        api.gui.terminated.connect(self.view_manager.store_view)
        api.gui.terminated.connect(self._store_fonts)

        api.gui.request_quit.connect(self.close)
        api.gui.request_begin_update.connect(
            lambda: self.setUpdatesEnabled(False)
        )
        api.gui.request_end_update.connect(
            lambda: self.setUpdatesEnabled(True)
        )
        api.subs.loaded.connect(self._update_title)
        api.cmd.commands_loaded.connect(self._setup_menu)
        api.cfg.opt.changed.connect(self._setup_menu)
        QtWidgets.QApplication.instance().installEventFilter(self)

    def eventFilter(
        self, source: QtCore.QObject, event: QtCore.QEvent
    ) -> bool:
        if (
            event.type() == QtCore.QEvent.WindowBlocked
            and not self._api.playback.is_paused
        ):
            # pause video for modal dialogs
            self._api.playback.is_paused = True
        return False

    def closeEvent(self, event: QtCore.QEvent) -> None:
        if self._closing_state == ClosingState.Confirmed:
            self._api.gui.terminated.emit()
            event.accept()
        elif self._closing_state == ClosingState.WaitingForConfirmation:
            event.ignore()
        elif self._closing_state == ClosingState.Ready:

            def on_close(task: "asyncio.Future[bool]") -> None:
                if task.result():
                    self._closing_state = ClosingState.Confirmed
                    self.close()
                else:
                    self._closing_state = ClosingState.Ready

            self._closing_state = ClosingState.WaitingForConfirmation
            task = asyncio.ensure_future(
                self._api.gui.confirm_unsaved_changes()
            )
            task.add_done_callback(on_close)
            event.ignore()

    def _setup_menu(self) -> None:
        setup_menu(
            self._api,
            self.menuBar(),
            self._api.cfg.menu[MenuContext.MainMenu],
            HotkeyContext.Global,
        )

    def _restore_splitters(self) -> None:
        def _load(widget: QtWidgets.QWidget, key: str) -> None:
            data = self._api.cfg.opt["gui"]["splitters"].get(key, None)
            if data:
                widget.restoreState(data)

        _load(self.audio, "audio")
        _load(self.top_bar, "top")
        _load(self.editor_splitter, "editor")
        _load(self.main_splitter, "main")
        _load(self.console_splitter, "console")

    def _store_splitters(self) -> None:
        self._api.cfg.opt["gui"]["splitters"] = {
            "audio": bytes(self.audio.saveState()),
            "top": bytes(self.top_bar.saveState()),
            "editor": bytes(self.editor_splitter.saveState()),
            "main": bytes(self.main_splitter.saveState()),
            "console": bytes(self.console_splitter.saveState()),
        }

    def _restore_fonts(self) -> None:
        try:
            font_def = self._api.cfg.opt["gui"]["fonts"]["main"]
        except KeyError:
            return
        font = QtGui.QFont()
        font.fromString(font_def)
        self.setFont(font)

    def _store_fonts(self) -> None:
        self._api.cfg.opt["gui"]["fonts"]["main"] = self.font().toString()

    def _update_title(self) -> None:
        self.setWindowTitle(
            f"bubblesub - {self._api.subs.path}"
            if self._api.subs.path
            else "bubblesub"
        )
