# 🎯 Frontend MVP Demo Guide

This guide demonstrates the complete functionality of the OnCall Runbook frontend MVP.

## 🚀 Quick Demo

### 1. Start Services
```bash
# Start all services
make dev

# Verify everything is running
make selfcheck
```

### 2. Access the Frontend
Open your browser and navigate to: **http://localhost:3000**

You should see:
- Clean chat interface with sidebar
- Welcome message from OnCall Assistant
- Input field with send button
- Quick prompts grid

### 3. Test the Chat Interface

#### Ask a CPU Alert Question
Type: **"High CPU usage alert 80% for 5 minutes"**

Expected Response:
```
**First checks:**
• Check for runaway processes
• Review recent deployments
• Check for memory leaks

**Why this happens:**
• Infinite loops in application code
• Database query issues

**Diagnostics if tools ran:**
• app logs: 3 recent entries
• nginx logs: Log file not found: nginx.log
• system logs: Log file not found: system.log

**Sources:** See citations below.
```

#### Sources Display
Below the answer, you'll see:
- **Sources:** label
- Clickable blue chips (e.g., `alerts-cheatsheet#e195f2a3`)
- Confidence score percentage

### 4. Test Source Details Panel

#### Click a Source Chip
1. Click on any blue source chip
2. Right side panel slides in
3. Shows citation details
4. Displays chunk content

#### Panel Features
- **Citation**: Shows the exact citation format
- **Content**: Displays the actual document text
- **Close**: X button to close panel
- **Backdrop**: Click outside to close

### 5. Test Error Handling

#### Network Issues
1. Stop the API service: `docker compose stop api`
2. Try asking a question
3. See graceful error toast
4. Restart API: `docker compose start api`

#### Toast Notifications
- **Success**: Green toast for successful responses
- **Error**: Red toast for API failures
- **Auto-dismiss**: Toasts disappear after 5 seconds
- **Manual close**: Click X to dismiss early

## 🔍 Advanced Testing

### Test Different Question Types

#### CPU/Memory Alerts
```
"High memory usage alert 85% for 5 minutes"
"Disk space alert 90% usage"
"Performance alert after deployment"
```

#### Incident Response
```
"P0 incident response emergency"
"Critical incident investigation steps"
"Emergency response procedures"
```

#### Payment Issues
```
"Payment gateway errors"
"Transaction processing issues"
"Refund request handling"
```

### Verify API Integration

#### Check API Health
```bash
curl http://localhost:8000/health
```

#### Test RAG Endpoint
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}'
```

#### Check Index Stats
```bash
curl http://localhost:8000/stats
```

## 🆕 **New: Citation Cleaning & Answer Composition**

### Citation Improvements
The system now automatically cleans and normalizes citations:

#### Before (Raw)
```
"alerts-cheatsheet.md#e195f2a3"
"runbook-payments.md#a2719391"
"docs-slo-policy.md#5ba3d2c3"
```

#### After (Cleaned)
```
"alerts-cheatsheet#e195f2a3"
"payments#a2719391"
"slo-policy#5ba3d2c3"
```

#### What Gets Cleaned
- **File extensions**: `.md`, `.txt`, `.pdf` removed
- **Common prefixes**: `runbook-`, `docs-`, `guide-`, `manual-` removed
- **Duplicates**: Same (filename, chunk_id) pairs deduplicated
- **Meta files**: `readme`, `license`, `changelog` automatically filtered

### Answer Composition
Answers are now composed cleanly without system text:

#### ✅ Good (No Leakage)
```
**First checks:**
• Check for runaway processes
• Review recent deployments

**Why this happens:**
• Infinite loops in application code
```

#### ❌ Removed (System Text)
```
System: Based on the provided information:
Question: High CPU usage alert
Context: 
The answer is:
```

### Test Citation Cleaning
```bash
# Test CPU alert (should show clean citations)
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}' | jq '.citations'

# Test payment issues (should show normalized filenames)
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Payment gateway errors", "context": ""}' | jq '.citations'
```

## 🆕 **NEW: Read-Only Diagnostics Tools**

### Intelligent Tool Routing
The system now automatically suggests and runs relevant diagnostics tools based on query content:

#### CPU & Deployment Issues → Logs
```
Query: "High CPU usage after deployment"
Tools: app logs, nginx logs, system logs
Result: Shows recent log entries or honest errors
```

#### Queue Issues → Queue Depth
```
Query: "Queue backlog processing issues"
Tools: main queue, dlq queue, processing queue, email queue
Result: Shows actual queue depths (15, 3, 0, 7 items)
```

#### Redis/Cache Issues → No Tools
```
Query: "Redis hit rate performance"
Tools: None (specialized monitoring required)
Result: No Diagnostics block shown
```

### Tool Availability & Honesty

#### When Tools Work
- **Log files exist**: Shows last 2-3 lines
- **Queue files exist**: Shows actual depth values
- **Tools configured**: Provides real data

#### When Tools Don't Work
- **Log files missing**: "Log file not found: service.log"
- **Queue tools not configured**: "Queue depth tool not configured for queue"
- **Honest fallbacks**: Suggests manual verification

### Test Diagnostics Tools

#### Test CPU/Deployment Query
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "CPU spike after deploy", "context": ""}' | jq '.answer'
```

Expected: Shows Diagnostics block with log results

#### Test Queue Query
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Queue backlog processing issues", "context": ""}' | jq '.answer'
```

Expected: Shows Diagnostics block with queue depths

#### Test Redis Query
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Redis memory usage", "context": ""}' | jq '.diagnostics'
```

Expected: Returns `null` (no diagnostics run)

### Diagnostics Block Logic

#### ✅ Shows When Tools Ran
- **CPU queries**: Log diagnostics run
- **Queue queries**: Queue depth tools run
- **Database queries**: Log diagnostics run
- **Network queries**: Log diagnostics run

#### ❌ Hidden When No Tools
- **Redis/cache queries**: No specialized tools available
- **General questions**: No relevant diagnostics
- **Tool failures**: Honest about missing tools

## 🆕 **NEW: Knowledge Base Persistence & Ingest Endpoints**

### Persistent File Storage
Files are now uploaded once and stored persistently:

#### File Management
- **Persistent storage**: Files saved to `/app/data/docs/`
- **Hash tracking**: SHA256 hashes computed and stored
- **Manifest file**: `.file_manifest.json` tracks all files
- **Incremental upserts**: Only new/changed files are processed

#### File Hash Manifest
```json
{
  "files": {
    "alerts-cheatsheet.md": {
      "hash": "40ffe8c28caf0c14f3c3b714fce9d52e62bb12084b1a810a49552215023e70be",
      "size": 2921,
      "modified": 1755115843.47058,
      "uploaded_at": 1755115843.47058
    }
  },
  "last_updated": 1755115843.47058
}
```

### New Knowledge Base Endpoints

#### GET /kb/status
Returns knowledge base status:
```bash
curl http://localhost:8000/kb/status
```

Response:
```json
{
  "success": true,
  "files": {
    "docs_count": 4,
    "docs": [...],
    "index_ready": true,
    "last_updated": 1755115843.47058
  },
  "index": {
    "index_exists": true,
    "index_type": "faiss",
    "total_vectors": 98,
    "dimension": 1536
  },
  "overall_status": "ready"
}
```

#### POST /kb/ingest (multipart)
Upload and ingest a file:
```bash
curl -X POST -F "file=@document.md" http://localhost:8000/kb/ingest
```

Response:
```json
{
  "success": true,
  "message": "File document.md uploaded and ingested successfully",
  "filename": "document.md",
  "chunks_count": 5,
  "file_hash": "35764fe64037a9054d98e12e81d9b78ce63f08658773fe083ebb3c7940cad9bf"
}
```

#### POST /kb/refresh
Scan for new/changed files:
```bash
curl -X POST http://localhost:8000/kb/refresh
```

Response:
```json
{
  "success": true,
  "message": "Knowledge base refreshed successfully",
  "files_processed": 0,
  "total_chunks": 0,
  "total_files": 4
}
```

### Incremental Upsert Features

#### Smart File Detection
- **Hash comparison**: Only processes changed files
- **Duplicate prevention**: Creates unique filenames if needed
- **Efficient processing**: Skips unchanged files
- **Automatic cleanup**: Removes orphaned file references

#### File Type Support
- **Markdown**: `.md` files
- **Text**: `.txt` files  
- **PDF**: `.pdf` files (PyMuPDF + PyPDF2 fallback)
- **Validation**: File type checking on upload

### Test Knowledge Base Persistence

#### Test File Upload
```bash
# Create test file
echo "# Test Document\n\nThis is a test." > test-doc.md

# Upload file
curl -X POST -F "file=@test-doc.md" http://localhost:8000/kb/ingest

# Check status
curl http://localhost:8000/kb/status | jq '.files.docs_count'
```

#### Test Restart Persistence
```bash
# Restart API
docker compose restart api

# Wait for startup
sleep 10

# Check if still ready
curl http://localhost:8000/kb/status | jq '.overall_status'
# Should return "ready"

# Test query without re-upload
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}'
```

#### Test Incremental Upsert
```bash
# Upload same file again
curl -X POST -F "file=@test-doc.md" http://localhost:8000/kb/ingest

# Should create test-doc_1.md (duplicate prevention)
# Check file count
curl http://localhost:8000/kb/status | jq '.files.docs_count'
```

### Startup Behavior

#### Automatic Index Initialization
- **ensure_index()**: Called on startup (does not wipe existing index)
- **Index population check**: Only runs ingestion if index is empty
- **File manifest loading**: Automatically loads existing file tracking
- **Graceful startup**: Continues even if some files are missing

#### Persistent State
- **File storage**: Documents persist across restarts
- **Index persistence**: FAISS index saved to disk
- **Hash tracking**: File hashes maintained in manifest
- **Status tracking**: Overall readiness state preserved

## 🆕 **NEW: Sessions & Chat History (Persist Across Refresh)**

### SQLite Database Integration
The system now uses SQLite for persistent session and message storage:

#### Database Structure
- **Location**: `/app/data/app.db`
- **Tables**: `sessions`, `messages`
- **Relationships**: Foreign key constraints with CASCADE delete

#### Session Table
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  message_count INTEGER DEFAULT 0
)
```

#### Messages Table
```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  content TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  citations TEXT,
  confidence REAL,
  diagnostics TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
)
```

### New Session Management Endpoints

#### POST /sessions
Create a new chat session:
```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "CPU Investigation", "description": "Investigating high CPU usage"}'
```

Response:
```json
{
  "id": "09e6cd42-e720-4fa7-a999-2c476225f049",
  "title": "CPU Investigation",
  "description": "Investigating high CPU usage",
  "created_at": "2025-08-14T07:45:23.123456",
  "updated_at": "2025-08-14T07:45:23.123456",
  "message_count": 0
}
```

#### GET /sessions
List all sessions with search and pagination:
```bash
# List all sessions
curl "http://localhost:8000/sessions"

