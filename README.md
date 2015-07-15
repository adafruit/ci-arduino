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
before_install:
  - source <(curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/install.sh)
install:
  - arduino --install-library "Adafruit SleepyDog Library,Adafruit FONA Library"
script:
  - arduino --board arduino:avr:uno --save-prefs
  - arduino --verify $PWD/examples/mqtt_cc3k/mqtt_cc3k.ino
notifications:
  email:
    on_success: change
    on_failure: change
```
