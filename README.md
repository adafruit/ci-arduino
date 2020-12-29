# Travis CI Arduino Init Script [![Build Status](https://travis-ci.com/adafruit/travis-ci-arduino.svg?branch=master)](https://travis-ci.com/adafruit/travis-ci-arduino)

The purpose of this repo is to create a centrally managed dependency
install script for all Adafruit Arduino Library Travis CI and Github Actions configs.
This will allow us to easily update the install steps without
having to manually or programatically update 100+ `.travis.yml` files.

We have a guide that you can use to follow along to install both TravisCI and Doxygen generation here https://learn.adafruit.com/the-well-automated-arduino-library/

## Adding to Travis CI Configs

You will need to source the script in the `before_install` step of your
`.travis.yml` file.

```sh
source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
```

If you only want to install and build on certain platforms, you can set the
`INSTALL_PLATFORMS` envionrment variable to a comma-seperated list of platforms.

**Example `.travis.yml`:**
```yaml
language: c
sudo: false
cache:
  directories:
    - ~/arduino_ide
    - ~/.arduino15/packages/
git:
  depth: false
  quiet: true
addons:
  apt:
    sources:
      - llvm-toolchain-trusty-5.0
      - key_url: 'http://apt.llvm.org/llvm-snapshot.gpg.key'
    packages:
      - clang-format-5.0
env:
  global:
#    - ARDUINO_IDE_VERSION="1.8.10"
     - PRETTYNAME="Adafruit FT6206 Arduino Library"
# Optional, will default to "$TRAVIS_BUILD_DIR/Doxyfile"
#    - DOXYFILE: $TRAVIS_BUILD_DIR/Doxyfile

before_install:
   - source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
   - curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/run-clang-format.py > run-clang-format.py

install:
   - arduino --install-library "Adafruit ILI9341","Adafruit GFX Library"

script:
   - python run-clang-format.py -r .
   - build_main_platforms

# Generate and deploy documentation
after_success:
  - source <(curl -SLs  https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/library_check.sh)
  - source <(curl -SLs  https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/doxy_gen_and_deploy.sh)
```

**Choosing Arduino IDE version**

You could use any version of IDE by setting `ARDUINO_IDE_VERSION` variable but we recommend keeping this variable unused because script gets updated and you then will not have to modify `.travis.yml` manually.

## Automated Example Verification Bash Functions

`build_platform` will build all `.ino` examples in the repo using the passed platform. The platforms
are defined in the `MAIN_PLATFORMS` and `AUX_PLATFORMS` associative arrays at the top of the script.

All of the examples will be built with the platforms in `MAIN_PLATFORMS` if you call `build_main_platforms`,
and `AUX_PLATFORMS` can be used to define other platforms that don't need to be verified for every repo.

Build the examples using the platforms in the MAIN_PLATFORMS array:
```yaml
script:
  - build_main_platforms
```

Build the examples only using the trinket:
```yaml
script:
  - build_platform trinket
```

### Skipping Platforms

If you would like to skip one of the main platforms when running `build_main_platforms`,
you can commit a `.YOUR_PLATFORM_HERE.test.skip` file to the example sketch directory you
wish to skip. You will need to use the array key defined in `MAIN_PLATFORMS` for the platform
you wish to skip.

For example, if you would like to skip the `esp8266` platform for an example
in your lib called `blink.ino`, you would need to do something like this in your library repo:

```sh
$ touch examples/blink/.esp8266.test.skip
$ git add -A
$ git commit -a
$ git push
```

If you need an easy way to skip a platform, you can also add something like this to your `~/.bash_profile`:

```sh
function travis_skip()
{

  local platform_key=$1

  # grab all pde and ino example sketches
  local examples=$(find $PWD -name "*.pde" -o -name "*.ino")

  # loop through example sketches
  for example in $examples; do

    # store the full path to the example's sketch directory
    local example_dir=$(dirname $example)

    touch ${example_dir}/.${platform_key}.test.skip

  done

}
```

You will then be able to skip a platform for all examples by running the `travis_skip` function from your library repo.
It will automatically add the `.YOUR_PLATFORM_HERE.test.skip` files to the examples.

```sh
$ travis_skip esp8266
```

## Using external libraries
External libraries (which are not hosted by the Arduino library manager) can be installed using the following command:
```sh
- if [ ! -d "$HOME/arduino_ide/libraries/<Name>" ]; then git clone <URL> $HOME/arduino_ide/libraries/<Name>; fi
```

## Deploying compiled artifacts
If you need to get hold of the compiled sketches of your project, in order to release them or forward them to an
deployment pipeline, you can find them in the `$ARDUINO_HEX_DIR` directory. Specifically, if `Foo` is the name
of your project, you are compiling for an `Arduino Mega` and the primary sketch is called `Foo.ino`, the flashable
`.hex` files will be found inside `$ARDUINO_HEX_DIR/mega2560/Foo` as `Foo.ino.hex` and `Foo.ino.with_bootloader.hex`.
Similarly for the rest of the platforms.

