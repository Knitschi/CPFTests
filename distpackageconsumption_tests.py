"""
This module contains tests of the created package archives.
"""

import unittest
import sys
import pprint

from . import testprojectfixture
from . import simpleonelibcpftestproject_tests1
from . import cpfpackageconsumertestprojectfixture

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess
from Sources.CPFBuildscripts.python import filelocations



class DistPackageFixture(unittest.TestCase):


    def setUp(self):

        module = __name__.split('.')[-1]
        print('[{0}] Run test: {1}'.format(module, self._testMethodName))

        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        # Checkout the library project.
        simpleonelibcpftestproject_tests1.SimpleOneLibCPFTestProjectFixture1.setUpClass(module)
        self.libraryProjectFixture = simpleonelibcpftestproject_tests1.SimpleOneLibCPFTestProjectFixture1()
        self.libraryProjectFixture.setUp()
        # For now set a release version tag, because the cmake package files only work for release
        # versions.
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")
        self.osa.execute_command_output(
            "git tag {0}".format(self.getNextReleaseVersion(myLibVersion)),
            cwd=self.libraryProjectFixture.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )

        # Checkout the consumer project.
        cpfpackageconsumertestprojectfixture.CPFPackageConsumerTestProjectFixture.setUpClass(module)
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
        return "MyLib.{0}.{1}.dev.{2}".format(version, self.osa.system(), compilerConfig)

    def assert_consumer_project_builds_and_runs(self):
        """
        This does the following checks.
        - Check the CPFPackageConsumerTestProject builds.
        - Check the MyLibConsumer executable runs without error.
        - Check that .pdb files from the consumed libraries are deployed into the build-tree.
        """
        # Check that the deployment of the external dll works by running the executable
        consumerVersion = self.consumerProjectFixture.get_package_version('MyLibConsumer')
        consumerExe = self.consumerProjectFixture.get_package_executable_path_in_build_tree(
            'MyLibConsumer',
            testprojectfixture.PARENT_CONFIG,
            testprojectfixture.COMPILER_CONFIG,
            consumerVersion
        )
        self.osa.execute_command_output(
            str(consumerExe),
            cwd=self.consumerProjectFixture.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR
        )


    def assert_pdb_files_from_external_package_are_deployed_to_build_tree(self):
        """
        Assert .pdb files are deployed in debug configuration when MyLib is a shared library.
        This tests the pdb deployment for imported targets.
        """
        if self.consumerProjectFixture.is_shared_libraries_config() and self.consumerProjectFixture.is_windows():
            debugConfig = "Debug"
            binaryOutputDirConfig = self.consumerProjectFixture.locations.get_full_path_binary_output_folder(
                "MyLibConsumer",
                testprojectfixture.PARENT_CONFIG,
                debugConfig
            )

            pdbFileLib = binaryOutputDirConfig / "MyLib-{0}.pdb".format(debugConfig.lower())
            pdbFileFixtureLib = binaryOutputDirConfig / "MyLib_fixtures-{0}.pdb".format(debugConfig.lower())
            self.consumerProjectFixture.assert_files_exist([pdbFileLib, pdbFileFixtureLib])


    def test_consume_the_simple_test_project_library_from_distribution_package(self):
        """
        This test builds the package archives of the SimpleOneLibCPFTestProject
        and tests for one of them if the package can be used within the CPFPackageConsumerTestProject.
        """
        # ------------------- Setup -----------------------

        # Create a package archive for each compiler config and deploy it in the consumer project.
        self.libraryProjectFixture.generate_project()
        compilerConfigs = self.libraryProjectFixture.get_compiler_configs()
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")
        commonPackageDirectory = self.consumerProjectFixture.cpf_root_dir / "MyLib.{0}.{1}.dev".format(myLibVersion, self.osa.system()) / "MyLib"   # Note that the last MyLib is required or the paths in the target properties will not be correct.
 
        for config in compilerConfigs:
            
            # Build the library project
            self.libraryProjectFixture.build_target("packageArchives", config=config)

            # Copy binary packages to the consumer package
            packageFileWE = self.libraryProjectFixture.get_distribution_package_name_we('MyLib', config, 'CT_DEVELOPER')
            packageFileShort = packageFileWE + ".7z"
            packageFile = self.libraryProjectFixture.get_distribution_package_directory('MyLib', config, 'CT_DEVELOPER') / packageFileShort
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
        self.consumerProjectFixture.build_target("MyLibConsumer")


        # ------------------- Verify -----------------------
        self.assert_consumer_project_builds_and_runs()
        self.assert_pdb_files_from_external_package_are_deployed_to_build_tree()



    def test_consume_the_simple_test_project_library_from_direct_install(self):
        """
        This test executes the install target of the SimpleOneLibCPFTestProject to copy
        the MyLib package to the CPFPacakgeConsumerTestProject and then checks if
        the consumer project can be build and run.
        """
        # ------------------- Setup -----------------------

        # Execute the install target for each compiler configuration.
        installPrefix = self.consumerProjectFixture.cpf_root_dir / "install"
        self.libraryProjectFixture.generate_project(d_options=['CMAKE_INSTALL_PREFIX={0}'.format(installPrefix)])
        compilerConfigs = self.libraryProjectFixture.get_compiler_configs()
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")

        for config in compilerConfigs:
            # Build and install the library project
            self.libraryProjectFixture.build_target("install", config=config)

        # Delete the library project to make sure unwanted references to
        # the original directory cause errors.
        self.fsa.rmtree(self.libraryProjectFixture.cpf_root_dir)


        # ------------------- Execute -----------------------

        # Build the consumer project.
        packageFileWE = self.get_package_file_we(myLibVersion, testprojectfixture.COMPILER_CONFIG)
        self.consumerProjectFixture.generate_project([
            "MYLIB_VERSION={0}".format(myLibVersion),
            "MYLIB_LOCATION={0}".format(installPrefix)
            ])
        self.consumerProjectFixture.build_target("MyLibConsumer")

        # ------------------- Verify -----------------------
        self.assert_consumer_project_builds_and_runs()
        self.assert_pdb_files_from_external_package_are_deployed_to_build_tree()



    def test_consume_the_simple_test_project_library_with_a_single_compiler_configuration_from_direct_install(self):
        """
        This test checks if the consumer project builds in all compiler configurations
        if the external package only provides a Release configuration.
        """
        # ------------------- Setup -----------------------

        # Execute the install target of the external package for Release configuration only.
        installPrefix = self.consumerProjectFixture.cpf_root_dir / "install"
        self.libraryProjectFixture.generate_project(d_options=['CMAKE_INSTALL_PREFIX={0}'.format(installPrefix)])
        compilerConfigs = self.libraryProjectFixture.get_compiler_configs()
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")

        # Build and install the library project
        self.libraryProjectFixture.build_target("install", config=testprojectfixture.COMPILER_CONFIG)

        # Delete the library project to make sure unwanted references to
        # the original directory cause errors.
        self.fsa.rmtree(self.libraryProjectFixture.cpf_root_dir)


        # ------------------- Execute -----------------------

        # Build the consumer project.
        packageFileWE = self.get_package_file_we(myLibVersion, testprojectfixture.COMPILER_CONFIG)
        self.consumerProjectFixture.generate_project([
            "MYLIB_VERSION={0}".format(myLibVersion),
            "MYLIB_LOCATION={0}".format(installPrefix)
            ])
        self.consumerProjectFixture.build_target("MyLibConsumer")

        # ------------------- Verify -----------------------
        self.assert_consumer_project_builds_and_runs()


