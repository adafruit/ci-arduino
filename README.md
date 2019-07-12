# Travis CI Arduino Init Script [![Build Status](https://travis-ci.com/adafruit/travis-ci-arduino.svg?branch=master)](https://travis-ci.com/adafruit/travis-ci-arduino)

The purpose of this repo is to create a centrally managed dependency
install script for all Adafruit Arduino Library Travis CI configs.
This will allow us to easily update the install steps without
having to manually or programatically update 100+ `.travis.yml` files.

We have a guide that you can use to follow along to install both TravisCI and Doxygen generation here https://learn.adafruit.com/the-well-automated-arduino-library/

## Adding to Travis CI Configs

You will need to source the script in the `before_install` step of your
`.travis.yml` file.

```
source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
```

If you only want to install and build on certain platforms, you can set the
`INSTALL_PLATFORMS` envionrment variable to a comma-seperated list of platforms.

**Example `.travis.yml`:**
```
language: c
sudo: false
cache:
  directories:
    - ~/arduino_ide
    - ~/.arduino15/packages/
git:
  depth: false
  quiet: true
env:
  global:
     - ARDUINO_IDE_VERSION="1.8.7"
before_install:
  - source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
install:
  # Note that every library should be installed in a seperate command
  - arduino --install-library "Adafruit SleepyDog Library"
  - arduino --install-library "Adafruit FONA Library"
script:
  - build_main_platforms
notifications:
  email:
    on_success: change
    on_failure: change
```

**Choosing Arduino IDE version**

You could use any version of IDE by setting `ARDUINO_IDE_VERSION` variable but we recommend keeping this variable unused because script gets updated and you then will not have to modify `.travis.yml` manually.

## Automated Example Verification Bash Functions

`build_platform` will build all `.ino` examples in the repo using the passed platform. The platforms
are defined in the `MAIN_PLATFORMS` and `AUX_PLATFORMS` associative arrays at the top of the script.

All of the examples will be built with the platforms in `MAIN_PLATFORMS` if you call `build_main_platforms`,
and `AUX_PLATFORMS` can be used to define other platforms that don't need to be verified for every repo.

Build the examples using the platforms in the MAIN_PLATFORMS array:
```
script:
  - build_main_platforms
```

Build the examples only using the trinket:
```
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

```
$ touch examples/blink/.esp8266.test.skip
$ git add -A
$ git commit -a
$ git push
```

If you need an easy way to skip a platform, you can also add something like this to your `~/.bash_profile`:

```
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

```
$ travis_skip esp8266
```

## Using external libraries
External libraries (which are not hosted by the Arduino library manager) can be installed using the following command:
```
- if [! -d "$HOME/arduino_ide/libraries/<Name>" ]; then git clone <URL> $HOME/arduino_ide/libraries/<Name>; fi
```
