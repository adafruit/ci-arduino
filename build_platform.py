import sys
import glob
import time
import os
import subprocess
import collections

# optional wall option cause build failed if has warnings
BUILD_WALL = False
if "--wall" in sys.argv:
    BUILD_WALL = True
    sys.argv.remove("--wall")

# add user bin to path!
BUILD_DIR = ''
# add user bin to path!
try:
    # If we're on actions
    BUILD_DIR = os.environ["GITHUB_WORKSPACE"]
except KeyError:
    try:
        # If we're on travis
        BUILD_DIR = os.environ["TRAVIS_BUILD_DIR"]
    except KeyError:
        # If we're running on local machine
        BUILD_DIR = os.path.abspath(".")
        pass

# Get home directory
try:
    HOME = os.environ["HOME_DIR"]
except KeyError:
    HOME = os.environ["HOME"]

try:
    ARDUINO_LOCATION = os.environ["ARDUINO_LIB_DIR"]
except KeyError:
    ARDUINO_LOCATION = '/Arduino/libraries'

os.environ["PATH"] += os.pathsep + BUILD_DIR + "/bin"
print("build dir:", BUILD_DIR)

IS_LEARNING_SYS = False
if "Adafruit_Learning_System_Guides" in BUILD_DIR:
    print("Found learning system repo")
    IS_LEARNING_SYS = True
elif "METROX-Examples-and-Project-Sketches" in BUILD_DIR:
    print("Found MetroX Examples Repo")
    IS_LEARNING_SYS = True

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
    "magtag" : "esp32:esp32:adafruit_magtag29_esp32s2",
    "funhouse" : "esp32:esp32:adafruit_funhouse_esp32s2",
    "metroesp32s2" : "esp32:esp32:adafruit_metro_esp32s2",
    # Adafruit AVR
    "trinket_3v" : "adafruit:avr:trinket3",
    "trinket_5v" : "adafruit:avr:trinket5",
    "protrinket_3v" : "adafruit:avr:protrinket3",
    "protrinket_5v" : "adafruit:avr:protrinket5",
    "gemma" : "adafruit:avr:gemma",
    "flora" : "adafruit:avr:flora8",
    "feather32u4" : "adafruit:avr:feather32u4",
    "cpc" : "arduino:avr:circuitplay32u4cat",
    # Adafruit SAMD
    "gemma_m0" : "adafruit:samd:adafruit_gemma_m0",
    "trinket_m0" : "adafruit:samd:adafruit_trinket_m0",
    "feather_m0_express" : "adafruit:samd:adafruit_feather_m0_express",
    "feather_m4_can" : "adafruit:samd:adafruit_feather_m4_can:speed=120",
    "feather_m4_can_tinyusb" : "adafruit:samd:adafruit_feather_m4_can:speed=120,usbstack=tinyusb",
    "metro_m0" : "adafruit:samd:adafruit_metro_m0",
    "metro_m0_tinyusb" : "adafruit:samd:adafruit_metro_m0:usbstack=tinyusb",
    "metro_m4" : "adafruit:samd:adafruit_metro_m4:speed=120",
    "metro_m4_tinyusb" : "adafruit:samd:adafruit_metro_m4:speed=120,usbstack=tinyusb",
    "metro_m4_airliftlite" : "adafruit:samd:adafruit_metro_m4_airliftlite:speed=120",
    "metro_m4_airliftlite_tinyusb" : "adafruit:samd:adafruit_metro_m4_airliftlite:speed=120,usbstack=tinyusb",
    "pybadge" : "adafruit:samd:adafruit_pybadge_m4:speed=120",
    "pybadge_tinyusb" : "adafruit:samd:adafruit_pybadge_m4:speed=120,usbstack=tinyusb",
    "pygamer" : "adafruit:samd:adafruit_pygamer_m4:speed=120",
    "hallowing_m0" : "adafruit:samd:adafruit_hallowing",
    "hallowing_m4" : "adafruit:samd:adafruit_hallowing_m4:speed=120",
    "hallowing_m4_tinyusb" : "adafruit:samd:adafruit_hallowing_m4:speed=120,usbstack=tinyusb",
    "neotrellis_m4" : "adafruit:samd:adafruit_trellis_m4:speed=120",
    "monster_m4sk" : "adafruit:samd:adafruit_monster_m4sk:speed=120",
    "monster_m4sk_tinyusb" : "adafruit:samd:adafruit_monster_m4sk:speed=120,usbstack=tinyusb",
    "pyportal" : "adafruit:samd:adafruit_pyportal_m4:speed=120",
    "pyportal_tinyusb" : "adafruit:samd:adafruit_pyportal_m4:speed=120,usbstack=tinyusb",
    "pyportal_titano" : "adafruit:samd:adafruit_pyportal_m4_titano:speed=120",
    "pyportal_titano_tinyusb" : "adafruit:samd:adafruit_pyportal_m4_titano:speed=120,usbstack=tinyusb",
    "cpx_ada" : "adafruit:samd:adafruit_circuitplayground_m0",
    "grand_central" : "adafruit:samd:adafruit_grandcentral_m4:speed=120",
    "grand_central_tinyusb" : "adafruit:samd:adafruit_grandcentral_m4:speed=120,usbstack=tinyusb",
    "matrixportal" : "adafruit:samd:adafruit_matrixportal_m4:speed=120",
    "matrixportal_tinyusb" : "adafruit:samd:adafruit_matrixportal_m4:speed=120,usbstack=tinyusb",
    "neotrinkey_m0" : "adafruit:samd:adafruit_neotrinkey_m0",
    "rotarytrinkey_m0" : "adafruit:samd:adafruit_rotarytrinkey_m0",
    "neokeytrinkey_m0" : "adafruit:samd:adafruit_neokeytrinkey_m0",
    "slidetrinkey_m0" : "adafruit:samd:adafruit_slidetrinkey_m0",
    "proxlighttrinkey_m0" : "adafruit:samd:adafruit_proxlighttrinkey_m0",
    # Arduino nRF
    "microbit" : "sandeepmistry:nRF5:BBCmicrobit:softdevice=s130",
    # Adafruit nRF
    "nrf52832" : "adafruit:nrf52:feather52832:softdevice=s132v6,debug=l0",
    "nrf52840" : "adafruit:nrf52:feather52840:softdevice=s140v6,debug=l0",
    "cpb" : "adafruit:nrf52:cplaynrf52840:softdevice=s140v6,debug=l0",
    "clue" : "adafruit:nrf52:cluenrf52840:softdevice=s140v6,debug=l0",
    # RP2040 (Philhower)
    "pico_rp2040" : "rp2040:rp2040:rpipico:freq=125,flash=2097152_0",
    "pico_rp2040_tinyusb" : "rp2040:rp2040:rpipico:flash=2097152_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb",
    "feather_rp2040" : "rp2040:rp2040:adafruitfeather:freq=125,flash=8388608_0",
    "feather_rp2040_tinyusb" : "rp2040:rp2040:adafruit_feather:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb",
    # Attiny8xy (SpenceKonde)
    "attiny817" : "megaTinyCore:megaavr:atxy7:chip=817",
    "attiny816" : "megaTinyCore:megaavr:atxy6:chip=816",
    "attiny807" : "megaTinyCore:megaavr:atxy7:chip=807",
    "attiny806" : "megaTinyCore:megaavr:atxy6:chip=806",
    # groupings
    "main_platforms" : ("uno", "leonardo", "mega2560", "zero",
                        "esp8266", "esp32", "metro_m4", "trinket_m0"),
    "arcada_platforms" : ("pybadge", "pygamer", "hallowing_m4",
                          "cpb", "cpx_ada"),
    "rp2040_platforms" : ("pico_rp2040", "feather_rp2040")
}

