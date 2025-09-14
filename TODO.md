## Baseline

- As a user, I want to set up my UseNet / NNTP provider so that I can download a list of available newsgroup sources ✅
  - correctly navigate paged results from the nntp server so that we can assemble a full list of groups ✅
  - cache the group list so that subsequent search / filter operations need not hit the nntp server every time, and searches are faster ✅
  - provide a way to update the cached list of groups ✅

## Message Search Implementation

### Phase 1: Basic Message Header Retrieval (Current)

**Goal**: Implement the fundamental capability to retrieve and search message headers from a single newsgroup.

#### 1.1 Extend NNTP Client for Message Operations
- [x] Add `get_message_headers()` method using pynntp's XOVER command
- [x] Implement streaming header retrieval with generators for efficiency
- [x] Support date range filtering for recent messages
- [x] Extract key header fields: subject, from, date, message-id, references

#### 1.2 Add Basic Search Command
- [x] Create `unc search-messages <newsgroup>` command
- [x] Support `--poster` flag to search by From header
- [x] Support `--since` flag for date-based filtering
- [x] Display results in Rich table format

#### 1.3 Initial DSPy Integration
- [x] Add DSPy dependency to pyproject.toml
- [x] Create simple DSPy signature for poster name matching
- [x] Implement basic content relevance assessment
- [x] Handle variations in poster names (nicknames, email formats)
- [x] Configure Ollama with qwen2.5:14b model for local LLM processing

**Success Criteria**: ✅ **ALL COMPLETED**
- ✅ Search `comp.sys.amiga.misc` for posts by "Bobbie Sellers" (working)
- ✅ Retrieve message headers in <1 second (fast)
- ✅ LLM-assisted poster name matching with confidence scores and reasoning

## ✅ **Completed Use Cases**

### Phase 1 Use Cases
**Single Group Search:**
```bash
# Search specific newsgroup for recent messages
unc search-messages comp.sys.amiga.misc --max 10

# Find messages by specific poster with LLM intelligence
unc search-messages comp.sys.amiga.misc --poster "Bobbie Sellers"

# Search with custom confidence and time window
unc search-messages comp.sys.amiga.misc --poster "RobertB" --confidence 0.7 --since 30
```

**Results Achieved:**
- ✅ Found 4 messages by "Bobbie Sellers" with 1.00 confidence
- ✅ LLM reasoning: "The message is from the searched poster, Bobbie Sellers"
- ✅ Sub-second performance with rich table display

### Phase 2 Use Cases
**Multi-Group Pattern Search:**
```bash
# Search all amiga-related groups
unc search-messages "*.amiga.*" --max 50

# Search comp.sys.amiga hierarchy
unc search-messages "comp.sys.amiga.*" --since 30

# Cross-group poster search
unc search-messages "comp.*amiga*" --poster "Frank Linhares" --max-groups 15
```

**Results Achieved:**
- ✅ Pattern matched 104 groups for `*.amiga.*` (auto-limited to 20)
- ✅ Found 34 groups for `comp.*amiga*` with parallel processing
- ✅ Retrieved live messages from `comp.sys.amiga.misc` and `comp.sys.amiga.applications`
- ✅ Multi-group table with Date, Group, From, Subject columns
- ✅ Groups Summary showing message distribution

### Phase 3 Use Cases
**Topic-Based Search:**
```bash
# Search for specific hardware topic with smart relevance matching
unc search-messages comp.sys.amiga.misc --topic "z3660 accelerator" --relevance 0.7

# Deep analysis with message body content (slower but more accurate)
unc search-messages comp.sys.amiga.misc --topic "Vampire accelerator" --with-body

# Multi-group topic search across amiga newsgroups
unc search-messages "*.amiga.*" --topic "Workbench 3.9" --max-groups 15
```

**Results Achieved:**
- ✅ Intelligent topic matching using DSPy with context awareness
- ✅ Message body analysis for deeper content relevance (--with-body flag)
- ✅ Relevance scoring from 0.0-1.0 with user-configurable thresholds
- ✅ Key indicator extraction showing why messages match topics
- ✅ Smart resource management: body retrieval limited to top 20 candidates
- ✅ Enhanced topic analysis summary with average relevance scores

### Phase 4 Use Cases
**Community Activity Summaries:**
```bash
# Weekly community summary with auto-detected community name
unc summarize "*.amiga.*" --period week --format detailed

# Monthly overview with custom community name
unc summarize "comp.sys.amiga.*" --period month --community "Amiga Systems"

# High-importance announcements only over custom period
unc summarize "*.amiga.*" --period 14 --min-importance 0.7 --format highlights

# Brief format for quick overview
unc summarize comp.sys.amiga.misc --period week --format brief
```

