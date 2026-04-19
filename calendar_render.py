"""Kalender-Rendering für den Wochenplaner (HTML/CSS/JS)."""

import html as html_lib
import json
from pathlib import Path

import streamlit as st

from constants import PX_PER_MIN, WOCHENTAGE
from i18n import WOCHENTAGE_KURZ_I18N, Lang
from utils import (
    Activity,
    darken,
    get_secondary_text_color,
    get_text_color,
    inline_note_fits_block_height,
    t2m,
    validate_color,
)

_STATIC_DIR = Path(__file__).parent / "static"


@st.cache_resource
def _load_css() -> str:
    return (_STATIC_DIR / "calendar.css").read_text("utf-8")


def _calendar_js(px: float, sh: int, eh: int) -> str:
    """Runtime JS for dark-mode sync and current-time indicator."""
    return (
        "(function(){"
        f"  var PX={px},SH={sh},EH={eh};"
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
        "})();"
    )


def _ctx_menu_js(edit_label: str, component_mode: bool = False) -> str:
    """Context-menu JS for activity blocks."""
    if component_mode:
        edit_action = (
            "    var id=el.getAttribute('data-id');"
            "    if(id && window.Streamlit){"
            "      window.Streamlit.setComponentValue({action:'edit',id:id,ts:Date.now()});"
            "    }"
        )
    else:
        edit_action = (
            "    var id=el.getAttribute('data-id');"
            "    if(id){try{"
            "      var url=new URL(window.parent.location.href);"
            "      url.searchParams.set('edit',id);"
            "      window.parent.history.replaceState(null,'',url.toString());"
            "      window.parent.location.reload();"
            "    }catch(ex){}}"
        )
    return (
        "var _menu=null;"
        "function hideCtx(){if(_menu){_menu.remove();_menu=null;}}"
        "document.addEventListener('click',function(e){"
        "  if(_menu&&!_menu.contains(e.target))hideCtx();"
        "});"
        "document.addEventListener('keydown',function(e){"
        "  if(e.key==='Escape')hideCtx();"
        "});"
        "function showCtx(ev,el){"
        "  ev.stopPropagation();hideCtx();"
        "  var m=document.createElement('div');"
        "  m.className='ctx-menu';"
        "  var c=el.getAttribute('data-color')||'#ccc';"
        "  var noteText=el.getAttribute('data-note')||'';"
        "  var noteHtml=noteText?'<div class=\"ctx-note\">'+noteText.replace(/</g,'&lt;')+'</div>':'';"
        "  m.innerHTML='"
        '<div class="ctx-dot" style="background:\'+c+\'"></div>\''
        "+'<div class=\"ctx-name\">'+el.getAttribute('data-name')+'</div>'"
        "+'<div class=\"ctx-time\">'+el.getAttribute('data-day')"
        "+' · '+el.getAttribute('data-start')+'\\u2013'+el.getAttribute('data-end')+'</div>'"
        "+noteHtml"
        '+\'<a class="ctx-edit" href="#">' + edit_label + "</a>';"
        "  var r=el.getBoundingClientRect();"
        "  m.style.left=Math.min(r.left,document.documentElement.clientWidth-170)+'px';"
        "  var t=r.bottom+4;"
        "  if(t+m.offsetHeight>document.documentElement.clientHeight)"
        "    t=Math.max(4,r.top-m.offsetHeight-4);"
        "  m.style.top=t+'px';"
        "  document.body.appendChild(m);"
        "  _menu=m;"
        "  m.querySelector('.ctx-edit').addEventListener('click',function(e2){"
        "    e2.preventDefault();hideCtx();" + edit_action + "  });"
        "}"
    )


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


