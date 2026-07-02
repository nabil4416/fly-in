PYTHON      := python3
PIP         := $(PYTHON) -m pip
MAIN        := main.py

# Default map (override with: make run FILE=maps/easy/xxx.txt)
FILE        ?= maps/challenger/01_the_impossible_dream.txt
VIZ_OUTPUT  ?= output/flyin_visualization.html

FLAKE8      := flake8
MYPY        := mypy
PYTEST      := pytest

.PHONY: all install run debug viz clean lint lint-strict test help

all: help

install:
	$(PIP) install --user -r requirements.txt

run:
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: input file not found: $(FILE)"; \
		echo "Usage: make run FILE=<input_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(MAIN) $(FILE)

debug:
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: input file not found: $(FILE)"; \
		echo "Usage: make debug FILE=<input_file>"; \
		exit 1; \
	fi
	$(PYTHON) -m pdb $(MAIN) $(FILE)

viz:
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: input file not found: $(FILE)"; \
		echo "Usage: make viz FILE=<input_file>"; \
		exit 1; \
	fi
	$(PYTHON) scripts/visualize.py "$(FILE)" --output "$(VIZ_OUTPUT)"
	@echo "Visualization generated: $(VIZ_OUTPUT)"

lint:
	-$(FLAKE8) .
	-$(MYPY) core models utils main.py scripts/visualize.py

lint-strict:
	-$(MYPY) --strict core models utils main.py scripts/visualize.py

test:
	$(PYTHON) -m $(PYTEST) -v --tb=short

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "Available targets:"
	@echo "  make install"
	@echo "  make run"
	@echo "  make run FILE=<input_file>"
	@echo "  make debug FILE=<input_file>"
	@echo "  make viz FILE=<input_file> [VIZ_OUTPUT=output/file.html]"
	@echo "  make clean"
	@echo "  make lint"
	@echo "  make lint-strict"
	@echo "  make test"
	@echo "  make help"