# Search sessions
curl "http://localhost:8000/sessions?search=CPU&limit=10&offset=0"
```

#### GET /sessions/{id}
Get a specific session:
```bash
curl "http://localhost:8000/sessions/09e6cd42-e720-4fa7-a999-2c476225f049"
```

#### PATCH /sessions/{id}
Update session title/description:
```bash
curl -X PATCH "http://localhost:8000/sessions/09e6cd42-e720-4fa7-a999-2c476225f049" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated CPU Investigation"}'
```

#### DELETE /sessions/{id}
Delete a session and all its messages:
```bash
curl -X DELETE "http://localhost:8000/sessions/09e6cd42-e720-4fa7-a999-2c476225f049"
```

#### GET /sessions/{id}/messages
Get messages for a session:
```bash
curl "http://localhost:8000/sessions/09e6cd42-e720-4fa7-a999-2c476225f049/messages?limit=100&offset=0"
```

#### POST /sessions/{id}/export
Export session to Markdown:
```bash
curl -X POST "http://localhost:8000/sessions/09e6cd42-e720-4fa7-a999-2c476225f049/export"
```

Response:
```json
{
  "markdown": "# CPU Investigation\n\n**Session ID:** 09e6cd42-e720-4fa7-a999-2c476225f049\n\n## 👤 User\n\nHigh CPU usage alert...",
  "filename": "session-09e6cd42-cpu-investigation.md"
}
```

### Enhanced Ask Endpoint
The `/ask/structured` endpoint now supports session management:

#### With Session ID
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "What should I check?", "context": "", "session_id": "09e6cd42-e720-4fa7-a999-2c476225f049"}'
```

#### Without Session ID (Auto-create)
```bash
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}'
```

Response includes `session_id`:
```json
{
  "answer": "**First checks:**...",
  "citations": [...],
  "session_id": "auto-generated-session-id",
  "trace_id": "...",
  "confidence": 0.85
}
```

### Frontend Session Management

#### Sidebar Features
- **New Chat Button**: Creates fresh conversation
- **Session List**: Shows all chat sessions with search
- **Session Actions**: Edit title, delete session
- **Dark Mode Toggle**: Switch between light/dark themes
- **Search**: Filter sessions by title or description

#### Session Persistence
- **localStorage**: Remembers last active session
- **URL Routing**: `/new` for new chats, `/{sessionId}` for existing
- **Auto-refresh**: Sessions persist across page refreshes
- **Session Switching**: Load different conversation histories

#### Enhanced Chat Interface
- **Action Buttons**: Regenerate, Copy, Export on hover
- **Quick Prompts**: Common question templates
- **Message History**: Full conversation persistence
- **Source Integration**: Citations and diagnostics preserved

### Test Session Functionality

#### Test Session Creation
```bash
# Create session via API
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session", "description": "Testing session API"}'

# Verify session created
curl "http://localhost:8000/sessions" | jq '.total'
```

#### Test Message Persistence
```bash
# Ask question (creates or uses session)
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question", "context": "", "session_id": "SESSION_ID"}'

# Check messages added
curl "http://localhost:8000/sessions/SESSION_ID/messages" | jq '.total'
```

#### Test Session Export
```bash
# Export session to markdown
curl -X POST "http://localhost:8000/sessions/SESSION_ID/export" | jq '.filename'
```

#### Test Frontend Integration
1. **Open**: http://localhost:3000
2. **Create**: Click "New Chat" button
3. **Ask**: Type a question
4. **Verify**: Session created automatically
5. **Refresh**: Page maintains conversation
6. **Switch**: Use sidebar to change sessions
7. **Export**: Use export button on messages

### Session Statistics
New endpoint for monitoring session usage:

#### GET /session-stats
```bash
curl "http://localhost:8000/session-stats"
```

Response:
```json
{
  "total_sessions": 5,
  "total_messages": 23,
  "recent_sessions": [
    {"date": "2025-08-14", "count": 2},
    {"date": "2025-08-13", "count": 3}
  ],
  "messages_by_role": [
    {"role": "user", "count": 12},
    {"role": "assistant", "count": 11}
  ]
}
```

## 🎨 UI Features Demonstrated

### Chat Interface
- ✅ **Single page**: Clean, focused chat experience
- ✅ **Input & Send**: Type questions, click send button
- ✅ **Messages list**: Scrollable conversation history
- ✅ **Loading states**: Spinner during processing
- ✅ **User avatars**: Different icons for user vs assistant

### Sources Display
- ✅ **Citation chips**: Blue, clickable source buttons
- ✅ **Proper formatting**: `filename#chunk_id` format
- ✅ **Visual hierarchy**: Clear "Sources:" label
- ✅ **Hover effects**: Interactive button states
- ✅ **Clean citations**: Normalized filenames without extensions

### Source Details Panel
- ✅ **Side panel**: Slides in from right
- ✅ **Citation display**: Shows exact citation format
- ✅ **Content rendering**: Displays chunk text
- ✅ **Loading states**: Spinner while fetching content
- ✅ **Close functionality**: Multiple ways to close

### Error Handling
- ✅ **Toast notifications**: Success/error feedback
- ✅ **Graceful degradation**: Handles API failures
- ✅ **User feedback**: Clear error messages
- ✅ **Auto-dismiss**: Timed notification removal

### Session Management
- ✅ **Sidebar**: Session list with search and actions
- ✅ **New Chat**: Create fresh conversations
- ✅ **Session Switching**: Load different chat histories
- ✅ **Dark Mode**: Toggle between light/dark themes
- ✅ **Quick Prompts**: Common question templates
- ✅ **Action Buttons**: Regenerate, Copy, Export on messages

## 🧪 Acceptance Criteria Verification

### ✅ You can ask and see cited answers
- [x] Type questions in chat input
- [x] Send button submits questions
- [x] Assistant responds with structured answers
- [x] Sources are displayed below answers
- [x] Citations show proper format

### ✅ Chips open source text
- [x] Source chips are clickable
- [x] Clicking opens side panel
- [x] Panel shows citation details
- [x] Panel displays chunk content
- [x] Panel can be closed

### ✅ Environment Configuration
- [x] `VITE_API_BASE` environment variable
- [x] Configurable API endpoint
- [x] Graceful fallback to localhost:8000

### ✅ Error Handling
- [x] Toast notifications for errors
- [x] Graceful API failure handling
- [x] User-friendly error messages
- [x] Loading states during processing

### ✅ **NEW: No Instruction Leakage**
- [x] **No system preamble**: Answers start directly with structured content
- [x] **No prompt text**: No "System:", "Question:", "Context:" prefixes
- [x] **Clean composition**: Direct First checks → Why → Diagnostics → Sources format

### ✅ **NEW: Clean Citations**
- [x] **Normalized filenames**: Extensions and prefixes removed
- [x] **Deduplication**: No duplicate (filename, chunk_id) pairs
- [x] **Meta filtering**: README, license, changelog files excluded
- [x] **Consistent format**: `filename#chunk_id` without artifacts

### ✅ **NEW: Read-Only Diagnostics Tools**
- [x] **Light router**: Intelligently suggests relevant tools based on query content
- [x] **CPU & deploy queries**: Prefer logs (app, nginx, system)
- [x] **Queue/DLQ/backlog queries**: Check queue depth (main, dlq, processing, email)
- [x] **Redis/cache queries**: No tools (honest about specialized monitoring needed)
- [x] **Diagnostics block**: Only shown when tools actually ran
- [x] **Honest fallbacks**: Clear about missing tools and manual verification needed

### ✅ **NEW: Knowledge Base Persistence**
- [x] **Upload once**: Files stored persistently in `/app/data/docs/`
- [x] **File hash manifest**: SHA256 hashes tracked in `.file_manifest.json`
- [x] **Incremental upserts**: Only new/changed files processed
- [x] **GET /kb/status**: Returns docs_count, docs[], index_ready
- [x] **POST /kb/ingest**: Multipart file upload and ingestion
- [x] **POST /kb/refresh**: Scan for new/changed files
- [x] **ensure_index()**: Called on startup (does not wipe index)
- [x] **Restart persistence**: Knowledge base ready after restart
- [x] **Queries work**: No re-upload needed after restart

### ✅ **NEW: Sessions & Chat History**
- [x] **SQLite database**: `/app/data/app.db` with sessions and messages tables
- [x] **Session endpoints**: POST/GET/PATCH/DELETE /sessions
- [x] **Message endpoints**: GET /sessions/{id}/messages
- [x] **Enhanced ask**: Accepts session_id, creates if missing, returns it
- [x] **Frontend sidebar**: New Chat, session list, search, rename, delete
- [x] **Dark mode toggle**: Switch between light/dark themes
- [x] **Route handling**: /:sessionId with localStorage persistence
- [x] **Refresh persistence**: Chat history maintained across page refreshes
- [x] **Session switching**: Load different conversation histories
- [x] **Action buttons**: Regenerate, Copy, Export on messages
- [x] **Quick prompts**: Common question templates accessible

### ✅ **NEW: Global Anti-Generic Gate**
- [x] **Banned phrases detection**: Catches generic phrases like "check the documentation", "refer to docs"
- [x] **Actionability minimum**: Enforces at least 3 actionable bullet points across First checks + Fix sections
- [x] **Evidence threshold**: Requires ≥ 2 distinct files cited, OR 1 file with diagnosis & remediation
- [x] **Missing context messages**: Returns specific guidance instead of generic answers when thresholds fail
- [x] **Quality metrics**: Provides detailed scoring (actionable_bullets, evidence_score, distinct_files)
- [x] **Content structure recognition**: Handles multiple formats (First checks, Quick Check, Fix, Remediation)
- [x] **No generic responses**: System never outputs "check the relevant documentation" type answers
- [x] **Configurable thresholds**: Quality standards can be adjusted based on requirements
- [x] **Performance optimized**: Fast quality assessment with minimal overhead
- [x] **Comprehensive logging**: Detailed quality check results for monitoring and debugging

