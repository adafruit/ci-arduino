#!/bin/bash

set -e

sudo apt-get update
sudo apt-get remove python3 python
sudo apt-get install python3.8

pip3 install clint pyserial setuptools adafruit-nrfutil
sudo apt-get install -y --allow-downgrades libllvm8=1:8-3~ubuntu18.04.2 -V
sudo apt install -fy cppcheck clang-format-8
#if [ ! -f /usr/bin/clang-format ]; then
#    sudo ln -s /usr/bin/clang-format-8 /usr/bin/clang-format
#fi

# make all our directories we need for files and libraries
mkdir ${HOME}/.arduino15
mkdir ${HOME}/.arduino15/packages
mkdir ${HOME}/Arduino
mkdir ${HOME}/Arduino/libraries

# install arduino IDE
export PATH=$PATH:$GITHUB_WORKSPACE/bin
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh -s 0.11.0 2>&1
arduino-cli config init > /dev/null
arduino-cli core update-index > /dev/null
