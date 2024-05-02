# image-tools v0.0.7

Commandline tools to manage Stackable container images available at https://github.com/stackabletech/docker-images

This repository (and the installable package) contain two tools:

* `bake` : build and publish product images.
* `check-container` : run RedHat preflight checks on container images.

## Usage examples

Run either `bake` or `check-container` with `--help` to get an overview of the accepted flags and their functionality.
Below are some common usage examples:

```shell
# Build images of the hello-world containers
bake -p hello-world -i 0.0.0-dev

# Build only one version [0.37.2] of OPA
bake -p opa=0.37.2 -i 0.0.0-dev

# Build half of all versions defined for OPA
bake -p opa -i 0.0.0-dev  --shard-count 2 --shard-index 0

# Build the other half of all versions defined for OPA
bake -p opa -i 0.0.0-dev  --shard-count 2 --shard-index 1
```

## Installation

We recommend to use [pipx](https://pypa.github.io/pipx/):

```shell
pipx install image-tools-stackabletech
```

But you can also use `pip`:

```shell
# from PyPI
pip install image-tools-stackabletech
# from GitHub
pip install git+https://github.com/stackabletech/image-tools.git@main
```

## Release a new version

Update the version in:

* `pyproject.toml`
* `README.md` : version and pip install command.

Update the CHANGELOG.
Commit and tag.
Build and publish:

```shell
rm -rf dist/
python -m build --sdist --wheel .
twine upload dist/*
```
