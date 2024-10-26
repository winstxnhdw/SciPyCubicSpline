from __future__ import annotations

from collections.abc import Sequence
from enum import IntEnum
from typing import Any, Generic, Literal, NamedTuple, TypeVar, overload

from numpy import arange, arctan2, concatenate, cumsum, diff, floating, zeros
from numpy.linalg import norm
from numpy.typing import NDArray
from scipy.interpolate import CubicSpline

type FloatArray = NDArray[floating[Any]]

P_contra = TypeVar("P_contra", bound=FloatArray | None, contravariant=True)
Y_contra = TypeVar("Y_contra", bound=FloatArray | None, contravariant=True)
C_contra = TypeVar("C_contra", bound=FloatArray | None, contravariant=True)


class ConsecutiveDuplicateError(Exception):
    def __init__(self) -> None:
        super().__init__("Your input should not contain consecutive duplicate(s)!")


class CubicPath2D(Generic[P_contra, Y_contra, C_contra], NamedTuple):
    path: P_contra
    yaw: Y_contra
    curvature: C_contra


class Profile(IntEnum):
    PATH = 0x001
    YAW = 0x010
    CURVATURE = 0x100
    NO_CURVATURE = 0x011
    NO_YAW = 0x101
    NO_PATH = 0x110
    ALL = 0x111


@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.PATH] = Profile.PATH,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray, FloatArray | None, FloatArray | None]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.YAW] = Profile.YAW,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray | None, FloatArray, FloatArray | None]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.CURVATURE] = Profile.CURVATURE,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray | None, FloatArray | None, FloatArray]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.NO_CURVATURE] = Profile.NO_CURVATURE,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray, FloatArray, FloatArray | None]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.NO_YAW] = Profile.NO_YAW,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray, FloatArray | None, FloatArray]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.NO_PATH] = Profile.NO_PATH,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray | None, FloatArray, FloatArray]: ...
@overload
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Literal[Profile.ALL] = Profile.ALL,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray, FloatArray, FloatArray]: ...
def create_cubic_path_2d(
    points: NDArray[floating[Any]] | Sequence[tuple[float, float]],
    *,
    profile: Profile = Profile.ALL,
    distance_step: float = 0.05,
    boundary_condition_type: str = "natural",
) -> CubicPath2D[FloatArray, FloatArray, FloatArray]:
    path = None
    yaw = None
    curvature = None
    dx = None
    dy = None
    norms = concatenate((zeros(1), cumsum(norm(diff(points, axis=0), axis=1))))
    steps = arange(0, norms[-1], distance_step)

    try:
        cubic_spline = CubicSpline(norms, points, bc_type=boundary_condition_type, axis=0, extrapolate=False)

    except ValueError as error:
        if diff(points, axis=1).all():
            raise

        raise ConsecutiveDuplicateError from error

    if profile & Profile.PATH:
        path = cubic_spline(steps)

    if profile & Profile.YAW:
        first_derivative = cubic_spline.derivative(1)
        dx, dy = first_derivative(steps).T
        yaw = arctan2(dy, dx)  # pyright: ignore [reportUnknownArgumentType]

    if profile & Profile.CURVATURE:
        second_derivative = cubic_spline.derivative(2)
        dx, dy = (dx, dy) if dx and dy else cubic_spline.derivative(1)(steps).T
        ddx, ddy = second_derivative(steps).T
        curvature = (dx * ddy - dy * ddx) / (dx * dx + dy * dy) ** 1.5

    return CubicPath2D(path, yaw, curvature)