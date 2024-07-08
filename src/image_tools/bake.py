"""Image builder

Requirements: docker and buildx.

Usage:

    python -m image_tools.bake -p opa -i 22.12.0
"""

import copy
import json
import logging
import sys
from argparse import Namespace
from datetime import datetime, timezone
from functools import cache
from subprocess import CalledProcessError, run
from typing import Any, Dict, List

from .args import bake_args, load_configuration
from .lib import Command
from .version import version


def build_image_args(conf_build_args: Dict[str, str], release_version: str):
    """
    Returns a list of --build-arg command line arguments that are used by the
    docker build command.

    Arguments:
    - version: Can be a str, in which case it's considered the PRODUCT
                or a dict.
    """
    result = {}

    for k, v in conf_build_args.items():
        result[k.upper()] = v
    result["RELEASE"] = release_version

    return result


def build_image_tags(image_name: str, image_version: str, product_version: str) -> List[str]:
    """
    Returns a list of --tag command line arguments that are used by the
    docker build command.
    """
    return [
        f"{image_name}:{product_version}-stackable{image_version}",
    ]


def generate_bakefile(args: Namespace, conf) -> Dict[str, Any]:
    """
    Generates a Bakefile (https://docs.docker.com/build/bake/file-definition/) describing how to build the image graph.

    build_and_publish_images() ensures that only the desired images are actually built.
    """
    build_cache = []
    try:
        build_cache = conf.cache
    except AttributeError:
        pass
    targets = {}
    groups = {}
    product_names: list[str] = [product["name"] for product in conf.products]
    for product in conf.products:
        product_name: str = product["name"]
        product_targets = {}
        for version_dict in product.get("versions", []):
            product_targets.update(
                bakefile_product_version_targets(args, product_name, version_dict, product_names, build_cache)
            )
        groups[product_name] = {
            "targets": list(product_targets.keys()),
        }
        targets.update(product_targets)
    groups["default"] = {
        "targets": list(groups.keys()),
    }
    return {
        "target": targets,
        "group": groups,
    }


def bakefile_target_name_for_product_version(product_name: str, version: str) -> str:
    """
    Creates a normalized Bakefile target name for a given (product, version) combination.
    """
    return f"{product_name}-{version.replace('.', '_')}"


def bakefile_product_version_targets(
    args: Namespace,
    product_name: str,
    versions: Dict[str, str],
    product_names: List[str],
    cache: List[Dict[str, str]],
):
    """
    Creates Bakefile targets defining how to build a given product version.

    A product is assumed to depend on another if it defines a `versions` field with the same name as the other product.
    """
    image_name = f"{args.registry}/{args.organization}/{product_name}"
    tags = build_image_tags(image_name, args.image_version, versions["product"])
    build_args = build_image_args(versions, args.image_version)
    target_name = bakefile_target_name_for_product_version(product_name, versions["product"])
    rfc3339_date_time = datetime.now(timezone.utc).isoformat()
    revision = get_git_revision()

    # The build-date label is set on UBI images automatically so we want to override it to not cause confusion even though it means we have the same date in the labels multiple times
    result = {
        target_name: {
            "annotations": [
                f"org.opencontainers.image.created={rfc3339_date_time}",
                f"org.opencontainers.image.revision={revision}",
            ],
            "labels": {
                "org.opencontainers.image.created": rfc3339_date_time,
                "build-date": rfc3339_date_time,
                "org.opencontainers.image.revision": revision,
            },
            "dockerfile": f"{product_name}/Dockerfile",
            "tags": tags,
            "args": build_args,
            "platforms": [args.architecture],
            "context": ".",
            "contexts": {
                f"stackable/image/{name}": f"target:{bakefile_target_name_for_product_version(name, version)}"
                for name, version in versions.items()
                if name in product_names
            },
        },
    }

    if args.cache:
        result[target_name]["cache-to"] = result[target_name]["cache-from"] = generate_cache_location(
            cache, target_name, args.architecture
        )

    return result


def targets_for_selector(conf, selected_products: List[str]) -> List[str]:
    targets = []
    for selected_product in selected_products or (product["name"] for product in conf.products):
        product_name, *versions = selected_product.split("=")
        product = next((product for product in conf.products if product["name"] == product_name), None)
        if product is None:
            raise ValueError(f"Requested unknown product [{product_name}]")
        for ver in versions or (ver["product"] for ver in product["versions"]):
            targets.append(bakefile_target_name_for_product_version(product_name, ver))
    return targets


def filter_targets_for_shard(targets: List[str], shard_count: int, shard_index: int) -> List[str]:
    return [target for i, target in enumerate(targets) if i % shard_count == shard_index]


def bake_command(args: Namespace, targets: List[str], bakefile) -> Command:
    """
    Returns a list of commands that need to be run in order to build and
    publish product images.

    For local building, builder instances are supported.
    """

    if args.dry:
        target_mode = ["--print"]
    else:
        if args.push:
            target_mode = ["--push"]
        else:
            target_mode = ["--load"]

    return Command(
        args=[
            "docker",
            "buildx",
            "bake",
            "--file",
            "-",
            *targets,
            *target_mode,
        ],
        stdin=json.dumps(bakefile),
    )


def generate_cache_location(cache: List[Dict[str, str]], target_name: str, arch: str) -> List[str]:
    cache_copy = copy.deepcopy(cache)
    result = []

    for backend in cache_copy:
        if "ref_prefix" in backend:
            # Need to replace the / from values like linux/amd64 because otherwise
            # the cache ref would be invalid.
            arch = arch.replace("/", "_")
            backend["ref"] = f"{backend['ref_prefix']}:{target_name}-{arch}"
            del backend["ref_prefix"]
        result.append(",".join([f"{k}={v}" for k, v in backend.items()]))

    return result


def main() -> int:
    """Generate a Docker bake file from conf.py and build the given args.product images."""
    args = bake_args()

    if args.version:
        print(version())
        return 0

    conf = load_configuration(args.configuration, args.build_arg)

    bakefile = generate_bakefile(args, conf)

    targets = filter_targets_for_shard(targets_for_selector(conf, args.product), args.shard_count, args.shard_index)

    if not targets:
        print("No targets match this filter")
        return 0

    cmd = bake_command(args, targets, bakefile)

    if args.dry:
        print(" ".join(cmd.args))

    result = run(cmd.args, input=cmd.input, check=True)

    if args.export_tags_file:
        with open(args.export_tags_file, "w") as tf:
            for t in targets:
                tf.writelines((f"{t}\n" for t in bakefile["target"][t]["tags"]))

    return result.returncode


@cache
def get_git_revision():
    try:
        result = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except CalledProcessError as e:
        logging.error("Failed to get git revision", e)
        return None


if __name__ == "__main__":
    sys.exit(main())
