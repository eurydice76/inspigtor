#!/bin/bash

VERSION=$1

git checkout $VERSION

rm -rf ./.env

rm -rf ./build

rm -rf ./dist

rm inspigtor*dmg

virtualenv -p python3 ./.env

source ./.env/bin/activate

pip install .

pip install py2app

python3 setup.py py2app --packages cffi

INSPIGTOR_DMG=inspigtor-${VERSION}-macOS-amd64.dmg
hdiutil unmount /Volumes/inspigtor -force -quiet
sleep 5
./deploy/macos/create-dmg --background "./deploy/macos/resources/dmg/dmg_background.jpg" \
                                                     --volname "inspigtor" \
									             	 --window-pos 200 120 \
										 			 --window-size 800 400 \
										 			 --icon inspigtor.app 200 190 \
										 			 --hide-extension inspigtor.app \
										 			 --app-drop-link 600 185 \
										 			 "${INSPIGTOR_DMG}" \
										 			 ./dist
