#!/bin/bash

#############################
# Create DMG
#############################

if [[ $GITHUB_REF == refs/heads/* ]] ;
then
    VERSION=${GITHUB_REF#refs/heads/}
else
	if [[ $GITHUB_REF == refs/tags/* ]] ;
	then
		VERSION=${GITHUB_REF#refs/tags/}
	else
		exit 1
	fi
fi

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
