"""
Kiwimath Usage Dashboard API — a single, key-gated endpoint that powers the
live founder dashboard.

GET /v3/admin/usage?key=...

It answers two questions:
  1. "How many people have used the app?"  -> Firebase Auth is the source of
     truth (every install that did anything has a Firebase account).
  2. "What are they doing?"                -> enriched per-user from Firestore
     users/{uid} profile + users/{uid}/gamification/state.

Design notes
------------
- Key-gated (not the email-allowlist auth used by /admin/analytics) so a static
  HTML dashboard can call it with no Firebase login. Set KIWIMATH_ADMIN_KEY in
  the environment to override the default; rotate it any time.
- CORS-open on this route only (it's read-only and key-gated) so the dashboard
  can be opened as a local file.
- Fully defensive: if Firebase/Firestore is unavailable it returns a clear
  {available: false} payload rather than 500-ing.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, HTMLResponse

logger = logging.getLogger("kiwimath.usage")

router = APIRouter(prefix="/v3", tags=["Usage Dashboard"])

# Override in the environment (recommended). Default lets the dashboard work
# immediately after a deploy; it only gates read-only aggregate stats.
ADMIN_KEY = os.environ.get("KIWIMATH_ADMIN_KEY", "kmx-founder-7Q2v9Lp4Ad")

_CORS = {"Access-Control-Allow-Origin": "*"}


def _ms_to_iso(ms: Optional[int]) -> Optional[str]:
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _days_since(iso: Optional[str], now: datetime) -> Optional[float]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).total_seconds() / 86400.0
    except Exception:
        return None


@router.get("/admin/usage")
def usage(key: str = Query("", description="Admin key")):
    if key != ADMIN_KEY:
        return JSONResponse({"error": "unauthorized"}, status_code=403, headers=_CORS)

    now = datetime.now(timezone.utc)

    # --- Firebase Auth: the master list of people ---
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        import firebase_admin
        from firebase_admin import auth as fb_auth
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            {"available": False, "reason": f"firebase libs unavailable: {e}"},
            headers=_CORS,
        )

    db = _get_db()  # also initialises firebase_admin app

    auth_users: List[Any] = []
    auth_ok = True
    try:
        for u in fb_auth.list_users().iterate_all():
            auth_users.append(u)
    except Exception as e:
        auth_ok = False
        logger.warning(f"auth.list_users failed: {e}")

    rows: List[Dict[str, Any]] = []
    seen = set()

    def _profile(uid: str) -> Dict[str, Any]:
        if not db:
            return {}
        try:
            doc = db.collection("users").document(uid).get()
            return doc.to_dict() or {} if doc.exists else {}
        except Exception:
            return {}

    def _gami(uid: str) -> Dict[str, Any]:
        if not db:
            return {}
        try:
            doc = (db.collection("users").document(uid)
                   .collection("gamification").document("state").get())
            return doc.to_dict() or {} if doc.exists else {}
        except Exception:
            return {}

    def _build_row(uid: str, created_iso, signin_iso, name, anon) -> Dict[str, Any]:
        prof = _profile(uid)
        g = _gami(uid)
        last_active = prof.get("last_active") or signin_iso
        # pick the most recent of auth-sign-in and profile-last-active
        la_days = _days_since(last_active, now)
        si_days = _days_since(signin_iso, now)
        if si_days is not None and (la_days is None or si_days < la_days):
            last_active, la_days = signin_iso, si_days
        attempts = int(g.get("total_attempts", 0) or 0)
        correct = int(g.get("total_correct", 0) or 0)
        topic_attempts = g.get("topic_attempts", {}) or {}
        return {
            "uid": uid,
            "name": name or prof.get("display_name") or ("(anonymous)" if anon else "(unnamed)"),
            "anonymous": anon,
            "grade": prof.get("grade"),
            "curriculum": prof.get("curriculum"),
            "created_at": created_iso,
            "last_active": last_active,
            "days_since_active": round(la_days, 1) if la_days is not None else None,
            "questions_answered": attempts,
            "correct": correct,
            "accuracy": round(100.0 * correct / attempts, 1) if attempts else None,
            "sessions": int(g.get("sessions_completed", 0) or 0),
            "streak_current": int(g.get("streak_current", prof.get("streak_current", 0)) or 0),
            "streak_longest": int(g.get("streak_longest", prof.get("streak_longest", 0)) or 0),
            "xp": int(g.get("xp_total", prof.get("xp_total", 0)) or 0),
            "coins": int(g.get("kiwi_coins", 0) or 0),
            "topics_touched": len(topic_attempts),
            "top_topics": topic_attempts,
        }

    if auth_ok:
        for u in auth_users:
            uid = u.uid
            seen.add(uid)
            md = getattr(u, "user_metadata", None)
            created_iso = _ms_to_iso(getattr(md, "creation_timestamp", None))
            signin_iso = _ms_to_iso(getattr(md, "last_sign_in_timestamp", None)
                                    or getattr(md, "last_refresh_timestamp", None))
            anon = not (u.email or (u.provider_data and len(u.provider_data) > 0))
            rows.append(_build_row(uid, created_iso, signin_iso, u.display_name, anon))
    else:
        # Fallback: enumerate the Firestore users collection if Auth listing failed.
        if db:
            try:
                for d in db.collection("users").stream():
                    uid = d.id
                    if uid in seen:
                        continue
                    seen.add(uid)
                    p = d.to_dict() or {}
                    rows.append(_build_row(uid, p.get("created_at"), p.get("last_active"),
                                           p.get("display_name"), False))
            except Exception as e:
                return JSONResponse({"available": False, "reason": f"firestore list failed: {e}"},
                                    headers=_CORS)

    # --- aggregates ---
    total = len(rows)
    def _active_within(days):
        return sum(1 for r in rows if r["days_since_active"] is not None and r["days_since_active"] <= days)

    by_day: Dict[str, int] = {}
    for r in rows:
        if r["created_at"]:
            day = r["created_at"][:10]
            by_day[day] = by_day.get(day, 0) + 1

    by_grade: Dict[str, int] = {}
    for r in rows:
        g = str(r["grade"]) if r["grade"] not in (None, "") else "—"
        by_grade[g] = by_grade.get(g, 0) + 1

    topic_totals: Dict[str, int] = {}
    for r in rows:
        for t, n in (r.get("top_topics") or {}).items():
            topic_totals[t] = topic_totals.get(t, 0) + int(n or 0)

    total_q = sum(r["questions_answered"] for r in rows)
    total_c = sum(r["correct"] for r in rows)
    total_sessions = sum(r["sessions"] for r in rows)

    # don't ship the bulky per-topic map in each row
    for r in rows:
        r.pop("top_topics", None)
    rows.sort(key=lambda r: (r["days_since_active"] is None, r["days_since_active"] if r["days_since_active"] is not None else 1e9))

    return JSONResponse({
        "available": True,
        "generated_at": now.isoformat(),
        "auth_listing_ok": auth_ok,
        "firestore_ok": bool(db),
        "totals": {
            "total_users": total,
            "active_24h": _active_within(1),
            "active_7d": _active_within(7),
            "active_30d": _active_within(30),
            "new_7d": sum(1 for r in rows if _days_since(r["created_at"], now) is not None and _days_since(r["created_at"], now) <= 7),
            "questions_answered": total_q,
            "correct": total_c,
            "avg_accuracy": round(100.0 * total_c / total_q, 1) if total_q else None,
            "sessions": total_sessions,
            "anonymous_users": sum(1 for r in rows if r["anonymous"]),
        },
        "new_users_by_day": dict(sorted(by_day.items())),
        "by_grade": dict(sorted(by_grade.items())),
        "by_topic": dict(sorted(topic_totals.items(), key=lambda kv: -kv[1])[:15]),
        "users": rows,
    }, headers=_CORS)


# ---------------------------------------------------------------------------
# Same-origin dashboard page (no CORS — fetches the endpoint relatively).
# Open:  https://<backend>/v3/dashboard?key=<admin key>
# ---------------------------------------------------------------------------

_DASH_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Kiwimath Live</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--orange:#FF6F00;--ink:#1E1633;--mute:#7A7290;--line:#E9E3F2;--green:#2FA866}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(170deg,#efe9f6,#f6f1ee);color:#231C30;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.top{background:var(--ink);color:#fff;padding:15px 22px;display:flex;align-items:center;gap:12px}
.top h1{font-size:18px;margin:0;font-weight:800}.tag{font-size:11px;font-weight:700;color:#1E1633;background:var(--orange);padding:3px 9px;border-radius:20px}
.st{margin-left:auto;font-size:12.5px;color:#cfc6e6}
.wrap{max-width:1180px;margin:0 auto;padding:16px 22px 50px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:16px;padding:15px 17px;box-shadow:0 8px 22px -16px rgba(40,20,60,.3)}
.kpi .v{font-size:30px;font-weight:800;color:var(--ink);letter-spacing:-1px;line-height:1}.kpi.hl .v{color:#E25E00}
.kpi .l{font-size:12px;color:var(--mute);margin-top:6px;font-weight:600}
.cards{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:13px;margin:14px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:15px 17px;box-shadow:0 8px 22px -16px rgba(40,20,60,.3)}
.card h3{font-size:12.5px;font-weight:800;margin:0 0 8px;text-transform:uppercase;letter-spacing:.4px;color:var(--ink)}
.card canvas{max-height:190px}
.tc{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 8px 22px -16px rgba(40,20,60,.3)}
.tc .hd{padding:13px 18px;font-size:12.5px;font-weight:800;text-transform:uppercase;letter-spacing:.4px;color:var(--ink);border-bottom:1px solid var(--line)}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:9px 14px;text-align:left;white-space:nowrap}
th{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--mute);cursor:pointer}th:hover{color:#E25E00}
tbody tr{border-bottom:1px solid #f3eef8}tbody tr:hover{background:#faf7fd}.num{text-align:right;font-variant-numeric:tabular-nums}
.rp{display:inline-block;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700}
.now{background:#e7f8ee;color:var(--green)}.wk{background:#fff3e0;color:#E25E00}.old{background:#f1eef6;color:var(--mute)}
.err{background:#fdecef;border:1px solid #f6c2cd;color:#9a2740;border-radius:12px;padding:14px;margin:14px 0;font-size:14px}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}}
</style></head><body>
<div class="top"><h1>\U0001F95D Kiwimath</h1><span class="tag">LIVE</span><span class="st" id="st">Loading…</span></div>
<div class="wrap"><div id="banner"></div><div class="kpis" id="kpis"></div>
<div class="cards"><div class="card"><h3>New users by day</h3><canvas id="chDay"></canvas></div>
<div class="card"><h3>By grade</h3><canvas id="chGrade"></canvas></div>
<div class="card"><h3>Top topics</h3><canvas id="chTopic"></canvas></div></div>
<div class="tc"><div class="hd">Who's using it · what they're doing</div><div style="overflow-x:auto"><table>
<thead><tr><th onclick="sb('name')">User</th><th onclick="sb('grade')">Grade</th><th onclick="sb('created_at')">Joined</th>
<th onclick="sb('days_since_active')">Last seen</th><th class="num" onclick="sb('questions_answered')">Questions</th>
<th class="num" onclick="sb('accuracy')">Accuracy</th><th class="num" onclick="sb('streak_current')">Streak</th>
<th class="num" onclick="sb('xp')">XP</th></tr></thead><tbody id="tb"></tbody></table></div></div></div>
<script>
const KEY=new URLSearchParams(location.search).get('key')||'';
const $=i=>document.getElementById(i);let ch={},data=null,sk='days_since_active',sd=1;
function fd(s){if(!s)return'—';try{return new Date(s).toLocaleDateString(undefined,{month:'short',day:'numeric'})}catch(e){return'—'}}
function rec(d){if(d==null)return['—','old'];if(d<=1)return['today','now'];if(d<=7)return[Math.round(d)+'d ago','wk'];return[Math.round(d)+'d ago','old']}
function esc(s){return(s==null?'':String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function load(){try{const r=await fetch('/v3/admin/usage?key='+encodeURIComponent(KEY));
if(r.status===403){$('banner').innerHTML='<div class=err>Add ?key=YOUR_KEY to the URL.</div>';$('st').textContent='unauthorized';return}
const d=await r.json();if(d.available===false){$('banner').innerHTML='<div class=err>Data layer unavailable: '+(d.reason||'')+'</div>';return}
data=d;render(d);$('st').textContent='Updated '+new Date(d.generated_at).toLocaleTimeString()+' · '+d.totals.total_users+' users';
}catch(e){$('st').textContent='error';$('banner').innerHTML='<div class=err>'+e.message+'</div>'}}
function kpi(v,l,h){return'<div class="kpi'+(h?' hl':'')+'"><div class=v>'+v+'</div><div class=l>'+l+'</div></div>'}
function render(d){const t=d.totals;$('kpis').innerHTML=kpi(t.total_users,'Total users',1)+kpi(t.active_7d,'Active this week')
+kpi(t.active_24h,'Active today')+kpi(t.new_7d,'New this week')+kpi(t.questions_answered.toLocaleString(),'Questions answered')
+kpi(t.avg_accuracy!=null?t.avg_accuracy+'%':'—','Avg accuracy')+kpi(t.sessions,'Sessions')+kpi(t.anonymous_users,'Anon logins');
if(t.total_users===0)$('banner').innerHTML='<div class=err>No users yet.</div>';
bar('chDay',Object.keys(d.new_users_by_day),Object.values(d.new_users_by_day),'#FF6F00');
dough('chGrade',Object.keys(d.by_grade),Object.values(d.by_grade));
bar('chTopic',Object.keys(d.by_topic).map(k=>k.replace(/^.*?-/,'').slice(0,15)),Object.values(d.by_topic),'#12A99B',1);tbl(d.users)}
function tbl(u){const a=[...u].sort((x,y)=>{let p=x[sk],q=y[sk];if(p==null)p=sk==='days_since_active'?1e9:'';if(q==null)q=sk==='days_since_active'?1e9:'';
return typeof p==='string'?sd*p.localeCompare(q):sd*(p-q)});
$('tb').innerHTML=a.map(u=>{const[rt,rc]=rec(u.days_since_active);return'<tr><td><b>'+esc(u.name)+'</b></td><td>'+(u.grade??'—')+'</td><td>'+fd(u.created_at)
+'</td><td><span class="rp '+rc+'">'+rt+'</span></td><td class=num>'+(u.questions_answered||0)+'</td><td class=num>'+(u.accuracy!=null?u.accuracy+'%':'—')
+'</td><td class=num>'+(u.streak_current||0)+'\U0001F525</td><td class=num>'+(u.xp||0)+'</td></tr>'}).join('')||'<tr><td colspan=8 style="padding:18px;color:#7A7290">No users yet.</td></tr>'}
function sb(k){sd=(sk===k)?-sd:1;sk=k;if(data)tbl(data.users)}
function bar(i,l,d,c,h){if(ch[i])ch[i].destroy();ch[i]=new Chart($(i),{type:'bar',data:{labels:l,datasets:[{data:d,backgroundColor:c,borderRadius:6,maxBarThickness:32}]},
options:{indexAxis:h?'y':'x',plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:10},color:'#7A7290'}},y:{grid:{color:'#f0ecf6'},ticks:{font:{size:10},color:'#7A7290',precision:0}}}}})}
function dough(i,l,d){if(ch[i])ch[i].destroy();ch[i]=new Chart($(i),{type:'doughnut',data:{labels:l.map(x=>'Grade '+x),datasets:[{data:d,backgroundColor:['#FF6F00','#12A99B','#7A5CFF','#FF5470','#F5A623','#2FA866','#cfc8da']}]},options:{plugins:{legend:{position:'right',labels:{font:{size:11},boxWidth:12}}},cutout:'58%'}})}
setInterval(load,60000);load();
</script></body></html>"""


@router.get("/dashboard")
def dashboard():
    """Serve the live dashboard same-origin (no CORS). Pass ?key=... in the URL."""
    return HTMLResponse(_DASH_HTML, headers=_CORS)
