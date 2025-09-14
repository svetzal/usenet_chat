"""LLM-powered search functionality using DSPy."""

from typing import List, Dict, Any, Optional
import dspy


class PosterMatcher(dspy.Signature):
    """Determine if a message poster matches a search query."""

    search_query: str = dspy.InputField(desc="The poster name or company being searched for")
    message_from: str = dspy.InputField(desc="The 'From' field of the newsgroup message")

    is_match: bool = dspy.OutputField(desc="True if the message is from the searched poster")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")
    reason: str = dspy.OutputField(desc="Brief explanation of the matching decision")


class ContentRelevance(dspy.Signature):
    """Assess if message content is relevant to a topic search."""

    topic_query: str = dspy.InputField(desc="The topic or theme being searched for")
    message_subject: str = dspy.InputField(desc="The subject line of the message")
    message_from: str = dspy.InputField(desc="The sender of the message")

    relevance_score: float = dspy.OutputField(desc="Relevance score between 0.0 and 1.0")
    is_relevant: bool = dspy.OutputField(desc="True if the message is relevant to the topic")
    reason: str = dspy.OutputField(desc="Brief explanation of the relevance assessment")


class TopicMatcher(dspy.Signature):
    """Advanced topic matching for newsgroup messages with context awareness."""

    topic_query: str = dspy.InputField(desc="The topic, product, or concept being searched for (e.g., 'z3660 accelerator', 'Amiga 1200')")
    message_subject: str = dspy.InputField(desc="The subject line of the message")
    message_from: str = dspy.InputField(desc="The sender of the message")
    newsgroup_name: str = dspy.InputField(desc="The newsgroup where this message was posted")

    topic_relevance: float = dspy.OutputField(desc="Topic relevance score between 0.0 and 1.0")
    is_topic_match: bool = dspy.OutputField(desc="True if the message is clearly about the searched topic")
    confidence: float = dspy.OutputField(desc="Confidence in the assessment between 0.0 and 1.0")
    key_indicators: str = dspy.OutputField(desc="Key words or phrases that indicate topic relevance")
    context_notes: str = dspy.OutputField(desc="Additional context about why this message matches or doesn't match")


class TopicMatcherWithBody(dspy.Signature):
    """Advanced topic matching using message body content for deeper analysis."""

    topic_query: str = dspy.InputField(desc="The topic, product, or concept being searched for (e.g., 'z3660 accelerator', 'Amiga 1200')")
    message_subject: str = dspy.InputField(desc="The subject line of the message")
    message_body: str = dspy.InputField(desc="The body content of the message (first 500 chars)")
    message_from: str = dspy.InputField(desc="The sender of the message")
    newsgroup_name: str = dspy.InputField(desc="The newsgroup where this message was posted")

    topic_relevance: float = dspy.OutputField(desc="Topic relevance score between 0.0 and 1.0")
    is_topic_match: bool = dspy.OutputField(desc="True if the message is clearly about the searched topic")
    confidence: float = dspy.OutputField(desc="Confidence in the assessment between 0.0 and 1.0")
    key_indicators: str = dspy.OutputField(desc="Key words or phrases from subject or body that indicate topic relevance")
    context_notes: str = dspy.OutputField(desc="Additional context about why this message matches or doesn't match")


class MessageClassifier(dspy.Signature):
    """Classify newsgroup messages by type and importance for community analysis."""

    message_subject: str = dspy.InputField(desc="The subject line of the message")
    message_from: str = dspy.InputField(desc="The sender of the message")
    newsgroup_name: str = dspy.InputField(desc="The newsgroup where this message was posted")
    message_body: str = dspy.InputField(desc="The message body content (first 300 chars)", optional=True)

    message_type: str = dspy.OutputField(desc="Category: announcement, question, discussion, technical, commercial, social")
    importance_score: float = dspy.OutputField(desc="Importance score between 0.0 and 1.0 for community relevance")
    is_announcement: bool = dspy.OutputField(desc="True if this is a significant announcement (release, event, news)")
    key_topics: str = dspy.OutputField(desc="Main topics or themes discussed (comma-separated)")
    summary: str = dspy.OutputField(desc="Brief 1-sentence summary of the message content")


