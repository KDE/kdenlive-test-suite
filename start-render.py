#!/usr/bin/env python3

import os
import ntpath
import subprocess
import sys
import xml.dom.minidom

# assign directory
directory = "projects"

# iterate over files in
# that directory
counter = 1
tmpFolder = os.path.join(".", "tmp")
if not os.path.isdir(tmpFolder):
    os.mkdir(tmpFolder)
outFolder = os.path.join(".", "renders")

if len(sys.argv) > 1:
    binaryFile = sys.argv[1]
else:
    binaryFile = "kdenlive"
# ensure the renders folder exists
if not os.path.isdir(outFolder):
    os.mkdir(outFolder)
elif len(os.listdir(outFolder)) > 0 :
    # If renders folder is not empty, ask if ok the clear it
    answer = input("Render folder is not empty, files will be overwritten. Continue [Y/n] ?")
    if answer.lower() in ["y","yes",""]:
        # Ok, proceed
        print("Proceeding...")
    else:
        # Abort
        sys.exit()

for filename in os.listdir(directory):
    projectFile = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(projectFile):
        document = xml.dom.minidom.parse(projectFile)
        pl = document.getElementsByTagName("playlist")
        renderProfile = ''
        renderUrl = ''
        for node in pl:
            pl_id=node.getAttribute('id')
            if pl_id == "main_bin":
                props=node.getElementsByTagName('property')
                for prop in props:
                    prop_name=prop.getAttribute('name')
                    if prop_name == "kdenlive:docproperties.renderprofile":
                        renderProfile = prop.firstChild.data
                    if prop_name == "kdenlive:docproperties.renderurl":
                        renderUrl = prop.firstChild.data
                break

        print('GOT PROFILE INFO:', renderProfile, " = ", renderUrl)
        fname = ntpath.basename(projectFile)
        # ensure destination render does not exists
        if renderUrl:
            fname, file_extension = os.path.splitext(renderUrl)
            outName = os.path.splitext(filename)[0] + file_extension
        else:
            outName = os.path.splitext(filename)[0] + ".mp4"
        outputFile = os.path.join("renders", outName)
        if os.path.isfile(outputFile):
            # delete previous render
            print("Clearing previous render: " + outputFile)
            os.remove(outputFile)
        print("Processing project: " + fname + "...")
        if renderProfile:
            subprocess.call([binaryFile, "--render", projectFile, '--render-preset', renderProfile, outputFile])
        else:
            subprocess.call([binaryFile, "--render", projectFile, outputFile])
        print("Processing project: " + fname + "... DONE")

subprocess.call(["./compare-renders.py"])
