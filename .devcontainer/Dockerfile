# ─────────────────────────────────────────────────────────────────────────────
# Basis: offizielles Microsoft DevContainer-Image für Python 3.14
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# ── uv installieren ───────────────────────────────────────────────────────────
RUN pip install --no-cache-dir uv

# ── Systempakete: GTK/Cairo Build-Deps für PyGObject (pip) ───────────────────
# Hinweis: python3-gi (apt) ist für System-Python 3.11 — nicht nutzbar in der
# Python-3.14-venv. PyGObject + pycairo werden via pip gebaut (pyproject.toml
# desktop-Gruppe). Diese Pakete stellen die nötigen C-Libs + Header bereit.
# PyGObject < 3.51.0: nutzt girepository-1.0 (libgirepository1.0-dev).
# Ab 3.51.0 wäre libgirepository-2.0-dev nötig (nicht in Debian Bookworm).
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgirepository1.0-dev \
        libcairo2-dev \
        libgtk-3-dev \
        libwebkit2gtk-4.0-dev \
        pkg-config \
        gir1.2-gtk-3.0 \
        gir1.2-webkit2-4.0 \
    && rm -rf /var/lib/apt/lists/*

# ── Umgebungsvariablen ────────────────────────────────────────────────────────
# Matplotlib: beschreibbares Cache-Verzeichnis (Docker-Volume-Permission-Fix)
ENV MPLCONFIGDIR=/home/vscode/.config/matplotlib
# Mesa: Shader-Cache deaktivieren — für GTK-UI nicht benötigt,
# verhindert "Permission denied"-Warnings beim Start der Desktop-App.
ENV MESA_SHADER_CACHE_DISABLE=true

# ── Cache-Verzeichnisse anlegen ───────────────────────────────────────────────
RUN mkdir -p /home/vscode/.config/matplotlib \
    && chown -R vscode:vscode /home/vscode/.config/matplotlib

# ── Shell-Komfort ─────────────────────────────────────────────────────────────
RUN echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.zshrc \
    && echo 'alias start="uv run streamlit run app.py"' >> /home/vscode/.bashrc
