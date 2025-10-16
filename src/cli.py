"""Command-line interface for the auto status report application."""

import click
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import sys

from .app import AutoStatusReportApp
from .config import settings


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Auto Status Report - Generate intelligent GitHub activity reports."""
    pass


@cli.command()
@click.option('--days', '-d', default=None, type=int, help='Number of days to look back (default: 7)')
@click.option('--repos', '-r', multiple=True, help='Specific repositories to include (can be used multiple times)')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'csv']), default='markdown', help='Output format')
@click.option('--no-ai', is_flag=True, help='Disable AI-generated summaries')
@click.option('--test', is_flag=True, help='Test connections before generating report')
def report(days, repos, output, format, no_ai, test):
    """Generate a comprehensive status report."""
    
    app = AutoStatusReportApp()
    
    # Test connections if requested
    if test:
        if not app.test_connections():
            click.echo("❌ Connection tests failed. Please check your configuration.", err=True)
            sys.exit(1)
        click.echo("✅ All connections successful!")
        return
    
    try:
        # Generate the report
        status_report = app.generate_status_report(
            days_back=days,
            repositories=list(repos) if repos else None,
            output_path=output,
            format=format,
            include_llm_summary=not no_ai
        )
        
        # Print summary to console
        app.print_summary(status_report)
        
        if not output:
            click.echo("\n💡 Use --output to save the full report to a file")
        
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']), help='Date to generate report for (YYYY-MM-DD)')
@click.option('--repos', '-r', multiple=True, help='Specific repositories to include')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']), default='markdown', help='Output format')
def daily(date, repos, output, format):
    """Generate a report for a specific day."""
    
    app = AutoStatusReportApp()
    
    try:
        app.generate_daily_report(
            date=date,
            repositories=list(repos) if repos else None,
            output_path=output,
            format=format
        )
    except Exception as e:
        click.echo(f"❌ Error generating daily report: {e}", err=True)
        sys.exit(1)


@cli.command()
def repos():
    """List all available repositories."""
    
    app = AutoStatusReportApp()
    
    try:
        click.echo("Fetching repositories...")
        repository_names = app.list_repositories()
        
        if not repository_names:
            click.echo("No repositories found.")
            return
        
        click.echo(f"\nFound {len(repository_names)} repositories:")
        click.echo("-" * 40)
        
        for i, repo in enumerate(repository_names, 1):
            click.echo(f"{i:2d}. {repo}")
        
        click.echo(f"\nUse --repos/-r with any of these names to filter reports.")
        
    except Exception as e:
        click.echo(f"❌ Error fetching repositories: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('repo_name')
@click.option('--days', '-d', default=30, type=int, help='Number of days to analyze (default: 30)')
def stats(repo_name, days):
    """Get detailed statistics for a specific repository."""
    
    app = AutoStatusReportApp()
    
    try:
        click.echo(f"Analyzing {repo_name} for the last {days} days...")
        stats = app.get_repository_stats(repo_name, days)
        
        click.echo(f"\n📊 Repository Statistics: {stats['repository']}")
        click.echo("=" * 50)
        click.echo(f"Period: {days} days")
        click.echo(f"Total Commits: {stats['total_commits']}")
        click.echo(f"Lines Added: {stats['total_additions']:,}")
        click.echo(f"Lines Deleted: {stats['total_deletions']:,}")
        click.echo(f"Files Changed: {stats['total_files_changed']}")
        click.echo(f"Average Commits/Day: {stats['average_commits_per_day']:.1f}")
        
        if stats['most_active_days']:
            click.echo(f"\n🔥 Most Active Days:")
            for date, count in stats['most_active_days']:
                click.echo(f"  {date}: {count} commits")
        
        if stats['commit_messages']:
            click.echo(f"\n📝 Recent Commit Messages:")
            for msg in stats['commit_messages']:
                click.echo(f"  • {msg}")
        
    except Exception as e:
        click.echo(f"❌ Error getting repository stats: {e}", err=True)
        sys.exit(1)


@cli.command()
def test():
    """Test all external connections."""
    
    app = AutoStatusReportApp()
    
    if app.test_connections():
        click.echo("✅ All connections successful!")
    else:
        click.echo("❌ Some connections failed. Please check your configuration.", err=True)
        sys.exit(1)


@cli.command()
def models():
    """List available Ollama models."""
    
    try:
        import requests
        from .config import settings
        
        click.echo("🤖 Available Ollama Models:")
        click.echo("-" * 30)
        
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('models', [])
        
        if not models:
            click.echo("No models found. Install a model with: ollama pull <model-name>")
            return
        
        for model in models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            modified = model.get('modified_at', 'Unknown')
            
            # Format size
            if size > 1024**3:
                size_str = f"{size / (1024**3):.1f} GB"
            elif size > 1024**2:
                size_str = f"{size / (1024**2):.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            
            click.echo(f"📦 {name}")
            click.echo(f"   Size: {size_str}")
            click.echo(f"   Modified: {modified}")
            click.echo()
        
        click.echo(f"Current model: {settings.ollama_model}")
        click.echo("\nTo change model, update OLLAMA_MODEL in your .env file")
        
    except Exception as e:
        click.echo(f"❌ Error fetching models: {e}", err=True)
        click.echo("Make sure Ollama is running: ollama serve")


@cli.command()
def config():
    """Show current configuration."""
    
    click.echo("🔧 Current Configuration:")
    click.echo("=" * 30)
    click.echo(f"GitHub Username: {settings.github_username}")
    click.echo(f"GitHub Token: {'*' * 20}...{settings.github_token[-4:] if settings.github_token else 'Not set'}")
    click.echo(f"Ollama Base URL: {settings.ollama_base_url}")
    click.echo(f"Ollama Model: {settings.ollama_model}")
    click.echo(f"Default Days Back: {settings.default_days_back}")
    click.echo(f"Report Format: {settings.report_format}")
    click.echo(f"GitHub API URL: {settings.github_api_base_url}")


@cli.command()
@click.option('--days', '-d', default=7, type=int, help='Number of days to look back')
@click.option('--repos', '-r', multiple=True, help='Specific repositories to include')
def quick(days, repos):
    """Generate a quick console-only report."""
    
    app = AutoStatusReportApp()
    
    try:
        status_report = app.generate_status_report(
            days_back=days,
            repositories=list(repos) if repos else None,
            include_llm_summary=True
        )
        
        app.print_summary(status_report)
        
    except Exception as e:
        click.echo(f"❌ Error generating quick report: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
