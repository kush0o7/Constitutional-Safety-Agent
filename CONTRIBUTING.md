# Contributing

## Workflow

1. Create a branch from `main`
2. Keep changes scoped and modular
3. Add or update tests for behavior changes
4. Run checks locally before PR

## Backend checks

```bash
cd backend
pytest -q
.venv/bin/python -m evals.runner --suite evals/suites/core_redteam.json --out-dir evals/reports
```

## Frontend checks

```bash
cd frontend
npm install
npm run lint
npm run build
```

## Code standards

- Python: typed, small modules, explicit error handling
- FastAPI: validate all external input using Pydantic schemas
- Frontend: React + TypeScript with ESLint and Prettier
- Security: do not log secrets; sanitize prompt content before model calls

## Pull requests

- Include summary, test evidence, and risk notes
- Include screenshots for UI changes
- Keep commits descriptive and focused
