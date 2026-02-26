#!/bin/bash
# Quick start script for PR-chat

echo "🚀 PR-chat Quick Start"
echo "===================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create venv
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Setup database
echo ""
echo "🗄️ Setting up database..."
python scripts/setup_db.py

# Copy .env if needed
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "💡 Edit .env to add your OpenAI API key (optional)"
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Add documents:"
echo "   python scripts/ingest.py <path-to-mp3-or-pdf>"
echo ""
echo "2. Build embeddings (for semantic search):"
echo "   python scripts/build_embeddings.py"
echo ""
echo "3. Run the app:"
echo "   streamlit run app/streamlit_app.py"
echo ""
