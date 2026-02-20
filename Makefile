POETRY := python -m poetry

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' ${MAKEFILE_LIST} | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'


all: format static test

format: ## Format code
	black src
	isort src

format_check: ## Check code formatting
	black --check src
	isort src --check-only

static: ## Run static analysis
	flake8 src
	mypy src

test: ## Run tests
	pytest --cov-report term-missing --cov=. src

test_coverage: ## Test coverage
	coverage run --source src -m pytest src && coverage report -m | tee .coverage_report
	tail -n1 .coverage_report | tr -d % | awk '$$NF < 50 { print "Test coverage should be >50%."; exit 1 }'

scan: ## Scan code
	semgrep --config "p/bandit" --config "p/owasp-top-ten" src
	poetry export --without-hashes -f requirements.txt | safety check --policy-file .safety-policy.yml --full-report --stdin

pre_commit: ## Run pre-commit
	pre-commit install
	pre-commit run --all-files

install: ## install
	$(POETRY) install --no-root --with dev

install.pre_commit: ## install pre-commit
	pre-commit install

run: ## Run app
	cd src && python main.py

migrations:  ## Create migrations
	cd src && alembic revision --autogenerate -m "$(message)"

migrate: ## Migrate
	cd src && alembic upgrade head

# Flags

.PHONY: *
