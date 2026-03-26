"""
Wochenplaner – lokale Streamlit-App
Start: uv run streamlit run app.py
"""

import html as html_lib
import json
import re as _re_mod
import sys
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import streamlit as st
import streamlit.components.v1 as components

from pdf_export import generate_pdf


class Activity(TypedDict):
    id: str
    name: str
    day: str
    start: str
    end: str
    color: str


WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]
WOCHENTAGE_KURZ = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

AKTIVITAETEN_FARBEN: dict[str, str] = {
    "Arbeit": "#F3E5AB",
    "Laufen": "#FFB6B6",
    "Kraft": "#FFCC99",
    "Sprachkurs": "#B6D7A8",
    "Dehnen": "#A8D8E8",
    "Long Run": "#B8E0C3",
    "Meeting": "#E8C8D8",
    "Freizeit": "#FFEAA7",
    "Schlafen": "#D8D8D8",
    "Kochen": "#F9C784",
}

START_HOUR = 6
END_HOUR = 22
PX_PER_MIN = 1.6
DEFAULT_VON = "09:00"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "wochenplan.json"
PLANS_DIR = DATA_DIR / "plans"

TIME_OPTIONS: list[str] = [
    f"{h:02d}:{m:02d}"
    for h in range(START_HOUR, END_HOUR + 1)
    for m in (0, 30)
    if not (h == END_HOUR and m > 0)
]


# ── Datenzugriff ──────────────────────────────────────────────────────────────
def load_activities(fp: Path | None = None) -> list[Activity]:
    fp = fp or DATA_FILE
    return json.loads(fp.read_text("utf-8")) if fp.exists() else []


def save_activities(a: list[Activity], fp: Path | None = None) -> None:
    fp = fp or DATA_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(a, ensure_ascii=False, indent=2), "utf-8")


def list_json_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []


