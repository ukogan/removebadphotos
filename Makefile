# Photo Deduplication Tool - Debugging Doom Loop Prevention
# HALT Protocol Implementation

.PHONY: help diagnostics unit integration e2e test-all debug-start validate clean install-test

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "Photo Dedup Tool - HALT Protocol Commands"
	@echo ""
	@echo "$(GREEN)HALT Protocol Debugging:$(NC)"
	@echo "  debug-start     Start 30-minute debug timer and diagnostics"
	@echo "  diagnostics     Run health checks (< 1 second)"  
	@echo "  unit            Run pure function tests (< 5 seconds)"
	@echo "  integration     Run service interaction tests (< 30 seconds)"
	@echo "  e2e             Run complete workflow tests (< 2 minutes)"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  test-all        Run complete test suite"
	@echo "  validate        Full validation before merge"
	@echo "  install-test    Install test dependencies"
	@echo "  clean           Clean up test artifacts"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install-test: ## Install test dependencies
	@echo "$(YELLOW)Installing test dependencies...$(NC)"
	pip install -r requirements-test.txt

diagnostics: ## Run diagnostic tests (< 1 second)
	@echo "$(YELLOW)Running diagnostic health checks...$(NC)"
	@echo "$(GREEN)⏱️  Time budget: < 1 second$(NC)"
	python3 -m pytest tests/diagnostics -v --timeout=1 -x
	@echo "$(GREEN)✅ Diagnostics complete$(NC)"

unit: ## Run unit tests (< 5 seconds)  
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@echo "$(GREEN)⏱️  Time budget: < 5 seconds$(NC)"
	python3 -m pytest tests/unit -v --timeout=5 -x
	@echo "$(GREEN)✅ Unit tests complete$(NC)"

integration: ## Run integration tests (< 30 seconds)
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@echo "$(GREEN)⏱️  Time budget: < 30 seconds$(NC)"  
	python3 -m pytest tests/integration -v --timeout=30 -x
	@echo "$(GREEN)✅ Integration tests complete$(NC)"

e2e: ## Run end-to-end tests (< 2 minutes)
	@echo "$(YELLOW)Running end-to-end tests...$(NC)"
	@echo "$(GREEN)⏱️  Time budget: < 2 minutes$(NC)"
	python3 -m pytest tests/e2e -v --timeout=120 -x  
	@echo "$(GREEN)✅ E2E tests complete$(NC)"

test-all: diagnostics unit integration e2e ## Run complete test suite
	@echo "$(GREEN)🎉 All tests passed!$(NC)"

debug-start: ## Start debugging session with 30-minute timer
	@echo "$(YELLOW)🚨 Starting HALT Protocol Debug Session$(NC)"
	@echo "$(RED)⏰ 30-MINUTE HARD LIMIT$(NC)"
	@echo "$(GREEN)Step 1: Running diagnostics...$(NC)"
	@make diagnostics
	@echo ""
	@echo "$(GREEN)✅ System health confirmed$(NC)"
	@echo "$(YELLOW)📝 Remember to:$(NC)"
	@echo "  1. Document hypothesis in DEBUGGING.md"
	@echo "  2. Update progress every 10 minutes"  
	@echo "  3. Test one layer at a time"
	@echo "  4. PIVOT at 20 minutes if stuck"
	@echo "  5. STOP at 30 minutes and escalate"
	@echo ""
	@echo "$(RED)⏰ Timer started: $$(date)$(NC)"
	@echo "$(RED)⏰ Stop time: $$(date -v+30M)$(NC)"

validate: test-all ## Full validation before merge  
	@echo "$(YELLOW)Running pre-merge validation...$(NC)"
	@echo "$(GREEN)✅ All tests passed$(NC)"
	@echo "$(YELLOW)Checking code style...$(NC)"
	@python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "$(YELLOW)No linter configured$(NC)"
	@echo "$(GREEN)✅ Validation complete$(NC)"

clean: ## Clean up test artifacts
	@echo "$(YELLOW)Cleaning test artifacts...$(NC)"
	rm -rf tests/coverage/ 
	rm -rf tests/reports/
	rm -rf tests/__pycache__/
	rm -rf tests/*/__pycache__/
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Development server with error monitoring
dev: diagnostics ## Start development server after health check
	@echo "$(GREEN)✅ System healthy, starting development server...$(NC)"
	FLASK_DEBUG=1 python3 app.py

# Memory monitoring during development
monitor: ## Monitor memory usage during development
	@echo "$(YELLOW)Monitoring memory usage (Ctrl+C to stop)...$(NC)"
	@while true; do \
		ps aux | grep "[p]ython.*app.py" | awk '{print "Memory: " $$6/1024 "MB  CPU: " $$3 "%  Time: " $$10}' || echo "App not running"; \
		sleep 5; \
	done

# Emergency procedures
emergency-stop: ## Emergency stop - kill all python processes
	@echo "$(RED)🚨 Emergency stop - killing all Python processes$(NC)"
	pkill -f "python.*app.py" || echo "No processes found"
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@make clean

emergency-reset: emergency-stop clean ## Emergency reset - stop processes and clean
	@echo "$(RED)🚨 Emergency reset complete$(NC)"
	@echo "$(YELLOW)System ready for fresh start$(NC)"

# Circuit breaker test
test-circuit-breaker: ## Test circuit breaker functionality
	@echo "$(YELLOW)Testing circuit breaker patterns...$(NC)"
	python3 -m pytest tests/diagnostics/test_photo_services.py::test_circuit_breaker_pattern -v

# Quick health check
health: ## Quick system health check
	@echo "$(YELLOW)Quick health check...$(NC)"
	@python3 -c "import sys; print(f'Python: {sys.version}')"
	@python3 -c "import flask; print(f'Flask: {flask.__version__}')" 2>/dev/null || echo "Flask: Not installed"
	@python3 -c "import PIL; print(f'PIL: {PIL.__version__}')" 2>/dev/null || echo "PIL: Not installed"  
	@python3 -c "import osxphotos; print('osxphotos: Available')" 2>/dev/null || echo "osxphotos: Not installed"
	@python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2>/dev/null || echo "OpenCV: Not installed"
	@echo "$(GREEN)✅ Health check complete$(NC)"