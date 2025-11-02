# Auto Status Report

An intelligent GitHub activity tracker that generates comprehensive status reports of your development work. This tool analyzes your commits across repositories and creates detailed summaries with AI-powered insights.

## Features

- 🔍 **Comprehensive Analysis**: Track commits, additions, deletions, and file changes across all your repositories
- 🤖 **AI-Powered Summaries**: Generate intelligent journal-style summaries of your daily development work using Ollama (local or cloud)
- 📊 **Multiple Formats**: Export reports in Markdown, JSON, or CSV formats
- 📅 **Flexible Time Ranges**: Generate reports for any date range or specific days
- 🎯 **Repository Filtering**: Focus on specific repositories or analyze all your work (owned and collaborator repos)
- ⏰ **Timezone Support**: All timestamps displayed in US/Eastern timezone for consistency
- 🖥️ **CLI Interface**: Easy-to-use command-line interface for automation
- 🏗️ **Jenkins Ready**: Designed to run on your Jenkins server for automated reporting

## Installation

1. **Clone or download this repository**:
   ```bash
   git clone <your-repo-url>
   cd auto-status-report
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp config.env.example .env
   ```

4. **Configure your credentials** in the `.env` file:
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

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:user` (Read user profile data)
4. Copy the token and add it to your `.env` file

## Ollama Setup

You can use Ollama either locally or via Ollama Cloud.

### Option 1: Local Ollama (Free)

1. **Install Ollama** (if not already installed):
   ```bash
   # On macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Or download from https://ollama.ai/download
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Install a model** (choose one):
   ```bash
   # Llama 3 (recommended, ~4.7GB)
   ollama pull llama3:latest

   # Or Granite 3.3 (IBM's model, ~4.9GB)
   ollama pull granite3.3:latest

   # Or Gemma 3 4B (smaller, ~3.3GB)
   ollama pull gemma3:4b
   ```

4. **Verify installation**:
   ```bash
   ollama list
   ```

### Option 2: Ollama Cloud

1. Sign up for Ollama Cloud at https://ollama.com
2. Get your API key from your account settings
3. Add to your `.env` file:
   ```env
   OLLAMA_BASE_URL=https://api.ollama.com  # Or your cloud endpoint
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

# List all repositories (including where you're a collaborator)
python main.py repos --include-collaborator

# Get detailed stats for a specific repository
python main.py stats my-repository --days 30

# List available Ollama models
python main.py models

# Test all connections
python main.py test

# Show current configuration
python main.py config

# Quick console-only report
python main.py quick
```

### Advanced Usage

```bash
# Generate report without AI summary
python main.py report --no-ai

# Generate CSV report for data analysis
python main.py report --format csv --output activity.csv

# Generate daily report for multiple repositories
python main.py daily --repos project1 --repos project2 --date 2024-01-15

# Test connections before generating report
python main.py report --test
```

## Jenkins Integration

To run this tool from your Jenkins server:

1. **Set up environment variables** in Jenkins:
   - `GITHUB_TOKEN`: Your GitHub personal access token
   - `GITHUB_USERNAME`: Your GitHub username
   - `OLLAMA_BASE_URL`: Your Ollama server URL (local or cloud)
   - `OLLAMA_MODEL`: The model to use
   - `OLLAMA_API_KEY`: Your Ollama Cloud API key (if using cloud)

2. **Create a Jenkins job** with a shell script:
   ```bash
   #!/bin/bash
   cd /path/to/auto-status-report
   python main.py report --days 7 --output reports/weekly-report-$(date +%Y-%m-%d).md
   ```

3. **Schedule the job** to run daily or weekly as needed

## Report Formats

### Markdown (Default)
- Human-readable journal-style format with narrative daily summaries
- Commits organized by day with timestamps in US/Eastern timezone
- AI-generated summaries that read like a development diary
- Perfect for sharing with team members or keeping a development log

### JSON
- Machine-readable format for further processing
- Contains all raw data and statistics
- Useful for integration with other tools

### CSV
- Tabular format for spreadsheet analysis
- Daily activity breakdown by repository
- Easy to import into Excel or Google Sheets

## Sample Output

### Console Summary
```
============================================================
STATUS REPORT SUMMARY
============================================================
Period: 2024-01-08 to 2024-01-15
Repositories: 3
Total Commits: 24
Lines Added: 1,247
Lines Deleted: 89
Net Changes: 1,158
Most Active Repos: my-project, api-service, frontend-app
Active Days: 5/7
============================================================
```

### Markdown Report Structure
The generated reports now use a **journal-style format**:

- **Overview**: Summary statistics for the entire period
- **Most Active Repositories**: Quick reference of where you spent most time
- **Daily Activity**: For each active day:
  - Day and date header (e.g., "Monday, January 15, 2024")
  - Table of all commits with:
    - Commit ID
    - Timestamp (US/Eastern timezone)
    - Repository name
    - Lines changed (+/-)
  - **AI-generated narrative summary** describing what was accomplished that day in prose format

This format makes it easy to track your development progress like a daily journal, with AI helping to create readable summaries of technical work.

## Configuration Options

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

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limiting**
   - The tool includes built-in rate limiting
   - If you hit limits, wait a few minutes and try again

2. **Ollama Connection Issues**
   - Make sure Ollama is running: `ollama serve` (for local setup)
   - Check that the model is installed: `ollama list` (for local setup)
   - Verify the OLLAMA_BASE_URL in your .env file
   - For Ollama Cloud, verify your OLLAMA_API_KEY is correct
   - The tool will work without AI summaries if Ollama is unavailable
   - Note: AI summary generation can take several minutes on CPU-only systems

3. **Repository Not Found**
   - Ensure the repository name is correct
   - Check that your GitHub token has access to the repository

4. **No Commits Found**
   - Verify the date range includes your activity
   - Check that commits are authored by your GitHub username

### Testing Your Setup

```bash
# Test all connections
python main.py test

# List your repositories
python main.py repos

# Generate a quick report
python main.py quick --days 1
```

## Development

### Project Structure
```
auto-status-report/
├── src/
│   ├── __init__.py
│   ├── app.py              # Main application class
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── data_processor.py   # Data analysis logic
│   ├── github_client.py    # GitHub API client
│   ├── llm_client.py       # Ollama LLM client for AI summaries
│   ├── models.py           # Data models
│   └── report_generator.py # Journal-style report generation
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── config.env.example     # Environment template
└── README.md              # This file
```

### Adding New Features

1. **New Report Formats**: Extend `ReportGenerator` class
2. **Additional Metrics**: Modify `DataProcessor` class
3. **New CLI Commands**: Add commands to `cli.py`
4. **Different LLM Providers**: Extend `LLMClient` class

## License

This project is open source. Feel free to modify and distribute as needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the GitHub issues
3. Create a new issue with detailed information

---

**Happy coding!** 🚀
