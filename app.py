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

import plotly.graph_objects as go
import streamlit as st

from calendar_component import calendar_component
from calendar_render import render_calendar
from constants import (
    AKTIVITAETEN_FARBEN,
    DATA_DIR,
    DATA_FILE,
    DEFAULT_VON,
    END_HOUR,
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
from storage import ls_delete, ls_load, ls_save
from templates import get_template_activities, get_template_names
from utils import (
    Activity,
    check_overlap,
    get_text_color,
    shift_day,
    shift_time,
    slugify,
    t2m,
    validate_activity,
    validate_color,
)

# ── Sharing helpers ──────────────────────────────────────────────────────────
_MAX_SHARE_BYTES = 1800  # URL-safe limit

# ── Form widget keys (stable across reruns) ──────────────────────────────────
_FORM_KEYS = (
    "sel_activity",
    "sel_day",
    "sel_from",
    "sel_to",
    "sel_color",
    "inp_note",
    "chk_custom",
    "custom_name",
    "_form_prev_name",
    "_prev_from",
)


def _normalize_activity_name(name: str) -> str:
    """Normalize user input for stable storage and matching."""
    return " ".join(name.split()).strip()


def _base_color_map() -> dict[str, str]:
    """Default color mapping from built-in activity presets."""
    return {k: validate_color(v) for k, v in AKTIVITAETEN_FARBEN.items()}


def _save_user_prefs() -> None:
    """Persist user-specific preferences (custom names + color map)."""
    _ls_counter = st.session_state.get("_ls_wc", 0) + 1
    st.session_state._ls_wc = _ls_counter
    ls_save(
        "custom_activities",
        json.dumps(st.session_state.custom_activities, ensure_ascii=False),
        f"custom_{_ls_counter}",
    )

    _ls_counter += 1
    st.session_state._ls_wc = _ls_counter
    ls_save(
        "activity_colors",
        json.dumps(st.session_state.activity_colors, ensure_ascii=False),
        f"colors_{_ls_counter}",
    )


def _sync_prefs_from_activities(acts: list[Activity]) -> None:
    """Learn custom names and colors from existing activities."""
    changed = False
    defaults = set(AKTIVITAETEN_FARBEN)
    for act in acts:
        nm = _normalize_activity_name(act.get("name", ""))
        if not nm:
            continue
        if nm not in defaults and nm not in st.session_state.custom_activities:
            st.session_state.custom_activities.append(nm)
            changed = True
        c = validate_color(act.get("color", "#F3E5AB"))
        if st.session_state.activity_colors.get(nm) != c:
            st.session_state.activity_colors[nm] = c
            changed = True
    if changed:
        _save_user_prefs()


def _reset_form_keys() -> None:
    """Clear form widget state so next render starts fresh."""
    for k in _FORM_KEYS:
        st.session_state.pop(k, None)


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
    if fp == DATA_FILE or fp is None:
        _ls_counter = st.session_state.get("_ls_wc", 0) + 1
        st.session_state._ls_wc = _ls_counter
        ls_save("activities", json.dumps(a, ensure_ascii=False), f"save_{_ls_counter}")


def _sort_activities(acts: list[Activity]) -> list[Activity]:
    day_order = {d: i for i, d in enumerate(WOCHENTAGE)}
    return sorted(acts, key=lambda a: (day_order.get(a["day"], 99), a["start"]))


def _export_csv(acts: list[Activity], lang: Lang = "de") -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    header = (
        ["Name", "Tag", "Von", "Bis", "Farbe", "Notiz"]
        if lang == "de"
        else ["Name", "Day", "From", "To", "Color", "Note"]
    )
    writer.writerow(header)
    for a in _sort_activities(acts):
        day_display = DAY_DISPLAY[lang].get(a["day"], a["day"])
        writer.writerow(
            [a["name"], day_display, a["start"], a["end"], a["color"],
             a.get("note", "")]
        )
    return buf.getvalue()


# ── Statistik ────────────────────────────────────────────────────────────────
@st.fragment
def _statistics_fragment(activities: list[Activity], lang: Lang = "de") -> None:
    st.markdown(f"## {t('time_dist', lang)}")

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
<meta name="application-name" content="Wochenplaner">
<meta name="author" content="Wochenplaner Contributors">
<meta name="description"
      content="Kostenloser Online-Wochenplaner mit PDF-Export – ohne Anmeldung, ohne Tracking. \
Free weekly schedule planner &amp; timetable builder with PDF export. No account needed.">
<meta name="keywords"
      content="Wochenplaner, Stundenplan, Wochenplan erstellen, Zeitplan, Wochenplan online,
      Stundenplan kostenlos, Wochenplaner kostenlos, Wochenplan PDF, Aktivitätenplaner,
      weekly planner, schedule builder, timetable, week planner online, free schedule,
      PDF export, open source planner, Streamlit, tryschedule alternative">
<meta property="og:title" content="Free Weekly Planner | Wochenplaner – kostenlos &amp; ohne Anmeldung">
<meta property="og:description"
      content="Plane deine Woche visuell mit proportionalen Zeitblöcken. \
PDF- &amp; CSV-Export kostenlos – kein Account, kein Tracking. \
Free weekly schedule planner with PDF export – no account, no ads.">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Free Weekly Planner | Wochenplaner">
<meta name="twitter:description"
      content="Kostenloser Wochenplaner mit PDF-Export – kein Account, kein Tracking. \
Free weekly schedule planner with PDF export.">
<meta name="robots" content="index, follow">
"""


# ── Callbacks for entry actions ──────────────────────────────────────────────
def _move_activity(act_id: str, field: str, value: object) -> None:
    """on_click callback – shift day or time of an activity."""
    for a in st.session_state.activities:
        if a["id"] == act_id:
            if field == "day":
                a["day"] = value
            else:
                a["start"], a["end"] = value  # type: ignore[assignment]
            break
    save_activities(st.session_state.activities)


def _delete_activity(act_id: str) -> None:
    """on_click callback – remove an activity by ID."""
    st.session_state.activities = [
        a for a in st.session_state.activities if a["id"] != act_id
    ]
    save_activities(st.session_state.activities)


def _edit_activity(act_id: str) -> None:
    """on_click callback – enter edit mode and pre-populate form widgets."""
    for a in st.session_state.activities:
        if a["id"] == act_id:
            st.session_state.edit_mode = a
            lang: Lang = st.session_state.lang
            nm = a["name"]
            all_preset = set(AKTIVITAETEN_FARBEN) | set(
                st.session_state.get("custom_activities", [])
            )
            st.session_state.custom_name = nm
            if nm in all_preset:
                st.session_state.chk_custom = False
                st.session_state.sel_activity = nm
            else:
                st.session_state.chk_custom = True
            st.session_state.sel_day = DAY_DISPLAY[lang].get(a["day"], a["day"])
            st.session_state.sel_from = a["start"]
            st.session_state.sel_to = a["end"]
            st.session_state.sel_color = a["color"]
            st.session_state.inp_note = a.get("note", "")
            st.session_state._form_prev_name = nm
            break


def _delete_all_activities() -> None:
    """on_click callback – delete all activities."""
    st.session_state.activities = []
    st.session_state.edit_mode = None
    save_activities([])
    _reset_form_keys()


def _duplicate_activity(act_id: str) -> None:
    """on_click callback – duplicate an activity."""
    for a in st.session_state.activities:
        if a["id"] == act_id:
            dup = Activity(
                id=str(uuid.uuid4()),
                name=a["name"],
                day=a["day"],
                start=a["start"],
                end=a["end"],
                color=a["color"],
                note=a.get("note", ""),
            )
            st.session_state.activities.append(dup)
            st.session_state.activity_colors[a["name"]] = validate_color(a["color"])
            save_activities(st.session_state.activities)
            _save_user_prefs()
            break


def _new_plan() -> None:
    """on_click callback – start a fresh empty plan."""
    st.session_state.activities = []
    st.session_state.edit_mode = None
    st.session_state.plan_note = ""
    _kw = datetime.now().isocalendar()[1]
    st.session_state.plan_title = f"Mein Wochenplan – KW {_kw}"
    save_activities([])
    _reset_form_keys()
    _ls_counter = st.session_state.get("_ls_wc", 0) + 1
    st.session_state._ls_wc = _ls_counter
    ls_delete("title", f"del_title_{_ls_counter}")
    _ls_counter += 1
    st.session_state._ls_wc = _ls_counter
    ls_delete("plan_note", f"del_pnote_{_ls_counter}")


# ── Activity form fragment ───────────────────────────────────────────────────
@st.fragment
def _activity_form() -> None:
    """Isolated fragment for the add/edit activity form.

    Widget interactions here only trigger a fragment rerun, keeping the
    calendar and the rest of the page stable.
    """
    ea = st.session_state.edit_mode
    lang: Lang = st.session_state.lang
    acts: list[Activity] = st.session_state.activities

    all_names = list(AKTIVITAETEN_FARBEN) + [
        n
        for n in st.session_state.custom_activities
        if n not in AKTIVITAETEN_FARBEN
    ]
    day_names = WOCHENTAGE_I18N[lang]
    day_from_display = DAY_FROM_DISPLAY[lang]

    # ── Defaults for a fresh form ────────────────────────────────────────
    if "sel_from" not in st.session_state:
        st.session_state.sel_from = DEFAULT_VON
    if "sel_color" not in st.session_state:
        st.session_state.sel_color = "#F3E5AB"
    if "sel_day" not in st.session_state:
        st.session_state.sel_day = day_names[0]

    _lbl = t("edit_activity", lang) if ea else t("add_activity", lang)
    with st.expander(_lbl, expanded=True):
        use_custom = st.checkbox(t("custom_activity", lang), key="chk_custom")
        if use_custom:
            name = _normalize_activity_name(
                st.text_input(t("activity_name", lang), key="custom_name")
            )
        else:
            name = st.selectbox(
                t("activity", lang), all_names, key="sel_activity"
            )

        # Auto-update color only when a *preset* activity is selected in add mode.
        # Custom names (typed char-by-char) and edit mode never auto-change the color.
        _prev_name = st.session_state.get("_form_prev_name")
        if name and name != _prev_name:
            st.session_state._form_prev_name = name
            if not ea and not use_custom:
                mapped = st.session_state.activity_colors.get(
                    name, AKTIVITAETEN_FARBEN.get(name, "#F3E5AB")
                )
                st.session_state.sel_color = mapped

        color = st.color_picker(t("color", lang), key="sel_color")

        tag_display = st.selectbox(t("day", lang), day_names, key="sel_day")
        tag_de = day_from_display.get(tag_display, WOCHENTAGE[0])

        _c1, _c2 = st.columns(2)
        with _c1:
            von = st.selectbox(t("from_time", lang), TIME_OPTIONS, key="sel_from")
        with _c2:
            bo = (
                TIME_OPTIONS[TIME_OPTIONS.index(von) + 1 :]
                if von in TIME_OPTIONS
                else TIME_OPTIONS
            )
            if "sel_to" in st.session_state and st.session_state.sel_to not in bo:
                _old_from = st.session_state.get("_prev_from")
                _old_to = st.session_state.sel_to
                if _old_from and _old_to:
                    _dur = t2m(_old_to) - t2m(_old_from)
                    _new_to_m = t2m(von) + _dur
                    _new_to = f"{_new_to_m // 60:02d}:{_new_to_m % 60:02d}"
                    if _dur > 0 and _new_to in bo:
                        st.session_state.sel_to = _new_to
                    else:
                        del st.session_state["sel_to"]
                else:
                    del st.session_state["sel_to"]
            st.session_state._prev_from = von
            bis = st.selectbox(t("to_time", lang), bo, key="sel_to")

        note = st.text_area(
            t("note", lang), height=68, key="inp_note",
            placeholder=t("note_placeholder", lang),
        )

        def _do_save() -> None:
            if not name:
                return
            st.session_state.activity_colors[name] = validate_color(color)
            if (
                name not in AKTIVITAETEN_FARBEN
                and name not in st.session_state.custom_activities
            ):
                st.session_state.custom_activities.append(name)
            if ea:
                for i, a in enumerate(acts):
                    if a["id"] == ea["id"]:
                        acts[i] = Activity(
                            id=ea["id"],
                            name=name,
                            day=tag_de,
                            start=von,
                            end=bis,
                            color=color,
                            note=note,
                        )
                        break
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
                        note=note,
                    )
                )
            save_activities(acts)
            _save_user_prefs()
            _reset_form_keys()
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
                    _reset_form_keys()
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
                _reset_form_keys()
                st.rerun()


# ── Entries list ─────────────────────────────────────────────────────────────
def _entries_fragment() -> None:
    """Sorted activity list with action buttons."""
    acts: list[Activity] = st.session_state.activities
    lang: Lang = st.session_state.lang

    if not acts:
        return

    with st.expander(f"{t('entries', lang)} ({len(acts)})", expanded=False):
        for _act in _sort_activities(acts):
            _ns = html_lib.escape(_act["name"])
            _ac = validate_color(_act["color"])
            _tc = get_text_color(_ac)
            _day_short = DAY_DISPLAY[lang].get(_act["day"], _act["day"])[:2]
            _aid = _act["id"]
            _note_preview = ""
            _raw_note = _act.get("note", "")
            if _raw_note:
                _short = _raw_note[:40] + ("…" if len(_raw_note) > 40 else "")
                _note_preview = (
                    f"<div style='font-size:10px;color:#888;margin-top:-1px;"
                    f"margin-bottom:3px;padding:0 10px;overflow:hidden;"
                    f"white-space:nowrap;text-overflow:ellipsis'>"
                    f"{html_lib.escape(_short)}</div>"
                )
            st.markdown(
                f"<div style='background:{_ac};color:{_tc};"
                "padding:4px 10px;border-radius:4px;font-size:12px;"
                "margin-bottom:2px;overflow-wrap:anywhere;"
                "word-break:break-word'>"
                f"<b>{_ns}</b>&nbsp;&middot;&nbsp;"
                f"{html_lib.escape(_day_short)}&nbsp;"
                f"{html_lib.escape(_act['start'])}"
                f"\u2013{html_lib.escape(_act['end'])}"
                "</div>"
                + _note_preview,
                unsafe_allow_html=True,
            )
            # ── Quick-move arrows ◀ ▲ ▼ ▶ ────────────────────────
            _new_left = shift_day(_act["day"], -1)
            _new_right = shift_day(_act["day"], 1)
            _new_up = shift_time(_act["start"], _act["end"], -15)
            _new_down = shift_time(_act["start"], _act["end"], 15)
            _mc = st.columns(4)
            with _mc[0]:
                st.button(
                    "◀",
                    key=f"ml_{_aid}",
                    disabled=_new_left is None,
                    on_click=_move_activity,
                    args=(_aid, "day", _new_left),
                )
            with _mc[1]:
                st.button(
                    "▲",
                    key=f"mu_{_aid}",
                    disabled=_new_up is None,
                    on_click=_move_activity,
                    args=(_aid, "time", _new_up),
                )
            with _mc[2]:
                st.button(
                    "▼",
                    key=f"md_{_aid}",
                    disabled=_new_down is None,
                    on_click=_move_activity,
                    args=(_aid, "time", _new_down),
                )
            with _mc[3]:
                st.button(
                    "▶",
                    key=f"mr_{_aid}",
                    disabled=_new_right is None,
                    on_click=_move_activity,
                    args=(_aid, "day", _new_right),
                )
            _eb, _dpb, _db = st.columns(3)
            with _eb:
                st.button(
                    t("edit_activity", lang),
                    key=f"e_{_aid}",
                    on_click=_edit_activity,
                    args=(_aid,),
                    width="stretch",
                )
            with _dpb:
                st.button(
                    t("duplicate", lang),
                    key=f"dup_{_aid}",
                    on_click=_duplicate_activity,
                    args=(_aid,),
                    width="stretch",
                )
            with _db:
                st.button(
                    t("delete", lang),
                    key=f"d_{_aid}",
                    on_click=_delete_activity,
                    args=(_aid,),
                    width="stretch",
                )
            st.divider()
        _confirm = st.checkbox(t("confirm_delete_all", lang), key="chk_del_all")
        st.button(
            t("delete_all", lang),
            width="stretch",
            key="btn_del_all",
            disabled=not _confirm,
            on_click=_delete_all_activities,
        )


# ── Haupt-UI ─────────────────────────────────────────────────────────────────
def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    st.set_page_config(
        page_title="Free Weekly Planner | Wochenplaner",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.html(_SEO_HTML)

    _kw = datetime.now().isocalendar()[1]
    _defaults: list[tuple] = [
        ("activities", None),
        ("edit_mode", None),
        ("plan_title", f"Mein Wochenplan – KW {_kw}"),
        ("plan_note", ""),
        ("pdf_bytes", None),
        ("pdf_format", "DIN-A4"),
        ("custom_activities", None),
        ("activity_colors", None),
        ("lang", "de"),
        ("_ls_wc", 0),
    ]
    for k, v in _defaults:
        if k not in st.session_state:
            if k == "activities":
                st.session_state[k] = load_activities()
            elif k == "custom_activities":
                st.session_state[k] = []
            elif k == "activity_colors":
                st.session_state[k] = _base_color_map()
            else:
                st.session_state[k] = v

    # ── Restore from LocalStorage (Cloud fallback) ───────────────────────────
    if not st.session_state.activities and "ls_checked" not in st.session_state:
        ls_data = ls_load("activities", "init_load")
        if ls_data:
            try:
                items = json.loads(ls_data)
                if isinstance(items, list):
                    valid = [item for item in items if validate_activity(item)]
                    if valid:
                        st.session_state.activities = valid
            except (json.JSONDecodeError, TypeError):
                pass
        st.session_state.ls_checked = True

    # ── Restore language from LocalStorage ───────────────────────────────────
    if "ls_lang_checked" not in st.session_state:
        ls_lang = ls_load("lang", "init_lang")
        if ls_lang and ls_lang in ("de", "en"):
            st.session_state.lang = ls_lang
        st.session_state.ls_lang_checked = True

    # ── Restore title from LocalStorage ──────────────────────────────────────
    if "ls_title_checked" not in st.session_state:
        ls_title = ls_load("title", "init_title")
        if ls_title and isinstance(ls_title, str) and ls_title.strip():
            st.session_state.plan_title = ls_title
        st.session_state.ls_title_checked = True

    # ── Restore plan note from LocalStorage ──────────────────────────────────
    if "ls_plan_note_checked" not in st.session_state:
        ls_pn = ls_load("plan_note", "init_plan_note")
        if ls_pn and isinstance(ls_pn, str):
            st.session_state.plan_note = ls_pn
        st.session_state.ls_plan_note_checked = True

    # ── Restore user prefs from LocalStorage ────────────────────────────────
    if "ls_prefs_checked" not in st.session_state:
        ls_custom = ls_load("custom_activities", "init_custom")
        if ls_custom:
            try:
                items = json.loads(ls_custom)
                if isinstance(items, list):
                    seen: set[str] = set()
                    cleaned: list[str] = []
                    for raw in items:
                        if isinstance(raw, str):
                            nm = _normalize_activity_name(raw)
                            if nm and nm not in seen:
                                seen.add(nm)
                                cleaned.append(nm)
                    st.session_state.custom_activities = cleaned
            except (json.JSONDecodeError, TypeError):
                pass

        ls_colors = ls_load("activity_colors", "init_colors")
        if ls_colors:
            try:
                items = json.loads(ls_colors)
                if isinstance(items, dict):
                    merged = _base_color_map()
                    for raw_name, raw_color in items.items():
                        if isinstance(raw_name, str) and isinstance(raw_color, str):
                            nm = _normalize_activity_name(raw_name)
                            if nm:
                                merged[nm] = validate_color(raw_color)
                    st.session_state.activity_colors = merged
            except (json.JSONDecodeError, TypeError):
                pass

        st.session_state.ls_prefs_checked = True

    # ── Pending calendar edit (from previous run; must run before sidebar widgets)
    if "_pending_cal_edit" in st.session_state:
        _pending_id = st.session_state.pop("_pending_cal_edit")
        _edit_activity(_pending_id)

    # ── Click-to-edit from calendar (legacy query param fallback) ────────────
    qp = st.query_params
    if "edit" in qp:
        _click_id = qp["edit"]
        del qp["edit"]
        _edit_activity(_click_id)

    # ── Handle shared plan from URL ──────────────────────────────────────────
    if "plan" in qp and "plan_loaded" not in st.session_state:
        shared = decode_plan(qp["plan"])
        if shared:
            st.session_state.activities = shared
            save_activities(shared)
            st.session_state.plan_loaded = True
            st.query_params.clear()
            st.toast(t("plan_loaded_from_link", st.session_state.lang))
            st.rerun()

    lang: Lang = st.session_state.lang
    acts: list[Activity] = st.session_state.activities
    _sync_prefs_from_activities(acts)

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
            st.session_state._ls_wc += 1
            ls_save("lang", new_lang, f"lang_{st.session_state._ls_wc}")
            _reset_form_keys()
            st.rerun()
        lang = st.session_state.lang

        st.title(t("app_title", lang))
        st.caption(t("app_caption", lang))

        # ── Activity form (fragment – only reruns itself on widget change) ──
        _activity_form()

        # ── Entries list ─────────────────────────────────────────────────────
        _entries_fragment()

        # ── Vorlagen / Templates ─────────────────────────────────────────────
        _tpl_open = not acts
        with st.expander(t("templates", lang), expanded=_tpl_open):
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
                        _reset_form_keys()
                        st.toast(f"{t('template_loaded', lang)} {tpl_names[sel_tpl]}")
                        st.rerun()
                if acts:
                    st.caption(f"⚠️ {t('template_overwrite', lang)}")

        # ── Neuer Plan / New Plan ────────────────────────────────────────────
        if acts:
            st.button(
                t("new_plan", lang),
                width="stretch",
                key="btn_new_plan",
                on_click=_new_plan,
            )

        # ── PDF erzeugen ─────────────────────────────────────────────────────
        with st.expander(t("generate_pdf", lang), expanded=False):
            _new_title = st.text_input(
                t("plan_title", lang), st.session_state.plan_title, key="pti"
            )
            if _new_title != st.session_state.plan_title:
                st.session_state.plan_title = _new_title
                _ls_counter = st.session_state.get("_ls_wc", 0) + 1
                st.session_state._ls_wc = _ls_counter
                ls_save("title", _new_title, f"title_{_ls_counter}")

            _new_plan_note = st.text_area(
                t("plan_note", lang),
                st.session_state.plan_note,
                height=80,
                key="inp_plan_note",
                placeholder=t("plan_note_placeholder", lang),
            )
            if _new_plan_note != st.session_state.plan_note:
                st.session_state.plan_note = _new_plan_note
                _ls_counter = st.session_state.get("_ls_wc", 0) + 1
                st.session_state._ls_wc = _ls_counter
                ls_save("plan_note", _new_plan_note, f"pnote_{_ls_counter}")

            fmt = st.radio(
                t("format", lang), ["DIN A4", "DIN A5"],
                horizontal=True, key="pdf_fmt",
            )
            with st.expander(t("time_range", lang), expanded=False):
                sh_s = st.slider(
                    t("start_hour", lang), 0, 23, START_HOUR, key="pdf_sh"
                )
                eh_s = st.slider(
                    t("end_hour", lang), 1, 24, END_HOUR, key="pdf_eh"
                )
            show_axis_times = st.checkbox(
                t("pdf_show_axis_times", lang),
                value=True,
                key="pdf_axis_times",
                help=t("pdf_show_axis_times_help", lang),
            )
            show_block_times = st.checkbox(
                t("pdf_show_block_times", lang),
                value=True,
                key="pdf_block_times",
                help=t("pdf_show_block_times_help", lang),
            )
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
                        st.session_state.pdf_format = fmt.replace(" ", "-")
                        st.session_state.pdf_bytes = generate_pdf(
                            acts,
                            paper_format=fmt.replace("DIN ", ""),
                            start_hour=sh_s,
                            end_hour=eh_s,
                            title=st.session_state.plan_title,
                            lang=lang,
                            plan_note=st.session_state.plan_note,
                            show_axis_times=show_axis_times,
                            show_block_times=show_block_times,
                        )
            if st.session_state.pdf_bytes is not None:
                _slug = slugify(st.session_state.plan_title)
                _fmt_slug = slugify(st.session_state.get("pdf_format", "DIN-A4"))
                _pdf_name = f"{_slug}_{_fmt_slug}.pdf"
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

        # ── Plan speichern / Download JSON ──────────────────────────────────
        if acts:
            _slug = slugify(st.session_state.plan_title)
            _json_name = f"{datetime.now().strftime('%Y-%m-%d')}_{_slug}.json"
            st.download_button(
                t("download_json", lang),
                data=json.dumps(acts, ensure_ascii=False, indent=2),
                file_name=_json_name,
                mime="application/json",
                width="stretch",
                key="btn_json_dl",
            )
            st.caption(t("download_json_hint", lang))

        # ── Dateiverwaltung ──────────────────────────────────────────────────
        with st.expander(t("file_mgmt", lang), expanded=False):
            uploaded = st.file_uploader(
                t("import_json", lang),
                type=["json"],
                key="json_upload",
            )
            if uploaded is not None:
                _fp = f"{uploaded.name}_{uploaded.size}"
                if st.session_state.get("_last_upload_fp") != _fp:
                    st.session_state._last_upload_fp = _fp
                    with st.spinner(t("importing_json", lang)):
                        try:
                            raw = json.loads(uploaded.read().decode("utf-8"))
                            if isinstance(raw, list):
                                valid = [
                                    item for item in raw if validate_activity(item)
                                ]
                                if valid:
                                    st.session_state.activities = valid
                                    _sync_prefs_from_activities(valid)
                                    save_activities(valid)
                                    _reset_form_keys()
                                    st.toast(
                                        f"{len(valid)} {t('activities_imported', lang)}"
                                    )
                                    st.rerun()
                                else:
                                    st.error(t("no_valid_acts", lang))
                            else:
                                st.error(t("json_must_list", lang))
                        except json.JSONDecodeError:
                            st.error(t("invalid_json", lang))

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

        st.markdown(
            "<div style='text-align:center;padding:16px 0 4px;"
            "font-size:11px;color:#aaa;letter-spacing:.02em'>"
            "v1.2 · "
            "<a href='https://github.com/grenzenloseSchublade/wochenplaner'"
            " target='_blank' style='color:#888;text-decoration:none'>"
            "GitHub</a></div>",
            unsafe_allow_html=True,
        )

    # ── Hauptbereich: Tabs ───────────────────────────────────────────────────
    tab1, tab2 = st.tabs([t("tab_calendar", lang), t("tab_statistics", lang)])

    with tab1:
        _th = (
            "<h2 style='text-align:center;margin-bottom:4px;"
            "font-weight:600;letter-spacing:.02em'>"
            + html_lib.escape(st.session_state.plan_title)
            + "</h2>"
        )
        _pn = st.session_state.plan_note.strip()
        if _pn:
            _pn_display = _pn[:100] + ("…" if len(_pn) > 100 else "")
            _th += (
                "<p style='text-align:center;font-size:.82rem;"
                "color:#888;margin-bottom:8px'>"
                + html_lib.escape(_pn_display)
                + "</p>"
            )
        else:
            _th += "<div style='margin-bottom:12px'></div>"
        st.markdown(_th, unsafe_allow_html=True)

        ea = st.session_state.edit_mode
        _editing_id = ea["id"] if ea else ""
        _cal_height = int((END_HOUR - START_HOUR) * 60 * PX_PER_MIN) + 60
        _cal_html = render_calendar(
            json.dumps(acts, ensure_ascii=False),
            START_HOUR,
            END_HOUR,
            _today=datetime.now().strftime("%Y-%m-%d"),
            lang=lang,
            editing_id=_editing_id,
            component_mode=True,
        )
        cal_event = calendar_component(
            calendar_html=_cal_html,
            height=_cal_height,
            key="cal",
        )
        if cal_event and cal_event.get("action") == "edit":
            _ts = cal_event.get("ts")
            if _ts and _ts != st.session_state.get("_cal_event_ts"):
                st.session_state._cal_event_ts = _ts
                st.session_state._pending_cal_edit = cal_event["id"]
                st.rerun()

        if not acts:
            st.caption(t("add_first", lang))

    with tab2:
        _statistics_fragment(acts, lang)


if __name__ == "__main__":
    main()