def t2m(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def get_text_color(bg: str) -> str:
    hx = bg.lstrip("#")
    lum = (
        0.299 * int(hx[0:2], 16) + 0.587 * int(hx[2:4], 16) + 0.114 * int(hx[4:6], 16)
    ) / 255
    return "#333" if lum > 0.5 else "#eee"


def _darken(hex_c: str, factor: float = 0.68) -> str:
    hx = hex_c.lstrip("#")
    return f"#{int(int(hx[0:2], 16) * factor):02x}{int(int(hx[2:4], 16) * factor):02x}{int(int(hx[4:6], 16) * factor):02x}"


def _slugify(text: str) -> str:
    for s, d in [
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("Ä", "Ae"),
        ("Ö", "Oe"),
        ("Ü", "Ue"),
        ("ß", "ss"),
    ]:
        text = text.replace(s, d)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = _re_mod.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "wochenplan"


_HEX_COLOR_RE = _re_mod.compile(r"^#[0-9a-fA-F]{6}$")


def _validate_color(c: str) -> str:
    """Return color if valid hex, else fallback."""
    return c if _HEX_COLOR_RE.match(c) else "#F3E5AB"


def check_overlap(
    acts: list[Activity],
    day: str,
    start: str,
    end: str,
    exclude_id: str | None = None,
) -> list[Activity]:
    ns, ne = t2m(start), t2m(end)
    return [
        a
        for a in acts
        if a["day"] == day
        and (exclude_id is None or a["id"] != exclude_id)
        and t2m(a["start"]) < ne
        and t2m(a["end"]) > ns
    ]


def _open_folder(path: Path) -> None:
    """Öffnet Ordner im Dateimanager. Zeigt Pfad wenn kein Tool verfügbar."""
    import platform as _pl
    import shutil as _shutil
    import subprocess as _sp

    _sys = _pl.system()
    if _sys == "Windows":
        cmd = ["explorer", str(path)]
    elif _sys == "Darwin":
        cmd = ["open", str(path)]
    else:
        cmd = ["xdg-open", str(path)]
    if _shutil.which(cmd[0]) is None:
        st.info(f"Gespeichert unter: {path}")
        return
    try:
        _sp.Popen(cmd)
    except Exception:
        st.info(f"Gespeichert unter: {path}")


# ── Kalender ─────────────────────────────────────────────────────────────────
def _time_labels(sh: int, eh: int, abs_start: int) -> str:
    out = []
    for h in range(sh, eh + 1):
        top = (h * 60 - abs_start) * PX_PER_MIN - 7
        out.append(f'<div class="cal-time" style="top:{top:.1f}px">{h:02d}:00</div>')
    return "".join(out)


def _grid_lines(sh: int, eh: int, abs_start: int) -> str:
    out = []
    for h in range(sh, eh + 1):
        y = (h * 60 - abs_start) * PX_PER_MIN
        out.append(f'<div class="cal-grid-line" style="top:{y:.1f}px"></div>')
        if h < eh:
            out.append(
                f'<div class="cal-grid-half" style="top:{y + 30 * PX_PER_MIN:.1f}px"></div>'
            )
    return "".join(out)


def _activity_block(act: Activity, abs_start: int, eh: int) -> str:
    sm, em = t2m(act["start"]), t2m(act["end"])
    dur = em - sm
    if dur <= 0:
        return ""
    smc, emc = max(sm, abs_start), min(em, eh * 60)
    if smc >= emc:
        return ""
    top = (smc - abs_start) * PX_PER_MIN
    ht = (emc - smc) * PX_PER_MIN
    c = _validate_color(act.get("color", "#F3E5AB"))
    tc = get_text_color(c)
    bc = _darken(c)
    dh, dm = dur // 60, dur % 60
    ds = f"{dh}h {dm}min" if dh and dm else (f"{dh}h" if dh else f"{dm}min")
    n = html_lib.escape(act["name"])
    s = html_lib.escape(act["start"])
    e = html_lib.escape(act["end"])
    body = f'<span class="act-name">{n}</span>'
    if ht > 30:
        body += f'<span class="act-dur">{ds}</span>'
    return (
        f'<div title="{n}: {s}\u2013{e}" class="act-block" '
        f'style="top:{top:.1f}px;height:{ht:.1f}px;background:{c};'
        f'color:{tc};border-left-color:{bc}">' + body + "</div>"
    )


_CALENDAR_TEMPLATE = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
    "*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}"
    ":root{"
    "  --c-bg:#ffffff;--c-we:#f7f8fc;--c-today:#eef4ff;--c-wrap:#f0f2f6;"
    "  --c-grid:#eeeeee;--c-gridh:#f7f7f7;--c-time:#cccccc;--c-bdr:#e8e8e8;"
    "  --c-hdra:#4a6fa5;--c-hdrb:#5c8a8a;--c-hdr-today:#2d5a9e;"
    "  --c-now:rgba(220,50,50,.75);--trans:.25s;}"
    "html.dark{"
    "  --c-bg:#1c1c1e;--c-we:#232326;--c-today:#1e2540;--c-wrap:#111113;"
    "  --c-grid:rgba(255,255,255,.07);--c-gridh:rgba(255,255,255,.03);"
    "  --c-time:#555558;--c-bdr:rgba(255,255,255,.08);"
    "  --c-hdra:#2a3f5f;--c-hdrb:#215050;--c-hdr-today:#1a3a7a;"
    "  --c-now:rgba(255,80,80,.7);}"
    "body,.cal-outer,.cal-day,.cal-day-we,.cal-day-today,"
    ".cal-hdr-wk,.cal-hdr-we,.cal-time{"
    "  transition:background var(--trans),background-color var(--trans),color var(--trans);}"
    "body{font-family:system-ui,'Segoe UI',Arial,sans-serif;background:var(--c-wrap)}"
    ".cal-outer{display:flex;width:100%;background:var(--c-wrap)}"
    ".cal-time-col{width:44px;flex-shrink:0;padding-top:35px}"
    ".cal-time-inner{position:relative}"
    ".cal-time{position:absolute;right:6px;font-size:9px;color:var(--c-time);"
    "  white-space:nowrap;font-variant-numeric:tabular-nums;letter-spacing:.02em}"
    ".cal-grid-line{position:absolute;left:0;right:0;border-top:1px solid var(--c-grid);pointer-events:none}"
    ".cal-grid-half{position:absolute;left:0;right:0;border-top:1px dashed var(--c-gridh);pointer-events:none}"
    ".cal-cols{flex:1;min-width:0;display:flex}"
    ".cal-day-wrap{flex:1;display:flex;flex-direction:column;min-width:0}"
    ".cal-hdr{font-size:11px;font-weight:600;text-align:center;padding:7px 2px;"
    "  color:rgba(255,255,255,.9);letter-spacing:.07em;text-transform:uppercase;"
    "  border-left:1px solid rgba(255,255,255,.1)}"
    ".cal-hdr-wk{background:var(--c-hdra)}.cal-hdr-we{background:var(--c-hdrb)}"
    ".cal-hdr.today{background:var(--c-hdr-today);color:#fff}"
    ".cal-day{position:relative;background:var(--c-bg);border-left:1px solid var(--c-bdr)}"
    ".cal-day-we{position:relative;background:var(--c-we);border-left:1px solid var(--c-bdr)}"
    ".cal-day-today{position:relative;background:var(--c-today);border-left:1px solid var(--c-bdr)}"
    ".act-block{position:absolute;left:2px;right:2px;border-radius:5px;"
    "  border-left:3px solid transparent;"
    "  box-shadow:0 1px 3px rgba(0,0,0,.08);"
    "  display:flex;flex-direction:column;align-items:center;"
    "  justify-content:center;text-align:center;overflow:hidden;padding:3px 4px;cursor:default;"
    "  transition:filter .15s ease,box-shadow .15s ease}"
    ".act-block:hover{filter:brightness(.92);box-shadow:0 2px 6px rgba(0,0,0,.15)}"
    ".act-name{font-weight:700;font-size:11px;line-height:1.2}"
    ".act-dur{font-size:9px;opacity:.72;margin-top:1px;font-variant-numeric:tabular-nums}"
    ".now-line{position:absolute;left:0;right:0;pointer-events:none;z-index:10}"
    ".now-line::before{content:'';position:absolute;left:0;right:0;top:0;border-top:2px solid var(--c-now)}"
    ".now-dot{position:absolute;width:8px;height:8px;border-radius:50%;"
    "  background:var(--c-now);top:-4px;left:-1px}"
    "</style></head><body>"
    "<script>(function(){"
    "  var PX=__PX__,SH=__SH__,EH=__EH__;"
    "  function syncDark(){"
    "    try{"
    "      var app=window.parent.document.querySelector('.stApp');"
    "      if(!app)return;"
    "      var s=window.parent.getComputedStyle(app).getPropertyValue('color-scheme').trim();"
    "      document.documentElement.classList.toggle('dark',s==='dark');"
    "    }catch(e){}"
    "  }"
    "  syncDark();"
    "  try{"
    "    var _a=window.parent.document.querySelector('.stApp');"
    "    if(_a)new MutationObserver(syncDark).observe(_a,{attributes:true});"
    "  }catch(e){}"
    "  setInterval(syncDark,500);"
    "  var now=new Date();"
    "  var todayIdx=(now.getDay()+6)%7;"
    "  var hdrs=document.querySelectorAll('.cal-hdr');"
    "  var days=document.querySelectorAll('.cal-day,.cal-day-we,.cal-day-today');"
    "  if(hdrs[todayIdx])hdrs[todayIdx].classList.add('today');"
    "  if(days[todayIdx])days[todayIdx].className='cal-day-today';"
    "  var nowMin=now.getHours()*60+now.getMinutes();"
    "  if(nowMin>=SH*60&&nowMin<=EH*60&&days[todayIdx]){"
    "    var top=(nowMin-SH*60)*PX;"
    "    var ln=document.createElement('div');"
    "    ln.className='now-line';ln.style.top=top+'px';"
    "    ln.innerHTML='<div class=\"now-dot\"></div>';"
    "    days[todayIdx].appendChild(ln);"
    "    setInterval(function(){"
    "      var n2=new Date();var m2=n2.getHours()*60+n2.getMinutes();"
    "      if(m2>=SH*60&&m2<=EH*60){ln.style.top=(m2-SH*60)*PX+'px'}"
    "    },60000);"
    "  }"
    "})();</script>"
    '<div class="cal-outer">'
    '  <div class="cal-time-col">'
    '    <div class="cal-time-inner" style="height:__TP__px">__LB__</div>'
    "  </div>"
    '  <div class="cal-cols">__DC__</div>'
    "</div></body></html>"
)