For example, assuming you have a `Foo` project as outlined above, to create a release which includes the `.hex`
files on GitHub, you could add this to your `.travis.yml` configuration:

```yaml
deploy:
  provider: releases
  api_key:
    secure: YOUR_API_KEY_ENCRYPTED
  file:
    - $ARDUINO_HEX_DIR/mega2560/Foo/Foo.ino.hex
    - $ARDUINO_HEX_DIR/mega2560/Foo/Foo.ino.with_bootloader.hex
  skip_cleanup: true
  on:
    tags: true
```

## Running build_platforms.py locally
1. Install arduino-cli from here: https://arduino.github.io/arduino-cli/installation/
2. Download ci-arduino
   * `git clone https://github.com/adafruit/ci-arduino`
3. Put these lines at the end of your `.bashrc` or `.bash_profile` if you're on OSX. Make sure to fill in the path to where you installed ci-arduino and replacing USER with your username.
   ```bash
   alias test-platforms='python3 ~/path/to/ci-arduino/build_platform.py'
   export HOME=/home/USER/
   ```
4. Run this at the top level of the library you want to test
   ```bash
   adafruit@adafruit:~/Adafruit_BMP183_Library$ export GITHUB_WORKSPACE=$(pwd)
   ```
5. Remove everything in test library, and re-create it
   ```bash
   adafruit@adafruit:~/Adafruit_BMP183_Library$ rm -rf ~/Arduino/libraries/Adafruit_Test_Library/; mkdir ~/Arduino/libraries/Adafruit_Test_Library
   ```
6. Still in the top-level directory of the library you'll be testing, copy the current library to Adafruit_Test_Library
   ```bash
   adafruit@adafruit:~/Adafruit_BMP183_Library$ cp * ~/Arduino/libraries/Adafruit_Test_Library/
   ```
7. Grep for build_platform.py in githubci.yml to find out what boards to test.
   ```bash
   adafruit@adafruit:~/Adafruit_BMP183_Library$ grep 'build_platform.py' .github/workflows/githubci.yml
           run: python3 ci/build_platform.py main_platforms
   ```
8. Run test-platforms. This may take a while, and tests for some boards sometimes run orders of magnitude slower than tests for other boards.
   ```bash
   test-platforms main_platforms
   ```
   OR, if githubci.yml specified other boards, let's say the metro m0 and pyportal, you'd run this:
   ```bash
   test-platforms metro_m0 pyportal
   ```

Here's what that returns
```bash
adafruit@adafruit:~/Adafruit_BMP183_Library$ test-platforms main_platforms
build dir: /home/dherrada/Adafruit_BMP183_Library

########################################
INSTALLING ARDUINO BOARDS
########################################
arduino-cli core update-index --additional-urls https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json,https://dl.espressif.com/dl/package_esp32_index.json,https://sandeepmistry.github.io/arduino-nRF5/package_nRF5_boards_index.json > /dev/null

Installing Adafruit Unified Sensor
arduino-cli lib install "Adafruit Unified Sensor" > /dev/null
arduino-cli lib uninstall "Adafruit BMP183 Library"
Library Adafruit BMP183 Library is not installed
Libraries installed:  ['/home/adafruit/Arduino/libraries/Adafruit_VL53L0X', '/home/adafruit/Arduino/libraries/RTClib', '/home/adafruit/Arduino/libraries/Adafruit-RGB-LCD-Shield-Library', '/home/adafruit/Arduino/libraries/readme.txt', '/home/adafruit/Arduino/libraries/Adafruit_Test_Library', '/home/adafruit/Arduino/libraries/Adafruit_Unified_Sensor']
  elif isinstance(platform, collections.Iterable):
################################################################################
SWITCHING TO arduino:avr:uno
Installing arduino:avr ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO arduino:avr:leonardo
Installing arduino:avr ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO arduino:avr:mega:cpu=atmega2560
Installing arduino:avr ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO arduino:samd:arduino_zero_native
Installing arduino:samd ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO esp8266:esp8266:huzzah:eesz=4M3M,xtal=80
Installing esp8266:esp8266 ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO esp32:esp32:featheresp32:FlashFreq=80
Installing esp32:esp32 ✓
################################################################################
  BMP183test.ino ✓
################################################################################
SWITCHING TO adafruit:samd:adafruit_metro_m4:speed=120
Installing adafruit:samd ✓
################################################################################
	BMP183test.ino ✓
################################################################################
SWITCHING TO adafruit:nrf52:feather52840:softdevice=s140v6,debug=l0
Installing adafruit:nrf52 ✓
################################################################################
	BMP183test.ino ✓
```
