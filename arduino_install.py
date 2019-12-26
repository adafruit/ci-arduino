#!/usr/bin/python3

import sys
import glob
import time
import os
from clint.textui import colored

# add user bin to path!
os.environ["PATH"] += os.pathsep + os.environ["TRAVIS_BUILD_DIR"] + "/bin"

########################################################################
print()
print('#'*40)
print(colored.yellow("INSTALLING ARDUINO IDE"))
print('#'*40)

print("build dir:", os.environ["TRAVIS_BUILD_DIR"])

if os.system('curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh') != 0:
    print(colored.red("FAILED to install arduino CLI"))
    exit(-1)

os.mkdir(os.environ["HOME"]+"/.arduino15")
os.mkdir(os.environ["HOME"]+"/.arduino15/packages")

if os.system('arduino-cli config init') != 0:
    print(colored.red("FAILED to configure arduino CLI"))
    exit(-1)

if os.system('arduino-cli core update-index') != 0:
    print(colored.red("FAILED to update arduino core"))
    exit(-1)

# Try installing a library
if os.system('arduino-cli lib install "Adafruit NeoPixel"') != 0:
    print(colored.red("FAILED to install a library"))
    exit(-1) 

os.system('ls -lA')
os.system('ls -lA ~/Arduino')
os.system('ls -lA ~/.arduino15')

# link test library folder to the arduino libraries folder
os.symlink(os.environ['TRAVIS_BUILD_DIR'], '~/Arduino/libraries/Adafruit_Test_Library')
# Todo install dependencies

