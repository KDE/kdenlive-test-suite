# Kdenlive Test Suite

This repository is a work in progress. It hosts scripts to automatically render project files and compare them with a reference render to test for regressions.

To make these scripts useful, we refactored the Kdenlive rendering code to make it possible to render a project file from the command line (see [Kdenlive task 1615](https://invent.kde.org/multimedia/kdenlive/-/issues/1615)).

The repository currently only contains very basic assets and project files to this repository, as well as reference renderings, but you can easily add resources locally and run the scripts on your computer. 

The testing is a 2 steps process:

- First script will open all the project files in the "projects" folder and render them in the "renders" folder. After all renderings are over, it will call the second script for comparison.

- Second script will compare the renders in "renders" folder produced in step 1 with "reference" renderings.

# The scripts
**For step 1:**
`start-renders.py` will loop all project files in the `projects` folder and check if a rendered file already exists. In that case it will abort. Otherwise, it will render the project in the `renders` folder. When all renders are done, it will call the `compare-renders.py` script (step 2).

**For step 2:**
`compare-renders.py` will check all existing renders in the `renders` folder and check if there is a matching name reference render. It will then pass the 2 files to the second script: `pnsr.py`
TODO: currently only video is compared, no check is made on audio

`pnsr.py` takes 3 arguments:

The reference render file
The newly rendered file
An incremental integer number describing the count of processed files

This script will then compare the 2 files using the FFmpeg pnsr filter, and detect inconsistensies. It will then output some html data that is then collected by the `compare-renders.py` script and displayed in an HTML page like below:

![Sample test web view](pics/pnsr.jpg "Sample results view")
