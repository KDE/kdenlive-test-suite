#!/usr/bin/env python3

import os
import ntpath
import subprocess
import sys
import webbrowser

# assign directory
directory = 'reference'

# iterate over files in
# that directory
resultHtml = "<!DOCTYPE html><head><style>body{font-family: arial};"
resultHtml += ".wrap-collabsible{margin-bottom: 1rem 0;} input[type='checkbox'] {display: none;} .lbl-toggle3{display: block; font-weight: bold; font-family: monospace; font-size: 1rem; text-align: left; padding: 1rem; color: #FFFF66; background: #996633; cursor: pointer; border-radius: 7px; transition: all 0.25s ease-out;} .lbl-toggle2{display: block; font-weight: bold; font-family: monospace; font-size: 1rem; text-align: left; padding: 1rem; color: #66FF66; background: #339933; cursor: pointer; border-radius: 7px; transition: all 0.25s ease-out;} .lbl-toggle{display: block; font-weight: bold; font-family: monospace; font-size: 1rem; text-align: left; padding: 1rem; color: #FFFFFF; background: #CC0000; cursor: pointer; border-radius: 7px; transition: all 0.25s ease-out;} .lbl-toggle:hover {color: #FF6666;} .lbl-toggle::before {content: ' '; display: inline-block; border-top: 5px solid transparent; border-bottom: 5px solid transparent; border-left: 5px solid currentColor; vertical-align: middle; margin-right: .7rem; transform: translateY(-2px); transition: transform .2s ease-out;} .toggle:checked+.lbl-toggle::before {transform: rotate(90deg) translateX(-3px);} .collapsible-content {max-height: 0px; overflow: hidden; transition: max-height .25s ease-in-out;} .toggle:checked+.lbl-toggle+.collapsible-content {max-height: 100vh;} .toggle:checked+.lbl-toggle {  border-bottom-right-radius: 0; border-bottom-left-radius: 0;} .collapsible-content .content-inner { background: rgba(250, 224, 66, .2); border-bottom: 1px solid rgba(250, 224, 66, .45); border-bottom-left-radius: 7px; border-bottom-right-radius: 7px; padding: .5rem 1rem;}"
resultHtml += "</style><script>function toggleImg0(charName) {document.getElementById(\"thumb\").src = charName ;}</script></head><body><div class=\"wrap-collabsible\">"
counter = 1
for filename in os.listdir(directory):
    if filename.lower().endswith('txt'):
        continue
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        fname = ntpath.basename(f)
        # ensure destination render exists
        if not os.path.isfile("renders/" + fname):
            resultHtml += "<input id=\"collapsible" + str(counter) + "\" class=\"toggle\" type=\"checkbox\">"
            resultHtml += "<label for=\"collapsible" + str(counter) + "\" class=\"lbl-toggle3\">Test #" + str(counter) + " for file <b>" + f + "</b> is missing.</label>"
            counter += 1
            continue
        print(f + ", ref: reference/" + fname)
        cmd = ["python3", "pnsr.py", f, "renders/" + fname, str(counter)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (output, err) = proc.communicate()
        resultHtml += output.decode()
        counter += 1
resultHtml += "</div></body></html>"
text_file = open("result.html", "wt")
n = text_file.write(resultHtml)
text_file.close()
webbrowser.open("result.html")
