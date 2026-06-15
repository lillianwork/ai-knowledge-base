pipeline {
    agent any

    environment {
        WORKSPACE_DIR = "${WORKSPACE}"
        SCRIPTS_DIR = "${WORKSPACE}/scripts"
        CONFIG_DIR = "${WORKSPACE}/config"
        BUILD_DIR = "${WORKSPACE}/build"
        RESULTS_DIR = "${WORKSPACE}/scan-reports"

        SONAR_HOST_URL = credentials('sonar-host-url')
        SONAR_TOKEN = credentials('sonar-token')
        GITLAB_API_TOKEN = credentials('gitlab-api-token')
        POLYSPACE_LICENSE = credentials('polyspace-license-file')
        NEXUS_PASSWORD = credentials('nexus-password')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds(abortPrevious: true)
        timeout(time: 2, unit: 'HOURS')
        gitLabConnection('gitlab-connection')
        ansiColor('xterm')
        timestamps()
    }

    triggers {
        gitlab(
            triggerOnPush: true,
            triggerOnMergeRequest: true,
            triggerOpenMergeRequestOnPush: "source",
            triggerOnNoteRequest: true,
            noteRegex: ".*recheck.*|.*retest.*",
            branchFilterType: "All"
        )
    }

    parameters {
        string(name: 'IDE_TOOLCHAIN', defaultValue: 'gcc',
               description: 'IDE toolchain: gcc, iar, keil, armcc')
        choice(name: 'BUILD_TYPE', choices: ['Debug', 'Release', 'MinSizeRel'],
               description: 'Build configuration')
        booleanParam(name: 'SKIP_POLYSPACE', defaultValue: false,
                     description: 'Skip Polyspace scan (requires license)')
        booleanParam(name: 'SKIP_ARCHIVE', defaultValue: false,
                     description: 'Skip artifact archiving')
        string(name: 'TEST_HW_TARGET', defaultValue: '',
               description: 'Hardware target for integration tests')
        string(name: 'TEST_LEAD', defaultValue: 'test-lead',
               description: 'Test lead username for notifications')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
                    env.GIT_COMMITTER = sh(script: 'git log -1 --format="%ae"', returnStdout: true).trim()
                    env.GIT_COMMIT_MSG = sh(script: 'git log -1 --format="%s"', returnStdout: true).trim()
                }
                updateGitlabCommitStatus name: 'pipeline', state: 'running'
                echo "Building commit ${GIT_COMMIT_SHORT} by ${GIT_COMMITTER} on ${GIT_BRANCH}"
            }
        }

        stage('Build') {
            steps {
                updateGitlabCommitStatus name: 'build', state: 'running'
                sh '''
                    chmod +x scripts/*.sh
                    export IDE_TOOLCHAIN="${IDE_TOOLCHAIN:-gcc}"
                    export BUILD_TYPE="${BUILD_TYPE:-Debug}"
                    scripts/build-ide.sh
                '''
            }
            post {
                success {
                    updateGitlabCommitStatus name: 'build', state: 'success'
                    archiveArtifacts artifacts: 'build/output/*.bin,build/output/*.hex,build/output/*.elf,build/output/build-info.json', fingerprint: true
                }
                failure {
                    updateGitlabCommitStatus name: 'build', state: 'failed'
                }
            }
        }

        stage('SonarQube Analysis') {
            parallel {
                stage('SonarQube Scan') {
                    steps {
                        updateGitlabCommitStatus name: 'sonarqube', state: 'running'
                        sh '''
                            export SONAR_HOST_URL="${SONAR_HOST_URL}"
                            export SONAR_TOKEN="${SONAR_TOKEN}"
                            scripts/sonar-scanner.sh
                        '''
                    }
                    post {
                        success {
                            updateGitlabCommitStatus name: 'sonarqube', state: 'success'
                        }
                        failure {
                            updateGitlabCommitStatus name: 'sonarqube', state: 'failed'
                        }
                    }
                }
                stage('Polyspace Scan') {
                    when { expression { !params.SKIP_POLYSPACE } }
                    steps {
                        updateGitlabCommitStatus name: 'polyspace', state: 'running'
                        sh '''
                            export POLYSPACE_HOME="${POLYSPACE_HOME:-/opt/polyspace}"
                            export MLM_LICENSE_FILE="${POLYSPACE_LICENSE}"
                            scripts/polyspace-scanner.sh
                        '''
                    }
                    post {
                        success {
                            updateGitlabCommitStatus name: 'polyspace', state: 'success'
                        }
                        failure {
                            updateGitlabCommitStatus name: 'polyspace', state: 'failed'
                        }
                    }
                }
            }
        }

        stage('Issue Assignment') {
            when {
                expression {
                    def sqIssues = sh(script: 'test -f scan-reports/sonar-env.txt && source scan-reports/sonar-env.txt && echo $SONAR_ISSUE_COUNT', returnStdout: true).trim()
                    def psIssues = sh(script: 'test -f scan-reports/polyspace/polyspace-env.txt && source scan-reports/polyspace/polyspace-env.txt && echo $POLYSPACE_TOTAL_ISSUES || echo 0', returnStdout: true).trim()
                    return sqIssues.toInteger() > 0 || psIssues.toInteger() > 0
                }
            }
            steps {
                script {
                    def scanIssues = sh(script: '''
                        source scan-reports/sonar-env.txt 2>/dev/null || true
                        source scan-reports/polyspace/polyspace-env.txt 2>/dev/null || true
                        echo "SonarQube: ${SONAR_ISSUE_COUNT:-0}, Polyspace: ${POLYSPACE_TOTAL_ISSUES:-0}"
                    ''', returnStdout: true).trim()
                    echo "Auto-assigning scan issues to committers: ${scanIssues}"
                }
                sh '''
                    export GITLAB_API_TOKEN="${GITLAB_API_TOKEN}"
                    export GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://gitlab:80}"
                    scripts/assign-issues.sh
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'scan-issues/tracking-report.json', fingerprint: true, allowEmptyArchive: true
                }
            }
        }

        stage('Quality Gate') {
            steps {
                sh 'scripts/quality-gate.sh'
            }
            post {
                success {
                    echo 'All quality gates passed'
                }
                failure {
                    updateGitlabCommitStatus name: 'quality-gate', state: 'failed'
                    error 'Quality gate failed — merge blocked'
                }
            }
        }

        stage('Automated Testing') {
            steps {
                updateGitlabCommitStatus name: 'tests', state: 'running'
                sh '''
                    export TEST_HW_TARGET="${TEST_HW_TARGET}"
                    export TEST_LEAD="${TEST_LEAD:-test-lead}"
                    export GITLAB_API_TOKEN="${GITLAB_API_TOKEN}"
                    scripts/trigger-tests.sh
                '''
            }
            post {
                success {
                    updateGitlabCommitStatus name: 'tests', state: 'success'
                    junit 'build/test/**/*_results.xml'
                }
                failure {
                    updateGitlabCommitStatus name: 'tests', state: 'failed'
                    junit 'build/test/**/*_results.xml'
                }
            }
        }

        stage('Defect Tracking') {
            when {
                expression {
                    return sh(script: 'test -f build/test/test-summary.json && jq -r ".fail // 0" build/test/test-summary.json', returnStdout: true).trim().toInteger() > 0
                }
            }
            steps {
                sh '''
                    export GITLAB_API_TOKEN="${GITLAB_API_TOKEN}"
                    scripts/defect-tracker.sh
                '''
            }
        }

        stage('Archive Artifacts') {
            when { expression { !params.SKIP_ARCHIVE } }
            steps {
                sh '''
                    export NEXUS_PASSWORD="${NEXUS_PASSWORD}"
                    scripts/archive-artifacts.sh
                '''
            }
            post {
                success {
                    script {
                        env.ARCHIVE_VERSION = sh(script: 'tail -2 build/logs/archive.log 2>/dev/null | grep ARCHIVE_VERSION | cut -d= -f2 || echo "unknown"', returnStdout: true).trim()
                    }
                    echo "Artifacts archived — version: ${ARCHIVE_VERSION}"
                }
            }
        }
    }

    post {
        success {
            updateGitlabCommitStatus name: 'pipeline', state: 'success'
            emailext(
                subject: "[CI/CD] ✅ ${env.JOB_NAME} - Build #${env.BUILD_NUMBER} 成功",
                body: """
                    <h3>CI/CD 流水线执行成功</h3>
                    <p><b>项目:</b> ${env.JOB_NAME}</p>
                    <p><b>构建号:</b> #${env.BUILD_NUMBER}</p>
                    <p><b>分支:</b> ${env.GIT_BRANCH}</p>
                    <p><b>提交者:</b> ${env.GIT_COMMITTER}</p>
                    <p><b>归档版本:</b> ${env.ARCHIVE_VERSION}</p>
                    <p><a href="${env.BUILD_URL}">查看详情</a></p>
                """,
                to: "${env.GIT_COMMITTER}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        failure {
            updateGitlabCommitStatus name: 'pipeline', state: 'failed'
            emailext(
                subject: "[CI/CD] ❌ ${env.JOB_NAME} - Build #${env.BUILD_NUMBER} 失败",
                body: """
                    <h3>CI/CD 流水线执行失败</h3>
                    <p><b>项目:</b> ${env.JOB_NAME}</p>
                    <p><b>构建号:</b> #${env.BUILD_NUMBER}</p>
                    <p><b>分支:</b> ${env.GIT_BRANCH}</p>
                    <p><a href="${env.BUILD_URL}">查看详情</a></p>
                """,
                to: "${env.GIT_COMMITTER}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        always {
            cleanWs(
                cleanWhenNotBuilt: false,
                deleteDirs: true,
                patterns: [[pattern: '.sonar/cache', type: 'EXCLUDE']]
            )
        }
    }
}