@st.cache_data(show_spinner=False)
def render_calendar(
    activities_json: str,
    sh: int = START_HOUR,
    eh: int = END_HOUR,
    _today: str = "",
) -> str:
    acts = json.loads(activities_json)
    total_px = int((eh - sh) * 60 * PX_PER_MIN)
    abs_start = sh * 60
    labels = _time_labels(sh, eh, abs_start)
    grid = _grid_lines(sh, eh, abs_start)
    day_cols = ""
    for di, (tag, tk) in enumerate(zip(WOCHENTAGE, WOCHENTAGE_KURZ, strict=True)):
        day_acts = [a for a in acts if a.get("day") == tag]
        blocks = "".join(_activity_block(a, abs_start, eh) for a in day_acts)
        hdr_cls = "cal-hdr-we" if di >= 5 else "cal-hdr-wk"
        day_cls = "cal-day-we" if di >= 5 else "cal-day"
        day_cols += (
            f'<div class="cal-day-wrap">'
            f'<div class="cal-hdr {hdr_cls}">{tk}</div>'
            f'<div class="{day_cls}" style="height:{total_px}px">'
            + grid
            + blocks
            + "</div></div>"
        )
    return (
        _CALENDAR_TEMPLATE.replace("__PX__", str(PX_PER_MIN))
        .replace("__SH__", str(sh))
        .replace("__EH__", str(eh))
        .replace("__TP__", str(total_px))
        .replace("__LB__", labels)
        .replace("__DC__", day_cols)
    )


