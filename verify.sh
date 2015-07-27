#!/usr/bin/env bash

# we need bash 4 for associative arrays
if [ "${BASH_VERSION%%[^0-9]*}" -lt "4" ]; then
  echo "BASH VERSION < 4: ${BASH_VERSION}" >&2
  exit 1
fi

# define platform associative array
declare -A test_platforms=( [uno]="arduino:avr:uno" [due]="arduino:sam:arduino_due_x" [esp8266]="esp8266:esp8266:huzzah" [leonardo]="arduino:avr:leonardo" )

# this is called by the .travis.yml in the repo
function build_examples()
{

  # expects argument 1 to be the platform key
  local platform=$1

  # grab all pde and ino example sketches
  local examples=$(find $PWD -name "*.pde" -o -name "*.ino")

  # switch to the requested board
  echo -e "\n\n ------------ PLAFORM: ${test_platforms[$platform]} ------------ \n\n";
  arduino --board ${test_platforms[$platform]} --save-prefs

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
    if [[ -f "${example_dir}/.${platform}.test.skip" ]]; then
      echo -e "\n\n ------------ SKIPPING: $example ------------ \n\n";
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

# build all platforms
for platform_key in "${!test_platforms[@]}"; do

  build_examples $platform_key

  # grab the exit status of the builds
  local result=$?

  # bail if the build failed
  if [ $result -ne 0 ]; then
    return $result
  fi

done

