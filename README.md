# Auto Status Report

An intelligent GitHub activity tracker that generates comprehensive status reports of your development work. This tool analyzes your commits across repositories and creates detailed summaries with AI-powered insights.

## Features

- 🔍 **Comprehensive Analysis**: Track commits, additions, deletions, and file changes across all your repositories
- 🤖 **AI-Powered Summaries**: Generate intelligent insights about your development patterns using local Ollama models
- 📊 **Multiple Formats**: Export reports in Markdown, JSON, or CSV formats
- 📅 **Flexible Time Ranges**: Generate reports for any date range or specific days
- 🎯 **Repository Filtering**: Focus on specific repositories or analyze all your work
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
   DEFAULT_DAYS_BACK=7
   REPORT_FORMAT=markdown
   ```

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:user` (Read user profile data)
4. Copy the token and add it to your `.env` file

## Ollama Setup

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

# List all your repositories
python main.py repos

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
   - `OPENAI_API_KEY`: Your OpenAI API key

2. **Create a Jenkins job** with a shell script:
   ```bash
   #!/bin/bash
   cd /path/to/auto-status-report
   python main.py report --days 7 --output reports/weekly-report-$(date +%Y-%m-%d).md
   ```

3. **Schedule the job** to run daily or weekly as needed

## Report Formats

### Markdown (Default)
- Human-readable format with sections and formatting
- Perfect for sharing with team members or managers
- Includes AI-generated insights and summaries

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

AI Summary:
----------------------------------------
This week shows strong development activity across three main projects. 
The focus appears to be on feature development with significant code 
additions in the my-project repository. The consistent daily commits 
indicate active development with good momentum.
============================================================
```

### Markdown Report Structure
- Executive Summary with key metrics
- Most Active Repositories
- AI-Generated Summary
- Daily Activity Breakdown
- Repository-specific details
- Recent commit messages

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | Required |
| `GITHUB_USERNAME` | Your GitHub username | Required |
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | Ollama model to use | llama3:latest |
| `DEFAULT_DAYS_BACK` | Default number of days to analyze | 7 |
| `REPORT_FORMAT` | Default report format | markdown |

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limiting**
   - The tool includes built-in rate limiting
   - If you hit limits, wait a few minutes and try again

2. **Ollama Connection Issues**
   - Make sure Ollama is running: `ollama serve`
   - Check that the model is installed: `ollama list`
   - Verify the OLLAMA_BASE_URL in your .env file
   - The tool will work without AI summaries if Ollama is unavailable

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
│   ├── llm_client.py       # OpenAI API client
│   ├── models.py           # Data models
│   └── report_generator.py # Report generation
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