BSP_URLS = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json,https://sandeepmistry.github.io/arduino-nRF5/package_nRF5_boards_index.json,https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json,http://drazzy.com/package_drazzy.com_index.json"

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
    if platform == "adafruit:avr":   # we have a platform dep
        install_platform("arduino:avr")
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
print("INSTALLING ARDUINO BOARDS")
ColorPrint.print_info('#'*40)

run_or_die("arduino-cli core update-index --additional-urls "+BSP_URLS+
           " > /dev/null", "FAILED to update core indecies")
print()

# link test library folder to the arduino libraries folder
if not IS_LEARNING_SYS:
    try:
        os.symlink(BUILD_DIR, HOME+ARDUINO_LOCATION+'/Adafruit_Test_Library')
    except FileExistsError:
        pass

################################ Install dependancies
our_name=None
try:
    if IS_LEARNING_SYS:
        libprop = open(BUILD_DIR+'/library.deps')
    else:
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
    print("No library dep or properties found!")
    pass  # no library properties

# Delete the existing library if we somehow downloaded
# due to dependancies
if our_name:
    run_or_die("arduino-cli lib uninstall \""+our_name+"\"", "Could not uninstall")

print("Libraries installed: ", glob.glob(HOME+ARDUINO_LOCATION+'/*'))

################################ Test platforms
platforms = []
success = 0

# expand groups:
for arg in sys.argv[1:]:
    platform = ALL_PLATFORMS.get(arg, None)
    if isinstance(platform, str):
        platforms.append(arg)
    elif isinstance(platform, collections.abc.Iterable):
        for p in platform:
            platforms.append(p)
    else:
        print("Unknown platform: ", arg)
        exit(-1)

def test_examples_in_folder(folderpath):
    global success
    for example in sorted(os.listdir(folderpath)):
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

        cmd = ['arduino-cli', 'compile', '--warnings', 'all', '--fqbn', fqbn, examplepath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        r = proc.wait()
        out = proc.stdout.read()
        err = proc.stderr.read()
        if r == 0 and not (err and BUILD_WALL == True):
            ColorPrint.print_pass(CHECK)
            if err:
                # also print out warning message
                ColorPrint.print_fail(err.decode("utf-8"))
        else:
            ColorPrint.print_fail(CROSS)
            ColorPrint.print_fail(out.decode("utf-8"))
            ColorPrint.print_fail(err.decode("utf-8"))
            success = 1

def test_examples_in_learningrepo(folderpath):
    global success
    for project in os.listdir(folderpath):
        projectpath = folderpath+"/"+project
        if os.path.isdir(learningrepo):
            test_examples_in_learningrepo(projectpath)
            continue
        if not projectpath.endswith(".ino"):
            continue
	    # found an INO!
        print('\t'+projectpath, end=' ')
        # check if we should SKIP
        skipfilename = folderpath+"/."+platform+".test.skip"
        onlyfilename = folderpath+"/."+platform+".test.only"
        if os.path.exists(skipfilename):
            ColorPrint.print_warn("skipping")
            continue
        elif glob.glob(folderpath+"/.*.test.only") and not os.path.exists(onlyfilename):
            ColorPrint.print_warn("skipping")
            continue

        cmd = ['arduino-cli', 'compile', '--warnings', 'all', '--fqbn', fqbn, projectpath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        r = proc.wait()
        out = proc.stdout.read()
        err = proc.stderr.read()
        if r == 0:
            ColorPrint.print_pass(CHECK)
            if err:
                # also print out warning message
                ColorPrint.print_fail(err.decode("utf-8"))
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
    if not IS_LEARNING_SYS:
        test_examples_in_folder(BUILD_DIR+"/examples")
    else:
        test_examples_in_folder(BUILD_DIR)
exit(success)
