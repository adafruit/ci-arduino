import sys
import glob
import time
import os
from clint.textui import colored

# add user bin to path!
os.environ["PATH"] += os.pathsep + os.environ["TRAVIS_BUILD_DIR"] + "/bin"

CROSS = u'\N{cross mark}'
CHECK = u'\N{check mark}'

ALL_PLATFORMS={
    # classic Arduino AVR
    "uno" : "arduino:avr:uno",
    "leonardo" : "arduino:avr:leonardo",
    "mega2560" : "arduino:avr:mega:cpu=atmega2560",
    # Arduino SAMD
    "zero" : "arduino:samd:arduino_zero_native",
    "cpx" : "arduino:samd:adafruit_circuitplayground_m0",
    # Espressif
    "esp8266" : "esp8266:esp8266:huzzah:eesz=4M3M,xtal=80",
    "esp32" : "esp32:esp32:featheresp32:FlashFreq=80",
    # Adafruit AVR
    "trinket" : "adafruit:avr:trinket5",
    "gemma" : "arduino:avr:gemma",
    "cpc" : "arduino:avr:circuitplay32u4cat",
    # Adafruit SAMD
    "m4" : "adafruit:samd:adafruit_metro_m4:speed=120",
    "cpx_ada" : "adafruit:samd:adafruit_circuitplayground_m0",
    # Adafruit nRF
    "cpb" : "adafruit:nrf52:cplaynrf52840:softdevice=s140v6,debug=l0",
}
#print(ALL_PLATFORMS)


def install_platform(platform):
    bsp_urls = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://dl.espressif.com/dl/package_esp32_index.json"
    print("Installing", platform, end=" ")
    ret = os.system('arduino-cli core install '+platform+' > /dev/null')
    if ret != 0:
        print(colored.red("FAILED to install "+platform))
        exit(-1)
    print(colored.green(CHECK))

platforms = sys.argv[1:]
for platform in platforms:
    fqbn = ALL_PLATFORMS[platform]
    #print("building", platform, "full name", fqbn)
    print('#'*40)
    print(colored.yellow("SWITCHING TO "+fqbn))
    install_platform(":".join(fqbn.split(':', 2)[0:2])) # take only first two elements
    print('#'*40)
    exampledir = os.environ['TRAVIS_BUILD_DIR']+"/examples"
    for example in os.listdir(exampledir):
        for filename in os.listdir(exampledir+"/"+example):
            if filename.endswith(".ino"):
                print('\t'+filename, end=' ')
                r = os.system('arduino-cli compile --fqbn '+fqbn+" "+exampledir+"/"+example+"/"+filename+' > /dev/null')
                if r == 0:
                    print(colored.green(CHECK))
                else:
                    print(colored.red(FAIL))
                    
