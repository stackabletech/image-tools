# image-tools

Version: 0.0.1

## Installation

We recommend to use [pipx](https://pypa.github.io/pipx/):

    pipx install image-tools-stackabletech

But you can also use `pip`:

    # from PyPI
    pip install image-tools-stackabletech
    # from GitHub
    pip install git+https://github.com/stackabletech/image-tools.git@master

## Description

Tools to manage Stackable container images available at https://github.com/stackabletech/docker-images

## Release a new version

Update the version in:

* `pyproject.toml`
* `version.py`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

    rm -rf dist/
    python -m build --wheel .
    twine upload dist/*
