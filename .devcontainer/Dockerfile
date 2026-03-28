# ─────────────────────────────────────────────────────────────────────────────
# Basis: offizielles Microsoft DevContainer-Image für Python 3.14
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

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