class TopicClusterer(dspy.Signature):
    """Identify and cluster related topics from multiple messages for trend analysis."""

    message_summaries: str = dspy.InputField(desc="List of message summaries and topics, one per line")
    time_period: str = dspy.InputField(desc="Time period being analyzed (e.g., 'last week', 'last month')")
    community_name: str = dspy.InputField(desc="Community or newsgroup context (e.g., 'Amiga community')")

    trending_topics: str = dspy.OutputField(desc="Top 3-5 trending topics with activity levels (format: 'Topic: Activity Level')")
    emerging_themes: str = dspy.OutputField(desc="New or emerging themes not seen in previous periods")
    discussion_types: str = dspy.OutputField(desc="Types of discussions: technical, social, commercial ratios")
    notable_announcements: str = dspy.OutputField(desc="Key announcements or significant events mentioned")


class CommunitySummarizer(dspy.Signature):
    """Generate engaging community activity summaries from analyzed message data."""

    trending_topics: str = dspy.InputField(desc="Top trending topics with activity levels")
    announcements: str = dspy.InputField(desc="Key announcements and significant events")
    discussion_stats: str = dspy.InputField(desc="Discussion statistics and types")
    time_period: str = dspy.InputField(desc="Time period analyzed (e.g., 'this week')")
    community_name: str = dspy.InputField(desc="Community name (e.g., 'Amiga community')")
    message_count: int = dspy.InputField(desc="Total number of messages analyzed")

    summary_title: str = dspy.OutputField(desc="Engaging title for the community summary")
    overview: str = dspy.OutputField(desc="2-3 sentence overview of community activity")
    key_highlights: str = dspy.OutputField(desc="3-5 bullet points of key highlights and notable discussions")
    trending_section: str = dspy.OutputField(desc="Paragraph about trending topics and popular discussions")
    announcements_section: str = dspy.OutputField(desc="Section highlighting important announcements and news")
    community_pulse: str = dspy.OutputField(desc="Brief assessment of community engagement and mood")


