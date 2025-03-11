# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy

from CompareResult import CompareResult, CompareResultStatus

ffmpegCommand = os.environ.get("TEST_FFMPEG_CMD", "ffmpeg").split()


def get_audio_data(fileName):
    with tempfile.TemporaryDirectory() as tmpdirname:
        fileName = convert_to_wav(fileName, tmpdirname)

        with wave.open(str(fileName), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            byted = wav_file.getsampwidth()

            dtype = numpy.int8
            if byted == 1:
                dtype = numpy.int8
            elif byted == 2:
                dtype = numpy.int16
            elif byted == 4:
                dtype = numpy.int32
            elif byted == 8:
                dtype = numpy.int64

            return (
                numpy.frombuffer(frames, dtype=dtype),
                wav_file.getframerate(),
                byted,
                wav_file.getnchannels(),
            )


def convert_to_wav(sourceFile, taregetDir, target_rate=44100) -> Path:
    stem = Path(sourceFile).stem
    targetFile = Path(taregetDir) / f"{stem}_{target_rate}Hz_converted.wav"
    cmd = ffmpegCommand + [
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",  # overwrite output files
        "-i",
        sourceFile,
        "-ar",
        str(target_rate),
        targetFile,
        "-y",
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    if result.returncode != 0:
        raise Exception("Converting to wav file with ffmpeg failed")

    return targetFile


def audioCompare(referenceFile, lastRender, fps=25) -> CompareResult:
    try:
        data1, rate1, sampWidth1, ch1 = get_audio_data(referenceFile)
        data2, rate2, sampWidth2, ch2 = get_audio_data(lastRender)
    except Exception as err:
        res = CompareResult(CompareResultStatus.PROCESS_FAILURE)
        res.errorDetails = str(err)
        return res

    if rate1 != rate2:
        return CompareResult(
            CompareResultStatus.COMPARE_FAILURE,
            f"sample rate differes {rate1} vs. {rate2}",
        )

    samples_per_frame = int(rate1 / 25)

    num_windows = int(min(len(data1), len(data2)) // samples_per_frame)

    def samples_to_frames(sample):
        return int((sample / sampWidth1) / samples_per_frame)

    firstFrame = -1
    errorArray: list[tuple[int, int]] = []
    firstErrorFrame = -1
    framesDuration = 0

    for i in range(num_windows):
        start = i * samples_per_frame
        end = start + samples_per_frame

        # Extrahiere die Audiodaten des aktuellen Fensters
        window1 = data1[start:end]
        window2 = data2[start:end]

        mean = abs(numpy.mean((window1 - window2) ** 2))
        rms_diff = numpy.sqrt(mean)

        if rms_diff > 0.2:
            frame = samples_to_frames(start)

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

    errorMsg: list[str] = []
    if ch1 != ch2:
        errorMsg += [f"channel count differes: {ch1} vs. {ch2}"]

    if len(errorArray) > 0 or len(errorMsg) > 0:
        errorMsg += [f"frame {firstErrorFrame}"]
        res = CompareResult(
            CompareResultStatus.COMPARE_FAILURE,
            ", ".join(errorMsg),
        )
        res.audioErrors = errorArray
        res.framesDuration = framesDuration

        return res

    else:
        # job succeded
        return CompareResult(CompareResultStatus.SUCCESS)
