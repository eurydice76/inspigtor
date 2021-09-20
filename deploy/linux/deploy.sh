#!/bin/bash

ROOT_DIR=$(pwd)

VERSION=$1

PYTHON_VERSION=$2

git checkout ${VERSION}

rm -rf ./.env

virtualenv -p python${PYTHON_VERSION} ./env

source ./env/bin/activate

pip install appimage-builder

pip install .

cd deploy/linux

# Remove previous images
rm inspigtor-*-x86_64.AppImage*

sed -i "s/version: 0.0.0/version: ${VERSION}/g" AppImageBuilder.yml

# Run app builder
appimage-builder

mv inspigtor-*-x86_64.AppImage ${ROOT_DIR}
