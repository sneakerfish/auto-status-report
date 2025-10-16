"""Report generation system for creating formatted status reports."""

from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

from .models import StatusReport, WorkSummary
from .llm_client import LLMClient


class ReportGenerator:
    """Generates formatted status reports in various formats."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate_markdown_report(
        self, 
        status_report: StatusReport, 
        include_llm_summary: bool = True
    ) -> str:
        """Generate a markdown formatted status report."""
        
        report_lines = []
        
        # Header
        report_lines.append("# GitHub Activity Status Report")
        report_lines.append("")
        report_lines.append(f"**Period**: {status_report.start_date.strftime('%Y-%m-%d')} to {status_report.end_date.strftime('%Y-%m-%d')}")
        report_lines.append(f"**Generated**: {status_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Repositories**: {status_report.total_repositories}")
        report_lines.append(f"- **Total Commits**: {status_report.total_commits}")
        report_lines.append(f"- **Lines Added**: {status_report.total_additions:,}")
        report_lines.append(f"- **Lines Deleted**: {status_report.total_deletions:,}")
        report_lines.append(f"- **Net Changes**: {status_report.total_additions - status_report.total_deletions:,}")
        report_lines.append("")
        
        # Most Active Repositories
        if status_report.most_active_repos:
            report_lines.append("## Most Active Repositories")
            report_lines.append("")
            for i, repo in enumerate(status_report.most_active_repos, 1):
                report_lines.append(f"{i}. {repo}")
            report_lines.append("")
        
        # LLM Summary
        if include_llm_summary and status_report.total_commits > 0:
            report_lines.append("## AI-Generated Summary")
            report_lines.append("")
            try:
                llm_summary = self.llm_client.generate_status_summary(status_report)
                report_lines.append(llm_summary)
                report_lines.append("")
            except Exception as e:
                report_lines.append(f"*Error generating AI summary: {e}*")
                report_lines.append("")
        
        # Daily Breakdown
        report_lines.append("## Daily Activity Breakdown")
        report_lines.append("")
        
        for daily_summary in status_report.daily_summaries:
            if daily_summary.total_commits > 0:
                report_lines.append(f"### {daily_summary.date.strftime('%Y-%m-%d (%A)')}")
                report_lines.append("")
                report_lines.append(f"- **Commits**: {daily_summary.total_commits}")
                report_lines.append(f"- **Repositories**: {', '.join(daily_summary.repositories)}")
                report_lines.append(f"- **Changes**: +{daily_summary.total_additions:,} / -{daily_summary.total_deletions:,}")
                report_lines.append(f"- **Files Changed**: {daily_summary.total_files_changed}")
                
                if daily_summary.primary_languages:
                    report_lines.append(f"- **Languages**: {', '.join(daily_summary.primary_languages)}")
                
                # Repository-specific details
                if len(daily_summary.repositories) > 1:
                    report_lines.append("")
                    report_lines.append("**Repository Details**:")
                    for repo_name, activity in daily_summary.activity_by_repo.items():
                        report_lines.append(f"- **{repo_name}**: {activity.commit_count} commits, {activity.total_additions} additions, {activity.total_deletions} deletions")
                
                # Recent commit messages
                if daily_summary.activity_by_repo:
                    first_repo_activity = list(daily_summary.activity_by_repo.values())[0]
                    if first_repo_activity.commits:
                        report_lines.append("")
                        report_lines.append("**Recent Commits**:")
                        for commit in first_repo_activity.commits[:3]:
                            report_lines.append(f"- {commit.message[:80]}{'...' if len(commit.message) > 80 else ''}")
                
                report_lines.append("")
            else:
                report_lines.append(f"### {daily_summary.date.strftime('%Y-%m-%d (%A)')}")
                report_lines.append("*No commits on this day*")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_json_report(self, status_report: StatusReport) -> str:
        """Generate a JSON formatted status report."""
        
        # Convert to dict for JSON serialization
        report_dict = {
            "period": {
                "start_date": status_report.start_date.isoformat(),
                "end_date": status_report.end_date.isoformat()
            },
            "summary": {
                "total_repositories": status_report.total_repositories,
                "total_commits": status_report.total_commits,
                "total_additions": status_report.total_additions,
                "total_deletions": status_report.total_deletions,
                "net_changes": status_report.total_additions - status_report.total_deletions,
                "most_active_repos": status_report.most_active_repos
            },
            "daily_activity": []
        }
        
        # Add daily summaries
        for daily_summary in status_report.daily_summaries:
            daily_dict = {
                "date": daily_summary.date.isoformat(),
                "total_commits": daily_summary.total_commits,
                "repositories": daily_summary.repositories,
                "total_additions": daily_summary.total_additions,
                "total_deletions": daily_summary.total_deletions,
                "total_files_changed": daily_summary.total_files_changed,
                "primary_languages": daily_summary.primary_languages,
                "repository_details": {}
            }
            
            for repo_name, activity in daily_summary.activity_by_repo.items():
                daily_dict["repository_details"][repo_name] = {
                    "commits": activity.commit_count,
                    "additions": activity.total_additions,
                    "deletions": activity.total_deletions,
                    "files_changed": activity.total_files_changed,
                    "commit_messages": [commit.message for commit in activity.commits]
                }
            
            report_dict["daily_activity"].append(daily_dict)
        
        # Add LLM summary if available
        if status_report.llm_summary:
            report_dict["ai_summary"] = status_report.llm_summary
        
        return json.dumps(report_dict, indent=2)
    
    def generate_csv_report(self, status_report: StatusReport) -> str:
        """Generate a CSV formatted status report."""
        
        csv_lines = []
        
        # Header
        csv_lines.append("Date,Repository,Commits,Additions,Deletions,Files Changed,Net Changes")
        
        # Daily data
        for daily_summary in status_report.daily_summaries:
            if daily_summary.total_commits > 0:
                for repo_name, activity in daily_summary.activity_by_repo.items():
                    net_changes = activity.total_additions - activity.total_deletions
                    csv_lines.append(
                        f"{daily_summary.date.strftime('%Y-%m-%d')},"
                        f"{repo_name},"
                        f"{activity.commit_count},"
                        f"{activity.total_additions},"
                        f"{activity.total_deletions},"
                        f"{activity.total_files_changed},"
                        f"{net_changes}"
                    )
            else:
                csv_lines.append(f"{daily_summary.date.strftime('%Y-%m-%d')},No Activity,0,0,0,0,0")
        
        return "\n".join(csv_lines)
    
    def save_report(
        self, 
        status_report: StatusReport, 
        output_path: str, 
        format: str = "markdown",
        include_llm_summary: bool = True
    ) -> None:
        """Save a status report to a file."""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "markdown":
            content = self.generate_markdown_report(status_report, include_llm_summary)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.md')
        elif format.lower() == "json":
            content = self.generate_json_report(status_report)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.json')
        elif format.lower() == "csv":
            content = self.generate_csv_report(status_report)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.csv')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Report saved to: {output_path}")
    
    def generate_daily_summary_report(
        self, 
        daily_summary: WorkSummary, 
        format: str = "markdown"
    ) -> str:
        """Generate a report for a single day's activity."""
        
        if format.lower() == "markdown":
            return self._generate_daily_markdown(daily_summary)
        elif format.lower() == "json":
            return self._generate_daily_json(daily_summary)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_daily_markdown(self, daily_summary: WorkSummary) -> str:
        """Generate markdown for a single day's activity."""
        
        lines = []
        lines.append(f"# Daily Activity Report - {daily_summary.date.strftime('%Y-%m-%d')}")
        lines.append("")
        
        if daily_summary.total_commits == 0:
            lines.append("No commits made on this day.")
            return "\n".join(lines)
        
        lines.append(f"**Total Commits**: {daily_summary.total_commits}")
        lines.append(f"**Repositories**: {', '.join(daily_summary.repositories)}")
        lines.append(f"**Changes**: +{daily_summary.total_additions:,} / -{daily_summary.total_deletions:,}")
        lines.append(f"**Files Changed**: {daily_summary.total_files_changed}")
        lines.append("")
        
        # Repository details
        for repo_name, activity in daily_summary.activity_by_repo.items():
            lines.append(f"## {repo_name}")
            lines.append("")
            lines.append(f"- Commits: {activity.commit_count}")
            lines.append(f"- Additions: {activity.total_additions}")
            lines.append(f"- Deletions: {activity.total_deletions}")
            lines.append(f"- Files Changed: {activity.total_files_changed}")
            lines.append("")
            
            if activity.commits:
                lines.append("**Commit Messages**:")
                for commit in activity.commits:
                    lines.append(f"- {commit.message}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_daily_json(self, daily_summary: WorkSummary) -> str:
        """Generate JSON for a single day's activity."""
        
        daily_dict = {
            "date": daily_summary.date.isoformat(),
            "total_commits": daily_summary.total_commits,
            "repositories": daily_summary.repositories,
            "total_additions": daily_summary.total_additions,
            "total_deletions": daily_summary.total_deletions,
            "total_files_changed": daily_summary.total_files_changed,
            "primary_languages": daily_summary.primary_languages,
            "repository_details": {}
        }
        
        for repo_name, activity in daily_summary.activity_by_repo.items():
            daily_dict["repository_details"][repo_name] = {
                "commits": activity.commit_count,
                "additions": activity.total_additions,
                "deletions": activity.total_deletions,
                "files_changed": activity.total_files_changed,
                "commit_messages": [commit.message for commit in activity.commits]
            }
        
        return json.dumps(daily_dict, indent=2)
