# Kdenlive Test Suite

This repository is a work in progress. It will ultimately host scripts to automatically render project files and compare them with a reference render to test for regressions

To make these scripts useful, we first need to refactor the Kdenlive rendering code to make it possible to render a project file from the command line (see [Kdenlive task 1615](https://invent.kde.org/multimedia/kdenlive/-/issues/1615)).

Then, we need to add some basic assets and project files to this repository, as well as reference renderings.

The testing will then be a 2 steps process:

- First step is to have a script opening all project files of the repository and create renders with the Kdenlive version installed on the host or an AppImage version. This is still a TODO

- Second step is to have scripts comparing the renders produced in step 1 and compare them with the reference renders.

# The scripts

**For step 2:**
`compare-renders.py` will check all existing renders in the `renders` folder and check if there is a matching name reference render. It will then pass the 2 files to the second script: `pnsr.py`

`pnsr.py` takes 3 arguments:

The reference render file
The newly rendered file
An incremental integer number describing the count of processed files

This script will then compare the 2 files using the FFmpeg pnsr filter, and detect inconsistensies. It will then output some html data that is then collected by the `compare-renders.py` script and displayed in an HTML page like below:

![Sample test web view](pics/pnsr.jpg "Sample results view")
