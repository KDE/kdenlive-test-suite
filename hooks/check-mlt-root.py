#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import argparse
import os
import re
import sys
from pathlib import Path
from xml.dom.minidom import parse
from xml.parsers import expat


def valid_path(path: str) -> Path:
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Path does not exist: {path}")
    return Path(path).resolve()


parser = argparse.ArgumentParser(
    description="Hook to check if the MLT root of Kdenlive projects is empty"
)

parser.add_argument(
    "--fix",
    action="store_true",
    help="Clear non-empty attributes",
)

parser.add_argument("paths", metavar="PATH", nargs="+", type=valid_path)

args = parser.parse_args()


def getAllProjectFiles(projectsDir: Path) -> list[Path]:
    return [
        (projectsDir / f) for f in os.listdir(projectsDir) if f.endswith(".kdenlive")
    ]


def clearMltRoot(projectFile: Path) -> None:
    print(f"Fixing {projectFile.name}...")
    try:
        with open(projectFile, "r", encoding="utf-8") as f:
            content = f.read()

        # Only modify the root attribute of <mlt>
        newContent, subCount = re.subn(
            r'(<mlt\s+[^>]*root\s*=\s*)"[^"]*"', r'\1""', content, flags=re.MULTILINE
        )

        if subCount > 0:
            with open(projectFile, "w", encoding="utf-8") as f:
                f.write(newContent)
            print("...done")
        else:
            print("...already clean")

    except Exception as e:
        print(f"ERROR: {projectFile} - {e}")


def checkMltRoot(projectFile: Path, fix: bool = False) -> bool:
    try:
        document = parse(str(projectFile))
        mlt = document.getElementsByTagName("mlt")[0]

        mltRoot = mlt.getAttribute("root")
    except expat.ExpatError as e:
        print(f"ERROR: {projectFile} is not a valid Kdenlive project file: {e}")
        return False

    if mltRoot:
        print(f"{projectFile.name} - root is not empty: {mltRoot}")

        if fix:
            clearMltRoot(projectFile)

        return False

    print(f"{projectFile.name} - ok")
    return True


kdenliveFiles = []

for path in args.paths:
    if path.is_dir():
        kdenliveFiles += getAllProjectFiles(path)
    else:
        kdenliveFiles += [path]

if not kdenliveFiles:
    print("No Project files found.")
    sys.exit()

wrongFiles = []
for xmlFile in kdenliveFiles:
    if not checkMltRoot(xmlFile, args.fix):
        wrongFiles += [xmlFile]

if wrongFiles:
    sys.exit("-> Some Kdenlive files have non-empty 'root' attributes in <mlt>.")
