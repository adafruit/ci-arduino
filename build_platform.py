import sys
import glob
import time
import os
import re
import shutil
import subprocess
import collections
from contextlib import contextmanager
from all_platforms import ALL_PLATFORMS

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

# optional wippersnapper argument to generate a dependencies header file
PRINT_DEPENDENCIES_AS_HEADER = False
INCLUDE_PRINT_DEPENDENCIES_HEADER = False
PRINT_DEPENDENCIES_AS_HEADER_FILENAME = None
if "--include_print_dependencies_header" in sys.argv:
    # check argument not null and folder path exists
    header_index = sys.argv.index("--include_print_dependencies_header") + 1
    PRINT_DEPENDENCIES_AS_HEADER_FILENAME = sys.argv[header_index] if len(sys.argv) > header_index else None
    if PRINT_DEPENDENCIES_AS_HEADER_FILENAME is None or not os.path.exists(PRINT_DEPENDENCIES_AS_HEADER_FILENAME):
        raise ValueError("Header file path not found or not provided to --include_print_dependencies_header argument")
    INCLUDE_PRINT_DEPENDENCIES_HEADER = True
    sys.argv.pop(header_index)
    sys.argv.remove("--include_print_dependencies_header")

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

CROSS = u'\N{cross mark}'
CHECK = u'\N{check mark}'

BSP_URLS = (
    "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,"
    "http://arduino.esp8266.com/stable/package_esp8266com_index.json,"
    "https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json,"
    "https://sandeepmistry.github.io/arduino-nRF5/package_nRF5_boards_index.json,"
    "https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json,"
    "https://drazzy.good-enough.cloud/package_drazzy.com_index.json,"
    "https://github.com/openwch/board_manager_files/raw/main/package_ch32v_index.json"
)

# global exit code
success = 0


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
    subprocess_result = subprocess.run("mkdir -p /home/runner/Arduino/hardware/espressif", shell=True)
    if subprocess_result.returncode != 0:
        ColorPrint.print_fail("Failed to create ESP32 Arduino BSP directory!\n" +
                              "Maybe the runner work location changed?\n" +
                              "Tried to create /home/runner/Arduino/hardware/espressif but failed: {}".format(subprocess_result.returncode))
        ColorPrint.print_fail(subprocess_result.stderr)
        exit(-1)
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
    print("Checking for drazzy.json (before moving)")
    if os.path.exists("/home/runner/.arduino15/package_drazzy.json"):
        print("Moving drazzy.json")
        shutil.move("/home/runner/.arduino15/package_drazzy.json", "/home/runner/.arduino15/package_drazzy.com_index.json")
    print("Installing", fqbn, " (", full_platform_name, ")", end=" ")
    if fqbn == "adafruit:avr":   # we have a platform dep
        install_platform("arduino:avr", full_platform_name)
    if full_platform_name[2] is not None:
        manually_install_esp32_bsp(full_platform_name[2]) # build esp32 bsp from desired source and branch
        print(os.popen('arduino-cli core list | grep {}'.format(fqbn)).read(), end='')
        return # bail out
    for retry in range(0, 3):
        print("arduino-cli core install "+fqbn+" --additional-urls "+BSP_URLS)
        if subprocess.run("arduino-cli core install "+fqbn+" --additional-urls "+BSP_URLS+" > /dev/null", shell=True, check=False).returncode == 0:
            break
        print("...retrying...", end=" ")
        time.sleep(10) # wait 10 seconds then try again?
    else:
        # tried 3 times to no avail
        ColorPrint.print_fail("FAILED to install "+fqbn)
        exit(-1)
    ColorPrint.print_pass(CHECK)
    # print installed core version
    result = subprocess.Popen('arduino-cli core list | grep {}'.format(fqbn), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result.stdout.read().decode(), end='')



def run_or_die(cmd, error):
    print(cmd)
    attempt = 0
    while attempt < 3:
        if subprocess.run(cmd, shell=True, check=False).returncode == 0:
            return
        attempt += 1
        print('attempt {} failed, {} retry left'.format(attempt, 3-attempt))
        time.sleep(5)
    ColorPrint.print_fail(error)
    exit(-1)


def is_library_installed(lib_name):
    try:
        installed_libs = subprocess.check_output("arduino-cli lib list", shell=True).decode("utf-8")
        return not all(not item for item in [re.match('^'+lib_name+'\\s*\\d+\\.', line) for line in installed_libs.split('\n')])
    except subprocess.CalledProcessError as e:
        print("Error checking installed libraries:", e)
        return False


