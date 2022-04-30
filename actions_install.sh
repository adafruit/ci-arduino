#!/bin/bash

set -e

pip3 install clint pyserial setuptools adafruit-nrfutil
sudo apt-get -o Acquire::Retries=3 install -y libllvm8 -V

sudo apt install -fy cppcheck clang-format-8
if [ ! -f /usr/bin/clang-format ]; then
    sudo ln -s /usr/bin/clang-format-8 /usr/bin/clang-format
fi

# make all our directories we need for files and libraries
mkdir ${HOME}/.arduino15
mkdir ${HOME}/.arduino15/packages
mkdir ${HOME}/Arduino
mkdir ${HOME}/Arduino/libraries

# install arduino IDE
export PATH=$PATH:$GITHUB_WORKSPACE/bin
echo $GITHUB_WORKSPACE/bin >> $GITHUB_PATH
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
arduino-cli config init > /dev/null
arduino-cli core update-index > /dev/null
