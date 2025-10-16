"""Data processing logic for analyzing commits and generating summaries."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict, Counter

from .models import Commit, DailyActivity, WorkSummary, StatusReport, Repository
from .github_client import GitHubClient


class DataProcessor:
    """Processes GitHub data to generate meaningful insights."""
    
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
    
    def generate_status_report(
        self, 
        days_back: int = 7, 
        repositories: Optional[List[str]] = None
    ) -> StatusReport:
        """Generate a comprehensive status report for the specified period."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get activity data
        if repositories:
            activity = {}
            for repo_name in repositories:
                commits = self.github_client.get_commits_for_repository(
                    repo_name, start_date, end_date
                )
                if commits:
                    activity[repo_name] = commits
        else:
            activity = self.github_client.get_recent_activity(days_back)
        
        # Process daily activities
        daily_summaries = self._process_daily_activities(activity, start_date, end_date)
        
        # Calculate totals
        total_commits = sum(summary.total_commits for summary in daily_summaries)
        total_additions = sum(summary.total_additions for summary in daily_summaries)
        total_deletions = sum(summary.total_deletions for summary in daily_summaries)
        
        # Find most active repositories
        repo_activity = defaultdict(int)
        for summary in daily_summaries:
            for repo_name, repo_activity_data in summary.activity_by_repo.items():
                repo_activity[repo_name] += repo_activity_data.commit_count
        
        most_active_repos = sorted(
            repo_activity.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return StatusReport(
            start_date=start_date,
            end_date=end_date,
            daily_summaries=daily_summaries,
            total_repositories=len(activity),
            total_commits=total_commits,
            total_additions=total_additions,
            total_deletions=total_deletions,
            most_active_repos=[repo for repo, _ in most_active_repos]
        )
    
    def _process_daily_activities(
        self, 
        activity: Dict[str, List[Commit]], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[WorkSummary]:
        """Process commits into daily activity summaries."""
        
        # Group commits by date
        daily_commits = defaultdict(lambda: defaultdict(list))
        
        for repo_name, commits in activity.items():
            for commit in commits:
                # Normalize date to start of day
                commit_date = commit.date.replace(hour=0, minute=0, second=0, microsecond=0)
                daily_commits[commit_date][repo_name].append(commit)
        
        # Generate daily summaries
        daily_summaries = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_date:
            if current_date in daily_commits:
                summary = self._create_daily_summary(current_date, daily_commits[current_date])
                daily_summaries.append(summary)
            else:
                # Create empty summary for days with no activity
                summary = WorkSummary(
                    date=current_date,
                    repositories=[],
                    total_commits=0,
                    total_additions=0,
                    total_deletions=0,
                    total_files_changed=0,
                    activity_by_repo={},
                    primary_languages=[]
                )
                daily_summaries.append(summary)
            
            current_date += timedelta(days=1)
        
        return daily_summaries
    
    def _create_daily_summary(
        self, 
        date: datetime, 
        repo_commits: Dict[str, List[Commit]]
    ) -> WorkSummary:
        """Create a daily summary for a specific date."""
        
        activity_by_repo = {}
        total_commits = 0
        total_additions = 0
        total_deletions = 0
        total_files_changed = 0
        languages = []
        
        for repo_name, commits in repo_commits.items():
            daily_activity = DailyActivity(
                date=date,
                repository=repo_name,
                commits=commits
            )
            
            # Recalculate totals (post_init doesn't work with Pydantic v2)
            daily_activity.total_additions = sum(commit.additions for commit in commits)
            daily_activity.total_deletions = sum(commit.deletions for commit in commits)
            daily_activity.total_files_changed = sum(commit.files_changed for commit in commits)
            daily_activity.commit_count = len(commits)
            
            activity_by_repo[repo_name] = daily_activity
            
            total_commits += daily_activity.commit_count
            total_additions += daily_activity.total_additions
            total_deletions += daily_activity.total_deletions
            total_files_changed += daily_activity.total_files_changed
        
        # Determine primary languages (simplified - would need repo language data)
        primary_languages = self._get_primary_languages(activity_by_repo)
        
        return WorkSummary(
            date=date,
            repositories=list(repo_commits.keys()),
            total_commits=total_commits,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_files_changed=total_files_changed,
            activity_by_repo=activity_by_repo,
            primary_languages=primary_languages
        )
    
    def _get_primary_languages(self, activity_by_repo: Dict[str, DailyActivity]) -> List[str]:
        """Get primary programming languages from file extensions."""
        file_extensions = Counter()
        
        for repo_activity in activity_by_repo.values():
            for commit in repo_activity.commits:
                for file_path in commit.files:
                    if '.' in file_path:
                        ext = file_path.split('.')[-1].lower()
                        file_extensions[ext] += 1
        
        # Map extensions to languages
        extension_to_language = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'go': 'Go',
            'rs': 'Rust',
            'php': 'PHP',
            'rb': 'Ruby',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'r': 'R',
            'sql': 'SQL',
            'html': 'HTML',
            'css': 'CSS',
            'scss': 'SCSS',
            'sass': 'Sass',
            'json': 'JSON',
            'yaml': 'YAML',
            'yml': 'YAML',
            'xml': 'XML',
            'md': 'Markdown',
            'sh': 'Shell',
            'bash': 'Bash',
            'dockerfile': 'Docker',
            'tf': 'Terraform',
            'hcl': 'HCL'
        }
        
        languages = []
        for ext, count in file_extensions.most_common(5):
            if ext in extension_to_language:
                languages.append(extension_to_language[ext])
        
        return languages
    
    def get_repository_statistics(self, repo_name: str, days_back: int = 30) -> Dict[str, Any]:
        """Get detailed statistics for a specific repository."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        commits = self.github_client.get_commits_for_repository(repo_name, start_date, end_date)
        
        if not commits:
            return {
                'repository': repo_name,
                'period_days': days_back,
                'total_commits': 0,
                'total_additions': 0,
                'total_deletions': 0,
                'total_files_changed': 0,
                'average_commits_per_day': 0,
                'most_active_days': [],
                'commit_messages': []
            }
        
        # Calculate statistics
        total_additions = sum(commit.additions for commit in commits)
        total_deletions = sum(commit.deletions for commit in commits)
        total_files_changed = sum(commit.files_changed for commit in commits)
        
        # Group by day
        daily_commits = defaultdict(int)
        for commit in commits:
            day = commit.date.strftime('%Y-%m-%d')
            daily_commits[day] += 1
        
        most_active_days = sorted(
            daily_commits.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            'repository': repo_name,
            'period_days': days_back,
            'total_commits': len(commits),
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'total_files_changed': total_files_changed,
            'average_commits_per_day': len(commits) / days_back,
            'most_active_days': most_active_days,
            'commit_messages': [commit.message for commit in commits[:10]]  # Last 10 commits
        }
