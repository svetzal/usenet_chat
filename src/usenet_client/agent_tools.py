"""Agent tools for the UseNet client.

This module provides LLMTool implementations that expo        result = self.service.list_newsgroups(pattern, max_results, all_groups, use_cache)

        # Add intelligent hints for the LLM about potentially more results
        if result.get('success'):
            total_found = result.get('total_count', 0)
            was_limited = result.get('limited', False)

            if was_limited and total_found >= max_results:
                result['hint_more_available'] = (
                    f"⚠️ Found exactly {total_found} groups (the max requested). "
                    f"There are likely MORE groups available. Consider using max_results={max_results * 2} "
                    f"or max_results=100 to see more, or use all_groups=true to see ALL matching groups."
                )
                result['ai_guidance'] = "MORE_RESULTS_LIKELY"
            else:
                result['ai_guidance'] = "COMPLETE_RESULTS"

            # Add user-friendly summary
            cache_status = "from cache" if result.get('used_cache') else "from server"
            pattern_text = f" matching '{pattern}'" if pattern else ""
            result['summary'] = f"Found {total_found} newsgroups{pattern_text} ({cache_status})"

        return resultnt functionality
to the mojentic conversational agent framework.
"""

from typing import List, Dict, Any, Optional
from mojentic.llm.tools.llm_tool import LLMTool

from .usenet_service import UseNetService


