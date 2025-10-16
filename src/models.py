"""Data models for the auto status report application."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Commit(BaseModel):
    """Represents a single Git commit."""
    
    sha: str
    message: str
    author: str
    date: datetime
    url: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    files: List[str] = Field(default_factory=list)


class Repository(BaseModel):
    """Represents a GitHub repository."""
    
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    private: bool = False


class DailyActivity(BaseModel):
    """Represents daily activity for a repository."""
    
    date: datetime
    repository: str
    commits: List[Commit] = Field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0
    commit_count: int = 0
    
    def __post_init__(self):
        """Calculate totals after initialization."""
        self.total_additions = sum(commit.additions for commit in self.commits)
        self.total_deletions = sum(commit.deletions for commit in self.commits)
        self.total_files_changed = sum(commit.files_changed for commit in self.commits)
        self.commit_count = len(self.commits)


class WorkSummary(BaseModel):
    """Represents a summary of work for a specific day."""
    
    date: datetime
    repositories: List[str] = Field(default_factory=list)
    total_commits: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0
    activity_by_repo: Dict[str, DailyActivity] = Field(default_factory=dict)
    primary_languages: List[str] = Field(default_factory=list)


class StatusReport(BaseModel):
    """Complete status report for a date range."""
    
    start_date: datetime
    end_date: datetime
    daily_summaries: List[WorkSummary] = Field(default_factory=list)
    total_repositories: int = 0
    total_commits: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    most_active_repos: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    llm_summary: Optional[str] = None
