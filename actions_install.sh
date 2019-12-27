#!/bin/bash

set -e

pip3 install clint pyserial setuptools adafruit-nrfutil
sudo apt install -fy cppcheck clang-format-9
sudo ln -s /usr/bin/clang-format-9 /usr/bin/clang-format