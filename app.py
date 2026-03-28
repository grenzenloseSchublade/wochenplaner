"""
Wochenplaner – lokale Streamlit-App
Start: uv run streamlit run app.py
"""

import csv
import html as html_lib
import io
import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from calendar_render import render_calendar
from constants import (
    AKTIVITAETEN_FARBEN,
    DATA_DIR,
    DATA_FILE,
    DEFAULT_VON,
    END_HOUR,
    PLANS_DIR,
    PX_PER_MIN,
    START_HOUR,
    TIME_OPTIONS,
    WOCHENTAGE,
)
from pdf_export import generate_pdf
from utils import (
    Activity,
    check_overlap,
    get_text_color,
    safe_filename,
    slugify,
    t2m,
    validate_activity,
    validate_color,
)


# ── Datenzugriff ──────────────────────────────────────────────────────────────
def load_activities(fp: Path | None = None) -> list[Activity]:
    fp = fp or DATA_FILE
    if not fp.exists():
        return []
    try:
        data = json.loads(fp.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if validate_activity(item)]


def save_activities(a: list[Activity], fp: Path | None = None) -> None:
    fp = fp or DATA_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(a, ensure_ascii=False, indent=2), "utf-8")


def list_json_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []


def _sort_activities(acts: list[Activity]) -> list[Activity]:
    day_order = {d: i for i, d in enumerate(WOCHENTAGE)}
    return sorted(acts, key=lambda a: (day_order.get(a["day"], 99), a["start"]))


