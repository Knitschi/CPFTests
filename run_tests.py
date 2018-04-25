#!/usr/bin/python3
"""
Runs all high-level tests of the CMakeProjectFramework.

Arguments:
1. The test files directory.
2. The configuration from which the current config derives.
"""

import unittest
import sys

from .testprojectfixture import BASE_TEST_DIR, PARENT_CONFIG

# tests
from .acpftestproject_tests import *
from .bcpftestproject_tests import *
from .misc_tests import *
from .simpleonelibcpftestproject_tests import *


if __name__ == '__main__':
    testprojectfixture.BASE_TEST_DIR = sys.argv[1]
    testprojectfixture.PARENT_CONFIG = sys.argv[2]
    del(sys.argv[1])
    del(sys.argv[1])
    unittest.main()

