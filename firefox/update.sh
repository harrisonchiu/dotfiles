#!/bin/bash

# Updating Firefox CSS for WSL ONLY
# Used to move data from WSL to Firefox in Windows
# TODO: 
#  - Add option for Linux only

readonly MAIN_FIREFOX_CSS='Firefox-Mod-Blur'
readonly WINDOWS_USER="$1"
if [ $# -eq 0 ]; then
    echo 'Windows user name is not given'
    exit 1
fi

cd "$(dirname "$0")" || exit 1

# Clean all Firefox mods
git submodule foreach --recursive git clean -xfd
git submodule foreach --recursive git reset --hard
git submodule update --init --recursive

( # Subshell to contain the `cd`
cd "${MAIN_FIREFOX_CSS}" || exit 1

# Extra CSS Mods specific to Firefox-Mod-Blur
shopt -s nocaseglob
cp ./*MODS/bookmarks*/*same*color*/*.css ./ 
cp ./*MODS/*extensions*/style*1/*.css ./ 
cp ./*MODS/tabs*/*sound*playing*/*.css ./ 
cp ./*MODS/tabs*/*static*width*/*.css ./ 
cp ./*MODS/icon*/*list*all*tabs*/*.css ./ 
cp ./*MODS/icon*/*icons*main*menu*/*.css ./ 
cp ./*MODS/search*bar*/*search*engine*buttons*/*.css ./ 
cp ./*MODS/privacy*/*change*main*menu*/*.css ./ 
cp ./*MODS/*control*buttons*/*thicker*windows*/*.css ./ 
shopt -u nocaseglob

# Add personal CSS fix file for Firefox-Mod-Blur
# Contents must be inside userChrome.css because the tags do not work when imported
echo '' >> userChrome.css
cat ../mod-blur-fix-window-controls.css >> userChrome.css
echo '' >> userChrome.css
)

# Move CSS files from WSL to Windows Firefox to actually see the changes
WINDOWS_FIREFOX_CHROME="$(
    find "/mnt/c/Users/${WINDOWS_USER}/AppData/Roaming/Mozilla/Firefox/Profiles" \
    -maxdepth 1 \
    -type d \
    -name "*default-release" \
)/chrome"
readonly WINDOWS_FIREFOX_CHROME

rm -rf "${WINDOWS_FIREFOX_CHROME}"
cp -r "${MAIN_FIREFOX_CSS}" "${WINDOWS_FIREFOX_CHROME}"

# Clean all Firefox mods
git submodule foreach --recursive git clean -xfd
git submodule foreach --recursive git reset --hard
git submodule update --init --recursive
