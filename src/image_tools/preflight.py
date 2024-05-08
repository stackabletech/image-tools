"""OpenShift image validation

Run RedHat's preflight command on images for a product.

Requirements:
* openshift-preflight. See: https://github.com/redhat-openshift-ecosystem/openshift-preflight

Usage:

    python -m image_tools.preflight -p opa -i 23.1.0
"""

from argparse import Namespace
from typing import List, Dict, Any
import subprocess
import json
import sys
import logging

from .args import preflight_args, load_configuration
from .lib import Command
from .bake import generate_bakefile


def get_images_for_target(product: str, bakefile: Dict[str, Any]) -> List[str]:
    tags = []

    for target in bakefile.get("group", {}).get(product, {}).get("targets", []):
        tags.extend(get_images_for_target(target, bakefile))

    tags.extend(bakefile["target"].get(product, {}).get("tags", []))

    return tags


def get_preflight_failures(image_commands: Dict[str, Command]) -> Dict[str, List[Any]]:
    """Run preflight commands for each image and return the failure field of the response."""
    failures = {}
    for image, cmd in image_commands.items():
        try:
            preflight_result = subprocess.run(cmd.args, input=cmd.input, check=True, stdout=subprocess.PIPE)
            preflight_json = json.loads(preflight_result.stdout)
            failures[image] = preflight_json.get("results", {}).get("failed", [])
        except subprocess.CalledProcessError as error:
            failures[image] = [error.stderr.decode("utf-8")]
        except FileNotFoundError:
            failures[image] = [
                "preflight: command not found. Install from https://github.com/redhat-openshift-ecosystem/openshift-preflight"
            ]
        except json.JSONDecodeError as error:
            failures[image] = [error.msg]
    return failures


def preflight_commands(images: List[str], args: Namespace, conf) -> Dict[str, Command]:
    """A mapping of image name to preflight command"""
    result = {}
    for img in images:
        cmd_args = [args.executable, "check", "container", img]
        if args.submit:
            cmd_args.extend(
                [
                    "--loglevel",
                    "trace",
                    "--submit",
                    "--pyxis-api-token",
                    args.token,
                    "--certification-project-id",
                    f"ospid-{conf.open_shift_projects[args.product]['id']}",
                ]
            )
        if args.architecture:
            cmd_args.extend(
                [
                    "--platform",
                    # this argument value has already been checked against valid values with an expected prefix.
                    # Preflight provides the same "linux/" prefix and so it must be removed here.
                    args.architecture.split("linux/")[1],
                ]
            )
        result[img] = Command(args=cmd_args)
    return result


def main() -> int:
    """Run OpenShift verification checks against the product images."""
    logging.basicConfig(
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    args = preflight_args()

    conf = load_configuration(args.configuration)

    bakefile = generate_bakefile(args, conf)

    # List of images (with tags) to apply preflight checks to.
    # Filter out images with platform release tags such as "23.4" and
    # only check images with patch versions such as "23.4.0".
    images = list(
        filter(
            lambda i: i.endswith(args.image_version),
            get_images_for_target(args.product, bakefile),
        )
    )
    if not images:
        logging.error("No images found for product [%s]", args.product)
        return 1

    # A mapping of image name to preflight command
    image_commands = preflight_commands(images, args, conf)

    if args.dry:
        for _, cmd in image_commands.items():
            logging.info(str(cmd))
        return 0

    # Run preflight and return failures
    failures = get_preflight_failures(image_commands)

    for image, img_fails in failures.items():
        if len(img_fails) == 0:
            logging.info("Image [%s] preflight check successful.", image)
        else:
            logging.error("Image [%s] preflight check failures: %s", image, ",".join(img_fails))

    fail_count = sum(map(len, failures.values()))
    return fail_count


if __name__ == "__main__":
    sys.exit(main())
