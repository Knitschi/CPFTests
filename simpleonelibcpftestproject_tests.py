"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint

from Sources.CPFBuildscripts.python import miscosaccess

from . import testprojectfixture


############################################################################################
class SimpleOneLibCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """
    def setUp(self):
        self.project = 'SimpleOneLibCPFTestProject'
        self.repository = 'https://github.com/Knitschi/SimpleOneLibCPFTestProject.git'
        super(SimpleOneLibCPFTestProjectFixture, self).setUp()


    def assert_targets_build(self, targets):
        for target in targets:
            self.run_python_command('3_Make.py --target {0}'.format(target))


    def assert_targets_do_not_exist(self, targets):
        for target in targets:
            with self.assertRaises(miscosaccess.CalledProcessError) as cm:
                # The reason to not print the output of the failing call ist, that MSBuild seems to parse
                # its own output to determine if an error happened. When a nested MSBuild call fails, the
                # parent call itself will also fail even if the nested call was supposed to fail like here.
                self.run_python_command('3_Make.py --target {0}'.format(target), print_output=miscosaccess.OutputMode.NEVER)
            # error MSB1009 says that a project is missing, which means the target does not exist.
            self.assertIn('MSBUILD : error MSB1009:', cm.exception.stdout)


    def test_target_builds_work(self):
        """
        Check that the pipeline target builds.
        """
        # pipeline build
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')

        # Test existence of platform independent targets
        # Global targets
        self.run_python_command('3_Make.py --target doxygen')
        self.run_python_command('3_Make.py --target distributionPackages')
        self.run_python_command('3_Make.py --target dynamicAnalysis')
        self.run_python_command('3_Make.py --target runAllTests')
        self.run_python_command('3_Make.py --target runFastTests')
        self.run_python_command('3_Make.py --target staticAnalysis')
        self.run_python_command('3_Make.py --target INSTALL')

        # Per package targets
        self.run_python_command('3_Make.py --target MyLib')
        self.run_python_command('3_Make.py --target MyLib_tests')
        self.run_python_command('3_Make.py --target MyLib_fixtures')
        self.run_python_command('3_Make.py --target distributionPackages_MyLib')
        self.run_python_command('3_Make.py --target install_MyLib')
        self.run_python_command('3_Make.py --target runAllTests_MyLib')
        self.run_python_command('3_Make.py --target runFastTests_MyLib')


        # Check existence and non-existence of targets that
        # are only available for certain configurations.
        visual_studio_debug_specific_targets = [
            'opencppcoverage_MyLib'
        ]

        linux_clang_specific_targets = [
            'clang-tidy_MyLib'
        ]

        linux_debug_specific_targets = [
            'valgrind_MyLib',
            'abi-compliance-checker-report_MyLib'
        ]

        if self.is_visual_studio_config():
            self.assert_targets_build(visual_studio_debug_specific_targets)
        else:
            self.assert_targets_do_not_exist(visual_studio_debug_specific_targets)

        if self.is_clang_config():
            self.assert_targets_build(linux_clang_specific_targets)
        else:
            self.assert_targets_do_not_exist(linux_clang_specific_targets)

        if self.is_linux_debug_config():
            self.assert_targets_build(linux_debug_specific_targets)
        else:
            self.assert_targets_do_not_exist(linux_debug_specific_targets)




    def test_configure_script(self):
        """
        This tests the underlying functionality of the '1_Configure.py' script.
        """
        # SETUP
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')

        # EXECUTE
        # Check that a failed call causes an test exception.
        self.assertRaises(miscosaccess.CalledProcessError, self.run_python_command, '1_Configure.py {0}'.format(testprojectfixture.PARENT_CONFIG))

        # Check that configuring an existing variable works.
        # Test overriding existing variables and setting variables with whitespaces.
        self.run_python_command('1_Configure.py MyConfig --inherits {0} -D CPF_ENABLE_DOXYGEN_TARGET=OFF -D BLUB="bli bla"'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        cmakeCacheVariables = self.osa.execute_command_output('cmake Generated/MyConfig -L', cwd=self.test_dir, print_output=False, print_command=False)
        # Note that variables that are added via 1_Configure.py are always of type string
        self.assertIn('CPF_ENABLE_DOXYGEN_TARGET:STRING=OFF', cmakeCacheVariables)
        self.assertIn('BLUB:STRING=bli bla', cmakeCacheVariables)

        


