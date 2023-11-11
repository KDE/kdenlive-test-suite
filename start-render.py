#!/usr/bin/env python3

import os
import ntpath
import subprocess
import sys
import webbrowser

# assign directory
directory = 'projects'

# iterate over files in
# that directory
counter = 1
outFolder = os.path.join('.', 'renders')
# ensure the renders folder exists
if not os.path.isdir(outFolder):
    os.mkdir(outFolder)
for filename in os.listdir(directory):
    projectFile = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(projectFile):
        fname = ntpath.basename(projectFile)
        # ensure destination render does not exists
        outName = os.path.splitext(filename)[0] + '.mp4'
        outputFile = os.path.join('renders', outName)
        if os.path.isfile(outputFile):
            print("Render file " + outputFile + " already exists, aborting")
            sys.exit()
        print("Processing project: " + fname + "...")
        subprocess.call(['kdenlive', "--render",  projectFile, outputFile])
        print("Processing project: " + fname + "... DONE")

subprocess.call(['./compare-renders.py'])

