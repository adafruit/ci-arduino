import sys
import glob
import time
import os
import shutil
import subprocess
import collections
from contextlib import contextmanager

# optional wall option cause build failed if has warnings
BUILD_WALL = False
BUILD_WARN = True
if "--wall" in sys.argv:
    BUILD_WALL = True
    sys.argv.remove("--wall")

if "--no_warn" in sys.argv:
    BUILD_WARN = False
    sys.argv.remove("--no_warn")

# optional timeout argument to extend build time
# for larger sketches or firmware builds
BUILD_TIMEOUT = False
if "--build_timeout" in sys.argv:
    BUILD_TIMEOUT = True
    popen_timeout = int(sys.argv[sys.argv.index("--build_timeout") + 1])
    sys.argv.pop(sys.argv.index("--build_timeout") + 1)
    sys.argv.remove("--build_timeout")

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

os.environ["PATH"] += os.pathsep + BUILD_DIR + "/bin"
print("build dir:", BUILD_DIR)

IS_LEARNING_SYS = False
if "Adafruit_Learning_System_Guides" in BUILD_DIR:
    print("Found learning system repo")
    IS_LEARNING_SYS = True
    shutil.rmtree(BUILD_DIR + "/ci/examples/Blink")
elif "METROX-Examples-and-Project-Sketches" in BUILD_DIR:
    print("Found MetroX Examples Repo")
    IS_LEARNING_SYS = True

#os.system('pwd')
#os.system('ls -lA')

CROSS = u'\N{cross mark}'
CHECK = u'\N{check mark}'

