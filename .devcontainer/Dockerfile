# ─────────────────────────────────────────────────────────────────────────────
# Basis: offizielles Microsoft DevContainer-Image für Python 3.13
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# WeasyPrint (Modern-PDF, HTML→PDF): Pango/Cairo-Laufzeitbibliotheken.
# Spiegelt packages.txt (Streamlit Community Cloud) – kein Browser nötig.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libharfbuzz0b \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ── uv installieren ───────────────────────────────────────────────────────────
RUN pip install --no-cache-dir uv

# ── Umgebungsvariablen ────────────────────────────────────────────────────────
# Matplotlib: beschreibbares Cache-Verzeichnis (Docker-Volume-Permission-Fix)
ENV MPLCONFIGDIR=/home/vscode/.config/matplotlib
# uv: Cache-Volume liegt auf anderem Dateisystem → Hardlinks nicht möglich
ENV UV_LINK_MODE=copy

# ── Cache-Verzeichnisse anlegen ───────────────────────────────────────────────
RUN mkdir -p /home/vscode/.config/matplotlib \
    && chown -R vscode:vscode /home/vscode/.config/matplotlib

# ── Shell-Komfort ─────────────────────────────────────────────────────────────
RUN echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.zshrc \
    && echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.bashrc
