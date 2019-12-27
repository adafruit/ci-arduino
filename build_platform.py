import sys
import glob
import time
import os
from clint.textui import colored

# add user bin to path!
BUILD_DIR = ''
# add user bin to path!
try:
    BUILD_DIR = os.environ["TRAVIS_BUILD_DIR"]
except KeyError:
    pass # ok maybe we're on actions?
try:
    BUILD_DIR = os.environ["GITHUB_WORKSPACE"]
except KeyError:
    pass # ok maybe we're on travis?

os.environ["PATH"] += os.pathsep + BUILD_DIR + "/bin"
print("build dir:", BUILD_DIR)
os.system('pwd')
os.system('ls -lA')

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

BSP_URLS = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://dl.espressif.com/dl/package_esp32_index.json"


def install_platform(platform):
    print("Installing", platform, end=" ")
    if os.system("arduino-cli core install "+platform+" --additional-urls "+BSP_URLS+" > /dev/null") != 0:
        print(colored.red("FAILED to install "+platform))
        exit(-1)
    print(colored.green(CHECK))

def run_or_die(cmd, error):
    if os.system(cmd) != 0:
        print(colored.red(error))
        exit(-1)

################################ Install Arduino IDE
print()
print('#'*40)
print(colored.yellow("INSTALLING ARDUINO IDE"))
print('#'*40)

run_or_die('curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh', "FAILED to install arduino CLI")

# make all our directories we need for files and libraries
for directory in ("/.arduino15", "/.arduino15/packages",
                  "/Arduino", "/Arduino/libraries"):
    os.mkdir(os.environ["HOME"]+directory)

run_or_die('arduino-cli config init > /dev/null',
           "FAILED to configure arduino CLI")
run_or_die('arduino-cli core update-index > /dev/null',
           "FAILED to update arduino core")
run_or_die("arduino-cli core update-index --additional-urls "+BSP_URLS+
           " > /dev/null", "FAILED to update core indecies")

# link test library folder to the arduino libraries folder
os.symlink(BUILD_DIR, os.environ['HOME']+'/Arduino/libraries/Adafruit_Test_Library')


################################ Test platforms
platforms = sys.argv[1:]
success = 0

for platform in platforms:
    fqbn = ALL_PLATFORMS[platform]
    #print("building", platform, "full name", fqbn)
    print('#'*80)
    print(colored.yellow("SWITCHING TO "+fqbn), end='   ')
    install_platform(":".join(fqbn.split(':', 2)[0:2])) # take only first two elements
    print('#'*80)
    exampledir = BUILD_DIR+"/examples"
    for example in os.listdir(exampledir):
        for filename in os.listdir(exampledir+"/"+example):
            if filename.endswith(".ino"):
                print('\t'+filename, end=' ')
                cmd = 'arduino-cli compile --fqbn '+fqbn+" "+exampledir+"/"+example+"/"+filename
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                r = proc.wait()
                err = proc.stderr.read()
                out = proc.stdout.read()
                print("OUTPUT: ", out)
                print("ERROUT: ", err)

                if r == 0:
                    print(colored.green(CHECK))
                else:
                    print(colored.red(CROSS))
                    success = 1

exit(success)
