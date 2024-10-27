# ruff: noqa

from pytest import raises
from scipath import Profile, create_cubic_path_2d
from scipath.cubic_path2d import ConsecutiveDuplicateError


def test_exception() -> None:
    invalid_waypoints = [(0, 0), (1, 1), (1, 1), (0, 1)]

    with raises(ConsecutiveDuplicateError):
        create_cubic_path_2d(invalid_waypoints, profile=Profile.ALL)