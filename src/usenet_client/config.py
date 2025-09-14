"""Configuration management for UseNet client."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Config:
    """Handle configuration storage and retrieval."""

    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = Path.home() / '.usenet_client'
        self.config_file = self.config_dir / 'config.json'
        self.cache_file = self.config_dir / 'newsgroups_cache.json'
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create configuration directory if it doesn't exist."""
        self.config_dir.mkdir(exist_ok=True)

    def save_provider_config(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False
    ) -> None:
        """Save NNTP provider configuration."""
        config = {
            'provider': {
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'use_ssl': use_ssl
            }
        }

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def load_provider_config(self) -> Optional[Dict[str, any]]:
        """Load NNTP provider configuration."""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('provider')
        except (json.JSONDecodeError, KeyError):
            return None

    def clear_config(self) -> None:
        """Remove configuration file."""
        if self.config_file.exists():
            self.config_file.unlink()

    def save_newsgroups_cache(self, groups: List[Tuple[str, int, int, str]]) -> None:
        """Save newsgroups list to cache with timestamp."""
        cache_data = {
            'timestamp': time.time(),
            'groups': [
                {
                    'name': name,
                    'last': last,
                    'first': first,
                    'flag': flag
                }
                for name, last, first, flag in groups
            ]
        }

        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def load_newsgroups_cache(self, max_age_hours: int = 24) -> Optional[List[Tuple[str, int, int, str]]]:
        """Load newsgroups list from cache if not expired."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is expired
            cache_age = time.time() - cache_data['timestamp']
            if cache_age > max_age_hours * 3600:
                return None

            # Convert back to tuple format
            groups = [
                (group['name'], group['last'], group['first'], group['flag'])
                for group in cache_data['groups']
            ]

            return groups

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def get_cache_info(self) -> Optional[Dict[str, any]]:
        """Get information about the current cache."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            cache_age = time.time() - cache_data['timestamp']
            return {
                'timestamp': cache_data['timestamp'],
                'age_hours': cache_age / 3600,
                'group_count': len(cache_data['groups']),
                'is_expired': cache_age > 24 * 3600
            }

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def clear_cache(self) -> None:
        """Remove newsgroups cache file."""
        if self.cache_file.exists():
            self.cache_file.unlink()