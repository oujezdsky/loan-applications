#!/bin/bash
set -e

echo "🚀 Loan Application System"
echo "===================================================="

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created. Please review and configure if needed."
    else
        echo "⚠️  .env.example not found, creating basic .env file..."
        cat > .env << EOF
# Environment
ENVIRONMENT=development

# Database
POSTGRES_DB_URL=postgresql://user:password@localhost:5433/loan_system
TEST_POSTGRES_DB_URL=postgresql://user:password@localhost:5433/loan_system_test

# Redis
REDIS_URL=redis://localhost:6380/0

# Security
SECRET_KEY=dev-secret-key-change-in-production

# Application Settings
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=5
VERIFICATION_TIMEOUT_HOURS=24
EOF
    fi
fi

# Ensure proper permissions for critical directories
echo "🔧 Setting up directory permissions..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   make start     - Start the full application"
echo "   make start-quick - Quick start (background)"
echo ""
echo "📖 For more commands: make help"