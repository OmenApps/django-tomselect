# Run tox tests
tox:
    rm -rf .tox
    tox -p auto

# Run pytest with coverage
test:
    pytest --cov --cov-config=./tests/.coveragerc --cov-report=term-missing -n auto --e2e tests

# Format code using ruff, black, and standard
reformat:
    ruff check . --fix
    black .
    npx standard client/ --fix

# Run linting checks
lint:
    ruff check . --no-fix
    black . --check
    npx standard client/

# Build the project
build:
    npm run build
    npm run buildsmall
    python3 -m build

# Initialize the development environment
init:
    pip install -e .[dev]
    npm install --include=dev
    npm run build
    npm run buildsmall