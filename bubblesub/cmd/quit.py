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

import bubblesub.api
from bubblesub.api.cmd import BaseCommand


class QuitCommand(BaseCommand):
    names = ['quit']
    help_text = (
        'Quits the application. '
        'Prompts user to save the current file if there are unsaved changes.'
    )

    async def run(self) -> None:
        self.api.gui.quit()


def register(cmd_api: bubblesub.api.cmd.CommandApi) -> None:
    cmd_api.register_core_command(QuitCommand)
