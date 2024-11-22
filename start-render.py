#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL


import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from audioCompare import audioCompare
from CompareResult import CompareResult, CompareResultStatus
from pnsr import pnsrCompare

# from compare_renders import compareRenders
from RenderProject import RenderProject
from ResultSummary import ResultSummary

# assign directory
projectFolder = "projects"
tmpFolder = os.path.join(".", "tmp")
outFolder = os.path.join(".", "renders")
refFolder = os.path.abspath("reference")

parser = argparse.ArgumentParser(
    description="Tooling for testing Kdenlive render functionality"
)

parser.add_argument("kdenlive_exec", nargs="?", default="kdenlive")
parser.add_argument(
    "-c",
    "--check-only",
    action="store_true",
    help="Skip rendering, only compare results",
)

args = parser.parse_args()


def setupFileStructure() -> bool:
    for folder in [tmpFolder, outFolder]:
        if not os.path.isdir(folder):
            os.mkdir(folder)

    if len(os.listdir(outFolder)) > 0:
        # If renders folder is not empty, ask if ok the clear it
        answer = input(
            "Render folder is not empty, files will be overwritten. Continue [Y/n] ?"
        )
        if not answer.lower() in ["y", "yes", ""]:
            # Abort
            return False

    return True


def renderKdenliveProject(project: RenderProject):
    outputFile = os.path.join(outFolder, project.renderFilename)

    # ensure destination render does not exists
    if os.path.isfile(outputFile):
        # delete previous render
        print(f"Clearing previous render: {outputFile}")
        os.remove(outputFile)

    print(
        f"Processing project: {project!s} to destination: {outputFile}",
        flush=True,
    )

    cmd = [args.kdenlive_exec]
    cmd += ["--render", str(project.projectPath)]

    if project.propRenderProfile:
        cmd += ["--render-preset", project.propRenderProfile]
    cmd += [outputFile]

    print("Starting command: ", cmd, flush=True)

    # ensure MLT's Qt module gets loaded by simulating a display
    my_env = os.environ.copy()
    if "DISPLAY" not in my_env:
        my_env["DISPLAY"] = ":0"

    result = subprocess.run(cmd, env=my_env, capture_output=True, text=True)

    project.renderLog = result.stdout
    project.renderErrorLog = result.stderr

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)

    print(
        f"Rendering project: {project!s}... DONE, return code {result.returncode}",
        flush=True,
    )


def openWebBrowser(filename):
    try:
        webbrowser.get("firefox").open(filename)
    except webbrowser.Error:
        print(f"Could not start Firefox... please open the {filename} file manually")


def compareRenders(projects: list[RenderProject]):
    results: list[tuple[RenderProject, CompareResult]] = []
    for project in projects:
        refFilePath = os.path.join(refFolder, project.renderFilename)

        # checking if it is a file
        if not os.path.isfile(refFilePath):
            continue

        # ensure destination render exists
        print(
            f"CHECKING FILE: {project.renderFilename}, ref: {refFilePath}",
            flush=True,
        )
        renderPath = os.path.join(outFolder, project.renderFilename)
        if not os.path.isfile(renderPath):
            results += [(project, CompareResult(CompareResultStatus.MISSING))]
            continue

        videoCompareResult = pnsrCompare(
            refFilePath, f"renders/{project.renderFilename}"
        )
        audioCompareResult = audioCompare(
            refFilePath, f"renders/{project.renderFilename}", project.propFps
        )

        compareResult = videoCompareResult + audioCompareResult

        results += [(project, compareResult)]

    return results


# ensure the folders exist
if not setupFileStructure():
    sys.exit()

projects = []

for filename in os.listdir(projectFolder):
    projectFile = Path(projectFolder) / filename

    # checking if it is a file
    if not projectFile.is_file():
        continue

    project = RenderProject(projectFile)
    if not args.check_only:
        renderKdenliveProject(project)
    projects += [project]

res = compareRenders(projects)

summary = ResultSummary(res, outFolder, refFolder)

summary.saveHtmlToFile(Path("result.html"))
summary.saveJUnitToFile(Path("JUnitRenderTestResults.xml"))

print(summary)

openWebBrowser("result.html")

# Compare the results with the references
if not summary.successful:
    sys.exit("Job failed")
else:
    print("JOB SUCCESSFUL", flush=True)
