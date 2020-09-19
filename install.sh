# set version to download
version="1.0.4"

rm -r "$HOME/.SWAT/SWATPlus"
rm -r "$HOME/.local/share/swatplus"

mkdir -p "$HOME/.SWAT/SWATPlus"
mkdir -p "$HOME/.local/share/swatplus"

wget -c "https://github.com/celray/swatplus-automatic-workflow/archive/v$version.zip"
wget -c "https://github.com/celray/swatplus-automatic-workflow/releases/download/v$version/TauDEM5Bin_Linux.zip"
wget -c "https://github.com/celray/swatplus-automatic-workflow/raw/master/editor_api/swatplus_wgn.sqlite"

unzip "./v$version.zip"
unzip "./TauDEM5Bin_Linux.zip"

echo "copying files"
mv "./swatplus-automatic-workflow-$version" "$HOME/.SWAT/SWATPlus/Workflow"
mv "./TauDEM5Bin" "$HOME/.local/share/swatplus/TauDEM5Bin"
mv "./swatplus_wgn.sqlite" "$HOME/.SWAT/SWATPlus/Workflow/editor_api/"
chmod 777 "$HOME/.SWAT/SWATPlus/Workflow/swatplus_aw.sh"
chmod -R 777 "$HOME/.local/share/swatplus/TauDEM5Bin"

# cleanup
echo "cleaning up"
rm "$HOME/.SWAT/SWATPlus/Workflow/.gitattributes"
rm "$HOME/.SWAT/SWATPlus/Workflow/swatplus_aw.bat"
rm "$HOME/.SWAT/SWATPlus/Workflow/code_of_conduct.md"
rm -r "$HOME/.SWAT/SWATPlus/Workflow/.github"
rm "./TauDEM5Bin_Linux.zip"
rm "./v$version.zip"

# set environmental variables
echo "setting up environmental variables"
echo 'export PATH=$PATH:$HOME/.SWAT/SWATPlus/Workflow' >>~/.bashrc
echo 'export swatplus_wf_dir=$HOME/.SWAT/SWATPlus/Workflow' >>~/.bashrc
