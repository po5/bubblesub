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

"""General GUI commands."""

import argparse
import enum

from PyQt5 import QtWidgets

import bubblesub.api
from bubblesub.api.cmd import BaseCommand


class TargetWidget(enum.Enum):
    """Known widgets in GUI."""

    def __str__(self):
        return self.value

    TextEditor = 'text-editor'
    NoteEditor = 'note-editor'
    StyleEditor = 'style-editor'
    ActorEditor = 'actor-editor'
    LayerEditor = 'layer-editor'
    MarginLeftEditor = 'margin-left-editor'
    MarginRightEditor = 'margin-right-editor'
    MarginVerticalEditor = 'margin-vertical-editor'
    StartTimeEditor = 'start-time-editor'
    EndTimeEditor = 'end-time-editor'
    DurationEditor = 'duration-editor'
    CommentCheckbox = 'comment-checkbox'
    SubtitlesGrid = 'subtitles-grid'
    Spectrogram = 'spectrogram'
    Console = 'console'
    ConsoleInput = 'console-input'


class SetPaletteCommand(BaseCommand):
    names = ['set-palette']
    help_text = 'Changes the GUI color theme.'

    @property
    def menu_name(self) -> str:
        return '&Switch to {} color scheme'.format(self.args.palette_name)

    async def run(self) -> None:
        await self.api.gui.exec(self._run_with_gui)

    async def _run_with_gui(self, main_window: QtWidgets.QMainWindow) -> None:
        main_window.apply_palette(self.args.palette_name)

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'palette_name',
            help='name of the palette to change to',
            type=str,
            choices=list(api.opt.general.gui.palettes.keys())
        )


class FocusWidgetCommand(BaseCommand):
    names = ['focus-widget']
    help_text = 'Focuses the target widget.'

    async def run(self) -> None:
        await self.api.gui.exec(self._run_with_gui)

    @property
    def menu_name(self) -> str:
        widget_name = {
            TargetWidget.TextEditor: 'text editor',
            TargetWidget.NoteEditor: 'note editor',
            TargetWidget.StyleEditor: 'style editor',
            TargetWidget.ActorEditor: 'actor editor',
            TargetWidget.LayerEditor: 'layer editor',
            TargetWidget.MarginLeftEditor: 'left margin editor',
            TargetWidget.MarginRightEditor: 'right margin editor',
            TargetWidget.MarginVerticalEditor: 'vertical margin editor',
            TargetWidget.StartTimeEditor: 'start time editor',
            TargetWidget.EndTimeEditor: 'end time editor',
            TargetWidget.DurationEditor: 'duration editor',
            TargetWidget.CommentCheckbox: 'comment checkbox',
            TargetWidget.SubtitlesGrid: 'subtitles grid',
            TargetWidget.Spectrogram: 'spectrogram',
            TargetWidget.Console: 'console',
            TargetWidget.ConsoleInput: 'console prompt'
        }[self.args.target]
        return '&Focus ' + widget_name

    async def _run_with_gui(self, main_window: QtWidgets.QMainWindow) -> None:
        widget = main_window.findChild(
            QtWidgets.QWidget, str(self.args.target)
        )
        widget.setFocus()
        if self.args.select:
            widget.selectAll()

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'target',
            help='which widget to focus',
            type=TargetWidget,
            choices=list(TargetWidget)
        )
        parser.add_argument(
            '-s', '--select',
            help='whether to select the text',
            action='store_true'
        )


def register(cmd_api: bubblesub.api.cmd.CommandApi) -> None:
    """
    Register commands in this file into the command API.

    :param cmd_api: command API
    """
    cmd_api.register_core_command(SetPaletteCommand)
    cmd_api.register_core_command(FocusWidgetCommand)
