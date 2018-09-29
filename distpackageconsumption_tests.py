"""
This module contains tests of the created distribution packages.
"""

import unittest
import pprint

from . import testprojectfixture
from . import simpleonelibcpftestproject_tests
from . import cpfpackageconsumertestprojectfixture

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess
from Sources.CPFBuildscripts.python import filelocations



class DistPackageFixture(unittest.TestCase):


    def setUp(self):

        print('-- Run test: {0}'.format(self._testMethodName))

        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        # Checkout the library project.
        simpleonelibcpftestproject_tests.SimpleOneLibCPFTestProjectFixture.setUpClass()
        self.libraryProjectFixture = simpleonelibcpftestproject_tests.SimpleOneLibCPFTestProjectFixture()
        self.libraryProjectFixture.setUp()
        # For now set a release version tag, because the cmake package files only work for release
        # versions.
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")
        self.osa.execute_command("git tag {0}".format(self.getNextReleaseVersion(myLibVersion)), self.libraryProjectFixture.cpf_root_dir)

        # Checkout the consumer project.
        cpfpackageconsumertestprojectfixture.CPFPackageConsumerTestProjectFixture.setUpClass()
        self.consumerProjectFixture = cpfpackageconsumertestprojectfixture.CPFPackageConsumerTestProjectFixture()
        
        self.consumerProjectFixture.setUp()


    def tearDown(self):
        self.libraryProjectFixture.tearDown()
        self.consumerProjectFixture.tearDown()


    def getNextReleaseVersion(self, currentVersion):
        versionElements = currentVersion.split('.')
        versionElements = versionElements[0:3] # remove the non release part
        versionElements[2] = str(int(versionElements[2]) + 1) # increment patch version
        return '.'.join(versionElements)


    def get_package_file_we(self, version, compilerConfig):
        return "MyLib.{0}.{1}.dev-bin.{2}".format(version, self.osa.system(), compilerConfig)


    def test_consume_the_simple_test_project_library(self):
        """
        This test builds the distribution packages of the SimpleOneLibCPFTestProject
        and tests for one of them if the package can be used within the CPFPackageConsumerTestProject.
        """
        # ------------------- Setup -----------------------

        # Create a distribution package for each compiler config and deploy it in the consumer project.
        self.libraryProjectFixture.generate_project()
        compilerConfigs = self.libraryProjectFixture.get_compiler_configs()
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")
        commonPackageDirectory = self.consumerProjectFixture.cpf_root_dir / "MyLib.{0}.{1}.dev-bin".format(myLibVersion, self.osa.system()) / "MyLib"   # Note that the last MyLib is required or the pathes in the target properties will not be correct.
 
        for config in compilerConfigs:
            
            # Build the library project
            self.libraryProjectFixture.build_target("distributionPackages", config=config)

            # Copy binary packages to the consumer package
            packageFileWE = self.get_package_file_we(myLibVersion, config)
            packageFileShort = packageFileWE + ".7z"
            packageFile = self.libraryProjectFixture.locations.get_full_path_config_makefile_folder(testprojectfixture.PARENT_CONFIG).joinpath("html/Downloads/MyLib/LastBuild").joinpath(packageFileShort)
            self.fsa.copyfile(packageFile, self.consumerProjectFixture.cpf_root_dir / packageFileShort)

            # Unzip the binary package
            self.osa.execute_command_output("cmake -E tar xzf " + packageFileShort, self.consumerProjectFixture.cpf_root_dir, print_output=miscosaccess.OutputMode.ON_ERROR, print_command=False)

            # Copy the package content into a directory that contains the package contents of all compiler configurations.
            configPackageDir = self.consumerProjectFixture.cpf_root_dir / packageFileWE
            self.fsa.copytree(configPackageDir / "MyLib", commonPackageDirectory)
            self.fsa.rmtree(configPackageDir)


        # Delete the library project to make sure possible references to
        # the original directory cause errors.
        self.fsa.rmtree(self.libraryProjectFixture.cpf_root_dir)

        # ------------------- Execute -----------------------

        # Build the consumer project.
        packageFileWE = self.get_package_file_we(myLibVersion, testprojectfixture.COMPILER_CONFIG)
        self.consumerProjectFixture.generate_project([
            "MYLIB_VERSION={0}".format(myLibVersion),
            "MYLIB_LOCATION={0}".format(commonPackageDirectory)
            ])
        self.consumerProjectFixture.build_target("ALL_BUILD")


        # ------------------- Verify -----------------------

        # Check that the deployment of the external dll works by running the executable
        consumerVersion = self.consumerProjectFixture.get_package_version('MyLibConsumer')
        consumerExe = self.consumerProjectFixture.get_package_executable_path_in_build_tree(
            'MyLibConsumer',
            testprojectfixture.PARENT_CONFIG,
            testprojectfixture.COMPILER_CONFIG,
            consumerVersion
        )
        self.assertTrue(self.osa.execute_command(str(consumerExe) , self.consumerProjectFixture.cpf_root_dir))
        
        # Assert that the binary output directory of one config does not contain deployed dlls from another.
        for config in compilerConfigs:
            otherConfigs = list(set(compilerConfigs) - set([config]))
            for otherConfig in otherConfigs:
                binaryOutputDirConfig = self.consumerProjectFixture.locations.get_full_path_binary_output_folder(
                    "MyLibConsumer",
                    testprojectfixture.PARENT_CONFIG,
                    config
                )
                dllFile = binaryOutputDirConfig / "MyLib-{0}.dll".format(otherConfig.lower())

                self.consumerProjectFixture.assert_target_does_not_create_files("MyLibConsumer", [dllFile])

        # Assert .pdb files are deployed in debug configuration when MyLib is a shared library.
        # This tests the pdb deployment for imported targets.
        if self.consumerProjectFixture.is_shared_libraries_config():
            debugConfig = "Debug"
            binaryOutputDirConfig = self.consumerProjectFixture.locations.get_full_path_binary_output_folder(
                "MyLibConsumer",
                testprojectfixture.PARENT_CONFIG,
                debugConfig
            )

            pdbFileLib = binaryOutputDirConfig / "MyLib-{0}.pdb".format(debugConfig.lower())
            pdbFileFixtureLib = binaryOutputDirConfig / "MyLib_fixtures-{0}.pdb".format(debugConfig.lower())
            self.consumerProjectFixture.assert_target_output_files_exist("MyLibConsumer", [pdbFileLib, pdbFileFixtureLib])


