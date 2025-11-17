PYTHON?=python
NPX?=npx

.PHONY: install-backend install-frontend install lint test dev-backend dev-frontend

install-backend:
	$(PYTHON) -m pip install -e .[dev]

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

lint:
	./scripts/run_linters.sh

test:
	./scripts/run_tests.sh

dev-backend:
	./scripts/dev.sh

dev-frontend:
	cd frontend && npm run dev
