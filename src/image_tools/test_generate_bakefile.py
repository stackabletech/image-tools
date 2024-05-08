from image_tools.test import conf
import unittest
import sys

from image_tools.args import bake_args
from image_tools.bake import generate_bakefile


class TestGenerateBakefile(unittest.TestCase):
    def test_generate_bakefile(self):
        sys.argv = ["test", "-p", "airflow"]
        bargs = bake_args()
        bakefile = generate_bakefile(bargs, conf)
        self.assertIsNotNone(bakefile)