ALL_PLATFORMS={
    # classic Arduino AVR
    "uno" : ["arduino:avr:uno", None, None],
    "leonardo" : ["arduino:avr:leonardo", None, None],
    "mega2560" : ["arduino:avr:mega:cpu=atmega2560", None, None],
    # Arduino SAMD
    "zero" : ["arduino:samd:arduino_zero_native", "0x68ed2b88", None, None],
    "cpx" : ["arduino:samd:adafruit_circuitplayground_m0", "0x68ed2b88", None],
    # Arduino mbed
    "pi_pico" : ["arduino:mbed_rp2040:pico", None, None],
    # Espressif
    "esp8266" : ["esp8266:esp8266:huzzah:eesz=4M3M,xtal=80", None, None],
    "esp32" : ["esp32:esp32:featheresp32:FlashFreq=80", None, None],
    "feather_esp8266" : ["esp8266:esp8266:huzzah:xtal=80,vt=flash,exception=disabled,stacksmash=disabled,ssl=all,mmu=3232,non32xfer=fast,eesz=4M2M,ip=lm2f,dbg=Disabled,lvl=None____,wipe=none,baud=115200", None, None],
    "feather_esp32" : ["esp32:esp32:featheresp32:FlashFreq=80", None, None],
    "feather_esp32_v2" : ["esp32:esp32:adafruit_feather_esp32_v2", None, None],
    "magtag" : ["esp32:esp32:adafruit_magtag29_esp32s2", "0xbfdd4eee", None],
    "funhouse" : ["esp32:esp32:adafruit_funhouse_esp32s2", "0xbfdd4eee", None],
    "metroesp32s2" : ["esp32:esp32:adafruit_metro_esp32s2", "0xbfdd4eee", None],
    "qtpy_esp32s2" : ["esp32:esp32:adafruit_qtpy_esp32s2", "0xbfdd4eee", None],
    "feather_esp32s2" : ["esp32:esp32:adafruit_feather_esp32s2", "0xbfdd4eee", None],
    "feather_esp32s2_tft" : ["esp32:esp32:adafruit_feather_esp32s2_tft", "0xbfdd4eee", None],
    "feather_esp32s2_reverse_tft" : ["esp32:esp32:adafruit_feather_esp32s2_reversetft", "0xbfdd4eee", None],
    "feather_esp32s3" : ["esp32:esp32:adafruit_feather_esp32s3_nopsram", "0xc47e5767", None],
    "feather_esp32s3_4mbflash_2mbpsram" : ["esp32:esp32:adafruit_feather_esp32s3", "0xc47e5767", None],
    "feather_esp32s3_tft" : ["esp32:esp32:adafruit_feather_esp32s3_tft", "0xc47e5767", None],
    "feather_esp32s3_reverse_tft" : ["esp32:esp32:adafruit_feather_esp32s3_reversetft", "0xc47e5767", None],
    "matrixportal_s3" : ["esp32:esp32:adafruit_matrixportal_esp32s3", "0xc47e5767", None],
    "qtpy_esp32s3" : ["esp32:esp32:adafruit_qtpy_esp32s3_nopsram", "0xc47e5767", None],
    "qtpy_esp32s3_n4r2" : ["esp32:esp32:adafruit_qtpy_esp32s3_n4r2", "0xc47e5767", None],
    "qtpy_esp32" : ["esp32:esp32:adafruit_qtpy_esp32_pico", None, None],
    "qtpy_esp32c3" : ["esp32:esp32:adafruit_qtpy_esp32c3:FlashMode=qio", None, None],
    # Adafruit AVR
    "trinket_3v" : ["adafruit:avr:trinket3", None, None],
    "trinket_5v" : ["adafruit:avr:trinket5", None, None],
    "protrinket_3v" : ["adafruit:avr:protrinket3", None, None],
    "protrinket_5v" : ["adafruit:avr:protrinket5", None, None],
    "gemma" : ["adafruit:avr:gemma", None, None],
    "flora" : ["adafruit:avr:flora8", None, None],
    "feather32u4" : ["adafruit:avr:feather32u4", None, None],
    "cpc" : ["arduino:avr:circuitplay32u4cat", None, None],
    # Adafruit SAMD
    "gemma_m0" : ["adafruit:samd:adafruit_gemma_m0", "0x68ed2b88", None],
    "trinket_m0" : ["adafruit:samd:adafruit_trinket_m0", "0x68ed2b88", None],
    "feather_m0_express" : ["adafruit:samd:adafruit_feather_m0_express", "0x68ed2b88", None],
    "feather_m0_express_tinyusb" : ["adafruit:samd:adafruit_feather_m0_express:usbstack=tinyusb", "0x68ed2b88", None],
    "feather_m4_express" : ["adafruit:samd:adafruit_feather_m4:speed=120", "0x55114460", None],
    "feather_m4_express_tinyusb" : ["adafruit:samd:adafruit_feather_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "feather_m4_can" : ["adafruit:samd:adafruit_feather_m4_can:speed=120", "0x55114460", None],
    "feather_m4_can_tinyusb" : ["adafruit:samd:adafruit_feather_m4_can:speed=120,usbstack=tinyusb", "0x55114460", None],
    "metro_m0" : ["adafruit:samd:adafruit_metro_m0", "0x68ed2b88", None],
    "metro_m0_tinyusb" : ["adafruit:samd:adafruit_metro_m0:usbstack=tinyusb", "0x68ed2b88", None],
    "metro_m4" : ["adafruit:samd:adafruit_metro_m4:speed=120", "0x55114460", None],
    "metro_m4_tinyusb" : ["adafruit:samd:adafruit_metro_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "metro_m4_airliftlite" : ["adafruit:samd:adafruit_metro_m4_airliftlite:speed=120", "0x55114460", None],
    "metro_m4_airliftlite_tinyusb" : ["adafruit:samd:adafruit_metro_m4_airliftlite:speed=120,usbstack=tinyusb", "0x55114460", None],
    "pybadge" : ["adafruit:samd:adafruit_pybadge_m4:speed=120", "0x55114460", None],
    "pybadge_tinyusb" : ["adafruit:samd:adafruit_pybadge_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "pygamer" : ["adafruit:samd:adafruit_pygamer_m4:speed=120", "0x55114460", None],
    "pygamer_tinyusb" : ["adafruit:samd:adafruit_pygamer_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "hallowing_m0" : ["adafruit:samd:adafruit_hallowing", "0x68ed2b88", None],
    "hallowing_m4" : ["adafruit:samd:adafruit_hallowing_m4:speed=120", "0x55114460", None],
    "hallowing_m4_tinyusb" : ["adafruit:samd:adafruit_hallowing_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "neotrellis_m4" : ["adafruit:samd:adafruit_trellis_m4:speed=120", "0x55114460", None],
    "monster_m4sk" : ["adafruit:samd:adafruit_monster_m4sk:speed=120", "0x55114460", None],
    "monster_m4sk_tinyusb" : ["adafruit:samd:adafruit_monster_m4sk:speed=120,usbstack=tinyusb", "0x55114460", None],
    "pyportal" : ["adafruit:samd:adafruit_pyportal_m4:speed=120", "0x55114460", None],
    "pyportal_tinyusb" : ["adafruit:samd:adafruit_pyportal_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "pyportal_titano" : ["adafruit:samd:adafruit_pyportal_m4_titano:speed=120", "0x55114460", None],
    "pyportal_titano_tinyusb" : ["adafruit:samd:adafruit_pyportal_m4_titano:speed=120,usbstack=tinyusb", "0x55114460", None],
    "cpx_ada" : ["adafruit:samd:adafruit_circuitplayground_m0", "0x68ed2b88", None],
    "grand_central" : ["adafruit:samd:adafruit_grandcentral_m4:speed=120", "0x55114460", None],
    "grand_central_tinyusb" : ["adafruit:samd:adafruit_grandcentral_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "matrixportal" : ["adafruit:samd:adafruit_matrixportal_m4:speed=120", "0x55114460", None],
    "matrixportal_tinyusb" : ["adafruit:samd:adafruit_matrixportal_m4:speed=120,usbstack=tinyusb", "0x55114460", None],
    "neotrinkey_m0" : ["adafruit:samd:adafruit_neotrinkey_m0", "0x68ed2b88", None],
    "rotarytrinkey_m0" : ["adafruit:samd:adafruit_rotarytrinkey_m0", "0x68ed2b88", None],
    "neokeytrinkey_m0" : ["adafruit:samd:adafruit_neokeytrinkey_m0", "0x68ed2b88", None],
    "slidetrinkey_m0" : ["adafruit:samd:adafruit_slidetrinkey_m0", "0x68ed2b88", None],
    "proxlighttrinkey_m0" : ["adafruit:samd:adafruit_proxlighttrinkey_m0", "0x68ed2b88", None],
    "qtpy_m0" : ["adafruit:samd:adafruit_qtpy_m0", "0x68ed2b88", None],
    "qtpy_m0_tinyusb" : ["adafruit:samd:adafruit_qtpy_m0:usbstack=tinyusb", "0x68ed2b88", None],
    # Arduino SAMD
    "mkrwifi1010" : ["arduino:samd:mkrwifi1010", "0x8054", None],
    "nano_33_iot" : ["arduino:samd:nano_33_iot", "0x8057", None],
    # Arduino nRF
    "microbit" : ["sandeepmistry:nRF5:BBCmicrobit:softdevice=s110", None, None],
    # Adafruit nRF
    "nrf52832" : ["adafruit:nrf52:feather52832:softdevice=s132v6,debug=l0", None, None],
    "nrf52840" : ["adafruit:nrf52:feather52840:softdevice=s140v6,debug=l0", "0xada52840", None],
    "cpb" : ["adafruit:nrf52:cplaynrf52840:softdevice=s140v6,debug=l0", "0xada52840", None],
    "clue" : ["adafruit:nrf52:cluenrf52840:softdevice=s140v6,debug=l0", "0xada52840", None],
    "ledglasses_nrf52840" : ["adafruit:nrf52:ledglasses_nrf52840:softdevice=s140v6,debug=l0", "0xada52840", None],
    # RP2040 (Philhower)
    "pico_rp2040" : ["rp2040:rp2040:rpipico:freq=125,flash=2097152_0", "0xe48bff56", None],
    "pico_rp2040_tinyusb" : ["rp2040:rp2040:rpipico:flash=2097152_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "picow_rp2040" : ["rp2040:rp2040:rpipicow:flash=2097152_0,freq=125", "0xe48bff56", None],
    "picow_rp2040_tinyusb" : ["rp2040:rp2040:rpipicow:flash=2097152_131072,freq=133,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "feather_rp2040" : ["rp2040:rp2040:adafruit_feather:freq=125,flash=8388608_0", "0xe48bff56", None],
    "feather_rp2040_tinyusb" : ["rp2040:rp2040:adafruit_feather:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "feather_rp2040_rfm" : ["rp2040:rp2040:adafruit_feather_rfm:freq=125,flash=8388608_0", "0xe48bff56", None],
    "feather_rp2040_rfm_tinyusb" : ["rp2040:rp2040:adafruit_feather_rfm:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "feather_rp2040_dvi" : ["rp2040:rp2040:adafruit_feather_dvi:freq=125,flash=8388608_0", "0xe48bff56", None],
    "feather_rp2040_dvi_tinyusb" : ["rp2040:rp2040:adafruit_feather_dvi:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "feather_rp2040_usbhost_tinyusb" : ["rp2040:rp2040:adafruit_feather_usb_host:flash=8388608_0,freq=120,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "qt2040_trinkey" : ["rp2040:rp2040:adafruit_trinkeyrp2040qt:freq=125,flash=8388608_0", "0xe48bff56", None],
    "qt2040_trinkey_tinyusb" : ["rp2040:rp2040:adafruit_trinkeyrp2040qt:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],
    "qt_py_rp2040": ["rp2040:rp2040:adafruit_qtpy:freq=125,flash=8388608_0", "0xe48bff56", None],
    "qt_py_rp2040_tinyusb": ["rp2040:rp2040:adafruit_qtpy:flash=8388608_0,freq=125,dbgport=Disabled,dbglvl=None,usbstack=tinyusb", "0xe48bff56", None],

    # Attiny8xy, 16xy, 32xy (SpenceKonde)
    "attiny3217" : ["megaTinyCore:megaavr:atxy7:chip=3217", None, None],
    "attiny3216" : ["megaTinyCore:megaavr:atxy6:chip=3216", None, None],
    "attiny1617" : ["megaTinyCore:megaavr:atxy7:chip=1617", None, None],
    "attiny1616" : ["megaTinyCore:megaavr:atxy6:chip=1616", None, None],
    "attiny1607" : ["megaTinyCore:megaavr:atxy7:chip=1607", None, None],
    "attiny1606" : ["megaTinyCore:megaavr:atxy6:chip=1606", None, None],
    "attiny817" : ["megaTinyCore:megaavr:atxy7:chip=817", None, None],
    "attiny816" : ["megaTinyCore:megaavr:atxy6:chip=816", None, None],
    "attiny807" : ["megaTinyCore:megaavr:atxy7:chip=807", None, None],
    "attiny806" : ["megaTinyCore:megaavr:atxy6:chip=806", None, None],
    # groupings
    "main_platforms" : ("uno", "leonardo", "mega2560", "zero", "qtpy_m0",
                        "esp8266", "esp32", "metro_m4", "trinket_m0"),
    "arcada_platforms" : ("pybadge", "pygamer", "hallowing_m4",
                          "cpb", "cpx_ada"),
    "wippersnapper_platforms" : ("metro_m4_airliftlite_tinyusb", "pyportal_tinyusb"),
    "rp2040_platforms" : ("pico_rp2040", "feather_rp2040")
}

BSP_URLS = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json,https://sandeepmistry.github.io/arduino-nRF5/package_nRF5_boards_index.json,https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json"

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

def manually_install_esp32_bsp(repo_info):
    print("Manually installing latest ESP32 BSP...")
    # Assemble git url
    repo_url = "git clone -b {0} https://github.com/{1}/arduino-esp32.git esp32".format(repo_info.split("/")[1], repo_info.split("/")[0])
    # Locally clone repo (https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html#linux)
    os.system("mkdir -p /home/runner/Arduino/hardware/espressif")
    print("Cloning %s"%repo_url)
    cmd = "cd /home/runner/Arduino/hardware/espressif && " + repo_url
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    r = proc.wait(timeout=1000)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if r != 0:
        ColorPrint.print_fail("Failed to download ESP32 Arduino BSP!")
        ColorPrint.print_fail(out.decode("utf-8"))
        ColorPrint.print_fail(err.decode("utf-8"))
        exit(-1)
    print(out)
    print("Cloned repository!")

    print("Installing ESP32 Arduino BSP...")
    cmd = "cd /home/runner/Arduino/hardware/espressif/esp32/tools && python3 get.py"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    r = proc.wait(timeout=1000)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if r != 0:
        ColorPrint.print_fail("Failed to install ESP32 Arduino BSP!")
        ColorPrint.print_fail(out.decode("utf-8"))
        ColorPrint.print_fail(err.decode("utf-8"))
        exit(-1)
    print(out)
    print("Installed ESP32 BSP from source!")

def install_platform(fqbn, full_platform_name=None):
    print("Installing", fqbn, end=" ")
    if fqbn == "adafruit:avr":   # we have a platform dep
        install_platform("arduino:avr", full_platform_name)
    if full_platform_name[2] is not None:
        manually_install_esp32_bsp(full_platform_name[2]) # build esp32 bsp from desired source and branch
    for retry in range(0, 3):
        if os.system("arduino-cli core install "+fqbn+" --additional-urls "+BSP_URLS+" > /dev/null") == 0:
            break
        print("...retrying...", end=" ")
        time.sleep(10) # wait 10 seconds then try again?
    else:
        # tried 3 times to no avail
        ColorPrint.print_fail("FAILED to install "+fqbn)
        exit(-1)
    ColorPrint.print_pass(CHECK)
    # print installed core version
    print(os.popen('arduino-cli core list | grep {}'.format(fqbn)).read(), end='')

def run_or_die(cmd, error):
    print(cmd)
    attempt = 0
    while attempt < 3:
        if os.system(cmd) == 0:
            return
        attempt += 1
        print('attempt {} failed, {} retry left'.format(attempt, 3-attempt))
        time.sleep(5)
    ColorPrint.print_fail(error)
    exit(-1)

################################ Install Arduino IDE
print()
ColorPrint.print_info('#'*40)
print("INSTALLING ARDUINO BOARDS")
ColorPrint.print_info('#'*40)

run_or_die("arduino-cli core update-index --additional-urls "+BSP_URLS+
           " > /dev/null", "FAILED to update core indices")
print()

################################ Install dependencies
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
                           "FAILED to install dependency "+dep)
except OSError:
    print("No library dep or properties found!")
    pass  # no library properties

# Delete the existing library if we somehow downloaded
# due to dependencies
if our_name:
    run_or_die("arduino-cli lib uninstall \""+our_name+"\"", "Could not uninstall")

print("Libraries installed: ", glob.glob(os.environ['HOME']+'/Arduino/libraries/*'))

# link our library folder to the arduino libraries folder
if not IS_LEARNING_SYS:
    try:
        os.symlink(BUILD_DIR, os.environ['HOME']+'/Arduino/libraries/' + os.path.basename(BUILD_DIR))
    except FileExistsError:
        pass

################################ UF2 Utils.

def glob01(pattern):
    result = glob.glob(pattern)
    if len(result) > 1:
        raise RuntimeError(f"Required pattern {pattern} to match at most 1 file, got {result}")
    return result[0] if result else None

def glob1(pattern):
    result = glob.glob(pattern)
    if len(result) != 1:
        raise RuntimeError(f"Required pattern {pattern} to match exactly 1 file, got {result}")
    return result[0]

def download_uf2_utils():
    """Downloads uf2conv tools if we don't already have them
    """
    cmd = "wget -nc --no-check-certificate http://raw.githubusercontent.com/microsoft/uf2/master/utils/uf2families.json https://raw.githubusercontent.com/microsoft/uf2/master/utils/uf2conv.py"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    r = proc.wait(timeout=60)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if r != 0:
        ColorPrint.print_fail("Failed to download UF2 Utils!")
        ColorPrint.print_fail(out.decode("utf-8"))
        ColorPrint.print_fail(err.decode("utf-8"))
        return False
    return True

def generate_uf2(example_path):
    """Generates a .uf2 file from a .bin or .hex file.
    :param str example_path: A path to the compiled .bin or .hex file.

    """
    if not download_uf2_utils():
        return None

    cli_build_uf2_path = "build/*.*." + fqbn.split(':')[2] + "/*.uf2"
    uf2_input_file = glob01(os.path.join(example_path, cli_build_uf2_path))

    # Some platforms, like rp2040, directly generate a uf2 file, so no need to do it ourselves
    if uf2_input_file is not None:
        output_file = os.path.splitext(uf2_input_file)[0] + ".uf2"
        ColorPrint.print_pass(CHECK)
        ColorPrint.print_info("Used uf2 generated by arduino-cli")
        return output_file

    # Generate using a hex file for all platforms except for ESP32-S2, ESP32-S3 (exports as .bin files)
    if not any (x in fqbn for x in ["esp32s2", "esp32s3"]):
        cli_build_hex_path = "build/*.*." + fqbn.split(':')[2] + "/*.hex"
        hex_input_file = glob1(os.path.join(example_path, cli_build_hex_path))
        output_file = os.path.splitext(hex_input_file)[0] + ".uf2"
        family_id = ALL_PLATFORMS[platform][1]
        cmd = ['python3', 'uf2conv.py', hex_input_file, '-c', '-f', family_id, '-o', output_file]
    else:
        cli_build_path = "build/*.*." + fqbn.split(':')[2] + "/*.ino.bin"
        input_file = glob1(os.path.join(example_path, cli_build_path))
        output_file = os.path.splitext(input_file)[0] + ".uf2"
        family_id = ALL_PLATFORMS[platform][1]
        cmd = ['python3', 'uf2conv.py', input_file, '-c', '-f', family_id, '-b', "0x0000", '-o', output_file]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if BUILD_TIMEOUT:
        r = proc.wait(timeout=popen_timeout)
    else:
        r = proc.wait(timeout=60)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if r == 0 and not err:
        ColorPrint.print_pass(CHECK)
        ColorPrint.print_info(out.decode("utf-8"))
    else:
        ColorPrint.print_fail(CROSS)
        ColorPrint.print_fail(out.decode("utf-8"))
        ColorPrint.print_fail(err.decode("utf-8"))
        return None
    return output_file

################################ Test platforms
platforms = []
success = 0

# expand groups:
for arg in sys.argv[1:]:
    platform = ALL_PLATFORMS.get(arg, None)
    if isinstance(platform, list):
        platforms.append(arg)
    elif isinstance(platform, tuple):
        for p in platform:
            platforms.append(p)
    else:
        print("Unknown platform: ", arg)
        exit(-1)

@contextmanager
def group_output(title):
    sys.stdout.flush()
    sys.stderr.flush()
    print(f"::group::{title}")
    try:
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        print(f"::endgroup::")
        sys.stdout.flush()


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
        # check if we should GENERATE UF2
        gen_file_name = folderpath+"/."+platform+".generate"
        if os.path.exists(skipfilename):
            ColorPrint.print_warn("skipping")
            continue
        if glob.glob(folderpath+"/.*.test.only"):
            platformname = glob.glob(folderpath+"/.*.test.only")[0].split('.')[1]
            if platformname != "none" and not platformname in ALL_PLATFORMS:
                # uh oh, this isnt a valid testonly!
                ColorPrint.print_fail(CROSS)
                ColorPrint.print_fail("This example does not have a valid .platform.test.only file")
                success = 1
                continue
            if not os.path.exists(onlyfilename):
                ColorPrint.print_warn("skipping")
                continue
        if os.path.exists(gen_file_name):
            ColorPrint.print_info("generating")

        if BUILD_WARN:
            if os.path.exists(gen_file_name):
                cmd = ['arduino-cli', 'compile', '--warnings', 'all', '--fqbn', fqbn, '-e', folderpath]
            else:
                cmd = ['arduino-cli', 'compile', '--warnings', 'all', '--fqbn', fqbn, folderpath]
        else:
            cmd = ['arduino-cli', 'compile', '--warnings', 'none', '--export-binaries', '--fqbn', fqbn, folderpath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        try:
            if BUILD_TIMEOUT:
                out, err = proc.communicate(timeout=popen_timeout)
            else:
                out, err = proc.communicate(timeout=120)
            r = proc.returncode
        except:
            proc.kill()
            out, err = proc.communicate()
            r = 1

        if r == 0 and not (err and BUILD_WALL == True):
            ColorPrint.print_pass(CHECK)
            if err:
                # also print out warning message
                with group_output(f"{example} {fqbn} build output"):
                    ColorPrint.print_fail(err.decode("utf-8"))
            if os.path.exists(gen_file_name):
                if ALL_PLATFORMS[platform][1] == None:
                    ColorPrint.print_info("Platform does not support UF2 files, skipping...")
                else:
                    ColorPrint.print_info("Generating UF2...")
                    filename = generate_uf2(folderpath)
                    if filename is None:
                        success = 1  # failure
                    if IS_LEARNING_SYS:
                        fqbnpath, uf2file = filename.split("/")[-2:]
                        os.makedirs(BUILD_DIR+"/build", exist_ok=True)
                        os.makedirs(BUILD_DIR+"/build/"+fqbnpath, exist_ok=True)
                        shutil.copy(filename, BUILD_DIR+"/build/"+fqbnpath+"-"+uf2file)
                        os.system("ls -lR "+BUILD_DIR+"/build")
        else:
            ColorPrint.print_fail(CROSS)
            with group_output(f"{example} {fqbn} built output"):
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
        print('\t'+projectpath, end=' ', flush=True)
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
    fqbn = ALL_PLATFORMS[platform][0]
    print('#'*80)
    ColorPrint.print_info("SWITCHING TO "+fqbn)
    install_platform(":".join(fqbn.split(':', 2)[0:2]), ALL_PLATFORMS[platform]) # take only first two elements
    print('#'*80)
    if not IS_LEARNING_SYS:
        test_examples_in_folder(BUILD_DIR+"/examples")
    else:
        test_examples_in_folder(BUILD_DIR)
exit(success)
