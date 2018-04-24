#!/usr/bin/python3
"""
Runs all high-level tests of the CMakeProjectFramework.

Arguments:
1. The test files directory.
2. The configuration from which the current config derives.
"""

import unittest
import sys

from .TestProject_tests import ExcecuteCommandCase
from .TestProject_tests import SimpleOneLibCPFTestProjectFixture


#from .TestProject_tests import TestProjectFixture
from . import TestProject_tests

if __name__ == '__main__':
    TestProject_tests.BASE_TEST_DIR = sys.argv[1]
    TestProject_tests.PARENT_CONFIG = sys.argv[2]
    del(sys.argv[1])
    del(sys.argv[1])
    unittest.main()

