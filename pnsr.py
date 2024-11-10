# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import subprocess

from CompareResult import CompareResult, CompareResultStatus

ffmpegCommand = os.environ.get("TEST_FFMPEG_CMD", "ffmpeg").split()


def pnsrCompare(referenceFile, lastRender) -> CompareResult:
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
    framesDuration = 0

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

        framesDuration += 1

    if firstFrame >= 0:
        errorArray += [(firstFrame, frame)]

    if len(errorArray) > 0:
        res = CompareResult(
            CompareResultStatus.COMPARE_FAILURE,
            f"frame {firstErrorFrame}, PNSR: {maxPnsrValue:.3f}",
        )
        res.videoErrors = errorArray
        res.framesDuration = framesDuration

        return res

    else:
        # job succeded
        return CompareResult(CompareResultStatus.SUCCESS)
