# This is the stackable release version
from argparse import Namespace, ArgumentParser
from typing import List
import re
import importlib.util
import sys

DEFAULT_IMAGE_VERSION_FORMATS = [
    re.compile(r"[2-9][0-9]\.[1-9][0-2]?\.\d+"),
    re.compile(r"[2-9][0-9]\.[1-9][0-2]?\.\d+-rc[1-9]\d?"),
    re.compile(r"0\.0\.0-dev"),
]


def bake_args() -> Namespace:
    parser = ArgumentParser(
        description="Build and publish product images. Requires docker and buildx (https://github.com/docker/buildx)."
    )
    parser.add_argument(
        "-c",
        "--configuration",
        help="Configuration file.",
        default="./conf.py",
    ),
    parser.add_argument(
        "-i",
        "--image-version",
        help="Image version",
        required=True,
        type=check_image_version_format,
    )
    parser.add_argument("-p", "--product", help="Product to build images for")
    parser.add_argument("-u", "--push", help="Push images",
                        action="store_true")
    parser.add_argument("-d", "--dry", help="Dry run.", action="store_true")
    parser.add_argument(
        "-a",
        "--architecture",
        help="Target platform for image. Default: linux/amd64.",
        nargs="+",
        default=["linux/amd64"],
        type=check_architecture_input,
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
    return parser.parse_args()


def check_image_version_format(image_version) -> str:
    """
    Check image version against allowed formats.

    >>> check_image_version_format("23.4.0")
    '23.4.0'
    >>> check_image_version_format("23.4.0-rc1")
    '23.4.0-rc1'
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


def preflight_args() -> Namespace:
    parser = ArgumentParser(
        description="Run OpenShift certification checks and submit results to RedHat Partner Connect portal"
    )
    parser.add_argument(
        "-i",
        "--image-version",
        help="Image version",
        required=True,
        type=check_image_version_format,
    )
    parser.add_argument(
        "-p", "--product", help="Product to build images for", required=True
    )
    parser.add_argument(
        "-s", "--submit", help="Submit results", action="store_true")
    parser.add_argument("-d", "--dry", help="Dry run.", action="store_true")
    parser.add_argument(
        "-a",
        "--architecture",
        help="Target platform for image. Default: linux/amd64.",
        nargs="+",
        default=["linux/amd64"],
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
    ),

    result = parser.parse_args()

    if result.submit and not result.token:
        raise ValueError("Missing API token for submitting results.")

    return result


def check_architecture_input(architecture) -> List[str]:
    supported_arch = ["linux/amd64", "linux/arm64"]

    if architecture not in supported_arch:
        raise ValueError(
            f"Architecture {architecture} not supported. Supported: {supported_arch}"
        )

    return architecture


def load_configuration(conf_file_name: str):
    module_name = "conf"
    spec = importlib.util.spec_from_file_location(module_name, conf_file_name)
    if spec:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        if spec.loader:
            spec.loader.exec_module(module)
            return module
    raise ImportError(name=module_name, path=conf_file_name)
