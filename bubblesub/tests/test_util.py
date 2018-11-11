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

import typing as T

import pytest

import bubblesub.util


@pytest.mark.parametrize(
    "indexes,reverse,expected_ranges",
    [
        ([1], False, [(1, 1)]),
        ([1, 2], False, [(1, 2)]),
        ([1, 2, 3], False, [(1, 3)]),
        ([1, 3], False, [(1, 1), (3, 1)]),
        ([1, 2, 3, 5], False, [(1, 3), (5, 1)]),
        ([1, 2, 3, 5, 6], False, [(1, 3), (5, 2)]),
        ([1, 2, 3, 5, 6, 8], False, [(1, 3), (5, 2), (8, 1)]),
        ([5, 6, 8, 1, 2, 3], False, [(1, 3), (5, 2), (8, 1)]),
        ([1], True, [(1, 1)]),
        ([1, 2], True, [(1, 2)]),
        ([1, 2, 3], True, [(1, 3)]),
        ([1, 3], True, [(3, 1), (1, 1)]),
        ([1, 2, 3, 5], True, [(5, 1), (1, 3)]),
        ([1, 2, 3, 5, 6], True, [(5, 2), (1, 3)]),
        ([1, 2, 3, 5, 6, 8], True, [(8, 1), (5, 2), (1, 3)]),
        ([5, 6, 8, 1, 2, 3], True, [(8, 1), (5, 2), (1, 3)]),
    ],
)
def test_make_ranges(
    indexes: T.Iterable[int],
    reverse: bool,
    expected_ranges: T.List[T.Tuple[int, int]],
) -> None:
    actual_ranges = list(bubblesub.util.make_ranges(indexes, reverse=reverse))
    assert actual_ranges == expected_ranges
