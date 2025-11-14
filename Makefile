.PHONY: start start-quick stop dev test lint clean logs shell migrate

# 🚀 Zero-configuration one-command setup
start:
	@echo "🚀 Starting Loan Application System"
	@echo "📦 Building and starting all services..."
	docker compose build --no-cache
	@echo "🔄 Starting infrastructure services..."
	docker compose up -d postgres redis
	@echo "⏳ Waiting for databases to be ready..."
	@while ! docker compose exec postgres pg_isready -U user -d loan_system > /dev/null 2>&1; do \
		echo "Waiting for PostgreSQL..."; \
		sleep 3; \
	done
	@echo "✅ Databases are ready!"
	@echo "🔄 Running database migrations..."
	docker compose run --rm web alembic upgrade head
	@echo "🎯 Starting all application services..."
	docker compose up

# 🚀 Quick start (background services)
start-quick:
	@echo "🚀 Quick starting all services in background..."
	docker compose up -d

# 🛑 Stop everything
stop:
	@echo "🛑 Stopping all services..."
	docker compose down

# 🔄 Restart services
restart:
	@echo "🔁 Restarting services..."
	docker compose restart

# 📊 Development commands
dev:
	@echo "🎯 Starting development server only..."
	docker compose up web

dev-all:
	@echo "🎯 Starting all development services..."
	docker compose up

# 🧪 Testing
test:
	@echo "🧪 Running tests..."
	docker compose run --rm web pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	docker compose run --rm web pytest --cov=app --cov-report=html

# 🎨 Code quality
lint:
	@echo "🎨 Running code quality checks..."
	docker compose run --rm web black app tests
	docker compose run --rm web isort app tests
	docker compose run --rm web flake8 app tests
	docker compose run --rm web mypy app

# 🗑️ Cleanup
clean:
	@echo "🗑️ Cleaning up containers and volumes..."
	docker compose down -v
	docker system prune -f

# 📝 Logs
logs:
	@echo "📝 Showing service logs..."
	docker compose logs -f

# 💻 Development shell
shell:
	@echo "💻 Opening shell in web container..."
	docker compose exec web bash

# 🗃️ Database migrations
migrate:
	@echo "🗃️ Running database migrations..."
	docker compose run --rm web alembic upgrade head

migrate-create:
	@echo "🗃️ Creating new migration..."
	docker compose run --rm web alembic revision --autogenerate -m "$(message)"

# 🔧 Database operations
db-reset:
	@echo "🔄 Resetting database..."
	docker compose down -v
	docker volume rm loan-applications_postgres_data || true
	docker compose up -d postgres redis
	@sleep 10
	docker compose run --rm web alembic upgrade head

# 📋 Status check
status:
	@echo "📋 Service status:"
	@docker compose ps

# 🆘 Help
help:
	@echo "Loan Approval System - Enterprise Development Commands:"
	@echo "  make start        - 🚀 Full setup & start (one command for new developers)"
	@echo "  make start-quick  - 🚀 Quick background start"
	@echo "  make stop         - 🛑 Stop all services"
	@echo "  make restart      - 🔄 Restart services"
	@echo "  make dev          - 🎯 Start development server"
	@echo "  make test         - 🧪 Run tests"
	@echo "  make lint         - 🎨 Code quality checks"
	@echo "  make clean        - 🗑️ Full cleanup"
	@echo "  make logs         - 📝 View logs"
	@echo "  make shell        - 💻 Container shell"
	@echo "  make migrate      - 🗃️ Run migrations"
	@echo "  make status       - 📋 Service status"
	@echo "  make help         - 🆘 This help message"