def render_statistics(activities: list[Activity]) -> None:
    import plotly.graph_objects as go

    if not activities:
        st.info("Keine Aktivitäten für Statistik vorhanden.")
        return
    time_per: dict[str, int] = {}
    for act in activities:
        dur = t2m(act["end"]) - t2m(act["start"])
        if dur > 0:
            time_per[act["name"]] = time_per.get(act["name"], 0) + dur
    if not time_per:
        st.info("Keine gültigen Zeitblöcke.")
        return
    names = list(time_per)
    hours = [v / 60 for v in time_per.values()]
    colors = [AKTIVITAETEN_FARBEN.get(n, "#4a6fa5") for n in names]
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


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    st.set_page_config(
        page_title="Wochenplaner",
        page_icon=":stopwatch:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
<style>
    section[data-testid="stSidebar"] {
        overflow-x: hidden;
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
    .stExpander summary { font-size: .85rem; font-weight: 600; }
    .stButton > button, .stDownloadButton > button { border-radius: 6px; }
    .stRadio [role="radiogroup"] label { font-size: .83rem; }
</style>
""",
        unsafe_allow_html=True,
    )

    _defaults: list[tuple] = [
        ("activities", None),
        ("edit_mode", None),
        ("plan_title", "Mein Wochenplan"),
        ("pdf_bytes", None),
    ]
    for k, v in _defaults:
        if k not in st.session_state:
            st.session_state[k] = load_activities() if k == "activities" else v
    acts: list[Activity] = st.session_state.activities

    with st.sidebar:
        st.title("Wochenplaner")
        st.caption("Lokale App  ·  Daten automatisch gespeichert")

        ea = st.session_state.edit_mode
        _lbl = "Bearbeiten" if ea else "Aktivität hinzufügen"
        with st.expander(_lbl, expanded=True):
            nm = list(AKTIVITAETEN_FARBEN)

            _def_name = ea["name"] if ea else nm[0]
            _def_tag = ea["day"] if ea else WOCHENTAGE[0]
            _def_von = ea["start"] if ea else DEFAULT_VON
            _def_bis = ea["end"] if ea else None

            name = st.selectbox(
                "Aktivität",
                nm,
                index=nm.index(_def_name) if _def_name in nm else 0,
            )
            _color_default = (
                ea["color"] if ea else AKTIVITAETEN_FARBEN.get(name, "#F3E5AB")
            )
            color = st.color_picker(
                "Farbe", _color_default, key=f"color_{name}_{id(ea)}"
            )
            tag = st.selectbox(
                "Tag",
                WOCHENTAGE,
                index=WOCHENTAGE.index(_def_tag) if _def_tag in WOCHENTAGE else 0,
            )
            _c1, _c2 = st.columns(2)
            with _c1:
                _von_idx = (
                    TIME_OPTIONS.index(_def_von)
                    if _def_von in TIME_OPTIONS
                    else TIME_OPTIONS.index(DEFAULT_VON)
                )
                von = st.selectbox("Von", TIME_OPTIONS, index=_von_idx)
            with _c2:
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

            if t2m(bis) <= t2m(von):
                st.error("Endzeit muss nach Startzeit liegen.")
            else:
                _conflicts = check_overlap(
                    acts, tag, von, bis, ea["id"] if ea else None
                )
                if _conflicts:
                    _cn = ", ".join(c["name"] for c in _conflicts)
                    st.warning(f"Zeitüberschneidung mit: **{_cn}**")
                    if st.button(
                        "Trotzdem speichern", width="stretch", key="btn_force"
                    ):
                        _do_save()
                    if st.button("Abbrechen", width="stretch", key="btn_ovlp_cancel"):
                        st.session_state.edit_mode = None
                        st.rerun()
                else:
                    _slbl = "Speichern" if ea else "+ Hinzufügen"
                    if st.button(
                        _slbl, width="stretch", type="primary", key="btn_save"
                    ):
                        _do_save()

            if ea:
                if st.button("Abbrechen", width="stretch", key="btn_cancel_edit"):
                    st.session_state.edit_mode = None
                    st.rerun()

        if acts:
            with st.expander(f"Einträge ({len(acts)})", expanded=False):
                for _act in list(acts):
                    _ns = html_lib.escape(_act["name"])
                    _ac = _validate_color(_act["color"])
                    _tc = get_text_color(_ac)
                    st.markdown(
                        f"<div style='background:{_ac};color:{_tc};"
                        "padding:4px 10px;border-radius:4px;font-size:12px;"
                        "margin-bottom:2px;overflow-wrap:anywhere;word-break:break-word'>"
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
                            "Bearbeiten", key=f"e_{_act['id']}", width="stretch"
                        ):
                            st.session_state.edit_mode = _act
                            st.rerun()
                    with _db:
                        if st.button("Löschen", key=f"d_{_act['id']}", width="stretch"):
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

        with st.expander("PDF erzeugen", expanded=False):
            st.session_state.plan_title = st.text_input(
                "Plantitel", st.session_state.plan_title, key="pti"
            )
            fmt = st.radio("Format", ["DIN A4", "DIN A5"], horizontal=True)
            with st.expander("Zeitbereich", expanded=False):
                sh_s = st.slider("Startzeit (Uhr)", 0, 23, START_HOUR)
                eh_s = st.slider("Endzeit   (Uhr)", 1, 24, END_HOUR)
            if st.button(
                "PDF erzeugen", width="stretch", type="primary", key="btn_pdf"
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
                _slug = _slugify(st.session_state.plan_title)
                _pdf_name = f"{_slug}.pdf"
                _pdf_path = PLANS_DIR / _pdf_name
                _pdf_path.write_bytes(st.session_state.pdf_bytes)
                st.success(f"Gespeichert: data/plans/{_pdf_name}")
                st.download_button(
                    "PDF herunterladen",
                    data=st.session_state.pdf_bytes,
                    file_name=_pdf_name,
                    mime="application/pdf",
                    width="stretch",
                    key="btn_pdf_dl",
                )
                if st.button("Ordner öffnen", width="stretch", key="btn_open_folder"):
                    _open_folder(PLANS_DIR)

        with st.expander("Dateiverwaltung", expanded=False):
            jf = list_json_files()
            if jf:
                sel = st.selectbox("Wochenplan laden", [p.stem for p in jf], key="imp")
                if st.button("Laden", width="stretch", key="btn_load"):
                    try:
                        st.session_state.activities = load_activities(
                            DATA_DIR / f"{sel}.json"
                        )
                        st.success(f"Geladen: {sel}")
                    except (json.JSONDecodeError, KeyError) as exc:
                        st.error(f"Fehler beim Laden: {exc}")
                    else:
                        st.rerun()
            else:
                st.caption("Keine gespeicherten Pläne gefunden.")
            st.divider()
            en = st.text_input(
                "Dateiname", datetime.now().strftime("%Y-%m-%d_wochenplan"), key="en"
            )
            if st.button("Speichern unter", width="stretch", key="btn_saveas"):
                save_activities(acts, DATA_DIR / f"{en.strip() or 'wochenplan'}.json")
                st.success(f"Gespeichert: {en}.json")

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
