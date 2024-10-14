#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import os
import sys
import ntpath
import subprocess
import webbrowser
from datetime import datetime

# assign directory
refDirectory = os.path.abspath("reference")
renderDirectory = os.path.abspath("renders")

# iterate over files in
# that directory
resultHtml = "<!DOCTYPE html><head><style>body{font-family: arial};"
resultHtml += ".wrap-collabsible{margin-bottom: 1rem 0;} input[type='checkbox'] {display: none;} .lbl-toggle3{display: block; font-weight: normal; font-family: monospace; font-size: 1rem; text-align: left; vertical-align: middle; padding: 0.2rem; color: #666666; background: #FFFFFF; cursor: arrow; border-bottom: 1px solid #999999; transition: all 0.25s ease-out;} .lbl-toggle2{display: block; font-weight: normal;font-family: monospace; font-size: 1rem; text-align: left; vertical-align: middle; padding: 0.2rem; color: #006600; background: #FFFFFF; cursor: arrow; border-bottom: 1px solid #999999; transition: all 0.25s ease-out;} .lbl-toggle{display: block; font-weight: normal; font-family: monospace; font-size: 1rem; text-align: left; vertical-align: middle; padding: 0.2rem; color: #660000; background: #FFFFFF; cursor: pointer; border-bottom: 1px solid #999999; transition: all 0.25s ease-out;} .lbl-toggle:hover {color: #FF6666;}  .collapsible-content {max-height: 0px; overflow: hidden; transition: max-height .25s ease-in-out;} .toggle:checked+.lbl-toggle+.collapsible-content {max-height: 100vh;} .toggle:checked+.lbl-toggle {  border-bottom-right-radius: 0; border-bottom-left-radius: 0;} .collapsible-content .content-inner { background: rgba(250, 224, 66, .2); border-bottom: 1px solid rgba(250, 224, 66, .45); border-bottom-left-radius: 7px; border-bottom-right-radius: 7px; padding: .5rem 1rem;} div.centered{vertical-align: middle}"  # noqa: E501
resultHtml += " .split { height: 100%; width: 50%; position: fixed; z-index: 1; top: 0; overflow-x: hidden; padding-top: 20px;} .left { left: 0; padding:5px; background-color: #FFFFFF;} .right { right: 0; background-color: #CCCCCC;} .rightcentered { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;}"  # noqa: E501
resultHtml += '</style><script>function toggleImg0(charName) {document.getElementById("thumb").src = charName ;}</script></head><body><div class="wrap-collabsible">'  # noqa: E501
resultHtml += '<div class="split right"><img class="rightcentered" width="98%" src="" id="thumb"></div>'
resultHtml += (
    '<div class="split left"><h2>Tests done on the ' + str(datetime.now()) + "</h2>"
)
counter = 1
items = os.listdir(refDirectory)
sorted_items = sorted(items)
for filename in sorted_items:
    if filename.lower().endswith("txt"):
        continue
    f = os.path.join(refDirectory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        fname = ntpath.basename(f)
        # ensure destination render exists
        print("CHECKING FILE: ", fname, flush=True)
        renderPath = os.path.join(renderDirectory, fname)
        if not os.path.isfile(renderPath):
            resultHtml += (
                '<input id="collapsible'
                + str(counter)
                + '" class="toggle" type="checkbox">'
            )
            resultHtml += (
                '<label for="collapsible'
                + str(counter)
                + '" class="lbl-toggle3"><div class="centered"><span><img src="resources/emblem-error.svg" /> Test #'
                + str(counter)
                + " for file <b>"
                + fname
                + " ("
                + renderPath
                + ")"
                + "</b> is missing.</span></div></label>"
            )
            counter += 1
            continue
        print(f + ", ref: reference/" + fname, flush=True)
        pythonName = "python" if os.name == "nt" else "python3"
        cmd = [pythonName, "pnsr.py", f, "renders/" + fname, str(counter)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (output, err) = proc.communicate()
        resultHtml += output.decode()
        counter += 1
resultHtml += "</div></div></body></html>"
testFailed = "failed.png" in resultHtml
text_file = open("result.html", "wt")
n = text_file.write(resultHtml)
text_file.close()
print(
    "-------------------------------\nRender results saved to result.html\n----------------------------",
    flush=True,
)
try:
    webbrowser.get("firefox").open("result.html")
except webbrowser.Error:
    print(
        "Could not start Firefox, trying chrome... otherwise open the result.html file manually"
    )

if testFailed:
    sys.exit(1)
