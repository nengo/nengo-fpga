#!/usr/bin/env bash

NAME=$0
COMMAND=$1

function usage {
    echo "usage: $NAME <command>"
    echo
    echo "  install  Install dependencies for building docs"
    echo "  check    Check documentation for broken links"
    echo "  run      Build documentation"
    echo "  upload   Upload documentation to gh-pages branch"
    exit 1
}

if [[ "$COMMAND" == "install" ]]; then
    conda install --quiet jupyter matplotlib numpy pillow
    pip install "sphinx>1.7" nbsphinx numpydoc nengo_sphinx_theme
    pip install -e .
elif [[ "$COMMAND" == "check" ]]; then
    sphinx-build -b linkcheck -v -D nbsphinx_execute=never docs docs/_build
elif [[ "$COMMAND" == "run" ]]; then
    git clone -b gh-pages https://github.com/nengo/nengo-fpga.git ../docs
    sphinx-build -vW docs ../docs
elif [[ "$COMMAND" == "upload" ]]; then
    cd ../docs
    git config --global user.email "travis@travis-ci.org"
    git config --global user.name "TravisCI"
    git add --all
    git commit -m "Last update at $(date '+%Y-%m-%d %T')"
    git push -fq "https://$GH_TOKEN@github.com/nengo/nengo-fpga.git" gh-pages
else
    if [[ -z "$COMMAND" ]]; then
        echo "Command required"
    else
        echo "Command $COMMAND not recognized"
    fi
    echo
    usage
fi
