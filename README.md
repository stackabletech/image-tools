# image-tools v0.0.12

Command line tools to manage Stackable container images available at [docker-images](https://github.com/stackabletech/docker-images)

This repository (and the installable package) contain two tools:

* `bake` : build and publish product images.
* `check-container` : run RedHat preflight checks on container images.

The `bake` command provides the following features:

* Build all Stackable product images
* Build individual product images
* Build individual product version images
* Use one or more distributed docker cache servers
* Publish images

## Docker Build Cache

Docker's `buildx` plugin supports different types of build cache back ends. Since Stackable product images are built by distributed GitHub actions, the distributed back ends are relevant.

To use the build cache, you have to configure one or more back ends and enable them by calling `bake` with the `--cache` flag.

To configure one or more cache back ends, add the relevant properties to the `cache` property of the configuration module.

Here an example with the `registry` backend:

```python
cache = [
    {
        "type": "registry",
        "ref_prefix": "build-repo.stackable.tech:8083/sandbox/cache",
        "mode": "max",
        "compression": "zstd",
        "ignore-error": "true",
    },
]
```

Here `ref_prefix` is used to build the unique `ref` property for each target.

NOTE: it's your responsibility to ensure that `bake` can read/write to the cache registry by performing a `docker login` before running `bake`.


For more information about the cache back ends, see the [Docker documentation](https://docs.docker.com/build/cache/backends/).

## Usage examples

Run either `bake` or `check-container` with `--help` to get an overview of the accepted flags and their functionality.
Below are some common usage examples:

```shell
# Build images of the hello-world containers
bake --product hello-world

# Build only one version [0.37.2] of OPA
bake --product opa=0.37.2

# Dry run. Do not build anything. Print the the generated Bakefile.
bake --product hello-world --dry

# Build all OPA images and set the organisation to "sandbox"
bake --product opa --organization sandbox

# Build all OPA images and set the image version to a release 24.7.0
bake --product opa --image-version 24.7.0

# Enable distributed docker cache (requires credentials to access the cache registry)
bake --product opa --cache

# Build the HBase images but use Java 21 instead of the values in conf.py
# for the java-base and java-devel images.
# It doesn't matter if you use lower or upper case for the build argument names,
# bake will normalize all of them to upper case.
bake --product hbase --build-arg 'java-base=21' --build-arg 'java-devel=21'

# Build half of all versions defined for OPA
bake --product opa --shard-count 2 --shard-index 0

# Build the other half of all versions defined for OPA
bake --product opa --shard-count 2 --shard-index 1
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

Or via Nix Shell:

```nix
{ lib, pkgs, ... }:
with lib;
let
  image-tools = pkgs.callPackage (pkgs.fetchFromGitHub {
    owner = "stackabletech";
    repo = "image-tools";
    rev = "caa4d993bcbb8b884097c89a54ee246f975e2ec6"; # pragma: allowlist secret
    hash = "sha256-gjTCroHw4iJhXPW+s3mHBzIH8seIKH1tPb82lUb8+a0="; # pragma: allowlist secret ; comment out to find new hashes when upgrading
  } + "/image-tools.nix") {};
in
{
  packages = with pkgs; [
    image-tools
    # ...
  ];

  // ...
}
```

## Development

Create a virtual environment where you install the package in "editable" mode:

Using `venv` and `pip`:

```shell
python -m venv ~/venv-image-tools-devel
source ~/venv-image-tools-devel/bin/activate
pip install --editable .
```

Using [pipx](https://pypa.github.io/pipx/):

```shell
pipx install --editable .
```

With the activated virtual environment, you can now run the tools from the `docker-images` repository and any local changes are immediately in effect.

We also recommend installing the `pre-commit` hooks in the activated virtual environment.

```shell
pip install pre-commit
pre-commit install
```

To run the hooks, stage the changes you want to commit and run:

```shell
pre-commit run
```

## Release a new version

1. Create a release PR where you:
1.1. Update the version in:

* `src/image_tools/version.py`
* `README.md` : version and pip install command.

1.2. Update the CHANGELOG.
2. Tag the release commit after it is merged to `main`.
3. Automated GH actions will publish the new version to PyPI.


To publish manually (requires PyPI credentials):

Build and publish:

```shell
rm -rf dist/
python -m build --sdist --wheel .
twine upload dist/*
```
