"""NNTP client module for connecting to UseNet servers."""

import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator, Any
import asyncio
import concurrent.futures
import fnmatch

import nntp
from dateutil.parser import parse as parse_date


class NNTPClient:
    """Modern async NNTP client for UseNet operations."""

    def __init__(self, config: Dict[str, any]):
        """Initialize NNTP client with server configuration."""
        self.host = config['host']
        self.port = config['port']
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_ssl = config.get('use_ssl', False)
        self._connection = None

    def _connect(self) -> nntp.NNTPClient:
        """Establish connection to NNTP server."""
        username = self.username or ''
        password = self.password or ''

        server = nntp.NNTPClient(
            self.host,
            self.port,
            username=username,
            password=password,
            use_ssl=self.use_ssl
        )

        return server

    def list_newsgroups(self, pattern: Optional[str] = None, max_results: int = 100) -> List[Tuple[str, int, int, str]]:
        """
        Retrieve list of available newsgroups.

        Returns:
            List of tuples: (group_name, last_article, first_article, posting_flag)
        """
        with self._connect() as server:
            groups_data = server.list()

            groups = []
            count = 0

            try:
                for line in groups_data:
                    if count >= max_results:
                        # Consume the rest of the generator to avoid sync error
                        for _ in groups_data:
                            pass
                        break

                    parts = line.split()
                    if len(parts) >= 4:
                        group_name, last, first, flag = parts[0], int(parts[1]), int(parts[2]), parts[3]

                        if pattern is None or pattern.lower() in group_name.lower():
                            groups.append((group_name, last, first, flag))
                            count += 1
            except Exception:
                # Ensure generator is exhausted even on error
                for _ in groups_data:
                    pass
                raise

            return groups

    def list_all_newsgroups(self, pattern: Optional[str] = None, page_size: int = 1000) -> List[Tuple[str, int, int, str]]:
        """
        Retrieve all available newsgroups with pagination support.

        Returns:
            List of tuples: (group_name, last_article, first_article, posting_flag)
        """
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn

        console = Console()

        with self._connect() as server:
            groups_data = server.list()
            groups = []
            processed = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TextColumn("Processed: {task.completed}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading newsgroups...", total=None)

                try:
                    for line in groups_data:
                        parts = line.split()
                        if len(parts) >= 4:
                            group_name, last, first, flag = parts[0], int(parts[1]), int(parts[2]), parts[3]

                            if pattern is None or pattern.lower() in group_name.lower():
                                groups.append((group_name, last, first, flag))

                        processed += 1
                        if processed % page_size == 0:
                            progress.update(task, completed=len(groups), description=f"Loading newsgroups... ({processed} processed)")

                    progress.update(task, completed=len(groups), description=f"Completed! ({processed} total processed)")

                except Exception:
                    # Ensure generator is exhausted even on error
                    for _ in groups_data:
                        pass
                    raise

            return groups

    def get_group_info(self, group_name: str) -> Optional[Tuple[int, int, int, str]]:
        """
        Get information about a specific newsgroup.

        Returns:
            Tuple: (article_count, first_article, last_article, group_name)
        """
        try:
            with self._connect() as server:
                count, first, last, name = server.group(group_name)
                return (count, first, last, name)
        except nntp.NNTPError:
            return None

    def test_connection(self) -> bool:
        """Test connection to NNTP server."""
        try:
            with self._connect() as server:
                server.capabilities()
                return True
        except Exception:
            return False

    def get_message_headers(
        self,
        group_name: str,
        max_messages: int = 100,
        since_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve message headers from a newsgroup using XOVER.

        Args:
            group_name: Name of the newsgroup
            max_messages: Maximum number of messages to retrieve
            since_days: Only get messages from the last N days

        Returns:
            List of message header dictionaries with keys:
            - article_number: int
            - subject: str
            - from: str (sender)
            - date: str (original date string)
            - message_id: str
            - references: str (thread references)
            - parsed_date: datetime (parsed date object)
        """
        with self._connect() as server:
            try:
                # Select the group
                count, first, last, name = server.group(group_name)

                # Calculate article range
                if max_messages > 0:
                    start_article = max(first, last - max_messages + 1)
                else:
                    start_article = first
                end_article = last

                if start_article > end_article:
                    return []

                # Get headers using XOVER
                headers_data = server.xover((start_article, end_article))
                messages = []

                # Calculate cutoff date if filtering by days
                cutoff_date = None
                if since_days is not None:
                    cutoff_date = datetime.now() - timedelta(days=since_days)

                for article_num, header_dict in headers_data:
                    try:
                        # Parse the date
                        date_str = header_dict.get('date', '')
                        parsed_date = None
                        if date_str:
                            try:
                                parsed_date = parse_date(date_str)
                                # Convert to UTC if timezone aware
                                if parsed_date.tzinfo is not None:
                                    parsed_date = parsed_date.utctimetuple()
                                    parsed_date = datetime(*parsed_date[:6])
                            except (ValueError, TypeError):
                                # If date parsing fails, set to None
                                parsed_date = None

                        # Skip if message is too old
                        if cutoff_date and parsed_date and parsed_date < cutoff_date:
                            continue

                        message_info = {
                            'article_number': article_num,
                            'subject': header_dict.get('subject', ''),
                            'from': header_dict.get('from', ''),
                            'date': date_str,
                            'message_id': header_dict.get('message-id', ''),
                            'references': header_dict.get('references', ''),
                            'parsed_date': parsed_date
                        }

                        messages.append(message_info)

                    except Exception:
                        # Skip malformed headers
                        continue

                # Sort by date (newest first) if we have parsed dates
                messages.sort(key=lambda x: x['parsed_date'] or datetime.min, reverse=True)

                return messages

            except nntp.NNTPError:
                return []

    def find_matching_groups(self, pattern: str, cached_groups: Optional[List[Tuple[str, int, int, str]]] = None) -> List[str]:
        """
        Find newsgroups matching a pattern.

        Args:
            pattern: Unix shell-style pattern (e.g., "*.amiga.*", "comp.sys.amiga.*")
            cached_groups: Optional list of cached groups to search in

        Returns:
            List of matching newsgroup names
        """
        if cached_groups:
            # Use cached groups for faster searching
            all_groups = [group[0] for group in cached_groups]
        else:
            # Fetch from server
            with self._connect() as server:
                groups_data = server.list()
                all_groups = []
                try:
                    for line in groups_data:
                        parts = line.split()
                        if len(parts) >= 4:
                            all_groups.append(parts[0])
                except Exception:
                    # Ensure generator is exhausted even on error
                    for _ in groups_data:
                        pass
                    raise

        # Filter using pattern matching
        matching_groups = []
        for group_name in all_groups:
            if fnmatch.fnmatch(group_name, pattern):
                matching_groups.append(group_name)

        return sorted(matching_groups)

    def get_message_headers_parallel(
        self,
        group_names: List[str],
        max_messages_per_group: int = 50,
        since_days: Optional[int] = None,
        max_workers: int = 4
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve message headers from multiple newsgroups in parallel.

        Args:
            group_names: List of newsgroup names to search
            max_messages_per_group: Maximum messages per group
            since_days: Only get messages from the last N days
            max_workers: Maximum number of parallel connections

        Returns:
            Dictionary mapping group names to their message lists
        """
        results = {}

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit jobs for each group
            future_to_group = {
                executor.submit(
                    self._get_headers_for_group_safe,
                    group_name,
                    max_messages_per_group,
                    since_days
                ): group_name
                for group_name in group_names
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_group):
                group_name = future_to_group[future]
                try:
                    messages = future.result()
                    if messages:  # Only include groups with messages
                        results[group_name] = messages
                except Exception as exc:
                    # Log error but continue with other groups
                    print(f"Error retrieving headers from {group_name}: {exc}")
                    results[group_name] = []

        return results

    def _get_headers_for_group_safe(
        self,
        group_name: str,
        max_messages: int,
        since_days: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Safe wrapper for get_message_headers that handles individual group errors.
        Each thread gets its own connection to avoid conflicts.
        """
        try:
            return self.get_message_headers(group_name, max_messages, since_days)
        except Exception:
            # Return empty list on any error
            return []

    def get_message_body(self, group_name: str, article_number: int) -> Optional[str]:
        """
        Retrieve the body of a specific message.

        Args:
            group_name: Name of the newsgroup
            article_number: Article number to retrieve

        Returns:
            Message body as string, or None if retrieval fails
        """
        try:
            with self._connect() as server:
                # Select the group
                server.group(group_name)

                # Get the article body
                article = server.body(article_number)

                # Extract body text
                body_lines = []
                for line in article[2]:
                    body_lines.append(line)

                return '\n'.join(body_lines)
        except nntp.NNTPError:
            return None

    def get_message_bodies_for_headers(
        self,
        group_name: str,
        messages: List[Dict[str, Any]],
        max_bodies: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve message bodies for a list of message headers.

        Args:
            group_name: Name of the newsgroup
            messages: List of message header dictionaries
            max_bodies: Maximum number of bodies to retrieve

        Returns:
            Updated message list with 'body' field added
        """
        messages_with_bodies = []

        with self._connect() as server:
            try:
                # Select the group once
                server.group(group_name)

                for i, msg in enumerate(messages):
                    if i >= max_bodies:
                        # Add remaining messages without bodies
                        messages_with_bodies.append(msg)
                        continue

                    article_num = msg.get('article_number')
                    if article_num:
                        try:
                            # Get the article body
                            article = server.body(article_num)

                            # Extract body text
                            body_lines = []
                            for line in article[2]:
                                body_lines.append(line)

                            # Create enhanced message with body
                            enhanced_msg = msg.copy()
                            enhanced_msg['body'] = '\n'.join(body_lines)
                            messages_with_bodies.append(enhanced_msg)
                        except nntp.NNTPError:
                            # If body retrieval fails, keep original message
                            messages_with_bodies.append(msg)
                    else:
                        messages_with_bodies.append(msg)

            except nntp.NNTPError:
                # Return original messages if group selection fails
                return messages

        return messages_with_bodies

    def search_multiple_groups(
        self,
        group_pattern: str,
        poster: Optional[str] = None,
        topic: Optional[str] = None,
        max_messages_per_group: int = 50,
        since_days: Optional[int] = 7,
        max_groups: int = 20,
        cached_groups: Optional[List[Tuple[str, int, int, str]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for messages across multiple newsgroups matching a pattern.

        Args:
            group_pattern: Pattern for newsgroup names (e.g., "*.amiga.*")
            poster: Optional poster name to filter by
            topic: Optional topic to search for (e.g., "z3660 accelerator")
            max_messages_per_group: Max messages to retrieve per group
            since_days: Only get messages from last N days
            max_groups: Maximum number of groups to search
            cached_groups: Optional cached group list for faster pattern matching

        Returns:
            Dictionary mapping group names to filtered messages
        """
        from rich.console import Console
        console = Console()

        # Find matching groups
        console.print(f"🔍 Finding groups matching pattern: {group_pattern}")
        matching_groups = self.find_matching_groups(group_pattern, cached_groups)

        if not matching_groups:
            console.print(f"❌ No groups found matching pattern: {group_pattern}")
            return {}

        # Limit number of groups to search
        if len(matching_groups) > max_groups:
            console.print(f"⚠️  Found {len(matching_groups)} groups, limiting to {max_groups}")
            matching_groups = matching_groups[:max_groups]

        console.print(f"📋 Searching {len(matching_groups)} groups: {', '.join(matching_groups[:5])}{'...' if len(matching_groups) > 5 else ''}")

        # Get headers in parallel
        all_results = self.get_message_headers_parallel(
            matching_groups,
            max_messages_per_group,
            since_days
        )

        # Filter by poster or topic if specified
        if poster or topic:
            from .llm_search import LLMSearchEngine
            search_engine = LLMSearchEngine()

            filtered_results = {}
            total_matches = 0

            for group_name, messages in all_results.items():
                if messages:  # Only process groups with messages
                    group_filtered = messages

                    # Apply poster filter first
                    if poster:
                        group_filtered = search_engine.filter_messages_by_poster(
                            group_filtered, poster, min_confidence=0.5
                        )

                    # Apply topic filter second
                    if topic and group_filtered:
                        group_filtered = search_engine.filter_messages_by_topic(
                            group_filtered, topic, min_relevance=0.5, min_confidence=0.5
                        )

                    if group_filtered:
                        filtered_results[group_name] = group_filtered
                        total_matches += len(group_filtered)

            if poster and topic:
                console.print(f"🎯 Found {total_matches} messages by '{poster}' about '{topic}' across {len(filtered_results)} groups")
            elif poster:
                console.print(f"🎯 Found {total_matches} messages matching poster '{poster}' across {len(filtered_results)} groups")
            elif topic:
                console.print(f"📌 Found {total_matches} messages about '{topic}' across {len(filtered_results)} groups")

            return filtered_results
        else:
            # Return all messages
            total_messages = sum(len(messages) for messages in all_results.values())
            console.print(f"📊 Retrieved {total_messages} messages from {len(all_results)} groups")
            return all_results