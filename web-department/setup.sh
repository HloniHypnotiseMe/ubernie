#!/usr/bin/env bash
# Web Department — local dev setup (Git Bash on Windows)
set -euo pipefail

cd "$(dirname "$0")"

echo "▶ Creating venv..."
python -m venv .venv

echo "▶ Activating venv..."
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

echo "▶ Upgrading pip..."
python -m pip install --upgrade pip

echo "▶ Installing requirements..."
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "▶ Creating .env from .env.example"
  cp .env.example .env
fi

echo ""
echo "✅ Setup complete."
echo ""
echo "To start the API:"
echo "  source .venv/Scripts/activate"
echo "  python api.py"
echo ""
echo "Then in another terminal:"
echo "  curl http://127.0.0.1:8100/health"
