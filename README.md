# image-tools

Version: 0.0.3

## Installation

We recommend to use [pipx](https://pypa.github.io/pipx/):

    pipx install image-tools-stackabletech

But you can also use `pip`:

    # from PyPI
    pip install image-tools-stackabletech
    # from GitHub
    pip install git+https://github.com/stackabletech/image-tools.git@main

## Description

Tools to manage Stackable container images available at https://github.com/stackabletech/docker-images

Following tools are installed:

* `bake` : build and publish product images.
* `check-container` : run RedHat preflight checks on container images.

## Examples

    # Build images of the hello-world containers
    bake -p hello-world -i 0.0.0-dev

    # Build only one version [0.37.2] of OPA
    bake -p opa=0.37.2 -i 0.0.0-dev

    # Build half of all versions defined for OPA
    bake -p opa -i 0.0.0-dev  --shard-count 2 --shard-index 0

    # Build the other half of all versions defined for OPA
    bake -p opa -i 0.0.0-dev  --shard-count 2 --shard-index 1

## Release a new version

Update the version in:

* `pyproject.toml`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

    rm -rf dist/
    python -m build --sdist --wheel .
    twine upload dist/*