def _export_csv(acts: list[Activity]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Name", "Tag", "Von", "Bis", "Farbe"])
    for a in _sort_activities(acts):
        writer.writerow([a["name"], a["day"], a["start"], a["end"], a["color"]])
    return buf.getvalue()


# ── Statistik ────────────────────────────────────────────────────────────────
def render_statistics(activities: list[Activity]) -> None:
    import plotly.graph_objects as go

    if not activities:
        st.info("Keine Aktivitäten für Statistik vorhanden.")
        return

    time_per: dict[str, int] = {}
    color_per: dict[str, str] = {}
    for act in activities:
        dur = t2m(act["end"]) - t2m(act["start"])
        if dur > 0:
            name = act["name"]
            time_per[name] = time_per.get(name, 0) + dur
            if name not in color_per:
                color_per[name] = act.get("color", "#4a6fa5")

    if not time_per:
        st.info("Keine gültigen Zeitblöcke.")
        return

    total_h = sum(time_per.values()) / 60
    st.metric("Gesamtstunden / Woche", f"{total_h:.1f} h")

    names = list(time_per)
    hours = [v / 60 for v in time_per.values()]
    colors = [color_per.get(n, "#4a6fa5") for n in names]

    fig = go.Figure(
        go.Bar(
            x=hours,
            y=names,
            orientation="h",
            marker_color=colors,
            marker_line=dict(width=0),
            hovertemplate="%{y}: %{x:.1f}h<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Stunden",
        yaxis_title="",
        margin=dict(l=10, r=20, t=40, b=30),
        title=dict(text="Zeitverteilung", font=dict(size=14)),
        xaxis=dict(showgrid=True, gridwidth=1, zeroline=False),
        bargap=0.35,
    )
    st.plotly_chart(fig, width="stretch")


# ── Haupt-UI ─────────────────────────────────────────────────────────────────
def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    st.set_page_config(
        page_title="Wochenplaner",
        page_icon=":stopwatch:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.html("""
<style>
    section[data-testid="stSidebar"] { overflow-x: hidden; }
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
    .stExpander summary { font-size: .85rem; font-weight: 600; }
    .stButton > button, .stDownloadButton > button { border-radius: 6px; }
    .stRadio [role="radiogroup"] label { font-size: .83rem; }
</style>
""")

    _defaults: list[tuple] = [
        ("activities", None),
        ("edit_mode", None),
        ("plan_title", "Mein Wochenplan"),
        ("pdf_bytes", None),
        ("custom_activities", None),
    ]
    for k, v in _defaults:
        if k not in st.session_state:
            if k == "activities":
                st.session_state[k] = load_activities()
            elif k == "custom_activities":
                st.session_state[k] = []
            else:
                st.session_state[k] = v
    acts: list[Activity] = st.session_state.activities

    with st.sidebar:
        st.title("Wochenplaner")
        st.caption("Lokale App · Daten automatisch gespeichert")

        ea = st.session_state.edit_mode
        _lbl = "Bearbeiten" if ea else "Aktivität hinzufügen"
        with st.expander(_lbl, expanded=True):
            # Zusammengeführte Liste: vordefinierte + benutzerdefinierte
            all_names = list(AKTIVITAETEN_FARBEN) + [
                n
                for n in st.session_state.custom_activities
                if n not in AKTIVITAETEN_FARBEN
            ]

            use_custom = st.checkbox("Eigene Aktivität", key="chk_custom")
            if use_custom:
                name = st.text_input("Name der Aktivität", key="custom_name")
                if name and name not in st.session_state.custom_activities:
                    st.session_state.custom_activities.append(name)
            else:
                _def_name = ea["name"] if ea else all_names[0]
                name = st.selectbox(
                    "Aktivität",
                    all_names,
                    index=all_names.index(_def_name) if _def_name in all_names else 0,
                )

            _color_default = (
                ea["color"] if ea else AKTIVITAETEN_FARBEN.get(name, "#F3E5AB")
            )
            color = st.color_picker(
                "Farbe", _color_default, key=f"color_{name}_{id(ea)}"
            )

            _def_tag = ea["day"] if ea else WOCHENTAGE[0]
            tag = st.selectbox(
                "Tag",
                WOCHENTAGE,
                index=WOCHENTAGE.index(_def_tag) if _def_tag in WOCHENTAGE else 0,
            )

            _def_von = ea["start"] if ea else DEFAULT_VON
            _c1, _c2 = st.columns(2)
            with _c1:
                _von_idx = (
                    TIME_OPTIONS.index(_def_von)
                    if _def_von in TIME_OPTIONS
                    else TIME_OPTIONS.index(DEFAULT_VON)
                )
                von = st.selectbox("Von", TIME_OPTIONS, index=_von_idx)
            with _c2:
                _def_bis = ea["end"] if ea else None
                bo = (
                    TIME_OPTIONS[TIME_OPTIONS.index(von) + 1 :]
                    if von in TIME_OPTIONS
                    else TIME_OPTIONS
                )
                _bis_idx = (
                    bo.index(_def_bis) if _def_bis in bo else (1 if len(bo) > 1 else 0)
                )
                bis = st.selectbox("Bis", bo, index=_bis_idx)

            def _do_save() -> None:
                if ea:
                    ea.update(
                        name=name,
                        day=tag,
                        start=von,
                        end=bis,
                        color=color,
                    )
                    st.session_state.edit_mode = None
                else:
                    acts.append(
                        Activity(
                            id=str(uuid.uuid4()),
                            name=name,
                            day=tag,
                            start=von,
                            end=bis,
                            color=color,
                        )
                    )
                save_activities(acts)
                st.rerun()

            if not name:
                st.warning("Bitte einen Aktivitätsnamen eingeben.")
            elif t2m(bis) <= t2m(von):
                st.error("Endzeit muss nach Startzeit liegen.")
            else:
                _conflicts = check_overlap(
                    acts, tag, von, bis, ea["id"] if ea else None
                )
                if _conflicts:
                    _cn = ", ".join(c["name"] for c in _conflicts)
                    st.warning(f"Zeitüberschneidung mit: **{_cn}**")
                    if st.button(
                        "Trotzdem speichern",
                        width="stretch",
                        key="btn_force",
                    ):
                        _do_save()
                    if st.button(
                        "Abbrechen",
                        width="stretch",
                        key="btn_ovlp_cancel",
                    ):
                        st.session_state.edit_mode = None
                        st.rerun()
                else:
                    _slbl = "Speichern" if ea else "+ Hinzufügen"
                    if st.button(
                        _slbl,
                        width="stretch",
                        type="primary",
                        key="btn_save",
                    ):
                        _do_save()

            if ea:
                if st.button(
                    "Abbrechen",
                    width="stretch",
                    key="btn_cancel_edit",
                ):
                    st.session_state.edit_mode = None
                    st.rerun()

        # ── Einträge (sortiert nach Tag + Uhrzeit) ──────────────────────────
        if acts:
            with st.expander(f"Einträge ({len(acts)})", expanded=False):
                for _act in _sort_activities(acts):
                    _ns = html_lib.escape(_act["name"])
                    _ac = validate_color(_act["color"])
                    _tc = get_text_color(_ac)
                    st.markdown(
                        f"<div style='background:{_ac};color:{_tc};"
                        "padding:4px 10px;border-radius:4px;font-size:12px;"
                        "margin-bottom:2px;overflow-wrap:anywhere;"
                        "word-break:break-word'>"
                        f"<b>{_ns}</b>&nbsp;&middot;&nbsp;"
                        f"{html_lib.escape(_act['day'][:2])}&nbsp;"
                        f"{html_lib.escape(_act['start'])}"
                        f"\u2013{html_lib.escape(_act['end'])}"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    _eb, _db = st.columns(2)
                    with _eb:
                        if st.button(
                            "Bearbeiten",
                            key=f"e_{_act['id']}",
                            width="stretch",
                        ):
                            st.session_state.edit_mode = _act
                            st.rerun()
                    with _db:
                        if st.button(
                            "Löschen",
                            key=f"d_{_act['id']}",
                            width="stretch",
                        ):
                            acts.remove(_act)
                            save_activities(acts)
                            st.rerun()
                    st.divider()
                _confirm = st.checkbox("Wirklich alle löschen?", key="chk_del_all")
                if st.button(
                    "Alle löschen",
                    width="stretch",
                    key="btn_del_all",
                    disabled=not _confirm,
                ):
                    st.session_state.activities = []
                    save_activities([])
                    st.rerun()

        # ── PDF erzeugen ─────────────────────────────────────────────────────
        with st.expander("PDF erzeugen", expanded=False):
            st.session_state.plan_title = st.text_input(
                "Plantitel", st.session_state.plan_title, key="pti"
            )
            fmt = st.radio("Format", ["DIN A4", "DIN A5"], horizontal=True)
            with st.expander("Zeitbereich", expanded=False):
                sh_s = st.slider("Startzeit (Uhr)", 0, 23, START_HOUR)
                eh_s = st.slider("Endzeit   (Uhr)", 1, 24, END_HOUR)
            if st.button(
                "PDF erzeugen",
                width="stretch",
                type="primary",
                key="btn_pdf",
            ):
                if not acts:
                    st.warning("Keine Aktivitäten vorhanden.")
                elif sh_s >= eh_s:
                    st.error("Startzeit muss kleiner als Endzeit sein.")
                else:
                    with st.spinner("PDF wird generiert..."):
                        st.session_state.pdf_bytes = generate_pdf(
                            acts,
                            paper_format=fmt.replace("DIN ", ""),
                            start_hour=sh_s,
                            end_hour=eh_s,
                            title=st.session_state.plan_title,
                        )
            if st.session_state.pdf_bytes is not None:
                _slug = slugify(st.session_state.plan_title)
                _pdf_name = f"{_slug}.pdf"
                _pdf_path = PLANS_DIR / _pdf_name
                _pdf_path.write_bytes(st.session_state.pdf_bytes)
                st.toast(f"PDF gespeichert: data/plans/{_pdf_name}")
                st.download_button(
                    "PDF herunterladen",
                    data=st.session_state.pdf_bytes,
                    file_name=_pdf_name,
                    mime="application/pdf",
                    width="stretch",
                    key="btn_pdf_dl",
                )

        # ── Dateiverwaltung ──────────────────────────────────────────────────
        with st.expander("Dateiverwaltung", expanded=False):
            jf = list_json_files()
            if jf:
                sel = st.selectbox("Wochenplan laden", [p.stem for p in jf], key="imp")
                if st.button("Laden", width="stretch", key="btn_load"):
                    try:
                        st.session_state.activities = load_activities(
                            DATA_DIR / f"{sel}.json"
                        )
                        st.toast(f"Geladen: {sel}")
                    except (json.JSONDecodeError, KeyError) as exc:
                        st.error(f"Fehler beim Laden: {exc}")
                    else:
                        st.rerun()
            else:
                st.caption("Keine gespeicherten Pläne gefunden.")

            st.divider()

            en = st.text_input(
                "Dateiname",
                datetime.now().strftime("%Y-%m-%d_wochenplan"),
                key="en",
            )
            if st.button(
                "Speichern unter",
                width="stretch",
                key="btn_saveas",
            ):
                safe_name = safe_filename(en.strip() or "wochenplan")
                save_activities(acts, DATA_DIR / f"{safe_name}.json")
                st.toast(f"Gespeichert: {safe_name}.json")

            st.divider()

            # JSON-Upload
            uploaded = st.file_uploader(
                "JSON importieren",
                type=["json"],
                key="json_upload",
            )
            if uploaded is not None:
                try:
                    raw = json.loads(uploaded.read().decode("utf-8"))
                    if isinstance(raw, list):
                        valid = [item for item in raw if validate_activity(item)]
                        if valid:
                            st.session_state.activities = valid
                            save_activities(valid)
                            st.toast(f"{len(valid)} Aktivitäten importiert")
                            st.rerun()
                        else:
                            st.error("Keine gültigen Aktivitäten in der Datei.")
                    else:
                        st.error("JSON muss eine Liste von Aktivitäten sein.")
                except json.JSONDecodeError:
                    st.error("Ungültige JSON-Datei.")

            # CSV-Export
            if acts:
                st.divider()
                st.download_button(
                    "CSV exportieren",
                    data=_export_csv(acts),
                    file_name=(f"{datetime.now().strftime('%Y-%m-%d')}_wochenplan.csv"),
                    mime="text/csv",
                    width="stretch",
                    key="btn_csv",
                )

    # ── Hauptbereich: Tabs ───────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["Kalender", "Statistik"])

    with tab1:
        _th = (
            "<h2 style='text-align:center;margin-bottom:12px;"
            "font-weight:600;letter-spacing:.02em'>"
            + html_lib.escape(st.session_state.plan_title)
            + "</h2>"
        )
        st.markdown(_th, unsafe_allow_html=True)
        components.html(
            render_calendar(
                json.dumps(acts, ensure_ascii=False),
                START_HOUR,
                END_HOUR,
                _today=datetime.now().strftime("%Y-%m-%d"),
            ),
            height=int((END_HOUR - START_HOUR) * 60 * PX_PER_MIN) + 60,
            scrolling=False,
        )
        if not acts:
            st.caption("<- Füge im Menü deine erste Aktivität hinzu.")

    with tab2:
        st.markdown("## Zeitverteilung")
        render_statistics(acts)


if __name__ == "__main__":
    main()
