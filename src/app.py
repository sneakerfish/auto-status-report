"""Main application class for the auto status report system."""

from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import sys

from .config import settings
from .github_client import GitHubClient
from .data_processor import DataProcessor
from .llm_client import LLMClient
from .report_generator import ReportGenerator
from .models import StatusReport


class AutoStatusReportApp:
    """Main application class for generating GitHub status reports."""
    
    def __init__(self):
        """Initialize the application with all required components."""
        self.github_client = GitHubClient()
        self.data_processor = DataProcessor(self.github_client)
        self.llm_client = LLMClient()
        self.report_generator = ReportGenerator(self.llm_client)
    
    def test_connections(self) -> bool:
        """Test all external connections."""
        print("Testing connections...")
        
        # Test GitHub connection
        if not self.github_client.test_connection():
            print("❌ GitHub API connection failed")
            return False
        print("✅ GitHub API connection successful")
        
        # Test Ollama connection (optional)
        if self.llm_client.test_connection():
            print("✅ Ollama connection successful")
        else:
            print("⚠️  Ollama connection failed")
            print("   Reports will be generated without AI summaries")
        
        return True
    
    def generate_status_report(
        self,
        days_back: int = None,
        repositories: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        format: str = "markdown",
        include_llm_summary: bool = True
    ) -> StatusReport:
        """Generate a comprehensive status report."""
        
        if days_back is None:
            days_back = settings.default_days_back
        
        print(f"Generating status report for the last {days_back} days...")
        
        # Generate the status report
        status_report = self.data_processor.generate_status_report(
            days_back=days_back,
            repositories=repositories
        )
        
        # Add LLM summary if requested
        if include_llm_summary and status_report.total_commits > 0:
            print("Generating AI summary...")
            try:
                status_report.llm_summary = self.llm_client.generate_status_summary(status_report)
            except Exception as e:
                print(f"Warning: Could not generate AI summary: {e}")
        
        # Save to file if output path is specified
        if output_path:
            self.report_generator.save_report(
                status_report,
                output_path,
                format=format,
                include_llm_summary=include_llm_summary
            )
        
        return status_report
    
    def generate_daily_report(
        self,
        date: Optional[datetime] = None,
        repositories: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        format: str = "markdown"
    ) -> None:
        """Generate a report for a specific day."""
        
        if date is None:
            date = datetime.now() - timedelta(days=1)  # Yesterday
        
        print(f"Generating daily report for {date.strftime('%Y-%m-%d')}...")
        
        # Get activity for the specific day
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        if repositories:
            activity = {}
            for repo_name in repositories:
                commits = self.github_client.get_commits_for_repository(
                    repo_name, start_date, end_date
                )
                if commits:
                    activity[repo_name] = commits
        else:
            # Get all repositories
            all_repos = self.github_client.get_user_repositories()
            activity = {}
            for repo in all_repos:
                commits = self.github_client.get_commits_for_repository(
                    repo.name, start_date, end_date
                )
                if commits:
                    activity[repo.name] = commits
        
        # Process the daily activity
        daily_summaries = self.data_processor._process_daily_activities(
            activity, start_date, end_date
        )
        
        if not daily_summaries or daily_summaries[0].total_commits == 0:
            print(f"No activity found for {date.strftime('%Y-%m-%d')}")
            return
        
        daily_summary = daily_summaries[0]
        
        # Generate and save report
        if output_path:
            content = self.report_generator.generate_daily_summary_report(
                daily_summary, format=format
            )
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "markdown" and not output_path.suffix:
                output_path = output_path.with_suffix('.md')
            elif format.lower() == "json" and not output_path.suffix:
                output_path = output_path.with_suffix('.json')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Daily report saved to: {output_path}")
        else:
            # Print to console
            content = self.report_generator.generate_daily_summary_report(
                daily_summary, format=format
            )
            print(content)
    
    def list_repositories(self, include_collaborator: bool = None) -> List[str]:
        """List all available repositories."""
        if include_collaborator is None:
            include_collaborator = settings.include_collaborator_repos
            
        if include_collaborator:
            # Get both owned and collaborator repositories
            owned_repos = self.github_client.get_user_repositories()
            collaborator_repos = self.github_client.get_collaborator_repositories()
            all_repos = owned_repos + collaborator_repos
        else:
            # Only owned repositories (default)
            all_repos = self.github_client.get_user_repositories()
        
        return [repo.name for repo in all_repos]
    
    def get_repository_stats(self, repo_name: str, days_back: int = 30) -> dict:
        """Get detailed statistics for a specific repository."""
        return self.data_processor.get_repository_statistics(repo_name, days_back)
    
    def print_summary(self, status_report: StatusReport) -> None:
        """Print a summary of the status report to console."""
        print("\n" + "="*60)
        print("STATUS REPORT SUMMARY")
        print("="*60)
        print(f"Period: {status_report.start_date.strftime('%Y-%m-%d')} to {status_report.end_date.strftime('%Y-%m-%d')}")
        print(f"Repositories: {status_report.total_repositories}")
        print(f"Total Commits: {status_report.total_commits}")
        print(f"Lines Added: {status_report.total_additions:,}")
        print(f"Lines Deleted: {status_report.total_deletions:,}")
        print(f"Net Changes: {status_report.total_additions - status_report.total_deletions:,}")
        
        if status_report.most_active_repos:
            print(f"Most Active Repos: {', '.join(status_report.most_active_repos[:3])}")
        
        active_days = len([s for s in status_report.daily_summaries if s.total_commits > 0])
        print(f"Active Days: {active_days}/{len(status_report.daily_summaries)}")
        
        if status_report.llm_summary:
            print("\nAI Summary:")
            print("-" * 40)
            print(status_report.llm_summary)
        
        print("="*60)