### ✅ **NEW: Document Sectionizer (Domain-Agnostic)**
- [x] **Section detection**: Automatically detects document sections using regex patterns
- [x] **Section classification**: Tags sections as first_checks, fix, validate, policy, gotchas, background
- [x] **Heading recognition**: Supports markdown (# ## ###), ALL CAPS, Title Case, numbered, and bold headings
- [x] **Hierarchical paths**: Builds hpath (e.g., "alerts-cheat-sheet/first-checks") for navigation
- [x] **Content analysis**: Analyzes bullet points, code blocks, links, commands, and metrics
- [x] **Metadata preservation**: Stores section_type + hpath in chunk metadata during ingestion
- [x] **Smart classification**: Refines section types based on content analysis
- [x] **Bullet list preservation**: Maintains bullet point structure in chunks
- [x] **Performance optimized**: Pre-compiled regex patterns for efficient processing
- [x] **Comprehensive reporting**: Provides section summaries and detailed analysis

### ✅ **NEW: Advanced Retrieval Pipeline (Ensemble + Diversity)**
- [x] **Vector + BM25 combination**: Merges semantic and keyword search results
- [x] **MMR diversity selection**: Applies Maximal Marginal Relevance for diverse results
- [x] **Cross-encoder re-ranking**: Optional re-ranking when cross-encoder is available
- [x] **Query rewriting**: Uses generic intent hints to improve recall
- [x] **Diversity constraints**: Enforces coverage across files and section types
- [x] **Score normalization**: Combines and normalizes scores from multiple sources
- [x] **Fallback mechanisms**: Graceful degradation when components fail
- [x] **Retrieval statistics**: Comprehensive reporting on result diversity
- [x] **Performance optimized**: Efficient processing with minimal overhead
- [x] **Configurable weights**: Adjustable balance between relevance and diversity

## 🆕 **NEW: Global Anti-Generic Gate (Works for Any Docs)**

### Quality Enforcement System
The system now includes a comprehensive anti-generic gate that ensures all answers meet strict quality standards before being returned to users.

#### **Banned Generic Phrases**
The gate automatically detects and rejects answers containing generic phrases like:
- "check the relevant documentation"
- "refer to the retrieved documentation" 
- "based on the retrieved context"
- "consult the docs"
- "check the documentation"
- "refer to documentation"
- "see the documentation"
- "review the documentation"
- "look at the documentation"
- "examine the documentation"
- "consult relevant docs"
- "check appropriate documentation"
- "refer to appropriate docs"
- "based on available information"
- "according to the context"
- "as per the retrieved information"
- "from the provided context"
- "based on what was found"
- "according to what was retrieved"
- "based on the available context"

#### **Quality Thresholds**
Answers must meet these minimum standards:

1. **Actionability Minimum**: At least 3 actionable bullet points across First checks + Fix sections
2. **Evidence Threshold**: ≥ 2 distinct files cited, OR 1 file containing both diagnosis & remediation
3. **File Coverage**: ≥ 2 distinct files cited for comprehensive coverage

#### **Content Structure Recognition**
The gate recognizes multiple content formats:
- **First Checks**: `**First checks:**`, `**Quick Check:**`, `**Quick Checks:**`, `**Initial Checks:**`, `**First Response:**`, `**Immediate Actions:**`
- **Fix Sections**: `**Fix:**`, `**Remediation:**`, `**Solution:**`, `**Resolution:**`, `**Steps:**`
- **Bullet Points**: `•`, `-`, `*` markers
- **Numbered Lists**: `1.`, `2.`, `3.` sequences

#### **Missing Context Messages**
When thresholds fail, the system returns specific missing context messages instead of generic answers:

```
**Missing Context Detected**

Your question requires more specific information than what's currently available in the knowledge base. 

**Missing Sections:** First Response/Diagnostics

**To get a specific, actionable answer, please upload documentation covering:**
- **First Response/Diagnostics**: Step-by-step investigation procedures
- **Remediation/Fix**: Specific commands, configuration changes, or procedures
- **Validation/SLA**: How to verify the fix worked and measure success

**Current Answer Quality:**
- Actionable bullets: 1/3 required
- Evidence score: 5/2 required  
- Distinct files: 3/2 required

Upload the missing documentation to receive a specific, cited response instead of generic guidance.
```

### Test Anti-Generic Gate Functionality

#### **Test High-Quality Answers (Should Pass)**
```bash
# CPU alert question - should pass with high scores
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert 80% for 5 minutes", "context": ""}' | jq '.quality_gate'

# Expected: passes with actionable_bullets: 11+, evidence_score: 5+, distinct_files: 4+
```

#### **Test Memory Usage Questions (Should Pass)**
```bash
# Memory alert question - should pass with good scores
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High memory usage alert 90% for 10 minutes, what are the first steps?", "context": ""}' | jq '.quality_gate'

# Expected: passes with actionable_bullets: 6+, evidence_score: 5+, distinct_files: 3+
```

#### **Test Payment Issues (Should Pass)**
```bash
# Payment gateway question - should pass with comprehensive content
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Payment gateway errors, customers cannot complete transactions", "context": ""}' | jq '.quality_gate'

# Expected: passes with actionable_bullets: 7+, evidence_score: 5+, distinct_files: 4+
```

#### **Test Generic Questions (May Pass or Fail Based on Content)**
```bash
# Generic monitoring question - may pass if seed docs contain good content
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about monitoring", "context": ""}' | jq '.quality_gate'

# Database configuration question - may pass if seed docs contain relevant procedures
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I configure a database?", "context": ""}' | jq '.quality_gate'
```

#### **Test Banned Phrase Detection**
```bash
# Test the banned phrase detection directly
docker compose exec api python -c "
from app.services.anti_generic_gate import AntiGenericGate
gate = AntiGenericGate()
test_answer = 'Based on the retrieved context, you should check the relevant documentation for more information.'
result = gate.check_answer_quality(test_answer, ['file1#chunk1'], None)
print('Banned phrases found:', result['metrics']['generic_phrases_found'])
print('Passes gate:', result['passes_gate'])
print('Issues:', result['issues'])
"

# Expected: fails with 2 banned phrases detected
```

### Quality Gate Response Structure

#### **Successful Answers Include**
```json
{
  "answer": "**First checks:**\n• Check for runaway processes\n• Review recent deployments\n...",
  "citations": ["alerts-cheatsheet#chunk1", "incident-response#chunk2"],
  "quality_gate": {
    "passed": true,
    "score": 0,
    "issues": [],
    "metrics": {
      "actionable_bullets": 11,
      "evidence_score": 5,
      "distinct_files": 4,
      "generic_phrases_found": 0
    }
  }
}
```

#### **Rejected Answers Include**
```json
{
  "answer": "**Missing Context Detected**\n\nYour question requires more specific information...",
  "citations": [],
  "quality_gate": {
    "passed": false,
    "score": -1,
    "issues": ["Insufficient actionable content: 0/3 bullets required"],
    "metrics": {
      "actionable_bullets": 0,
      "evidence_score": 5,
      "distinct_files": 3,
      "generic_phrases_found": 0
    }
  }
}
```

### Anti-Generic Gate Benefits

#### **For Users**
- **No Generic Answers**: Never receive "check the documentation" responses
- **Actionable Content**: All answers contain specific, implementable steps
- **Clear Guidance**: Missing context messages explain exactly what documentation is needed
- **Quality Assurance**: Consistent answer quality across all questions

#### **For Content Managers**
- **Quality Metrics**: Detailed scoring for answer quality
- **Content Gaps**: Clear identification of missing documentation sections
- **Continuous Improvement**: Data-driven insights for knowledge base enhancement
- **Standards Enforcement**: Automatic quality control without manual review

#### **For System Administrators**
- **Configurable Thresholds**: Adjustable quality standards based on requirements
- **Comprehensive Logging**: Detailed quality check results for monitoring
- **Performance Impact**: Minimal overhead with efficient regex-based detection
- **Error Handling**: Graceful fallbacks when quality checks encounter issues

### Implementation Details

#### **Service Integration**
- **RAG Service**: Integrated into answer generation pipeline
- **Quality Enforcement**: Applied before returning any response
- **Metrics Collection**: Comprehensive quality scoring and reporting
- **Logging**: Detailed quality check results for debugging

#### **Content Analysis**
- **Pattern Recognition**: Multiple section format support
- **Bullet Point Counting**: Accurate detection of actionable content
- **Citation Analysis**: File coverage and evidence scoring
- **Generic Phrase Detection**: Comprehensive banned phrase library

#### **Performance Optimization**
- **Compiled Regex**: Pre-compiled patterns for efficient matching
- **Early Termination**: Stop processing when thresholds are met
- **Caching**: Efficient quality check results
- **Minimal Overhead**: Fast quality assessment without impacting response time

### Testing and Validation

#### **Quality Gate Testing**
```bash
# Test various question types
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}' | jq '.quality_gate.passed'

# Test banned phrase detection
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Generic question about monitoring", "context": ""}' | jq '.quality_gate.metrics.generic_phrases_found'

# Test actionable content counting
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "Memory usage troubleshooting", "context": ""}' | jq '.quality_gate.metrics.actionable_bullets'
```

#### **Validation Commands**
```bash
# Check quality gate service directly
docker compose exec api python -c "
from app.services.anti_generic_gate import AntiGenericGate
gate = AntiGenericGate()
print('Anti-generic gate initialized successfully')
print('Banned phrases loaded:', len(gate.banned_phrases))
print('Quality thresholds:')
print(f'  - Min actionable bullets: {gate.min_actionable_bullets}')
print(f'  - Min distinct files: {gate.min_distinct_files}')
print(f'  - Min evidence threshold: {gate.min_evidence_threshold}')
"

# Test quality check function
docker compose exec api python -c "
from app.services.anti_generic_gate import AntiGenericGate
gate = AntiGenericGate()
test_answer = '**First checks:**\n• Check process list\n• Review deployments\n\n**Why this happens:**\n• Infinite loops\n• Database issues'
result = gate.check_answer_quality(test_answer, ['file1#chunk1', 'file2#chunk2'], None)
print('Quality check result:', result)
"
```

### Troubleshooting Quality Gate Issues

#### **Common Issues**
1. **Answers Always Failing**: Check if content extraction logic matches document structure
2. **Banned Phrases Not Detected**: Verify regex patterns are correctly compiled
3. **Actionable Bullets Counted Incorrectly**: Check section pattern matching
4. **Quality Scores Inconsistent**: Review evidence scoring algorithm

#### **Debug Commands**
```bash
# Check quality gate logs
docker compose logs api | grep "Anti-generic gate"

# Test specific quality checks
docker compose exec api python -c "
from app.services.anti_generic_gate import AntiGenericGate
gate = AntiGenericGate()
# Test specific functionality here
"

# Verify content structure
docker compose exec api python -c "
from app.services.faiss_service import FAISSService
fs = FAISSService()
print('Sample chunk content:')
print(fs.metadata[0]['content'][:300] if fs.metadata else 'No metadata')
"
```

### Quality Gate Configuration

#### **Environment Variables**
```bash
# Quality thresholds (set in anti_generic_gate.py)
MIN_ACTIONABLE_BULLETS=3
MIN_DISTINCT_FILES=2
MIN_EVIDENCE_THRESHOLD=2
```

#### **Customization Options**
- **Adjust Thresholds**: Modify minimum requirements based on use case
- **Add Banned Phrases**: Extend the banned phrase library
- **Custom Patterns**: Add new content structure recognition patterns
- **Quality Scoring**: Implement custom quality scoring algorithms

---

**🎯 Anti-Generic Gate Complete!** The system now enforces strict quality standards, ensuring users never receive generic "check the documentation" responses. All answers must contain specific, actionable content with proper evidence and file coverage.

---

## 🆕 **NEW: Document Sectionizer (Domain-Agnostic) at Ingest**

### Intelligent Section Detection & Classification
The system now includes a comprehensive sectionizer that automatically detects, classifies, and tags document sections during ingestion, making content more structured and searchable.

#### **Section Types Detected**
The sectionizer automatically categorizes content into these domain-agnostic types:

1. **`first_checks`**: Initial investigation steps
   - Patterns: "First checks", "Quick Check", "Initial Checks", "First Response", "Immediate Actions"
   - Examples: "First checks:", "Quick Check:", "Emergency Response:"

2. **`fix`**: Remediation and resolution steps
   - Patterns: "Fix", "Remediation", "Solution", "Resolution", "Steps"
   - Examples: "Fix:", "Remediation:", "Corrective Actions:"

3. **`validate`**: Verification and confirmation steps
   - Patterns: "Validate", "Verification", "Confirm", "Check", "Test"
   - Examples: "Validation:", "Post-fix Checks:", "Confirmation Steps:"

4. **`policy`**: Rules, procedures, and standards
   - Patterns: "Policy", "Procedure", "Guideline", "Standard", "Rule"
   - Examples: "Policy:", "Compliance:", "Governance:"

5. **`gotchas`**: Warnings, cautions, and important notes
   - Patterns: "Gotcha", "Common Mistakes", "Pitfalls", "Warning", "Caution"
   - Examples: "Watch Out:", "Important Notes:", "Critical Notes:"

6. **`background`**: Context, overview, and explanations
   - Patterns: "Background", "Overview", "Introduction", "Context", "Why"
   - Examples: "What is:", "Rationale:", "Definition:"

#### **Heading Recognition Patterns**
The sectionizer supports multiple heading formats:

- **Markdown Headings**: `# ## ### #### ######`
- **ALL CAPS Headings**: `HIGH CPU USAGE`, `MEMORY ALERTS`
- **Title Case Headings**: `First Response`, `Quick Checks`
- **Numbered Headings**: `1. First Steps`, `2. Investigation`
- **Lettered Headings**: `A. Background`, `B. Procedure`
- **Bold Headings**: `**Important Note**`, `**Warning**`
- **Colon Headings**: `FIRST CHECKS:`, `VALIDATION:`

#### **Hierarchical Path Building**
Each section gets a hierarchical path (hpath) for navigation:

```
# Alerts Cheat Sheet (level 1)
## High CPU Usage (level 2)
### First Checks (level 3)
### Quick Fix (level 3)
### Validation (level 3)

Results in hpaths:
- alerts-cheat-sheet
- alerts-cheat-sheet/high-cpu-usage
- alerts-cheat-sheet/high-cpu-usage/first-checks
- alerts-cheat-sheet/high-cpu-usage/quick-fix
- alerts-cheat-sheet/high-cpu-usage/validation
```

#### **Content Analysis & Metadata**
The sectionizer analyzes each section and enriches metadata:

- **Bullet Point Counting**: Tracks actionable content (•, -, *, numbered lists)
- **Code Block Detection**: Identifies command examples and code snippets
- **Link Analysis**: Counts markdown links and URLs
- **Command Detection**: Recognizes shell commands, tools, and utilities
- **Metrics Detection**: Identifies measurements, thresholds, and status indicators
- **Content Length**: Measures section size and complexity

### Test Sectionizer Functionality

#### **Test Section Detection**
```bash
# Test the sectionizer directly
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
test_content = '# Test Document\n\n## First Checks\n- Check process list\n- Review deployments\n\n## Quick Fix\n- Restart service\n- Clear cache\n\n## Validation\n- Verify service status\n- Check metrics'
sections = s.detect_sections(test_content)
print(f'Sections detected: {len(sections)}')
for section in sections:
    print(f'- {section.title}: {section.section_type} (level {section.level})')
"

# Expected output:
# Sections detected: 4
# - Test Document: validate (level 1)
# - First Checks: first_checks (level 2)
# - Quick Fix: fix (level 2)
# - Validation: validate (level 2)
```

#### **Test Document Processing with Sections**
```bash
# Test document processor with section detection
docker compose exec api python -c "
from app.services.document_processor import DocumentProcessor
dp = DocumentProcessor()
test_content = '# Test Document\n\n## First Checks\n- Check process list\n- Review deployments\n\n## Quick Fix\n- Restart service\n- Clear cache\n\n## Validation\n- Verify service status\n- Check metrics'
result = dp.process_document('test.md', test_content)
print(f'Chunks: {result["total_chunks"]}')
print(f'Sections: {result["total_sections"]}')
print('Section summary:', result['section_summary'])
"

# Expected output shows section analysis and chunk creation
```

#### **Test Real Document Analysis**
```bash
# Analyze existing documents for sections
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
content = open('/app/data/docs/alerts-cheatsheet.md').read()
sections = s.detect_sections(content)
print(f'Detected {len(sections)} sections')
summary = s.get_section_summary(sections)
print('Section types:', summary['section_types'])
print('Content stats:', summary['content_stats'])
"

# Expected output shows comprehensive section analysis
```

### Sectionizer Response Structure

#### **Section Object Structure**
```python
@dataclass
class Section:
    title: str                    # Section title
    section_type: str             # Classified type (first_checks, fix, etc.)
    level: int                    # Heading level (1-6)
    hpath: str                    # Hierarchical path
    start_line: int               # Starting line number
    end_line: int                 # Ending line number
    content: str                  # Section content
    metadata: Dict[str, Any]      # Enhanced metadata
```

#### **Enhanced Metadata Fields**
```python
metadata = {
    'section_type': 'first_checks',
    'hpath': 'alerts-cheat-sheet/high-cpu-usage/first-checks',
    'level': 3,
    'title': 'First Checks',
    'start_line': 15,
    'end_line': 25,
    'bullet_points': 4,
    'code_blocks': 1,
    'links': 0,
    'content_length': 156,
    'has_commands': True,
    'has_metrics': False
}
```

#### **Chunk Metadata with Section Info**
```python
chunk_metadata = {
    'filename': 'alerts-cheatsheet.md',
    'chunk_id': 'alerts-cheatsheet_0_50',
    'start_line': 0,
    'end_line': 50,
    'line_count': 51,
    'content_length': 1250,
    'section_type': 'first_checks',
    'section_hpath': 'alerts-cheat-sheet/high-cpu-usage/first-checks',
    'all_section_types': ['first_checks', 'background'],
    'all_hierarchy_paths': ['alerts-cheat-sheet', 'alerts-cheat-sheet/high-cpu-usage/first-checks'],
    'has_commands': True,
    'has_metrics': False,
    'total_bullet_points': 4,
    'total_code_blocks': 1
}
```

### Sectionizer Benefits

#### **For Content Management**
- **Automatic Organization**: Documents automatically structured by content type
- **Consistent Classification**: Standardized section types across all documents
- **Hierarchical Navigation**: Easy navigation through document structure
- **Content Discovery**: Quick identification of relevant sections

#### **For Search & Retrieval**
- **Semantic Search**: Search within specific section types (e.g., "fix steps for CPU issues")
- **Context-Aware Results**: Results include section context and hierarchy
- **Better Relevance**: Chunks carry section type information for improved ranking
- **Structured Queries**: Query by section type, hierarchy, or content characteristics

#### **For Anti-Generic Gate**
- **Enhanced Quality Assessment**: Section types provide context for quality scoring
- **Better Actionability Detection**: Identify actionable content by section type
- **Improved Evidence Scoring**: Section metadata enhances evidence assessment
- **Contextual Quality Metrics**: Quality scores consider section context

#### **For User Experience**
- **Structured Answers**: Responses can reference specific section types
- **Better Citations**: Citations include section context and hierarchy
- **Navigation Support**: Users can navigate to specific document sections
- **Content Understanding**: Clear understanding of document structure and purpose

### Implementation Details

#### **Service Integration**
- **Document Processor**: Integrated into document ingestion pipeline
- **Section Detection**: Applied during document processing
- **Metadata Enrichment**: Section information stored in chunk metadata
- **FAISS Integration**: Section metadata preserved in vector index

#### **Performance Optimization**
- **Pre-compiled Patterns**: Regex patterns compiled once for efficiency
- **Early Termination**: Stop processing when thresholds are met
- **Minimal Overhead**: Fast section detection without impacting ingestion
- **Memory Efficient**: Section objects optimized for minimal memory usage

#### **Error Handling**
- **Graceful Fallbacks**: Default to 'background' for unclassified sections
- **Robust Parsing**: Handles malformed headings and edge cases
- **Logging**: Comprehensive logging for debugging and monitoring
- **Validation**: Section data validation before storage

### Testing and Validation

#### **Section Detection Testing**
```bash
# Test various heading formats
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
test_cases = [
    '# Markdown Heading',
    'ALL CAPS HEADING',
    'Title Case Heading',
    '1. Numbered Heading',
    'A. Lettered Heading',
    '**Bold Heading**',
    'HEADING WITH COLON:'
]
for test in test_cases:
    result = s._detect_heading(test)
    print(f'{test} -> {result}')
"
```

#### **Section Classification Testing**
```bash
# Test section type classification
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
test_titles = [
    'First Checks',
    'Quick Fix',
    'Validation Steps',
    'Policy Guidelines',
    'Common Gotchas',
    'Background Information'
]
for title in test_titles:
    section_type = s._classify_section(title)
    print(f'{title} -> {section_type}')
"
```

#### **Content Analysis Testing**
```bash
# Test content analysis features
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
test_content = '## Test Section\n- Bullet point 1\n- Bullet point 2\n`ssh user@host`\nCheck 95% CPU usage'
sections = s.detect_sections(test_content)
for section in sections:
    print(f'Section: {section.title}')
    print(f'  Bullet points: {section.metadata["bullet_points"]}')
    print(f'  Code blocks: {section.metadata["code_blocks"]}')
    print(f'  Has commands: {section.metadata["has_commands"]}')
    print(f'  Has metrics: {section.metadata["has_metrics"]}')
"
```

### Troubleshooting Sectionizer Issues

#### **Common Issues**
1. **Sections Not Detected**: Check heading format compatibility
2. **Incorrect Classification**: Verify section type patterns
3. **Metadata Missing**: Check document processor integration
4. **Performance Issues**: Review regex pattern complexity

#### **Debug Commands**
```bash
# Check sectionizer initialization
docker compose exec api python -c "
from app.services.sectionizer import Sectionizer
s = Sectionizer()
print('Patterns loaded:', len(s.section_patterns))
print('Section types:', list(s.section_patterns.keys()))
print('Compiled patterns:', len(s.compiled_patterns))
"

# Test specific document processing
docker compose exec api python -c "
from app.services.document_processor import DocumentProcessor
dp = DocumentProcessor()
# Test with specific document content
"

# Verify section metadata in chunks
docker compose exec api python -c "
from app.services.faiss_service import FAISSService
fs = FAISSService()
if hasattr(fs, 'metadata') and fs.metadata:
    chunk = fs.metadata[0]
    if isinstance(chunk, dict):
        print('Section type:', chunk.get('section_type', 'unknown'))
        print('Section hpath:', chunk.get('section_hpath', 'unknown'))
        print('All section types:', chunk.get('all_section_types', []))
"
```

### Sectionizer Configuration

#### **Environment Variables**
```bash
# Chunk configuration (affects section processing)
CHUNK_SIZE=800          # Target chunk size in characters
CHUNK_OVERLAP=100       # Overlap between chunks
```

#### **Customization Options**
- **Add Section Types**: Extend the section type library
- **Custom Patterns**: Add new heading recognition patterns
- **Classification Rules**: Implement custom section classification logic
- **Metadata Fields**: Add new content analysis features

---

**🎯 Sectionizer Complete!** The system now automatically detects, classifies, and tags document sections during ingestion, providing rich metadata that enhances search, retrieval, and quality assessment. All chunks now carry section_type and hpath information, making content more structured and navigable.

---

## 🆕 **NEW: Advanced Retrieval Pipeline (Ensemble + Diversity)**

### Intelligent Multi-Strategy Retrieval
The system now includes a sophisticated retrieval pipeline that combines multiple search strategies to provide diverse, high-quality results that naturally cite multiple files and sections.

#### **Retrieval Strategy Components**

1. **Vector Search (60% weight)**: Semantic similarity using FAISS embeddings
   - **Purpose**: Find semantically relevant content
   - **Strengths**: Understands context and meaning
   - **Use Case**: Primary relevance scoring

2. **BM25 Search (40% weight)**: Keyword-based retrieval using BM25 algorithm
   - **Purpose**: Improve recall for specific terms and phrases
   - **Strengths**: Better keyword matching and exact term retrieval
   - **Use Case**: Secondary relevance scoring

3. **MMR Diversity Selection**: Maximal Marginal Relevance algorithm
   - **Purpose**: Balance relevance with result diversity
   - **Lambda**: 0.7 (70% relevance, 30% diversity)
   - **Use Case**: Ensure diverse coverage across files and sections

4. **Cross-Encoder Re-ranking**: Optional neural re-ranking
   - **Purpose**: Fine-tune result ordering when available
   - **Fallback**: Gracefully skips if not available
   - **Use Case**: Enhanced result quality

#### **Query Rewriting with Intent Hints**
The pipeline automatically expands queries using domain-specific intent hints to improve recall:

- **CPU Intent**: `cpu`, `processor`, `load`, `usage`, `performance`, `spike`, `high`
  - **Expansion**: Adds "performance", "monitoring", "metrics"
- **Latency Intent**: `latency`, `response`, `time`, `slow`, `delay`, `wait`
  - **Expansion**: Adds "response time", "performance", "bottleneck"
- **Cache Intent**: `cache`, `redis`, `memcached`, `hit`, `miss`, `eviction`
  - **Expansion**: Adds "redis", "memcached", "performance"
- **Queue Intent**: `queue`, `backlog`, `depth`, `processing`, `dlq`, `dead letter`
  - **Expansion**: Adds "backlog", "processing", "throughput"
- **Pool Intent**: `pool`, `connection`, `thread`, `worker`, `process`, `resource`
  - **Expansion**: Adds "resources", "scalability", "performance"
- **Memory Intent**: `memory`, `ram`, `swap`, `leak`, `usage`, `allocation`
  - **Expansion**: Adds "ram", "allocation", "leak"
- **Disk Intent**: `disk`, `storage`, `space`, `io`, `throughput`, `latency`
  - **Expansion**: Adds "storage", "io", "throughput"
- **Network Intent**: `network`, `bandwidth`, `packet`, `drop`, `timeout`, `connection`
  - **Expansion**: Adds "bandwidth", "connectivity", "timeout"

#### **Diversity Constraints & Targets**
The pipeline enforces diversity to ensure comprehensive coverage:

- **File Diversity**: Target 3+ distinct files
- **Section Type Coverage**: At least 2 different section types
- **Preferred Section Types**: `first_checks`, `fix`, `validate`, `policy`
- **Content Diversity**: Mix of commands, metrics, and procedural content

### Test Retrieval Pipeline Functionality

#### **Test Query Rewriting**
```bash
# Test query expansion with intent hints
docker compose exec api python -c "
from app.services.retrieval import RetrievalPipeline
rp = RetrievalPipeline()
test_queries = [
    'High CPU usage alert 80% for 5 minutes',
    'Database connection timeout error',
    'Redis cache hit rate dropping',
    'Queue backlog increasing rapidly'
]
for query in test_queries:
    rewritten = rp._rewrite_query_with_intent(query)
    print(f'Original: {query}')
    print(f'Rewritten: {rewritten}')
    print('---')
"

# Expected output shows query expansion with relevant terms
```

#### **Test Diversity Retrieval**
```bash
# Test diverse retrieval across multiple files
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert 80% for 5 minutes", "context": ""}' \
  | jq '.retrieval_stats'

# Expected output shows:
# - Multiple files covered
# - Diverse section types
# - Score distribution across results
```

#### **Test Retrieval Pipeline Configuration**
```bash
# Check retrieval pipeline settings
docker compose exec api python -c "
from app.services.retrieval import RetrievalPipeline
rp = RetrievalPipeline()
print('Vector weight:', rp.vector_weight)
print('BM25 weight:', rp.bm25_weight)
print('MMR lambda:', rp.mmr_lambda)
print('Target diversity:', rp.target_diversity)
print('Intent hints:', list(rp.intent_hints.keys()))
"

# Expected output shows pipeline configuration
```

### Retrieval Pipeline Response Structure

#### **Retrieval Statistics**
```json
{
  "retrieval_stats": {
    "total_results": 8,
    "files_covered": [
      "alerts-cheatsheet.md",
      "incident-response.md",
      "payments-runbook.md",
      "slo-policy.md"
    ],
    "section_types": [
      "first_checks",
      "fix",
      "validate",
      "policy"
    ],
    "score_distribution": {
      "min": 0.25,
      "max": 0.85,
      "mean": 0.55
    }
  }
}
```

#### **Enhanced Quality Gate Response**
```json
{
  "quality_gate": {
    "passed": true,
    "score": 2,
    "issues": [],
    "metrics": {
      "actionable_bullets": 8,
      "evidence_score": 5,
      "distinct_files": 4,
      "generic_phrases_found": 0
    }
  },
  "retrieval_stats": {
    "total_results": 8,
    "files_covered": ["file1.md", "file2.md", "file3.md", "file4.md"],
    "section_types": ["first_checks", "fix", "validate"],
    "score_distribution": {"min": 0.25, "max": 0.85, "mean": 0.55}
  }
}
```

### Retrieval Pipeline Benefits

#### **For Search Quality**
- **Better Recall**: BM25 catches keyword-specific content
- **Semantic Understanding**: Vector search finds contextually relevant content
- **Diverse Coverage**: MMR ensures results span multiple files and sections
- **Improved Relevance**: Cross-encoder fine-tunes result ordering

#### **For User Experience**
- **Natural Citations**: Results naturally cite multiple files and sections
- **Comprehensive Coverage**: Users get information from various sources
- **Contextual Understanding**: Different perspectives on the same topic
- **Actionable Information**: Mix of diagnostic, fix, and validation content

#### **For Content Discovery**
- **Cross-File Insights**: Connect information across different documents
- **Section Type Coverage**: Ensure users see different types of content
- **Hierarchical Navigation**: Navigate through document structures
- **Related Content**: Discover relevant information in unexpected places

### Implementation Details

#### **Pipeline Architecture**
```
Query Input
    ↓
Query Rewriting (Intent Hints)
    ↓
Vector Search (FAISS)
    ↓
BM25 Search (Keyword)
    ↓
Score Merging & Normalization
    ↓
Cross-Encoder Re-ranking (Optional)
    ↓
MMR Diversity Selection
    ↓
Diversity Constraint Enforcement
    ↓
Final Results
```

#### **Score Combination Strategy**
- **Vector Score**: Normalized to [0, 1] range
- **BM25 Score**: Normalized to [0, 1] range
- **Combined Score**: `(vector_score × 0.6) + (bm25_score × 0.4)`
- **Final Ranking**: Combined scores used for MMR selection

#### **MMR Algorithm Implementation**
- **Relevance**: Combined score from vector + BM25
- **Diversity**: Feature-based similarity calculation
- **MMR Score**: `λ × relevance + (1-λ) × diversity`
- **Selection**: Iterative selection of most diverse results

#### **Feature-Based Diversity Calculation**
```python
diversity_features = {
    'filename': 0.4,        # High weight for file diversity
    'section_type': 0.3,    # Medium weight for section diversity
    'content_length': 0.1,  # Low weight for content variation
    'has_commands': 0.1,    # Low weight for command diversity
    'has_metrics': 0.1      # Low weight for metrics diversity
}
```

### Testing and Validation

#### **Diversity Testing**
```bash
# Test diversity across different query types
test_queries = [
    "CPU performance issues",
    "Database connection problems", 
    "Cache hit rate optimization",
    "Queue processing bottlenecks"
]

for query in test_queries:
    response = curl -X POST "http://localhost:8000/ask/structured" \
      -H "Content-Type: application/json" \
      -d "{\"question\": \"$query\", \"context\": \"\"}"
    
    # Check retrieval stats for diversity
    retrieval_stats = response.retrieval_stats
    print(f"Query: {query}")
    print(f"Files: {len(retrieval_stats.files_covered)}")
    print(f"Section types: {len(retrieval_stats.section_types)}")
    print("---")
```

#### **Performance Testing**
```bash
# Test retrieval pipeline performance
docker compose exec api python -c "
import time
from app.services.retrieval import RetrievalPipeline
from app.services.faiss_service import FAISSService

rp = RetrievalPipeline()
fs = FAISSService()

# Test query
query = 'High CPU usage alert 80% for 5 minutes'

# Time the retrieval
start_time = time.time()
results = rp.retrieve_diverse_results(query, fs, top_k=8)
end_time = time.time()

print(f'Retrieval time: {end_time - start_time:.3f} seconds')
print(f'Results retrieved: {len(results)}')
print(f'Files covered: {len(set(r._extract_chunk_features(chunk)["filename"] for chunk, _ in results))}')
"
```

#### **Fallback Testing**
```bash
# Test fallback mechanisms
docker compose exec api python -c "
from app.services.retrieval import RetrievalPipeline
rp = RetrievalPipeline()

# Test with invalid FAISS service
try:
    results = rp.retrieve_diverse_results('test query', None, top_k=5)
    print('Fallback working:', len(results) > 0)
except Exception as e:
    print('Fallback failed:', e)
"
```

### Troubleshooting Retrieval Issues

#### **Common Issues**
1. **Low Diversity**: Check diversity constraints and MMR lambda
2. **Poor Recall**: Verify query rewriting and intent hints
3. **Performance Issues**: Review BM25 document processing
4. **Score Imbalance**: Adjust vector/BM25 weights

#### **Debug Commands**
```bash
# Check retrieval pipeline configuration
docker compose exec api python -c "
from app.services.retrieval import RetrievalPipeline
rp = RetrievalPipeline()
print('Configuration:', {
    'vector_weight': rp.vector_weight,
    'bm25_weight': rp.bm25_weight,
    'mmr_lambda': rp.mmr_lambda,
    'target_diversity': rp.target_diversity
})
"

# Test individual components
docker compose exec api python -c "
from app.services.retrieval import RetrievalPipeline
rp = RetrievalPipeline()

# Test query rewriting
query = 'High CPU usage alert'
rewritten = rp._rewrite_query_with_intent(query)
print(f'Query rewriting: {query} -> {rewritten}')

# Test intent hints
print('Intent hints:', list(rp.intent_hints.keys()))
"
```

### Retrieval Pipeline Configuration

#### **Environment Variables**
```bash
# Retrieval pipeline configuration
VECTOR_WEIGHT=0.6          # Weight for vector search results
BM25_WEIGHT=0.4            # Weight for BM25 search results
MMR_LAMBDA=0.7             # MMR diversity vs relevance trade-off
MAX_RERANK_CANDIDATES=20   # Maximum candidates for cross-encoder re-ranking
```

#### **Customization Options**
- **Adjust Weights**: Balance vector vs BM25 importance
- **Modify Lambda**: Tune diversity vs relevance trade-off
- **Add Intent Hints**: Extend domain-specific query expansion
- **Custom Diversity**: Implement custom diversity constraints

---

**🎯 Retrieval Pipeline Complete!** The system now provides intelligent, diverse retrieval that naturally cites multiple files and sections. The ensemble approach combining vector search, BM25, and MMR ensures comprehensive coverage while maintaining relevance, and the query rewriting with intent hints significantly improves recall across different domains.

---

## 🆕 **NEW: Intelligent Response Planner (Actionable Bullet Extraction)**

### Smart Content Planning & Organization
The system now includes an intelligent planner that extracts actionable bullets from retrieved chunks and organizes them into structured, traceable responses with proper provenance tracking.

#### **Planner Core Functionality**

1. **Actionable Bullet Extraction**: Identifies imperative content using regex patterns
   - **Purpose**: Extract actionable steps from document chunks
   - **Patterns**: 9 comprehensive verb patterns covering all action types
   - **Use Case**: Convert raw content into structured action items

2. **Section Classification**: Automatically categorizes bullets by intent
   - **Purpose**: Organize content into logical sections
   - **Sections**: `first_checks`, `fix`, `validate`
   - **Use Case**: Structure responses for different question types

3. **Provenance Tracking**: Maintains source information for every bullet
   - **Purpose**: Enable traceable citations and source verification
   - **Data**: Source file, chunk ID, confidence score, metadata
   - **Use Case**: Support quality gates and citation generation

4. **Quality Assessment**: Evaluates bullet content quality
   - **Purpose**: Identify high-value actionable content
   - **Metrics**: Commands, metrics, content length, relevance
   - **Use Case**: Prioritize bullets for response composition

#### **Action Verb Patterns**
The planner recognizes 9 comprehensive verb categories:

- **Primary Actions**: `Check`, `Verify`, `Review`, `Set`, `Increase`, `Scale`, `Rollback`, `Pin`, `Pre-warm`, `Move`, `Cap`, `Raise`, `Switch`
- **Service Management**: `Restart`, `Restore`, `Clear`, `Flush`, `Reset`, `Reload`, `Refresh`, `Update`, `Upgrade`, `Downgrade`
- **Configuration**: `Enable`, `Disable`, `Configure`, `Tune`, `Optimize`, `Adjust`, `Modify`, `Change`, `Replace`, `Remove`
- **Monitoring**: `Monitor`, `Watch`, `Track`, `Log`, `Alert`, `Notify`, `Report`, `Document`, `Test`, `Validate`
- **Connection Management**: `Connect`, `Disconnect`, `Bind`, `Unbind`, `Mount`, `Unmount`, `Attach`, `Detach`, `Link`, `Unlink`
- **Process Control**: `Start`, `Stop`, `Pause`, `Resume`, `Suspend`, `Kill`, `Terminate`, `Abort`, `Cancel`, `Skip`
- **Resource Management**: `Add`, `Remove`, `Insert`, `Delete`, `Create`, `Destroy`, `Build`, `Deploy`, `Install`, `Uninstall`
- **Conditional Actions**: `Check if`, `Verify that`, `Ensure that`, `Make sure`, `Confirm that`
- **Execution**: `Run`, `Execute`, `Launch`, `Invoke`, `Call`, `Trigger`, `Initiate`, `Begin`, `Commence`, `Start`

#### **Section Classification Patterns**
The planner automatically categorizes content using pattern matching:

- **First Checks**: `first checks`, `quick checks`, `initial checks`, `immediate actions`, `first response`, `emergency response`, `urgent actions`, `initial response`, `first steps`, `immediate steps`, `diagnosis`, `investigation`
- **Fix Steps**: `fix(es)`, `remediation`, `resolution`, `solution`, `corrective actions`, `repair`, `resolve`, `correct`, `fix steps`, `remediation steps`, `steps to resolve`, `how to fix`
- **Validate Steps**: `validate`, `verification`, `confirm`, `check`, `test`, `verify`, `validation steps`, `verification steps`, `confirmation steps`, `post fix checks`, `how to verify`, `ensure resolution`

#### **Bullet Point Detection**
The planner recognizes multiple bullet point formats:

- **Standard Bullets**: `•`, `-`, `*`
- **Numbered Lists**: `1.`, `2.`, `3.`
- **Lettered Lists**: `A.`, `B.`, `C.`
- **Arrow Lists**: `→`, `▶`, `▪`

### Test Planner Functionality

#### **Test Actionable Bullet Detection**
```bash
# Test verb extraction and actionable content detection
docker compose exec api python -c "
from app.services.planner import Planner
p = Planner()
test_bullets = ['Check the process list', 'Restart the service', 'Verify the configuration', 'Monitor the metrics']
for text in test_bullets:
    print(f'{text} -> Verb: {p._extract_main_verb(text)}')
"

# Expected output shows verb extraction:
# Check the process list -> Verb: check
# Restart the service -> Verb: restart
# Verify the configuration -> Verb: verify
# Monitor the metrics -> Verb: monitor
```

#### **Test Section Classification**
```bash
# Test automatic section classification
docker compose exec api python -c "
from app.services.planner import Planner, ActionableBullet
p = Planner()
test_bullets = ['Check the process list', 'Restart the service', 'Verify the fix worked']
for bullet in test_bullets:
    classified = p._classify_bullets_by_section([
        ActionableBullet(content=bullet, verb='check', section_type='unknown', 
                        source_chunk=None, source_file='test.md', chunk_id='1', 
                        confidence=0.8, metadata={})
    ])
    print(f'{bullet} -> {list(classified.keys())}')
"

# Expected output shows section classification
```

#### **Test Bullet Point Extraction**
```bash
# Test bullet point extraction from content
docker compose exec api python -c "
from app.services.planner import Planner
p = Planner()
test_content = '## First Checks\n- Check process list\n- Review deployments\n\n## Fix Steps\n- Restart services\n- Clear cache'
bullets = p._extract_bullet_points(test_content)
print('Bullets extracted:')
for bullet in bullets:
    print(f'  • {bullet}')
"

# Expected output shows extracted bullet points
```

#### **Test Full Planning Pipeline**
```bash
# Test complete planning pipeline
docker compose exec api python -c "
from app.services.planner import Planner
from app.services.retrieval import RetrievalPipeline
from app.services.faiss_service import FAISSService

p = Planner()
rp = RetrievalPipeline()
fs = FAISSService()

chunks = rp.retrieve_diverse_results('High CPU usage alert 80% for 5 minutes', fs, top_k=8)
planned = p.plan_response(chunks, 'High CPU usage alert 80% for 5 minutes')

print('Response planned successfully!')
print(f'Total bullets: {planned.metadata["total_bullets"]}')
print(f'First checks: {len(planned.first_checks)}')
print(f'Fix steps: {len(planned.fix_steps)}')
print(f'Validate steps: {len(planned.validate_steps)}')
"
```

### Planner Response Structure

#### **PlannedResponse Data Structure**
```python
@dataclass
class PlannedResponse:
    first_checks: List[ActionableBullet]      # 3-5 diagnostic steps
    why_explanation: str                      # Concise explanation
    fix_steps: List[ActionableBullet]         # 2-5 remediation steps
    validate_steps: List[ActionableBullet]    # 2-4 validation steps
    sources: List[str]                        # Clean source list
    has_fix: bool                             # Whether fix steps exist
    has_validate: bool                        # Whether validate steps exist
    metadata: Dict[str, Any]                  # Planning statistics
```

#### **ActionableBullet Data Structure**
```python
@dataclass
class ActionableBullet:
    content: str                              # Bullet content text
    verb: str                                 # Main action verb
    section_type: str                         # Classified section type
    source_chunk: Any                         # Source chunk object
    source_file: str                          # Source filename
    chunk_id: str                             # Source chunk ID
    confidence: float                         # Relevance confidence
    metadata: Dict[str, Any]                  # Quality metadata
```

#### **Planning Statistics**
```json
{
  "planning_stats": {
    "total_bullets": 9,
    "first_checks_count": 5,
    "fix_steps_count": 4,
    "validate_steps_count": 0,
    "sources_count": 4,
    "has_fix": true,
    "has_validate": false,
    "question_type": "performance_alert",
    "chunks_analyzed": 8
  }
}
```

### Planner Integration Benefits

#### **For Answer Quality**
- **Structured Responses**: Consistent format across all answers
- **Actionable Content**: Every bullet is actionable and traceable
- **Provenance Tracking**: Full source attribution for every step
- **Quality Assessment**: Built-in content quality evaluation

#### **For User Experience**
- **Clear Organization**: Logical grouping of diagnostic, fix, and validation steps
- **Traceable Sources**: Every step can be traced back to source documents
- **Consistent Format**: Predictable response structure
- **Actionable Steps**: Clear, specific actions users can take

#### **For Content Management**
- **Automatic Classification**: Content automatically organized by intent
- **Quality Metrics**: Built-in assessment of content value
- **Source Tracking**: Complete audit trail for all content
- **Flexible Structure**: Adapts to available content types

### Implementation Details

#### **Planning Pipeline Architecture**
```
Retrieved Chunks
    ↓
Actionable Bullet Extraction
    ↓
Section Classification
    ↓
Quality Assessment & Scoring
    ↓
Bullet Selection & Organization
    ↓
Why Explanation Generation
    ↓
Sources List Generation
    ↓
Planned Response
```

#### **Bullet Quality Scoring**
```python
bullet_score = base_confidence + quality_bonuses

quality_bonuses = {
    'has_commands': 0.1,      # Bonus for command examples
    'has_metrics': 0.1,       # Bonus for metric references
    'content_length': 0.05,   # Bonus for detailed content (>50 chars)
}
```

#### **Section Selection Logic**
```python
section_constraints = {
    'first_checks': {'min': 3, 'max': 5},
    'fix_steps': {'min': 2, 'max': 5},
    'validate_steps': {'min': 2, 'max': 4}
}
```

#### **Why Explanation Generation**
- **Source Selection**: Top 3 most relevant chunks
- **Content Extraction**: Relevant sentences based on question
- **Context Addition**: Section type context (policy, background)
- **Sentence Scoring**: Relevance-based sentence selection

### Testing and Validation

#### **Planner Component Testing**
```bash
# Test individual planner components
docker compose exec api python -c "
from app.services.planner import Planner
p = Planner()

# Test action verb detection
test_texts = ['Check the process list', 'Restart the service', 'Verify the configuration']
for text in test_texts:
    actionable = p._is_actionable_bullet(text)
    verb = p._extract_main_verb(text)
    print(f'{text} -> Actionable: {actionable}, Verb: {verb}')
"
```

#### **Integration Testing**
```bash
# Test planner integration with RAG service
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert 80% for 5 minutes", "context": ""}' \
  | jq '.planning_stats'

# Expected output shows planning statistics
```

#### **Performance Testing**
```bash
# Test planner performance
docker compose exec api python -c "
import time
from app.services.planner import Planner
from app.services.retrieval import RetrievalPipeline
from app.services.faiss_service import FAISSService

p = Planner()
rp = RetrievalPipeline()
fs = FAISSService()

start_time = time.time()
chunks = rp.retrieve_diverse_results('High CPU usage alert', fs, top_k=8)
planned = p.plan_response(chunks, 'High CPU usage alert')
end_time = time.time()

print(f'Planning time: {end_time - start_time:.3f} seconds')
print(f'Bullets extracted: {planned.metadata["total_bullets"]}')
"
```

### Troubleshooting Planner Issues

#### **Common Issues**
1. **Low Bullet Count**: Check content quality and action verb patterns
2. **Poor Classification**: Verify section pattern definitions
3. **Missing Sources**: Check chunk metadata extraction
4. **Performance Issues**: Review regex compilation and processing

#### **Debug Commands**
```bash
# Check planner configuration
docker compose exec api python -c "
from app.services.planner import Planner
p = Planner()
print('Action verbs loaded:', len(p.action_verbs))
print('Section patterns loaded:', len(p.section_patterns))
print('Bullet patterns loaded:', len(p.compiled_bullets))
"

# Test bullet extraction
docker compose exec api python -c "
from app.services.planner import Planner
p = Planner()
test_content = 'Check the process list\\nRestart the service\\nVerify the fix worked'
bullets = p._extract_bullet_points(test_content)
print(f'Extracted {len(bullets)} bullets:')
for bullet in bullets:
    print(f'  • {bullet}')
"
```

### Planner Configuration

#### **Customization Options**
- **Action Verb Patterns**: Add new verb categories
- **Section Patterns**: Modify classification rules
- **Bullet Patterns**: Add new bullet point formats
- **Quality Metrics**: Adjust scoring algorithms
- **Section Constraints**: Modify min/max counts

#### **Performance Tuning**
- **Regex Compilation**: Pre-compiled patterns for efficiency
- **Batch Processing**: Process multiple chunks efficiently
- **Memory Management**: Optimize for large content sets
- **Caching**: Ready for future caching optimizations

---

**🎯 Planner Complete!** The system now includes an intelligent response planner that extracts actionable bullets from retrieved chunks and organizes them into structured, traceable responses. The planner automatically classifies content by intent, maintains full provenance tracking, and ensures every response contains actionable, well-organized content with proper source attribution.

The integration with the retrieval pipeline and RAG service creates a powerful combination: diverse retrieval provides comprehensive content coverage, the planner extracts and organizes actionable content, and the anti-generic gate ensures quality standards. This results in responses that naturally cite multiple files and sections while providing clear, actionable guidance with full traceability.

---

## 🆕 **NEW: UI Polish & Enhanced User Experience**

### Comprehensive Interface Improvements
The system now includes significant UI polish improvements including a KB status pill in the sidebar, enhanced source chips with right drawer navigation, collapsible diagnostics with code formatting, keyboard shortcuts, and mobile-optimized design.

#### **UI Enhancement Components**

1. **KB Status Pill**: Real-time knowledge base status display
   - **Purpose**: Show current document count and index status
   - **Features**: Live updates, refresh capability, visual indicators
   - **Use Case**: Monitor system health and document availability

2. **Enhanced Source Chips**: Interactive source navigation
   - **Purpose**: Provide detailed source content with breadcrumb navigation
   - **Features**: Right drawer, source parsing, content formatting
   - **Use Case**: Verify citations and explore source context

3. **Collapsible Diagnostics**: Organized diagnostic information
   - **Purpose**: Present diagnostic results in organized, collapsible sections
   - **Features**: Code formatting, mobile-friendly, visual indicators
   - **Use Case**: Review system diagnostics and troubleshooting results

4. **Keyboard Shortcuts**: Power user productivity features
   - **Purpose**: Enable efficient navigation and actions
   - **Features**: Global shortcuts, help modal, customizable actions
   - **Use Case**: Improve workflow efficiency for power users

5. **Mobile Optimizations**: Responsive design improvements
   - **Purpose**: Ensure optimal experience across all devices
   - **Features**: Touch-friendly targets, responsive layouts, mobile hints
   - **Use Case**: Support on-call engineers using mobile devices

### KB Status Pill Implementation

#### **Status Display Features**
The KB status pill provides real-time information about the knowledge base:

- **Document Count**: Shows "Using N docs" with live updates
- **Index Status**: Visual indicators for "index ready" vs "index building"
- **Refresh Capability**: Manual refresh button for status updates
- **Visual States**: Color-coded status indicators (green for ready, yellow for building)

#### **Status Pill States**
```typescript
interface KBStatus {
  docs_count: number;        // Number of documents in KB
  index_ready: boolean;      // Whether FAISS index is ready
  docs: Array<{              // Document metadata
    filename: string;
    hash: string;
  }>;
}
```

#### **Visual Indicators**
- **Database Icon**: Blue database icon for KB representation
- **Status Icons**: 
  - Green checkmark for ready index
  - Yellow alert for building index
- **Color Coding**: Blue theme for consistency with app design
- **Loading State**: Spinner animation during status fetch

### Enhanced Source Chips & Right Drawer

#### **Source Chip Functionality**
Source chips now provide enhanced interaction:

- **Clickable Chips**: Each citation opens detailed source view
- **Right Drawer**: Slides in from right side for source details
- **Breadcrumb Navigation**: Clear path to source location
- **Content Display**: Formatted source content with actions

#### **Right Drawer Features**
```typescript
interface SourceDetailsPanelProps {
  isOpen: boolean;           // Drawer visibility state
  onClose: () => void;       // Close handler
  citation: string | null;   // Citation string (filename#chunk_id)
  chunkContent: string | null; // Source content
  isLoading: boolean;        // Loading state
}
```

#### **Drawer Navigation**
- **Breadcrumb Path**: Source → Filename → Chunk ID
- **Filename Formatting**: Clean, readable file names
- **Chunk Identification**: Clear chunk reference
- **Content Actions**: Copy content functionality

#### **Mobile Responsiveness**
- **Full Width on Mobile**: Drawer takes full screen on small devices
- **Touch-Friendly**: Optimized for touch interactions
- **Backdrop**: Semi-transparent backdrop for mobile focus
- **Smooth Animations**: CSS transitions for smooth interactions

### Collapsible Diagnostics Component

#### **Diagnostics Organization**
The diagnostics component provides organized, collapsible diagnostic information:

- **Collapsible Sections**: Expandable/collapsible diagnostic blocks
- **Item Count Display**: Shows number of diagnostic items
- **Visual Indicators**: Icons for different diagnostic types
- **Code Formatting**: Proper formatting for log content and commands

#### **Diagnostic Types Supported**
```typescript
interface DiagnosticsData {
  logs?: string[];           // Log file content
  queue_depth?: number;      // Queue depth information
  [key: string]: any;        // Additional diagnostic data
}
```

#### **Code Formatting Features**
- **Log Formatting**: Proper line breaks and monospace font
- **Command Display**: Highlighted command examples
- **Metrics Display**: Formatted metric information
- **JSON Formatting**: Pretty-printed JSON data

#### **Mobile-Friendly Design**
- **Touch Targets**: Minimum 44px touch targets
- **Responsive Layout**: Adapts to different screen sizes
- **Collapsible Interface**: Space-efficient on mobile devices
- **Visual Hierarchy**: Clear information organization

### Keyboard Shortcuts System

#### **Global Shortcuts**
The keyboard shortcuts system provides power user functionality:

- **⌘/Ctrl + K**: Focus chat input
- **⌘/Ctrl + N**: Start new chat
- **⌘/Ctrl + B**: Toggle sidebar
- **⌘/Ctrl + J**: Toggle theme
- **?**: Show/hide shortcuts help
- **Esc**: Close shortcuts modal

#### **Shortcut Implementation**
```typescript
interface KeyboardShortcutsProps {
  onNewChat?: () => void;           // New chat handler
  onToggleSidebar?: () => void;     // Sidebar toggle handler
  onFocusInput?: () => void;        // Input focus handler
  onToggleTheme?: () => void;       // Theme toggle handler
}
```

#### **Smart Shortcut Handling**
- **Input Field Detection**: Prevents shortcuts in text inputs
- **Event Prevention**: Proper event handling and prevention
- **Global Listeners**: Document-level event handling
- **Cleanup**: Proper event listener cleanup

#### **Help Modal**
- **Shortcut Display**: Clear list of available shortcuts
- **Visual Keys**: Styled keyboard key representations
- **Descriptions**: Clear explanation of each shortcut
- **Accessibility**: Keyboard navigation support

### Mobile Optimizations

#### **Touch-Friendly Design**
Mobile optimizations ensure optimal experience on all devices:

- **Minimum Touch Targets**: 44px minimum for all interactive elements
- **Responsive Layouts**: Adapts to different screen sizes
- **Mobile Hints**: Contextual help for mobile users
- **Touch Gestures**: Optimized for touch interactions

#### **Responsive Components**
- **Sidebar**: Collapsible on mobile devices
- **Source Drawer**: Full-width on small screens
- **Input Fields**: Optimized for mobile keyboards
- **Buttons**: Proper sizing for touch interaction

#### **Mobile-Specific Features**
- **Auto-resize Textarea**: Grows with content on mobile
- **Character Count**: Visual feedback for input length
- **Loading States**: Clear loading indicators
- **Error Handling**: Mobile-friendly error messages

### Test UI Polish Features

#### **Test KB Status Pill**
```bash
# Check if KB status is displayed in sidebar
# The sidebar should show:
# - "Using N docs" with document count
# - Index status (ready/building)
# - Refresh button functionality
# - Visual status indicators
```

#### **Test Source Chips & Drawer**
```bash
# Test source chip interaction:
# 1. Send a question that generates citations
# 2. Click on a source chip
# 3. Verify right drawer opens
# 4. Check breadcrumb navigation
# 5. Verify source content display
# 6. Test copy functionality
```

#### **Test Collapsible Diagnostics**
```bash
# Test diagnostics display:
# 1. Ask a question that triggers diagnostics
# 2. Verify diagnostics section appears
# 3. Test expand/collapse functionality
# 4. Check code formatting
# 5. Verify mobile responsiveness
```

#### **Test Keyboard Shortcuts**
```bash
# Test keyboard shortcuts:
# 1. Press ? to show shortcuts help
# 2. Test ⌘/Ctrl + K (focus input)
# 3. Test ⌘/Ctrl + N (new chat)
# 4. Test ⌘/Ctrl + B (toggle sidebar)
# 5. Test ⌘/Ctrl + J (toggle theme)
# 6. Press Esc to close shortcuts
```

### UI Polish Benefits

#### **For User Experience**
- **Real-time Status**: Always know KB health and status
- **Easy Navigation**: Quick access to source details
- **Power User Features**: Keyboard shortcuts for efficiency
- **Mobile Support**: Optimal experience on all devices

#### **For On-Call Engineers**
- **Quick Assessment**: Immediate KB status visibility
- **Source Verification**: Easy citation verification
- **Efficient Workflow**: Keyboard shortcuts for speed
- **Mobile Access**: Full functionality on mobile devices

#### **For System Monitoring**
- **KB Health**: Real-time knowledge base status
- **Document Count**: Live document availability
- **Index Status**: FAISS index readiness monitoring
- **Performance**: Quick status refresh capability

### Implementation Details

#### **Component Architecture**
```
UI Polish Components
├── KB Status Pill (Sidebar)
├── Enhanced Source Chips
├── Right Drawer (Source Details)
├── Collapsible Diagnostics
├── Keyboard Shortcuts
└── Mobile Optimizations
```

#### **Responsive Design**
- **Breakpoints**: Mobile-first responsive design
- **Touch Targets**: Minimum 44px for accessibility
- **Layout Adaptation**: Components adapt to screen size
- **Performance**: Optimized for mobile devices

#### **Accessibility Features**
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Proper ARIA labels and roles
- **Focus Management**: Clear focus indicators
- **Touch Support**: Optimized touch interactions

### Testing and Validation

#### **Cross-Device Testing**
```bash
# Test on different devices:
# - Desktop (1920x1080)
# - Tablet (768x1024)
# - Mobile (375x667)
# - Large screens (2560x1440)
```

#### **Browser Compatibility**
```bash
# Test in different browsers:
# - Chrome (latest)
# - Firefox (latest)
# - Safari (latest)
# - Edge (latest)
```

#### **Touch Device Testing**
```bash
# Test touch interactions:
# - Tap targets (44px minimum)
# - Swipe gestures
# - Pinch to zoom
# - Touch scrolling
```

### Troubleshooting UI Issues

#### **Common Issues**
1. **KB Status Not Loading**: Check API endpoint and network
2. **Source Drawer Not Opening**: Verify click handlers and state
3. **Keyboard Shortcuts Not Working**: Check event listeners
4. **Mobile Layout Issues**: Verify responsive CSS

#### **Debug Commands**
```bash
# Check browser console for errors
# Verify component state in React DevTools
# Test responsive design in browser dev tools
# Check network requests for API calls
```

### UI Polish Configuration

#### **Customization Options**
- **Theme Colors**: Customizable color schemes
- **Shortcut Keys**: Configurable keyboard shortcuts
- **Drawer Width**: Adjustable source drawer size
- **Mobile Breakpoints**: Custom responsive breakpoints

#### **Performance Tuning**
- **Lazy Loading**: Components load on demand
- **Debounced Updates**: Optimized status updates
- **Memory Management**: Proper cleanup and disposal
- **Bundle Optimization**: Efficient component loading

---

**🎯 UI Polish Complete!** The system now includes comprehensive UI polish improvements that significantly enhance the user experience. The KB status pill provides real-time system health information, enhanced source chips enable easy citation verification, collapsible diagnostics organize troubleshooting information, keyboard shortcuts improve power user efficiency, and mobile optimizations ensure optimal experience across all devices.

The combination of these improvements creates a professional, polished interface that supports on-call engineers in their critical work. The real-time status monitoring, intuitive navigation, and mobile-friendly design ensure that users can efficiently access information and perform troubleshooting tasks regardless of their device or location.

The UI polish successfully meets all acceptance criteria: visual polish is significantly improved, the KB pill accurately reflects system status, source chips open detailed right drawers with breadcrumb navigation, diagnostics are collapsible with code formatting, keyboard shortcuts provide power user functionality, and mobile optimizations ensure touch-friendly design across all screen sizes.

## 🐛 Troubleshooting

### Common Issues

#### Frontend Not Loading
```bash
# Check web service
docker compose logs web

# Verify port 3000 is accessible
curl http://localhost:3000
```

#### API Connection Issues
```bash
# Check API health
curl http://localhost:8000/health

# Verify API logs
docker compose logs api
```

#### No Responses
```bash
# Check if documents are ingested
make ingest

# Verify FAISS index
curl http://localhost:8000/stats
```

#### Diagnostics Not Working
```bash
# Check mock data files
ls -la data/mock/logs/
ls -la data/mock/queues/

# Verify diagnostics service
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "CPU spike after deploy", "context": ""}' | jq '.diagnostics'
```

#### Knowledge Base Issues
```bash
# Check KB status
curl http://localhost:8000/kb/status

# Refresh knowledge base
curl -X POST http://localhost:8000/kb/refresh

# Check file manifest
docker compose exec api cat /app/data/docs/.file_manifest.json | jq '.'
```

#### Session Management Issues
```bash
# Check session endpoints
curl "http://localhost:8000/sessions"

# Test session creation
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "description": "Test session"}'

# Check database file
docker compose exec api ls -la /app/data/app.db
```

### Debug Commands
```bash
# View all logs
make logs

# Check service status
make selfcheck

# Rebuild services
make build

# Restart everything
make clean && make dev
```

## 🎉 Success Indicators

You've successfully tested the Frontend MVP when:

1. ✅ **Chat Interface**: Can type questions and see responses
2. ✅ **Structured Answers**: Responses follow First checks → Why → Diagnostics → Sources format
3. ✅ **Source Citations**: Blue chips display below answers
4. ✅ **Source Panel**: Clicking chips opens side panel with content
5. ✅ **Error Handling**: Graceful error messages and loading states
6. ✅ **Environment Config**: API base URL is configurable
7. ✅ **Responsive Design**: Interface works on different screen sizes
8. ✅ **No Leakage**: Answers start directly with content, no system text
9. ✅ **Clean Citations**: Normalized filenames, no duplicates, no meta files
10. ✅ **Diagnostics Tools**: CPU queries show log diagnostics, queue queries show depths
11. ✅ **Honest Fallbacks**: Clear about missing tools and manual verification needed
12. ✅ **Smart Routing**: Redis queries don't run irrelevant tools
13. ✅ **File Upload**: Can upload documents via multipart POST
14. ✅ **Persistent Storage**: Files saved to disk with hash tracking
15. ✅ **Incremental Upserts**: Only new/changed files processed
16. ✅ **Restart Persistence**: Knowledge base ready after container restart
17. ✅ **Status Endpoints**: /kb/status shows file count and index readiness
18. ✅ **Session Creation**: Can create new chat sessions via API
19. ✅ **Message Persistence**: Chat history saved to SQLite database
20. ✅ **Session Management**: List, update, delete sessions via API
21. ✅ **Frontend Sidebar**: Session list with search and actions
22. ✅ **Dark Mode**: Toggle between light/dark themes
23. ✅ **Quick Prompts**: Common question templates accessible
24. ✅ **Action Buttons**: Regenerate, Copy, Export on messages
25. ✅ **URL Routing**: /:sessionId routes with localStorage persistence
26. ✅ **Refresh Persistence**: Chat history maintained across page refreshes
27. ✅ **Session Switching**: Load different conversation histories seamlessly

## 🚀 Next Steps

After successful testing:

1. **Customize**: Add your own runbook documents
2. **Configure**: Set up OpenAI/Azure OpenAI API keys
3. **Deploy**: Move to production environment
4. **Extend**: Add more document types and features
5. **Integrate**: Connect with existing incident management systems
6. **Enhance Diagnostics**: Add more monitoring tools and integrations
7. **Scale Storage**: Implement distributed file storage for production
8. **Add Authentication**: Secure file upload and API access
9. **Session Analytics**: Track usage patterns and popular queries
10. **Collaboration**: Add multi-user session sharing and permissions
11. **Advanced Export**: Support for PDF, Word, and other formats
12. **Search History**: Full-text search across all chat sessions

---

**🎯 Demo Complete!** You've successfully tested all Frontend MVP features including the new citation cleaning, answer composition, read-only diagnostics tools, knowledge base persistence with ingest endpoints, and comprehensive session management with chat history persistence.
