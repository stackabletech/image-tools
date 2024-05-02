"""Image builder

Requirements: docker and buildx.

Usage:

    python -m image_tools.bake -p opa -i 22.12.0
"""
import sys
from typing import List, Dict, Any
from argparse import Namespace
from subprocess import run
import json

from image_tools.lib import Command
from image_tools.args import bake_args, load_configuration


def build_image_args(version: Dict[str, str], release_version: str):
    """
    Returns a list of --build-arg command line arguments that are used by the
    docker build command.

    Arguments:
    - version: Can be a str, in which case it's considered the PRODUCT
                or a dict.
    """
    result = {}

    for k, v in version.items():
        result[k.upper()] = v
    result["RELEASE"] = release_version

    return result


def build_image_tags(
        image_name: str, image_version: str, product_version: str
) -> List[str]:
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
    targets = {}
    groups = {}
    product_names: list[str] = [product["name"] for product in conf.products]
    for product in conf.products:
        product_name: str = product["name"]
        product_targets = {}
        for version_dict in product.get("versions", []):
            product_targets.update(
                bakefile_product_version_targets(
                    args, product_name, version_dict, product_names
                )
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
):
    """
    Creates Bakefile targets defining how to build a given product version.

    A product is assumed to depend on another if it defines a `versions` field with the same name as the other product.
    """
    image_name = f"{args.registry}/{args.organization}/{product_name}"
    tags = build_image_tags(
        image_name, args.image_version, versions["product"])
    build_args = build_image_args(versions, args.image_version)

    return {
        bakefile_target_name_for_product_version(product_name, versions["product"]): {
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


def targets_for_selector(conf, selected_products: List[str]) -> List[str]:
    targets = []
    for selected_product in selected_products or (product['name'] for product in conf.products):
        product_name, *versions = selected_product.split("=")
        product = next(
            (product for product in conf.products if product['name'] == product_name), None)
        if product is None:
            raise ValueError(f"Requested unknown product [{product_name}]")
        for version in versions or (version['product'] for version in product['versions']):
            targets.append(bakefile_target_name_for_product_version(
                product_name, version))
    return targets


def filter_targets_for_shard(targets: List[str], shard_count: int, shard_index: int) -> List[str]:
    return [target for i, target in enumerate(targets) if i % shard_count == shard_index]


def bake_command(args: Namespace, targets: List[str], bakefile) -> Command:
    """
    Returns a list of commands that need to be run in order to build and
    publish product images.

    For local building, builder instances are supported.
    """

    if args.push:
        target_mode = ["--push"]
    else:
        target_mode = ["--load"]

    if args.dry:
        target_mode = ["--print"]

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


def main() -> int:
    """Generate a Docker bake file from conf.py and build the given args.product images."""
    args = bake_args()

    conf = load_configuration(args.configuration)

    bakefile = generate_bakefile(args, conf)

    targets = filter_targets_for_shard(targets_for_selector(
        conf, args.product), args.shard_count, args.shard_index)

    if not targets:
        print("No targets match this filter")
        return 0

    cmd = bake_command(args, targets, bakefile)

    if args.dry:
        print(" ".join(cmd.args))

    result = run(cmd.args, input=cmd.input, check=True)

    if args.export_tags_file:
        with open(args.export_tags_file, 'w') as tf:
            for t in targets:
                tf.writelines(
                    (f"{t}\n" for t in bakefile["target"][t]["tags"]))

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
