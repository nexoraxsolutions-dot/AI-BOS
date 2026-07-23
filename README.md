# AI-BOS

Enterprise-grade AI Business Operating System

[![CI Pipeline](https://github.com/ai-bos/ai-bos/actions/workflows/ci.yml/badge.svg)](https://github.com/ai-bos/ai-bos/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/ai-bos/ai-bos/actions/workflows/cd.yml/badge.svg)](https://github.com/ai-bos/ai-bos/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

## Overview

AI-BOS is a modular SaaS platform designed to provide centralized business operations for authentication, user management, companies, and dashboards.

## Architecture

The project follows Clean Architecture principles with:
- **Backend**: FastAPI with async SQLAlchemy, Alembic migrations, and JWT authentication
- **Frontend**: Next.js with TypeScript, Tailwind CSS, and React components
- **Database**: PostgreSQL with async support
- **Testing**: Pytest with async support and in-memory SQLite for unit tests

## Project Structure

```
ai-bos/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST API endpoints
│   │   ├── core/               # Configuration, security, tokens
│   │   ├── db/                 # Database session and base
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Business logic layer
│   │   └── main.py             # FastAPI application entry
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Unit and integration tests
│   └── requirements.txt
├── frontend/
│   ├── app/                    # Next.js pages
│   ├── components/             # React components
│   └── package.json
├── .github/                    # GitHub Actions and templates
├── docker-compose.yml
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

## Features

- [x] Backend API with FastAPI, SQLAlchemy, Alembic, and JWT auth
- [x] PostgreSQL database and Docker Compose setup
- [x] Frontend with Next.js, TypeScript, Tailwind CSS, and login UI
- [x] Full CRUD for users and companies (Create, Read, Update, Delete)
- [x] Health check endpoint (`GET /api/v1/health`)
- [x] Input validation with Pydantic
- [x] Unit and integration tests (70 backend tests + 15 frontend tests)
- [x] CI/CD pipelines with GitHub Actions
- [x] Docker containerization with multi-stage builds, healthchecks, and networking
- [x] Dashboard API with real-time aggregated statistics
- [x] Frontend authentication context and protected dashboard route
- [x] Users management page with table view
- [x] Companies management page with table view
- [x] Form validation with real-time feedback
- [x] Navigation bar with protected routes
- [x] Frontend unit tests with Jest and React Testing Library
- [x] Redis caching for improved performance
- [x] Redis health monitoring and statistics
- [x] Cache management UI for administrators
- [x] Environment variable management system with database persistence
- [x] Environment variable CRUD operations with validation
- [x] Secret value masking for sensitive environment variables
- [x] Environment variable export to .env file format
- [x] User profile management with username support
- [x] Self-service password change
- [x] User search by email, name, or username
- [x] User CRUD with admin modal-based management UI
- [x] Enhanced company model with 13 new fields (description, address, phone, email, website, tax_id, industry, employee_count, subscription_plan, subscription_status, subscription_expires_at, logo_url, settings)
- [x] Company search, filtering, and pagination
- [x] Company statistics API with plan distribution
- [x] Company CRUD with admin modal-based management UI
- [x] Company lookup by domain
- [x] Multi-tenancy support with data isolation by company
- [x] Tenant management API (list, detail, stats, user assignment)
- [x] Tenant-scoped environment variables
- [x] Tenant dashboard with company-specific metrics
- [x] User assignment and removal from companies
- [x] Tenant management UI for superusers

## API Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/health` | GET | Health check (API + database) | No |
| `/api/v1/auth/login` | POST | User login with email/password | No |
| `/api/v1/users/` | POST | Create new user | Yes (Superuser) |
| `/api/v1/users/` | GET | List all users (supports `?search=`) | Yes (Active user) |
| `/api/v1/users/me` | GET | Get current user profile | Yes (Active user) |
| `/api/v1/users/me/profile` | PUT | Update own profile (name, username, email) | Yes (Active user) |
| `/api/v1/users/me/change-password` | POST | Change own password | Yes (Active user) |
| `/api/v1/users/{id}` | GET | Get user by ID | Yes (Active user) |
| `/api/v1/users/{id}` | PUT | Update user | Yes (Superuser) |
| `/api/v1/users/{id}` | DELETE | Delete user | Yes (Superuser) |
| `/api/v1/companies/` | POST | Create new company (all fields) | Yes (Superuser) |
| `/api/v1/companies/` | GET | List companies (search, filter, paginate, sort) | Yes (Active user) |
| `/api/v1/companies/stats` | GET | Get company statistics (counts, plan distribution) | Yes (Active user) |
| `/api/v1/companies/by-domain/{domain}` | GET | Get company by domain | Yes (Active user) |
| `/api/v1/companies/{id}` | GET | Get company by ID (with user count) | Yes (Active user) |
| `/api/v1/companies/{id}` | PUT | Update company (any fields) | Yes (Superuser) |
| `/api/v1/companies/{id}` | DELETE | Delete company | Yes (Superuser) |
| `/api/v1/dashboard/summary` | GET | Get dashboard summary | Yes (Active user) |
| `/api/v1/redis/health` | GET | Get Redis health status | No |
| `/api/v1/redis/stats` | GET | Get cache statistics | Yes (Active user) |
| `/api/v1/redis/flush` | DELETE | Flush all cache data | Yes (Superuser) |
| `/api/v1/environment-variables/` | POST | Create environment variable | Yes (Superuser) |
| `/api/v1/environment-variables/` | GET | List all environment variables | Yes (Active user) |
| `/api/v1/environment-variables/{id}` | GET | Get environment variable by ID | Yes (Active user) |
| `/api/v1/environment-variables/key/{key}` | GET | Get environment variable by key | Yes (Active user) |
| `/api/v1/environment-variables/{id}` | PUT | Update environment variable | Yes (Superuser) |
| `/api/v1/environment-variables/{id}` | DELETE | Delete environment variable | Yes (Superuser) |
| `/api/v1/environment-variables/export/.env` | GET | Export all environment variables | Yes (Superuser) |
| `/api/v1/tenants/` | GET | List all tenants with search/filter | Yes (Superuser) |
| `/api/v1/tenants/stats` | GET | Get global tenant statistics | Yes (Superuser) |
| `/api/v1/tenants/my-tenant` | GET | Get current user's tenant details | Yes (Active user with company) |
| `/api/v1/tenants/my-tenant/dashboard` | GET | Get current tenant's dashboard | Yes (Active user with company) |
| `/api/v1/tenants/my-tenant/users` | GET | Get users in current tenant | Yes (Active user with company) |
| `/api/v1/tenants/{company_id}` | GET | Get detailed tenant information | Yes (Superuser) |
| `/api/v1/tenants/{company_id}/users` | GET | Get users of a specific tenant | Yes (Superuser) |
| `/api/v1/tenants/assign` | POST | Assign user to a company | Yes (Superuser) |
| `/api/v1/tenants/remove` | POST | Remove user from company | Yes (Superuser) |

## Quick Start

### Prerequisites

- Docker and Docker Compose (v2.20+)
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/ai-bos/ai-bos.git
   cd ai-bos
   ```

2. Start all services:
   ```bash
   docker compose up --build
   ```

3. The backend automatically runs database migrations on startup via the entrypoint script.

4. Create admin user (first-time setup):
   ```bash
   docker compose exec backend python create_admin.py
   ```

5. Access the application:
   - **Frontend**: http://localhost:3000
   - **API Docs (Swagger)**: http://localhost:8000/api/v1/docs
   - **pgAdmin** (devtools profile): http://localhost:5050 (email: `admin@ai-bos.com`, password: `admin`)

### Docker Profiles

Optional services are available via Docker Compose profiles:

```bash
# Start with devtools (pgAdmin)
docker compose --profile devtools up --build
```

### Docker Commands

```bash
# Build images without starting
docker compose build

# Start services in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop services and remove volumes (reset database)
docker compose down -v

# Run migrations manually
docker compose exec backend alembic upgrade head

# Run tests inside container
docker compose exec backend pytest -v
```

### Local Development (Without Docker)

#### Backend

1. Create and activate virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start PostgreSQL and update `.env` with your database URL.

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

## Testing

Run the full test suite:
```bash
cd backend
pytest -v
```

Run tests with coverage:
```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

## Docker Architecture

The Docker setup follows production best practices:

### Multi-Stage Builds
- **Backend**: Builder stage installs dependencies (gcc, libpq-dev), runtime stage is minimal with only libpq
- **Frontend**: Builder stage compiles Next.js, runtime serves production build

### Security
- Non-root users (`appuser` for backend, `nextjs` for frontend)
- `.dockerignore` files prevent leaking secrets and dev files
- Environment variables via `env_file` (not hardcoded)

### Resilience
- Healthchecks on all services (database `pg_isready`, backend health API, frontend HTTP)
- `depends_on` with `condition: service_healthy` ensures correct startup order
- `restart: unless-stopped` for automatic recovery

### Networking
- All services on an isolated `ai-bos-network` bridge network
- No accidental host network exposure (only mapped ports are accessible)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Security

See [SECURITY.md](SECURITY.md) for our security policy and vulnerability reporting guidelines.

## Default Credentials

- **Email**: `admin@ai-bos.com`
- **Password**: `SecurePass123!`

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

### CI Pipeline (Continuous Integration)

The CI pipeline runs on every push to `main` and `develop` branches, and on pull requests to `main`:

1. **Backend Linting**: Code quality checks with flake8 and black formatting
2. **Backend Tests**: Comprehensive test suite with PostgreSQL and Redis services
3. **Frontend Linting**: Next.js linting and npm audit for security vulnerabilities
4. **Frontend Tests**: Jest tests with coverage reporting
5. **Frontend Build**: Production build verification
6. **Docker Build Check**: Multi-stage Docker builds with healthchecks
7. **Security Scanning**: Trivy vulnerability scanning for Docker images
8. **Integration Tests**: End-to-end testing with Docker Compose

### CD Pipeline (Continuous Deployment)

The CD pipeline runs on every push to `main` branch:

1. **Security Scan**: Trivy filesystem vulnerability scanning
2. **Build and Push**: Multi-arch Docker images pushed to GitHub Container Registry (GHCR)
3. **Image Scanning**: Post-build vulnerability scanning
4. **GitHub Release**: Automated release creation with image tags
5. **Deployment Summary**: Detailed deployment information in GitHub Actions summary

### Pipeline Features

- **Parallel Execution**: Jobs run in parallel where possible for faster feedback
- **Caching**: pip and npm cache for faster dependency installation
- **Security**: Multiple layers of vulnerability scanning (dependencies, Docker images, filesystem)
- **Quality Gates**: All tests, linting, and security scans must pass before deployment
- **Artifacts**: Test results and build artifacts uploaded for debugging
- **Monitoring**: Health checks on all services with proper startup ordering
- **Notifications**: Deployment success notifications

### Viewing Pipeline Status

[![CI Pipeline](https://github.com/ai-bos/ai-bos/actions/workflows/ci.yml/badge.svg)](https://github.com/ai-bos/ai-bos/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/ai-bos/ai-bos/actions/workflows/cd.yml/badge.svg)](https://github.com/ai-bos/ai-bos/actions/workflows/cd.yml)

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), Alembic, PostgreSQL, Redis
- **Frontend**: Next.js 14, TypeScript, React 18, Tailwind CSS
- **Authentication**: JWT (Bearer tokens), bcrypt password hashing
- **Caching**: Redis 7 for application-level caching
- **Infrastructure**: Docker, Docker Compose, GitHub Actions (CI/CD)
- **Testing**: Pytest, pytest-asyncio, pytest-cov, in-memory SQLite

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Project Status

- **Phase 1 (Foundation)**: ✅ Complete
- **Phase 2 (API Enhancement)**: ✅ Complete
- **Phase 3 (GitHub Repository)**: ✅ Complete
- **Phase 4 (Docker Configuration)**: ✅ Complete
- **Phase 5 (Redis Configuration)**: ✅ Complete

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed milestone tracking.
