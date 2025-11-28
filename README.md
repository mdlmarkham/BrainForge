# BrainForge AI Knowledge Base

A modern, constitutionally-compliant AI knowledge base system built with Python 3.11+, FastAPI, and PostgreSQL/PGVector. BrainForge enables structured knowledge management with AI integration, semantic search, and Obsidian vault synchronization.

## 🚀 Features

- **Constitutional Compliance**: Built-in tracking for AI-generated content, provenance, versioning, and audit trails
- **Semantic Search**: Vector embeddings with PostgreSQL/PGVector for intelligent content discovery
- **Obsidian Integration**: Bidirectional sync with Obsidian vaults for seamless workflow integration
- **AI Agent Framework**: Track and audit AI operations with human review workflows
- **Modern API**: FastAPI-based REST API with OpenAPI documentation
- **Containerized**: Docker and Docker Compose for easy deployment

## 🛠️ Tech Stack

- **Python 3.11+** (constitutional requirement)
- **FastAPI** - Modern, fast web framework for APIs
- **Pydantic v2.12.5** - Data validation with modern type annotations
- **PostgreSQL/PGVector** - Vector database for semantic search
- **FastMCP** - MCP server framework for AI integration
- **SpiffWorkflow** - Workflow orchestration
- **Docker** - Containerization and deployment

## 📋 Project Structure

```
BrainForge/
├── src/                    # Source code
│   ├── api/               # FastAPI application and routes
│   ├── models/            # Pydantic data models
│   ├── services/          # Business logic services
│   ├── compliance/        # Constitutional compliance framework
│   └── cli/               # Command-line tools
├── tests/                 # Test suite
├── config/               # Configuration files
├── specs/               # Design specifications
└── docs/               # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 13+ (with PGVector extension)
- Docker and Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/brainforge.git
   cd brainforge
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Set up database**
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d postgres
   
   # Or configure your own PostgreSQL instance
   # Update config/database.env with your connection details
   ```

5. **Run database migrations**
   ```bash
   python -m src.cli.migrate
   ```

6. **Start the development server**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individually
docker build -t brainforge .
docker run -p 8000:8000 brainforge
```

## 🧪 Testing

Run the test suite with coverage:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Code quality checks
ruff check src/
```

## 📚 API Endpoints

- `GET /api/v1/notes` - List notes
- `POST /api/v1/notes` - Create note
- `GET /api/v1/notes/{id}` - Get note by ID
- `PUT /api/v1/notes/{id}` - Update note
- `DELETE /api/v1/notes/{id}` - Delete note
- `POST /api/v1/search` - Semantic search
- `POST /api/v1/ingestion` - Ingest external content
- `POST /api/v1/vault/sync` - Sync with Obsidian vault
- `GET /api/v1/agent/runs/{id}` - Get agent run status

## 🔧 Development

### Code Style

This project follows Python 3.11+ conventions with:
- Pydantic v2.12.5 for data validation
- Type hints throughout
- Ruff for linting and formatting
- pytest for testing

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📖 Documentation

- [Design Specifications](specs/master/) - Detailed feature plans and architecture
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)
- [Constitutional Compliance](src/compliance/) - AI governance framework

## 🏛️ Constitutional Principles

BrainForge adheres to the following constitutional principles:

1. **Structured Data Foundation**: All content must be structured and versioned
2. **AI Agent Integration**: AI operations must be tracked and auditable
3. **Provenance Tracking**: Content origin and modifications must be recorded
4. **Human Review**: AI-generated content requires human approval
5. **Version Control**: All changes must maintain complete history

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/brainforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/brainforge/discussions)
- **Email**: your-email@example.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python ecosystem tools
- Inspired by Zettelkasten and personal knowledge management systems
- Designed for AI-assisted knowledge work with constitutional safeguards