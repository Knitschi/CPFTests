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


    def test_consume_the_simple_test_project_library(self):
        """
        This test builds the distribution packages of the SimpleOneLibCPFTestProject
        and tests for one of them if the package can be used within the CPFPackageConsumerTestProject.
        """

        # ------------------- Setup -----------------------

        compilerConfigSmallCase = testprojectfixture.COMPILER_CONFIG.lower()

        # build the library project
        self.libraryProjectFixture.generate_project()
        self.libraryProjectFixture.build_target("distributionPackages")

        # Copy binary package to the consumer package
        myLibVersion = self.libraryProjectFixture.get_package_version("MyLib")
        packageFileWE = "MyLib.{0}.{1}.dev-bin.{2}".format(myLibVersion, self.osa.system(), compilerConfigSmallCase)
        packageFileShort = packageFileWE + ".7z"
        packageFile = self.libraryProjectFixture.locations.get_full_path_config_makefile_folder(testprojectfixture.PARENT_CONFIG).joinpath("html/Downloads/MyLib/LastBuild").joinpath(packageFileShort)
        self.fsa.copyfile(packageFile, self.consumerProjectFixture.cpf_root_dir / packageFileShort)

        # Unzip the binary package
        self.osa.execute_command("cmake -E tar xzf " + packageFileShort, self.consumerProjectFixture.cpf_root_dir)

        # Delete the library project to make sure possible references to
        # the original directory cause errors.
        self.fsa.rmtree(self.libraryProjectFixture.cpf_root_dir)


        # ------------------- Execute -----------------------

        # Build the consumer project.
        self.consumerProjectFixture.generate_project([
            "MYLIB_VERSION={0}".format(myLibVersion),
            "MYLIB_LOCATION={0}".format(self.consumerProjectFixture.cpf_root_dir / packageFileWE / "MyLib")
            ])
        self.consumerProjectFixture.build_target("ALL_BUILD")


        # ------------------- Verify -----------------------

        # Check that the deployment of the external dll works by running the executable
        binaryOutputDirCurrentConfig = self.consumerProjectFixture.locations.get_full_path_binary_output_folder(
            testprojectfixture.PARENT_CONFIG,
            testprojectfixture.COMPILER_CONFIG,
            "MyLibConsumer" 
        )
        consumerExe = binaryOutputDirCurrentConfig / "MyLibConsumer-{0}.exe".format(compilerConfigSmallCase)
        self.assertTrue(self.osa.execute_command(str(consumerExe) , self.consumerProjectFixture.cpf_root_dir))
        
        # Assert that the buildstage directories of the not-current
        # configuration do not contain the MyLib-<config>.dll (this this was a bug)
        compilerConfigs = self.consumerProjectFixture.get_compiler_configs()
        if len(compilerConfigs) > 1:
            notCurrentCompilerConfig = list(set(compilerConfigs) - set([testprojectfixture.PARENT_CONFIG]))[0]
            binaryOutputDirOtherConfig = self.consumerProjectFixture.locations.get_full_path_binary_output_folder(
                testprojectfixture.PARENT_CONFIG,
                notCurrentCompilerConfig,
                "MyLibConsumer" 
            )
            dllFile = binaryOutputDirOtherConfig / "MyLib-{0}.dll".format(testprojectfixture.COMPILER_CONFIG.lower())
            print("-----------" + str(dllFile))

            self.consumerProjectFixture.assert_target_does_not_create_files("MyLibConsumer", [dllFile])

        # Assert .pdb file is deployed

        # Assert source files are deployed


 
        


