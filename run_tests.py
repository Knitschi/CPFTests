#!/usr/bin/python3
"""
Runs all high-level tests of the CMakeProjectFramework.

Arguments:
The script takes keyword arguments in the form

test_dir="C:/mytests" -> A base directory in which the script can put temporary files for tests.
parent_config=VS      -> The configuration from which the current config derives. Testprojects will be build in this configuration.
test_name             -> Determines the tests that is run. If the value is empty, it will run all tests.
"""

import unittest
import sys

from .testprojectfixture import BASE_TEST_DIR, PARENT_CONFIG

# tests
from .acpftestproject_tests import *
from .bcpftestproject_tests import *
from .misc_tests import *
from .simpleonelibcpftestproject_tests import *


def parseKeyWordArgs( arglist ):
    """
    The function takes a list of strings of the shape
    bla=2 bli='blub' and sets fills a dictionary with
    them which then is returned.
    """
    arg_dict = {}
    for arg in arglist[1:]:
        # check that argument has the equal sign
        index = arg.find('=')
        if index == -1:
            raise Exception('Argument "{0}" does not seem to be a keyword argument.'.format(arg))
        # check that argument has a keyword.
        if index == 0:
            raise Exception('Argument "{0}" is missing a keyword before the "=".'.format(arg))
        
        keyword = arg[:index]
        value = arg[index+1:]

        # strip quotes from value
        firstchar = value[:1]
        if firstchar == "'":
            value = value.strip("'")
        elif firstchar == '"':
            value = value.strip('"')

        arg_dict[keyword] = value

    return arg_dict

def getKeywordArgument(keyword, keywordargs):
    if not keyword in keywordargs:
        raise Exception('Test script requires {0} argument.'.format(keyword))
    return keywordargs[keyword]


if __name__ == '__main__':

    # Get the script arguments
    keywordargs = parseKeyWordArgs(sys.argv)
    testprojectfixture.BASE_TEST_DIR = getKeywordArgument('test_dir', keywordargs)
    testprojectfixture.PARENT_CONFIG = getKeywordArgument('parent_config', keywordargs)
    test_name = getKeywordArgument('test_name', keywordargs)
    # run all tests by default
    if test_name == '':
        test_name = 'run_tests'

    # Run the tests
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromName('Sources.CPFTests.' + test_name)
    result = unittest.TextTestRunner(failfast=True).run(suite)
    sys.exit(not result.wasSuccessful())


