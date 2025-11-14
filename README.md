# Loan applications API

# WIP Usage Instructions

### Quick Start (One Command)
```bash
# Clone and setup
git clone <repository-url>
cd loan-applications
make start


make start        # 🚀 Full setup & start
make start-quick  # 🚀 Quick background start  
make stop         # 🛑 Stop all services
make dev          # 🎯 Development server only
make test         # 🧪 Run tests
make lint         # 🎨 Code quality
make shell        # 💻 Container shell
make logs         # 📝 View logs
make help         # 🆘 All commands

# initial DB install
docker compose run --rm web alembic revision --autogenerate -m "initial_tables"
docker compose run --rm web alembic upgrade head


# Start the development environment:
make dev-all

## Run specific services:

bash
# Just database
make db-up

# Web app only
make dev

# Celery worker only
make worker

# Run migrations
make migrate

# Run tests:
make test

# Code quality:
make lint

# Rebuild everything
make rebuild


curl -X POST "http://localhost:8000/api/v1/applications" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "phone": "+420123456789",
       "full_name": "Jan Novák",
       "date_of_birth": "1985-05-15",
       "citizenship": "CZE",
       "monthly_income": 45000,
       "income_history": [45000, 44000, 46000],
       "income_type": "zaměstnání",
       "employment_length": 36,
       "housing_type": "vlastní",
       "education_level": "vysokoškolské",
       "marital_status": "vdaná/ženatý",
       "dependents_count": 2,
       "loan_amount": 500000,
       "loan_purpose": "Koupě automobilu"
     }'