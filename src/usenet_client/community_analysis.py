"""Community analysis and summarization functionality."""

from typing import List, Dict, Any, Optional
from .llm_search import LLMSearchEngine


class CommunityAnalyzer:
    """Analyze newsgroup community activity and generate summaries."""

    def __init__(self, search_engine: Optional[LLMSearchEngine] = None):
        """Initialize community analyzer with search engine."""
        self.search_engine = search_engine or LLMSearchEngine()

    def analyze_messages(
        self,
        messages: List[Dict[str, Any]],
        time_period: str = "this week",
        community_name: str = "community"
    ) -> Dict[str, Any]:
        """
        Analyze a collection of messages for community insights.

        Args:
            messages: List of message dictionaries
            time_period: Time period description (e.g., "this week")
            community_name: Name of the community being analyzed

        Returns:
            Dict with comprehensive analysis results
        """
        if not messages:
            return {
                'summary_title': f"{community_name.title()} Community Activity - {time_period.title()}",
                'overview': f"No activity found in the {community_name} during {time_period}.",
                'key_highlights': "• No messages found\n• Community appears inactive",
                'trending_section': f"No trending topics found in {time_period}.",
                'announcements_section': "No announcements during this period.",
                'community_pulse': f"The {community_name} appears to be quiet during {time_period}.",
                'classified_messages': [],
                'message_count': 0
            }

        # Step 1: Classify all messages
        classified_messages = []
        for msg in messages:
            classification = self.search_engine.classify_message(msg)
            enhanced_msg = msg.copy()
            enhanced_msg['classification'] = classification
            classified_messages.append(enhanced_msg)

        # Step 2: Analyze trends and topics
        trend_analysis = self.search_engine.analyze_community_trends(
            classified_messages, time_period, community_name
        )

        # Step 3: Generate comprehensive summary
        summary = self.search_engine.generate_community_summary(
            trend_analysis, len(messages), time_period, community_name
        )

        # Add detailed analysis data
        summary['classified_messages'] = classified_messages
        summary['trend_analysis'] = trend_analysis
        summary['message_count'] = len(messages)

        return summary

    def get_announcements(self, classified_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract announcement messages from classified messages."""
        announcements = []
        for msg in classified_messages:
            if msg.get('classification', {}).get('is_announcement', False):
                announcements.append(msg)

        # Sort by importance score
        announcements.sort(
            key=lambda x: x.get('classification', {}).get('importance_score', 0),
            reverse=True
        )
        return announcements

    def get_discussion_stats(self, classified_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate discussion statistics from classified messages."""
        if not classified_messages:
            return {
                'total_messages': 0,
                'announcements': 0,
                'discussions': 0,
                'questions': 0,
                'technical': 0,
                'social': 0,
                'groups': {}
            }

        stats = {
            'total_messages': len(classified_messages),
            'announcements': 0,
            'discussions': 0,
            'questions': 0,
            'technical': 0,
            'social': 0,
            'commercial': 0,
            'groups': {}
        }

        for msg in classified_messages:
            classification = msg.get('classification', {})
            msg_type = classification.get('message_type', 'discussion').lower()
            group = msg.get('newsgroup', 'unknown')

            # Count message types
            if msg_type == 'announcement':
                stats['announcements'] += 1
            elif msg_type == 'question':
                stats['questions'] += 1
            elif msg_type == 'technical':
                stats['technical'] += 1
            elif msg_type == 'social':
                stats['social'] += 1
            elif msg_type == 'commercial':
                stats['commercial'] += 1
            else:
                stats['discussions'] += 1

            # Count by group
            if group not in stats['groups']:
                stats['groups'][group] = 0
            stats['groups'][group] += 1

        return stats

    def filter_by_importance(
        self,
        classified_messages: List[Dict[str, Any]],
        min_importance: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Filter messages by importance score."""
        important_messages = []
        for msg in classified_messages:
            importance = msg.get('classification', {}).get('importance_score', 0.0)
            if importance >= min_importance:
                important_messages.append(msg)

        # Sort by importance
        important_messages.sort(
            key=lambda x: x.get('classification', {}).get('importance_score', 0),
            reverse=True
        )
        return important_messages