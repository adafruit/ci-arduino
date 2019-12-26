#!/usr/bin/python3

import sys
import glob
import time
import os

# install our deps here
os.system('pip3 install clint')
from clint.textui import colored

print("hi!")


ALL_PLATFORMS={
    # classic Arduino AVR
    "uno" : "arduino:avr:uno",
    "leonardo" : "arduino:avr:leonardo",
    "mega2560" : "arduino:avr:mega:cpu=atmega2560",
    # Arduino SAMD
    "zero" : "arduino:samd:arduino_zero_native",
    "cplayExpress" : "arduino:samd:adafruit_circuitplayground_m0",
    # Espressif
    "esp8266" : "esp8266:esp8266:huzzah:eesz=4M3M,xtal=80",
    "esp32" : "esp32:esp32:featheresp32:FlashFreq=80",
    # Adafruit AVR
    "trinket" : "adafruit:avr:trinket5",
    "gemma" : "arduino:avr:gemma",
    "cplayClassic" : "arduino:avr:circuitplay32u4cat",
    # Adafruit SAMD
    "m4" : "adafruit:samd:adafruit_metro_m4:speed=120",
    "cplayExpressAda" : "adafruit:samd:adafruit_circuitplayground_m0",
    # Adafruit nRF
    "cplayBluefruit" : "adafruit:nrf52:cplaynrf52840:softdevice=s140v6,debug=l0",
}
print(ALL_PLATFORMS)
########################################################################
print()
print('#'*40)
print(colored.yellow("INSTALLING ARDUINO IDE")
print('#'*40)

os.system('curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh')

