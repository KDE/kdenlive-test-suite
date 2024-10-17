# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from pnsr import CompareResult, CompareResultStatus
from RenderProject import RenderProject

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

    .lbl-toggle-missing {
        color: #666666;
        background: #FFFFFF;

    }

    .lbl-toggle-ok{
        color: #006600;
    }

    .lbl-toggle-warning{
        color: #FF7700;
    }

    .lbl-toogle-exists.lbl-toggle-warning:hover{
        color: #ffAA00;
    }

    .lbl-toggle-error{
        color: #660000;
    }

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
        projectResults: list[tuple[RenderProject, CompareResult]],
        renderFolder,
        referenceFolder,
    ):
        self.projectResults = projectResults
        self.renderFolder = renderFolder
        self.referenceFolder = referenceFolder
        self._tempFiles: list[Path] = []

    def _celanupTempFile(self):
        for filePath in self._tempFiles:
            filePath.unlink(missing_ok=True)
        self._tempFiles = []

    @staticmethod
    def _getFps(filename: Path):
        fps = 25
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
                        fps = int(v.split(" ")[1])
                        break
        proc3.wait()
        return fps

    def _extractFrameToImage(self, videoFile, frame, fps):
        imageFile = f"tmp/{datetime.now()}.png"
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
        return Image.open(imageFile)

    def _constructComparisonImage(
        self,
        referenceVideoFile: Path,
        renderVideoFile: Path,
        frame,
        fps,
        errors,
        length,
    ) -> Image.Image:
        borderWidth = 10

        img1 = self._extractFrameToImage(referenceVideoFile, frame, fps)
        img2 = self._extractFrameToImage(renderVideoFile, frame, fps)

        widths, heights = zip(*(i.size for i in [img1, img2]))

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

        new_im = Image.new("RGB", (total_width, max_height + (2 * timelineHeight)))
        new_im.paste(timeline, (0, max_height + timelineHeight))
        new_im.paste(resultImage, (0, max_height))
        x_offset = 0
        for im in [img1, img2]:
            img = ImageOps.expand(im, border=borderWidth, fill="red")
            new_im.paste(img, (x_offset, 0))
            x_offset += im.size[0] + 2 * borderWidth

        self._celanupTempFile()

        return new_im

    def _itemHtml(self, item: tuple[RenderProject, CompareResult], index: int) -> str:
        collapsible = ""

        project, result = item

        if result.status == CompareResultStatus.COMPARE_FAILURE:
            referenceVideo = Path(self.referenceFolder) / project.renderFilename
            fps = self._getFps(referenceVideo)
            renderVideo = Path(self.renderFolder) / project.renderFilename

            collapsible = "<b>Broken frames: </b>"
            for frameRange in result.errors:
                errorPos = frameRange[0] - 1

                comparisonImage = self._constructComparisonImage(
                    referenceVideo,
                    renderVideo,
                    errorPos,
                    fps,
                    result.errors,
                    result.framesCount,
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
                        result.errors,
                        result.framesCount,
                    )
                    imageName = f"tmp/{index}-{errorPos}-result.png"
                    comparisonImage.save(imageName)

                    collapsible += f"""
                    <a href="javascript:void(0)" onclick="toggleImg0('{imageName}')">
                        {errorPos}
                    </a> |
                    """

        status = result.statusString
        if project.allowFaliure:
            status = "warning"
        icon = (
            "emblem-checked.svg"
            if (status == "ok" or project.allowFaliure)
            else "emblem-error.svg"
        )

        if result.errorDetails:
            collapsible += result.errorDetails

        if project.allowFaliure:
            collapsible += "<p><b>Note:</b> This test is allowed to fail.</p>"

        collapsibleClass = "lbl-toogle-exists" if collapsible else ""
        html = f"""
        <input id="collapsible{index}" class="toggle" type="checkbox">
        <label for="collapsible{index}" class="lbl-toggle lbl-toggle-{status} {collapsibleClass}">
            <div class="centered">
                <img src="resources/{icon}" />
                Test #{index} for file <b>{project.renderFilename}</b>: {result.message}.
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
        body = ""

        counter = 1
        for item in self.projectResults:
            body += self._itemHtml(item, counter)
            counter += 1

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
                        <h2>Tests done on the {datetime.now()}</h2>
                        {body}
                    </div>
                </div>
            </body>
        </html>
        """

    def saveHtmlToFile(self, outputFile: Path):
        with open(outputFile, "wt") as text_file:
            text_file.write(self.toHtml())

        print(
            f"---------------\nRender results saved to {outputFile!s}\n---------------",
            flush=True,
        )

    @property
    def successful(self):
        success = True
        for item in self.projectResults:
            project, result = item
            success = success and (
                result.status == CompareResultStatus.SUCCESS or project.allowFaliure
            )

        return success
