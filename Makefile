.PHONY: install run debug clean lint lint-strict help

# Python interpreter
PYTHON := python3

# Project name
PROJECT_NAME := fly-in

# Help target (default)
help:
	@echo "$(PROJECT_NAME) - Drone Simulation Project"
	@echo "=========================================="
	@echo "Available targets:"
	@echo "  make install       Install dependencies"
	@echo "  make run           Run the simulation"
	@echo "  make debug         Run with debugger (pdb)"
	@echo "  make clean         Remove cache files"
	@echo "  make lint          Run flake8 and mypy checks"
	@echo "  make lint-strict   Run strict mypy checks (optional)"
	@echo "  make test          Run unit tests"
	@echo "  make help          Show this help message"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install flake8 mypy pytest pytest-cov
	@echo "✅ Dependencies installed"

# Run the main script
run:
	@echo "🚀 Running simulation..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run FILE=<input_file>"; \
		exit 1; \
	fi
	$(PYTHON) main.py $(FILE)

# Run with debugger
debug:
	@echo "🐛 Running with debugger (pdb)..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make debug FILE=<input_file>"; \
		exit 1; \
	fi
	$(PYTHON) -m pdb main.py $(FILE)

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "✅ Cache cleaned"

# Linting: flake8 + mypy with mandatory flags
lint:
	@echo "🔍 Running linting checks..."
	@echo "  - flake8..."
	$(PYTHON) -m flake8 .
	@echo "  - mypy..."
	$(PYTHON) -m mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs
	@echo "✅ Linting passed"

# Strict linting (optional)
lint-strict:
	@echo "🔍 Running STRICT linting checks..."
	@echo "  - flake8..."
	$(PYTHON) -m flake8 .
	@echo "  - mypy (strict mode)..."
	$(PYTHON) -m mypy . --strict
	@echo "✅ Strict linting passed"

# Run unit tests
test:
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest -v --tb=short
	@echo "✅ Tests completed"

# All-in-one: clean, lint, test
all: clean lint test
	@echo "✅ All checks passed!"