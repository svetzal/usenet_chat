"""Command-line interface for the UseNet client."""

import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime

from .nntp_client import NNTPClient
from .config import Config
from .llm_search import LLMSearchEngine
from .community_analysis import CommunityAnalyzer

app = typer.Typer(help="Modern NNTP/UseNet client")
console = Console()

@app.command()
def setup(
    host: str = typer.Argument(..., help="NNTP server hostname"),
    port: int = typer.Option(119, help="NNTP server port"),
    username: str = typer.Option(None, help="Username for authentication"),
    password: str = typer.Option(None, help="Password for authentication"),
    use_ssl: bool = typer.Option(False, help="Use SSL connection"),
):
    """Set up your UseNet/NNTP provider configuration."""
    config = Config()
    config.save_provider_config(host, port, username, password, use_ssl)
    console.print(f"✅ NNTP provider configured: {host}:{port}", style="green")

@app.command()
def list_groups(
    pattern: str = typer.Option(None, help="Pattern to filter newsgroups"),
    max_results: int = typer.Option(100, help="Maximum number of groups to display"),
    all_groups: bool = typer.Option(False, "--all", help="Load all available newsgroups (ignores max-results)"),
    page_size: int = typer.Option(1000, help="Number of groups to load per batch"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache and fetch directly from server"),
):
    """Display available newsgroups from your NNTP provider."""
    config = Config()
    provider_config = config.load_provider_config()

    if not provider_config:
        console.print("❌ No NNTP provider configured. Run 'unc setup' first.", style="red")
        raise typer.Exit(1)

    # Try to load from cache first (unless no-cache is specified)
    groups = None
    if not no_cache:
        cached_groups = config.load_newsgroups_cache()
        if cached_groups:
            console.print("📋 Using cached newsgroups (run 'unc cache-info' for details)", style="dim")

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
        cache_info = config.get_cache_info()
        if cache_info and cache_info['is_expired']:
            console.print("⚠️  Cache is expired. Consider running 'unc update-cache'", style="yellow")

        with console.status("[bold green]Connecting to NNTP server..."):
            client = NNTPClient(provider_config)

            if all_groups:
                groups = client.list_all_newsgroups(pattern, page_size)
            else:
                groups = client.list_newsgroups(pattern, max_results)

    if not groups:
        console.print("No newsgroups found.", style="yellow")
        return

    table = Table(title=f"Available Newsgroups ({len(groups)} found)")
    table.add_column("Group Name", style="cyan")
    table.add_column("Last Article", justify="right")
    table.add_column("First Article", justify="right")
    table.add_column("Status", style="green")

    for group_name, last, first, flag in groups:
        table.add_row(group_name, str(last), str(first), flag)

    console.print(table)

@app.command()
def update_cache(
    force: bool = typer.Option(False, "--force", help="Force cache update even if current cache is recent")
):
    """Update the cached list of newsgroups from the NNTP server."""
    config = Config()
    provider_config = config.load_provider_config()

    if not provider_config:
        console.print("❌ No NNTP provider configured. Run 'unc setup' first.", style="red")
        raise typer.Exit(1)

    # Check current cache status
    cache_info = config.get_cache_info()
    if cache_info and not force and not cache_info['is_expired']:
        console.print(f"📋 Cache is recent ({cache_info['age_hours']:.1f} hours old, {cache_info['group_count']} groups)", style="yellow")
        console.print("Use --force to update anyway.")
        return

    console.print("🔄 Updating newsgroups cache from server...")

    with console.status("[bold green]Connecting to NNTP server and downloading newsgroups..."):
        client = NNTPClient(provider_config)
        groups = client.list_all_newsgroups()

    config.save_newsgroups_cache(groups)

    console.print(f"✅ Cache updated with {len(groups)} newsgroups", style="green")

@app.command()
def cache_info():
    """Show information about the current newsgroups cache."""
    config = Config()
    cache_info = config.get_cache_info()

    if not cache_info:
        console.print("❌ No cache found. Run 'unc update-cache' to create one.", style="red")
        return

    cache_time = datetime.fromtimestamp(cache_info['timestamp'])
    status = "🟡 Expired" if cache_info['is_expired'] else "🟢 Fresh"

    table = Table(title="Newsgroups Cache Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Status", status)
    table.add_row("Created", cache_time.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Age", f"{cache_info['age_hours']:.1f} hours")
    table.add_row("Groups", str(cache_info['group_count']))

    console.print(table)

@app.command()
def search_messages(
    newsgroup: str = typer.Argument(..., help="Newsgroup to search in (or pattern like '*.amiga.*')"),
    poster: str = typer.Option(None, "--poster", help="Search for messages by this poster/author"),
    topic: str = typer.Option(None, "--topic", help="Search for messages about a specific topic (e.g., 'z3660 accelerator')"),
    since: int = typer.Option(7, "--since", help="Search messages from last N days"),
    max_messages: int = typer.Option(100, "--max", help="Maximum number of messages to retrieve"),
    use_llm: bool = typer.Option(True, "--llm/--no-llm", help="Use LLM for smarter matching"),
    confidence: float = typer.Option(0.5, "--confidence", help="Minimum confidence for LLM matching (0.0-1.0)"),
    relevance: float = typer.Option(0.5, "--relevance", help="Minimum topic relevance for topic search (0.0-1.0)"),
    multi_group: bool = typer.Option(False, "--multi-group", help="Enable multi-group pattern search"),
    max_groups: int = typer.Option(20, "--max-groups", help="Maximum number of groups to search when using patterns"),
    with_body: bool = typer.Option(False, "--with-body", help="Retrieve message bodies for deeper topic analysis (slower)"),
):
    """Search for messages in a newsgroup by poster or other criteria."""
    config = Config()
    provider_config = config.load_provider_config()

    if not provider_config:
        console.print("❌ No NNTP provider configured. Run 'unc setup' first.", style="red")
        raise typer.Exit(1)

    client = NNTPClient(provider_config)

    # Check if this is a multi-group search
    if multi_group or ('*' in newsgroup or '?' in newsgroup):
        console.print(f"🔍 Multi-group search: {newsgroup}", style="blue")

        # Load cached groups for faster pattern matching
        cached_groups = config.load_newsgroups_cache()

        with console.status(f"[bold green]Searching multiple newsgroups matching {newsgroup}..."):
            all_results = client.search_multiple_groups(
                group_pattern=newsgroup,
                poster=poster,
                topic=topic,
                max_messages_per_group=max_messages // max_groups if max_groups > 0 else 50,
                since_days=since,
                max_groups=max_groups,
                cached_groups=cached_groups
            )

        if not all_results:
            console.print(f"❌ No messages found in groups matching {newsgroup}", style="red")
            return

        # Flatten results for display
        all_messages = []
        for group_name, messages in all_results.items():
            for msg in messages:
                msg['newsgroup'] = group_name  # Add group info to each message
                all_messages.append(msg)

        # Sort by date (newest first)
        all_messages.sort(key=lambda x: x['parsed_date'] or datetime.min, reverse=True)

        messages = all_messages
        console.print(f"📋 Retrieved {len(messages)} message headers from {len(all_results)} groups", style="dim")

    else:
        console.print(f"🔍 Searching {newsgroup} for messages...", style="blue")

        with console.status(f"[bold green]Retrieving message headers from {newsgroup}..."):
            messages = client.get_message_headers(newsgroup, max_messages, since)

        if not messages:
            console.print(f"❌ No messages found in {newsgroup}", style="red")
            return

        console.print(f"📋 Retrieved {len(messages)} message headers", style="dim")

    # For single-group search, handle poster filtering here
    # Multi-group search already filters by poster in the backend
    filtered_messages = messages
    if poster and not (multi_group or ('*' in newsgroup or '?' in newsgroup)):
        if use_llm:
            # Use LLM-powered search
            console.print("🤖 Using LLM for intelligent poster matching...", style="blue")
            search_engine = LLMSearchEngine()

            with console.status("[bold yellow]Analyzing messages with LLM..."):
                filtered_messages = search_engine.filter_messages_by_poster(
                    messages, poster, min_confidence=confidence
                )

            if search_engine.available:
                console.print(f"🎯 LLM found {len(filtered_messages)} messages matching poster '{poster}' (confidence ≥ {confidence})", style="green")
            else:
                console.print(f"⚠️  LLM unavailable, using fallback matching. Found {len(filtered_messages)} messages", style="yellow")
        else:
            # Simple string matching
            filtered_messages = []
            poster_lower = poster.lower()

            for msg in messages:
                from_field = msg.get('from', '').lower()
                if poster_lower in from_field:
                    filtered_messages.append(msg)

            console.print(f"🎯 Found {len(filtered_messages)} messages matching poster '{poster}' (simple matching)", style="green")

    # Handle topic-based search
    if topic:
        # For single-group search with body retrieval option
        if with_body and not (multi_group or ('*' in newsgroup or '?' in newsgroup)):
            console.print(f"📖 Retrieving message bodies for deeper topic analysis...", style="blue")
            with console.status("[bold yellow]Fetching message bodies..."):
                # Retrieve bodies for top candidates (limit to avoid excessive downloads)
                max_bodies = min(20, len(filtered_messages))  # Retrieve bodies for up to 20 messages
                filtered_messages = client.get_message_bodies_for_headers(
                    newsgroup, filtered_messages[:max_bodies], max_bodies
                ) + filtered_messages[max_bodies:]

        if use_llm:
            console.print(f"🎯 Using LLM for intelligent topic matching: '{topic}'", style="blue")
            search_engine = LLMSearchEngine()

            with console.status("[bold yellow]Analyzing message topics with LLM..."):
                if with_body and not (multi_group or ('*' in newsgroup or '?' in newsgroup)):
                    # Use enhanced body-aware topic matching
                    filtered_messages = search_engine.filter_messages_by_topic_with_bodies(
                        filtered_messages, topic, min_relevance=relevance, min_confidence=confidence, use_body=True
                    )
                else:
                    # Use standard header-only topic matching
                    filtered_messages = search_engine.filter_messages_by_topic(
                        filtered_messages, topic, min_relevance=relevance, min_confidence=confidence
                    )

            if search_engine.available:
                analysis_type = "with body content" if with_body else "from headers"
                console.print(f"📌 LLM found {len(filtered_messages)} messages about '{topic}' {analysis_type} (relevance ≥ {relevance})", style="green")
            else:
                console.print(f"⚠️  LLM unavailable, using keyword matching. Found {len(filtered_messages)} messages", style="yellow")
        else:
            # Simple keyword matching for topic
            topic_filtered = []
            topic_words = topic.lower().split()

            for msg in filtered_messages:
                subject = msg.get('subject', '').lower()
                body = msg.get('body', '').lower() if with_body else ''
                text = subject + ' ' + body
                matches = sum(1 for word in topic_words if word in text)
                if matches > 0:
                    topic_filtered.append(msg)

            filtered_messages = topic_filtered
            match_type = "in subject+body" if with_body else "in subject"
            console.print(f"📌 Found {len(filtered_messages)} messages about '{topic}' (keyword matching {match_type})", style="green")

    if not filtered_messages:
        console.print(f"❌ No messages found matching the criteria", style="yellow")
        return

    # Display results in table
    is_multi_group = multi_group or ('*' in newsgroup or '?' in newsgroup)

    if is_multi_group:
        table_title = f"Multi-group search: {newsgroup}"
        if poster:
            table_title += f" by {poster}"
        if topic:
            table_title += f" about '{topic}'"
    else:
        table_title = f"Messages in {newsgroup}"
        if poster:
            table_title += f" by {poster}"
            if use_llm and not topic:
                table_title += f" (confidence ≥ {confidence})"
        if topic:
            table_title += f" about '{topic}'"
            if use_llm:
                table_title += f" (relevance ≥ {relevance})"

    table = Table(title=table_title)
    table.add_column("Date", style="cyan", width=20)
    if is_multi_group:
        table.add_column("Group", style="magenta", width=25)
    table.add_column("From", style="yellow", width=25)
    table.add_column("Subject", style="white")
    if use_llm and not is_multi_group:
        if topic:
            table.add_column("Relevance", style="blue", width=10)
        elif poster:
            table.add_column("Confidence", style="green", width=10)

    for msg in filtered_messages[:20]:  # Limit display to 20 results
        date_str = ""
        if msg['parsed_date']:
            date_str = msg['parsed_date'].strftime("%Y-%m-%d %H:%M")
        elif msg['date']:
            # Show first 20 chars of original date if parsing failed
            date_str = msg['date'][:20]

        from_field = msg.get('from', '')
        if len(from_field) > 25:
            from_field = from_field[:22] + "..."

        subject = msg.get('subject', '')
        if len(subject) > 60:
            subject = subject[:57] + "..."

        # Build row data
        row_data = [date_str]

        # Add group name for multi-group searches
        if is_multi_group:
            group_name = msg.get('newsgroup', 'Unknown')
            if len(group_name) > 25:
                group_name = group_name[:22] + "..."
            row_data.append(group_name)

        row_data.extend([from_field, subject])

        # Add score columns if using LLM (single-group only)
        if use_llm and not is_multi_group:
            if topic and 'topic_analysis' in msg:
                relevance_score = f"{msg['topic_analysis']['topic_relevance']:.2f}"
                row_data.append(relevance_score)
            elif poster and 'llm_analysis' in msg:
                confidence_score = f"{msg['llm_analysis']['match_confidence']:.2f}"
                row_data.append(confidence_score)

        table.add_row(*row_data)

    console.print(table)

    if len(filtered_messages) > 20:
        console.print(f"... and {len(filtered_messages) - 20} more messages", style="dim")

    # Show LLM analysis summary if available (single-group only)
    if use_llm and poster and not is_multi_group and filtered_messages and 'llm_analysis' in filtered_messages[0]:
        console.print("\n📊 Analysis Summary:", style="bold blue")
        reasons = {}
        for msg in filtered_messages[:5]:  # Show top 5 reasons
            reason = msg['llm_analysis']['match_reason']
            reasons[reason] = reasons.get(reason, 0) + 1

        for reason, count in reasons.items():
            console.print(f"  • {reason} ({count} messages)", style="dim")

    # Show topic analysis summary if available
    if use_llm and topic and not is_multi_group and filtered_messages and 'topic_analysis' in filtered_messages[0]:
        console.print("\n🎯 Topic Analysis Summary:", style="bold blue")
        indicators = {}
        used_body_count = 0
        for msg in filtered_messages[:5]:  # Show top 5 indicators
            indicator = msg['topic_analysis']['key_indicators']
            indicators[indicator] = indicators.get(indicator, 0) + 1
            if msg['topic_analysis'].get('used_body', False):
                used_body_count += 1

        for indicator, count in indicators.items():
            console.print(f"  • {indicator} ({count} messages)", style="dim")

        # Show average relevance
        avg_relevance = sum(msg['topic_analysis']['topic_relevance'] for msg in filtered_messages) / len(filtered_messages)
        console.print(f"  • Average relevance: {avg_relevance:.2f}", style="dim")

        # Show if body content was used
        if with_body and used_body_count > 0:
            console.print(f"  • Body content analyzed: {used_body_count}/{min(len(filtered_messages), 20)} messages", style="dim")

    # Show multi-group summary if applicable
    if is_multi_group and filtered_messages:
        console.print("\n📊 Groups Summary:", style="bold blue")
        group_counts = {}
        for msg in filtered_messages:
            group = msg.get('newsgroup', 'Unknown')
            group_counts[group] = group_counts.get(group, 0) + 1

        for group, count in sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            console.print(f"  • {group}: {count} messages", style="dim")

@app.command()
def summarize(
    newsgroup_pattern: str = typer.Argument(..., help="Newsgroup or pattern to summarize (e.g., '*.amiga.*', 'comp.sys.amiga.misc')"),
    period: str = typer.Option("week", "--period", help="Time period: 'week', 'month', or number of days (e.g., '7', '30')"),
    max_messages: int = typer.Option(200, "--max-messages", help="Maximum number of recent messages to analyze"),
    max_groups: int = typer.Option(15, "--max-groups", help="Maximum number of groups when using patterns"),
    community_name: str = typer.Option(None, "--community", help="Community name for the summary (auto-detected from pattern)"),
    format_style: str = typer.Option("detailed", "--format", help="Summary format: 'detailed', 'brief', or 'highlights'"),
    min_importance: float = typer.Option(0.3, "--min-importance", help="Minimum importance score to include messages (0.0-1.0)"),
):
    """Generate an intelligent community activity summary for newsgroups."""
    config = Config()
    provider_config = config.load_provider_config()

    if not provider_config:
        console.print("❌ No NNTP provider configured. Run 'unc setup' first.", style="red")
        raise typer.Exit(1)

    # Convert period to days
    period_days = 7  # Default to week
    period_description = "this week"

    if period.lower() == "week":
        period_days = 7
        period_description = "this week"
    elif period.lower() == "month":
        period_days = 30
        period_description = "this month"
    elif period.isdigit():
        period_days = int(period)
        period_description = f"the last {period_days} days"

    # Auto-detect community name from pattern
    if not community_name:
        if "amiga" in newsgroup_pattern.lower():
            community_name = "Amiga community"
        elif "comp.sys" in newsgroup_pattern.lower():
            community_name = "Computer systems community"
        else:
            community_name = f"{newsgroup_pattern} community"

    client = NNTPClient(provider_config)
    analyzer = CommunityAnalyzer()

    console.print(f"🔍 Analyzing {community_name} activity over {period_description}...", style="blue")

    # Check if this is a multi-group pattern
    if '*' in newsgroup_pattern or '?' in newsgroup_pattern:
        # Multi-group analysis
        cached_groups = config.load_newsgroups_cache()

        # Calculate messages per group with better scaling for time periods
        # Use a minimum of 50 messages per group, scaling up for longer periods
        base_messages_per_group = max(50, max_messages // max(max_groups, 4))
        time_multiplier = max(1.0, period_days / 7.0)  # Scale by weeks
        messages_per_group = int(base_messages_per_group * time_multiplier)

        # Cap at reasonable maximum to prevent excessive memory usage
        messages_per_group = min(messages_per_group, 500)

        console.print(f"📊 Retrieving up to {messages_per_group} messages per group over {period_days} days", style="dim")

        with console.status(f"[bold green]Gathering messages from groups matching {newsgroup_pattern}..."):
            all_results = client.search_multiple_groups(
                group_pattern=newsgroup_pattern,
                max_messages_per_group=messages_per_group,
                since_days=period_days,
                max_groups=max_groups,
                cached_groups=cached_groups
            )

        if not all_results:
            console.print(f"❌ No messages found in groups matching {newsgroup_pattern}", style="red")
            return

        # Flatten results for analysis
        all_messages = []
        for group_name, messages in all_results.items():
            for msg in messages:
                msg['newsgroup'] = group_name
                all_messages.append(msg)

        console.print(f"📋 Found {len(all_messages)} messages across {len(all_results)} groups", style="dim")

    else:
        # Single group analysis
        console.print(f"🔍 Analyzing {newsgroup_pattern}...", style="blue")

        # Scale max_messages for single group based on time period
        time_multiplier = max(1.0, period_days / 7.0)  # Scale by weeks
        scaled_max_messages = int(max_messages * time_multiplier)
        scaled_max_messages = min(scaled_max_messages, 1000)  # Cap at reasonable maximum

        console.print(f"📊 Retrieving up to {scaled_max_messages} messages over {period_days} days", style="dim")

        with console.status(f"[bold green]Retrieving messages from {newsgroup_pattern}..."):
            all_messages = client.get_message_headers(newsgroup_pattern, scaled_max_messages, period_days)

            # Add newsgroup to each message
            for msg in all_messages:
                msg['newsgroup'] = newsgroup_pattern

        if not all_messages:
            console.print(f"❌ No messages found in {newsgroup_pattern}", style="red")
            return

        console.print(f"📋 Found {len(all_messages)} messages", style="dim")

    # Analyze messages for community insights
    console.print("🤖 Analyzing community activity with AI...", style="blue")

    with console.status("[bold yellow]Classifying messages and analyzing trends..."):
        summary = analyzer.analyze_messages(
            all_messages,
            time_period=period_description,
            community_name=community_name
        )

    # Filter by importance if requested
    if min_importance > 0.0:
        important_messages = analyzer.filter_by_importance(summary['classified_messages'], min_importance)
        console.print(f"📊 Filtered to {len(important_messages)} high-importance messages (≥{min_importance})", style="dim")

    # Display summary based on format
    console.print(f"\n{summary['summary_title']}", style="bold cyan")
    console.print("=" * len(summary['summary_title']), style="dim")

    console.print(f"\n📈 {summary['overview']}")

    if format_style != "brief":
        console.print(f"\n🎯 **Key Highlights:**")
        highlights = summary['key_highlights'].split('\n')
        for highlight in highlights:
            if highlight.strip():
                console.print(f"  {highlight}")

        console.print(f"\n📊 **Trending Topics:**")
        console.print(f"  {summary['trending_section']}")

        if summary['announcements_section'] and "no announcements" not in summary['announcements_section'].lower():
            console.print(f"\n📢 **Announcements:**")
            console.print(f"  {summary['announcements_section']}")

        if format_style == "detailed":
            console.print(f"\n🌡️  **Community Pulse:**")
            console.print(f"  {summary['community_pulse']}")

            # Show top announcements
            announcements = analyzer.get_announcements(summary['classified_messages'])
            if announcements:
                console.print(f"\n📋 **Notable Announcements ({len(announcements)} found):**")
                for i, msg in enumerate(announcements[:5], 1):
                    classification = msg.get('classification', {})
                    importance = classification.get('importance_score', 0.0)
                    console.print(f"  {i}. {msg.get('subject', 'No subject')} (importance: {importance:.2f})")
                    console.print(f"     From: {msg.get('from', 'Unknown')} in {msg.get('newsgroup', 'Unknown')}", style="dim")

            # Show statistics
            stats = analyzer.get_discussion_stats(summary['classified_messages'])
            console.print(f"\n📈 **Activity Statistics:**")
            console.print(f"  • Total messages: {stats['total_messages']}")
            console.print(f"  • Announcements: {stats['announcements']}")
            console.print(f"  • Questions: {stats['questions']}")
            console.print(f"  • Technical discussions: {stats['technical']}")
            console.print(f"  • Social posts: {stats['social']}")

            if len(stats['groups']) > 1:
                console.print(f"  • Active groups: {len(stats['groups'])}")
                top_groups = sorted(stats['groups'].items(), key=lambda x: x[1], reverse=True)[:5]
                for group, count in top_groups:
                    console.print(f"    - {group}: {count} messages", style="dim")

    console.print(f"\n✨ Summary generated from {len(all_messages)} messages analyzed over {period_description}.", style="green")

@app.command()
def list_messages(
    newsgroup_pattern: str = typer.Argument(..., help="Newsgroup or pattern to list messages from (e.g., 'comp.sys.amiga.misc', '*.amiga.*')"),
    period: str = typer.Option("week", "--period", help="Time period: 'week', 'month', or number of days (e.g., '7', '30')"),
    max_messages: int = typer.Option(100, "--max", help="Maximum number of messages to display"),
    max_groups: int = typer.Option(15, "--max-groups", help="Maximum number of groups when using patterns"),
    since_days: int = typer.Option(None, "--since", help="Show messages from last N days (overrides --period)"),
):
    """List recent message headers for data verification and exploration."""
    config = Config()
    provider_config = config.load_provider_config()

    if not provider_config:
        console.print("❌ No NNTP provider configured. Run 'unc setup' first.", style="red")
        raise typer.Exit(1)

    # Convert period to days (same logic as summarize command)
    if since_days is not None:
        period_days = since_days
        period_description = f"the last {since_days} days"
    elif period.lower() == "week":
        period_days = 7
        period_description = "this week"
    elif period.lower() == "month":
        period_days = 30
        period_description = "this month"
    elif period.isdigit():
        period_days = int(period)
        period_description = f"the last {period_days} days"
    else:
        console.print(f"❌ Invalid period: {period}. Use 'week', 'month', or a number of days.", style="red")
        raise typer.Exit(1)

    client = NNTPClient(provider_config)

    console.print(f"📋 Listing messages from {newsgroup_pattern} over {period_description}...", style="blue")

    # Check if this is a multi-group pattern
    if '*' in newsgroup_pattern or '?' in newsgroup_pattern:
        # Multi-group listing (reuse logic from summarize command)
        cached_groups = config.load_newsgroups_cache()

        # Use same time-scaling logic as summarize command
        base_messages_per_group = max(50, max_messages // max(max_groups, 4))
        time_multiplier = max(1.0, period_days / 7.0)
        messages_per_group = int(base_messages_per_group * time_multiplier)
        messages_per_group = min(messages_per_group, 500)

        console.print(f"📊 Retrieving up to {messages_per_group} messages per group over {period_days} days", style="dim")

        with console.status(f"[bold green]Gathering messages from groups matching {newsgroup_pattern}..."):
            all_results = client.search_multiple_groups(
                group_pattern=newsgroup_pattern,
                max_messages_per_group=messages_per_group,
                since_days=period_days,
                max_groups=max_groups,
                cached_groups=cached_groups
            )

        if not all_results:
            console.print(f"❌ No messages found in groups matching {newsgroup_pattern}", style="red")
            return

        # Flatten results for display
        all_messages = []
        for group_name, messages in all_results.items():
            for msg in messages:
                msg['newsgroup'] = group_name
                all_messages.append(msg)

        console.print(f"📋 Found {len(all_messages)} messages across {len(all_results)} groups", style="dim")

    else:
        # Single group listing (reuse logic from summarize command)
        time_multiplier = max(1.0, period_days / 7.0)
        scaled_max_messages = int(max_messages * time_multiplier)
        scaled_max_messages = min(scaled_max_messages, 1000)

        console.print(f"📊 Retrieving up to {scaled_max_messages} messages over {period_days} days", style="dim")

        with console.status(f"[bold green]Retrieving messages from {newsgroup_pattern}..."):
            all_messages = client.get_message_headers(newsgroup_pattern, scaled_max_messages, period_days)

            # Add newsgroup to each message
            for msg in all_messages:
                msg['newsgroup'] = newsgroup_pattern

        if not all_messages:
            console.print(f"❌ No messages found in {newsgroup_pattern}", style="red")
            return

        console.print(f"📋 Found {len(all_messages)} messages", style="dim")

    # Sort messages by date (newest first)
    all_messages.sort(key=lambda x: x.get('parsed_date') or datetime.min, reverse=True)

    # Limit to max_messages for display
    display_messages = all_messages[:max_messages]

    # Display messages in Rich table
    from rich.table import Table

    table = Table(title=f"Messages from {newsgroup_pattern} ({period_description})")
    table.add_column("Date", style="cyan", width=12)
    table.add_column("From", style="yellow", width=25, overflow="ellipsis")
    table.add_column("Subject", style="white", width=50, overflow="ellipsis")

    # Add Group column for multi-group results
    if '*' in newsgroup_pattern or '?' in newsgroup_pattern:
        table.add_column("Group", style="green", width=20, overflow="ellipsis")

    for msg in display_messages:
        # Format date
        date_str = "Unknown"
        if msg.get('parsed_date'):
            date_str = msg['parsed_date'].strftime("%Y-%m-%d")
        elif msg.get('date'):
            # Try to extract just the date part if parsing failed
            date_part = msg['date'][:10] if len(msg['date']) >= 10 else msg['date']
            date_str = date_part

        # Prepare row data
        from_field = msg.get('from', 'Unknown')[:25]
        subject_field = msg.get('subject', 'No subject')[:50]

        if '*' in newsgroup_pattern or '?' in newsgroup_pattern:
            group_field = msg.get('newsgroup', 'Unknown')[:20]
            table.add_row(date_str, from_field, subject_field, group_field)
        else:
            table.add_row(date_str, from_field, subject_field)

    console.print(table)

    # Show summary statistics
    if len(all_messages) > max_messages:
        console.print(f"\n📊 Showing {max_messages} of {len(all_messages)} total messages", style="dim")

    if '*' in newsgroup_pattern or '?' in newsgroup_pattern:
        # Show group breakdown
        group_counts = {}
        for msg in all_messages:
            group = msg.get('newsgroup', 'Unknown')
            group_counts[group] = group_counts.get(group, 0) + 1

        console.print(f"\n📈 Messages by group:")
        for group, count in sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            console.print(f"  • {group}: {count} messages", style="dim")

@app.command()
def interactive(
    model: str = typer.Option("qwen3:30b-a3b-q4_K_M", "--model", help="LLM model to use for conversation"),
    system_prompt: str = typer.Option(
        "You are a helpful assistant for exploring UseNet/NNTP newsgroups. You have access to tools for configuring NNTP providers, listing newsgroups, searching messages, and generating community summaries. Always provide clear, helpful responses and suggest relevant follow-up actions.",
        "--system-prompt",
        help="System prompt for the conversational agent"
    )
):
    """Start an interactive conversational session with the UseNet client."""
    try:
        from mojentic.llm import ChatSession, LLMBroker
        from .agent_tools import get_all_tools
    except ImportError as e:
        console.print("❌ Mojentic framework not available. Please install with: pip install mojentic", style="red")
        console.print(f"Import error: {e}", style="dim")
        raise typer.Exit(1)

    # Check if configured
    from .usenet_service import UseNetService
    service = UseNetService()

    if not service.is_configured():
        console.print("⚠️  No NNTP provider configured. You can configure one during this session.", style="yellow")

    console.print("🤖 Starting interactive UseNet client session...", style="blue")
    console.print("🔧 Available capabilities:", style="dim")
    console.print("  • Configure NNTP provider", style="dim")
    console.print("  • List and search newsgroups", style="dim")
    console.print("  • Search messages by poster or topic", style="dim")
    console.print("  • Generate community activity summaries", style="dim")
    console.print("  • List recent messages for exploration", style="dim")
    console.print("\nType your questions naturally, or 'exit' to quit.\n", style="dim")

    # Initialize the conversational agent
    try:
        llm_broker = LLMBroker(model=model)
        tools = get_all_tools()
        chat_session = ChatSession(
            llm_broker,
            system_prompt=system_prompt,
            tools=tools
        )

        # Interactive loop
        while True:
            try:
                query = input("📝 You: ").strip()

                if not query:
                    continue

                if query.lower() in ['exit', 'quit', 'bye']:
                    console.print("👋 Goodbye! Thanks for using the UseNet client.", style="green")
                    break

                console.print("🤖 Assistant: ", end="", style="blue")

                # Send query to the chat session
                response = chat_session.send(query)
                console.print(response)
                console.print()  # Add spacing

            except KeyboardInterrupt:
                console.print("\n👋 Session interrupted. Goodbye!", style="yellow")
                break
            except Exception as e:
                console.print(f"\n❌ Error processing query: {e}", style="red")
                # Show stack trace for debugging
                import traceback
                console.print("Debug information:", style="dim")
                console.print(traceback.format_exc(), style="dim red")
                console.print("Please try again or type 'exit' to quit.\n", style="dim")

    except Exception as e:
        console.print(f"❌ Failed to initialize conversational agent: {e}", style="red")
        console.print("Please check your Ollama installation and model availability.", style="dim")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
    app()