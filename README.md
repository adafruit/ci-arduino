# Arduino CI Scripts

This repo contains various scripts and tools related to running continuous integration (CI) checks on Arduino Library Repos. The operations include:

* checking formatting using [clang-format](https://clang.llvm.org/docs/ClangFormat.html),
* generating documentation from source comments using [Doxygen](https://www.doxygen.nl/), and
* building each example in the library for selected targets.

There is an associated guide available here:
https://learn.adafruit.com/the-well-automated-arduino-library/

## Adding GitHub Actions to Repo

To run these continuous integration checks on each push, pull-request or [repository dispatch](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-a-repository-dispatch-event) using [GitHub actions](https://github.com/features/actions):  

* Create a folder named `.github/worflows` in the root of the repo.
* Copy `example_actions.yml` into the above directory and rename it `githubci.yml`.
* Edit `githubci.yml` and change `PRETTYNAME` to the library repo name. Optionally, delete or comment out steps (using the `#` character), you don't want to include. 
* Here's an example: [Adafruit_BME280_Library](https://github.com/adafruit/Adafruit_BME280_Library/blob/master/.github/workflows/githubci.yml)

## Controlling Test Behavior

The `build_platform.py` script is used to test each `.ino` example in the repo for selected build platforms. The [`ALL_PLATFORMS`](ci-arduino/blob/master/build_platform.py#L54) dictionary contains a listing of all available platforms and selected platform groups. By default, `main_platforms` is used. To select a specific platform or group, replace `main_platforms` in [`githubci.yml`](`example_actions.yml`) with the group or platform name.

Additionally, [UF2 files](https://github.com/microsoft/uf2) of the compiled sketches can be generated for supported platforms. 

### Fine tuning test selection

The script behavior can be controlled using special filenames: 

* `.PLATFORM_ID.test.skip` - Skip the specified platform. All others are tested.
* `.PLATFORM_ID.test.only` - Test the specified platform. All others are skipped.
* `.PLATFORM_ID.generate` - Generate UF2 of sketch for specified platform (if supported).

These are just empty files placed in an example folder. Replace `PLATFORM_ID` in the name with the key from [`ALL_PLATFORMS`](ci-arduino/blob/master/build_platform.py#L54). `metro_m0` from the following line in `build_platform.py`, for example:

```python
"metro_m0" : ["adafruit:samd:adafruit_metro_m0", "0x68ed2b88", None],
```

You can use several `.PLATFORM_ID.test.skip` or `.PLATFORM_ID.test.only` to exclude or include multiple platforms. For example:

* To **skip** testing on ESP8266, add a file named `.esp8266.test.skip`
* To test **only** the Arduino UNO, add a file named `.uno.test.only`
* To skip all and test **nothing**, add a file named `.none.test.only`
* To generate UF2s for PyPortal, add a file named `.pyportal.generate`

### Dependencies

Any library dependencies included in the [`library.properties`](https://arduino.github.io/arduino-cli/0.19/library-specification/#libraryproperties-file-format) are automatically installed before the tests are started. To install additional dependencies (e.g., those required for some examples but not the library itself) using [`arduino-cli`](https://arduino.github.io/arduino-cli/0.19/commands/arduino-cli_lib_install/), you could add additional steps to the `githubci.yml` file. For example:

```yaml
- name: Set configuration
  run: arduino-cli config set library.enable_unsafe_install true 

- name: Install test dependencies
  run: arduino-cli lib install --git-url https://github.com/arduino-libraries/Servo --git-url https://github.com/arduino-libraries/Ethernet
```

Note: you'll only need to enable the [`enable_unsafe_install`](https://arduino.github.io/arduino-cli/0.32/configuration/#configuration-keys) option if you want to identify libraries using urls. This isn't necessary when using the library name. 

## Formatting Check with Clang

The `run-clang-format.py` script is used to run [clang-format](https://clang.llvm.org/docs/ClangFormat.html) and check file formatting.
See [the guide](https://learn.adafruit.com/the-well-automated-arduino-library/formatting-with-clang-format) for details on installing `clang-format` to run formatting locally.
Even a single extra white space can cause the CI to fail on formatting.
You can typically just let clang do its thing and edit files in place using:

```
clang-format -i File_To_Format.cpp
```

## Documentation with Doxygen

The `doxy_gen_and_deploy.sh` script uses [Doxygen](https://www.doxygen.nl/) to generate and deploy documentation
for the library. Any issues, like missing documentation, will cause the CI to fail.
See the [guide](https://learn.adafruit.com/the-well-automated-arduino-library/doxygen) for details on installing and running Doxygen locally. The guide also has some
[tips](https://learn.adafruit.com/the-well-automated-arduino-library/doxygen-tips) on basic usage of Doxygen markup within your code.