def _activity_block(
    act: Activity, abs_start: int, eh: int, editing_id: str = ""
) -> str:
    sm, em = t2m(act["start"]), t2m(act["end"])
    dur = em - sm
    if dur <= 0:
        return ""
    smc, emc = max(sm, abs_start), min(em, eh * 60)
    if smc >= emc:
        return ""
    top = (smc - abs_start) * PX_PER_MIN
    ht = (emc - smc) * PX_PER_MIN
    c = validate_color(act.get("color", "#F3E5AB"))
    tc = get_text_color(c)
    bc = darken(c)
    dh, dm = dur // 60, dur % 60
    ds = f"{dh}h {dm}min" if dh and dm else (f"{dh}h" if dh else f"{dm}min")
    n = html_lib.escape(act["name"])
    s = html_lib.escape(act["start"])
    e = html_lib.escape(act["end"])
    note_raw = act.get("note", "") or ""
    note_attr = f' data-note="{html_lib.escape(note_raw)}"' if note_raw else ""
    note_stripped = note_raw.strip()
    show_note_inline = bool(note_stripped) and inline_note_fits_block_height(ht)
    note_icon = (
        '<span class="act-note-icon">&#9998;</span>'
        if (note_stripped and not show_note_inline)
        else ""
    )
    title_attr = html_lib.escape(f"{act['start']}\u2013{act['end']} · {act['name']}")
    parts: list[str] = []
    # Zeit erst ab genug Höhe (sonst nur Titel im Band 22–27 px sichtbar)
    if ht >= 28:
        parts.append(f'<span class="act-time">{s}\u2013{e}</span>')
    if ht >= 22:
        parts.append(f'<span class="act-name">{n}</span>')
    if show_note_inline:
        _sn = html_lib.escape(note_stripped)
        _sec = get_secondary_text_color(c, tc)
        parts.append(f'<span class="act-note-inline" style="color:{_sec}">{_sn}</span>')
    if ht >= 38:
        parts.append(f'<span class="act-dur">{ds}</span>')
    body = "".join(parts)
    aid = html_lib.escape(act.get("id", ""))
    day = html_lib.escape(act.get("day", ""))
    _is_editing = 'data-editing="true" ' if aid == editing_id and editing_id else ""
    return (
        f'<div class="act-block" '
        f"{_is_editing}"
        f'title="{title_attr}" '
        f'data-id="{aid}" data-name="{n}" data-day="{day}" '
        f'data-start="{s}" data-end="{e}" data-color="{c}"{note_attr} '
        f'style="top:{top:.1f}px;height:{ht:.1f}px;background:{c};'
        f'color:{tc};border-left-color:{bc}" '
        f'onclick="showCtx(event,this)">' + note_icon + body + "</div>"
    )


@st.cache_data(show_spinner=False)
def render_calendar(
    activities_json: str,
    sh: int,
    eh: int,
    _today: str = "",
    lang: Lang = "de",
    editing_id: str = "",
    component_mode: bool = False,
) -> str:
    acts: list[dict] = json.loads(activities_json)
    css = _load_css()
    total_px = int((eh - sh) * 60 * PX_PER_MIN)
    abs_start = sh * 60
    labels = _time_labels(sh, eh, abs_start)
    grid = _grid_lines(sh, eh, abs_start)
    short_days = WOCHENTAGE_KURZ_I18N[lang]

    day_cols = ""
    for di, (tag, tk) in enumerate(zip(WOCHENTAGE, short_days, strict=True)):
        day_acts = [a for a in acts if a.get("day") == tag]
        blocks = "".join(
            _activity_block(a, abs_start, eh, editing_id) for a in day_acts
        )
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

    _edit_label = "Bearbeiten ✏️" if lang == "de" else "Edit ✏️"
    ctx_js = _ctx_menu_js(_edit_label, component_mode=component_mode)
    cal_js = _calendar_js(PX_PER_MIN, sh, eh)
    js = ctx_js + cal_js

    body = (
        f'<div class="cal-outer">'
        f'  <div class="cal-time-col">'
        f'    <div class="cal-time-inner" style="height:{total_px}px">{labels}</div>'
        f"  </div>"
        f'  <div class="cal-cols">{day_cols}</div>'
        f'  <div class="cal-time-col cal-time-col--right">'
        f'    <div class="cal-time-inner" style="height:{total_px}px">{labels}</div>'
        f"  </div>"
        f"</div>"
    )

    if component_mode:
        return f"<style>{css}</style>{body}<script>{js}</script>"

    return (
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{css}</style></head><body>"
        f"{body}<script>{js}</script></body></html>"
    )
