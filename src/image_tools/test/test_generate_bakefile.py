from typing import List

from image_tools.test import conf
import unittest

from image_tools.args import bake_args
from image_tools.bake import generate_bakefile


class TestGenerateBakefile(unittest.TestCase):
    def test_generate_bakefile(self):
        args: List[str] = ["-p", "airflow"]
        bargs = bake_args(args)
        bakefile = generate_bakefile(bargs, conf)
        self.assertIsNotNone(bakefile)
