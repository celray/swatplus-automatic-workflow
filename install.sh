#!/bin/bash

# To isolate this from other Python projects, create a specific user on your machine
# and install libraries at user level, excepted qgis, python3-pip and mpich packages.
#
# Before launching this script make sure that the following packages have been installed
# 
# For Ubuntu 20.04
# sudo apt install qgis python3-pip mpich
# pip3 install --user geopandas peewee cython scipy
#
# set version to download
version="1.0.4"
# set swat home
export SWAT_HOME="~/dev/conda/pesteaux_conda/swat_tools"

rm -r "$SWAT_HOME/.SWAT/SWATPlus"
rm -r "$SWAT_HOME/.local/share/swatplus"

mkdir -p "$SWAT_HOME/.SWAT/SWATPlus"
mkdir -p "$SWAT_HOME/.local/share/swatplus"

wget -c "https://github.com/celray/swatplus-automatic-workflow/archive/v$version.zip"
wget -c "https://github.com/celray/swatplus-automatic-workflow/releases/download/v$version/TauDEM5Bin_Linux.zip"
# wget -c "https://github.com/celray/swatplus-automatic-workflow/raw/master/editor_api/swatplus_wgn.sqlite"
wget -c "https://bitbucket.org/swatplus/swatplus.editor/downloads/swatplus_wgn.sqlite"

unzip "./v$version.zip"
unzip "./TauDEM5Bin_Linux.zip"

echo "copying files"
mv "./swatplus-automatic-workflow-$version" "$SWAT_HOME/.SWAT/SWATPlus/Workflow"
mv "./TauDEM5Bin" "$SWAT_HOME/.local/share/swatplus/TauDEM5Bin"
mv "./swatplus_wgn.sqlite" "$SWAT_HOME/.SWAT/SWATPlus/Workflow/editor_api/"
chmod 777 "$SWAT_HOME/.SWAT/SWATPlus/Workflow/swatplus_aw.sh"
chmod -R 777 "$SWAT_HOME/.local/share/swatplus/TauDEM5Bin"

# cleanup
echo "cleaning up"
rm "$SWAT_HOME/.SWAT/SWATPlus/Workflow/.gitattributes"
rm "$SWAT_HOME/.SWAT/SWATPlus/Workflow/swatplus_aw.bat"
rm "$SWAT_HOME/.SWAT/SWATPlus/Workflow/code_of_conduct.md"
rm -r "$SWAT_HOME/.SWAT/SWATPlus/Workflow/.github"
rm "./TauDEM5Bin_Linux.zip"
rm "./v$version.zip"

# set environmental variables
echo "setting up environmental variables"
echo 'export PATH=$PATH:$SWAT_HOME/.SWAT/SWATPlus/Workflow' >>~/.bashrc
echo 'export swatplus_wf_dir=$SWAT_HOME/.SWAT/SWATPlus/Workflow' >>~/.bashrc
