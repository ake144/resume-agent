"""
PROFESSIONAL ARCHITECTURE GUIDE
================================

This document outlines the refactored, senior-level architecture of the Resume Agent API.

## Project Structure

```
app/
├── __init__.py
├── main.py                          # Entry point - minimal and clean
├── api/                             # API endpoints and routing
│   ├── __init__.py
│   ├── middleware.py                # Custom middleware (error handling, logging)
│   ├── dependencies/                # Dependency injection
│   │   └── __init__.py
│   └── v1/                          # API v1
│       ├── __init__.py
│       ├── router.py                # Main router consolidation
│       └── endpoints/               # Endpoint modules
│           ├── __init__.py
│           ├── health.py            # Health check endpoints
│           ├── job.py               # Job-related endpoints
│           ├── application.py       # Application generation endpoints
│           └── resume.py            # Legacy (deprecated)
├── core/                            # Core application utilities
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── factory.py                   # App factory pattern
│   ├── logging.py                   # Logging configuration
│   ├── database.py                  # Database utils
│   ├── embeddings.py                # Embedding utilities
│   ├── memory.py                    # Memory management
│   └── utils.py                     # General utilities
├── services/                        # Business logic layer
│   ├── __init__.py
│   ├── base.py                      # Base service class
│   ├── job_service.py               # Job service logic
│   └── application_service.py       # Application service logic
├── schemas/                         # Pydantic models (request/response)
│   ├── __init__.py
│   ├── base.py                      # Base response schemas
│   ├── job.py                       # Job schemas
│   └── application.py               # Application schemas
├── agents/                          # AI agent logic
│   ├── generator.py
│   ├── matcher.py
│   ├── workflow.py
│   └── __init__.py
├── ingestion/                       # Data ingestion
│   ├── job_ingestor.py
│   ├── resume_ingestor.py
│   └── __init__.py
├── rag/                             # Retrieval-Augmented Generation
│   ├── retriever.py
│   └── __init__.py
├── models/                          # Database models
│   ├── jobMatch.py
│   ├── workflow.py
│   └── __init__.py
└── utils/                           # Utilities
    ├── scheduler.py
    └── __init__.py
```

## Architecture Principles

### 1. **Separation of Concerns**
- **API Layer** (`api/`): Handles HTTP requests/responses
- **Service Layer** (`services/`): Contains business logic
- **Core Layer** (`core/`): Configuration and infrastructure
- **Schema Layer** (`schemas/`): Request/response validation

### 2. **Dependency Injection**
- Services are injected into endpoints via FastAPI's `Depends()`
- All service instances are managed in `api/dependencies/`
- Ensures loose coupling and testability

### 3. **Error Handling**
- Global error handling middleware catches all exceptions
- Standardized error responses with status, message, and error_code
- Proper HTTP status codes for different error scenarios

### 4. **Logging**
- Request/response logging middleware tracks all API calls
- Unique request IDs for tracing
- Structured logging with context (user_id, action, etc.)
- Rotating file handler for log management

### 5. **App Factory Pattern**
- Clean separation of app creation from initialization
- All middleware and routers configured in `core/factory.py`
- Makes testing and instantiation easier

## Key Features

### Configuration Management (`core/config.py`)
- Centralized settings using Pydantic BaseSettings
- Environment-based configuration
- Type-safe settings with validation
- Helper methods for environment checks

### Request/Response Schemas (`schemas/`)
- **base.py**: Generic `APIResponse[T]` for standardized responses
- **job.py**: Job-related request/response models
- **application.py**: Application generation models
- Full OpenAPI documentation with examples

### Service Layer (`services/`)
- **BaseService**: Common functionality (logging, etc.)
- **JobService**: Job ingestion and matching logic
- **ApplicationService**: Application generation logic
- Each service encapsulates business logic and error handling

### Endpoints (`api/v1/endpoints/`)
- **health.py**: Health and readiness checks
- **job.py**: Job operations (ingest, match)
- **application.py**: Application generation (generate, workflow)
- All use dependency injection for services
- Proper docstrings and OpenAPI documentation

### Middleware (`api/middleware.py`)
- **ErrorHandlingMiddleware**: Catches unhandled exceptions
- **RequestLoggingMiddleware**: Logs all requests with timing and IDs

## API Endpoints

All endpoints follow the `/api/v1/` prefix:

### Health
- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /` - Root info

### Jobs
- `POST /api/v1/jobs/ingest` - Ingest job posting
- `POST /api/v1/jobs/match` - Match job with user

### Applications
- `POST /api/v1/applications/generate` - Generate application document
- `POST /api/v1/applications/workflow` - Execute full workflow

## Running the Application

```bash
# Development with auto-reload
python -m uvicorn app.main:app --reload --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use the main.py script
python app/main.py
```

## Best Practices Applied

✅ **Strong:**
- Clear separation of concerns
- Dependency injection pattern
- Type safety with Pydantic
- Comprehensive logging and error handling
- Middleware for cross-cutting concerns
- Factory pattern for app initialization
- Comprehensive docstrings
- Consistent code style

✅ **Production-Ready:**
- Proper CORS configuration
- Request ID tracing
- Rotating log files
- Environment-based settings
- Structured error responses
- OpenAPI documentation
- Ready for containerization

## Future Improvements

- Add request validation and rate limiting middleware
- Implement database session management
- Add authentication/authorization
- Create full test suite with proper mocking
- Add metrics collection (Prometheus)
- Implement request/response caching
- Add pagination helpers
- Create API versioning strategy

## Testing

The clean architecture allows for easy testing:
- Mock services for unit tests
- Use Depends with override for integration tests
- Isolated endpoints with clear contracts
- See future examples in `tests/` folder

## Migration Notes

Old endpoints have been moved:
- Old: `POST /ingest/job` → New: `POST /api/v1/jobs/ingest`
- Old: `POST /match/job` → New: `POST /api/v1/jobs/match`
- Old: `POST /generate/application` → New: `POST /api/v1/applications/generate`
- Old: `POST /workflow/apply` → New: `POST /api/v1/applications/workflow`
- Old: `GET /health` → New: `GET /health` (via router)

Response format changed to standardized APIResponse:
```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": {...}
}
```

"""
