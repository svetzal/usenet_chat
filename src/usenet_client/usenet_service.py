"""Service layer for UseNet client operations.

This module provides a clean interface for UseNet operations that can be used
by both CLI commands and agent tools, separating business logic from presentation.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import fnmatch

from .nntp_client import NNTPClient
from .config import Config
from .llm_search import LLMSearchEngine
from .community_analysis import CommunityAnalyzer


class UseNetService:
    """Service layer for UseNet client operations."""

    def __init__(self):
        self.config = Config()
        self.search_engine = LLMSearchEngine()
        self.analyzer = CommunityAnalyzer()

    def is_configured(self) -> bool:
        """Check if NNTP provider is configured."""
        return self.config.load_provider_config() is not None

    def setup_provider(self, host: str, port: int = 119, username: Optional[str] = None,
                      password: Optional[str] = None, use_ssl: bool = False) -> Dict[str, Any]:
        """Configure NNTP provider settings."""
        self.config.save_provider_config(host, port, username, password, use_ssl)
        return {
            "success": True,
            "message": f"NNTP provider configured: {host}:{port}",
            "host": host,
            "port": port,
            "username": username,
            "use_ssl": use_ssl
        }

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the newsgroups cache."""
        cache_info = self.config.get_cache_info()
        if not cache_info:
            return {
                "exists": False,
                "message": "No cache found"
            }

        cache_time = datetime.fromtimestamp(cache_info['timestamp'])
        return {
            "exists": True,
            "status": "expired" if cache_info['is_expired'] else "fresh",
            "created": cache_time.isoformat(),
            "age_hours": cache_info['age_hours'],
            "group_count": cache_info['group_count'],
            "is_expired": cache_info['is_expired']
        }

    def update_cache(self, force: bool = False) -> Dict[str, Any]:
        """Update the newsgroups cache from the NNTP server."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "NNTP provider not configured"
            }

        # Check current cache status
        cache_info = self.config.get_cache_info()
        if cache_info and not force and not cache_info['is_expired']:
            return {
                "success": False,
                "skipped": True,
                "message": f"Cache is recent ({cache_info['age_hours']:.1f} hours old, {cache_info['group_count']} groups)",
                "cache_info": self.get_cache_info()
            }

        try:
            provider_config = self.config.load_provider_config()
            if not provider_config:
                return {
                    "success": False,
                    "error": "Provider configuration not found"
                }
            client = NNTPClient(provider_config)
            groups = client.list_all_newsgroups()
            self.config.save_newsgroups_cache(groups)

            return {
                "success": True,
                "message": f"Cache updated with {len(groups)} newsgroups",
                "group_count": len(groups)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_newsgroups(self, pattern: Optional[str] = None, max_results: int = 100,
                       all_groups: bool = False, use_cache: bool = True,
                       page_size: int = 1000) -> Dict[str, Any]:
        """List available newsgroups."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "NNTP provider not configured"
            }

        groups = None
        used_cache = False

        # Try to load from cache first
        if use_cache:
            cached_groups = self.config.load_newsgroups_cache()
            if cached_groups:
                used_cache = True

                # Filter cached results
                if pattern:
                    groups = [
                        (name, last, first, flag)
                        for name, last, first, flag in cached_groups
                        if pattern.lower() in name.lower()
                    ]
                else:
                    groups = cached_groups

                # Limit results if not showing all
                if not all_groups and len(groups) > max_results:
                    groups = groups[:max_results]

        # If no cache or cache failed, fetch from server
        if groups is None:
            try:
                provider_config = self.config.load_provider_config()
                if not provider_config:
                    return {
                        "success": False,
                        "error": "Provider configuration not found"
                    }
                client = NNTPClient(provider_config)

                if all_groups:
                    groups = client.list_all_newsgroups(pattern, page_size)
                else:
                    groups = client.list_newsgroups(pattern, max_results)

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        # Convert to list of dicts for easier consumption
        group_list = []
        for name, last, first, flag in groups:
            group_list.append({
                "name": name,
                "last_article": last,
                "first_article": first,
                "status": flag
            })

        cache_info = self.get_cache_info()

        return {
            "success": True,
            "groups": group_list,
            "total_count": len(group_list),
            "used_cache": used_cache,
            "cache_info": cache_info,
            "pattern": pattern,
            "limited": not all_groups and len(group_list) >= max_results
        }

    def search_messages(self, newsgroup: str, poster: Optional[str] = None, topic: Optional[str] = None,
                       since_days: int = 7, max_messages: int = 100, use_llm: bool = True,
                       confidence: float = 0.5, relevance: float = 0.5,
                       multi_group: bool = False, max_groups: int = 20,
                       with_body: bool = False) -> Dict[str, Any]:
        """Search for messages in newsgroups."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "NNTP provider not configured"
            }

        try:
            provider_config = self.config.load_provider_config()
            if not provider_config:
                return {
                    "success": False,
                    "error": "Provider configuration not found"
                }
            client = NNTPClient(provider_config)

            # Check if this is a multi-group search
            is_multi_group = multi_group or ('*' in newsgroup or '?' in newsgroup)

            if is_multi_group:
                # Multi-group search
                cached_groups = self.config.load_newsgroups_cache()

                all_results = client.search_multiple_groups(
                    group_pattern=newsgroup,
                    poster=poster,
                    topic=topic,
                    max_messages_per_group=max_messages // max_groups if max_groups > 0 else 50,
                    since_days=since_days,
                    max_groups=max_groups,
                    cached_groups=cached_groups
                )

                if not all_results:
                    return {
                        "success": True,
                        "messages": [],
                        "total_count": 0,
                        "is_multi_group": True,
                        "pattern": newsgroup
                    }

                # Flatten results for processing
                messages = []
                for group_name, group_messages in all_results.items():
                    for msg in group_messages:
                        msg['newsgroup'] = group_name
                        messages.append(msg)

                # Sort by date (newest first)
                messages.sort(key=lambda x: x.get('parsed_date') or datetime.min, reverse=True)

            else:
                # Single group search
                messages = client.get_message_headers(newsgroup, max_messages, since_days)

                if not messages:
                    return {
                        "success": True,
                        "messages": [],
                        "total_count": 0,
                        "is_multi_group": False,
                        "newsgroup": newsgroup
                    }

                # Add newsgroup to each message
                for msg in messages:
                    msg['newsgroup'] = newsgroup

            # Filter by poster if specified (for single-group searches)
            if poster and not is_multi_group:
                if use_llm:
                    messages = self.search_engine.filter_messages_by_poster(
                        messages, poster, min_confidence=confidence
                    )
                else:
                    # Simple string matching
                    poster_lower = poster.lower()
                    messages = [
                        msg for msg in messages
                        if poster_lower in msg.get('from', '').lower()
                    ]

            # Filter by topic if specified
            if topic:
                if with_body and not is_multi_group:
                    # Retrieve bodies for top candidates
                    max_bodies = min(20, len(messages))
                    messages = client.get_message_bodies_for_headers(
                        newsgroup, messages[:max_bodies], max_bodies
                    ) + messages[max_bodies:]

                if use_llm:
                    if with_body and not is_multi_group:
                        messages = self.search_engine.filter_messages_by_topic_with_bodies(
                            messages, topic, min_relevance=relevance, min_confidence=confidence, use_body=True
                        )
                    else:
                        messages = self.search_engine.filter_messages_by_topic(
                            messages, topic, min_relevance=relevance, min_confidence=confidence
                        )
                else:
                    # Simple keyword matching
                    topic_words = topic.lower().split()
                    filtered = []
                    for msg in messages:
                        subject = msg.get('subject', '').lower()
                        body = msg.get('body', '').lower() if with_body else ''
                        text = subject + ' ' + body
                        matches = sum(1 for word in topic_words if word in text)
                        if matches > 0:
                            filtered.append(msg)
                    messages = filtered

            # Prepare analysis summaries
            analysis_summary = {}
            if use_llm and poster and not is_multi_group and messages:
                if 'llm_analysis' in messages[0]:
                    reasons = {}
                    for msg in messages[:5]:
                        reason = msg['llm_analysis']['match_reason']
                        reasons[reason] = reasons.get(reason, 0) + 1
                    analysis_summary['poster_analysis'] = reasons

            if use_llm and topic and not is_multi_group and messages:
                if 'topic_analysis' in messages[0]:
                    indicators = {}
                    used_body_count = 0
                    for msg in messages[:5]:
                        indicator = msg['topic_analysis']['key_indicators']
                        indicators[indicator] = indicators.get(indicator, 0) + 1
                        if msg['topic_analysis'].get('used_body', False):
                            used_body_count += 1

                    avg_relevance = sum(msg['topic_analysis']['topic_relevance'] for msg in messages) / len(messages)
                    analysis_summary['topic_analysis'] = {
                        'indicators': indicators,
                        'average_relevance': avg_relevance,
                        'used_body_count': used_body_count
                    }

            # Group summary for multi-group searches
            group_summary = {}
            if is_multi_group and messages:
                for msg in messages:
                    group = msg.get('newsgroup', 'Unknown')
                    group_summary[group] = group_summary.get(group, 0) + 1

            return {
                "success": True,
                "messages": messages,
                "total_count": len(messages),
                "is_multi_group": is_multi_group,
                "newsgroup": newsgroup if not is_multi_group else None,
                "pattern": newsgroup if is_multi_group else None,
                "search_params": {
                    "poster": poster,
                    "topic": topic,
                    "since_days": since_days,
                    "use_llm": use_llm,
                    "confidence": confidence,
                    "relevance": relevance,
                    "with_body": with_body
                },
                "analysis_summary": analysis_summary,
                "group_summary": group_summary,
                "llm_available": self.search_engine.available
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_messages(self, newsgroup_pattern: str, period_days: int = 7,
                     max_messages: int = 100, max_groups: int = 15) -> Dict[str, Any]:
        """List recent message headers for data verification."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "NNTP provider not configured"
            }

        try:
            provider_config = self.config.load_provider_config()
            if not provider_config:
                return {
                    "success": False,
                    "error": "Provider configuration not found"
                }
            client = NNTPClient(provider_config)

            # Check if this is a multi-group pattern
            is_multi_group = '*' in newsgroup_pattern or '?' in newsgroup_pattern

            if is_multi_group:
                # Multi-group listing
                cached_groups = self.config.load_newsgroups_cache()

                # Use time-scaling logic
                base_messages_per_group = max(50, max_messages // max(max_groups, 4))
                time_multiplier = max(1.0, period_days / 7.0)
                messages_per_group = int(base_messages_per_group * time_multiplier)
                messages_per_group = min(messages_per_group, 500)

                all_results = client.search_multiple_groups(
                    group_pattern=newsgroup_pattern,
                    max_messages_per_group=messages_per_group,
                    since_days=period_days,
                    max_groups=max_groups,
                    cached_groups=cached_groups
                )

                if not all_results:
                    return {
                        "success": True,
                        "messages": [],
                        "total_count": 0,
                        "is_multi_group": True,
                        "pattern": newsgroup_pattern,
                        "period_days": period_days
                    }

                # Flatten results
                messages = []
                for group_name, group_messages in all_results.items():
                    for msg in group_messages:
                        msg['newsgroup'] = group_name
                        messages.append(msg)

            else:
                # Single group listing
                time_multiplier = max(1.0, period_days / 7.0)
                scaled_max_messages = int(max_messages * time_multiplier)
                scaled_max_messages = min(scaled_max_messages, 1000)

                messages = client.get_message_headers(newsgroup_pattern, scaled_max_messages, period_days)

                # Add newsgroup to each message
                for msg in messages:
                    msg['newsgroup'] = newsgroup_pattern

            # Sort messages by date (newest first)
            messages.sort(key=lambda x: x.get('parsed_date') or datetime.min, reverse=True)

            # Limit to max_messages for display
            display_messages = messages[:max_messages]

            # Generate group statistics for multi-group results
            group_stats = {}
            if is_multi_group:
                for msg in messages:
                    group = msg.get('newsgroup', 'Unknown')
                    group_stats[group] = group_stats.get(group, 0) + 1

            return {
                "success": True,
                "messages": display_messages,
                "total_count": len(messages),
                "displayed_count": len(display_messages),
                "is_multi_group": is_multi_group,
                "newsgroup": newsgroup_pattern if not is_multi_group else None,
                "pattern": newsgroup_pattern if is_multi_group else None,
                "period_days": period_days,
                "group_stats": group_stats
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def summarize_community(self, newsgroup_pattern: str, period_days: int = 7,
                           max_messages: int = 200, max_groups: int = 15,
                           community_name: Optional[str] = None, format_style: str = "detailed",
                           min_importance: float = 0.3) -> Dict[str, Any]:
        """Generate an intelligent community activity summary."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "NNTP provider not configured"
            }

        # Auto-detect community name from pattern
        if not community_name:
            if "amiga" in newsgroup_pattern.lower():
                community_name = "Amiga community"
            elif "comp.sys" in newsgroup_pattern.lower():
                community_name = "Computer systems community"
            else:
                community_name = f"{newsgroup_pattern} community"

        try:
            provider_config = self.config.load_provider_config()
            if not provider_config:
                return {
                    "success": False,
                    "error": "Provider configuration not found"
                }
            client = NNTPClient(provider_config)

            # Generate period description
            if period_days == 7:
                period_description = "this week"
            elif period_days == 30:
                period_description = "this month"
            else:
                period_description = f"the last {period_days} days"

            # Check if this is a multi-group pattern
            is_multi_group = '*' in newsgroup_pattern or '?' in newsgroup_pattern

            if is_multi_group:
                # Multi-group analysis
                cached_groups = self.config.load_newsgroups_cache()

                # Calculate messages per group with time scaling
                base_messages_per_group = max(50, max_messages // max(max_groups, 4))
                time_multiplier = max(1.0, period_days / 7.0)
                messages_per_group = int(base_messages_per_group * time_multiplier)
                messages_per_group = min(messages_per_group, 500)

                all_results = client.search_multiple_groups(
                    group_pattern=newsgroup_pattern,
                    max_messages_per_group=messages_per_group,
                    since_days=period_days,
                    max_groups=max_groups,
                    cached_groups=cached_groups
                )

                if not all_results:
                    return {
                        "success": True,
                        "summary": f"No recent activity found in {community_name} over {period_description}",
                        "messages_analyzed": 0,
                        "groups_analyzed": 0,
                        "is_multi_group": True
                    }

                # Flatten results
                all_messages = []
                for group_name, messages in all_results.items():
                    for msg in messages:
                        msg['newsgroup'] = group_name
                        all_messages.append(msg)

            else:
                # Single group analysis
                time_multiplier = max(1.0, period_days / 7.0)
                scaled_max_messages = int(max_messages * time_multiplier)
                scaled_max_messages = min(scaled_max_messages, 1000)

                all_messages = client.get_message_headers(newsgroup_pattern, scaled_max_messages, period_days)

                # Add newsgroup to each message
                for msg in all_messages:
                    msg['newsgroup'] = newsgroup_pattern

                if not all_messages:
                    return {
                        "success": True,
                        "summary": f"No recent activity found in {community_name} over {period_description}",
                        "messages_analyzed": 0,
                        "groups_analyzed": 1 if not is_multi_group else 0,
                        "is_multi_group": False
                    }

            # Analyze messages for community insights
            summary = self.analyzer.analyze_messages(
                all_messages,
                time_period=period_description,
                community_name=community_name
            )

            # Filter by importance if requested
            important_messages = []
            if min_importance > 0.0:
                important_messages = self.analyzer.filter_by_importance(
                    summary['classified_messages'], min_importance
                )

            # Get additional statistics
            announcements = self.analyzer.get_announcements(summary['classified_messages'])
            stats = self.analyzer.get_discussion_stats(summary['classified_messages'])

            return {
                "success": True,
                "summary": summary,
                "important_messages": important_messages,
                "announcements": announcements[:5],  # Top 5 announcements
                "stats": stats,
                "messages_analyzed": len(all_messages),
                "groups_analyzed": len(all_results) if is_multi_group and 'all_results' in locals() else 1,
                "is_multi_group": is_multi_group,
                "period_description": period_description,
                "community_name": community_name,
                "min_importance": min_importance,
                "format_style": format_style
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }