# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.dom.minidom import Document

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from CompareResult import CompareResult, CompareResultStatus
from RenderProject import RenderProject
from SetupReport import SetupReport

# class ProjectResult():
#     def __init__(self):
ffmpegCommand = os.environ.get("TEST_FFMPEG_CMD", "ffmpeg").split()


class ResultSummary:
    freeMonoFontFile = Path(__file__).parent / "fonts/freemono/FreeMono.ttf"
    cssStyle = """
    body {
        font-family: arial;
    }

    .wrap-collabsible {
        margin-bottom: 1rem 0;
    }

    input[type='checkbox'] {
        display: none;
    }

    .lbl-toggle {
        display: block;
        font-weight: normal;
        font-family: monospace;
        font-size: 1rem;
        text-align: left;
        vertical-align: middle;
        padding: 0.2rem;
        background: #FFFFFF;
        cursor: arrow;
        border-bottom: 1px solid #999999;
        transition: all 0.25s ease-out;
    }

    .lbl-toggle-skipped {
        color: #666666;
        background: #FFFFFF;
    }

    .lbl-toogle-exists.lbl-toggle-skipped:hover {
        color: #313131;
        background: #FFFFFF;
    }

    .lbl-toggle-ok{
        color: #006600;
    }

    .lbl-toogle-exists.lbl-toggle-ok:hover{
        color: #4dad46;
    }

    .lbl-toggle-warning{
        color: #FF7700;
    }

    .lbl-toogle-exists.lbl-toggle-warning:hover{
        color: #ffAA00;
    }

    .lbl-toggle-missing,
    .lbl-toggle-error{
        color: #660000;
    }

    .lbl-toogle-exists.lbl-toggle-missing:hover,
    .lbl-toogle-exists.lbl-toggle-error:hover{
        color: #FF6666;
    }

    .collapsible-content {
        max-height: 0px;
        overflow: hidden;
        transition: max-height .25s ease-in-out;
    }

    .toggle:checked+.lbl-toggle+.collapsible-content {
        max-height: 100vh;
    }

    .toggle:checked+.lbl-toggle {
        border-bottom-right-radius: 0;
        border-bottom-left-radius: 0;
    }

    .collapsible-content .content-inner {
        background: rgba(250, 224, 66, .2);
        border-bottom: 1px solid rgba(250, 224, 66, .45);
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        padding: .5rem 1rem;
    }

    div.centered {
        vertical-align: middle;
    }

    .split {
        height: 100%;
        width: 50%;
        position: fixed;
        z-index: 1;
        top: 0;
        overflow-x: hidden;
        padding-top: 20px;
    }

    .left {
        left: 0;
        padding:5px;
        background-color: #FFFFFF;
    }

    .right {
        right: 0;
        background-color: #CCCCCC;
    }

    .rightcentered {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }
    """

    def __init__(
        self,
        setupReport: SetupReport,
        setupResults: list[tuple[str, CompareResult]],
        projectResults: list[tuple[RenderProject, CompareResult]],
        renderFolder: str,
        referenceFolder: str,
    ):
        self.setupReport = setupReport
        self.setupResults = setupResults
        self.projectResults = projectResults
        self.renderFolder = renderFolder
        self.referenceFolder = referenceFolder
        self._tempFiles: list[Path] = []

    def _celanupTempFile(self) -> None:
        for filePath in self._tempFiles:
            filePath.unlink(missing_ok=True)
        self._tempFiles = []

    @staticmethod
    def _getFps(filename: Path) -> float:
        fps = 25.0
        cmd3 = ffmpegCommand + ["-hide_banner", "-i", str(filename)]
        proc3 = subprocess.Popen(
            cmd3,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
        )

        if not proc3.stderr:
            return fps

        for line in proc3.stderr:
            linestr = line.strip()
            if "Stream #" in linestr and "Video:" in linestr:
                # match
                vals = linestr.split(",")
                for v in vals:
                    if " tbr" in v:
                        fps = float(v.split(" ")[1])
                        break
        proc3.wait()
        return fps

    def _extractFrameToImage(
        self, videoFile: Path, frame: int, fps: float
    ) -> Image.Image:
        imageFile = f"tmp/{time.time()}.png"
        self._tempFiles += [Path(imageFile)]
        cmd = ffmpegCommand + [
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            str(frame / fps),
            "-i",
            str(videoFile),
            "-frames:v",
            "1",
            imageFile,
        ]
        subprocess.call(cmd)
        if Path(imageFile).is_file():
            return Image.open(imageFile)
        else:
            resultImage = Image.new(mode="RGB", size=(800, 450))
            myFont = ImageFont.truetype(str(self.freeMonoFontFile), 48)
            I1 = ImageDraw.Draw(resultImage)
            I1.text(
                (10, 2),
                "Could not create thumbnail",
                font=myFont,
                fill="white",
                stroke_width=2,
                stroke_fill="white",
            )
            return resultImage

    def _constructComparisonImage(
        self,
        referenceVideoFile: Path,
        renderVideoFile: Path,
        frame: int,
        fps: float,
        errors: list[tuple[int, int]],
        length: int,
    ) -> Image.Image:
        borderWidth = 10

        img1 = self._extractFrameToImage(referenceVideoFile, frame, fps)
        img2 = self._extractFrameToImage(renderVideoFile, frame, fps)

        diff = ImageChops.difference(img1, img2)

        images = [img1, img2]

        widths, heights = zip(*(i.size for i in images))

        total_width = sum(widths) + 4 * borderWidth
        max_height = max(heights) + 2 * borderWidth
        timelineHeight = int(max_height / 6)
        # Results text
        resultImage = Image.new("RGB", (total_width, timelineHeight))
        I1 = ImageDraw.Draw(resultImage)
        textHeight = int(timelineHeight / 3)
        resultImage.paste("red", (0, 0, total_width, textHeight + borderWidth))
        myFont = ImageFont.truetype(str(self.freeMonoFontFile), textHeight)
        I1.text(
            (10, 2),
            f"Reference: {referenceVideoFile.name}",
            font=myFont,
            fill="white",
            stroke_width=2,
            stroke_fill="white",
        )
        I1.text(
            (total_width / 2 + 10, 2),
            f"Last render: {renderVideoFile}",
            font=myFont,
            fill="white",
            stroke_width=2,
            stroke_fill="white",
        )
        I1.text(
            (10, timelineHeight / 2 + 10),
            f"Error at frame : {frame}",
            font=myFont,
            fill="yellow",
            stroke_width=2,
            stroke_fill="yellow",
        )

        # timeline of ok and incorrect segments
        timeline = Image.new("RGB", (total_width, timelineHeight))
        I2 = ImageDraw.Draw(timeline)
        timeline.paste("darkgreen", (0, 0, timeline.size[0], timeline.size[1]))

        for segment in errors:
            shape = (
                (total_width * segment[0] / length, 0),
                (total_width * segment[1] / length, timelineHeight),
            )
            I2.rectangle(shape, fill="orange")

        shape = (
            (total_width * frame / length, 0),
            (total_width * frame / length + borderWidth, timelineHeight),
        )
        I2.rectangle(shape, fill="darkred")

        diffWidth, diffHeight = diff.size
        diff = diff.resize((diffWidth * 2, diffHeight * 2))
        diffWidth, diffHeight = diff.size

        diff = ImageOps.expand(diff, border=borderWidth * 2, fill="red")

        new_im = Image.new(
            "RGB", (total_width, diffHeight + max_height + (2 * timelineHeight))
        )
        new_im.paste(diff, (0, 0))
        new_im.paste(timeline, (0, diffHeight + max_height + timelineHeight))
        new_im.paste(resultImage, (0, diffHeight + max_height))
        x_offset = 0
        for im in images:
            img = ImageOps.expand(im, border=borderWidth, fill="red")
            new_im.paste(img, (x_offset, diffHeight))
            x_offset += im.size[0] + 2 * borderWidth

        self._celanupTempFile()

        return new_im

    def __str__(self) -> str:
        string = ["==== SUMMARY ===="]
        for setupRes in self.setupResults:
            category, result = setupRes

            string += [f"{result.statusString}\t - setup.{category}"]

        for projectRes in self.projectResults:
            project, result = projectRes
            failureAllowed = project.isFailureAllowed(
                result.videoErrors, result.audioErrors
            )
            suffix = " (FAILURE ALLOWED)" if failureAllowed else ""
            string += [f"{result.statusString}\t - {project.name}{suffix}"]

        return "\n".join(string)

    def _setupItemHtml(self, item: tuple[str, CompareResult], index: int) -> str:
        category, result = item
        collapsible = ""

        if result.details:
            collapsible += f"<p>{result.details}</p>"

        icon = "emblem-error.svg"

        if result.statusString == "ok":
            icon = "emblem-checked.svg"
        elif result.statusString == "skipped":
            icon = "emblem-skipped.svg"

        collapsibleClass = "lbl-toogle-exists" if collapsible else ""
        html = f"""
        <input id="collapsible-setup{index}" class="toggle" type="checkbox">
        <label for="collapsible-setup{index}" class="lbl-toggle lbl-toggle-{result.statusString} {collapsibleClass}">
            <div class="centered">
                <img src="resources/{icon}" />
                Comparing <b>{category}</b>: {result.message}. {'[Click for Details]' if collapsible else ''}
            </div>
        </label>
        """

        if collapsible:
            html += f"""
            <div class="collapsible-content">
                <div class="content-inner">
                    {collapsible}
                </div>
            </div>
            """

        return html

    def _projectItemHtml(
        self, item: tuple[RenderProject, CompareResult], index: int
    ) -> str:
        project, result = item
        collapsible = ""

        failureAllowed = project.isFailureAllowed(
            result.videoErrors, result.audioErrors
        )

        if project.description:
            collapsible += project.description + "</br>"

        if result.status == CompareResultStatus.CONTENT_COMPARE_FAILURE:
            referenceVideo = Path(self.referenceFolder) / project.renderFilename
            fps = self._getFps(referenceVideo)
            renderVideo = Path(self.renderFolder) / project.renderFilename

            collapsible += "<b>Broken video frames: </b>"
            if not result.videoErrors:
                collapsible += "None"
            for frameRange in result.videoErrors:
                errorPos = frameRange[0] - 1

                comparisonImage = self._constructComparisonImage(
                    referenceVideo,
                    renderVideo,
                    errorPos,
                    fps,
                    result.videoErrors,
                    result.framesDuration,
                )
                imageName = f"tmp/{index}-{errorPos}-result.png"
                comparisonImage.save(imageName)

                collapsible += f"""
                <a href="javascript:void(0)" onclick="toggleImg0('{imageName}')">
                    {errorPos}
                </a>
                """

                if frameRange[1] - frameRange[0] < 2:
                    collapsible += " | "
                else:
                    collapsible += "-"
                    # Second image
                    errorPos = frameRange[1] - 1

                    comparisonImage = self._constructComparisonImage(
                        referenceVideo,
                        renderVideo,
                        errorPos,
                        fps,
                        result.videoErrors,
                        result.framesDuration,
                    )
                    imageName = f"tmp/{index}-{errorPos}-result.png"
                    comparisonImage.save(imageName)

                    collapsible += f"""
                    <a href="javascript:void(0)" onclick="toggleImg0('{imageName}')">
                        {errorPos}
                    </a> |
                    """

            collapsible += "</br><b>Broken audio frames: </b>"
            if not result.audioErrors:
                collapsible += "None"

            for frameRange in result.audioErrors:
                errorPos = frameRange[0] - 1

                collapsible += f"{errorPos}"

                if frameRange[1] - frameRange[0] < 2:
                    collapsible += " | "
                else:
                    collapsible += "-"
                    # Second image
                    errorPos = frameRange[1] - 1

                    collapsible += f"{errorPos} | "

        status = result.statusString
        if failureAllowed:
            status = "warning"

        icon = "emblem-error.svg"
        if status == "ok" or failureAllowed:
            icon = "emblem-checked.svg"
        elif status == "skipped":
            icon = "emblem-skipped.svg"

        if result.details:
            collapsible += f"<p>{result.details}</p>"

        if failureAllowed:
            collapsible += "<p><b>Note:</b> This test is allowed to fail.</p>"

        collapsibleClass = "lbl-toogle-exists" if collapsible else ""
        html = f"""
        <input id="collapsible{index}" class="toggle" type="checkbox">
        <label for="collapsible{index}" class="lbl-toggle lbl-toggle-{status} {collapsibleClass}">
            <div class="centered">
                <img src="resources/{icon}" />
                Test #{index} for file <b>{project.renderFilename}</b>: {result.message}.
                {'[Click for Details]' if collapsible else ''}
            </div>
        </label>
        """

        if collapsible:
            html += f"""
            <div class="collapsible-content">
                <div class="content-inner">
                    {collapsible}
                </div>
            </div>
            """

        return html

    def toHtml(self) -> str:
        print("Creating HTML")

        components = "No components info"
        if self.setupReport.data:
            components = ""

            packageType = self.setupReport.data.get("packageType")
            if packageType:
                components += f"Packaging: {self.setupReport.data.get('packageType')}"

            componentsData = self.setupReport.data.get("components")
            if componentsData:
                componentList: list[str] = []
                for item in componentsData:
                    componentList += [
                        f"<li>{item.get('name')}: {item.get('version')}</li>"
                    ]

                if componentList:
                    components += "<ul>" + "".join(componentList) + "</ul>"

        setupBody = ""
        size = len(self.projectResults)
        for ix, setupRes in enumerate(self.setupResults):
            print(f"Processing setup result {ix + 1} of {size}", end="\r")
            setupBody += self._setupItemHtml(setupRes, ix + 1)

        projectsBody = ""
        size = len(self.projectResults)
        for ix, projectRes in enumerate(self.projectResults):
            print(f"Processing project result {ix + 1} of {size}", end="\r")
            projectsBody += self._projectItemHtml(projectRes, ix + 1)
        print()

        cijobName = os.environ.get("CI_JOB_NAME", "Tests")

        return f"""
        <!DOCTYPE html>
            <head>
                <style>
                    {self.cssStyle}
                </style>
                <script>
                    function toggleImg0(charName) {{document.getElementById("thumb").src = charName ;}}
                </script>
            </head>
            <body>
                <div class="wrap-collabsible">
                    <div class="split right">
                        <img class="rightcentered" width="98%" src="" id="thumb">
                    </div>
                    <div class="split left">
                        <h1>{cijobName} done on {datetime.now().ctime()}<h1>

                        <h2>Setup</h2>
                        <p>{components}</p>
                        {setupBody}
                        <h2>Projects</h2>
                        {projectsBody}
                    </div>
                </div>
            </body>
        </html>
        """

    def saveJUnitToFile(self, outputFile: Path) -> None:
        root = Document()
        root.toprettyxml(encoding="utf-8")

        suites = root.createElement("testsuites")
        root.appendChild(suites)

        suite = root.createElement("testsuite")
        suites.appendChild(suite)

        failed_count = 0
        error_count = 0

        for setupRes in self.setupResults:
            category, result = setupRes

            case = root.createElement("testcase")
            case.setAttribute("classname", f"setup.{category}")
            case.setAttribute("name", category)
            case.setAttribute("time", "0.00")
            suite.appendChild(case)

            if result.status == CompareResultStatus.CONTENT_COMPARE_FAILURE:
                failure = root.createElement("failure")
                failure.setAttribute("message", result.message)
                case.appendChild(failure)
                failed_count += 1

                failure_details = root.createTextNode(
                    result.details if result.details else result.message
                )
                failure.appendChild(failure_details)

            elif result.status != CompareResultStatus.SUCCESS:
                error = root.createElement("error")
                error.setAttribute("message", result.message)
                case.appendChild(error)
                error_count += 1

                error_details = root.createTextNode(
                    result.details if result.details else result.message
                )
                error.appendChild(error_details)

        for projectRes in self.projectResults:
            project, result = projectRes

            case = root.createElement("testcase")
            case.setAttribute("classname", f"project.{project.name}")
            case.setAttribute("name", project.name)
            case.setAttribute("time", "0.00")
            suite.appendChild(case)

            if result.status == CompareResultStatus.CONTENT_COMPARE_FAILURE:
                failure = root.createElement("failure")
                failure.setAttribute("message", result.message)
                case.appendChild(failure)
                failed_count += 1

                message = "Video comparison failed in the following ranges:"
                if not result.videoErrors:
                    message += " None"
                for frameRange in result.videoErrors:
                    message += f"\n - frame {frameRange[0]} - {frameRange[1]}"
                message += "\nAudio comparison failed in the following ranges:"
                if not result.audioErrors:
                    message += " None"
                for frameRange in result.audioErrors:
                    message += f"\n - frame {frameRange[0]} - {frameRange[1]}"
                failure_details = root.createTextNode(message)
                failure.appendChild(failure_details)

            elif result.status != CompareResultStatus.SUCCESS:
                error = root.createElement("error")
                error.setAttribute("message", result.message)
                case.appendChild(error)
                error_count += 1

                error_details = root.createTextNode(
                    result.details if result.details else result.message
                )
                error.appendChild(error_details)

            if project.renderLog:
                stdout = root.createElement("system-out")
                stdout_content = root.createTextNode(project.renderLog)
                stdout.appendChild(stdout_content)
                case.appendChild(stdout)

            if project.renderErrorLog:
                stderr = root.createElement("system-err")
                stderr_content = root.createTextNode(project.renderErrorLog)
                stderr.appendChild(stderr_content)
                case.appendChild(stderr)

        suite.setAttribute("name", "kdenlive")
        suite.setAttribute("errors", str(error_count))
        suite.setAttribute("failures", str(failed_count))
        suite.setAttribute("time", "0.00")
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        suite.setAttribute("timestamp", timestamp)
        suite.setAttribute("hostname", socket.gethostname())

        xml_str = root.toprettyxml(indent="\t")

        with open(outputFile, "w") as f:
            f.write(xml_str)

    def saveHtmlToFile(self, outputFile: Path) -> None:
        with open(outputFile, "wt") as text_file:
            text_file.write(self.toHtml())

        print(
            f"---------------\nRender results saved to {outputFile!s}\n---------------",
            flush=True,
        )

    @property
    def successful(self) -> bool:
        success = True
        for setupTestItem in self.setupResults:
            category, result = setupTestItem
            success = success and (
                result.status == CompareResultStatus.SUCCESS
                or result.status == CompareResultStatus.SKIPPED
            )

        for projectTestItem in self.projectResults:
            project, result = projectTestItem
            failureAllowed = project.isFailureAllowed(
                result.videoErrors, result.audioErrors
            )
            success = success and (
                result.status == CompareResultStatus.SUCCESS
                or result.status == CompareResultStatus.SKIPPED
                or failureAllowed
            )

        return success
