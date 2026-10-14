# SPDX-FileCopyrightText: 2026 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import json
from pathlib import Path
from typing import Optional, TypedDict, cast

from CompareResult import CompareResult, CompareResultStatus


class SetupComponent(TypedDict):
    name: str
    version: str


class SetupReportType(TypedDict):
    version: int
    components: list[SetupComponent]
    packageType: Optional[str]
    audioCodecs: list[str]
    videoCodecs: list[str]
    supportedFormats: list[str]
    enabledEffects: list[str]
    enabledTransitions: list[str]


class SetupReport:
    def __init__(self, reportFile: str):
        self.data: Optional[SetupReportType] = None

        if Path(reportFile).exists():
            with open(reportFile, mode="r", encoding="utf-8") as read_file:
                self.data = cast(SetupReportType, json.load(read_file))


def compareSetup(
    referenceSetupReport: SetupReport, testedSetupReport: SetupReport
) -> list[tuple[str, CompareResult]]:
    finalResults: list[tuple[str, CompareResult]] = []

    for category in [
        "enabledEffects",
        "enabledTransitions",
        "audioCodecs",
        "videoCodecs",
        "supportedFormats",
    ]:
        res = CompareResult(CompareResultStatus.SUCCESS)

        if not referenceSetupReport.data:
            res = CompareResult(CompareResultStatus.MISSING_REFERENCE)
            res.msg = "Missing setup reference"
            finalResults += [(category, res)]
            continue

        if not testedSetupReport.data:
            res = CompareResult(CompareResultStatus.MISSING_RENDER)
            finalResults += [(category, res)]
            continue

        reference = cast("list[str]", referenceSetupReport.data.get(category, []))
        testing = cast("list[str]", testedSetupReport.data.get(category, []))

        # Check for missing elements
        diff = list(set(reference) - set(testing))

        if diff:
            res = CompareResult(CompareResultStatus.CONTENT_COMPARE_FAILURE)
            res.details = (
                f"The following {category} are available in the reference,"
                f" but missing in the tested setup: {diff}"
            )

        # Check for additional elements
        diff = list(set(testing) - set(reference))

        if diff:
            if not res.details:
                res.details = ""
            res.details += (
                f"Note: The following {category} are not required according to the reference,"
                f" but are additionally available in the tested setup: {diff}"
            )

        finalResults += [(category, res)]

    return finalResults
