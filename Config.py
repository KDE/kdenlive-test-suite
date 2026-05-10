# SPDX-FileCopyrightText: 2026 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

from enum import StrEnum, auto
from typing import Optional, TypedDict


class ExceptionType(StrEnum):
    ALLOW_TO_FAIL = "allow-to-fail"
    UNKNOWN = auto()


class AVType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"


class ExceptionConfig(TypedDict):
    type: ExceptionType
    reason: Optional[str]
    platforms: list[str]
    av_types: list[AVType]
    from_frame: int
    to_frame: int


class ProjectConfig(TypedDict):
    filename: str
    description: str
    exceptions: Optional[list[ExceptionConfig]]
