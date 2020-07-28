#!/bin/bash

#############################
# CONFIGURATION
#############################
cd ../..


# Debug option for py2app, if needed
export INSPIGTOR_ROOT_DIR=`pwd`
export DISTUTILS_DEBUG=0
export DISTRO=macOS
export ARCH=amd64
export VERSION=`python3 -c "package_info={};exec(open('${INSPIGTOR_ROOT_DIR}/src/inspigtor/__pkginfo__.py').read(), {}, package_info);print(package_info['__version__'])"`

#############################
# PREPARATION
#############################
export INSPIGTOR_DIST_DIR=${INSPIGTOR_ROOT_DIR}/dist
export INSPIGTOR_APP_DIR=${INSPIGTOR_DIST_DIR}/inspigtor.app

#python3 setup.py build install
pip3 install .

#############################
# PACKAGING
#############################

echo -e "${BLUE}""Packaging inspigtor""${NORMAL}"
INSPIGTOR_DMG=inspigtor-${VERSION}-${DISTRO}-${ARCH}.dmg

cd ${INSPIGTOR_ROOT_DIR}/build_app/macos
python3 build.py py2app
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi

#############################
# BUNDLE PYTHON
#############################

# Add inspigtor version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION}" > ${INSPIGTOR_APP_DIR}/Contents/Resources/version

install_name_tool -change @loader_path/.dylibs/libjpeg.9.dylib @executable_path/../Frameworks/libjpeg.9.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/lib-dynload/PIL/_imaging.so

install_name_tool -change @loader_path/.dylibs/libopenjp2.2.3.1.dylib @executable_path/../Frameworks/libopenjp2.2.3.1.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/lib-dynload/PIL/_imaging.so

install_name_tool -change @loader_path/.dylibs/libz.1.2.11.dylib @executable_path/../Frameworks/libz.1.2.11.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/lib-dynload/PIL/_imaging.so

install_name_tool -change @loader_path/.dylibs/libtiff.5.dylib @executable_path/../Frameworks/libtiff.5.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/lib-dynload/PIL/_imaging.so

install_name_tool -change @loader_path/.dylibs/libxcb.1.1.0.dylib @executable_path/../Frameworks/libxcb.1.1.0.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/lib-dynload/PIL/_imaging.so

rm ${INSPIGTOR_APP_DIR}/Contents/MacOS/python
mkdir -p ${INSPIGTOR_APP_DIR}/Contents/Resources/bin
cp /Library/Frameworks/Python.framework/Versions/3.8/Resources/Python.app/Contents/MacOS/Python ${INSPIGTOR_APP_DIR}/Contents/Resources/bin/python

cp -r /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/* ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/
cp /Library/Frameworks/Python.framework/Versions/3.8/Python ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/libpython3.8.dylib
chmod 777 ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/libpython3.8.dylib

install_name_tool -change /Library/Frameworks/Python.framework/Versions/3.8/Python @executable_path/../Resources/lib/libpython3.8.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/bin/python
install_name_tool -id @loader_path/libpython3.8.dylib ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/libpython3.8.dylib

ln -s ../Resources/bin/python ${INSPIGTOR_APP_DIR}/Contents/MacOS/python

cp ${INSPIGTOR_ROOT_DIR}/build_app/macos/site.py ${INSPIGTOR_APP_DIR}/Contents/Resources/.
cp ${INSPIGTOR_ROOT_DIR}/build_app/macos/site.py ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/.

#############################
# Cleanup
#############################

# Removing matplotlib/tests ==> 45.2 Mb
rm -rf ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/matplotlib/tests
# Sample data for matplotlib is useless
rm -rf ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python3.8/matplotlib/mpl-data/sample_data
rm -rf ${INSPIGTOR_APP_DIR}/Contents/Resources/mpl-data/sample_data
# ZMQ package is useless
rm -rf ${INSPIGTOR_APP_DIR}/Contents/Resources/lib/python2.7/zmq

#############################
# Create DMG
#############################
hdiutil unmount /Volumes/inspigtor -force -quiet
sleep 5

${INSPIGTOR_ROOT_DIR}/build_app/macos/resources/dmg/create-dmg --background "${INSPIGTOR_ROOT_DIR}/build_app/macos/resources/dmg/dmg_background.jpg" --volname "inspigtor" --window-pos 200 120 --window-size 800 400 --icon inspigtor.app 200 190 --hide-extension inspigtor.app --app-drop-link 600 185 "${INSPIGTOR_DMG}" ${INSPIGTOR_DIST_DIR}

mv ${INSPIGTOR_ROOT_DIR}/build_app/macos/${INSPIGTOR_DMG} ${INSPIGTOR_ROOT_DIR}/
