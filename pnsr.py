# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import subprocess
from enum import Enum
from typing import Optional

ffmpegCommand = os.environ.get("TEST_FFMPEG_CMD", "ffmpeg").split()


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
        self.framesCount = 0

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


def psnrCompare(referenceFile, lastRender, testIndex) -> CompareResult:
    cmd = ffmpegCommand + [
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        referenceFile,
        "-i",
        lastRender,
        "-filter_complex",
        "psnr=f=-",
        "-f",
        "null",
        "/dev/null",
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    # Check if process failed
    if result.returncode != 0:
        res = CompareResult(CompareResultStatus.PROCESS_FAILURE)
        res.errorDetails = result.stderr
        return res

    firstFrame = -1
    firstErrorFrame = -1
    errorArray: list[tuple[int, int]] = []
    maxPnsrValue = 0.0
    threshold = 10
    frame = 0
    framesCount = 0

    for line in result.stdout.split("\n"):
        # Example line:
        # n:1 mse_avg:0.00 mse_y:0.00 mse_u:0.00 mse_v:0.00 psnr_avg:inf psnr_y:inf psnr_u:inf psnr_v:inf

        values = line.split()
        if len(values) < 2:
            continue

        frame = int(values[0].split(":")[1])
        mse_avg = float(values[1].split(":")[1])

        if mse_avg > threshold:
            maxPnsrValue = max(mse_avg, maxPnsrValue)
            if firstFrame < 0:
                firstFrame = frame

            if firstErrorFrame < 0:
                firstErrorFrame = frame
        else:
            if firstFrame >= 0:
                errorArray += [(firstFrame, frame)]
                firstFrame = -1

        framesCount += 1

    if firstFrame >= 0:
        errorArray += [(firstFrame, frame)]

    if len(errorArray) > 0:
        res = CompareResult(
            CompareResultStatus.COMPARE_FAILURE,
            f"frame {firstErrorFrame}, PNSR: {maxPnsrValue:.3f}",
        )
        res.errors = errorArray
        res.framesCount = framesCount

        return res

    else:
        # job succeded
        return CompareResult(CompareResultStatus.SUCCESS)
