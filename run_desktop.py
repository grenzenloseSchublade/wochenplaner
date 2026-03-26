# run_desktop.py – startet die App im nativen Desktop-Fenster (ohne Browser).
# Verwendung: uv run python run_desktop.py
#
# WICHTIG: if __name__ == "__main__" ist zwingend erforderlich.
# streamlit-desktop-app startet intern einen Prozess via multiprocessing.
# Ohne diesen Guard schlägt Python's Spawn/Forkserver-Context fehl (RuntimeError).
from streamlit_desktop_app import start_desktop_app

if __name__ == "__main__":
    start_desktop_app(
        "app.py",
        title="Wochenplaner",
        width=1280,
        height=900,
    )
