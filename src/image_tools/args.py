# This is the stackable release version
from argparse import Namespace, ArgumentParser
import re
import importlib.util
import sys
import os
from types import ModuleType
from typing import List, Tuple

from .version import version


DEFAULT_IMAGE_VERSION_FORMATS = [
    re.compile(r"[2-9][0-9]\.[1-9][0-2]?\.\d+(-.+)?"),
    re.compile(r"0\.0\.0-dev(-.+)?"),
]


def bake_args() -> Namespace:
    parser = ArgumentParser(
        description=f"bake {version()} Build and publish product images. Requires docker and buildx (https://github.com/docker/buildx)."
    )
    parser.add_argument("-v", "--version", help="Display version", action="store_true")

    parser.add_argument(
        "-c",
        "--configuration",
        help="Configuration file. Default: './conf.py'.",
        default="./conf.py",
    )

    parser.add_argument(
        "-i",
        "--image-version",
        type=check_image_version_format,
        default="0.0.0-dev",
        help="Image version. Default: 0.0.0-dev.",
    )
    parser.add_argument(
        "-p",
        "--product",
        action="append",
        help="Product to build images for. For example 'druid' or 'druid=28.0.1' to build a specific version.",
    )
    parser.add_argument(
        "--shard-count",
        type=positive_int,
        default=1,
        help="Split the build into N shards, which can be built separately. \
                        All shards must be built separately, by specifying the --shard-index argument.",
    )
    parser.add_argument(
        "--shard-index",
        type=positive_int,
        default=0,
        help="Build shard number M out of --shard-count. Shards are zero-indexed.",
    )
    parser.add_argument("-u", "--push", help="Push images.", action="store_true")
    parser.add_argument("-d", "--dry", help="Dry run.", action="store_true")
    parser.add_argument(
        "-a",
        "--architecture",
        help="Target platform for image. Default: linux/amd64.",
        default="linux/amd64",
        type=check_architecture_input,
    )
    parser.add_argument(
        "-o",
        "--organization",
        help="Organization name within the given registry. Default: stackable.",
        default="stackable",
    )
    parser.add_argument(
        "-r",
        "--registry",
        help="Image registry to publish to. Default: docker.stackable.tech.",
        default="docker.stackable.tech",
    )
    parser.add_argument(
        "--export-tags-file",
        help="Write target image tags to a text file. Useful for signing or other follow-up CI steps.",
    )

    parser.add_argument("--cache", help="Enable distributed build cache", action="store_true")

    parser.add_argument(
        "--build-arg",
        help="Override build arguments. Expecting an KEY=VALUE format. The key is case insensitive.",
        nargs="*",
        type=check_build_arg,
    )

    result = parser.parse_args()

    if result.shard_index >= result.shard_count:
        raise ValueError(
            "shard index [{}] cannot be greater or equal than shard count [{}]".format(
                result.shard_index, result.shard_count
            )
        )
    return result


def positive_int(value) -> int:
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise ValueError
        return ivalue
    except ValueError:
        raise ValueError(f"Invalid value [{value}]. Must be an integer greater than or equal to zero.")


def check_image_version_format(image_version) -> str:
    """
    Check image version against allowed formats.

    >>> check_image_version_format("23.4.0")
    '23.4.0'
    >>> check_image_version_format("23.4.0-rc1")
    '23.4.0-rc1'
    >>> check_image_version_format("0.0.0-dev")
    '0.0.0-dev'
    >>> check_image_version_format("0.0.0-dev-kebab")
    '0.0.0-dev-kebab'
    >>> check_image_version_format("23.11.1-dev-kaese")
    '23.11.1-dev-kaese'
    >>> check_image_version_format("23.04.0")
    Traceback (most recent call last):
    ...
    ValueError: Invalid image version: 23.04.0
    >>> check_image_version_format("23.4.0.prerelease")
    Traceback (most recent call last):
    ...
    ValueError: Invalid image version: 23.4.0.prerelease
    """
    for p in DEFAULT_IMAGE_VERSION_FORMATS:
        if p.fullmatch(image_version):
            return image_version
    raise ValueError(f"Invalid image version: {image_version}")


def check_build_arg(build_args: str) -> Tuple[str, str]:
    kv = build_args.split("=")
    if len(kv) != 2:
        raise ValueError
    return kv[0], kv[1]


def preflight_args() -> Namespace:
    parser = ArgumentParser(
        description="Run OpenShift certification checks and submit results to RedHat Partner Connect portal"
    )

    parser.add_argument("-v", "--version", help="Display version", action="store_true")

    parser.add_argument(
        "-i",
        "--image-version",
        help="Image version",
        required=True,
        type=check_image_version_format,
    )
    parser.add_argument("-p", "--product", help="Product to build images for", required=True)
    parser.add_argument("-s", "--submit", help="Submit results", action="store_true")
    parser.add_argument("-d", "--dry", help="Dry run.", action="store_true")
    parser.add_argument(
        "-a",
        "--architecture",
        help="Target platform for image. Default: linux/amd64.",
        default="linux/amd64",
        type=check_architecture_input,
    )
    parser.add_argument(
        "-t",
        "--token",
        help="RedHat portal API token",
    )
    parser.add_argument(
        "-o",
        "--organization",
        help="Organization name within the given registry. Default: stackable",
        default="stackable",
    )
    parser.add_argument(
        "-r",
        "--registry",
        help="Image registry to publish to. Default: docker.stackable.tech",
        default="docker.stackable.tech",
    )
    parser.add_argument(
        "-e",
        "--executable",
        help="Name of the preflight program. Default: preflight",
        default="preflight",
    )
    parser.add_argument(
        "-c",
        "--configuration",
        help="Configuration file.",
        default="./conf.py",
    )

    result = parser.parse_args()

    if result.submit and not result.token:
        raise ValueError("Missing API token for submitting results.")

    # Dummy property needed by the generate_bakefile() function
    # but not used by the preflight tool.
    result.cache = False

    return result


def check_architecture_input(architecture: str) -> str:
    supported_arch = ["linux/amd64", "linux/arm64"]

    if architecture not in supported_arch:
        raise ValueError(f"Architecture {architecture} not supported. Supported: {supported_arch}")

    return architecture


def load_configuration(conf_file_name: str, user_build_args: List[Tuple[str, str]] = []) -> ModuleType:
    """Load the configuration module conf.py and potentially override build arguments
    with values provided by the user with the --build-arg flag.
    The build arguments are key, value pairs from the "conf.products.<product name>.versions.<version>" dictionary.
    """
    module_name = "conf"
    sys.path.append(str(os.getcwd()))
    spec = importlib.util.spec_from_file_location(module_name, conf_file_name)
    if spec:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        if spec.loader:
            spec.loader.exec_module(module)
            override_build_args(module, user_build_args)
            return module
    raise ImportError(name=module_name, path=conf_file_name)


def override_build_args(conf: ModuleType, user_build_args: List[Tuple[str, str]] = []) -> None:
    if not user_build_args:
        return
    # convert user_build_args to a dictionary for easier lookup
    user_build_args_dict = {kv[0]: kv[1] for kv in user_build_args}
    for product in conf.products:
        for conf_build_args in product["versions"]:
            for arg in conf_build_args:
                if arg in user_build_args_dict:
                    conf_build_args[arg] = user_build_args_dict[arg]
