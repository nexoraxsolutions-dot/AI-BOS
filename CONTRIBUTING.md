# Contributing to AI-BOS

Thank you for considering contributing to AI-BOS! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/ai-bos/ai-bos/issues)
2. If not, create a new issue using the **Bug Report** template
3. Provide detailed steps to reproduce the bug
4. Include information about your environment

### Suggesting Features

1. Check if the feature has already been suggested in [Issues](https://github.com/ai-bos/ai-bos/issues)
2. If not, create a new issue using the **Feature Request** template
3. Describe the problem you're trying to solve
4. Explain your proposed solution

### Pull Requests

1. Fork the repository
2. Create a new branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following the coding standards
4. Write or update tests as needed
5. Run the full test suite to ensure nothing is broken
6. Update documentation (README.md, etc.)
7. Commit your changes using conventional commit messages:
   ```
   feat: add new feature
   fix: correct bug in module
   docs: update documentation
   test: add test coverage
   refactor: restructure code
   chore: update dependencies
   ```
8. Push to your fork and submit a pull request to `develop`

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 16 (optional, Docker handles this)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/ai-bos/ai-bos.git
   cd ai-bos
   ```

2. Start the services:
   ```bash
   docker-compose up --build
   ```

3. Create admin user:
   ```bash
   docker-compose exec backend python create_admin.py
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/v1/docs

### Running Tests

```bash
cd backend
pytest -v
```

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function signatures
- Write async code using `async/await`
- Follow Clean Architecture principles:
  - Models → Schemas → Services → Endpoints
  - Dependency injection for database sessions
  - Separation of concerns between layers

### TypeScript/React (Frontend)

- Follow the [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- Use functional components with hooks
- Prefer TypeScript over plain JavaScript
- Use Tailwind CSS for styling

### Testing

- Write unit tests for all service layer functions
- Write integration tests for all API endpoints
- Use fixtures for test data and authentication tokens
- Aim for >80% code coverage

## Branch Naming Convention

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or improvements
- `chore/` - Maintenance tasks

## Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `style`

## Review Process

1. At least one code owner must approve the changes
2. All CI checks must pass
3. Code must follow the project's coding standards
4. Tests must be included for new functionality
5. Documentation must be updated where applicable

## Questions?

If you have questions, please open a [Discussion](https://github.com/ai-bos/ai-bos/discussions) or reach out to the maintainers.