def install_library_deps():
    print()
    ColorPrint.print_info('#'*40)
    print("INSTALLING ARDUINO LIBRARIES")
    ColorPrint.print_info('#'*40)

    run_or_die("arduino-cli core update-index --additional-urls "+BSP_URLS+
               " > /dev/null", "FAILED to update core indices")
    print()

    # Install dependencies
    our_name = None
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
                    if not is_library_installed(dep):
                        print("Installing "+dep)
                        run_or_die('arduino-cli lib install "'+dep+'" > /dev/null',
                                   "FAILED to install dependency "+dep)
                    else:
                        print("Skipping already installed lib: "+dep)
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


def generate_uf2(platform, fqbn, example_path):
    """Generates a .uf2 file from a .bin or .hex file.
    :param str platform: The platform name.
    :param str fqbn: The fully qualified board name.
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
        # ColorPrint.print_info(subprocess.check_output(["tree"]).decode("utf-8"))
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
    if r == 0: # and not err:  # we might get warnings that do not affect the result
        ColorPrint.print_pass(CHECK)
        ColorPrint.print_info(out.decode("utf-8"))
    else:
        ColorPrint.print_fail(CROSS)
        ColorPrint.print_fail("\n\rERRCODE:", str(r))
        ColorPrint.print_fail("\n\rOUTPUT: ", out.decode("utf-8"))
        ColorPrint.print_fail("\n\rERROR: ", err.decode("utf-8"))
        return None
    return output_file


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


def extract_dependencies(output):
    print("Extracting libraries from output:", output)
    print(f"{"############## Done #############":-^80}")

    IS_LIBS_FOUND = False
    IS_BSP_FOUND = False
    libraries = []
    platforms = []
    COLS = []
    for i,line in enumerate(output.split('\n')):
        if line.strip() == '':
            continue
        if not IS_LIBS_FOUND:
            if re.match(r'Used library', line):
                IS_LIBS_FOUND = True
                print("Found libraries token using regex")
                print("find Version:", line.find('Version'))
                print("find Path:", line.find('Path'))
                COLS = [0,line.find('Version'), line.find('Path')]
                continue
            else:
                if line.find("Used library") != -1:
                    print("Found libraries token using find")
                    IS_LIBS_FOUND = True
                    print("non regex find Version:", line.find('Version'))
                    print("find Path:", line.find('Path'))
                    COLS = [0,line.find('Version'), line.find('Path')]
        else:
            if not IS_BSP_FOUND:
                if re.match(r'Used platform', line):
                    print("Found platform token using regex")
                    IS_BSP_FOUND = True
                    COLS = [0,line.find('Version'), line.find('Path')]
                    continue
                elif line.find("Used platform") != -1:
                    print("Found platform token using find")
                    IS_BSP_FOUND = True
                    COLS = [0,line.find('Version'), line.find('Path')]
                    continue
                else:
                    libraries.append([line[:COLS[1]].strip(),line[COLS[1]:COLS[2]].strip()])
            else:
                platforms.append([line[:COLS[1]].strip(),line[COLS[1]:COLS[2]].strip()])
    
    dependencies = {
        'libraries': libraries,
        'platforms': platforms
    }
    print("Extracted list of dependencies:", dependencies)
    return dependencies

def write_dependencies_to_header(dependencies, output_file):
    # header file
    with open(output_file, 'w') as f:
        f.write('#ifndef PROJECT_DEPENDENCIES_H\n')
        f.write('#define PROJECT_DEPENDENCIES_H\n\n')
        f.write('#define PRINT_DEPENDENCIES 1\n')
        f.write('extern const char* project_dependencies;\n\n')
        f.write('#endif // PROJECT_DEPENDENCIES_H\n')
    # cpp file
    with open(re.sub(r'\.h$','.cpp', output_file), 'w') as f:
        f.write('#include "print_dependencies.h"\n\n')
        f.write('const char* project_dependencies = R"(\n')
        
        f.write('Libraries and Versions:\n')
        for lib in dependencies['libraries']:
            f.write(f'Library: {lib[0].strip()}, Version: {lib[1].strip()}\n')
        
        f.write('\nPlatforms and Versions:\n')
        for plat in dependencies['platforms']:
            f.write(f'Platform: {plat[0].strip()}, Version: {plat[1].strip()}\n')
        
        f.write(')";\n\n')

def test_examples_in_folder(platform, folderpath):
    global success, BUILD_TIMEOUT, popen_timeout, BUILD_WALL, BUILD_WARN, PRINT_DEPENDENCIES_AS_HEADER, INCLUDE_PRINT_DEPENDENCIES_HEADER, IS_LEARNING_SYS, BUILD_DIR
    fqbn = ALL_PLATFORMS[platform][0]
    for example in sorted(os.listdir(folderpath)):
        examplepath = folderpath + "/" + example
        if os.path.isdir(examplepath):
            test_examples_in_folder(platform, examplepath)
            continue
        if not examplepath.endswith(".ino"):
            continue

        print('\t' + example, end=' ')

        # check if we should SKIP
        skipfilename = folderpath + "/." + platform + ".test.skip"
        onlyfilename = folderpath + "/." + platform + ".test.only"
        # check if we should GENERATE UF2
        gen_file_name = folderpath + "/." + platform + ".generate"

        # .skip txt include all skipped platforms, one per line
        skip_txt = folderpath + "/.skip.txt"

        is_skip = False
        if os.path.exists(skipfilename):
            is_skip = True
        if os.path.exists(skip_txt):
            with open(skip_txt) as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip() == platform:
                        is_skip = True
                        break
        if is_skip:
            ColorPrint.print_warn("skipping")
            continue

        if glob.glob(folderpath + "/.*.test.only"):
            platformname = glob.glob(folderpath + "/.*.test.only")[0].split('.')[1]
            if platformname != "none" and platformname not in ALL_PLATFORMS:
                # uh oh, this isn't a valid testonly!
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

        if PRINT_DEPENDENCIES_AS_HEADER:
            cmd.append('--only-compilation-database')
            cmd.append('--no-color')
        elif INCLUDE_PRINT_DEPENDENCIES_HEADER:
            cmd.append('--build-property')
            cmd.append('"build.extra_flags=\'-DPRINT_DEPENDENCIES -I\"' + os.path.join(BUILD_DIR, "print_dependencies.cpp") + '\"\'"')
            cmd.append('--verbose')

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            if PRINT_DEPENDENCIES_AS_HEADER:
                # Extract dependencies and write to header for the first successful example
                dependencies = extract_dependencies(out.decode("utf-8") + err.decode("utf-8"))
                write_dependencies_to_header(dependencies, PRINT_DEPENDENCIES_AS_HEADER_FILENAME)
            elif os.path.exists(gen_file_name):
                if ALL_PLATFORMS[platform][1] is None:
                    ColorPrint.print_info("Platform does not support UF2 files, skipping...")
                else:
                    ColorPrint.print_info("Generating UF2...")
                    filename = generate_uf2(platform, fqbn, folderpath)
                    if filename is None:
                        success = 1  # failure
                    if IS_LEARNING_SYS:
                        fqbnpath, uf2file = filename.split("/")[-2:]
                        os.makedirs(BUILD_DIR + "/build", exist_ok=True)
                        os.makedirs(BUILD_DIR + "/build/" + fqbnpath, exist_ok=True)
                        shutil.copy(filename, BUILD_DIR + "/build/" + fqbnpath + "-" + uf2file)
                        subprocess.run("ls -lR " + BUILD_DIR + "/build", shell=True, check=True)
        else:
            ColorPrint.print_fail(CROSS)
            with group_output(f"{example} {fqbn} built output"):
                ColorPrint.print_fail(out.decode("utf-8"))
                ColorPrint.print_fail(err.decode("utf-8"))
            success = 1


def main():
    global INCLUDE_PRINT_DEPENDENCIES_HEADER, PRINT_DEPENDENCIES_AS_HEADER
    # Test platforms
    platforms = []

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

    # Install libraries deps
    install_library_deps()

    for platform in platforms:
        fqbn = ALL_PLATFORMS[platform][0]
        print('#'*80)
        ColorPrint.print_info("SWITCHING TO " + fqbn)
        install_platform(":".join(fqbn.split(':', 2)[0:2]), ALL_PLATFORMS[platform]) # take only first two elements
        print('#'*80)
        if not IS_LEARNING_SYS:
            if INCLUDE_PRINT_DEPENDENCIES_HEADER:
                PRINT_DEPENDENCIES_AS_HEADER = True
                INCLUDE_PRINT_DEPENDENCIES_HEADER = False
                test_examples_in_folder(platform, BUILD_DIR + "/examples")
                PRINT_DEPENDENCIES_AS_HEADER = False
                INCLUDE_PRINT_DEPENDENCIES_HEADER = True
                test_examples_in_folder(platform, BUILD_DIR + "/examples")
            else:
                test_examples_in_folder(platform, BUILD_DIR + "/examples")
        else:
            test_examples_in_folder(platform, BUILD_DIR)

if __name__ == "__main__":
    main()
    exit(success)
