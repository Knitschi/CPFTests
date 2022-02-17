"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint
import types
import datetime
import sys
from pathlib import PureWindowsPath, PurePosixPath, PurePath


from Sources.CPFBuildscripts.python import miscosaccess
from . import testprojectfixture
from . import simpleonelibcpftestprojectfixture


############################################################################################
class SimpleOneLibCPFTestProjectFixture2(simpleonelibcpftestprojectfixture.SimpleOneLibCPFTestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    cpf_cmake_dir = 'Sources/external/CPFCMake'
    ci_buildconfigurations_dir = 'Sources/external/CIBuildConfigurations'
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'SimpleOneLibCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/SimpleOneLibCPFTestProject.git', cls.project, cls.cpf_cmake_dir, cls.cpf_buildscripts_dir, cls.instantiating_module)

    def setUp(self):
        super(SimpleOneLibCPFTestProjectFixture2, self).setUp(self.instantiating_module)


    def test_runFastTests_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.RUN_FAST_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, simpleonelibcpftestprojectfixture.RUN_FAST_TESTS_MYLIB_TARGET)


    def test_clangformat_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.CLANGFORMAT_TARGET

        # Execute
        # Check the target builds
        self.do_basic_target_tests(target, simpleonelibcpftestprojectfixture.CLANG_FORMAT_MYLIB_TARGET)


    def test_clangtidy_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.CLANGTIDY_TARGET

        # Execute
        # Check the target builds
        self.do_basic_target_tests(target, simpleonelibcpftestprojectfixture.CLANG_TIDY_MYLIB_TARGET, target_exists=self.is_clang_config())


    def test_acylic_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.ACYCLIC_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_valgrind_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.VALGRIND_TARGET
        sources = [
            'Sources/MyLib/function.cpp',
        ]

        # Execute
        self.do_basic_target_tests( 
            target, 
            simpleonelibcpftestprojectfixture.VALGRIND_MYLIB_TARGET, 
            target_exists=self.is_linux_debug_config(),
            source_files=sources
        )