class LLMSearchEngine:
    """LLM-powered search engine for newsgroup messages."""

    def __init__(self, model_name: str = "ollama/qwen2.5:14b"):
        """Initialize the search engine with a language model."""
        try:
            # Configure LLM with JSON mode preference for Ollama compatibility
            self.lm = dspy.LM(
                model_name,
                api_base="http://localhost:11434",
                max_tokens=1000,
                temperature=0.1
            )
            dspy.configure(lm=self.lm)

            # Search and filtering capabilities
            self.poster_matcher = dspy.Predict(PosterMatcher)
            self.content_assessor = dspy.Predict(ContentRelevance)
            self.topic_matcher = dspy.Predict(TopicMatcher)
            self.topic_matcher_with_body = dspy.Predict(TopicMatcherWithBody)

            # Community analysis capabilities
            self.message_classifier = dspy.Predict(MessageClassifier)
            self.topic_clusterer = dspy.Predict(TopicClusterer)
            self.community_summarizer = dspy.Predict(CommunitySummarizer)

            self.available = True
            print("✅ LLM initialized successfully with Ollama")
        except Exception as e:
            # If LLM setup fails, disable LLM features
            print(f"Warning: LLM setup failed ({e}), falling back to simple matching")
            self.available = False

    def match_poster(self, search_query: str, message_from: str) -> Dict[str, Any]:
        """
        Use LLM to determine if a message is from the searched poster.

        Args:
            search_query: The poster name/company being searched for
            message_from: The 'From' field of the message

        Returns:
            Dict with keys: is_match, confidence, reason
        """
        if not self.available:
            # Fallback to simple string matching
            return {
                'is_match': search_query.lower() in message_from.lower(),
                'confidence': 0.5,
                'reason': 'Simple string matching (LLM unavailable)'
            }

        try:
            # Suppress DSPy warnings about structured output fallback
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")
                result = self.poster_matcher(
                    search_query=search_query,
                    message_from=message_from
                )

            return {
                'is_match': result.is_match,
                'confidence': result.confidence,
                'reason': result.reason
            }
        except Exception:
            # Fallback on error
            return {
                'is_match': search_query.lower() in message_from.lower(),
                'confidence': 0.3,
                'reason': 'Fallback matching (LLM error)'
            }

    def assess_relevance(self, topic_query: str, message_subject: str, message_from: str) -> Dict[str, Any]:
        """
        Use LLM to assess message relevance to a topic.

        Args:
            topic_query: The topic being searched for
            message_subject: Subject line of the message
            message_from: Sender of the message

        Returns:
            Dict with keys: relevance_score, is_relevant, reason
        """
        if not self.available:
            # Fallback to simple keyword matching
            topic_words = topic_query.lower().split()
            subject_lower = message_subject.lower()
            matches = sum(1 for word in topic_words if word in subject_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'relevance_score': relevance_score,
                'is_relevant': relevance_score > 0.3,
                'reason': f'Keyword matching: {matches}/{len(topic_words)} matches'
            }

        try:
            result = self.content_assessor(
                topic_query=topic_query,
                message_subject=message_subject,
                message_from=message_from
            )

            return {
                'relevance_score': result.relevance_score,
                'is_relevant': result.is_relevant,
                'reason': result.reason
            }
        except Exception:
            # Fallback on error
            topic_words = topic_query.lower().split()
            subject_lower = message_subject.lower()
            matches = sum(1 for word in topic_words if word in subject_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'relevance_score': relevance_score,
                'is_relevant': relevance_score > 0.3,
                'reason': f'Fallback matching: {matches}/{len(topic_words)} matches'
            }

    def filter_messages_by_poster(
        self,
        messages: List[Dict[str, Any]],
        poster_query: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Filter messages using LLM-powered poster matching.

        Args:
            messages: List of message dictionaries
            poster_query: Poster name/company to search for
            min_confidence: Minimum confidence threshold

        Returns:
            Filtered list of messages with added LLM analysis
        """
        filtered_messages = []

        for msg in messages:
            from_field = msg.get('from', '')
            if not from_field:
                continue

            match_result = self.match_poster(poster_query, from_field)

            if match_result['is_match'] and match_result['confidence'] >= min_confidence:
                # Add LLM analysis to message
                enhanced_msg = msg.copy()
                enhanced_msg['llm_analysis'] = {
                    'match_confidence': match_result['confidence'],
                    'match_reason': match_result['reason']
                }
                filtered_messages.append(enhanced_msg)

        # Sort by confidence (highest first)
        filtered_messages.sort(key=lambda x: x['llm_analysis']['match_confidence'], reverse=True)

        return filtered_messages

    def assess_topic_relevance(self, topic_query: str, message_subject: str, message_from: str, newsgroup_name: str) -> Dict[str, Any]:
        """
        Use LLM to assess message relevance to a specific topic.

        Args:
            topic_query: The topic being searched for
            message_subject: Subject line of the message
            message_from: Sender of the message
            newsgroup_name: Name of the newsgroup

        Returns:
            Dict with keys: topic_relevance, is_topic_match, confidence, key_indicators, context_notes
        """
        if not self.available:
            # Fallback to simple keyword matching
            topic_words = topic_query.lower().split()
            subject_lower = message_subject.lower()
            matches = sum(1 for word in topic_words if word in subject_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'topic_relevance': relevance_score,
                'is_topic_match': relevance_score > 0.3,
                'confidence': 0.5,
                'key_indicators': f'{matches}/{len(topic_words)} keyword matches',
                'context_notes': 'Simple keyword matching (LLM unavailable)'
            }

        try:
            # Suppress DSPy warnings about structured output fallback
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")
                result = self.topic_matcher(
                    topic_query=topic_query,
                    message_subject=message_subject,
                    message_from=message_from,
                    newsgroup_name=newsgroup_name
                )

            return {
                'topic_relevance': result.topic_relevance,
                'is_topic_match': result.is_topic_match,
                'confidence': result.confidence,
                'key_indicators': result.key_indicators,
                'context_notes': result.context_notes
            }
        except Exception:
            # Fallback on error
            topic_words = topic_query.lower().split()
            subject_lower = message_subject.lower()
            matches = sum(1 for word in topic_words if word in subject_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'topic_relevance': relevance_score,
                'is_topic_match': relevance_score > 0.3,
                'confidence': 0.3,
                'key_indicators': f'{matches}/{len(topic_words)} keyword matches',
                'context_notes': 'Fallback matching (LLM error)'
            }

    def filter_messages_by_topic(
        self,
        messages: List[Dict[str, Any]],
        topic_query: str,
        min_relevance: float = 0.5,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Filter messages using LLM-powered topic matching.

        Args:
            messages: List of message dictionaries
            topic_query: Topic/theme to search for
            min_relevance: Minimum relevance threshold
            min_confidence: Minimum confidence threshold

        Returns:
            Filtered list of messages with added topic analysis
        """
        filtered_messages = []

        for msg in messages:
            subject = msg.get('subject', '')
            from_field = msg.get('from', '')
            newsgroup = msg.get('newsgroup', 'unknown')

            if not subject:
                continue

            topic_result = self.assess_topic_relevance(topic_query, subject, from_field, newsgroup)

            if (topic_result['is_topic_match'] and
                topic_result['topic_relevance'] >= min_relevance and
                topic_result['confidence'] >= min_confidence):

                # Add topic analysis to message
                enhanced_msg = msg.copy()
                enhanced_msg['topic_analysis'] = {
                    'topic_relevance': topic_result['topic_relevance'],
                    'confidence': topic_result['confidence'],
                    'key_indicators': topic_result['key_indicators'],
                    'context_notes': topic_result['context_notes']
                }
                filtered_messages.append(enhanced_msg)

        # Sort by relevance score (highest first), then confidence
        filtered_messages.sort(key=lambda x: (
            x['topic_analysis']['topic_relevance'],
            x['topic_analysis']['confidence']
        ), reverse=True)

        return filtered_messages

    def assess_topic_with_body(
        self,
        topic_query: str,
        message_subject: str,
        message_body: str,
        message_from: str,
        newsgroup_name: str
    ) -> Dict[str, Any]:
        """
        Use LLM to assess message relevance using both subject and body content.

        Args:
            topic_query: The topic being searched for
            message_subject: Subject line of the message
            message_body: Body content of the message
            message_from: Sender of the message
            newsgroup_name: Name of the newsgroup

        Returns:
            Dict with keys: topic_relevance, is_topic_match, confidence, key_indicators, context_notes
        """
        if not self.available:
            # Fallback to simple keyword matching
            topic_words = topic_query.lower().split()
            text_lower = (message_subject + ' ' + message_body).lower()
            matches = sum(1 for word in topic_words if word in text_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'topic_relevance': relevance_score,
                'is_topic_match': relevance_score > 0.3,
                'confidence': 0.5,
                'key_indicators': f'{matches}/{len(topic_words)} keyword matches in subject+body',
                'context_notes': 'Simple keyword matching (LLM unavailable)'
            }

        try:
            # Truncate body to first 500 chars for LLM processing
            truncated_body = message_body[:500] if len(message_body) > 500 else message_body

            # Suppress DSPy warnings about structured output fallback
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")
                result = self.topic_matcher_with_body(
                    topic_query=topic_query,
                    message_subject=message_subject,
                    message_body=truncated_body,
                    message_from=message_from,
                    newsgroup_name=newsgroup_name
                )

            return {
                'topic_relevance': result.topic_relevance,
                'is_topic_match': result.is_topic_match,
                'confidence': result.confidence,
                'key_indicators': result.key_indicators,
                'context_notes': result.context_notes
            }
        except Exception:
            # Fallback on error
            topic_words = topic_query.lower().split()
            text_lower = (message_subject + ' ' + message_body).lower()
            matches = sum(1 for word in topic_words if word in text_lower)
            relevance_score = min(matches / len(topic_words), 1.0) if topic_words else 0.0

            return {
                'topic_relevance': relevance_score,
                'is_topic_match': relevance_score > 0.3,
                'confidence': 0.3,
                'key_indicators': f'{matches}/{len(topic_words)} keyword matches',
                'context_notes': 'Fallback matching (LLM error)'
            }

    def filter_messages_by_topic_with_bodies(
        self,
        messages: List[Dict[str, Any]],
        topic_query: str,
        min_relevance: float = 0.5,
        min_confidence: float = 0.5,
        use_body: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter messages using enhanced topic matching with optional body content.

        Args:
            messages: List of message dictionaries (may include 'body' field)
            topic_query: Topic/theme to search for
            min_relevance: Minimum relevance threshold
            min_confidence: Minimum confidence threshold
            use_body: Whether to use message body for analysis

        Returns:
            Filtered list of messages with added topic analysis
        """
        filtered_messages = []

        for msg in messages:
            subject = msg.get('subject', '')
            from_field = msg.get('from', '')
            newsgroup = msg.get('newsgroup', 'unknown')
            body = msg.get('body', '')

            if not subject:
                continue

            # Use body-aware analysis if body is available and requested
            if use_body and body:
                topic_result = self.assess_topic_with_body(
                    topic_query, subject, body, from_field, newsgroup
                )
            else:
                # Fall back to header-only analysis
                topic_result = self.assess_topic_relevance(
                    topic_query, subject, from_field, newsgroup
                )

            if (topic_result['is_topic_match'] and
                topic_result['topic_relevance'] >= min_relevance and
                topic_result['confidence'] >= min_confidence):

                # Add topic analysis to message
                enhanced_msg = msg.copy()
                enhanced_msg['topic_analysis'] = {
                    'topic_relevance': topic_result['topic_relevance'],
                    'confidence': topic_result['confidence'],
                    'key_indicators': topic_result['key_indicators'],
                    'context_notes': topic_result['context_notes'],
                    'used_body': use_body and bool(body)
                }
                filtered_messages.append(enhanced_msg)

        # Sort by relevance score (highest first), then confidence
        filtered_messages.sort(key=lambda x: (
            x['topic_analysis']['topic_relevance'],
            x['topic_analysis']['confidence']
        ), reverse=True)

        return filtered_messages

    def classify_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a message by type and importance for community analysis.

        Args:
            message: Message dictionary with subject, from, newsgroup, and optionally body

        Returns:
            Dict with classification results
        """
        if not self.available:
            # Fallback classification
            subject = message.get('subject', '').lower()
            is_announcement = any(keyword in subject for keyword in
                                ['announce', 'release', 'new', 'available', 'update'])

            return {
                'message_type': 'announcement' if is_announcement else 'discussion',
                'importance_score': 0.7 if is_announcement else 0.5,
                'is_announcement': is_announcement,
                'key_topics': 'general discussion',
                'summary': message.get('subject', 'No subject')[:100]
            }

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")

                result = self.message_classifier(
                    message_subject=message.get('subject', ''),
                    message_from=message.get('from', ''),
                    newsgroup_name=message.get('newsgroup', ''),
                    message_body=message.get('body', '')[:300] if message.get('body') else ''
                )

            return {
                'message_type': result.message_type,
                'importance_score': result.importance_score,
                'is_announcement': result.is_announcement,
                'key_topics': result.key_topics,
                'summary': result.summary
            }
        except Exception:
            # Fallback on error
            subject = message.get('subject', '').lower()
            is_announcement = any(keyword in subject for keyword in
                                ['announce', 'release', 'new', 'available', 'update'])

            return {
                'message_type': 'announcement' if is_announcement else 'discussion',
                'importance_score': 0.7 if is_announcement else 0.3,
                'is_announcement': is_announcement,
                'key_topics': 'general discussion',
                'summary': message.get('subject', 'No subject')[:100]
            }

    def analyze_community_trends(
        self,
        classified_messages: List[Dict[str, Any]],
        time_period: str = "last week",
        community_name: str = "community"
    ) -> Dict[str, Any]:
        """
        Analyze trends and topics from classified messages.

        Args:
            classified_messages: List of messages with classification data
            time_period: Time period description
            community_name: Name of the community being analyzed

        Returns:
            Dict with trend analysis results
        """
        if not classified_messages:
            return {
                'trending_topics': 'No activity found',
                'emerging_themes': 'No emerging themes',
                'discussion_types': 'No discussions',
                'notable_announcements': 'No announcements'
            }

        if not self.available:
            # Fallback analysis
            announcements = [msg for msg in classified_messages if msg.get('classification', {}).get('is_announcement')]
            topics = []
            for msg in classified_messages:
                if msg.get('classification', {}).get('key_topics'):
                    topics.extend(msg['classification']['key_topics'].split(','))

            return {
                'trending_topics': ', '.join(list(set(topics))[:3]) if topics else 'General discussions',
                'emerging_themes': 'Various community discussions',
                'discussion_types': f'Technical: {len([m for m in classified_messages if "technical" in m.get("classification", {}).get("message_type", "")])}, Social: {len(classified_messages) - len([m for m in classified_messages if "technical" in m.get("classification", {}).get("message_type", "")])}',
                'notable_announcements': f'{len(announcements)} announcements found'
            }

        try:
            # Prepare message summaries for analysis
            summaries = []
            for msg in classified_messages:
                classification = msg.get('classification', {})
                summary_line = f"{classification.get('summary', 'No summary')}, Topics: {classification.get('key_topics', 'unknown')}, Type: {classification.get('message_type', 'unknown')}"
                summaries.append(summary_line)

            message_summaries = '\n'.join(summaries[:50])  # Limit to avoid token overflow

            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")

                result = self.topic_clusterer(
                    message_summaries=message_summaries,
                    time_period=time_period,
                    community_name=community_name
                )

            return {
                'trending_topics': result.trending_topics,
                'emerging_themes': result.emerging_themes,
                'discussion_types': result.discussion_types,
                'notable_announcements': result.notable_announcements
            }
        except Exception:
            # Fallback on error
            announcements = [msg for msg in classified_messages if msg.get('classification', {}).get('is_announcement')]
            return {
                'trending_topics': 'General community discussions',
                'emerging_themes': 'Various topics of interest',
                'discussion_types': f'Mixed discussions across {len(set(msg.get("newsgroup", "unknown") for msg in classified_messages))} groups',
                'notable_announcements': f'{len(announcements)} announcements found'
            }

    def generate_community_summary(
        self,
        trend_analysis: Dict[str, Any],
        message_count: int,
        time_period: str = "this week",
        community_name: str = "community"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive community summary from trend analysis.

        Args:
            trend_analysis: Results from analyze_community_trends
            message_count: Total number of messages analyzed
            time_period: Time period description
            community_name: Name of the community

        Returns:
            Dict with comprehensive summary sections
        """
        if not self.available:
            return {
                'summary_title': f"{community_name.title()} Community Activity - {time_period.title()}",
                'overview': f"Analyzed {message_count} messages from the {community_name} over {time_period}.",
                'key_highlights': f"• Active discussions across multiple topics\n• {message_count} total messages\n• Community remains engaged",
                'trending_section': f"The {community_name} has been discussing various topics with good engagement levels.",
                'announcements_section': trend_analysis.get('notable_announcements', 'No major announcements'),
                'community_pulse': f"The {community_name} shows healthy activity with diverse discussions."
            }

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Failed to use structured output format")

                result = self.community_summarizer(
                    trending_topics=trend_analysis.get('trending_topics', 'Various topics'),
                    announcements=trend_analysis.get('notable_announcements', 'No announcements'),
                    discussion_stats=trend_analysis.get('discussion_types', 'Mixed discussions'),
                    time_period=time_period,
                    community_name=community_name,
                    message_count=message_count
                )

            return {
                'summary_title': result.summary_title,
                'overview': result.overview,
                'key_highlights': result.key_highlights,
                'trending_section': result.trending_section,
                'announcements_section': result.announcements_section,
                'community_pulse': result.community_pulse
            }
        except Exception:
            return {
                'summary_title': f"{community_name.title()} Community Activity - {time_period.title()}",
                'overview': f"Analyzed {message_count} messages from the {community_name} over {time_period}. {trend_analysis.get('trending_topics', 'Various discussions')} were popular topics.",
                'key_highlights': f"• {trend_analysis.get('trending_topics', 'Active discussions')}\n• {trend_analysis.get('discussion_types', 'Mixed content types')}\n• {message_count} total messages analyzed",
                'trending_section': f"Popular topics included {trend_analysis.get('trending_topics', 'various discussions')}.",
                'announcements_section': trend_analysis.get('notable_announcements', 'No major announcements noted'),
                'community_pulse': f"The {community_name} shows active engagement with {trend_analysis.get('discussion_types', 'diverse discussions')}."
            }