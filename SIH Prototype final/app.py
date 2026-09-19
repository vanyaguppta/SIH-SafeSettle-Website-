"""
ASCENDANT — SAFESETTLE  (Assam Flood Relief Edition)
Single-file Flask application.

Run with:  pip install flask   then   python app.py
Open:      http://localhost:5000

Everything — backend API, SQLite database, and the entire frontend
(HTML/CSS/JS, cinematic landing page + SafeSettle dashboard) — lives in
this ONE file. No React/Node/npm needed.

DATA HONESTY NOTES (read before your viva):
- Village/habitation names, population figures and risk scores are SAMPLE /
  ILLUSTRATIVE data placed near real Assam districts (Sivasagar, Charaideo,
  Jorhat, Golaghat, Kamrup Metro) for a realistic-looking demo. They are not
  scraped real GIS records.
- The helpline numbers in `seed_data()` -> `survey_team` are copied from the
  official Assam State Disaster Management Authority public flood-helpline
  notice and an NGO relief-contact list you supplied. They look real and are
  published for exactly this purpose (public flood assistance), but phone
  numbers and duty rosters change — verify they are still active before
  relying on them or presenting them as live.
- The food-stock numbers and per-person daily requirements are exactly what
  you provided; the "days remaining" calculator below is straightforward
  arithmetic on those numbers, nothing fabricated.
"""

import os
import sqlite3
from flask import Flask, jsonify, request, g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safesettle.db")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def seed_data():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE habitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, district TEXT, state TEXT, lat REAL, lng REAL,
            population INTEGER, households INTEGER,
            risk_score INTEGER, risk_level TEXT,
            flood_risk INTEGER, landslide_risk INTEGER, cloudburst_risk INTEGER,
            cyclone_risk INTEGER, historical_events INTEGER, vulnerability_score INTEGER,
            hazard_exposure_pct INTEGER, population_vuln_pct INTEGER,
            accessibility_pct INTEGER, infra_exposure_pct INTEGER, historical_impact_pct INTEGER,
            children INTEGER, elderly INTEGER, pwd INTEGER,
            low_income_hh INTEGER, women_headed_hh INTEGER, recommendation TEXT
        );
        CREATE TABLE sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, lat REAL, lng REAL, safety_score INTEGER, capacity INTEGER,
            road_access TEXT, hospital_km REAL, water_availability TEXT,
            school_capacity TEXT, hazard_exposure TEXT
        );
        CREATE TABLE habitation_sites (
            habitation_id INTEGER, site_id INTEGER, distance_km REAL,
            suitability_score INTEGER, recommended INTEGER
        );
        CREATE TABLE survey_team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, role TEXT, phone TEXT, area TEXT, status TEXT, source TEXT
        );
        CREATE TABLE food_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT, stock REAL, unit TEXT, per_person_daily REAL, per_person_unit TEXT
        );
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, severity TEXT, title TEXT, message TEXT,
            habitation_id INTEGER, created_at TEXT
        );
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, mobile TEXT, email TEXT, created_at TEXT
        );
        """
    )

    # ---- Habitations: sample data placed near real Assam districts ----
    habitations = [
        ("Sivasagar Riverside Basti", "Sivasagar", "Assam", 26.9850, 94.6417, 3120, 640,
         88, "Very High", 90, 20, 55, 15, 85, 80, 40, 25, 15, 10, 10,
         780, 430, 95, 300, 210, "Immediate / Short-term relocation recommended."),
        ("Charaideo Char Area", "Charaideo", "Assam", 27.0167, 95.1667, 2280, 430,
         79, "High", 82, 15, 48, 12, 60, 66, 40, 25, 15, 10, 10,
         560, 300, 62, 195, 140, "Short-term relocation recommended; monitor Brahmaputra levels."),
        ("Jorhat Bank Colony", "Jorhat", "Assam", 26.7509, 94.2037, 1940, 370,
         61, "Moderate", 58, 10, 40, 10, 42, 50, 40, 25, 15, 10, 10,
         430, 260, 44, 150, 108, "Continue monitoring; strengthen embankments."),
        ("Golaghat Lowland Village", "Golaghat", "Assam", 26.5106, 93.9600, 1520, 300,
         70, "High", 72, 12, 45, 10, 55, 58, 40, 25, 15, 10, 10,
         360, 205, 42, 128, 92, "Short-term relocation recommended."),
        ("Kamrup Metro Wetland Basti", "Kamrup Metro", "Assam", 26.1445, 91.7362, 2650, 520,
         83, "Very High", 85, 18, 52, 14, 78, 74, 40, 25, 15, 10, 10,
         640, 380, 78, 255, 176, "Immediate / Short-term relocation recommended."),
        ("Golaghat Upland Hamlet", "Golaghat", "Assam", 26.5400, 93.9900, 960, 190,
         31, "Low", 26, 10, 22, 8, 18, 28, 40, 25, 15, 10, 10,
         205, 128, 19, 68, 48, "Low priority; routine monitoring sufficient."),
    ]
    cur.executemany(
        """INSERT INTO habitations
        (name, district, state, lat, lng, population, households, risk_score, risk_level,
         flood_risk, landslide_risk, cloudburst_risk, cyclone_risk, historical_events,
         vulnerability_score, hazard_exposure_pct, population_vuln_pct, accessibility_pct,
         infra_exposure_pct, historical_impact_pct, children, elderly, pwd,
         low_income_hh, women_headed_hh, recommendation)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        habitations,
    )

    # ---- Relocation sites: safer elevated ground near the same districts ----
    sites = [
        ("Sivasagar Town Relief Site", 26.9820, 94.6380, 90, 3500, "Good", 2.8, "Good", "Adequate", "Low"),
        ("Jorhat Elevated Ground Site", 26.7550, 94.2100, 82, 2600, "Moderate", 5.2, "Moderate", "Limited", "Low"),
        ("Golaghat Highland Site", 26.5450, 93.9700, 86, 3000, "Good", 4.0, "Good", "Adequate", "Low"),
    ]
    cur.executemany(
        """INSERT INTO sites (name, lat, lng, safety_score, capacity, road_access,
        hospital_km, water_availability, school_capacity, hazard_exposure)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        sites,
    )

    hab_sites = [
        (1, 1, 3.5, 92, 1), (1, 2, 22.0, 58, 0), (1, 3, 30.0, 55, 0),
        (2, 1, 25.0, 60, 0), (2, 2, 15.0, 85, 1),
        (4, 3, 4.5, 89, 1), (4, 1, 30.0, 52, 0),
        (5, 1, 35.0, 50, 0), (5, 2, 28.0, 70, 1),
    ]
    cur.executemany(
        "INSERT INTO habitation_sites (habitation_id, site_id, distance_km, suitability_score, recommended) VALUES (?,?,?,?,?)",
        hab_sites,
    )

    # ---- Survey team / helplines — from Assam SDMA public notice + relief NGOs you shared ----
    survey_team = [
        ("Assam SDMA — State Control Room", "24x7 State Control Room", "03612-237219 / 09401044617", "All Assam", "Available", "Official notice"),
        ("National Toll-Free Helpline", "Disaster Toll-Free (India)", "1070 / 1079 / 112", "All Assam", "Available", "Official notice"),
        ("District Control Room", "District Emergency Line", "1077 / 112", "All Districts", "Available", "Official notice"),
        ("Sivasagar Flood Helpline", "District Flood Helpline", "8471864355", "Sivasagar", "Available", "Official notice"),
        ("Charaideo Flood Helpline", "District Flood Helpline", "9085412180", "Charaideo", "Available", "Official notice"),
        ("Jorhat Flood Helpline", "District Flood Helpline", "0376-2300124", "Jorhat", "Available", "Official notice"),
        ("Golaghat Flood Helpline", "District Flood Helpline", "9394985421", "Golaghat", "Available", "Official notice"),
        ("Guwahati / Kamrup Metro Admin Helpline", "District Administration Helpline", "8638112297", "Kamrup Metro", "Available", "District records"),
        ("Mission Green Mumbai & Frontline Alliance", "Ground Relief Distribution — Subhajit Mukherjee", "9323942388", "Multi-district", "On Duty", "NGO relief contact"),
        ("Smile Foundation — Assam Relief", "Medical camps & relief material", "See smilefoundationindia.org", "Morigaon & flood-hit areas", "Available", "NGO relief contact"),
        ("NEAID", "WASH kits, ration, maternal relief kits", "See NEAID official channels", "Nagaon & other districts", "Available", "NGO relief contact"),
    ]
    cur.executemany(
        "INSERT INTO survey_team (name, role, phone, area, status, source) VALUES (?,?,?,?,?,?)", survey_team
    )

    # ---- Food inventory: exact figures supplied by the user ----
    food = [
        ("Rice", 450, "kg", 150, "g/person/day"),
        ("Atta", 360, "kg", 120, "g/person/day"),
        ("Dal", 120, "kg", 40, "g/person/day"),
        ("Cooking Oil", 90, "litres", 30, "ml/person/day"),
        ("Sugar", 60, "kg", 20, "g/person/day"),
        ("Salt", 15, "kg", 5, "g/person/day"),
        ("Fresh Vegetables", 600, "kg", 200, "g/person/day"),
    ]
    cur.executemany(
        "INSERT INTO food_inventory (item, stock, unit, per_person_daily, per_person_unit) VALUES (?,?,?,?,?)",
        food,
    )

    alerts = [
        ("HIGH RISK UPDATE", "high", "Sivasagar Riverside Basti", "River level near danger mark; cloudburst risk elevated.", 1, "2026-09-12 08:00"),
        ("RELOCATION ALERT", "moderate", "Jorhat Elevated Ground Site", "Relocation site capacity approaching limit.", None, "2026-09-11 17:30"),
        ("WEATHER ALERT", "high", "Regional", "Heavy rainfall expected across Sivasagar and Charaideo in next 24h.", None, "2026-09-13 06:00"),
        ("HIGH RISK UPDATE", "high", "Kamrup Metro Wetland Basti", "Waterlogging risk revised upward after continuous rain.", 5, "2026-09-10 14:00"),
        ("RESOURCE ALERT", "moderate", "Central Relief Store", "Dal and cooking oil stock below 15-day buffer.", None, "2026-09-12 19:00"),
    ]
    cur.executemany(
        "INSERT INTO alerts (type, severity, title, message, habitation_id, created_at) VALUES (?,?,?,?,?,?)",
        alerts,
    )

    conn.commit()
    conn.close()


# ------------------------------------------------------------------- API --

@app.route("/api/dashboard/stats")
def api_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) c FROM habitations").fetchone()["c"]
    levels = {lv: db.execute("SELECT COUNT(*) c FROM habitations WHERE risk_level=?", (lv,)).fetchone()["c"]
              for lv in ["Very High", "High", "Moderate", "Low"]}
    return jsonify({"total": total, "levels": levels})


@app.route("/api/habitations")
def api_habitations():
    db = get_db()
    q = "SELECT * FROM habitations WHERE 1=1"
    params = []
    if request.args.get("risk_level"):
        q += " AND risk_level=?"; params.append(request.args["risk_level"])
    if request.args.get("district"):
        q += " AND district=?"; params.append(request.args["district"])
    if request.args.get("search"):
        q += " AND name LIKE ?"; params.append(f"%{request.args['search']}%")
    rows = db.execute(q, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/habitations/<int:hid>")
def api_habitation(hid):
    db = get_db()
    row = db.execute("SELECT * FROM habitations WHERE id=?", (hid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.route("/api/habitations/<int:hid>/sites")
def api_site_comparison(hid):
    db = get_db()
    rows = db.execute(
        """SELECT s.*, hs.distance_km, hs.suitability_score, hs.recommended
           FROM habitation_sites hs JOIN sites s ON s.id = hs.site_id
           WHERE hs.habitation_id=? ORDER BY hs.suitability_score DESC""",
        (hid,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/relocation-plan/<int:hid>")
def api_plan(hid):
    db = get_db()
    hab = db.execute("SELECT * FROM habitations WHERE id=?", (hid,)).fetchone()
    site = db.execute(
        """SELECT s.*, hs.distance_km, hs.suitability_score FROM habitation_sites hs
           JOIN sites s ON s.id = hs.site_id WHERE hs.habitation_id=? AND hs.recommended=1""",
        (hid,),
    ).fetchone()
    if not hab or not site:
        return jsonify({"error": "no recommended site found"}), 404
    pop = hab["population"]
    p1 = round(pop * 0.36); p2 = round(pop * 0.37); p3 = pop - p1 - p2
    return jsonify({
        "habitation": dict(hab), "site": dict(site),
        "phases": [
            {"phase": "Phase 1 - Immediate", "label": "High Vulnerable Population", "count": p1, "pct": 36},
            {"phase": "Phase 2 - Short Term", "label": "Next Priority Population", "count": p2, "pct": 37},
            {"phase": "Phase 3 - Medium Term", "label": "Remaining Population", "count": p3, "pct": 27},
        ],
        "supporting_actions": [
            "Prepare transport and logistics",
            "Ensure temporary shelter availability",
            "Coordinate water, health and sanitation",
            "Monitor weather and river-level updates",
        ],
    })


@app.route("/api/survey-team")
def api_team():
    db = get_db()
    return jsonify([dict(r) for r in db.execute("SELECT * FROM survey_team").fetchall()])


@app.route("/api/food-inventory")
def api_food():
    db = get_db()
    return jsonify([dict(r) for r in db.execute("SELECT * FROM food_inventory").fetchall()])


@app.route("/api/alerts")
def api_alerts():
    db = get_db()
    return jsonify([dict(r) for r in db.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()])


@app.route("/api/report/<int:hid>")
def api_report(hid):
    db = get_db()
    hab = db.execute("SELECT * FROM habitations WHERE id=?", (hid,)).fetchone()
    if not hab:
        return jsonify({"error": "not found"}), 404
    sites = db.execute(
        """SELECT s.*, hs.distance_km, hs.suitability_score, hs.recommended
           FROM habitation_sites hs JOIN sites s ON s.id = hs.site_id
           WHERE hs.habitation_id=? ORDER BY hs.suitability_score DESC""",
        (hid,),
    ).fetchall()
    return jsonify({"habitation": dict(hab), "sites": [dict(s) for s in sites]})


@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "Ascendant SafeSettle",
        "short_name": "SafeSettle",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b1220",
        "theme_color": "#0b1220",
        "orientation": "portrait",
        "icons": [
            {"src": "/icon.svg", "sizes": "192x192", "type": "image/svg+xml", "purpose": "any"},
            {"src": "/icon.svg", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any"},
        ],
    })


@app.route("/icon.svg")
def icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient></defs>
    <rect width="200" height="200" rx="44" fill="url(#g)"/>
    <text x="100" y="135" font-size="110" font-weight="800" font-family="Arial, sans-serif"
          fill="#ffffff" text-anchor="middle">A</text>
    </svg>"""
    return app.response_class(svg, mimetype="image/svg+xml")


@app.route("/sw.js")
def service_worker():
    js = """
    const CACHE = 'safesettle-v1';
    self.addEventListener('install', e => { self.skipWaiting(); });
    self.addEventListener('activate', e => { self.clients.claim(); });
    self.addEventListener('fetch', e => {
      // Network-first; falls back to cache if offline (basic offline support).
      e.respondWith(
        fetch(e.request).then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
          return res;
        }).catch(() => caches.match(e.request))
      );
    });
    """
    return app.response_class(js, mimetype="application/javascript")


@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True)
        db.execute("DELETE FROM users")
        db.execute(
            "INSERT INTO users (name, mobile, email, created_at) VALUES (?,?,?,datetime('now'))",
            (data.get("name", ""), data.get("mobile", ""), data.get("email", "")),
        )
        db.commit()
        return jsonify({"ok": True})
    row = db.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify(dict(row) if row else {})


