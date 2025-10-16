"""GitHub API client for fetching repository and commit data."""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import parser
import time

from .config import settings
from .models import Repository, Commit


class GitHubClient:
    """Client for interacting with the GitHub API."""
    
    def __init__(self):
        self.base_url = settings.github_api_base_url
        self.token = settings.github_token
        self.username = settings.github_username
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'auto-status-report/{self.username}'
        })
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the GitHub API with error handling."""
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=settings.github_api_timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise
    
    def get_user_repositories(self, include_private: bool = True) -> List[Repository]:
        """Get all repositories owned by the authenticated user."""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            params = {
                'type': 'all' if include_private else 'public',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': per_page,
                'page': page,
                'affiliation': 'owner'  # Only get repositories owned by the user
            }
            
            url = f"{self.base_url}/user/repos"
            data = self._make_request(url, params)
            
            if not data:
                break
                
            for repo_data in data:
                # Double-check that the owner is the authenticated user
                if repo_data['owner']['login'].lower() == self.username.lower():
                    repo = Repository(
                        name=repo_data['name'],
                        full_name=repo_data['full_name'],
                        description=repo_data.get('description'),
                        url=repo_data['html_url'],
                        language=repo_data.get('language'),
                        stars=repo_data['stargazers_count'],
                        forks=repo_data['forks_count'],
                        private=repo_data['private']
                    )
                    repos.append(repo)
            
            if len(data) < per_page:
                break
                
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return repos
    
    def get_collaborator_repositories(self, include_private: bool = True) -> List[Repository]:
        """Get repositories where the user is a collaborator (not owner)."""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            params = {
                'type': 'all' if include_private else 'public',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': per_page,
                'page': page,
                'affiliation': 'collaborator'  # Only get repositories where user is collaborator
            }
            
            url = f"{self.base_url}/user/repos"
            data = self._make_request(url, params)
            
            if not data:
                break
                
            for repo_data in data:
                repo = Repository(
                    name=repo_data['name'],
                    full_name=repo_data['full_name'],
                    description=repo_data.get('description'),
                    url=repo_data['html_url'],
                    language=repo_data.get('language'),
                    stars=repo_data['stargazers_count'],
                    forks=repo_data['forks_count'],
                    private=repo_data['private']
                )
                repos.append(repo)
            
            if len(data) < per_page:
                break
                
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return repos
    
    def get_commits_for_repository(
        self, 
        repo_name: str, 
        since: datetime, 
        until: Optional[datetime] = None
    ) -> List[Commit]:
        """Get commits for a specific repository within a date range."""
        commits = []
        page = 1
        per_page = 100
        
        params = {
            'author': self.username,
            'since': since.isoformat(),
            'per_page': per_page,
            'page': page
        }
        
        if until:
            params['until'] = until.isoformat()
        
        while True:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}/commits"
            data = self._make_request(url, params)
            
            if not data:
                break
            
            for commit_data in data:
                # Get detailed commit information including stats
                commit_detail = self._get_commit_details(repo_name, commit_data['sha'])
                
                commit = Commit(
                    sha=commit_data['sha'],
                    message=commit_data['commit']['message'],
                    author=commit_data['commit']['author']['name'],
                    date=parser.parse(commit_data['commit']['author']['date']),
                    url=commit_data['html_url'],
                    additions=commit_detail.get('stats', {}).get('additions', 0),
                    deletions=commit_detail.get('stats', {}).get('deletions', 0),
                    files_changed=len(commit_detail.get('files', [])),
                    files=[f['filename'] for f in commit_detail.get('files', [])]
                )
                commits.append(commit)
            
            if len(data) < per_page:
                break
                
            page += 1
            params['page'] = page
            time.sleep(0.1)  # Rate limiting
        
        return commits
    
    def _get_commit_details(self, repo_name: str, sha: str) -> Dict[str, Any]:
        """Get detailed information about a specific commit."""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/commits/{sha}"
        return self._make_request(url)
    
    def get_recent_activity(self, days_back: int = 7, include_collaborator: bool = None) -> Dict[str, List[Commit]]:
        """Get recent activity across all repositories."""
        from .config import settings
        
        if include_collaborator is None:
            include_collaborator = settings.include_collaborator_repos
            
        since = datetime.now() - timedelta(days=days_back)
        
        if include_collaborator:
            # Get both owned and collaborator repositories
            owned_repos = self.get_user_repositories()
            collaborator_repos = self.get_collaborator_repositories()
            repositories = owned_repos + collaborator_repos
        else:
            # Only owned repositories (default)
            repositories = self.get_user_repositories()
        
        activity = {}
        
        for repo in repositories:
            print(f"Fetching commits for {repo.name}...")
            commits = self.get_commits_for_repository(repo.name, since)
            if commits:
                activity[repo.name] = commits
            time.sleep(0.2)  # Rate limiting between repositories
        
        return activity
    
    def test_connection(self) -> bool:
        """Test the GitHub API connection."""
        try:
            url = f"{self.base_url}/user"
            self._make_request(url)
            return True
        except Exception as e:
            print(f"GitHub API connection test failed: {e}")
            return False
