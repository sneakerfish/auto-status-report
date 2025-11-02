"""Report generation system for creating formatted status reports."""

from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path
import json
import pytz

from .models import StatusReport, WorkSummary, DailyActivity, Commit
from .llm_client import LLMClient


class ReportGenerator:
    """Generates formatted status reports in various formats."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.eastern_tz = pytz.timezone('US/Eastern')

    def _convert_to_eastern(self, dt: datetime) -> str:
        """Convert a datetime to US Eastern timezone and format it."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)
        eastern_time = dt.astimezone(self.eastern_tz)
        return eastern_time.strftime('%Y-%m-%d %I:%M %p %Z')

    def _parse_commit_message(self, message: str) -> Tuple[str, Optional[str]]:
        """Parse commit message into summary and details.

        Returns (summary, details) where details is None if not present or if it's too similar to summary.
        """
        lines = message.split('\n')
        summary = lines[0].strip()

        # Find the detailed description (skip blank lines)
        details_lines = []
        for line in lines[1:]:
            stripped = line.strip()
            if stripped:
                details_lines.append(stripped)

        if not details_lines:
            return summary, None

        details = ' '.join(details_lines)

        # Check if details is too similar to summary (simple check)
        # If details starts with the same words or is very similar, skip it
        if details.lower().startswith(summary.lower()[:20]) or summary.lower().startswith(details.lower()[:20]):
            return summary, None

        # If details is just a longer version of summary with minor additions, skip it
        summary_words = set(summary.lower().split())
        details_words = set(details.lower().split())

        # If 80% of words overlap, consider them too similar
        if len(summary_words) > 0:
            overlap = len(summary_words & details_words) / len(summary_words)
            if overlap > 0.8:
                return summary, None

        return summary, details

    def _strip_line_markings(self, text: str) -> str:
        """Remove line markings like (lines 27-28, 60-109) from text."""
        import re
        # Pattern matches (lines X-Y, Z-W) or (lines X-Y) etc.
        pattern = r'\s*\(lines\s+[\d\-,\s]+\)'
        return re.sub(pattern, '', text)

    def _create_commit_narrative(self, commits: List[Commit]) -> str:
        """Create a narrative paragraph from commit messages."""
        if not commits:
            return "No commits."

        narratives = []
        for commit in commits:
            # Use the full commit message, not just parsed parts
            full_message = self._strip_line_markings(commit.message)
            narratives.append(full_message.strip())

        # Join into a flowing paragraph
        return ' '.join(narratives)
    
    def generate_markdown_report(
        self,
        status_report: StatusReport,
        include_llm_summary: bool = True
    ) -> str:
        """Generate a diary-style markdown formatted status report."""

        report_lines = []

        # Header
        report_lines.append("# GitHub Activity Status Report")
        report_lines.append("")
        report_lines.append(f"**Period**: {status_report.start_date.strftime('%Y-%m-%d')} to {status_report.end_date.strftime('%Y-%m-%d')}")
        report_lines.append(f"**Generated**: {status_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Executive Summary
        active_days = len([s for s in status_report.daily_summaries if s.total_commits > 0])
        report_lines.append("## Overview")
        report_lines.append("")
        report_lines.append(f"During this {len(status_report.daily_summaries)}-day period, you worked across **{status_report.total_repositories} repositories** "
                           f"on **{active_days} active days**, making **{status_report.total_commits} commits** with "
                           f"**{status_report.total_additions:,} lines added** and **{status_report.total_deletions:,} lines deleted** "
                           f"(net: **{status_report.total_additions - status_report.total_deletions:,} lines**).")
        report_lines.append("")

        # Most Active Repositories
        if status_report.most_active_repos:
            repo_list = ', '.join(f"**{repo}**" for repo in status_report.most_active_repos[:5])
            report_lines.append(f"Your most active repositories were: {repo_list}.")
            report_lines.append("")

        # Note: Overall AI summary removed - using daily summaries instead

        # Daily Diary-Style Breakdown
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Daily Activity")
        report_lines.append("")

        for daily_summary in status_report.daily_summaries:
            if daily_summary.total_commits > 0:
                report_lines.append(f"### {daily_summary.date.strftime('%A, %B %d, %Y')}")
                report_lines.append("")

                # Collect all commits from all repositories for this day
                all_commits = []
                for repo_name, activity in daily_summary.activity_by_repo.items():
                    for commit in activity.commits:
                        all_commits.append((repo_name, commit))

                # Sort commits by time
                all_commits.sort(key=lambda x: x[1].date)

                # Create single table for all commits on this day
                report_lines.append("| Commit ID | Time (US/Eastern) | Repository | Changes (+/-) |")
                report_lines.append("|-----------|-------------------|------------|---------------|")

                for repo_name, commit in all_commits:
                    short_sha = commit.sha[:7]
                    timestamp = self._convert_to_eastern(commit.date)
                    lines_changed = f"+{commit.additions}/-{commit.deletions}"

                    report_lines.append(f"| `{short_sha}` | {timestamp} | {repo_name} | {lines_changed} |")

                report_lines.append("")

                # Generate AI summary for this day's commits
                if include_llm_summary:
                    try:
                        daily_ai_summary = self.llm_client.generate_daily_summary(daily_summary)
                        report_lines.append(daily_ai_summary)
                        report_lines.append("")
                    except Exception as e:
                        # Fallback to manual narrative if LLM fails
                        commits_only = [commit for _, commit in all_commits]
                        narrative = self._create_commit_narrative(commits_only)
                        report_lines.append(narrative)
                        report_lines.append("")
                else:
                    # If LLM disabled, use manual narrative
                    commits_only = [commit for _, commit in all_commits]
                    narrative = self._create_commit_narrative(commits_only)
                    report_lines.append(narrative)
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
