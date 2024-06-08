#!/usr/bin/env python3

import subprocess
import sys
import array
import os
from pathlib import Path
from PIL import Image, ImageOps
from PIL import ImageDraw
from PIL import ImageFont

referenceFile = sys.argv[1]
lastRender = sys.argv[2]
testCounter = int(sys.argv[3])
freeMonoFontFile = Path(__file__).parent / "fonts/freemono/FreeMono.ttf"

ffmpegCommand = os.environ.get('TEST_FFMPEG_CMD', "ffmpeg").split()

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

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
framesCount = 0
framesError = 0
errorThumb = 0
firstErrorFrame = -1
borderWidth = 10
errorArray = array.array("i")
# lastState remembers the last frame's status (0 = ok, 1 = error)
lastState = 0
maxPnsrValue = 0
for line in proc.stdout:
    linestr = str(line, "utf-8")
    values = linestr.split()
    pnsr = values[1].split(":")
    value = float(pnsr[1])
    if value > 10:
        maxPnsrValue = max(value, maxPnsrValue)
        errorFrame = int(values[0].split(":")[1])
        if lastState == 0:
            errorArray.append(errorFrame)
            lastState = 1
        framesError += 1
        #        print(str(errorFrame) + ': PNSR=' + str(value))
        if firstErrorFrame < 0:
            firstErrorFrame = errorFrame
    else:
        if lastState == 1:
            errorFrame = int(values[0].split(":")[1])
            errorArray.append(errorFrame)
            lastState = 0
    framesCount += 1

framesCount -= 1

if lastState == 1:
    errorArray.append(framesCount)
    lastState = 0

