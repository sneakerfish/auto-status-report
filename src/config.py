"""Configuration management for the auto status report application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # GitHub Configuration
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_username = os.getenv("GITHUB_USERNAME", "")
        
        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3:latest")
        
        # Report Configuration
        self.default_days_back = int(os.getenv("DEFAULT_DAYS_BACK", "7"))
        self.report_format = os.getenv("REPORT_FORMAT", "markdown")
        
        # GitHub API Configuration
        self.github_api_base_url = "https://api.github.com"
        self.github_api_timeout = 30
        
        # Validate required settings
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.github_username:
            raise ValueError("GITHUB_USERNAME environment variable is required")


# Global settings instance
settings = Settings()