**Results Achieved:**
- ✅ AI-powered message classification with confidence scoring and fallback
- ✅ Trending topic identification with activity level analysis
- ✅ Automatic announcement detection and importance ranking
- ✅ Community pulse assessment with engagement measurement
- ✅ Time-period scaling: longer periods retrieve proportionally more messages
- ✅ Multi-format output: detailed, brief, and highlights modes
- ✅ Rich statistical breakdowns by message type and newsgroup
- ✅ Intelligent community name auto-detection from patterns

### Phase 5 Use Cases
**Message Listing & Data Verification:**
```bash
# Single newsgroup with time period
unc list-messages "0.test" --max 10 --period week

# Multi-group pattern with scaling verification
unc list-messages "0.*" --max 20 --period month --max-groups 5

# Custom time period for detailed exploration
unc list-messages "0.test" --since 365 --max 50

# Compare time scaling (debugging the original issue)
unc list-messages "0.*" --period week    # 50 messages per group
unc list-messages "0.*" --period month   # 214 messages per group
```

**Results Achieved:**
- ✅ Raw message header display without LLM overhead for data verification
- ✅ Time-period scaling validation: month retrieves 4x+ more messages than week
- ✅ Multi-group pattern support with Group column and statistics breakdown
- ✅ Chronological sorting (newest first) with configurable display limits
- ✅ Rich table formatting with proper column truncation for readability
- ✅ Foundation for debugging message retrieval and time-scaling logic
- ✅ Enables verification of summarization input data before expensive analysis

### Advanced Features Working
**Performance & Reliability:**
- ✅ Parallel processing: 4 concurrent NNTP connections
- ✅ Resource management: Auto-limit to 20 groups max
- ✅ Error resilience: Individual group failures don't stop search
- ✅ Memory efficiency: Streaming XOVER with generators
- ✅ Smart caching: Uses newsgroup cache for pattern matching

**User Experience:**
- ✅ Auto-detection: `*` patterns trigger multi-group mode
- ✅ Rich display: Group names in multi-group results
- ✅ Progress feedback: Shows groups being searched
- ✅ Result summaries: Message counts per group
- ✅ Graceful fallbacks: LLM unavailable handling

**Topic Intelligence:**
- ✅ Context-aware topic matching with newsgroup awareness
- ✅ Dual analysis modes: header-only vs header+body content
- ✅ Confidence scoring and relevance thresholds
- ✅ Key indicator extraction and reasoning explanations
- ✅ Fallback keyword matching when LLM unavailable

**Community Intelligence:**
- ✅ AI-powered message classification and trend analysis
- ✅ Intelligent time-period scaling: 7-day vs 30-day message retrieval automatically adjusted
- ✅ Community pulse assessment and engagement metrics
- ✅ Announcement detection with importance scoring
- ✅ Multi-format summaries: detailed, brief, and highlights modes
- ✅ Auto-community detection from newsgroup patterns

### Phase 2 Completion ✅ **COMPLETED**
**Multi-Group Search Implementation:**
- [x] Search across multiple newsgroups (e.g., all amiga.* groups)
- [x] Parallel header retrieval for performance (4 concurrent connections)
- [x] Aggregate and deduplicate results
- [x] Unix shell-style pattern matching with fnmatch
- [x] Smart group limiting and resource management
- [x] Enhanced display with Group column for multi-group results
- [x] Integration with cached newsgroup lists for faster pattern matching
- [x] Comprehensive error handling per group

### Phase 3 Completion ✅ **COMPLETED**
**Topic-Based Search Implementation:**
- [x] DSPy signature for topic matching (e.g., "z3660 accelerator")
- [x] Enhanced TopicMatcher and TopicMatcherWithBody signatures for contextual analysis
- [x] Message body retrieval capability with `get_message_body()` and batch processing
- [x] Relevance scoring and ranking with confidence thresholds
- [x] CLI `--topic` flag with `--with-body` option for deeper content analysis
- [x] Smart body retrieval limiting (up to 20 messages) to balance accuracy vs performance
- [x] Fallback keyword matching when LLM is unavailable

