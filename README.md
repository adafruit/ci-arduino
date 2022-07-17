# Arduino CI Scripts

This repos contains various scripts and tools related to running
continuous integration (CI) checks on Arduino Library Repos.

There is an associated guide available here:
https://learn.adafruit.com/the-well-automated-arduino-library/

## Adding GitHub Actions to Repo

* Create a folder named `.github/workflows` in the root of the repo.
* Copy `example_actions.yml` into the above directory and rename it `githubci.yml`.
* Edit `githubci.yml` and change `PRETTYNAME` to the library repo name.
* Here's an example: [Adafruit_BME280_Library](https://github.com/adafruit/Adafruit_BME280_Library/blob/master/.github/workflows/githubci.yml)
* These actions will now run automatically on any pull, push, or dispatch.

## Controlling Test Behavior

The `build_platform.py` script is used to test each `.ino` example in the repo for the
selected build platforms. The `ALL_PLATFORMS` dictionary contains a listing of all
available platforms. By default, `main_platforms` is used. Additionally, UF2 files
of the compiled sketches can be generated for supported platforms. The behavior
can be controlled using special hidden filenames. These are just empty files
placed in the root folder:

* `.YOUR_PLATFORM_HERE.test.skip` - Skip the specified platform. All others are tested.
* `.YOUR_PLATFORM_HERE.test.only` - Test only the specfied platform. All others are skipped.
* `.YOUR_PLATFORM_HERE.generate` - Generate UF2 of sketch for specified platform (if supported).

Replace `YOUR_PLATFORM_HERE` in the name with exact text from `ALL_PLATFORMS`.

### Examples

* To **skip** testing on ESP8266, add a file named `.esp8266.test.skip`
* To test **only** the Arduino UNO, add a file named `.uno.test.only`
* To skip all and test **nothing**, add a file named `.none.test.only`
* To generate UF2s for PyPortal, add a file named `.pyportal.generate`

## Formatting Check with Clang

The `run-clang-format.py` script is used to run ClangFormat and check file formatting.
See [the guide](https://learn.adafruit.com/the-well-automated-arduino-library/formatting-with-clang-format) for details on installing `clang-format` to run formatting locally.
Even a single extra white space can cause the CI to fail on formatting.
You can typically just let clang do its thing and edit files in place using:
```
clang-format -i File_To_Format.cpp
```

## Documentation with Doxygen

The `doxy_gen_and_deploy.sh` script uses Doxygen to generate and deploy documentation
for the library. Any issues, like missing documentation, will cause the CI to fail.
See the [the guide](https://learn.adafruit.com/the-well-automated-arduino-library/doxygen)
for details on installing and running doxygen locally. The guide also has some
[tips](https://learn.adafruit.com/the-well-automated-arduino-library/doxygen-tips)
on basic usage of doxygen markup within your code.
