import sys
import glob
import time
import os
import subprocess
import collections

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
#os.system('pwd')
#os.system('ls -lA')

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
    "metro_m0" : "adafruit:samd:adafruit_metro_m0",
    "metro_m0_tinyusb" : "adafruit:samd:adafruit_metro_m0:usbstack=tinyusb",
    "metro_m4" : "adafruit:samd:adafruit_metro_m4:speed=120",
    "metro_m4_tinyusb" : "adafruit:samd:adafruit_metro_m4:speed=120,usbstack=tinyusb",
    "metro_m4_airliftlite" : "adafruit:samd:adafruit_metro_m4_airliftlite:speed=120",
    "pybadge" : "adafruit:samd:adafruit_pybadge_m4:speed=120",
    "pygamer" : "adafruit:samd:adafruit_pygamer_m4:speed=120",
    "hallowing_m0" : "adafruit:samd:adafruit_hallowing",
    "hallowing_m4" : "adafruit:samd:adafruit_hallowing_m4:speed=120",
    "monster_m4sk" : "adafruit:samd:adafruit_monster_m4sk:speed=120",
    "pyportal" : "adafruit:samd:adafruit_pyportal_m4:speed=120",
    "pyportal_titano" : "adafruit:samd:adafruit_pyportal_m4_titano:speed=120",
    "cpx_ada" : "adafruit:samd:adafruit_circuitplayground_m0",
    # Arduino nRF
    "microbit" : "sandeepmistry:nRF5:BBCmicrobit:softdevice=s130",
    # Adafruit nRF
    "nrf52840" : "adafruit:nrf52:feather52840:softdevice=s140v6,debug=l0",
    "cpb" : "adafruit:nrf52:cplaynrf52840:softdevice=s140v6,debug=l0",
    # groupings
    "main_platforms" : ("uno", "leonardo", "mega2560", "zero",
                        "esp8266", "esp32", "metro_m4", "nrf52840"),
    "arcada_platforms" : ("pybadge", "pygamer", "hallowing_m4",
                          "cpb", "cpx_ada")
}

BSP_URLS = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://dl.espressif.com/dl/package_esp32_index.json,https://sandeepmistry.github.io/arduino-nRF5/package_nRF5_boards_index.json"

class ColorPrint:

    @staticmethod
    def print_fail(message, end = '\n'):
        sys.stdout.write('\x1b[1;31m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_pass(message, end = '\n'):
        sys.stdout.write('\x1b[1;32m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end = '\n'):
        sys.stdout.write('\x1b[1;33m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end = '\n'):
        sys.stdout.write('\x1b[1;34m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end = '\n'):
        sys.stdout.write('\x1b[1;37m' + message.strip() + '\x1b[0m' + end)


def install_platform(platform):
    print("Installing", platform, end=" ")
    if platform == "adafruit:samd":   # we have a platform dep
        install_platform("arduino:samd")
    if os.system("arduino-cli core install "+platform+" --additional-urls "+BSP_URLS+" > /dev/null") != 0:
        ColorPrint.print_fail("FAILED to install "+platform)
        exit(-1)
    ColorPrint.print_pass(CHECK)

def run_or_die(cmd, error):
    print(cmd)
    if os.system(cmd) != 0:
        ColorPrint.print_fail(error)
        exit(-1)

################################ Install Arduino IDE
print()
ColorPrint.print_info('#'*40)
print("INSTALLING ARDUINO IDE")
ColorPrint.print_info('#'*40)

run_or_die('curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh 2>&1', "FAILED to install arduino CLI")
run_or_die('arduino-cli config init > /dev/null',
           "FAILED to configure arduino CLI")
run_or_die('arduino-cli core update-index > /dev/null',
           "FAILED to update arduino core")
run_or_die("arduino-cli core update-index --additional-urls "+BSP_URLS+
           " > /dev/null", "FAILED to update core indecies")
print()

# link test library folder to the arduino libraries folder
os.symlink(BUILD_DIR, os.environ['HOME']+'/Arduino/libraries/Adafruit_Test_Library')

################################ Install dependancies
our_name=None
try:
    libprop = open(BUILD_DIR+'/library.properties')
    for line in libprop:
        if line.startswith("name="):
            our_name = line.replace("name=", "").strip()
        if line.startswith("depends="):
            deps = line.replace("depends=", "").split(",")
            for dep in deps:
                dep = dep.strip()
                print("Installing "+dep)
                run_or_die('arduino-cli lib install "'+dep+'" > /dev/null',
                           "FAILED to install dependancy "+dep)
except OSError:
    pass  # no library properties

# Delete the existing library if we somehow downloaded
# due to dependancies
if our_name:
    run_or_die("arduino-cli lib uninstall \""+our_name+"\"", "Could not uninstall")

print("Libraries installed: ", glob.glob(os.environ['HOME']+'/Arduino/libraries/*'))

################################ Test platforms
platforms = []
success = 0

# expand groups:
for arg in sys.argv[1:]:
    platform = ALL_PLATFORMS.get(arg, None)
    if isinstance(platform, str):
        platforms.append(arg)
    elif isinstance(platform, collections.Iterable):
        for p in platform:
            platforms.append(p)
    else:
        print("Unknown platform: ", arg)
        exit(-1)

def test_examples_in_folder(folderpath):
    global success
    for example in os.listdir(folderpath):
        examplepath = folderpath+"/"+example
        if os.path.isdir(examplepath):
            test_examples_in_folder(examplepath)
            continue
        if not examplepath.endswith(".ino"):
            continue

        print('\t'+example, end=' ')
        # check if we should SKIP
        skipfilename = folderpath+"/."+platform+".test.skip"
        onlyfilename = folderpath+"/."+platform+".test.only"
        if os.path.exists(skipfilename):
            ColorPrint.print_warn("skipping")
            continue
        if glob.glob(folderpath+"/.*.test.only") and not os.path.exists(onlyfilename):
            ColorPrint.print_warn("skipping")
            continue

        cmd = ['arduino-cli', 'compile', '--fqbn', fqbn, examplepath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        r = proc.wait()
        out = proc.stdout.read()
        err = proc.stderr.read()
        if r == 0:
            ColorPrint.print_pass(CHECK)
        else:
            ColorPrint.print_fail(CROSS)
            ColorPrint.print_fail(out.decode("utf-8"))
            ColorPrint.print_fail(err.decode("utf-8"))
            success = 1

for platform in platforms:
    fqbn = ALL_PLATFORMS[platform]
    print('#'*80)
    ColorPrint.print_info("SWITCHING TO "+fqbn)
    install_platform(":".join(fqbn.split(':', 2)[0:2])) # take only first two elements
    print('#'*80)
    test_examples_in_folder(BUILD_DIR+"/examples")

exit(success)
