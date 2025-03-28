# Development Guidelines

## Build & Run Commands
- Run app: `uv run hello.py`
- Install dependencies: `uv add <package>` or `uv pip install -r requirements.txt`
- Update dependencies: `uv pip compile pyproject.toml -o requirements.txt`
- Create virtual environment: `uv venv`
- Run commands in virtual env: `uv run -- <command>`
- Upgrade a package: `uv lock --upgrade-package <package>`

## Testing Commands
- Run Python tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_file.py::test_function`
- Run JS tests: `CI=true yarn test path/to/file.spec.tsx`

## Code Style
- Python: Follow Black formatting (100 char line length)
- Type hints: Use mypy type annotations for all functions
- Imports: Group standard library, third-party, and local imports
- Error handling: Use explicit exception types, avoid bare except
- Variable naming: snake_case for variables, CamelCase for classes
- JavaScript: Follow ESLint rules and React component guidelines

## Project Structure
- `external/` directory contains cloned GitHub repositories for reference:
  - `sentry/`: Main Sentry backend/frontend codebase
  - `sentry-python/`: Python SDK for Sentry
  - `relay/`: Proxy service that validates and processes events

## Available Tools
- `gh` (GitHub CLI) is available for GitHub operations

## React Testing
- Use exports from 'sentry-test/reactTestingLibrary' instead of directly from '@testing-library/react'