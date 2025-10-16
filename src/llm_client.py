"""LLM client for generating intelligent status report summaries using Ollama."""

from typing import List, Dict, Any, Optional
import requests
import json

from .config import settings
from .models import StatusReport, WorkSummary, DailyActivity


class LLMClient:
    """Client for generating intelligent summaries using Ollama."""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = 120  # Ollama can take longer than OpenAI
    
    def _call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Make a call to the Ollama API."""
        
        # Prepare the full prompt with system message if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API call failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Ollama response: {e}")
    
    def test_connection(self) -> bool:
        """Test the connection to Ollama."""
        try:
            # Try to list models to test connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False
    
    def generate_status_summary(self, status_report: StatusReport) -> str:
        """Generate an intelligent summary of the status report."""
        
        # Prepare data for the LLM
        report_data = self._prepare_report_data(status_report)
        
        prompt = self._create_summary_prompt(report_data)
        
        try:
            response = self._call_ollama(prompt, system_prompt="You are a helpful assistant that creates concise, professional status reports for software developers. Focus on key achievements, patterns, and insights from their GitHub activity.")
            return response.strip()
            
        except Exception as e:
            print(f"Error generating LLM summary: {e}")
            return self._generate_fallback_summary(status_report)
    
    def generate_daily_summary(self, daily_summary: WorkSummary) -> str:
        """Generate a summary for a specific day's activity."""
        
        if daily_summary.total_commits == 0:
            return "No commits made on this day."
        
        # Prepare daily data
        daily_data = {
            'date': daily_summary.date.strftime('%Y-%m-%d'),
            'repositories': daily_summary.repositories,
            'total_commits': daily_summary.total_commits,
            'total_additions': daily_summary.total_additions,
            'total_deletions': daily_summary.total_deletions,
            'total_files_changed': daily_summary.total_files_changed,
            'primary_languages': daily_summary.primary_languages,
            'activity_by_repo': {}
        }
        
        # Add repository-specific details
        for repo_name, activity in daily_summary.activity_by_repo.items():
            daily_data['activity_by_repo'][repo_name] = {
                'commits': activity.commit_count,
                'additions': activity.total_additions,
                'deletions': activity.total_deletions,
                'files_changed': activity.total_files_changed,
                'commit_messages': [commit.message for commit in activity.commits[:3]]  # Top 3 commits
            }
        
        prompt = self._create_daily_prompt(daily_data)
        
        try:
            response = self._call_ollama(prompt, system_prompt="You are a helpful assistant that creates brief, informative daily summaries for software developers. Highlight the main work done and any notable patterns.")
            return response.strip()
            
        except Exception as e:
            print(f"Error generating daily LLM summary: {e}")
            return self._generate_fallback_daily_summary(daily_summary)
    
    def _prepare_report_data(self, status_report: StatusReport) -> Dict[str, Any]:
        """Prepare status report data for LLM processing."""
        
        # Calculate some additional metrics
        active_days = len([s for s in status_report.daily_summaries if s.total_commits > 0])
        total_days = len(status_report.daily_summaries)
        
        # Get top commit messages for context
        all_commits = []
        for daily_summary in status_report.daily_summaries:
            for activity in daily_summary.activity_by_repo.values():
                all_commits.extend([commit.message for commit in activity.commits])
        
        # Get most active days
        daily_activity = []
        for daily_summary in status_report.daily_summaries:
            if daily_summary.total_commits > 0:
                daily_activity.append({
                    'date': daily_summary.date.strftime('%Y-%m-%d'),
                    'commits': daily_summary.total_commits,
                    'repositories': daily_summary.repositories
                })
        
        return {
            'period': {
                'start_date': status_report.start_date.strftime('%Y-%m-%d'),
                'end_date': status_report.end_date.strftime('%Y-%m-%d'),
                'total_days': total_days,
                'active_days': active_days
            },
            'totals': {
                'repositories': status_report.total_repositories,
                'commits': status_report.total_commits,
                'additions': status_report.total_additions,
                'deletions': status_report.total_deletions,
                'net_changes': status_report.total_additions - status_report.total_deletions
            },
            'most_active_repos': status_report.most_active_repos,
            'daily_activity': daily_activity,
            'recent_commits': all_commits[:10]  # Last 10 commit messages
        }
    
    def _create_summary_prompt(self, report_data: Dict[str, Any]) -> str:
        """Create a prompt for generating the status report summary."""
        
        return f"""
Please analyze the following GitHub activity data and create a professional status report summary:

**Period**: {report_data['period']['start_date']} to {report_data['period']['end_date']} ({report_data['period']['total_days']} days, {report_data['period']['active_days']} active days)

**Activity Summary**:
- Repositories worked on: {report_data['totals']['repositories']}
- Total commits: {report_data['totals']['commits']}
- Lines added: {report_data['totals']['additions']}
- Lines deleted: {report_data['totals']['deletions']}
- Net changes: {report_data['totals']['net_changes']}

**Most Active Repositories**: {', '.join(report_data['most_active_repos'])}

**Recent Commit Messages** (for context):
{chr(10).join(f"- {msg}" for msg in report_data['recent_commits'])}

**Daily Activity**:
{chr(10).join(f"- {day['date']}: {day['commits']} commits across {len(day['repositories'])} repos" for day in report_data['daily_activity'])}

Please provide a concise summary (2-3 paragraphs) that:
1. Highlights the main areas of work and repositories
2. Identifies any patterns or trends in the development activity
3. Provides insights about the developer's focus and productivity
4. Mentions any notable achievements or milestones

Keep the tone professional and informative, suitable for a status report.
"""
    
    def _create_daily_prompt(self, daily_data: Dict[str, Any]) -> str:
        """Create a prompt for generating a daily summary."""
        
        repo_details = []
        for repo_name, details in daily_data['activity_by_repo'].items():
            repo_details.append(f"- {repo_name}: {details['commits']} commits, {details['additions']} additions, {details['deletions']} deletions")
        
        return f"""
Please create a brief daily summary for {daily_data['date']}:

**Activity**:
- Total commits: {daily_data['total_commits']}
- Lines added: {daily_data['total_additions']}
- Lines deleted: {daily_data['total_deletions']}
- Files changed: {daily_data['total_files_changed']}
- Repositories: {', '.join(daily_data['repositories'])}

**Repository Details**:
{chr(10).join(repo_details)}

**Primary Languages**: {', '.join(daily_data['primary_languages']) if daily_data['primary_languages'] else 'Not specified'}

**Recent Commit Messages**:
{chr(10).join(f"- {msg}" for msg in daily_data['activity_by_repo'].get(list(daily_data['activity_by_repo'].keys())[0], {}).get('commit_messages', []))}

Provide a concise 1-2 sentence summary of the day's work, highlighting the main focus areas and any notable changes.
"""
    
    def _generate_fallback_summary(self, status_report: StatusReport) -> str:
        """Generate a fallback summary when LLM is unavailable."""
        
        active_days = len([s for s in status_report.daily_summaries if s.total_commits > 0])
        net_changes = status_report.total_additions - status_report.total_deletions
        
        return f"""
**Status Report Summary ({status_report.start_date.strftime('%Y-%m-%d')} to {status_report.end_date.strftime('%Y-%m-%d')})**

During this {len(status_report.daily_summaries)}-day period, you were active on {active_days} days across {status_report.total_repositories} repositories. 
You made {status_report.total_commits} commits with {status_report.total_additions} additions and {status_report.total_deletions} deletions (net: {net_changes} lines).

Your most active repositories were: {', '.join(status_report.most_active_repos[:3])}.

This represents consistent development activity with focus on multiple projects.
"""
    
    def _generate_fallback_daily_summary(self, daily_summary: WorkSummary) -> str:
        """Generate a fallback daily summary when LLM is unavailable."""
        
        if daily_summary.total_commits == 0:
            return f"No commits made on {daily_summary.date.strftime('%Y-%m-%d')}."
        
        net_changes = daily_summary.total_additions - daily_summary.total_deletions
        repos_str = ', '.join(daily_summary.repositories)
        
        return f"""
On {daily_summary.date.strftime('%Y-%m-%d')}, you made {daily_summary.total_commits} commits across {len(daily_summary.repositories)} repositories ({repos_str}). 
Total changes: {daily_summary.total_additions} additions, {daily_summary.total_deletions} deletions (net: {net_changes} lines), {daily_summary.total_files_changed} files changed.
"""