class SetupProviderTool(LLMTool):
    """Tool for configuring NNTP provider settings."""

    def __init__(self):
        self.service = UseNetService()

    def run(self, **kwargs) -> Dict[str, Any]:
        """Configure NNTP provider settings."""
        host = kwargs.get('host')
        if not host:
            return {"success": False, "error": "Host parameter is required"}

        port = kwargs.get('port', 119)
        username = kwargs.get('username')
        password = kwargs.get('password')
        use_ssl = kwargs.get('use_ssl', False)

        # Convert types (LLM may pass strings)
        port = int(port) if isinstance(port, str) else port
        use_ssl = bool(use_ssl) if isinstance(use_ssl, str) else use_ssl

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

    def run(self, **kwargs) -> Dict[str, Any]:
        """List available newsgroups, optionally filtered by pattern."""
        # Extract and validate parameters
        pattern = kwargs.get('pattern')
        max_results = kwargs.get('max_results', 25)  # Increased default from 10 to 25
        all_groups = kwargs.get('all_groups', False)
        use_cache = kwargs.get('use_cache', True)

        # Convert string parameters to proper types (LLM may pass strings)
        max_results = int(max_results) if isinstance(max_results, str) else max_results
        all_groups = bool(all_groups) if isinstance(all_groups, str) else all_groups
        use_cache = bool(use_cache) if isinstance(use_cache, str) else use_cache

        result = self.service.list_newsgroups(pattern, max_results, all_groups, use_cache)

        # Add intelligent hints for the LLM about potentially more results
        if result.get('success'):
            total_found = result.get('total_count', 0)
            was_limited = result.get('limited', False)

            if was_limited:
                result['hint_more_available'] = (
                    f"⚠️ Found exactly {total_found} groups (the max requested). "
                    f"There are likely MORE groups available. Consider using max_results={max_results * 2} "
                    f"or max_results=100 to see more, or use all_groups=true to see ALL matching groups."
                )
                result['ai_guidance'] = "MORE_RESULTS_LIKELY"
            else:
                result['ai_guidance'] = "COMPLETE_RESULTS"

            # Add user-friendly summary
            cache_status = "from cache" if result.get('used_cache') else "from server"
            pattern_text = f" matching '{pattern}'" if pattern else ""
            result['summary'] = f"Found {total_found} newsgroups{pattern_text} ({cache_status})"

        return result

    @property
    def descriptor(self):
        return {
            "type": "function",
            "function": {
                "name": "list_newsgroups",
                "description": "List available newsgroups from the NNTP server, with optional filtering by pattern. IMPORTANT: The default max_results is 25. If you get exactly 25 results, there are likely more groups available - increase max_results or use all_groups=true to see all matching groups. Always check the 'hint_more_available' field in the response for guidance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to filter newsgroups (e.g., 'amiga', 'comp.sys'). Case-insensitive substring match."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of groups to return (default: 25). Use higher values like 50-100 for comprehensive searches. If you get exactly the max_results number back, there are probably more groups available.",
                            "default": 25
                        },
                        "all_groups": {
                            "type": "boolean",
                            "description": "Return ALL matching groups (ignores max_results limit). Use this when the user wants a comprehensive list or when you get exactly max_results back indicating more are available.",
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

    def run(self, **kwargs) -> Dict[str, Any]:
        """Update the cached list of newsgroups from the NNTP server."""
        force = kwargs.get('force', False)
        force = bool(force) if isinstance(force, str) else force

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

    def run(self, **kwargs) -> Dict[str, Any]:
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

    def run(self, **kwargs) -> Dict[str, Any]:
        """Search for messages in newsgroups by poster, topic, or other criteria."""
        newsgroup = kwargs.get('newsgroup')
        if not newsgroup:
            return {"success": False, "error": "Newsgroup parameter is required"}

        poster = kwargs.get('poster')
        topic = kwargs.get('topic')
        since_days = kwargs.get('since_days', 7)
        max_messages = kwargs.get('max_messages', 100)
        use_llm = kwargs.get('use_llm', True)
        confidence = kwargs.get('confidence', 0.5)
        relevance = kwargs.get('relevance', 0.5)
        multi_group = kwargs.get('multi_group', False)
        max_groups = kwargs.get('max_groups', 20)
        with_body = kwargs.get('with_body', False)

        # Convert types
        since_days = int(since_days) if isinstance(since_days, str) else since_days
        max_messages = int(max_messages) if isinstance(max_messages, str) else max_messages
        use_llm = bool(use_llm) if isinstance(use_llm, str) else use_llm
        confidence = float(confidence) if isinstance(confidence, str) else confidence
        relevance = float(relevance) if isinstance(relevance, str) else relevance
        multi_group = bool(multi_group) if isinstance(multi_group, str) else multi_group
        max_groups = int(max_groups) if isinstance(max_groups, str) else max_groups
        with_body = bool(with_body) if isinstance(with_body, str) else with_body

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

    def run(self, **kwargs) -> Dict[str, Any]:
        """List recent message headers for data verification and exploration."""
        newsgroup_pattern = kwargs.get('newsgroup_pattern')
        if not newsgroup_pattern:
            return {"success": False, "error": "Newsgroup pattern parameter is required"}

        period_days = kwargs.get('period_days', 7)
        max_messages = kwargs.get('max_messages', 100)
        max_groups = kwargs.get('max_groups', 15)

        # Convert types
        period_days = int(period_days) if isinstance(period_days, str) else period_days
        max_messages = int(max_messages) if isinstance(max_messages, str) else max_messages
        max_groups = int(max_groups) if isinstance(max_groups, str) else max_groups

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

    def run(self, **kwargs) -> Dict[str, Any]:
        """Generate an intelligent community activity summary for newsgroups."""
        newsgroup_pattern = kwargs.get('newsgroup_pattern')
        if not newsgroup_pattern:
            return {"success": False, "error": "Newsgroup pattern parameter is required"}

        period_days = kwargs.get('period_days', 7)
        max_messages = kwargs.get('max_messages', 200)
        max_groups = kwargs.get('max_groups', 15)
        community_name = kwargs.get('community_name')
        format_style = kwargs.get('format_style', "detailed")
        min_importance = kwargs.get('min_importance', 0.3)

        # Convert types
        period_days = int(period_days) if isinstance(period_days, str) else period_days
        max_messages = int(max_messages) if isinstance(max_messages, str) else max_messages
        max_groups = int(max_groups) if isinstance(max_groups, str) else max_groups
        min_importance = float(min_importance) if isinstance(min_importance, str) else min_importance

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