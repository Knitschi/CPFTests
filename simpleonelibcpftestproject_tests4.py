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
class SimpleOneLibCPFTestProjectFixture4(simpleonelibcpftestprojectfixture.SimpleOneLibCPFTestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'SimpleOneLibCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/SimpleOneLibCPFTestProject.git', cls.project, cls.instantiating_module)

    def setUp(self):
        super(SimpleOneLibCPFTestProjectFixture4, self).setUp(self.project, self.cpf_root_dir, self.instantiating_module)


    def test_distributionPackages_MyLib_target(self):
        """
        Not that this test only tests if the package is created
        and if it is properly rebuild. The correctness of the 
        the package content is tested in acpftestproject_tests.
        """
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.PACKAGE_ARCHIVES_MYLIB_TARGET

        sources = [
            'Sources/MyLib/function.cpp'
        ]

        # Check the zip file is created.
        distPackagePath = self.get_full_distribution_package_path('MyLib', '7Z', 'CT_DEVELOPER')
        output = [
            distPackagePath
        ]

        # Execute
        self.do_basic_target_tests(target, target, source_files=sources, output_files=output)

    def test_runAllTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.RUN_ALL_TESTS_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_runFastTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.RUN_FAST_TESTS_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_opencppcoverage_MyLib_target(self):
        """
        Check that the target runs the OpenCppCoverage.exe for the
        compiler debug config and not for the release config.
        """
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.OPENCPPCOVERAGE_MYLIB_TARGET
        sources = [
            'Sources/MyLib/function.cpp'
        ]
        output = []
        if self.is_visual_studio_config() and self.is_debug_compiler_config():
            output.extend([
                'MyLib/opencppcoverage_MyLib/MyLib_tests.cov'
            ])

        # Execute
        self.do_basic_target_tests(
            target, 
            target, 
            self.is_visual_studio_debug_config(), 
            not self.is_debug_compiler_config(),
            source_files=sources,
            output_files=output
        )


    def test_clangformat_MyLib_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.CLANG_FORMAT_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)