# extract thumbnail
if firstErrorFrame > 0:
    # Find video file fps to calculate position in seconds
    keyword1 = "Stream #"
    keyword2 = "Video:"
    fps = 25
    cmd3 = ffmpegCommand + ["-hide_banner", "-i", referenceFile]
    proc3 = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc3.stderr:
        linestr = str(line, "utf-8")
        if keyword1 in linestr and keyword2 in linestr:
            # match
            vals = linestr.split(",")
            keyword3 = " tbr"
            for v in vals:
                if keyword3 in v:
                    fps = int(v.split(" ")[1])
                    break

    # errorPos = firstErrorFrame + (errorArray[1] - errorArray[0])/2
    for x in range(len(errorArray)):
        if x % 2 == 0 or errorArray[x] - errorArray[x - 1] > 1:
            errorPos = errorArray[x] - 1
            thbcmd = ffmpegCommand + [
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(errorPos / fps),
                "-i",
                referenceFile,
                "-frames:v",
                "1",
                "tmp/ref.png",
            ]
            proc2 = subprocess.Popen(thbcmd, stdout=subprocess.PIPE)
            proc2.wait()
            img = Image.open("tmp/ref.png")

            thbcmd2 = ffmpegCommand + [
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(errorPos / fps),
                "-i",
                lastRender,
                "-frames:v",
                "1",
                "tmp/render.png",
            ]
            proc3 = subprocess.Popen(thbcmd2, stdout=subprocess.PIPE)
            proc3.wait()

            images = [Image.open(x) for x in ["tmp/ref.png", "tmp/render.png"]]
            widths, heights = zip(*(i.size for i in images))

            total_width = sum(widths) + 4 * borderWidth
            max_height = max(heights) + 2 * borderWidth
            timelineHeight = int(max_height / 6)
            # Results text
            result = Image.new("RGB", (total_width, timelineHeight))
            I1 = ImageDraw.Draw(result)
            textHeight = int(timelineHeight / 3)
            result.paste("red", (0, 0, total_width, textHeight + borderWidth))
            myFont = ImageFont.truetype(freeMonoFontFile, textHeight)
            I1.text(
                (10, 2),
                "Reference: " + referenceFile,
                font=myFont,
                fill="white",
                stroke_width=2,
                stroke_fill="white",
            )
            I1.text(
                (total_width / 2 + 10, 2),
                "Last render: " + lastRender,
                font=myFont,
                fill="white",
                stroke_width=2,
                stroke_fill="white",
            )
            I1.text(
                (10, timelineHeight / 2 + 10),
                "Error at frame : " + str(int(errorPos)),
                font=myFont,
                fill="yellow",
                stroke_width=2,
                stroke_fill="yellow",
            )

            # timeline of ok and incorrect segments
            timeline = Image.new("RGB", (total_width, timelineHeight))
            I2 = ImageDraw.Draw(timeline)
            timeline.paste("darkgreen", (0, 0, timeline.size[0], timeline.size[1]))
            for y in range(len(errorArray)):
                # print(str(x) + " = " + str(errorArray[x]) + " / MAX: " + str(framesCount))
                if y % 2 == 0:
                    shape = [
                        (total_width * errorArray[y] / framesCount, 0),
                        (total_width * errorArray[y + 1] / framesCount, timelineHeight),
                    ]
                    I2.rectangle(shape, fill="orange")

            shape = [
                (total_width * errorPos / framesCount, 0),
                (total_width * errorPos / framesCount + borderWidth, timelineHeight),
            ]
            I2.rectangle(shape, fill="darkred")

            new_im = Image.new("RGB", (total_width, max_height + (2 * timelineHeight)))
            new_im.paste(timeline, (0, max_height + timelineHeight))
            new_im.paste(result, (0, max_height))
            x_offset = 0
            for im in images:
                img = ImageOps.expand(im, border=borderWidth, fill="red")
                new_im.paste(img, (x_offset, 0))
                x_offset += im.size[0] + 2 * borderWidth

            outputImage = (
                "tmp/" + str(testCounter) + "-" + str(errorThumb) + "-result.png"
            )
            new_im.save(outputImage)
            errorThumb += 1

    print(
        '<input id="collapsible'
        + str(testCounter)
        + '" class="toggle" type="checkbox">'
    )
    print(
        '<label for="collapsible'
        + str(testCounter)
        + '" class="lbl-toggle"><div class="centered"><img src="resources/failed.png" /> Test #'
        + str(testCounter)
        + " for file <b>"
        + referenceFile
        + "</b> failed at frame <b>"
        + str(firstErrorFrame)
        + "</b>, PNSR: "
        + f"{maxPnsrValue:.3f}"
        + ".</div></label>"
    )
    print(
        '<div class="collapsible-content"><div class="content-inner"><b>Broken frames: </b>'
    )
    counter2 = 0
    for z in range(len(errorArray)):
        if z % 2 == 0:
            errorPos2 = errorArray[z] - 1
            outputImage2 = (
                "tmp/" + str(testCounter) + "-" + str(counter2) + "-result.png"
            )
            print(
                '<a href="javascript:void(0)" onclick="toggleImg0(\''
                + outputImage2
                + "')\">"
                + str(errorPos2)
            )
            counter2 += 1
            if errorArray[z + 1] - errorArray[z] < 2:
                print("</a> | ")
            else:
                print("</a>-")
                # Second image
                errorPos2 = errorArray[z + 1] - 1
                outputImage2 = (
                    "tmp/" + str(testCounter) + "-" + str(counter2) + "-result.png"
                )
                print(
                    '<a href="javascript:void(0)" onclick="toggleImg0(\''
                    + outputImage2
                    + "')\">"
                    + str(errorPos2)
                )
                print("</a> | ")
                counter2 += 1
    print("</div></div>")
else:
    # job succeded
    print(
        '<input id="collapsible'
        + str(testCounter)
        + '" class="toggle" type="checkbox">'
    )
    print(
        '<label for="collapsible'
        + str(testCounter)
        + '" class="lbl-toggle2"><div class="centered"><img src="resources/ok.png" /> Test #'
        + str(testCounter)
        + " for file <b> "
        + referenceFile
        + " </b> succeded.</div></label>"
    )


# print("First Error: " + str(firstErrorFrame) + ", TOTAL ERRORS: " + str(int(100*framesError/framesCount + 0.5)) + "%")
