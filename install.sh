#!/usr/bin/env bash

# we need bash 4 for associative arrays
if [ "${BASH_VERSION%%[^0-9]*}" -lt "4" ]; then
  echo "BASH VERSION < 4: ${BASH_VERSION}" >&2
  exit 1
fi

# associative array for platforms that will be verified in build_main_platforms()
declare -A main_platforms=( [uno]="arduino:avr:uno" [due]="arduino:sam:arduino_due_x" [esp8266]="esp8266:esp8266:huzzah" [leonardo]="arduino:avr:leonardo" )

# associative array for other platforms that can be called explicitly in .travis.yml configs
declare -A aux_platforms=( [trinket]="adafruit:avr:trinket5" [gemma]="arduino:avr:gemma" )

# export platform vars
export main_platforms
export aux_platforms

# make display available for arduino CLI
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_1.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :1 -ac -screen 0 1280x1024x16
sleep 3
export DISPLAY=:1.0

# download and install arduino 1.6.5
wget http://downloads.arduino.cc/arduino-1.6.5-linux64.tar.xz
tar xf arduino-1.6.5-linux64.tar.xz
mv arduino-1.6.5 $HOME/arduino_ide

# move this library to the arduino libraries folder
ln -s $PWD $HOME/arduino_ide/libraries/Adafruit_Test_Library

# add the arduino CLI to our PATH
export PATH="$HOME/arduino_ide:$PATH"

# install the due, esp8266, and adafruit board packages
arduino --pref "boardsmanager.additional.urls=https://adafruit.github.io/arduino-board-index/package_adafruit_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json" --save-prefs
arduino --install-boards arduino:sam > /dev/null
arduino --install-boards esp8266:esp8266 > /dev/null
arduino --install-boards adafruit:avr > /dev/null

# install random lib so the arduino IDE grabs a new library index
# see: https://github.com/arduino/Arduino/issues/3535
arduino --install-library USBHost

# build all of the examples for the passed platform
function build_examples()
{

  # expects argument 1 to be the platform key
  local platform_key=$1

  # placeholder for platform
  local platform=""

  # grab all pde and ino example sketches
  local examples=$(find $PWD -name "*.pde" -o -name "*.ino")

  # grab the platform info from array or bail if invalid
  if [ ${main_platforms[$platform_key]+_} ]; then
    platform=${main_platforms[$platform_key]}
  elif [ ${aux_platforms[$platform_key]+_} ]; then
    platform=${aux_platforms[$platform_key]}
  else
    echo "INVALID PLATFORM KEY: $platform_key" >&2
    return 1
  fi

  # switch to the requested board
  echo -e "\n\n ------------ PLATFORM: ${platform_key} ------------ \n\n";
  arduino --board $platform --save-prefs

  # grab the exit status of the arduino board change
  local platform_switch=$?

  # bail if the platform switch failed
  if [ $platform_switch -ne 0 ]; then
    echo "SWITCHING PLATFORM FAILED: ${platform}" >&2
    return $platform_switch
  fi

  # loop through example sketches
  for example in $examples; do

    # store the full path to the example's sketch directory
    local example_dir=$(dirname $example)

    # ignore this example if there is a skip file preset for this platform
    if [[ -f "${example_dir}/.${platform_key}.test.skip" ]]; then
      echo -e "\n\n ------------ SKIPPING $platform_key BUILD: $example ------------ \n\n";
      continue
    fi

    # make sure that all examples are .ino files
    if [[ $example =~ \.pde$ ]]; then
      echo "PDE EXAMPLE EXTENSION: $example" >&2
      return 1
    fi

    echo -e "\n\n ------------ BUILDING: $example ------------ \n\n";
    arduino --verify $example;

    # grab the exit status of the arduino verify
    local build_result=$?

    # bail if the build failed
    if [ $build_result -ne 0 ]; then
      echo "BUILD FAILED" >&2
      return $build_result
    fi

  done

}

# build all examples for every platform in $main_platforms
function build_main_platforms()
{

  for p_key in "${!main_platforms[@]}"; do

    # build all examples for this platform
    build_examples $p_key

    # grab the exit status of the builds
    local result=$?

    # bail if the build failed
    if [ $result -ne 0 ]; then
      return $result
    fi

  done

}

