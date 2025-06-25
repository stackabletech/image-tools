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

DEFAULT_RELEASE_FORMATS = [
    re.compile(r"[2-9][0-9]\.[1-9][0-2]?\.\d+(-rc\d+)?"),
    re.compile(r"0\.0\.0-dev"),
]


def build_bake_argparser() -> ArgumentParser:
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
        "--release",
        type=check_release_format,
        default="0.0.0-dev",
        help="SDP release version. Default: 0.0.0-dev.",
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
        help="Organization name within the given registry. Default: sdp.",
        default="sdp",
    )
    parser.add_argument(
        "-r",
        "--registry",
        help="Image registry to publish to. Default: oci.stackable.tech.",
        default="oci.stackable.tech",
    )
    parser.add_argument(
        "--export-tags-file",
        help="Write target image tags to a text file. Useful for signing or other follow-up CI steps.",
    )

    parser.add_argument("--cache", help="Enable distributed build cache", action="store_true")

    parser.add_argument(
        "--list-products",
        action="store_true",
        help="Display structured output of products and their versions in JSON format",
    )

    parser.add_argument(
        "--build-arg",
        help="Override build arguments. Expecting an KEY=VALUE format. The key is case insensitive.",
        nargs="*",
        type=check_build_arg,
    )

    parser.add_argument(
        "--target-containerfile",
        help="Override the target containerfile used, points to <PRODUCT>/<TARGET_CONTAINERFILE>. Default: Dockerfile",
        default="Dockerfile",
    )

    parser.add_argument(
        "--completions",
        choices=["nushell"],
        help="Generate shell completions. Currently supports: nushell.",
    )

    return parser


def bake_args() -> Namespace:
    parser = build_bake_argparser()

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


def check_release_format(release) -> str:
    """
        Check release against allowed formats.

    >>> check_release_format("23.4.0")
    '23.4.0'
    >>> check_release_format("23.4.0-rc1")
    '23.4.0-rc1'
    >>> check_release_format("0.0.0-dev")
    '0.0.0-dev'
    >>> check_release_format("0.0.0-dev-kebab")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 5, in check_release_format
    ValueError: Invalid release: 0.0.0-dev-kebab
    >>> check_release_format("23.11.1-dev-kaese")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 5, in check_release_format
    ValueError: Invalid release: 23.11.1-dev-kaese
    >>> check_release_format("23.04.0")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 5, in check_release_format
    ValueError: Invalid release: 23.04.0
    >>> check_release_format("23.4.0.prerelease")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 5, in check_release_format
    ValueError: Invalid release: 23.4.0.prerelease
    """
    for p in DEFAULT_RELEASE_FORMATS:
        if p.fullmatch(release):
            return release
    raise ValueError(f"Invalid release: {release}")


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
        help="Image version.",
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
        help="Organization name within the given registry. Default: sdp",
        default="sdp",
    )
    parser.add_argument(
        "-r",
        "--registry",
        help="Image registry to publish to. Default: oci.stackable.tech",
        default="oci.stackable.tech",
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


def load_configuration(conf_file_name: str, cli_build_args: List[Tuple[str, str]] = []) -> ModuleType:
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
            assemble_final_build_args(module, cli_build_args)
            return module
    raise ImportError(name=module_name, path=conf_file_name)


def assemble_final_build_args(conf: ModuleType, cli_build_args: List[Tuple[str, str]] = []) -> None:
    cli_build_args = cli_build_args or []
    # Convert user_build_args to a dictionary with lowercase keys for easier, case-insensitive lookup
    cli_build_args_dict = {k.lower(): v for k, v in cli_build_args}

    global_build_args = {k.lower(): v for k, v in (getattr(conf, "args", {}) or {}).items()}

    for product in conf.products:
        # Prepare a new list to store the updated dictionaries
        updated_args_list = []

        # Iterate through each dictionary in the product["args"] list.
        # Each of those dictonaries represents a version of a product we build.
        for conf_build_args in product.get("versions", []):
            # Normalize product-specific arguments to lower case for all handling in here
            product_args = {k.lower(): v for k, v in conf_build_args.items()}

            # Merge global_build_args and product_args, prioritizing product_args
            merged_args = global_build_args.copy()
            merged_args.update(product_args)

            # Override with CLI-provided args (cli_build_args_dict) -> they have highest priority
            final_args = {**merged_args, **cli_build_args_dict}

            # Add the final arguments to the updated list
            updated_args_list.append(final_args)

        # Update product["versions"] with the new list of merged argument dictionaries
        product["versions"] = updated_args_list
