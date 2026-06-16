# Contributing to TaskFlow

Thank you for considering contributing to TaskFlow! This document outlines the guidelines for contributing.

## Code of Conduct

By participating, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/TaskFlow.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it and install dependencies: `pip install -r requirements.txt`
5. Install pre-commit hooks: `pre-commit install`
6. Create a branch: `git checkout -b feature/your-feature-name`

## Coding Standards

### Python
- Follow PEP 8 guidelines
- Use Black formatter (line length: 88)
- Sort imports with isort (black profile)
- Type hints are encouraged but not required

### JavaScript
- Use `'use strict'` mode
- Follow the existing IIFE pattern
- Use `var` consistently (ES5 compatibility)

### HTML/Templates
- Use consistent indentation (4 spaces)
- Follow existing Jinja2 patterns
- Keep templates minimal — logic in Python

### SQL
- Always use parameterized queries (`%s` placeholders)
- Never use f-strings or string concatenation for SQL
- Use explicit column names, not `SELECT *`

## Branch Naming

- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation changes
- `refactor/description` — Code refactoring

## Commit Messages

Follow conventional commits format:

```
type(scope): short description

Longer description if needed.
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(auth): add password reset flow`
- `fix(kanban): prevent duplicate task on drop`
- `docs(readme): update deployment section`

## Pull Request Process

1. Ensure your branch is up to date with `main`
2. Run `python -m py_compile app.py` to check syntax
3. Run `flake8 .` to check linting
4. Run all tests to ensure nothing is broken
5. Update documentation if needed (README, CHANGELOG)
6. Create a PR with a clear title and description
7. Link any related issues

## Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] All existing tests pass
- [ ] New tests added (if applicable)

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Testing Guidelines

- Write tests for all new functionality
- Follow the existing test pattern (simple assert, PASS/FAIL output)
- Tests should clean up after themselves
- Run the full test suite before submitting

## Questions?

Open an issue or reach out to the maintainers.
