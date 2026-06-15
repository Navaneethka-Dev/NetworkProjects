.PHONY: install install-dev test test-cov lint format clean report

# ── Default ───────────────────────────────────────────────────────────────────
help:
	@echo "Available targets:"
	@echo "  install      Install runtime dependencies"
	@echo "  install-dev  Install dev + test dependencies"
	@echo "  test         Run unit tests"
	@echo "  test-cov     Run tests with HTML coverage report"
	@echo "  lint         Run flake8 linter"
	@echo "  format       Format code with black"
	@echo "  clean        Remove __pycache__, .pyc files, and reports"
	@echo "  demo         Run a quick demo against simulated devices"
	@echo "  report       Generate a sample compliance HTML report"

# ── Installation ──────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[test,dev]"

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=netautomate --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	flake8 netautomate/ main.py

format:
	black netautomate/ main.py tests/

# ── Housekeeping ──────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf reports/ htmlcov/ .coverage dist/ build/ *.egg-info

# ── Developer shortcuts ───────────────────────────────────────────────────────
demo:
	@echo "=== NetAutomate Pro Demo (Simulation Mode) ==="
	python main.py backup --all
	python main.py compliance --all
	python main.py deploy --device router1 --template templates/cisco_base.j2 --dry-run

report:
	python -c "\
from netautomate import NetworkAutomation; \
from netautomate.reporter import ReportGenerator; \
na = NetworkAutomation('inventory/devices.yaml'); \
results = na.check_compliance_all(); \
rg = ReportGenerator('reports'); \
path = rg.generate_compliance_report(results, fmt='html'); \
print(f'Report: {path}') \
"
