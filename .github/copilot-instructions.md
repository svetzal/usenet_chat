# AI Coding Agent Instructions

Concise, project-specific guidance for working effectively in this repository. Focus on THESE conventions; avoid generic boilerplate.

## Project Overview
Modern async-leaning NNTP/UseNet client (package: `usenet_client`) with:
- Rich + Typer CLI (`unc`) for interactive commands
- Local LLM (DSPy + Ollama) optional enhancement for fuzzy poster/topic matching
- Caching of provider setup and newsgroup list in user home (`~/.usenet_client`)
- Parallel multi-group header searches with graceful degradation when LLM unavailable

## Key Entry Points
- CLI root: `src/usenet_client/cli.py` (Typer app + subcommands: `setup`, `list-groups`, `update-cache`, `cache-info`, `search-messages`)
- NNTP operations: `src/usenet_client/nntp_client.py` (group listing, XOVER header retrieval, multi-group + parallel search, pattern matching)
- Config & caching: `src/usenet_client/config.py` (JSON files: `config.json`, `newsgroups_cache.json` + age-based invalidation)
- LLM augmentation: `src/usenet_client/llm_search.py` (Poster matching & relevance signatures; falls back automatically)

## Runtime & Tooling
- Python ≥3.13 (see `pyproject.toml` / PEP 621 metadata). Build backend: Hatchling.
- Install/edit deps via `[project.dependencies]` only. Keep versions minimal & caret-free (current style: lower bounds).
- CLI installed via entry point `unc = usenet_client.cli:app`.
- **CRITICAL**: ALWAYS activate local venv first with `source .venv/bin/activate` before ANY Python commands.
- **NEVER** use `python3` directly - always use `python` after venv activation.

## CLI Conventions
- Commands provide rich status + emoji feedback (preserve this UX style).
- Multi-group search auto-triggers if pattern contains `*` or `?`, OR `--multi-group` flag supplied.
- Limit displays to a curated subset (e.g., top 20 messages) while showing summary counts.
- Provide helpful guidance when config/cache missing instead of stack traces; use `typer.Exit(1)` for fatal user errors.

## Caching & Expiry
- Newsgroup cache considered expired after 24h (`get_cache_info()` logic). Respect `--force` for overrides.
- Prefer using cache for pattern enumeration; only hit server when necessary or cache stale.
- Cache persistence format: list of dicts (name,last,first,flag) with top-level timestamp.

## Parallel & Pattern Search
- Pattern matching uses `fnmatch` and optional cached list to avoid network roundtrips.
- Parallel retrieval uses `ThreadPoolExecutor` (max 4 workers) in `get_message_headers_parallel`; each task builds its own connection.
- Errors per group are logged/ignored to keep aggregate results flowing.

## LLM Integration (Optional)
- DSPy model initialization may fail; code must proceed with fallback string/keyword matching.
- Poster matching attaches `llm_analysis` with `match_confidence` + `match_reason`; sort by confidence descending.
- Do NOT hard-require model downloads or external APIs—keep silent fallback path intact.

## Date & Filtering Semantics
- `--since N` uses days; implemented as cutoff datetime before header iteration; only skip when parsed date < cutoff.
- Date parsing uses `dateutil.parser.parse`; unreadable dates → `parsed_date=None` (retain ordering safety).

## Error Handling Patterns
- Wrap NNTP operations in context managers; exhaust generators on early exit to avoid protocol sync issues.
- Broad exceptions inside per-message loops skip malformed records without aborting the batch.
- Return empty lists/dicts instead of raising where user-facing commands rely on simple conditional messaging.

## Adding New Features
When extending:
- Keep CLI additions small, self-contained functions decorated with `@app.command()`.
- Reuse config & NNTP client rather than duplicating connection logic.
- Provide rich progress feedback for long-running tasks (see `list_all_newsgroups` progress usage pattern).
- For new LLM capabilities, follow existing signature pattern (`dspy.Signature` + `dspy.Predict`). Provide a graceful non-LLM fallback.

## Style & UX Norms
- Emojis + concise phrases for status (✅, ❌, 🔍, 📋, ⚠️, 🎯, 📊) – remain consistent.
- Table outputs: fixed width for columns prone to overflow (From, Group) with ellipsis truncation.
- Summaries (e.g., group counts, reason aggregation) appear after primary table when present.

## Guardrails / Non-Goals
- Do NOT implement persistent DB yet (future note mentions SQLite – not active).
- Avoid fetching full message bodies until topic/ relevance phase is added (Phase 3 TBD).
- Keep memory footprint low: no bulk loading of entire large hierarchies into RAM beyond current streaming approach.

## Quick Reference Examples
- Configure: `unc setup news.server.tld --port 119 --username alice --password secret`
- Update cache: `unc update-cache --force`
- List groups (cached): `unc list-groups --max-results 50 amiga`
- Multi-group poster search: `unc search-messages "comp.sys.amiga.*" --poster "Bobbie Sellers" --max 200 --max-groups 15`

## Documentation & TODO Management

### Technology Foundation Standards
- Use clean, modular, and modern async Python code with PEP 621 compliant `pyproject.toml`
- Maintain rich command-line experience using Rich and Typer libraries for good CLI UX and code modularity
- Characterize UseNet/NNTP server behaviors to provide comprehensive test coverage

### TODO.md Structure Pattern
When maintaining TODO.md, follow this three-section structure:

**1. Implementation Details (Top Section)**
- **Phase N: [Feature Name]** - Technical implementation details with task lists
- Use `[x]` for completed and `[ ]` for pending items
- Include success criteria for each phase

**2. Success Showcase (Middle Section)**
- **Completed Use Cases** - Real command examples with actual results
- **Advanced Features Working** - Technical achievements and UX enhancements
- Proven functionality with specific examples and performance metrics

**3. Future Planning (Bottom Section)**
- **Future Considerations** - Upcoming phases and development roadmap
- Keep focused on what's next, not what's done

This pattern ensures the document tells a complete story: what was built, how it works, and what's planned next.

## Ready Signals for Agents
If adding a feature, verify:
1. Falls back cleanly when network/LLM unavailable
2. Emits user-facing guidance instead of raw tracebacks
3. Respects existing cache + pattern matching strategies
4. Maintains confidence sorting & display truncation patterns

Request clarification from maintainers if you need message body retrieval logic, SQLite caching design, or topic relevance scoring details (not yet codified).
