# ─────────────────────────────────────────────────────────────────────────────
# Basis: offizielles Microsoft DevContainer-Image für Python 3.13
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# Playwright/Chromium (HTML→PDF): Laufzeitbibliotheken für Headless-Browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# ── uv installieren ───────────────────────────────────────────────────────────
RUN pip install --no-cache-dir uv

# ── Umgebungsvariablen ────────────────────────────────────────────────────────
# Matplotlib: beschreibbares Cache-Verzeichnis (Docker-Volume-Permission-Fix)
ENV MPLCONFIGDIR=/home/vscode/.config/matplotlib

# ── Cache-Verzeichnisse anlegen ───────────────────────────────────────────────
RUN mkdir -p /home/vscode/.config/matplotlib \
    && chown -R vscode:vscode /home/vscode/.config/matplotlib

# ── Shell-Komfort ─────────────────────────────────────────────────────────────
RUN echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.zshrc \
    && echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.bashrc
