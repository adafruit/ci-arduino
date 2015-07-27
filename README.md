# Travis CI Arduino Init Script

The purpose of this repo is to create a centrally managed dependency
install script for all Adafruit Arduino Library Travis CI configs.
This will allow us to easily update the install steps without
having to manually or programatically update 100+ `.travis.yml` files.

## Adding to Travis CI Configs

You will need to source the script in the `before_install` step of your
`.travis.yml` file.

```
source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
```

**Example `.travis.yml`:**
```
language: c
sudo: false
before_install:
  - source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
install:
  - arduino --install-library "Adafruit SleepyDog Library,Adafruit FONA Library"
script:
  - build_main_platforms
notifications:
  email:
    on_success: change
    on_failure: change
```

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
