import subprocess
import struct
import sys
import array
from PIL import Image, ImageOps
from PIL import ImageDraw
from PIL import ImageFont

referenceFile = sys.argv[1]
lastRender = sys.argv[2]
testCounter = int(sys.argv[3])

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", referenceFile, "-i", lastRender, "-filter_complex", "psnr=f=-", "-f", "null", "/dev/null"]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
framesCount = 0
framesError = 0
firstErrorFrame = -1
borderWidth = 10
errorArray = array.array('i')
# lastState remembers the last frame's status (0 = ok, 1 = error)
lastState = 0
for line in proc.stdout:
    linestr = str(line, 'utf-8')
    values = linestr.split()
    pnsr = values[1].split(':')
    value = float(pnsr[1])
    if (value > 0) :
        errorFrame = int(values[0].split(':')[1])
        if (lastState == 0):
            errorArray.append(errorFrame)
            lastState = 1
        framesError += 1
        #print(str(errorFrame) + ': PNSR=' + str(value))
        if (firstErrorFrame < 0) :
            firstErrorFrame = errorFrame
    else:
        if (lastState == 1):
            errorFrame = int(values[0].split(':')[1])
            errorArray.append(errorFrame)
            lastState = 0
    framesCount += 1

framesCount -= 1

if (lastState == 1):
    errorArray.append(framesCount)
    lastState = 0

# extract thumbnail
if (firstErrorFrame > 0):
    # Find video file fps to calculate position in seconds
    cmd3 = ["ffmpeg", "-hide_banner", "-i", referenceFile]
    proc3 = subprocess.Popen(cmd3, stdout=subprocess.PIPE)
    keyword1 = "Stream #"
    keyword2 = "Video:"
    fps = 25
    for line in proc3.stdout:
        linestr = str(line, 'utf-8')
        print("::GOT LINE: "+linestr)
        if keyword1 in linestr and keyword2 in linestr:
            # match
            vals = linestr.split(',')
            keyword3 = " tbr"
            for v in vals:
                if keyword3 in v:
                    fps = int(v.split(' ')[0])
                    print("<b>FOUND FPS FOR: "+referenceFile+" = "+str(fps))
                    break

    errorPos = firstErrorFrame + (errorArray[1] - errorArray[0])/2
    thbcmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(errorPos/25), "-i", referenceFile, "-frames:v", "1", "out.png"]
    proc2 = subprocess.Popen(thbcmd, stdout=subprocess.PIPE)
    proc2.wait()
    img = Image.open('out.png')

    thbcmd2 = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(errorPos/25), "-i", lastRender, "-frames:v", "1", "out2.png"]
    proc3 = subprocess.Popen(thbcmd2, stdout=subprocess.PIPE)
    proc3.wait()
    images = [Image.open(x) for x in ['out.png', 'out2.png']]
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths) + 4 * borderWidth
    max_height = max(heights) + 2 * borderWidth
    timelineHeight = int(max_height / 5)
    # Results text
    result = Image.new("RGB", (total_width, timelineHeight))
    I1 = ImageDraw.Draw(result)
    textHeight = int(timelineHeight / 3)
    result.paste( "red", (0, 0, total_width, textHeight + borderWidth))
    myFont = ImageFont.truetype('FreeMono.ttf', textHeight)
    I1.text((10, 2), "Reference: " + referenceFile, font=myFont, fill="white", stroke_width=2, stroke_fill="white")
    I1.text((total_width / 2 + 10, 2), "Last render: " + lastRender, font=myFont, fill="white", stroke_width=2, stroke_fill="white")
    I1.text((10, timelineHeight / 2 + 10), "First error: " + str(firstErrorFrame) + ", Thumb: " + str(int(errorPos)), font=myFont, fill="yellow", stroke_width=2, stroke_fill="yellow")

    # timeline of ok and incorrect segments
    timeline = Image.new("RGB", (total_width, timelineHeight))
    I2 = ImageDraw.Draw(timeline)
    timeline.paste( "darkgreen", (0, 0, timeline.size[0], timeline.size[1]))
    for x in range(len(errorArray)):
        # print(str(x) + " = " + str(errorArray[x]) + " / MAX: " + str(framesCount))
        if (x%2 == 0):
            shape = [(total_width * errorArray[x] / framesCount, 0), (total_width * errorArray[x+1] / framesCount, timelineHeight)]
            I2.rectangle(shape, fill ="red")

    shape = [(total_width * errorPos / framesCount, 0), (total_width * errorPos / framesCount + borderWidth, timelineHeight)]
    I2.rectangle(shape, fill ="darkred")

    new_im = Image.new('RGB', (total_width, max_height + (2 * timelineHeight)))
    new_im.paste(timeline, (0, max_height + timelineHeight))
    new_im.paste(result, (0, max_height))
    x_offset = 0
    for im in images:
        img = ImageOps.expand(im, border=borderWidth,fill='red')
        new_im.paste(img, (x_offset,0))
        x_offset += im.size[0]+2*borderWidth

    new_im.save('result.png')
    print("<input id=\"collapsible" + str(testCounter) + "\" class=\"toggle\" type=\"checkbox\">")
    print("<label for=\"collapsible" + str(testCounter) + "\" class=\"lbl-toggle\">Test #" + str(testCounter) + " for file <b>" + lastRender + "</b> failed at frame <b>" + str(firstErrorFrame) + "</b>.</label>")
    print("<div class=\"collapsible-content\"><div class=\"content-inner\"><p><img width=\"50%\" src=\"result.png\"></p></div></div>");
else:
    # job succeded
    print("<input id=\"collapsible" + str(testCounter) + "\" class=\"toggle\" type=\"checkbox\">")
    print("<label for=\"collapsible" + str(testCounter) + "\" class=\"lbl-toggle2\">Test #" + str(testCounter) + " for file <b>" + lastRender + "</b> succeded.</label>")


#print("First Error: " + str(firstErrorFrame) + ", TOTAL ERRORS: " + str(int(100*framesError/framesCount + 0.5)) + "%")
