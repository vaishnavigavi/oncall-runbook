# OnCall Runbook - AI-Powered Incident Response

A comprehensive monorepo for managing and querying oncall runbooks and incident response documentation using AI-powered search and retrieval.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd oncall-runbook

# Start all services
make dev

# Or start individually
make api      # Start API only
make web      # Start web only
```

## 📁 Project Structure

```
.
├── api/                 # FastAPI backend service
├── web/                 # React + Vite frontend
├── data/                # Data directories
│   ├── docs/           # Documentation files
│   ├── index/          # FAISS index storage
│   └── mock/           # Mock logs and test data
├── docker/              # Docker configuration files
├── .env.example         # Environment variables template
├── docker-compose.yml   # Multi-service orchestration
├── Makefile            # Development commands
└── requirements.txt     # Python dependencies
```

## 🛠️ Development Commands

```bash
make dev          # Start all services
make web          # Start web frontend only
make api          # Start API only
make ingest       # Run document ingestion
make selfcheck    # Verify services and data
make build        # Build Docker images
make clean        # Cleanup Docker containers
make logs         # View all service logs
```

## 🌐 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `POST /ingest` - Document ingestion
- `POST /ask` - Question answering (legacy format)
- `POST /ask/structured` - Structured RAG responses
- `GET /stats` - FAISS index statistics

### Document Ingestion
```bash
# Ingest seed documents
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"ingest_seed_docs": true}'

# Ingest specific file
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/app/data/docs/alerts-cheatsheet.md"}'
```

### Question Answering
```bash
# Ask a question with structured response
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU > 85% for 5 min after deploy", "context": ""}'
```

## 💬 Frontend Features

### Chat Interface
- **Single page chat**: Clean, modern chat interface
- **Input & Send**: Type questions and send with button
- **Messages list**: View conversation history
- **Loading states**: Visual feedback during processing

### Sources & Citations
- **Sources chips**: Clickable citation chips below answers
- **Side panel**: Click chips to open source details
- **Chunk content**: View actual document text for each citation
- **Citation format**: `filename#chunk_id` (e.g., `alerts-cheatsheet.md#e195f2a3`)

### Error Handling
- **Graceful errors**: Toast notifications for user feedback
- **API fallbacks**: Handles connection issues gracefully
- **Loading states**: Clear visual feedback

### Environment Configuration
```bash
# Frontend environment variables
VITE_API_BASE=http://localhost:8000  # API base URL
```

## 🔍 RAG System Features

### Document Processing
- **Multiple formats**: `.md`, `.txt`, `.pdf` support
- **Smart chunking**: Heading-aware with 800-token chunks
- **Overlap handling**: 100-token overlap for context
- **PDF support**: PyMuPDF with PyPDF2 fallback

### Embedding & Search
- **OpenAI integration**: Azure OpenAI and OpenAI support
- **Mock fallback**: Works without API keys
- **FAISS index**: Efficient similarity search
- **Keyword fallback**: Intelligent content matching

### Answer Structure
```
**First checks:**
• Check for runaway processes
• Review recent deployments

**Why this happens:**
• Infinite loops in application code
• Database query issues

**Diagnostics if tools ran:**
• `top` or `htop` to see process list
• `free -h` to see memory status

**Sources:** See citations below.
```

## 📊 Data & Storage

### Seed Documents
- **Payments Runbook**: Payment system troubleshooting
- **Incident Response**: P0/P1 incident procedures
- **Alerts Cheat Sheet**: CPU, memory, disk alerts
- **SLO Policy**: Service level objectives

### FAISS Index
- **Persistent storage**: `/app/data/index/`
- **Metadata tracking**: Chunk information and sources
- **Upsert support**: Add documents without rebuilding
- **Statistics**: Real-time index metrics

## 🐳 Docker Configuration

### Services
- **API**: FastAPI with Python 3.11
- **Web**: React + Vite + Tailwind
- **Networking**: Isolated network with health checks
- **Volumes**: Persistent data storage

### Health Checks
- **API**: `/health` endpoint monitoring
- **Web**: HTTP response validation
- **Dependencies**: Service startup ordering

## 🧪 Testing & Validation

### Acceptance Criteria
- ✅ **Docker compose up --build** → Services start successfully
- ✅ **GET /health** → Returns "ok" status
- ✅ **Web interface** → Opens and displays chat
- ✅ **Seed documents** → Present on disk
- ✅ **POST /ingest** → Ingests documents successfully
- ✅ **FAISS files** → Index and metadata created
- ✅ **Re-calling /ingest** → Idempotent operation
- ✅ **POST /ask** → Returns structured answers with citations
- ✅ **Frontend chat** → Ask questions and see cited answers
- ✅ **Source chips** → Click to open source text panel

### Manual Testing
```bash
# Test ingestion
make ingest

# Test question answering
curl -X POST "http://localhost:8000/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "High CPU usage alert", "context": ""}'

# Test self-check
make selfcheck
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Web Configuration
WEB_PORT=3000
WEB_HOST=0.0.0.0

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Azure OpenAI (alternative)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here

# Document Processing
CHUNK_SIZE=800
CHUNK_OVERLAP=100
FAISS_DIMENSION=1536
```

## 🚀 Production Deployment

### Requirements
- Docker and Docker Compose
- OpenAI API key or Azure OpenAI credentials
- Sufficient storage for document index
- Network access for API calls

### Scaling
- **API**: Multiple workers with load balancer
- **Web**: Static build with CDN
- **Index**: Shared storage for FAISS files
- **Monitoring**: Health checks and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup
```bash
# Install dependencies
cd api && pip install -r requirements.txt
cd ../web && npm install

# Run locally
cd ../api && python main.py
cd ../web && npm run dev
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the documentation
- Review the logs: `make logs`
- Run self-check: `make selfcheck`
- Open an issue on GitHub
