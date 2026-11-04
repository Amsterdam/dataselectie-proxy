.PHONY: help install sync lock upgrade test retest coverage format lint type typecheck
help:
	@grep -F -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | perl -pe 's/^(\w+):(.+?)##/"  $$1:" . " " x (20 - length($$1))/e' | perl -pe 's/^## ?//'

## Makefile to perform all tasks for development.
##
## Install commands:
##

.PHONY: install
install: 								## Perform all install steps.
	if ! command -v uv >/dev/null 2>&1; \
	then echo "uv not found, installing..." \
	&& curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv sync
	uv run pre-commit install

.PHONY: sync
sync:                                  ## Install packages, remove unmentioned packages
	uv sync

##
## Package management:
##

.PHONY: upgrade
upgrade:                               ## Upgrade locked dependencies
	uv sync --upgrade

##
## Testing:
##

.PHONY: test
test:                                  ## Run the test-suite.
	uv run pytest --reuse-db --nomigrations .

.PHONY: retest
retest:                                ## Run the failed tests again.
	uv run pytest --reuse-db --nomigrations -vvs --lf .

.PHONY: coverage
coverage:
	uv run pytest --reuse-db --nomigrations --cov=dataselectie_proxy --cov-report=term-missing

##
## Development tools:
##

.PHONY: format
format:                                ## Report Ruff formatting errors to all files.
	uv run ruff format .

.PHONY: lint
lint:                                  ## Report linting errors for all files
	uv run ruff check .

.PHONY: type
type:                                  ## Show typing errors for all files
	uv run ty check

##
