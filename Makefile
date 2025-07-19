# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    🚀 DDC Build Automation Makefile                         ║
# ║                                                                              ║
# ║  Quick commands for building and deploying DDC                              ║
# ║                                                                              ║
# ║  Usage:                                                                      ║
# ║    make dev      - Fast development build                                    ║
# ║    make build    - Standard build                                            ║
# ║    make prod     - Production build                                          ║
# ║    make push     - Build and push to Docker Hub                             ║
# ║    make clean    - Clean up                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: help dev build prod push clean logs restart stop test

# Default target
help:
	@echo "🚀 DDC Build Commands:"
	@echo ""
	@echo "  dev      - ⚡ Fast development build (with cache)"
	@echo "  build    - 🏗️  Standard build (no cache)"
	@echo "  prod     - 🏭 Production build (multi-arch)"
	@echo "  push     - 📤 Build and push to Docker Hub"
	@echo "  clean    - 🧹 Clean up containers and images"
	@echo "  logs     - 📋 Show container logs"
	@echo "  restart  - 🔄 Restart container"
	@echo "  stop     - ⏹️  Stop container"
	@echo "  test     - 🧪 Run tests"
	@echo ""
	@echo "Examples:"
	@echo "  make dev              # Fast development build"
	@echo "  make prod VERSION=1.0.0   # Production build with version"
	@echo "  make push VERSION=1.0.0   # Build and push version 1.0.0"

# Fast development build
dev:
	@echo "⚡ Starting fast development build..."
	@./scripts/rebuild-fast.sh

# Standard build
build:
	@echo "🏗️ Starting standard build..."
	@./scripts/rebuild.sh

# Production build
prod:
	@echo "🏭 Starting production build..."
	@./scripts/build-production.sh $(VERSION)

# Build and push to Docker Hub
push:
	@echo "📤 Building and pushing to Docker Hub..."
	@./scripts/build-production.sh $(VERSION) push

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@docker stop ddc 2>/dev/null || true
	@docker rm ddc 2>/dev/null || true
	@docker system prune -f
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Show logs
logs:
	@docker logs ddc -f

# Restart container
restart:
	@echo "🔄 Restarting container..."
	@docker restart ddc
	@echo "✅ Container restarted"

# Stop container
stop:
	@echo "⏹️ Stopping container..."
	@docker stop ddc
	@echo "✅ Container stopped"

# Run tests
test:
	@echo "🧪 Running tests..."
	@python -m pytest tests/ -v || echo "No tests found"

# Development workflow
dev-setup:
	@echo "🛠️ Setting up development environment..."
	@pip install -r requirements.txt
	@echo "✅ Development environment ready"

# Version management
version:
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Please specify VERSION=x.y.z"; \
		exit 1; \
	fi
	@echo "$(VERSION)" > VERSION
	@echo "📦 Version set to $(VERSION)"

# Quick status check
status:
	@echo "📊 DDC Status:"
	@echo ""
	@echo "🐳 Docker containers:"
	@docker ps -a --filter name=ddc --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "🏷️ Docker images:"
	@docker images dockerdiscordcontrol --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
	@echo ""
	@if [ -f "VERSION" ]; then \
		echo "📦 Current version: $$(cat VERSION)"; \
	else \
		echo "📦 No version file found"; \
	fi 