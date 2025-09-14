"""Agent tools for the UseNet client.

This module provides LLMTool implementations that expose UseNet client functionality
to the mojentic conversational agent framework.
"""

from typing import List, Dict, Any, Optional
from mojentic.llm.tools.llm_tool import LLMTool

from .usenet_service import UseNetService


class SetupProviderTool(LLMTool):
    """Tool for configuring NNTP provider settings."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, host: str, port: int = 119, username: Optional[str] = None,
            password: Optional[str] = None, use_ssl: bool = False) -> Dict[str, Any]:
        """Configure NNTP provider settings."""
        return self.service.setup_provider(host, port, username, password, use_ssl)

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "setup_nntp_provider",
                "description": "Configure NNTP/UseNet provider settings including server, port, authentication, and SSL options.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "description": "NNTP server hostname (e.g., 'news.example.com')"
                        },
                        "port": {
                            "type": "integer",
                            "description": "NNTP server port (default: 119 for standard, 563 for SSL)",
                            "default": 119
                        },
                        "username": {
                            "type": "string",
                            "description": "Username for authentication (optional)"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for authentication (optional)"
                        },
                        "use_ssl": {
                            "type": "boolean",
                            "description": "Whether to use SSL/TLS connection",
                            "default": False
                        }
                    },
                    "required": ["host"]
                }
            }
        }


class ListNewsgroupsTool(LLMTool):
    """Tool for listing available newsgroups."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, pattern: Optional[str] = None, max_results: int = 100,
            all_groups: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """List available newsgroups, optionally filtered by pattern."""
        return self.service.list_newsgroups(pattern, max_results, all_groups, use_cache)

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "list_newsgroups",
                "description": "List available newsgroups from the NNTP server, with optional filtering by pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to filter newsgroups (e.g., 'amiga', 'comp.sys'). Case-insensitive substring match."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of groups to return",
                            "default": 100
                        },
                        "all_groups": {
                            "type": "boolean",
                            "description": "Return all matching groups (ignores max_results limit)",
                            "default": False
                        },
                        "use_cache": {
                            "type": "boolean",
                            "description": "Use cached newsgroup list if available",
                            "default": True
                        }
                    },
                    "required": []
                }
            }
        }


class UpdateCacheTool(LLMTool):
    """Tool for updating the newsgroups cache."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, force: bool = False) -> Dict[str, Any]:
        """Update the cached list of newsgroups from the NNTP server."""
        return self.service.update_cache(force)

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "update_newsgroups_cache",
                "description": "Update the cached list of newsgroups from the NNTP server. This can take a while for servers with many groups.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force update even if cache is recent",
                            "default": False
                        }
                    },
                    "required": []
                }
            }
        }


class GetCacheInfoTool(LLMTool):
    """Tool for getting cache information."""

    def __init__(self):
        self.service = UseNetService()

    def run(self) -> Dict[str, Any]:
        """Get information about the newsgroups cache."""
        return self.service.get_cache_info()

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "get_cache_info",
                "description": "Get information about the current newsgroups cache including age, size, and status.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }


class SearchMessagesTool(LLMTool):
    """Tool for searching messages in newsgroups."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, newsgroup: str, poster: Optional[str] = None, topic: Optional[str] = None,
            since_days: int = 7, max_messages: int = 100, use_llm: bool = True,
            confidence: float = 0.5, relevance: float = 0.5,
            multi_group: bool = False, max_groups: int = 20,
            with_body: bool = False) -> Dict[str, Any]:
        """Search for messages in newsgroups by poster, topic, or other criteria."""
        return self.service.search_messages(
            newsgroup, poster, topic, since_days, max_messages, use_llm,
            confidence, relevance, multi_group, max_groups, with_body
        )

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "search_messages",
                "description": "Search for messages in newsgroups by poster name, topic, or other criteria. Supports both single newsgroup and pattern-based multi-group searches.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "newsgroup": {
                            "type": "string",
                            "description": "Newsgroup name or pattern (e.g., 'comp.sys.amiga.misc', '*.amiga.*', 'comp.*')"
                        },
                        "poster": {
                            "type": "string",
                            "description": "Search for messages by this poster/author name. Uses intelligent matching when LLM is available."
                        },
                        "topic": {
                            "type": "string",
                            "description": "Search for messages about a specific topic (e.g., 'Amiga 1200', 'accelerator cards'). Uses AI analysis when available."
                        },
                        "since_days": {
                            "type": "integer",
                            "description": "Search messages from the last N days",
                            "default": 7
                        },
                        "max_messages": {
                            "type": "integer",
                            "description": "Maximum number of messages to retrieve",
                            "default": 100
                        },
                        "use_llm": {
                            "type": "boolean",
                            "description": "Use LLM for intelligent matching and analysis",
                            "default": True
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Minimum confidence for LLM poster matching (0.0-1.0)",
                            "default": 0.5
                        },
                        "relevance": {
                            "type": "number",
                            "description": "Minimum relevance for LLM topic matching (0.0-1.0)",
                            "default": 0.5
                        },
                        "multi_group": {
                            "type": "boolean",
                            "description": "Enable multi-group pattern search mode",
                            "default": False
                        },
                        "max_groups": {
                            "type": "integer",
                            "description": "Maximum number of groups to search when using patterns",
                            "default": 20
                        },
                        "with_body": {
                            "type": "boolean",
                            "description": "Retrieve message bodies for deeper topic analysis (slower but more accurate)",
                            "default": False
                        }
                    },
                    "required": ["newsgroup"]
                }
            }
        }


