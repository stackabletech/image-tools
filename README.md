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

Following tools are installed:

* `bake` : build and publish product images.
* `check-container` : run RedHat preflight checks on container images.

## Examples

    # Build images of the hello-world containers
    bake -p hello-world -i 0.0.0-dev --organization sandbox
    # Run preflight checks on the hello-world container images
    check-container -p hello-world -i 0.0.0-dev

## Release a new version

Update the version in:

* `pyproject.toml`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

    rm -rf dist/
    python -m build --wheel .
    twine upload dist/*
