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
class SimpleOneLibCPFTestProjectFixture3(simpleonelibcpftestprojectfixture.SimpleOneLibCPFTestProjectFixture):
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
        super(SimpleOneLibCPFTestProjectFixture3, self).setUp(self.instantiating_module)


    def test_opencppcoverage_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.OPENCPPCOVERAGE_TARGET
        sources = [
            'Sources/MyLib/MyLib/function.cpp',
        ]
        
        output = [
            'OpenCppCoverage/Debug/index.html',
        ]

        # Execute
        self.do_basic_target_tests( 
            target, 
            target, 
            target_exists=self.is_visual_studio_debug_config(),
            is_dummy_target=testprojectfixture.COMPILER_CONFIG.lower() != 'debug',
            source_files=sources,
            output_files=output
        )


    def test_install_target(self):
        # Setup
        self.generate_project(d_options=['CMAKE_INSTALL_PREFIX="{0}"'.format(self.cpf_root_dir / 'install_tree')])
        target = simpleonelibcpftestprojectfixture.INSTALL_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_target(self):
        # Setup
        self.generate_project(d_options = ['CMAKE_VERBOSE_MAKEFILE=ON'])
        target = simpleonelibcpftestprojectfixture.MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_Tests_target(self):
        # Setup
        self.generate_project(d_options = ['CMAKE_VERBOSE_MAKEFILE=ON'])
        target = simpleonelibcpftestprojectfixture.MYLIB_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_Fixtures_target(self):
        # Setup
        self.generate_project(d_options = ['CMAKE_VERBOSE_MAKEFILE=ON'])
        target = simpleonelibcpftestprojectfixture.MYLIB_FIXTURES_TARGET

        # Execute
        self.do_basic_target_tests(target, target)