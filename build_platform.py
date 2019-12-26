import sys
import glob
import time
import os
from clint.textui import colored

# add user bin to path!
os.environ["PATH"] += os.pathsep + os.environ["TRAVIS_BUILD_DIR"] + "/bin"

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
#print(ALL_PLATFORMS)


ESP8266_INSTALLED = False
def install_esp8266():
    ESP8266_INSTALLED = (os.system('arduino_cli core install esp8266:esp8266') != 0)
    if not ESP8266_INSTALLED:
        print(colored.red("FAILED to install ESP8266"))
        exit(-1)

platforms = sys.argv[1:]
for platform in platforms:
    fqbn = ALL_PLATFORMS[platform]
    print("building", platform, "full name", fqbn)
    print('#'*40)
    print(colored.yellow("SWITCHING TO "+fqbn))
    print('#'*40)
    exampledir = os.environ['TRAVIS_BUILD_DIR']+"/examples"
    for example in os.listdir(exampledir):
        for filename in os.listdir(exampledir+"/"+example):
            if filename.endswith(".ino"):
                print(filename)
                # print(os.path.join(directory, filename))
                os.system('arduino-cli compile --fqbn '+fqbn+" "+filename)
    
