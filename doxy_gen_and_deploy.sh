#!/bin/bash
################################################################################
# Title         : doxy_gen_and_deploy.sh
# Date modified : 2018/01/14
# Notes         :
__AUTHOR__="Jeroen de Bruijn, modified by ladyada"
# Preconditions:
# - Doxygen configuration file must have the destination directory empty and
#   source code directory with a $(TRAVIS_BUILD_DIR) prefix.
# - An gh-pages branch should already exist. See below for mor info on hoe to
#   create a gh-pages branch.
#
# Required global variables:
# - TRAVIS_BUILD_NUMBER : The number of the current build.
# - TRAVIS_COMMIT       : The commit that the current build is testing.
# - GH_REPO_TOKEN       : Secure token to the github repository.
# - TRAVIS_REPO_SLUG    : The author/url slug
# Optional global variables:
# - DOXYFILE            : The Doxygen configuration file.
# - PRETTYNAME          : A string name of the project (for the doxy headers)
#
# For information on how to encrypt variables for Travis CI please go to
# https://docs.travis-ci.com/user/environment-variables/#Encrypted-Variables
# or https://gist.github.com/vidavidorra/7ed6166a46c537d3cbd2
# For information on how to create a clean gh-pages branch from the master
# branch, please go to https://gist.github.com/vidavidorra/846a2fc7dd51f4fe56a0
#
# This script will generate Doxygen documentation and push the documentation to
# the gh-pages branch of a repository
# Before this script is used there should already be a gh-pages branch in the
# repository.
#
################################################################################

################################################################################
##### Setup this script and get the current gh-pages branch.               #####
echo 'Setting up the script...'
# Exit with nonzero exit code if anything fails
set -e

cd $TRAVIS_BUILD_DIR

# The default version of doxygen is too old so we'll use a modern version
wget -q https://cdn-learn.adafruit.com/assets/assets/000/067/405/original/doxygen-1.8.13.linux.bin.tar.gz
tar -xf doxygen-1.8.13.linux.bin.tar.gz
mv doxygen-1.8.13/bin/doxygen .
chmod +x doxygen

# Create a clean working directory for this script.
mkdir code_docs
cd code_docs

# Get the current gh-pages branch
git clone -b gh-pages https://github.com/${TRAVIS_REPO_SLUG}.git
export TRAVIS_REPO_NAME=${TRAVIS_REPO_SLUG#*/}
cd ${TRAVIS_REPO_NAME}

##### Configure git.
# Set the push default to simple i.e. push only the current branch.
git config --global push.default simple
# Pretend to be an user called Travis CI.
git config user.name "Travis CI"
git config user.email "travis@travis-ci.org"

# Remove everything currently in the gh-pages branch.
# GitHub is smart enough to know which files have changed and which files have
# stayed the same and will only update the changed files. So the gh-pages branch
# can be safely cleaned, and it is sure that everything pushed later is the new
# documentation.
# If there's no index.html (forwarding stub) grab our default one
shopt -s extglob
if [ ! -f index.html ]; then
    rm -rf *
    curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/doxy_index.html > index.html
else
    # Don't fail if there's no files in the directory, just keep going!
    rm -r -- !(index.html) || true
fi

# Need to create a .nojekyll file to allow filenames starting with an underscore
# to be seen on the gh-pages site. Therefore creating an empty .nojekyll file.
# Presumably this is only needed when the SHORT_NAMES option in Doxygen is set
# to NO, which it is by default. So creating the file just in case.
echo "" > .nojekyll

################################################################################
##### Generate the Doxygen code documentation and log the output.          #####
echo 'Generating Doxygen code documentation...'
# Redirect both stderr and stdout to the log file AND the console.

if [ ! -f "$DOXYFILE" ]; then
    echo "Grabbing default Doxyfile"
    export DOXYFILE=${TRAVIS_BUILD_DIR}/Doxyfile

    curl -SLs https://raw.githubusercontent.com/adafruit/travis-ci-arduino/master/Doxyfile.default > ${DOXYFILE}
    #sed -i "s/^INPUT .*/INPUT = ..\/../"  ${DOXYFILE}

    # If we can, fix up the name
    if [ ! -z "$PRETTYNAME" ]; then
    sed -i "s/^PROJECT_NAME.*/PROJECT_NAME = \"${PRETTYNAME}\"/"  ${DOXYFILE}
    fi
fi

sed -i "s;^HTML_OUTPUT .*;HTML_OUTPUT = code_docs/${TRAVIS_REPO_NAME}/html;"  ${DOXYFILE}
cd $TRAVIS_BUILD_DIR

# Print out doxygen warnings in red
${TRAVIS_BUILD_DIR}/doxygen $DOXYFILE 2>&1 | tee foo.txt > >(while read line; do echo -e "\e[01;31m$line\e[0m" >&2; done)

# if any warnings, bail!
if [ -s foo.txt ]; then exit 1 ; fi

rm foo.txt

# If we're a pull request, don't push docs to github!
if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
    echo "This is a Pull Request, we're done!"
    exit 0
else
    echo "This is a Commit, Uploading documentation..."
fi

cd code_docs/${TRAVIS_REPO_NAME}

################################################################################
##### Upload the documentation to the gh-pages branch of the repository.   #####
# Only upload if Doxygen successfully created the documentation.
# Check this by verifying that the html directory and the file html/index.html
# both exist. This is a good indication that Doxygen did it's work.
if [ -d "html" ] && [ -f "html/index.html" ]; then

    echo 'Uploading documentation to the gh-pages branch...'
    # Add everything in this directory (the Doxygen code documentation) to the
    # gh-pages branch.
    # GitHub is smart enough to know which files have changed and which files have
    # stayed the same and will only update the changed files.
    echo 'Adding all files'
    git add --all

    if [ -n "$(git status --porcelain)" ]; then
    echo "Changes to commit"
    else
    echo "No changes to commit"
    exit 0
    fi

    # Commit the added files with a title and description containing the Travis CI
    # build number and the GitHub commit reference that issued this build.
    echo 'Git committing'
    git commit -m "Deploy code docs to GitHub Pages Travis build: ${TRAVIS_BUILD_NUMBER}" -m "Commit: ${TRAVIS_COMMIT}"

    # Force push to the remote gh-pages branch.
    # The ouput is redirected to /dev/null to hide any sensitive credential data
    # that might otherwise be exposed.
    echo 'Git pushing'
    git push --force "https://${GH_REPO_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git" > /dev/null 2>&1
else
    echo '' >&2
    echo 'Warning: No documentation (html) files have been found!' >&2
    echo 'Warning: Not going to push the documentation to GitHub!' >&2
    exit 1
fi
