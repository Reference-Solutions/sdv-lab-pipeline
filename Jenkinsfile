// Jenkinsfile demo
@Library('RefSolutions-Pipeliner@feature/18081-Versioning') _ // Load the my-nested-library as a shared library


// Define environment variables
env.CHECKOUT_URL_1 = "https://github.boschdevcloud.com/exmachina/qnx-hv-nxp-s32g.git"
env.CHECKOUT_BRANCH_1 = "feature/qnx-bsp710-s32g-vip"
env.CHECKOUT_CREDENTIALS_ID_1 = "hari-user-github"
env.pip_sonar_stage = "false"
env.pip_artifact_version = "v1.0.0"
env.pip_archive_patterns = "qnx-hv-nxp-s32g/images/*.ui"


execQnxPipeline()