class ListMessagesTool(LLMTool):
    """Tool for listing recent message headers."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, newsgroup_pattern: str, period_days: int = 7,
            max_messages: int = 100, max_groups: int = 15) -> Dict[str, Any]:
        """List recent message headers for data verification and exploration."""
        return self.service.list_messages(newsgroup_pattern, period_days, max_messages, max_groups)

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "list_messages",
                "description": "List recent message headers from newsgroups for data verification and exploration. No LLM processing - pure data display.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "newsgroup_pattern": {
                            "type": "string",
                            "description": "Newsgroup name or pattern (e.g., 'comp.sys.amiga.misc', '*.amiga.*')"
                        },
                        "period_days": {
                            "type": "integer",
                            "description": "Show messages from the last N days",
                            "default": 7
                        },
                        "max_messages": {
                            "type": "integer",
                            "description": "Maximum number of messages to display",
                            "default": 100
                        },
                        "max_groups": {
                            "type": "integer",
                            "description": "Maximum number of groups when using patterns",
                            "default": 15
                        }
                    },
                    "required": ["newsgroup_pattern"]
                }
            }
        }


class SummarizeCommunityTool(LLMTool):
    """Tool for generating community activity summaries."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, newsgroup_pattern: str, period_days: int = 7,
            max_messages: int = 200, max_groups: int = 15,
            community_name: Optional[str] = None, format_style: str = "detailed",
            min_importance: float = 0.3) -> Dict[str, Any]:
        """Generate an intelligent community activity summary for newsgroups."""
        return self.service.summarize_community(
            newsgroup_pattern, period_days, max_messages, max_groups,
            community_name, format_style, min_importance
        )

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "summarize_community",
                "description": "Generate an intelligent AI-powered summary of community activity in newsgroups, including trending topics, announcements, and discussion analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "newsgroup_pattern": {
                            "type": "string",
                            "description": "Newsgroup name or pattern to summarize (e.g., '*.amiga.*', 'comp.sys.amiga.misc')"
                        },
                        "period_days": {
                            "type": "integer",
                            "description": "Time period in days to analyze (7=week, 30=month)",
                            "default": 7
                        },
                        "max_messages": {
                            "type": "integer",
                            "description": "Maximum number of recent messages to analyze",
                            "default": 200
                        },
                        "max_groups": {
                            "type": "integer",
                            "description": "Maximum number of groups when using patterns",
                            "default": 15
                        },
                        "community_name": {
                            "type": "string",
                            "description": "Custom community name for the summary (auto-detected if not provided)"
                        },
                        "format_style": {
                            "type": "string",
                            "description": "Summary format style",
                            "enum": ["detailed", "brief", "highlights"],
                            "default": "detailed"
                        },
                        "min_importance": {
                            "type": "number",
                            "description": "Minimum importance score to include messages (0.0-1.0)",
                            "default": 0.3
                        }
                    },
                    "required": ["newsgroup_pattern"]
                }
            }
        }


def get_all_tools() -> List[LLMTool]:
    """Get all available UseNet client tools."""
    return [
        SetupProviderTool(),
        ListNewsgroupsTool(),
        UpdateCacheTool(),
        GetCacheInfoTool(),
        SearchMessagesTool(),
        ListMessagesTool(),
        SummarizeCommunityTool(),
    ]