### Phase 4 Completion ✅ **COMPLETED**
**Community Activity Summary Implementation:**
- [x] Recent posts aggregation and analysis across newsgroups
- [x] Topic clustering and trend identification using DSPy
- [x] Weekly/monthly community activity summaries with intelligent time-period scaling
- [x] Announcement detection and categorization (releases, events, discussions)
- [x] Multi-group summary reports with key highlights and emerging topics
- [x] Smart filtering to surface important announcements vs routine discussions
- [x] `unc summarize` command with flexible time periods and output formats
- [x] Community pulse assessment and engagement measurement
- [x] LLM-powered message classification with graceful fallback

### Phase 5 Completion ✅ **COMPLETED**
**Message Listing & Data Verification Implementation:**
- [x] Simple message listing command for data verification and exploration
- [x] `unc list-messages <newsgroup_pattern>` with time period filtering (week, month, custom days)
- [x] Display raw message headers: subject, from, date, newsgroup in Rich table format
- [x] Support multi-group patterns with same time-period scaling as summarize command
- [x] No LLM processing - pure data display for verification of search/summarization inputs
- [x] Chronological sorting with configurable limits (e.g., `--max 100`, `--since 7`)
- [x] Enable users to verify message retrieval before running expensive LLM analysis
- [x] Foundation for debugging time-period scaling and message filtering logic
- [x] Time-period scaling validation: week vs month shows 4x+ message retrieval difference
- [x] Multi-group pattern support with Group column and statistics breakdown

### Phase 6 Completion ✅ **COMPLETED**
**Conversational Agent Interface Implementation:**
- [x] Create conversational front-end to existing CLI commands using mojentic framework
- [x] Expose all CLI commands (`search-messages`, `summarize`, `list-messages`, etc.) as agent tools
- [x] Implement `unc interactive` command for conversational CLI interface
- [x] Natural language query processing for newsgroup exploration
- [x] Service layer abstraction to separate business logic from CLI presentation
- [x] Agent tools that wrap service layer functionality for mojentic integration
- [x] Context-aware conversational interface with tool access
- [x] All CLI functionality accessible through natural conversation
- [x] Smart model selection: qwen3:30b-a3b-q4_K_M for conversation, qwen2.5:14b for DSPy operations
- [x] Mojentic framework integration with proper error handling and graceful degradation

### Phase 6 Use Cases
**Interactive Conversational Interface:**
```bash
# Start conversational session
unc interactive

# Natural language queries work seamlessly:
# "What tools do you have available?"
# "Show me information about the newsgroups cache"
# "Search for recent Amiga discussions"
# "List some comp.sys.amiga groups"
# "Summarize the Amiga community activity this week"
```

**Results Achieved:**
- ✅ Conversational agent successfully integrates all CLI functionality
- ✅ Natural language processing with automatic tool selection
- ✅ Service layer provides clean abstraction for both CLI and agent use
- ✅ All existing commands (setup, list-groups, search-messages, summarize, etc.) work through conversation
- ✅ Context preservation across conversation turns
- ✅ Intelligent error handling and user guidance

## Future Considerations

#### Phase 7: UseNet File Sharing Pattern Recognition
- Intelligent recognition of file sharing message patterns
- Detect multi-part file sharing sequences (similar subjects across many messages)
- Group related file-sharing messages into single atomic community interactions
- Optimize to skip message body retrieval for recognized binary file sharing
- Pattern matching for common file sharing formats (RAR parts, PAR files, etc.)
- Community analysis enhancement: distinguish discussion from file sharing activity
- Smart filtering to focus on actual discussions vs automated file posts
- Performance optimization: avoid downloading useless binary content
- Enhanced community summaries that separate conversation from file sharing volume

#### Phase 8: Translation & Language Support
- Detect message language using DSPy
- Integrate translation service (Google Translate API or local model)
- User-configurable target language
- Preserve original with translated version

#### Phase 9: Advanced Features
- Message thread reconstruction using References header
- Smart caching of message metadata with SQLite
- Real-time search optimization using DSPy's auto-optimization
- Export search results to various formats
- Advanced filtering (score thresholds, date ranges, group patterns)

#### Phase 10: Performance & Scalability
- Message metadata indexing for faster searches
- Incremental updates to message cache
- Search result caching and invalidation
- Batch processing for large newsgroup collections

## Technical Architecture Notes

- **Streaming Processing**: Use pynntp's generator-based XOVER for memory efficiency
- **DSPy Signatures**: Create modular, reusable LLM interaction patterns
- **Caching Strategy**: Separate caches for newsgroups vs message metadata
- **Error Handling**: Graceful degradation when servers are unavailable
- **Extensibility**: Plugin architecture for custom search filters
