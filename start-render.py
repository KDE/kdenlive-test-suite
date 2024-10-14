#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-FileCopyrightText: 2024 Julius Künzel <julius.kuenzel@kde.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL


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

        print('GOT PROFILE INFO:', renderProfile, " = ", renderUrl, flush=True)
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
        print("Processing project: " + fname + " to destination: " + outputFile, flush=True)
        args = []
        if len(sys.argv) > 1:
            args += sys.argv[1].split()
        else:
            args += ["kdenlive"]
        args += ["--render", projectFile]
        if renderProfile:
            args += ['--render-preset', renderProfile]
        args += [outputFile]
        print("Starting command: ", args, flush=True)
        # ensure MLT's Qt module gets loaded by simulating a display
        my_env = os.environ.copy()
        my_env["DISPLAY"] = ":0"
        subprocess.run(args, env=my_env)
        print("Rendering project: " + fname + "... DONE", flush=True)

pythonName = "python" if os.name == 'nt' else "python3"
child = subprocess.Popen([pythonName, "./compare-renders.py"])
child.communicate()
status = child.returncode
if status != 0:
    print("\n****************************************\n"
          "*           JOB FAILED                 *"
          "****************************************\n", flush=True)
else:
    print("JOB SUCCESSFUL\n", flush=True)
sys.exit(status)
