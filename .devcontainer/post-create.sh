#!/usr/bin/env bash
set -euo pipefail

echo "──────────────────────────────────────────"
echo "  📦 Wochenplaner – Dev-Setup"
echo "──────────────────────────────────────────"

# Fix: Docker Volumes werden als root initialisiert → Ownership korrigieren
sudo chown -R vscode:vscode /home/vscode/.cache/uv 2>/dev/null || true
sudo chown -R vscode:vscode /home/vscode/.config/matplotlib 2>/dev/null || true

# Lockfile vorhanden → --frozen (reproduzierbar), sonst sync + Hinweis
if [ -f uv.lock ]; then
    echo "🔒 uv.lock gefunden → uv sync --frozen"
    uv sync --frozen
else
    echo "⚠️  Kein uv.lock → uv sync (generiert Lockfile)"
    uv sync
    echo ""
    echo "💡 Tipp: Committe uv.lock für reproduzierbare Builds!"
    echo "   git add uv.lock && git commit -m 'chore: add uv.lock'"
fi

echo ""
echo "✅ Setup abgeschlossen."
echo "   App starten: uv run streamlit run app.py"
echo "   oder kurz:   start   (Shell-Alias)"
echo "──────────────────────────────────────────"
