#!/bin/bash

# Updating Firefox CSS
# Used to move data from WSL to Firefox in Windows
# TODO: 
#  - Add option for Linux only

readonly MAIN_FIREFOX_CSS="$1"
readonly REDDIT_OLD_REDESIGNED="$2"
readonly WINDOWS_USER_NAME="$3"

cd "$(dirname "$0")"

# Clean all Firefox mods
git submodule foreach --recursive git clean -xfd
git submodule foreach --recursive git reset --hard
git submodule update --init --recursive


cd "${MAIN_FIREFOX_CSS}"

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

# CSS for redesigning old.reddit.com
readonly REDDIT_CSS="$(echo .css)"
cp "../${REDDIT_OLD_REDESIGNED}/${REDDIT_CSS}" ./
printf "\n\n@import url("%s");\n" "${REDDIT_CSS}" >> userContent.css

cd ..


# Move CSS files to Windows Firefox to actually see the changes
readonly WINDOWS_FIREFOX_CHROME="/Users/$2/AppData/Roaming/Mozilla/Firefox/Profiles/*default-release/chrome"

rm -r "${WINDOWS_FIREFOX_CHROME}"
cp -r "${MAIN_FIREFOX_CSS}" "${WINDOWS_FIREFOX_CHROME}"