# -------------------------------------------------------------- frontend --

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Ascendant — SafeSettle | Assam Flood Relief</title>
<link rel="manifest" href="/manifest.json" />
<link rel="icon" href="/icon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/icon.svg" />
<meta name="theme-color" content="#0b1220" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<style>
:root{
  --navy:#0b1220;--navy2:#0f1a2e;
  --blue:#2563eb;--blue2:#3b82f6;
  --accent1:#6366f1;--accent2:#06b6d4;--accent3:#f43f5e;
  --red:#dc2626;--orange:#ea580c;--amber:#d97706;--green:#16a34a;
  --bg:#f4f6fb;--card:#fff;--text:#101828;--muted:#667085;--border:#e5e9f0;--r:16px;
}
*{box-sizing:border-box;}
html,body,#root{height:100%;margin:0;}
body{font-family:'Segoe UI',Inter,system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);}
a{text-decoration:none;color:inherit;cursor:pointer;}
button{font-family:inherit;cursor:pointer;}
::-webkit-scrollbar{width:8px;height:8px;}
::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px;}

/* ---------------- Landing / cinematic ---------------- */
.landing{min-height:100vh;width:100%;position:relative;overflow:hidden;background:#05070d;
color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
#particle-canvas{position:absolute;inset:0;z-index:0;}
.landing::after{content:"";position:absolute;inset:0;z-index:1;
background:radial-gradient(circle at 50% 30%, rgba(99,102,241,0.28) 0%, rgba(5,7,13,0.2) 45%, #05070d 85%);pointer-events:none;}
.landing-content{position:relative;z-index:2;animation:fadeUp 1.3s ease;}
@keyframes fadeUp{from{opacity:0;transform:translateY(28px);}to{opacity:1;transform:translateY(0);}}
.landing .logo-mark{width:100px;height:100px;margin:0 auto 22px auto;border-radius:26px;
background:linear-gradient(135deg,var(--accent1) 0%,var(--accent2) 100%);display:flex;align-items:center;justify-content:center;
font-size:42px;font-weight:800;color:#fff;box-shadow:0 0 70px rgba(99,102,241,.6);animation:pulseLogo 3.2s ease-in-out infinite;}
@keyframes pulseLogo{0%,100%{box-shadow:0 0 50px rgba(99,102,241,.55);transform:scale(1);}50%{box-shadow:0 0 90px rgba(6,182,212,.65);transform:scale(1.04);}}
.landing h1{font-size:48px;margin:0 0 6px 0;letter-spacing:7px;font-weight:300;}
.landing h1 b{font-weight:800;background:linear-gradient(90deg,var(--accent2),var(--accent1));-webkit-background-clip:text;background-clip:text;color:transparent;}
.landing .tagline{font-size:19px;background:linear-gradient(90deg,#93c5fd,#67e8f9);-webkit-background-clip:text;background-clip:text;color:transparent;margin-bottom:8px;letter-spacing:1px;font-weight:600;}
.landing .subtext{font-size:14px;color:#94a3b8;max-width:500px;margin:0 auto 34px auto;}
.landing .enter-btn{background:linear-gradient(135deg,var(--accent1),var(--accent2));color:#fff;border:none;padding:16px 40px;border-radius:44px;
font-size:14px;letter-spacing:2px;font-weight:700;box-shadow:0 12px 44px rgba(99,102,241,.5);transition:transform .25s, box-shadow .25s;}
.landing .enter-btn:hover{transform:translateY(-3px) scale(1.04);box-shadow:0 16px 54px rgba(6,182,212,.55);}
.landing .badges{display:flex;gap:14px;justify-content:center;margin-top:26px;flex-wrap:wrap;}
.landing .badge-pill{font-size:11px;color:#cbd5e1;border:1px solid rgba(255,255,255,.18);padding:6px 14px;border-radius:20px;background:rgba(255,255,255,.04);}

/* ---------------- App shell ---------------- */
.app-shell{display:flex;min-height:100vh;}
.sidebar{width:246px;background:linear-gradient(180deg,var(--navy) 0%,var(--navy2) 100%);color:#cbd5e1;
display:flex;flex-direction:column;padding:22px 14px;position:sticky;top:0;height:100vh;}
.sidebar .brand{display:flex;align-items:center;gap:10px;padding:0 8px 22px 8px;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:18px;}
.sidebar .brand .dot{width:12px;height:12px;border-radius:50%;background:var(--accent2);box-shadow:0 0 14px var(--accent2);animation:blink 2s infinite;}
@keyframes blink{50%{opacity:.4;}}
.sidebar .brand h1{font-size:16px;margin:0;color:#fff;letter-spacing:.5px;}
.sidebar .brand span{font-size:11px;color:#94a3b8;}
.sidebar nav{display:flex;flex-direction:column;gap:4px;flex:1;}
.sidebar nav a{padding:10px 12px;border-radius:10px;font-size:14px;color:#cbd5e1;display:flex;align-items:center;gap:10px;transition:.15s;}
.sidebar nav a:hover{background:rgba(255,255,255,.07);transform:translateX(2px);}
.sidebar nav a.active{background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#fff;font-weight:600;}
.sidebar .foot{font-size:11px;color:#64748b;padding:8px;}

.topbar{display:flex;justify-content:flex-end;align-items:center;gap:14px;padding:6px 0 18px 0;}
.icon-btn{position:relative;width:40px;height:40px;border-radius:50%;background:#fff;border:1px solid var(--border);
display:flex;align-items:center;justify-content:center;font-size:17px;}
.icon-btn .dotcount{position:absolute;top:-4px;right:-4px;background:var(--accent3);color:#fff;font-size:10px;font-weight:700;
border-radius:10px;padding:1px 5px;min-width:16px;text-align:center;}
.notif-dropdown{position:absolute;top:52px;right:32px;width:320px;max-height:380px;overflow-y:auto;background:#fff;
border:1px solid var(--border);border-radius:14px;box-shadow:0 12px 40px rgba(16,24,40,.15);z-index:50;display:none;}
.notif-dropdown.open{display:block;}
.notif-dropdown .nd-item{padding:12px 14px;border-bottom:1px solid var(--border);font-size:13px;}
.notif-dropdown .nd-item b{display:block;margin-bottom:2px;}
.notif-dropdown .nd-head{padding:10px 14px;font-weight:700;font-size:13px;border-bottom:1px solid var(--border);background:#f8fafc;border-radius:14px 14px 0 0;}

.toast-stack{position:fixed;top:20px;right:20px;z-index:999;display:flex;flex-direction:column;gap:10px;}
.toast{background:#fff;border-left:4px solid var(--accent3);border-radius:12px;padding:12px 16px;box-shadow:0 10px 30px rgba(16,24,40,.18);
min-width:260px;max-width:320px;animation:slideIn .35s ease;font-size:13px;}
.toast b{display:block;margin-bottom:2px;}
.toast.fade-out{animation:slideOut .35s ease forwards;}
@keyframes slideIn{from{opacity:0;transform:translateX(40px);}to{opacity:1;transform:translateX(0);}}
@keyframes slideOut{to{opacity:0;transform:translateX(40px);}}

.main{flex:1;padding:20px 32px 32px 32px;max-width:1440px;}
.main-content{animation:contentFade .4s ease;}
@keyframes contentFade{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px;}
.page-header h2{margin:0 0 4px 0;font-size:23px;}
.page-header p{margin:0;color:var(--muted);font-size:14px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:20px;box-shadow:0 2px 10px rgba(16,24,40,.05);}
.stats-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:20px;}
@media(max-width:1100px){.stats-grid{grid-template-columns:repeat(2,1fr);}}
.stat-card{padding:16px 18px;border-radius:var(--r);background:var(--card);border:1px solid var(--border);position:relative;overflow:hidden;}
.stat-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;}
.stat-card.total::before{background:linear-gradient(90deg,var(--accent1),var(--accent2));}
.stat-card.vhigh::before{background:var(--red);}
.stat-card.high::before{background:var(--orange);}
.stat-card.moderate::before{background:var(--amber);}
.stat-card.low::before{background:var(--green);}
.stat-card .label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;}
.stat-card .value{font-size:30px;font-weight:800;margin-top:4px;}
.stat-card.total .value{color:var(--accent1);}
.stat-card.vhigh .value{color:var(--red);}
.stat-card.high .value{color:var(--orange);}
.stat-card.moderate .value{color:var(--amber);}
.stat-card.low .value{color:var(--green);}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;}
.badge.Very-High{background:#fee2e2;color:var(--red);}
.badge.High{background:#ffedd5;color:var(--orange);}
.badge.Moderate{background:#fef3c7;color:#92400e;}
.badge.Low{background:#dcfce7;color:var(--green);}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:10px;}
.legend .sw{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;}
.grid-2{display:grid;grid-template-columns:2fr 1fr;gap:18px;}
@media(max-width:1000px){.grid-2{grid-template-columns:1fr;}}
.map-box{height:480px;border-radius:var(--r);overflow:hidden;border:1px solid var(--border);}
.list-row{display:flex;justify-content:space-between;align-items:center;padding:12px 6px;border-bottom:1px solid var(--border);font-size:14px;}
.list-row:last-child{border-bottom:none;}
.btn{border:none;border-radius:10px;padding:10px 18px;font-size:14px;font-weight:600;transition:transform .15s;}
.btn:hover{transform:translateY(-1px);}
.btn-primary{background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#fff;}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text);}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;}
.filters select,.filters input{padding:9px 12px;border-radius:10px;border:1px solid var(--border);font-size:13px;background:#fff;}
.progress-row{margin-bottom:12px;}
.progress-row .top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;}
.progress-track{height:8px;border-radius:6px;background:#eef1f6;overflow:hidden;}
.progress-fill{height:100%;border-radius:6px;transition:width 1s ease;}
.recommendation-box{border-radius:var(--r);padding:18px;background:#fff7ed;border:1px solid #fed7aa;margin-top:18px;}
.recommendation-box.good{background:#f0fdf4;border-color:#bbf7d0;}
.site-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;}
.site-card{border-radius:var(--r);border:1px solid var(--border);padding:18px;background:#fff;position:relative;}
.site-card.recommended{border:2px solid var(--green);box-shadow:0 0 0 4px #dcfce766;}
.site-card .tag{position:absolute;top:-10px;right:14px;background:var(--green);color:#fff;font-size:11px;padding:3px 10px;border-radius:20px;font-weight:700;}
.phase-card{border-left:4px solid var(--accent1);padding:14px 16px;border-radius:10px;background:#fff;border-top:1px solid var(--border);border-right:1px solid var(--border);border-bottom:1px solid var(--border);margin-bottom:12px;}
.alert-item{display:flex;gap:12px;padding:14px;border-radius:12px;border:1px solid var(--border);margin-bottom:10px;}
.alert-item.high{border-left:4px solid var(--red);}
.alert-item.moderate{border-left:4px solid var(--orange);}
.team-card{border:1px solid var(--border);border-radius:var(--r);padding:16px;display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:10px;flex-wrap:wrap;}
.chat-box{border:1px solid var(--border);border-radius:var(--r);height:360px;display:flex;flex-direction:column;}
.chat-messages{flex:1;padding:14px;overflow-y:auto;}
.chat-bubble{max-width:70%;padding:10px 14px;border-radius:14px;margin-bottom:8px;font-size:14px;}
.chat-bubble.me{background:var(--blue);color:#fff;margin-left:auto;}
.chat-bubble.them{background:#eef1f6;}
.chat-input{display:flex;border-top:1px solid var(--border);}
.chat-input input{flex:1;border:none;padding:12px;font-size:14px;}
.chat-input button{border:none;background:var(--blue);color:#fff;padding:0 20px;}
.disclaimer-banner{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;padding:10px 16px;border-radius:10px;font-size:12.5px;margin-bottom:18px;}
.form-grid{display:grid;gap:14px;max-width:420px;}
.form-grid label{font-size:13px;font-weight:600;margin-bottom:4px;display:block;}
.form-grid input{padding:11px 14px;border-radius:10px;border:1px solid var(--border);font-size:14px;width:100%;}
.profile-chip{display:flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--border);border-radius:30px;padding:5px 14px 5px 5px;font-size:13px;}
.profile-chip .av{width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,var(--accent1),var(--accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;}
.food-calc-result{margin-top:14px;padding:14px;border-radius:12px;background:#f0fdf4;border:1px solid #bbf7d0;}
.zone-pulse{animation:zonePulse 2.4s ease-in-out infinite;}
@keyframes zonePulse{0%,100%{opacity:.55;}50%{opacity:.15;}}
.pulse-dot{width:20px;height:20px;border-radius:50%;background:var(--red);border:2px solid #fff;box-shadow:0 0 0 rgba(220,38,38,.6);animation:dotPulse 1.6s infinite;}
@keyframes dotPulse{0%{box-shadow:0 0 0 0 rgba(220,38,38,.55);}70%{box-shadow:0 0 0 14px rgba(220,38,38,0);}100%{box-shadow:0 0 0 0 rgba(220,38,38,0);}}
</style>
</head>
<body>

<div id="landing-view" class="landing">
  <canvas id="particle-canvas"></canvas>
  <div class="landing-content">
    <div class="logo-mark">A</div>
    <h1>ASCE<b>ND</b>ANT</h1>
    <div class="tagline">Intelligence for Safer Communities</div>
    <div class="subtext">Data-driven disaster risk assessment and proactive relocation planning for Assam's flood-prone habitations.</div>
    <button class="enter-btn" onclick="enterApp()">ENTER SAFESETTLE →</button>
    <div style="margin-top:16px">
      <button id="install-btn" class="btn btn-outline" style="display:none;color:#fff;border-color:rgba(255,255,255,.3)" onclick="installApp()">📲 Install App on this device</button>
    </div>
    <div class="badges">
      <span class="badge-pill">🗺️ Live GIS Map</span>
      <span class="badge-pill">🚨 Real-time Alerts</span>
      <span class="badge-pill">📍 Relocation Planning</span>
    </div>
  </div>
</div>

<div id="app-view" class="app-shell">
  <aside class="sidebar">
    <div class="brand"><span class="dot" id="admin-gate" onclick="location.hash='#/details'" title="Authorized personnel only" style="cursor:pointer"></span><div><h1>SAFESETTLE</h1><span>Assam · by Ascendant</span></div></div>
    <nav id="nav-links"></nav>
    <div class="foot">Ascendant · Disaster Decision Support<br/>Prototype build</div>
  </aside>
  <main class="main">
    <div class="topbar">
      <div style="position:relative">
        <button class="icon-btn" onclick="toggleNotif()">🔔<span class="dotcount" id="notif-count">0</span></button>
        <div class="notif-dropdown" id="notif-dropdown">
          <div class="nd-head">Live Alerts (demo feed)</div>
          <div id="notif-list"></div>
        </div>
      </div>
      <a href="#/profile" class="profile-chip" id="profile-chip"><span class="av">?</span><span>Register / Profile</span></a>
    </div>
    <div class="main-content" id="content"></div>
  </main>
</div>
<div class="toast-stack" id="toast-stack"></div>

<script>
const NAV = [
  {hash:'#/dashboard', label:'Dashboard', icon:'📊'},
  {hash:'#/risk-map', label:'Risk Map', icon:'🗺️'},
  {hash:'#/habitations', label:'Habitations', icon:'🏘️'},
  {hash:'#/relocation-sites', label:'Relocation Sites', icon:'📍'},
  {hash:'#/food', label:'Food Availability', icon:'🍚'},
  {hash:'#/reports', label:'Reports', icon:'📄'},
  {hash:'#/alerts', label:'Alerts', icon:'🚨'},
  {hash:'#/survey-team', label:'Survey Team & Chat', icon:'💬'},
  {hash:'#/profile', label:'Profile', icon:'👤'},
];

/* ---------------- particle background (landing) ---------------- */
function initParticles(){
  const canvas = document.getElementById('particle-canvas');
  const ctx = canvas.getContext('2d');
  let w,h,particles=[];
  function resize(){ w=canvas.width=window.innerWidth; h=canvas.height=window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  const N = 70;
  for(let i=0;i<N;i++){
    particles.push({x:Math.random()*w, y:Math.random()*h, vx:(Math.random()-0.5)*0.4, vy:(Math.random()-0.5)*0.4, r:Math.random()*2+0.6});
  }
  function tick(){
    ctx.clearRect(0,0,w,h);
    particles.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>w) p.vx*=-1;
      if(p.y<0||p.y>h) p.vy*=-1;
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(99,140,246,0.65)';
      ctx.fill();
    });
    for(let i=0;i<N;i++){
      for(let j=i+1;j<N;j++){
        const dx=particles[i].x-particles[j].x, dy=particles[i].y-particles[j].y;
        const d=Math.sqrt(dx*dx+dy*dy);
        if(d<120){
          ctx.strokeStyle='rgba(99,140,246,'+(0.16*(1-d/120))+')';
          ctx.beginPath(); ctx.moveTo(particles[i].x,particles[i].y); ctx.lineTo(particles[j].x,particles[j].y); ctx.stroke();
        }
      }
    }
    requestAnimationFrame(tick);
  }
  tick();
}

function enterApp(){
  document.getElementById('landing-view').style.display='none';
  document.getElementById('app-view').style.display='flex';
  window.location.hash = '#/dashboard';
  startNotificationEngine();
  loadProfileChip();
}

function riskColor(level){
  if(level==='Very High') return '#dc2626';
  if(level==='High') return '#ea580c';
  if(level==='Moderate') return '#d97706';
  return '#16a34a';
}
function badgeClass(level){ return level.replace(' ','-'); }
async function getJSON(url){ const r = await fetch(url); return r.json(); }

function renderNav(activeHash){
  const nav = document.getElementById('nav-links');
  nav.innerHTML = NAV.map(n => `<a href="${n.hash}" class="${n.hash===activeHash?'active':''}">${n.icon} ${n.label}</a>`).join('');
}

function animateCount(el, target, suffix){
  let cur = 0; const step = Math.max(1, Math.round(target/40));
  const timer = setInterval(()=>{
    cur += step;
    if(cur >= target){ cur = target; clearInterval(timer); }
    el.textContent = cur.toLocaleString() + (suffix||'');
  }, 20);
}

/* ---------------- map helpers ---------------- */
let currentMap = null;
function freshMapContainer(id, height){
  return `<div class="map-box" style="height:${height||480}px"><div id="${id}" style="height:100%;width:100%"></div></div>`;
}
function buildMap(containerId, center, zoom){
  if(currentMap){ currentMap.remove(); currentMap = null; }
  const map = L.map(containerId).setView(center, zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  currentMap = map;
  return map;
}
function addHabitationMarkers(map, habitations, showZones, onClick){
  habitations.forEach(h => {
    const color = riskColor(h.risk_level);
    if(showZones){
      L.circle([h.lat,h.lng], {radius:2400, color, fillColor:color, fillOpacity:0.16, weight:1,
        className: (h.risk_level==='Very High'||h.risk_level==='High') ? 'zone-pulse' : ''}).addTo(map)
        .bindTooltip(h.district + ' — ' + h.risk_level + ' zone', {permanent:false});
    }
    let marker;
    if(h.risk_level === 'Very High'){
      const icon = L.divIcon({className:'', html:'<div class="pulse-dot"></div>', iconSize:[20,20]});
      marker = L.marker([h.lat,h.lng], {icon}).addTo(map);
    } else {
      marker = L.circleMarker([h.lat,h.lng], {radius:9, color:'#fff', fillColor:color, fillOpacity:1, weight:2}).addTo(map);
    }
    marker.bindTooltip(`${h.name} — ${h.risk_level} (${h.risk_score}/100)`);
    marker.bindPopup(`<b>${h.name}</b><br/>${h.district}, ${h.state}<br/>Population: ${h.population}<br/>Risk: ${h.risk_level} (${h.risk_score}/100)`);
    if(onClick) marker.on('click', () => onClick(h));
  });
}
function addSiteMarkers(map, sites){
  sites.forEach(s => {
    const m = L.circleMarker([s.lat,s.lng], {radius:8, color:'#fff', fillColor:'#2563eb', fillOpacity:1, weight:2}).addTo(map);
    m.bindTooltip(`${s.name} (Relocation Site)`);
    m.bindPopup(`<b>${s.name}</b><br/>Capacity: ${s.capacity||''}`);
  });
}
function showMyLocation(map){
  if(!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(pos => {
    L.marker([pos.coords.latitude, pos.coords.longitude]).addTo(map).bindPopup('Your current real GPS location').openPopup();
  });
}
async function drawRoute(map, from, to){
  const url = `https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;
  try{
    const data = await (await fetch(url)).json();
    const coords = data.routes[0].geometry.coordinates.map(c => [c[1],c[0]]);
    L.polyline(coords, {color:'#16a34a', weight:5, opacity:0.85}).addTo(map);
  }catch(e){
    L.polyline([from,to], {color:'#16a34a', weight:5, opacity:0.85}).addTo(map);
  }
}

/* ---------------- notifications (bell + toasts) ---------------- */
let notifStore = [];
function toggleNotif(){
  document.getElementById('notif-dropdown').classList.toggle('open');
}
function pushNotification(n){
  notifStore.unshift(n);
  if(notifStore.length>12) notifStore.pop();
  renderNotifDropdown();
  showToast(n);
}
function renderNotifDropdown(){
  document.getElementById('notif-count').textContent = notifStore.length;
  document.getElementById('notif-list').innerHTML = notifStore.map(n=>`
    <div class="nd-item"><b>${n.title}</b>${n.message}<div style="color:#98a2b3;font-size:11px;margin-top:2px">${n.time}</div></div>
  `).join('') || '<div class="nd-item">No alerts yet.</div>';
}
function showToast(n){
  const stack = document.getElementById('toast-stack');
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `<b>${n.title}</b>${n.message}`;
  stack.appendChild(el);
  setTimeout(()=>{ el.classList.add('fade-out'); setTimeout(()=>el.remove(), 400); }, 5000);
}
let notifEngineStarted = false;
function startNotificationEngine(){
  // Seed the bell dropdown once from real backend alerts. No repeating/simulated toasts —
  // the bell just reflects the current alert list; open it to see what's there.
  if(notifEngineStarted) return;
  notifEngineStarted = true;
  getJSON('/api/alerts').then(alerts=>{
    notifStore = alerts.map(a => ({title:a.type, message:a.title+': '+a.message, time:a.created_at}));
    renderNotifDropdown();
  });
}

/* ---------------- profile / registration ---------------- */
function loadProfileChip(){
  getJSON('/api/profile').then(p=>{
    if(p && p.name){
      document.getElementById('profile-chip').innerHTML =
        `<span class="av">${p.name.charAt(0).toUpperCase()}</span><span>${p.name}</span>`;
    }
  });
}

/* ================================================================ pages */

async function pageDashboard(){
  const [stats, habitations] = await Promise.all([getJSON('/api/dashboard/stats'), getJSON('/api/habitations')]);
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Dashboard</h2><p>Assam district-wide multi-hazard risk overview</p></div></div>
    <div class="disclaimer-banner">Sample / illustrative dataset for prototype demonstration — coordinates are placed near real Assam districts (Sivasagar, Charaideo, Jorhat, Golaghat, Kamrup Metro), but risk scores and population figures are not live GIS data.</div>
    <div class="stats-grid">
      <div class="stat-card total"><div class="label">Total Habitations</div><div class="value" id="c-total">0</div></div>
      <div class="stat-card vhigh"><div class="label">Very High Risk</div><div class="value" id="c-vhigh">0</div></div>
      <div class="stat-card high"><div class="label">High Risk</div><div class="value" id="c-high">0</div></div>
      <div class="stat-card moderate"><div class="label">Moderate Risk</div><div class="value" id="c-mod">0</div></div>
      <div class="stat-card low"><div class="label">Low Risk</div><div class="value" id="c-low">0</div></div>
    </div>
    <div class="grid-2">
      <div class="card">
        <h3 style="margin-top:0">Assam Flood Risk Map</h3>
        ${freshMapContainer('map-dash', 460)}
        <div class="legend">
          <span><span class="sw" style="background:#dc2626"></span>Very High Risk</span>
          <span><span class="sw" style="background:#ea580c"></span>High Risk</span>
          <span><span class="sw" style="background:#d97706"></span>Moderate Risk</span>
          <span><span class="sw" style="background:#16a34a"></span>Low Risk</span>
        </div>
      </div>
      <div class="card">
        <h3 style="margin-top:0">Risk Factors Considered</h3>
        ${['Flood','Landslide','Cyclone','Cloudburst','River Erosion','Other'].map(f=>`<div class="list-row"><span>${f}</span><span class="badge Moderate">Tracked</span></div>`).join('')}
        <h3>Top Priority Habitations</h3>
        ${habitations.slice().sort((a,b)=>b.risk_score-a.risk_score).slice(0,4).map(h=>`
          <div class="list-row" style="cursor:pointer" onclick="location.hash='#/habitations/${h.id}'">
            <span>${h.name} <small style="color:#667085">(${h.district})</small></span>
            <span class="badge ${badgeClass(h.risk_level)}">${h.risk_level}</span>
          </div>`).join('')}
      </div>
    </div>`;
  animateCount(document.getElementById('c-total'), stats.total);
  animateCount(document.getElementById('c-vhigh'), stats.levels['Very High']);
  animateCount(document.getElementById('c-high'), stats.levels['High']);
  animateCount(document.getElementById('c-mod'), stats.levels['Moderate']);
  animateCount(document.getElementById('c-low'), stats.levels['Low']);
  const map = buildMap('map-dash', [26.6,94.3], 8);
  addHabitationMarkers(map, habitations, true, h => location.hash = `#/habitations/${h.id}`);
}

async function pageRiskMap(params){
  const q = new URLSearchParams();
  if(params.risk_level) q.set('risk_level', params.risk_level);
  if(params.district) q.set('district', params.district);
  if(params.search) q.set('search', params.search);
  const habitations = await getJSON('/api/habitations?' + q.toString());
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Risk Map</h2><p>Interactive GIS-style hazard visualization — click a marker to open its profile</p></div></div>
    <div class="filters">
      <input id="f-search" placeholder="Search habitation..." value="${params.search||''}"/>
      <select id="f-risk">
        <option value="">All Risk Levels</option>
        ${['Very High','High','Moderate','Low'].map(l=>`<option ${params.risk_level===l?'selected':''}>${l}</option>`).join('')}
      </select>
      <select id="f-district">
        <option value="">All Districts</option>
        ${['Sivasagar','Charaideo','Jorhat','Golaghat','Kamrup Metro'].map(d=>`<option ${params.district===d?'selected':''}>${d}</option>`).join('')}
      </select>
      <button class="btn btn-outline" id="f-loc">📍 Show my real GPS location</button>
    </div>
    <div class="card">${freshMapContainer('map-risk', 560)}</div>`;
  const map = buildMap('map-risk', [26.6,94.3], 8);
  addHabitationMarkers(map, habitations, true, h => location.hash = `#/habitations/${h.id}`);
  const apply = () => {
    const rl = document.getElementById('f-risk').value;
    const dt = document.getElementById('f-district').value;
    const se = document.getElementById('f-search').value;
    location.hash = `#/risk-map?risk_level=${encodeURIComponent(rl)}&district=${encodeURIComponent(dt)}&search=${encodeURIComponent(se)}`;
  };
  document.getElementById('f-risk').onchange = apply;
  document.getElementById('f-district').onchange = apply;
  document.getElementById('f-search').onkeydown = e => { if(e.key==='Enter') apply(); };
  document.getElementById('f-loc').onclick = () => showMyLocation(map);
}

async function pageHabitations(params){
  const q = new URLSearchParams();
  if(params.risk_level) q.set('risk_level', params.risk_level);
  if(params.search) q.set('search', params.search);
  const habitations = await getJSON('/api/habitations?' + q.toString());
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Habitations</h2><p>All tracked habitations with current risk classification</p></div></div>
    <div class="filters">
      <input id="f-search" placeholder="Search by name..." value="${params.search||''}"/>
      <select id="f-risk"><option value="">All Risk Levels</option>
        ${['Very High','High','Moderate','Low'].map(l=>`<option ${params.risk_level===l?'selected':''}>${l}</option>`).join('')}
      </select>
    </div>
    <div class="card">
      ${habitations.map(h=>`
        <div class="list-row" style="cursor:pointer" onclick="location.hash='#/habitations/${h.id}'">
          <span><b>${h.name}</b> — ${h.district}, ${h.state} · Pop. ${h.population.toLocaleString()}</span>
          <span style="display:flex;gap:10px;align-items:center"><span>${h.risk_score}/100</span><span class="badge ${badgeClass(h.risk_level)}">${h.risk_level}</span></span>
        </div>`).join('') || '<p style="color:#667085">No habitations match these filters.</p>'}
    </div>`;
  const apply = () => {
    const rl = document.getElementById('f-risk').value;
    const se = document.getElementById('f-search').value;
    location.hash = `#/habitations?risk_level=${encodeURIComponent(rl)}&search=${encodeURIComponent(se)}`;
  };
  document.getElementById('f-risk').onchange = apply;
  document.getElementById('f-search').onkeydown = e => { if(e.key==='Enter') apply(); };
}

function bar(label, value, color){
  return `<div class="progress-row"><div class="top"><span>${label}</span><b>${value}/100</b></div>
  <div class="progress-track"><div class="progress-fill" style="width:0%;background:${color}" data-final="${value}"></div></div></div>`;
}

async function pageHabitationProfile(id){
  const h = await getJSON(`/api/habitations/${id}`);
  const vulnTotal = h.children + h.elderly + h.pwd;
  const vulnPct = Math.round((vulnTotal / h.population) * 100);
  document.getElementById('content').innerHTML = `
    <div class="page-header">
      <div><h2>${h.name}</h2><p>${h.district}, ${h.state}</p></div>
      <span class="badge ${badgeClass(h.risk_level)}" style="font-size:14px">${h.risk_level} RISK</span>
    </div>
    <div class="grid-2">
      <div class="card">
        <div style="display:flex;gap:30px;margin-bottom:18px">
          <div><div style="color:#667085;font-size:13px">Population</div><b style="font-size:20px">${h.population.toLocaleString()}</b></div>
          <div><div style="color:#667085;font-size:13px">Households</div><b style="font-size:20px">${h.households.toLocaleString()}</b></div>
          <div><div style="color:#667085;font-size:13px">Risk Score</div><b style="font-size:20px;color:${riskColor(h.risk_level)}">${h.risk_score}/100</b></div>
        </div>
        <h3>Risk Breakdown</h3>
        ${bar('Flood Risk', h.flood_risk, '#2563eb')}
        ${bar('Landslide Risk', h.landslide_risk, '#92400e')}
        ${bar('Cloudburst Risk', h.cloudburst_risk, '#0ea5e9')}
        ${bar('Cyclone Risk', h.cyclone_risk, '#7c3aed')}
        ${bar('Historical Events', h.historical_events, '#dc2626')}
        ${bar('Vulnerability Score', h.vulnerability_score, '#ea580c')}
        <div class="recommendation-box ${h.risk_level==='Low'?'good':''}">
          <b>RECOMMENDATION</b><p style="margin:6px 0 12px 0">${h.recommendation}</p>
          <button class="btn btn-primary" onclick="location.hash='#/habitations/${h.id}/sites'">Find Suitable Relocation Sites →</button>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:18px">
          <h3 style="margin-top:0">Vulnerable Population</h3>
          <div class="list-row"><span>Children</span><b>${h.children}</b></div>
          <div class="list-row"><span>Elderly</span><b>${h.elderly}</b></div>
          <div class="list-row"><span>Persons with Disabilities</span><b>${h.pwd}</b></div>
          <div class="list-row"><span>Low Income Households</span><b>${h.low_income_hh}</b></div>
          <div class="list-row"><span>Women Headed HH</span><b>${h.women_headed_hh}</b></div>
          <div style="margin-top:14px;padding:12px;background:#fef3c7;border-radius:10px;font-size:13px">
            <b>High Vulnerable Population:</b> ${vulnTotal.toLocaleString()} people (${vulnPct}%)</div>
        </div>
        <div class="card">
          <h3 style="margin-top:0">Why is this habitation vulnerable?</h3>
          <p style="font-size:13px;color:#667085;margin-top:-6px">Prototype scoring model — weighted composite</p>
          <div class="list-row"><span>Hazard Exposure</span><b>${h.hazard_exposure_pct}%</b></div>
          <div class="list-row"><span>Population Vulnerability</span><b>${h.population_vuln_pct}%</b></div>
          <div class="list-row"><span>Accessibility</span><b>${h.accessibility_pct}%</b></div>
          <div class="list-row"><span>Critical Infrastructure Exposure</span><b>${h.infra_exposure_pct}%</b></div>
          <div class="list-row"><span>Historical Disaster Impact</span><b>${h.historical_impact_pct}%</b></div>
        </div>
      </div>
    </div>`;
  requestAnimationFrame(()=>{
    document.querySelectorAll('.progress-fill').forEach(el=>{ el.style.width = el.dataset.final + '%'; });
  });
}

async function pageSiteComparison(id){
  const [h, sites] = await Promise.all([getJSON(`/api/habitations/${id}`), getJSON(`/api/habitations/${id}/sites`)]);
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Relocation Site Comparison</h2><p>For ${h.name} — People to relocate: <b>${h.population.toLocaleString()}</b></p></div></div>
    <div class="card" style="margin-bottom:18px">${freshMapContainer('map-sites', 340)}</div>
    <div class="site-grid">
      ${sites.map(s=>`
        <div class="site-card ${s.recommended?'recommended':''}">
          ${s.recommended?'<span class="tag">RECOMMENDED</span>':''}
          <h3 style="margin-top:0">${s.name}</h3>
          <div class="list-row"><span>Suitability Score</span><b>${s.suitability_score}/100</b></div>
          <div class="list-row"><span>Safety Score</span><b>${s.safety_score}</b></div>
          <div class="list-row"><span>Distance</span><b>${s.distance_km} km</b></div>
          <div class="list-row"><span>Capacity</span><b>${s.capacity.toLocaleString()}</b></div>
          <div class="list-row"><span>Road Accessibility</span><b>${s.road_access}</b></div>
          <div class="list-row"><span>Hospital</span><b>${s.hospital_km} km</b></div>
          <div class="list-row"><span>Water</span><b>${s.water_availability}</b></div>
          <div class="list-row"><span>Schools</span><b>${s.school_capacity}</b></div>
          <div class="list-row"><span>Hazard Exposure</span><b>${s.hazard_exposure}</b></div>
          <div style="display:flex;gap:8px;margin-top:14px">
            <button class="btn btn-outline" onclick='routeToSite(${h.lat},${h.lng},${s.lat},${s.lng})'>Show Safest Route</button>
            ${s.recommended?`<button class="btn btn-primary" onclick="location.hash='#/habitations/${h.id}/plan'">Generate Plan →</button>`:''}
          </div>
        </div>`).join('')}
    </div>`;
  const map = buildMap('map-sites', [h.lat,h.lng], 9);
  addHabitationMarkers(map, [h], false, null);
  addSiteMarkers(map, sites);
  window.routeToSite = (hlat,hlng,slat,slng) => drawRoute(map, [hlat,hlng], [slat,slng]);
}

async function pageRelocationPlan(id){
  const plan = await getJSON(`/api/relocation-plan/${id}`);
  const {habitation, site, phases, supporting_actions} = plan;
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Recommended Plan for ${habitation.name}</h2><p>Prioritized, phased relocation strategy</p></div></div>
    <div class="stats-grid" style="grid-template-columns:repeat(4,1fr)">
      <div class="stat-card total"><div class="label">Preferred Site</div><div class="value" style="font-size:16px">${site.name}</div></div>
      <div class="stat-card low"><div class="label">Capacity</div><div class="value">${site.capacity.toLocaleString()}</div></div>
      <div class="stat-card moderate"><div class="label">Distance</div><div class="value">${site.distance_km} km</div></div>
      <div class="stat-card high"><div class="label">Suitability</div><div class="value">${site.suitability_score}/100</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h3 style="margin-top:0">Relocation Phases</h3>
        ${phases.map(p=>`<div class="phase-card"><b>${p.phase.toUpperCase()}</b>
          <div style="display:flex;justify-content:space-between;margin-top:6px"><span>${p.label}</span><b>${p.count.toLocaleString()} people (${p.pct}%)</b></div></div>`).join('')}
      </div>
      <div class="card"><h3 style="margin-top:0">Supporting Actions</h3>
        ${supporting_actions.map(a=>`<div class="list-row"><span>✓ ${a}</span></div>`).join('')}
        <div style="display:flex;gap:10px;margin-top:18px">
          <button class="btn btn-primary" id="plan-pdf">Download Plan (PDF)</button>
          <button class="btn btn-outline" onclick="alert('Shared with authorities (prototype action)')">Share with Authorities</button>
        </div>
      </div>
    </div>`;
  document.getElementById('plan-pdf').onclick = () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    let y = 18;
    const line = (txt, size, bold) => {
      doc.setFontSize(size || 11);
      doc.setFont(undefined, bold ? 'bold' : 'normal');
      const wrapped = doc.splitTextToSize(txt, 175);
      doc.text(wrapped, 15, y);
      y += 7 * wrapped.length;
    };
    line(`Recommended Plan for ${habitation.name}`, 15, true); y += 2;
    line(`Preferred Site: ${site.name}    Capacity: ${site.capacity}    Distance: ${site.distance_km} km    Suitability: ${site.suitability_score}/100`); y += 3;
    line('Relocation Phases', 12, true);
    phases.forEach(p => line(`${p.phase}: ${p.label} — ${p.count.toLocaleString()} people (${p.pct}%)`));
    y += 3;
    line('Supporting Actions', 12, true);
    supporting_actions.forEach(a => line('- ' + a));
    doc.save(`${habitation.name.replace(/\s+/g,'_')}_relocation_plan.pdf`);
  };
}

async function pageRelocationSites(){
  const allSites = await getJSON('/api/report/1'); // habitation 1's comparison covers all 3 sites
  const sites = allSites.sites;
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Relocation Sites</h2><p>Elevated, safer ground identified across Assam districts</p></div></div>
    <div class="card" style="margin-bottom:18px">${freshMapContainer('map-relsites', 420)}</div>
    <div class="site-grid">
      ${sites.map(s=>`
        <div class="site-card">
          <h3 style="margin-top:0">${s.name}</h3>
          <div class="list-row"><span>Safety Score</span><b>${s.safety_score}</b></div>
          <div class="list-row"><span>Capacity</span><b>${s.capacity.toLocaleString()}</b></div>
          <div class="list-row"><span>Road Accessibility</span><b>${s.road_access}</b></div>
          <div class="list-row"><span>Hospital</span><b>${s.hospital_km} km</b></div>
          <div class="list-row"><span>Water</span><b>${s.water_availability}</b></div>
          <div class="list-row"><span>Schools</span><b>${s.school_capacity}</b></div>
          <div class="list-row"><span>Hazard Exposure</span><b>${s.hazard_exposure}</b></div>
        </div>`).join('')}
    </div>`;
  const map = buildMap('map-relsites', [26.7,94.2], 8);
  addSiteMarkers(map, sites);
}

async function pageFood(){
  const items = await getJSON('/api/food-inventory');
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Food & Supply Availability</h2><p>Central relief store — exact stock and per-person daily requirement</p></div></div>
    <div class="grid-2">
      <div class="card">
        <h3 style="margin-top:0">Current Stock</h3>
        ${items.map(f=>`<div class="list-row"><span>${f.item}</span><b>${f.stock} ${f.unit}</b></div>`).join('')}
      </div>
      <div class="card">
        <h3 style="margin-top:0">Daily Requirement / Person</h3>
        ${items.map(f=>`<div class="list-row"><span>${f.item}</span><b>${f.per_person_daily} ${f.per_person_unit}</b></div>`).join('')}
      </div>
    </div>
    <div class="card" style="margin-top:18px">
      <h3 style="margin-top:0">How many people can this feed?</h3>
      <div class="filters" style="margin-bottom:0">
        <input type="number" id="pop-input" placeholder="Number of people to relocate" style="width:240px"/>
        <button class="btn btn-primary" id="calc-btn">Calculate</button>
      </div>
      <div id="calc-result"></div>
    </div>`;

  const norm = {}; // convert everything to grams/ml for a clean per-person-day comparison
  items.forEach(f=>{
    let stockG = f.stock;
    if(f.unit==='kg') stockG = f.stock*1000;
    if(f.unit==='litres') stockG = f.stock*1000;
    norm[f.item] = {stockG, perDay:f.per_person_daily, unit:f.per_person_unit};
  });

  document.getElementById('calc-btn').onclick = () => {
    const pop = parseInt(document.getElementById('pop-input').value);
    if(!pop || pop<=0){ document.getElementById('calc-result').innerHTML = '<p style="color:#dc2626">Enter a valid number of people.</p>'; return; }
    let minDays = Infinity, limiting = '';
    const rows = items.map(f=>{
      let stockUnits = f.unit==='kg' ? f.stock*1000 : (f.unit==='litres' ? f.stock*1000 : f.stock);
      const days = stockUnits / (f.per_person_daily * pop);
      if(days < minDays){ minDays = days; limiting = f.item; }
      return `<div class="list-row"><span>${f.item}</span><b>${days.toFixed(1)} days</b></div>`;
    }).join('');
    document.getElementById('calc-result').innerHTML = `
      <div class="food-calc-result">
        <b>For ${pop.toLocaleString()} people, current stock lasts ≈ ${minDays.toFixed(1)} days</b>
        (limited by <b>${limiting}</b> running out first).
        <div style="margin-top:10px">${rows}</div>
        <p style="font-size:12px;color:#667085;margin-top:10px">Fresh vegetables also get a daily transport top-up of 20 kg/day, which alone supports up to 100 additional people/day (20,000g ÷ 200g) on an ongoing basis.</p>
      </div>`;
  };
}

async function pageReports(){
  const habitations = await getJSON('/api/habitations');
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Reports</h2><p>Generate a full risk & relocation report for a habitation</p></div></div>
    <div class="card" style="margin-bottom:18px">
      <div class="filters" style="margin-bottom:0">
        <select id="rep-select"><option value="">Select a habitation...</option>
          ${habitations.map(h=>`<option value="${h.id}">${h.name} — ${h.district}</option>`).join('')}
        </select>
        <button class="btn btn-primary" id="rep-gen">Generate Report</button>
        <button class="btn btn-outline" id="rep-pdf" style="display:none">Download PDF</button>
      </div>
    </div>
    <div id="report-area"></div>`;
  document.getElementById('rep-gen').onclick = async () => {
    const id = document.getElementById('rep-select').value;
    if(!id) return;
    const r = await getJSON(`/api/report/${id}`);
    const h = r.habitation;
    const siteLines = r.sites.map(s=>`${s.name}: suitability ${s.suitability_score}/100, distance ${s.distance_km} km, capacity ${s.capacity}${s.recommended?' — RECOMMENDED':''}`);

    document.getElementById('report-area').innerHTML = `
      <div class="card">
        <h3 style="margin-top:0">${h.name} — Full Risk & Relocation Report</h3>
        <p><b>District:</b> ${h.district}, ${h.state}</p>
        <p><b>Risk Score:</b> ${h.risk_score}/100 (${h.risk_level})</p>
        <h4>Risk Breakdown</h4>
        <p>Flood ${h.flood_risk} · Landslide ${h.landslide_risk} · Cloudburst ${h.cloudburst_risk} · Cyclone ${h.cyclone_risk} · Historical ${h.historical_events}</p>
        <h4>Vulnerability</h4>
        <p>Children ${h.children} · Elderly ${h.elderly} · PWD ${h.pwd} · Low income HH ${h.low_income_hh} · Women-headed HH ${h.women_headed_hh}</p>
        <h4>Population Affected</h4>
        <p>${h.population.toLocaleString()} people across ${h.households.toLocaleString()} households</p>
        <h4>Site Comparison</h4>
        ${siteLines.map(l=>`<p>${l}</p>`).join('')}
        <h4>Recommendation</h4>
        <p>${h.recommendation}</p>
      </div>`;
    document.getElementById('rep-pdf').style.display = 'inline-block';
    document.getElementById('rep-pdf').onclick = () => {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      let y = 18;
      const line = (txt, size, bold) => {
        doc.setFontSize(size || 11);
        doc.setFont(undefined, bold ? 'bold' : 'normal');
        const wrapped = doc.splitTextToSize(txt, 175);
        doc.text(wrapped, 15, y);
        y += 7 * wrapped.length;
      };
      line(`${h.name} — Full Risk & Relocation Report`, 15, true); y += 2;
      line(`District: ${h.district}, ${h.state}`);
      line(`Risk Score: ${h.risk_score}/100 (${h.risk_level})`); y += 3;
      line('Risk Breakdown', 12, true);
      line(`Flood ${h.flood_risk} · Landslide ${h.landslide_risk} · Cloudburst ${h.cloudburst_risk} · Cyclone ${h.cyclone_risk} · Historical ${h.historical_events}`); y += 3;
      line('Vulnerability', 12, true);
      line(`Children ${h.children} · Elderly ${h.elderly} · PWD ${h.pwd} · Low income HH ${h.low_income_hh} · Women-headed HH ${h.women_headed_hh}`); y += 3;
      line('Population Affected', 12, true);
      line(`${h.population.toLocaleString()} people across ${h.households.toLocaleString()} households`); y += 3;
      line('Site Comparison', 12, true);
      siteLines.forEach(l => line(l));
      y += 3;
      line('Recommendation', 12, true);
      line(h.recommendation);
      doc.save(`${h.name.replace(/\s+/g,'_')}_report.pdf`);
    };
  };
}

async function pageAlerts(){
  const alerts = await getJSON('/api/alerts');
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Alerts</h2><p>Live-style hazard and relocation alerts (sample feed)</p></div></div>
    <div class="card">
      ${alerts.map(a=>`
        <div class="alert-item ${a.severity}">
          <div style="font-size:20px">${a.type.includes('WEATHER')?'⛈️':a.type.includes('RELOCATION')?'📍':a.type.includes('RESOURCE')?'🍚':'⚠️'}</div>
          <div><b>${a.type}</b> · ${a.title}<p style="margin:4px 0 0 0;color:#667085;font-size:13px">${a.message}</p>
          <span style="font-size:11px;color:#98a2b3">${a.created_at}</span></div>
        </div>`).join('')}
    </div>`;
}

function copyPhone(phone){
  const clean = phone.split('/')[0].trim();
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(clean).then(()=> showToast({title:'📞 Number copied', message: clean}));
  } else {
    showToast({title:'📞 Call this number', message: clean});
  }
}
let chatActive = null;
async function pageSurveyTeam(){
  const team = await getJSON('/api/survey-team');
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Survey Team & Chat</h2><p>Real Assam flood-helpline & relief-organization contacts</p></div></div>
    <div class="disclaimer-banner">These numbers are copied from the Assam State Disaster Management Authority public notice and relief-NGO list you provided. Verify they are still active before presenting this as a live system — helpline rosters change.</div>
    <div class="grid-2">
      <div id="team-list">
        ${team.map(t=>`
          <div class="team-card">
            <div><b>${t.name}</b><br/><span style="font-size:13px;color:#667085">${t.role} · ${t.area}</span><br/><span style="font-size:13px">📞 ${t.phone}</span><br/><span style="font-size:11px;color:#98a2b3">Source: ${t.source}</span></div>
            <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end">
              <span class="badge ${t.status==='Available'?'Low':'Moderate'}">${t.status}</span>
              <div style="display:flex;gap:6px">
                <button class="btn btn-outline" onclick='copyPhone(${JSON.stringify(t.phone)})' title="Copy number">📞 Call</button>
                <button class="btn btn-outline" onclick='openChat(${t.id}, ${JSON.stringify(t.name)})'>💬 Chat</button>
              </div>
            </div>
          </div>`).join('')}
      </div>
      <div class="card">
        <h3 id="chat-title" style="margin-top:0">Select a contact to chat</h3>
        <div class="chat-box">
          <div class="chat-messages" id="chat-messages"><p style="color:#98a2b3;font-size:13px">No conversation selected. This is a UI demo — messages are not actually sent to the number.</p></div>
          <div class="chat-input">
            <input id="chat-input" placeholder="Select a contact first" disabled onkeydown="if(event.key==='Enter') sendChat()"/>
            <button onclick="sendChat()" disabled id="chat-send">Send</button>
          </div>
        </div>
      </div>
    </div>`;
}
function openChat(id, name){
  chatActive = name;
  document.getElementById('chat-title').innerText = 'Chat with ' + name;
  document.getElementById('chat-messages').innerHTML = '';
  document.getElementById('chat-input').disabled = false;
  document.getElementById('chat-input').placeholder = 'Type a message...';
  document.getElementById('chat-send').disabled = false;
}
function sendChat(){
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if(!text || !chatActive) return;
  const box = document.getElementById('chat-messages');
  box.innerHTML += `<div class="chat-bubble me">${text}</div>`;
  input.value = '';
  box.scrollTop = box.scrollHeight;
  setTimeout(()=>{
    box.innerHTML += `<div class="chat-bubble them">(${chatActive}) Received — dispatching team to your location. [demo reply]</div>`;
    box.scrollTop = box.scrollHeight;
  }, 700);
}

async function pageProfile(){
  const p = await getJSON('/api/profile');
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Profile / Registration</h2><p>Register your name, mobile number and email so relief teams can reach you</p></div></div>
    <div class="card">
      <div class="form-grid">
        <div><label>Full Name *</label><input id="p-name" value="${p.name||''}" placeholder="e.g. Palak Vij"/></div>
        <div><label>Mobile Number *</label><input id="p-mobile" value="${p.mobile||''}" placeholder="e.g. 98765xxxxx"/></div>
        <div><label>Email ID (optional)</label><input id="p-email" value="${p.email||''}" placeholder="e.g. name@example.com"/></div>
        <button class="btn btn-primary" id="p-save" style="width:160px">Save Profile</button>
        <p id="p-msg" style="color:#16a34a;font-size:13px;display:none">Saved!</p>
      </div>
      <p style="font-size:12px;color:#667085;margin-top:16px">* Required. Once Name and Mobile are both filled in, your profile saves itself automatically — Email is optional. Stored locally in this app's own SQLite database on your machine.</p>
    </div>`;

  const nameEl = document.getElementById('p-name');
  const mobileEl = document.getElementById('p-mobile');
  const emailEl = document.getElementById('p-email');

  async function saveProfile(silent){
    const body = { name: nameEl.value.trim(), mobile: mobileEl.value.trim(), email: emailEl.value.trim() };
    if(!body.name || !body.mobile) return;
    await fetch('/api/profile', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    document.getElementById('p-msg').style.display = 'block';
    loadProfileChip();
    if(!silent) showToast({title:'Profile saved', message: body.name + ' · ' + body.mobile});
  }

  document.getElementById('p-save').onclick = () => saveProfile(false);
  [nameEl, mobileEl].forEach(el => el.addEventListener('blur', () => saveProfile(true)));
}

function pageDetails(){
  document.getElementById('content').innerHTML = `
    <div class="page-header"><div><h2>Details</h2><p>Restricted — visible only to the owner / authorized administrators</p></div></div>
    <div class="disclaimer-banner">This page is intentionally not in the main navigation. Only someone who knows to click the small logo dot in the sidebar reaches it.</div>
    <div class="card">
      <div class="list-row"><span>Data source</span><b>Local SQLite (sample data)</b></div>
      <div class="list-row"><span>Map provider</span><b>OpenStreetMap (Leaflet)</b></div>
      <div class="list-row"><span>Routing engine</span><b>OSRM public demo server</b></div>
      <div class="list-row"><span>Future integration</span><b>QGIS / GeoPandas / PostGIS ready</b></div>
      <p style="font-size:13px;color:#667085;margin-top:14px">To connect a real GIS backend later: replace the SQLite queries in this file's API routes with PostGIS queries. The frontend calls the same REST endpoints, so it does not need to change.</p>
    </div>`;
}

/* ------------------------------------------------------------ router --*/

function parseHash(){
  const raw = location.hash.replace(/^#/, '') || '/dashboard';
  const [path, qs] = raw.split('?');
  const parts = path.split('/').filter(Boolean);
  const params = Object.fromEntries(new URLSearchParams(qs || ''));
  return {parts, params};
}

async function router(){
  const {parts, params} = parseHash();
  const activeTop = '#/' + (parts[0] || 'dashboard');
  renderNav(activeTop);
  const content = document.getElementById('content');
  content.classList.remove('main-content'); void content.offsetWidth; content.classList.add('main-content');

  if(parts[0] === 'dashboard' || parts.length === 0) return pageDashboard();
  if(parts[0] === 'risk-map') return pageRiskMap(params);
  if(parts[0] === 'habitations' && parts.length === 1) return pageHabitations(params);
  if(parts[0] === 'habitations' && parts.length === 2) return pageHabitationProfile(parts[1]);
  if(parts[0] === 'habitations' && parts.length === 3 && parts[2] === 'sites') return pageSiteComparison(parts[1]);
  if(parts[0] === 'habitations' && parts.length === 3 && parts[2] === 'plan') return pageRelocationPlan(parts[1]);
  if(parts[0] === 'relocation-sites') return pageRelocationSites();
  if(parts[0] === 'food') return pageFood();
  if(parts[0] === 'reports') return pageReports();
  if(parts[0] === 'alerts') return pageAlerts();
  if(parts[0] === 'survey-team') return pageSurveyTeam();
  if(parts[0] === 'profile') return pageProfile();
  if(parts[0] === 'details') return pageDetails();
  return pageDashboard();
}

if('serviceWorker' in navigator){
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}
let deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  const btn = document.getElementById('install-btn');
  if(btn) btn.style.display = 'inline-block';
});
function installApp(){
  if(!deferredInstallPrompt) return;
  deferredInstallPrompt.prompt();
  deferredInstallPrompt = null;
  const btn = document.getElementById('install-btn');
  if(btn) btn.style.display = 'none';
}

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', () => {
  initParticles();
  document.addEventListener('click', (e)=>{
    if(!e.target.closest('.icon-btn') && !e.target.closest('.notif-dropdown')){
      document.getElementById('notif-dropdown').classList.remove('open');
    }
  });
  if(location.hash && location.hash !== '#/'){
    document.getElementById('landing-view').style.display = 'none';
    document.getElementById('app-view').style.display = 'flex';
    startNotificationEngine();
    loadProfileChip();
    router();
  }
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return PAGE


if __name__ == "__main__":
    seed_data()
    print("Database seeded with sample data at", DB_PATH)
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    app.run()