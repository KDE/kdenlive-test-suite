# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import json
import os
import subprocess
import typing

from CompareResult import CompareResult, CompareResultStatus

ffprobeCommand = os.environ.get("TEST_FFPROBE_CMD", "ffprobe").split()


class Metadata:
    def __init__(self, mediaFile: str):
        self._data = self._readStreamMetadata(mediaFile)
        self._mediaFile = mediaFile

    def __str__(self) -> str:
        return f"""Metadata for {self._mediaFile}:
        {len(self.audioStreams)} audio stream(s),
        {len(self.videoStreams)} video stream(s)
        """

    def _readStreamMetadata(self, mediaFile: str) -> typing.Any:
        cmd = ffprobeCommand + [
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            mediaFile,
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        # Check if process failed
        if result.returncode != 0:
            print(
                f"Reading metadata with ffprobe failed. Command:\n{cmd}\nOutput to stderr:\n{result.stderr}"
            )
            raise Exception("Reading metadata with ffprobe failed.")

        return json.loads(result.stdout)

    @property
    def audioStreams(self) -> list[typing.Any]:
        return [
            s for s in self._data.get("streams", []) if s.get("codec_type") == "audio"
        ]

    @property
    def videoStreams(self) -> list[typing.Any]:
        return [
            s for s in self._data.get("streams", []) if s.get("codec_type") == "video"
        ]


def compareMetadata(
    referenceMetadata: Metadata, lastRenderMetadata: Metadata
) -> CompareResult:
    results = []

    if len(referenceMetadata.audioStreams) != len(lastRenderMetadata.audioStreams):
        res = CompareResult(CompareResultStatus.METADATA_COMPARE_FAILURE)
        res.errorDetails = (
            "Different number of audio streams"
            f" ({len(referenceMetadata.audioStreams)} vs. {len(lastRenderMetadata.audioStreams)})"
        )
        results += [res]

    if len(referenceMetadata.videoStreams) != len(lastRenderMetadata.videoStreams):
        res = CompareResult(CompareResultStatus.METADATA_COMPARE_FAILURE)
        res.errorDetails = (
            "Different number of video streams"
            f"({len(referenceMetadata.audioStreams)} vs. {len(lastRenderMetadata.audioStreams)})"
        )
        results += [res]

    finalResult = CompareResult(CompareResultStatus.SUCCESS)

    for r in results:
        finalResult += r

    return finalResult
