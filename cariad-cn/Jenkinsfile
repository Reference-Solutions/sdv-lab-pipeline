@Library('RefSolutions-Pipeliner@feature/18648-Nexus') _ // Load the my-nested-library as a shared library



// Define environment variables
env.CHECKOUT_URL_1 = "https://github.com/Reference-Solutions/VIP_XSPACE_E2E.git"
env.CHECKOUT_BRANCH_1 = "feature/Cop"
env.CHECKOUT_CREDENTIALS_ID_1 = "Github_RefSolution"
env.CHECKOUT_COUNT = 1

//Define pip variables

env.pip_asw_build_dir_path = "VIP_XSPACE_E2E/M7/vip-project-uC-AR45"
env.pip_bsw_build_dir_path = "VIP_XSPACE_E2E/M7/cubas-nxp-s32g-AR45"
env.pip_integeration_dir_path = "VIP_XSPACE_E2E/M7/CoP"
env.pip_bsw_pre_build_file_name = "PreBuild.bat"
env.pip_asw_build_file_name = "ConanBuild.bat"
env.pip_bsw_build_file_name = "Build.bat"
env.pip_integeration_file_name = "Build.bat"
env.pip_bsw_build = true
env.pip_asw_build = true
env.pip_autosar_tool = "aeee_pro"
env.pip_autosar_tool_version = "2022.2.2"
env.pip_autosar_tool_env = "cdg.de"
env.pip_project_variant = "VIP_MAIN_BOARD"
env.pip_artifactory_upload_type = "conan"
env.pip_conan_remote_name_to_upload = "conan-releases-local-nexus"
env.pip_conan_package_ref_to_upload = "vip-project-uC-AR45_swint/1.0.0@etas/stable"


//Define stages
env.pip_sonar_stage = "false"
env.pip_archive_stage = "false"
env.pip_dac_stage = "false"

execArcBswPipeline()