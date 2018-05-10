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


    def test_target_existence(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()
        
        # Test existence of platform independent targets
        # Global targets
        global_targets = [
            'pipeline',
            'doxygen',
            'distributionPackages',
            'dynamicAnalysis',
            'runAllTests',
            'runFastTests',
            'staticAnalysis',
        ]
        self.assert_targets_build(global_targets)

        # Per package targets
        per_package_targets = [
            'MyLib',
            'MyLib_tests',
            'MyLib_fixtures',
            'distributionPackages_MyLib',
            'install_MyLib',
            'runAllTests_MyLib',
            'runFastTests_MyLib',
        ]
        self.assert_targets_build(per_package_targets)

        # Check existence and non-existence of targets that are only available for certain configurations.
        # MSVC
        msvc_specific_targets = [
            'INSTALL',
            'opencppcoverage_MyLib',
        ]
        if self.is_visual_studio_config():
            self.assert_targets_build(msvc_specific_targets)
        else:
            self.assert_targets_do_not_exist(msvc_specific_targets)

        # Clang
        linux_clang_specific_targets = [
            'install'
            'clang-tidy_MyLib'
        ]
        if self.is_clang_config():
            self.assert_targets_build(linux_clang_specific_targets)
        else:
            self.assert_targets_do_not_exist(linux_clang_specific_targets)

        # Linux debug info
        linux_debug_specific_targets = [
            'valgrind_MyLib',
            'abi-compliance-checker',
            'abi-compliance-checker_MyLib',
        ]
        if self.is_linux_debug_config():
            self.assert_targets_build(linux_debug_specific_targets)
        else:
            self.assert_targets_do_not_exist(linux_debug_specific_targets)


    def test_opencppcoverage_target_works(self):
        """
        Check that the target runs the OpenCppCoverage.exe for the
        compiler debug config and not for the release config.
        """
        if self.is_visual_studio_config():
            # Setup
            self.generate_project()

            # This is a part of the command line call for the tool.
            opencppcoverage_output_signature = 'OpenCppCoverage.exe" --export_type=binary' 

            # check that the tool is run for the debug configuration.
            output = self.build_target('opencppcoverage_MyLib', config='Debug')
            self.assertIn(opencppcoverage_output_signature, output)

            # check that the tool is not run for the release configuration.
            output = self.build_target('opencppcoverage_MyLib', config='Release')
            self.assertNotIn(opencppcoverage_output_signature, output)










        


