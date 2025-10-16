#!/bin/bash

# Auto Status Report Installation Script

echo "🚀 Installing Auto Status Report..."

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."

# Check if pyenv is available
if command -v pyenv &> /dev/null; then
    echo "Using pyenv for Python environment management..."
    pyenv virtualenv auto-status-report 2>/dev/null || echo "Virtual environment already exists"
    pyenv local auto-status-report
    pip install -r requirements.txt
else
    echo "Using system Python..."
    pip3 install -r requirements.txt
fi

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp config.env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env file with your GitHub token and OpenAI API key"
else
    echo "✅ .env file already exists"
fi

# Make main.py executable
chmod +x main.py

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Make sure Ollama is running:"
echo "   ollama serve"
echo ""
echo "2. Install a model (if not already done):"
echo "   ollama pull llama3:latest"
echo ""
echo "3. Edit .env file with your credentials:"
echo "   - GITHUB_TOKEN: Your GitHub personal access token"
echo "   - GITHUB_USERNAME: Your GitHub username"
echo "   - OLLAMA_MODEL: Your preferred model (e.g., llama3:latest)"
echo ""
echo "4. Test your setup:"
echo "   python3 main.py test"
echo ""
echo "5. Generate your first report:"
echo "   python3 main.py quick"
echo ""
echo "For more information, see README.md"
