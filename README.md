# Loan applications API
# TODO



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