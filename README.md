# Loan applications API

# WIP Usage Instructions

### Quick Start (One Command)
```bash
# Clone and setup
git clone <repository-url>
cd loan-applications
make start

# Make options
make start        # 🚀 Full setup & start
make start-quick  # 🚀 Quick background start
make init-db      # 🗃️ Initialize database with migrations
make stop         # 🛑 Stop all services
make dev          # 🎯 Development server only
make test         # 🧪 Run tests
make lint         # 🎨 Code quality
make clean        # 🗑️ Docker cleanup (container, volumes...)
make shell        # 💻 Container shell (used with make start-quick)
make logs         # 📝 View logs
make help         # 🆘 All commands

# DB model update procedure
make migrate-create message="add_new_col_to_zoo_table"

# 2. Aplikujte migraci
make migrate


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