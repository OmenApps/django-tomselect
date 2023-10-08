.PHONY: tox
tox:
	rm -rf .tox
	tox -p auto

.PHONY: test
test:
	pytest --cov --cov-config=./tests/.coveragerc --cov-report=term-missing -n auto --e2e tests

.PHONY: reformat
reformat:
	ruff check . --fix
	black .
	npx standard client/ --fix

.PHONY: lint
lint:
	ruff . --no-fix
	black . --check
	npx standard client/

.PHONY: build
build:
	npm run build
	npm run buildsmall
	python3 -m build

.PHONY: init
init:
	pip install -e .
	pip install -U -r requirements.txt
	npm install --include=dev
	npm run build
	npm run buildsmall