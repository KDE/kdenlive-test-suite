# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

from enum import Enum
from typing import Optional


class CompareResultStatus(Enum):
    SUCCESS = 1
    MISSING = 2
    PROCESS_FAILURE = 3
    COMPARE_FAILURE = 4


class CompareResult:
    def __init__(self, status: CompareResultStatus, msg: Optional[str] = None):
        self.status = status
        self.msg = msg
        self.errorDetails: Optional[str] = None
        self.errors: list[tuple[int, int]] = []
        self.framesDuration = 0

    @property
    def message(self) -> str:
        if self.msg:
            return self.msg

        if self.status == CompareResultStatus.MISSING:
            return "missing render result"

        if self.status == CompareResultStatus.PROCESS_FAILURE:
            return "process failed"

        if self.status == CompareResultStatus.COMPARE_FAILURE:
            return "comparison failed"

        if self.status == CompareResultStatus.SUCCESS:
            return "success"

        return ""

    @property
    def statusString(self) -> str:
        if self.status == CompareResultStatus.MISSING:
            return "missing"

        if self.status == CompareResultStatus.PROCESS_FAILURE:
            return "error"

        if self.status == CompareResultStatus.COMPARE_FAILURE:
            return "error"

        if self.status == CompareResultStatus.SUCCESS:
            return "ok"

        return "error"
