# Run pytest with coverage
test:
    pytest --cov --cov-config=./tests/.coveragerc --cov-report=term-missing -n auto --e2e tests

# Format code using ruff, and standard
reformat:
    ruff check . --fix
    npx standard client/ --fix

# Run linting checks
lint:
    ruff check . --no-fix
    npx standard client/

# Build the project
build:
    npm run build
    npm run buildsmall
    python3 -m build

# Check npm dependencies for known vulnerabilities
audit:
    npm audit --audit-level=high

# Run JavaScript security pattern checks
security-check:
    bash scripts/js-security-check.sh

# Run semgrep security analysis
semgrep:
    semgrep --config p/django --config p/javascript --config .semgrep.yml src/django_tomselect/

# Initialize the development environment
init:
    uv sync --extra dev
    npm install --include=dev
    npm run build
    npm run buildsmall
