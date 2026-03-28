"""
Wochenplaner – Streamlit-App (Cloud & Lokal)
Start: uv run streamlit run app.py
"""

import base64
import csv
import html as html_lib
import io
import json
import uuid
import zlib
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
from i18n import (
    DAY_DISPLAY,
    DAY_FROM_DISPLAY,
    LANG_FLAGS,
    WOCHENTAGE_I18N,
    Lang,
    t,
)
from pdf_export import generate_pdf
from templates import get_template_activities, get_template_names
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

# ── Sharing helpers ──────────────────────────────────────────────────────────
_MAX_SHARE_BYTES = 1800  # URL-safe limit


def encode_plan(acts: list[Activity]) -> str | None:
    """Compress + base64-encode a plan for URL sharing."""
    raw = json.dumps(acts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw, 9)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    if len(encoded) > _MAX_SHARE_BYTES:
        return None
    return encoded


def decode_plan(data: str) -> list[Activity] | None:
    """Decode a shared plan from URL parameter."""
    try:
        compressed = base64.urlsafe_b64decode(data)
        raw = zlib.decompress(compressed, wbits=15, bufsize=1_000_000)
        if len(raw) > 1_000_000:
            return None
        items = json.loads(raw)
        if isinstance(items, list):
            return [item for item in items if validate_activity(item)]
    except Exception:
        pass
    return None


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
    try:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(a, ensure_ascii=False, indent=2), "utf-8")
    except OSError:
        pass  # Cloud: filesystem may be ephemeral


def list_json_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []


def _sort_activities(acts: list[Activity]) -> list[Activity]:
    day_order = {d: i for i, d in enumerate(WOCHENTAGE)}
    return sorted(acts, key=lambda a: (day_order.get(a["day"], 99), a["start"]))


def _export_csv(acts: list[Activity], lang: Lang = "de") -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    header = (
        ["Name", "Tag", "Von", "Bis", "Farbe"]
        if lang == "de"
        else ["Name", "Day", "From", "To", "Color"]
    )
    writer.writerow(header)
    for a in _sort_activities(acts):
        day_display = DAY_DISPLAY[lang].get(a["day"], a["day"])
        writer.writerow([a["name"], day_display, a["start"], a["end"], a["color"]])
    return buf.getvalue()


# ── Statistik ────────────────────────────────────────────────────────────────
def render_statistics(activities: list[Activity], lang: Lang = "de") -> None:
    import plotly.graph_objects as go

    if not activities:
        st.info(t("no_stats", lang))
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
        st.info(t("no_valid_blocks", lang))
        return

    total_h = sum(time_per.values()) / 60
    st.metric(t("total_hours", lang), f"{total_h:.1f} h")

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
        xaxis_title=t("hours_label", lang),
        yaxis_title="",
        margin=dict(l=10, r=20, t=40, b=30),
        title=dict(text=t("time_dist", lang), font=dict(size=14)),
        xaxis=dict(showgrid=True, gridwidth=1, zeroline=False),
        bargap=0.35,
    )
    st.plotly_chart(fig, width="stretch")


# ── SEO meta tags ────────────────────────────────────────────────────────────
_SEO_HTML = """
<style>
    section[data-testid="stSidebar"] { overflow-x: hidden; }
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
    .stExpander summary { font-size: .85rem; font-weight: 600; }
    .stButton > button, .stDownloadButton > button { border-radius: 6px; }
    .stRadio [role="radiogroup"] label { font-size: .83rem; }
</style>
<meta name="description"
      content="Free weekly schedule planner with PDF export. No account needed. \
Kostenloser Wochenplaner mit PDF-Export – ohne Anmeldung.">
<meta name="keywords"
      content="weekly planner, schedule builder, Wochenplaner, Stundenplan, \
PDF export, free, kostenlos, open source">
<meta property="og:title" content="Free Weekly Planner | Wochenplaner">
<meta property="og:description"
      content="Plan your week visually with proportional time blocks. \
Free PDF &amp; CSV export – no account, no tracking.">
<meta property="og:type" content="website">
"""


