.PHONY: orient validate build check test audit clean serve

PYTHON ?= python3

orient:
	@$(PYTHON) -m epistemedia orient

validate:
	@$(PYTHON) -m epistemedia validate

build:
	@$(PYTHON) -m epistemedia build --output generated/public

test:
	@$(PYTHON) -m pytest -q

audit:
	@$(PYTHON) -m epistemedia audit --public generated/public

check: validate build test audit
	@git diff --exit-code -- generated/public || (echo "generated/public is stale; commit the deterministic rebuild" && exit 1)

serve:
	@$(PYTHON) -m epistemedia serve --public generated/public --port 8000

clean:
	rm -rf generated/public .pytest_cache .ruff_cache **/__pycache__
