pipeline {
    agent any
    
    environment {
        // These should be configured in Jenkins credentials
        GITHUB_TOKEN = credentials('github-token')
        GITHUB_USERNAME = credentials('github-username')
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    triggers {
        // Run daily at 9 AM
        cron('0 9 * * *')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                script {
                    // Create .env file from Jenkins environment variables
                    writeFile file: '.env', text: """
GITHUB_TOKEN=${env.GITHUB_TOKEN}
GITHUB_USERNAME=${env.GITHUB_USERNAME}
OPENAI_API_KEY=${env.OPENAI_API_KEY}
DEFAULT_DAYS_BACK=7
REPORT_FORMAT=markdown
"""
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'pip3 install -r requirements.txt'
            }
        }
        
        stage('Test Connections') {
            steps {
                sh 'python3 main.py test'
            }
        }
        
        stage('Generate Weekly Report') {
            steps {
                script {
                    def date = new Date().format('yyyy-MM-dd')
                    sh "python3 main.py report --days 7 --output reports/weekly-report-${date}.md"
                }
            }
        }
        
        stage('Generate Daily Report') {
            steps {
                script {
                    def date = new Date().format('yyyy-MM-dd')
                    sh "python3 main.py daily --output reports/daily-report-${date}.md"
                }
            }
        }
        
        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'reports/*.md', fingerprint: true
            }
        }
        
        stage('Send Notification') {
            steps {
                script {
                    // Example: Send email notification with report
                    def date = new Date().format('yyyy-MM-dd')
                    emailext (
                        subject: "Daily Development Report - ${date}",
                        body: "Your daily development report has been generated. Check the attached files.",
                        attachmentsPattern: "reports/daily-report-${date}.md",
                        to: "${env.CHANGE_AUTHOR_EMAIL ?: 'your-email@example.com'}"
                    )
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            cleanWs()
        }
        
        success {
            echo '✅ Status report generation completed successfully!'
        }
        
        failure {
            echo '❌ Status report generation failed!'
            // Send failure notification
            emailext (
                subject: "Status Report Generation Failed - ${new Date().format('yyyy-MM-dd')}",
                body: "The automated status report generation failed. Please check the Jenkins logs.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'your-email@example.com'}"
            )
        }
    }
}