# ── Haupt-UI ─────────────────────────────────────────────────────────────────
def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    st.set_page_config(
        page_title="Free Weekly Planner | Wochenplaner",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.html(_SEO_HTML)

    _defaults: list[tuple] = [
        ("activities", None),
        ("edit_mode", None),
        ("plan_title", "Mein Wochenplan"),
        ("pdf_bytes", None),
        ("custom_activities", None),
        ("lang", "de"),
    ]
    for k, v in _defaults:
        if k not in st.session_state:
            if k == "activities":
                st.session_state[k] = load_activities()
            elif k == "custom_activities":
                st.session_state[k] = []
            else:
                st.session_state[k] = v

    # ── Handle shared plan from URL ──────────────────────────────────────────
    qp = st.query_params
    if "plan" in qp and "plan_loaded" not in st.session_state:
        shared = decode_plan(qp["plan"])
        if shared:
            st.session_state.activities = shared
            save_activities(shared)
            st.session_state.plan_loaded = True
            st.query_params.clear()
            st.toast(t("plan_loaded_from_link", st.session_state.lang))
            st.rerun()

    # ── Load example as fallback ─────────────────────────────────────────────
    if not st.session_state.activities and "tried_example" not in st.session_state:
        beispiel = DATA_DIR / "beispiel.json"
        if beispiel.exists():
            st.session_state.activities = load_activities(beispiel)
        st.session_state.tried_example = True

    lang: Lang = st.session_state.lang
    acts: list[Activity] = st.session_state.activities

    with st.sidebar:
        # ── Language selector ────────────────────────────────────────────────
        lang_options = list(LANG_FLAGS.keys())
        _li = lang_options.index(lang) if lang in lang_options else 0
        new_lang = st.selectbox(
            t("language", lang),
            lang_options,
            index=_li,
            format_func=lambda k: LANG_FLAGS[k],
            key="lang_sel",
        )
        if new_lang != lang:
            st.session_state.lang = new_lang
            st.rerun()
        lang = st.session_state.lang

        st.title(t("app_title", lang))
        st.caption(t("app_caption", lang))

        day_names = WOCHENTAGE_I18N[lang]
        day_from_display = DAY_FROM_DISPLAY[lang]
        day_display_map = DAY_DISPLAY[lang]

        ea = st.session_state.edit_mode
        _lbl = t("edit_activity", lang) if ea else t("add_activity", lang)
        with st.expander(_lbl, expanded=True):
            all_names = list(AKTIVITAETEN_FARBEN) + [
                n
                for n in st.session_state.custom_activities
                if n not in AKTIVITAETEN_FARBEN
            ]

            use_custom = st.checkbox(t("custom_activity", lang), key="chk_custom")
            if use_custom:
                name = st.text_input(t("activity_name", lang), key="custom_name")
                if name and name not in st.session_state.custom_activities:
                    st.session_state.custom_activities.append(name)
            else:
                _def_name = ea["name"] if ea else all_names[0]
                name = st.selectbox(
                    t("activity", lang),
                    all_names,
                    index=all_names.index(_def_name) if _def_name in all_names else 0,
                )

            _color_default = (
                ea["color"] if ea else AKTIVITAETEN_FARBEN.get(name, "#F3E5AB")
            )
            color = st.color_picker(
                t("color", lang), _color_default, key=f"color_{name}_{id(ea)}"
            )

            _def_tag_de = ea["day"] if ea else WOCHENTAGE[0]
            _def_tag_display = day_display_map.get(_def_tag_de, day_names[0])
            tag_display = st.selectbox(
                t("day", lang),
                day_names,
                index=(
                    day_names.index(_def_tag_display)
                    if _def_tag_display in day_names
                    else 0
                ),
            )
            tag_de = day_from_display.get(tag_display, WOCHENTAGE[0])

            _def_von = ea["start"] if ea else DEFAULT_VON
            _c1, _c2 = st.columns(2)
            with _c1:
                _von_idx = (
                    TIME_OPTIONS.index(_def_von)
                    if _def_von in TIME_OPTIONS
                    else TIME_OPTIONS.index(DEFAULT_VON)
                )
                von = st.selectbox(t("from_time", lang), TIME_OPTIONS, index=_von_idx)
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
                bis = st.selectbox(t("to_time", lang), bo, index=_bis_idx)

            def _do_save() -> None:
                if ea:
                    ea.update(
                        name=name,
                        day=tag_de,
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
                            day=tag_de,
                            start=von,
                            end=bis,
                            color=color,
                        )
                    )
                save_activities(acts)
                st.rerun()

            if not name:
                st.warning(t("enter_name", lang))
            elif t2m(bis) <= t2m(von):
                st.error(t("end_after_start", lang))
            else:
                _conflicts = check_overlap(
                    acts, tag_de, von, bis, ea["id"] if ea else None
                )
                if _conflicts:
                    _cn = ", ".join(c["name"] for c in _conflicts)
                    st.warning(f"{t('overlap_with', lang)} **{_cn}**")
                    if st.button(
                        t("save_anyway", lang),
                        width="stretch",
                        key="btn_force",
                    ):
                        _do_save()
                    if st.button(
                        t("cancel", lang),
                        width="stretch",
                        key="btn_ovlp_cancel",
                    ):
                        st.session_state.edit_mode = None
                        st.rerun()
                else:
                    _slbl = t("save", lang) if ea else t("add", lang)
                    if st.button(
                        _slbl,
                        width="stretch",
                        type="primary",
                        key="btn_save",
                    ):
                        _do_save()

            if ea:
                if st.button(
                    t("cancel", lang),
                    width="stretch",
                    key="btn_cancel_edit",
                ):
                    st.session_state.edit_mode = None
                    st.rerun()

        # ── Einträge (sortiert nach Tag + Uhrzeit) ──────────────────────────
        if acts:
            with st.expander(f"{t('entries', lang)} ({len(acts)})", expanded=False):
                for _act in _sort_activities(acts):
                    _ns = html_lib.escape(_act["name"])
                    _ac = validate_color(_act["color"])
                    _tc = get_text_color(_ac)
                    _day_short = DAY_DISPLAY[lang].get(_act["day"], _act["day"])[:2]
                    st.markdown(
                        f"<div style='background:{_ac};color:{_tc};"
                        "padding:4px 10px;border-radius:4px;font-size:12px;"
                        "margin-bottom:2px;overflow-wrap:anywhere;"
                        "word-break:break-word'>"
                        f"<b>{_ns}</b>&nbsp;&middot;&nbsp;"
                        f"{html_lib.escape(_day_short)}&nbsp;"
                        f"{html_lib.escape(_act['start'])}"
                        f"\u2013{html_lib.escape(_act['end'])}"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    _eb, _db = st.columns(2)
                    with _eb:
                        if st.button(
                            t("edit_activity", lang),
                            key=f"e_{_act['id']}",
                            width="stretch",
                        ):
                            st.session_state.edit_mode = _act
                            st.rerun()
                    with _db:
                        if st.button(
                            t("delete", lang),
                            key=f"d_{_act['id']}",
                            width="stretch",
                        ):
                            acts.remove(_act)
                            save_activities(acts)
                            st.rerun()
                    st.divider()
                _confirm = st.checkbox(t("confirm_delete_all", lang), key="chk_del_all")
                if st.button(
                    t("delete_all", lang),
                    width="stretch",
                    key="btn_del_all",
                    disabled=not _confirm,
                ):
                    st.session_state.activities = []
                    save_activities([])
                    st.rerun()

        # ── Vorlagen / Templates ───────────────────────────────────────────────
        with st.expander(t("templates", lang), expanded=False):
            tpl_names = get_template_names(lang)
            if tpl_names:
                sel_tpl = st.selectbox(
                    t("templates", lang),
                    list(tpl_names.keys()),
                    format_func=lambda k: tpl_names[k],
                    key="tpl_sel",
                    label_visibility="collapsed",
                )
                if st.button(
                    t("load_template", lang),
                    width="stretch",
                    key="btn_tpl",
                ):
                    tpl_acts = get_template_activities(sel_tpl)
                    if tpl_acts:
                        st.session_state.activities = tpl_acts
                        save_activities(tpl_acts)
                        st.toast(f"{t('template_loaded', lang)} {tpl_names[sel_tpl]}")
                        st.rerun()

        # ── PDF erzeugen ─────────────────────────────────────────────────────────
        with st.expander(t("generate_pdf", lang), expanded=False):
            st.session_state.plan_title = st.text_input(
                t("plan_title", lang), st.session_state.plan_title, key="pti"
            )
            fmt = st.radio(t("format", lang), ["DIN A4", "DIN A5"], horizontal=True)
            with st.expander(t("time_range", lang), expanded=False):
                sh_s = st.slider(t("start_hour", lang), 0, 23, START_HOUR)
                eh_s = st.slider(t("end_hour", lang), 1, 24, END_HOUR)
            if st.button(
                t("generate_pdf", lang),
                width="stretch",
                type="primary",
                key="btn_pdf",
            ):
                if not acts:
                    st.warning(t("no_activities", lang))
                elif sh_s >= eh_s:
                    st.error(t("start_lt_end", lang))
                else:
                    with st.spinner(t("generating_pdf", lang)):
                        st.session_state.pdf_bytes = generate_pdf(
                            acts,
                            paper_format=fmt.replace("DIN ", ""),
                            start_hour=sh_s,
                            end_hour=eh_s,
                            title=st.session_state.plan_title,
                            lang=lang,
                        )
            if st.session_state.pdf_bytes is not None:
                _slug = slugify(st.session_state.plan_title)
                _pdf_name = f"{_slug}.pdf"
                st.download_button(
                    t("download_pdf", lang),
                    data=st.session_state.pdf_bytes,
                    file_name=_pdf_name,
                    mime="application/pdf",
                    width="stretch",
                    key="btn_pdf_dl",
                )

        # ── Teilen / Share ───────────────────────────────────────────────────
        if acts:
            with st.expander(t("share", lang), expanded=False):
                encoded = encode_plan(acts)
                if encoded:
                    share_url = f"?plan={encoded}"
                    st.code(share_url, language=None)
                    st.caption(t("copy_link", lang) + " — " + t("share_help", lang))
                else:
                    st.warning(t("share_too_large", lang))

        # ── Dateiverwaltung ──────────────────────────────────────────────────
        with st.expander(t("file_mgmt", lang), expanded=False):
            jf = list_json_files()
            if jf:
                sel = st.selectbox(
                    t("load_plan", lang), [p.stem for p in jf], key="imp"
                )
                if st.button(t("load", lang), width="stretch", key="btn_load"):
                    try:
                        st.session_state.activities = load_activities(
                            DATA_DIR / f"{sel}.json"
                        )
                        st.toast(f"{t('loaded', lang)} {sel}")
                    except (json.JSONDecodeError, KeyError) as exc:
                        st.error(f"{t('load_error', lang)} {exc}")
                    else:
                        st.rerun()
            else:
                st.caption(t("no_plans", lang))

            st.divider()

            en = st.text_input(
                t("filename", lang),
                datetime.now().strftime("%Y-%m-%d_wochenplan"),
                key="en",
            )
            if st.button(
                t("save_as", lang),
                width="stretch",
                key="btn_saveas",
            ):
                safe_name = safe_filename(en.strip() or "wochenplan")
                save_activities(acts, DATA_DIR / f"{safe_name}.json")
                st.toast(f"{t('saved', lang)} {safe_name}.json")

            st.divider()

            # JSON-Upload
            uploaded = st.file_uploader(
                t("import_json", lang),
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
                            st.toast(f"{len(valid)} {t('activities_imported', lang)}")
                            st.rerun()
                        else:
                            st.error(t("no_valid_acts", lang))
                    else:
                        st.error(t("json_must_list", lang))
                except json.JSONDecodeError:
                    st.error(t("invalid_json", lang))

            # CSV-Export
            if acts:
                st.divider()
                st.download_button(
                    t("export_csv", lang),
                    data=_export_csv(acts, lang),
                    file_name=(f"{datetime.now().strftime('%Y-%m-%d')}_wochenplan.csv"),
                    mime="text/csv",
                    width="stretch",
                    key="btn_csv",
                )

    # ── Hauptbereich: Tabs ───────────────────────────────────────────────────
    tab1, tab2 = st.tabs([t("tab_calendar", lang), t("tab_statistics", lang)])

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
                lang=lang,
            ),
            height=int((END_HOUR - START_HOUR) * 60 * PX_PER_MIN) + 60,
            scrolling=False,
        )
        if not acts:
            st.caption(t("add_first", lang))

    with tab2:
        st.markdown(f"## {t('time_dist', lang)}")
        render_statistics(acts, lang)


if __name__ == "__main__":
    main()
