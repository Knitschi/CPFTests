#!/usr/bin/python3
"""
Runs all high-level tests of the CMakeProjectFramework.

Arguments:
The script takes keyword arguments in the form

test_dir="C:/mytests" -> A base directory in which the script can put temporary files for tests.
parent_config=VS      -> The configuration from which the current config derives. Testprojects will be build in this configuration.
compiler_config=Debug -> For multi-configuration generators, the compiler config that is used to build Testprojects.
module                -> The module (python '*_tests.py' file) from which we want to run the tests. e.g. acpftestproject_tests
test_filter           -> Only run test cases with names that contain the filter string. e.g. test_distributionPackages_content
"""

import unittest
import sys

from .testprojectfixture import BASE_TEST_DIR, PARENT_CONFIG

# tests
from .acpftestproject_tests import *
from .bcpftestproject_tests import *
from .ccpftestproject_tests import *
from .misc_tests import *
from .simpleonelibcpftestproject_tests1 import *
from .simpleonelibcpftestproject_tests2 import *
from .simpleonelibcpftestproject_tests3 import *
from .simpleonelibcpftestproject_tests4 import *
from .simpleonelibcpftestproject_tests5 import *
from .distpackageconsumption_tests import *


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


def getTestNames():
    """
    Returns a list with all the dotted test names that can be found, e.g. 
    ['Sources.CPFTests.simpleonelibcpftestproject_tests.SimpleOneLibCPFTestProjectFixture.test_doxygen_target',
    'Sources.CPFTests.simpleonelibcpftestproject_tests.ACPFTestProjectFixture.test_pipeline_works'
    ]
    """

    # Get a list with all full test function names so we can filter them.
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromName('Sources.CPFTests.run_tests')
    return getTestNamesFromSuite(suite, test_loader)


def getTestNamesFromSuite(suite, test_loader):
    fullTestNames = []
    for moduleTests in suite._tests:
        for test in moduleTests._tests:
            testNames = test_loader.getTestCaseNames(test)
            for testName in testNames:
                fullTestNames.append(test.__class__.__module__ + '.' + test.__class__.__name__ + '.' + testName)

    # Remove duplicates (which exist for unknown reasons)
    fullTestNames = list(dict.fromkeys(fullTestNames))
    return fullTestNames


def filterTests(module, testFilter, testNames):
    """
    Filters out all test names that do not belong to the given module or where one name component
    equals the testFilter string.
    """
    filteredNames = []
    for testName in testNames:
        nameComponents = testName.split('.')

        testIsFromModule = module in nameComponents
        hasTestFilter = True
        if testFilter:
            hasTestFilter = testFilter in nameComponents

        if testIsFromModule and hasTestFilter:
            filteredNames.append(testName)

    return filteredNames


def runTests(testNames):

    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromNames(testNames)
    names = getTestNamesFromSuite(suite, test_loader)
    result = unittest.TextTestRunner(failfast=True).run(suite)
    return not result.wasSuccessful()


if __name__ == '__main__':

    # Get the script arguments
    keywordargs = parseKeyWordArgs(sys.argv)
    testprojectfixture.BASE_TEST_DIR = getKeywordArgument('test_dir', keywordargs)
    testprojectfixture.PARENT_CONFIG = getKeywordArgument('parent_config', keywordargs)
    testprojectfixture.COMPILER_CONFIG = getKeywordArgument('compiler_config', keywordargs)
    testFilter = getKeywordArgument('test_filter', keywordargs)
    module = getKeywordArgument('module', keywordargs)
    
    # Get all tests in the suite
    allTests = getTestNames()
    # Remove test names that do not contain the filter and module string.
    filteredTests = filterTests(module, testFilter, allTests)

    #pprint.pprint(filteredTests)

    # Run the selected Tests
    retVal = 0
    if filteredTests:
        result = runTests(filteredTests)

    sys.exit(retVal)




