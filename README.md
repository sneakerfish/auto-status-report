# Auto Status Report

An intelligent GitHub activity tracker that generates comprehensive status reports of your development work. This tool analyzes your commits across repositories and creates detailed summaries with AI-powered insights.

## Features

-   **Comprehensive Analysis**: Track commits, additions, deletions, and file changes across all your repositories.
-   **AI-Powered Summaries**: Generate intelligent journal-style summaries of your daily development work using Ollama (local or cloud).
-   **Multiple Formats**: Export reports in Markdown, JSON, or CSV formats.
-   **Flexible Time Ranges**: Generate reports for any date range or specific days.
-   **Repository Filtering**: Focus on specific repositories or analyze all your work (owned and collaborator repos).
-   **Timezone Support**: All timestamps displayed in US/Eastern timezone for consistency.
-   **CLI Interface**: Easy-to-use command-line interface for automation.
-   **Jenkins Ready**: Designed to run on your Jenkins server for automated reporting.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd auto-status-report
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create your environment file**:
    ```bash
    cp config.env.example .env
    ```

4.  **Configure your `.env` file** with your credentials and preferences:

    ```env
    GITHUB_TOKEN=your_github_personal_access_token_here
    GITHUB_USERNAME=your_github_username
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=llama3:latest
    OLLAMA_API_KEY=  # Optional: For Ollama Cloud
    DEFAULT_DAYS_BACK=7
    REPORT_FORMAT=markdown
    INCLUDE_COLLABORATOR_REPOS=false
    ```

    | Variable | Description | Default |
    |----------|-------------|---------|
    | `GITHUB_TOKEN` | GitHub personal access token | Required |
    | `GITHUB_USERNAME` | Your GitHub username | Required |
    | `OLLAMA_BASE_URL` | Ollama server URL (local or cloud) | http://localhost:11434 |
    | `OLLAMA_MODEL` | Ollama model to use | llama3:latest |
    | `OLLAMA_API_KEY` | Ollama Cloud API key (optional) | (empty) |
    | `DEFAULT_DAYS_BACK` | Default number of days to analyze | 7 |
    | `REPORT_FORMAT` | Default report format | markdown |
    | `INCLUDE_COLLABORATOR_REPOS` | Include repos where you're a collaborator | false |

## GitHub Token Setup

1.  Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2.  Click "Generate new token (classic)"
3.  Select the following scopes:
    -   `repo` (Full control of private repositories)
    -   `read:user` (Read user profile data)
4.  Copy the token and add it to your `.env` file.

## Ollama Setup

You can use Ollama either locally or via Ollama Cloud.

### Option 1: Local Ollama (Free)

1.  **Install Ollama**:
    ```bash
    # On macOS/Linux
    curl -fsSL [https://ollama.ai/install.sh](https://ollama.ai/install.sh) | sh

    # Or download from [https://ollama.ai/download](https://ollama.ai/download)
    ```

2.  **Start Ollama service**:
    ```bash
    ollama serve
    ```

3.  **Install a model** (e.g., `llama3`):
    ```bash
    ollama pull llama3:latest
    ```

4.  **Verify installation**:
    ```bash
    ollama list
    ```

### Option 2: Ollama Cloud

1.  Sign up for Ollama Cloud at https://ollama.com
2.  Get your API key from your account settings.
3.  Add the following to your `.env` file:
    ```env
    OLLAMA_BASE_URL=[https://api.ollama.com](https://api.ollama.com)  # Or your cloud endpoint
    OLLAMA_API_KEY=your_api_key_here
    OLLAMA_MODEL=llama3:latest
    ```

## Usage

### Basic Commands

```bash
# Generate a 7-day status report
python main.py report

# Generate a report for the last 30 days
python main.py report --days 30

# Generate a report for specific repositories
python main.py report --repos my-project --repos another-project

# Save report to a file
python main.py report --output my-report.md

# Generate JSON report
python main.py report --format json --output report.json

# Generate daily report for yesterday
python main.py daily

# Generate daily report for a specific date
python main.py daily --date 2024-01-15

# List all your owned repositories
python main.py repos

# List available Ollama models
python main.py models

# Test all connections
python main.py test

# Show current configuration
python main.py config

# Quick console-only report
python main.py quick
```
