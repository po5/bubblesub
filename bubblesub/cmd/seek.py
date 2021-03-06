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

import argparse

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.cmd.common import Pts


class SeekCommand(BaseCommand):
    names = ["seek"]
    help_text = "Changes the video playback position to desired place."

    @property
    def is_enabled(self) -> bool:
        return self.api.playback.is_ready

    async def run(self) -> None:
        pts = await self.args.pos.get(
            origin=self.api.playback.current_pts, align_to_near_frame=True
        )
        self.api.playback.seek(pts, self.args.precise)
        if self.args.pause is not None:
            self.api.playback.is_paused = self.args.pause

    @staticmethod
    def decorate_parser(api: Api, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-p",
            "--pos",
            help="where to seek",
            type=lambda value: Pts(api, value),
            required=True,
        )
        parser.add_argument(
            "--precise",
            help=(
                "whether to use precise seeking at the expense of performance"
            ),
            action="store_true",
        )
        parser.add_argument(
            "-P", "--pause", help="pause after seeking", action="store_true",
        )
        parser.add_argument(
            "-U",
            "--unpause",
            help="unpause after seeking",
            dest="pause",
            action="store_false",
        )


COMMANDS = [SeekCommand]
