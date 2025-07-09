# AI Company Web - Four Sages Real-time System

A comprehensive full-stack web application featuring the **Four Sages System** with real-time WebSocket communication, built with Next.js 14 and FastAPI.

## System Overview

The Four Sages System represents four specialized AI assistants working in harmony:

- **Knowledge Sage** 📚 - Manages documentation, knowledge base, and learning resources
- **Task Sage** ⚡ - Handles project management, workflows, and task automation  
- **Incident Sage** 🚨 - Monitors system health, manages alerts, and automates responses
- **Search Sage** 🔍 - Provides intelligent RAG-powered search across all domains

**Elder Council** 🏛️ - Coordinates between sages for complex decision-making and system-wide operations.

## Architecture

### Frontend (Next.js 14)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand stores
- **Real-time**: WebSocket integration with custom hooks
- **TypeScript**: Full type safety

### Backend (FastAPI)
- **Framework**: FastAPI with async/await
- **Real-time**: WebSocket manager for sage communication
- **Documentation**: Auto-generated OpenAPI 3.0
- **Validation**: Pydantic schemas
- **Logging**: Structured logging with correlation IDs

### Infrastructure
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache**: Redis for session management
- **Containerization**: Docker & Docker Compose
- **Monitoring**: Health checks and metrics

## Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+ and pip
- Docker and Docker Compose (optional)

### Development Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd ai-company-web
npm install
```

2. **Start Backend**:
```bash
cd backend
pip install -r requirements.txt
python start-dev.py
```

3. **Start Frontend**:
```bash
npm run dev
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- WebSocket: ws://localhost:8000/api/ws/connect

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Key Features

### Real-time Four Sages Communication
- WebSocket-based real-time updates
- Sage-to-sage message passing
- Elder Council session management
- Connection heartbeat and auto-reconnection

### Knowledge Management
- Article creation and versioning
- Category and tag organization
- Full-text search capabilities
- Markdown rendering support

### Task Management
- Kanban board interface
- Priority and status management
- Project organization
- Progress tracking and analytics

### Incident Management
- Alert monitoring and response
- Severity-based escalation
- System impact tracking
- Automated resolution workflows

### Intelligent Search
- Semantic search across all content
- RAG (Retrieval-Augmented Generation)
- Auto-suggestions and filters
- Similar content discovery

## API Endpoints

### Four Sages APIs
```
GET    /api/sages/knowledge/     - List knowledge articles
POST   /api/sages/knowledge/     - Create article
GET    /api/sages/tasks/         - List tasks
POST   /api/sages/tasks/         - Create task
GET    /api/sages/incidents/     - List incidents
POST   /api/sages/incidents/     - Create incident
POST   /api/sages/search/        - Search all content
```

### Elder Council APIs
```
GET    /api/elder-council/sessions     - List sessions
POST   /api/elder-council/sessions     - Create session
POST   /api/elder-council/sessions/{id}/invoke - Invoke council
```

### WebSocket Endpoints
```
WS     /api/ws/connect              - Main WebSocket connection
WS     /api/ws/sage/{sage_type}     - Sage-specific connection
WS     /api/ws/council/{session_id} - Council session connection
```

## Development Commands

### Frontend
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript checking
```

### Backend
```bash
python start-dev.py           # Start development server
pip install -r requirements.txt # Install dependencies
python scripts/sample-data.py   # Generate sample data
pytest                          # Run tests
black . && isort .              # Format code
```

## Configuration

### Environment Variables

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/ws
```

**Backend (.env)**:
```bash
# Copy from .env.example and customize
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
```

## Project Structure

```
ai-company-web/
├── src/                      # Next.js frontend
│   ├── app/                  # App Router pages
│   ├── components/           # React components
│   │   ├── sages/           # Four Sages components
│   │   ├── integration/     # Elder Council components
│   │   └── ui/              # shadcn/ui components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities and API client
│   └── stores/              # Zustand state stores
├── backend/                  # FastAPI backend
│   ├── app/                 # Application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── schemas/        # Pydantic models
│   │   └── websocket/      # WebSocket manager
│   └── scripts/            # Utility scripts
└── docker-compose.yml      # Multi-service setup
```

## Integration Testing

1. **Start both services**:
```bash
# Terminal 1: Backend
cd backend && python start-dev.py

# Terminal 2: Frontend  
npm run dev
```

2. **Test WebSocket connection**:
- Open browser dev tools
- Navigate to any sage page
- Verify WebSocket connection in Network tab

3. **Test API integration**:
- Create a knowledge article
- Create a task with high priority
- Verify cross-sage notifications

## Contributing

1. **Code Style**: Follow TypeScript/Python conventions
2. **Testing**: Add tests for new features
3. **Documentation**: Update API docs and README
4. **WebSocket**: Test real-time functionality
5. **Sage Integration**: Ensure proper inter-sage communication

## Deployment

### Production Checklist
- [ ] Set production environment variables
- [ ] Configure PostgreSQL and Redis
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up monitoring and logging
- [ ] Test WebSocket connections

### Docker Production
```bash
# Use production profile
docker-compose --profile production up -d
```

## Monitoring & Health

- **Health Check**: GET /health
- **WebSocket Stats**: GET /api/ws/connections  
- **Sage Statistics**: GET /api/sages/{type}/stats
- **Council Stats**: GET /api/elder-council/stats

## License

MIT License - see LICENSE file for details.

---

**AI Company Web** - Where the Four Sages collaborate in real-time to create intelligent, responsive systems. 🚀
