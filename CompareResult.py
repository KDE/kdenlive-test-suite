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

    def __str__(self):
        return f"Compare Result: {self.statusString}, {len(self.errors)} error(s), {self.message}"

    def __add__(self, other):
        status = CompareResultStatus.SUCCESS
        if self.status.value > other.status.value:
            status = self.status
        else:
            status = other.status

        sumRes = CompareResult(status)

        def _joinOptionalStr(a, b):
            if a:
                if b:
                    sumRes.msg = "; ".join([a, b])
                else:
                    return a
            else:
                return b

        sumRes.msg = _joinOptionalStr(self.msg, other.msg)
        sumRes.errorDetails = _joinOptionalStr(self.errorDetails, other.errorDetails)

        sumRes.errors = self.errors + other.errors
        sumRes.framesDuration = max(self.framesDuration, other.framesDuration)

        return sumRes

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
