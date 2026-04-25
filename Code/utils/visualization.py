from textwrap import dedent

import folium
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium


def apply_custom_css():
    """Apply a restrained command-center visual system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Rajdhani:wght@500;600;700&display=swap');

        :root {
            --bg: #060816;
            --surface: #0b1220;
            --surface-2: #0f1728;
            --line: rgba(90, 129, 173, 0.24);
            --line-strong: rgba(83, 224, 255, 0.35);
            --text: #e8f3ff;
            --muted: #8ca0b8;
            --cyan: #53e0ff;
            --cyan-soft: rgba(83, 224, 255, 0.14);
            --green: #24d58a;
            --amber: #ffbe55;
            --red: #ff5d73;
            --shadow: 0 22px 60px rgba(0, 0, 0, 0.42);
        }

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 0%, rgba(83, 224, 255, 0.08), transparent 28%),
                radial-gradient(circle at 100% 0%, rgba(36, 213, 138, 0.07), transparent 22%),
                linear-gradient(180deg, #050814 0%, #070c18 52%, #050713 100%);
            color: var(--text);
        }

        header, footer, #MainMenu, .stDeployButton {
            visibility: hidden;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.1rem;
            padding-bottom: 2.4rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(10, 14, 26, 0.98), rgba(8, 11, 20, 0.96));
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
        }

        h1, h2, h3, h4 {
            font-family: 'Rajdhani', sans-serif !important;
            color: var(--text) !important;
            letter-spacing: 0.04em;
            font-weight: 700 !important;
            margin: 0;
        }

        .top-shell {
            display: grid;
            grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
            gap: 18px;
            margin-bottom: 18px;
        }

        .hero-panel,
        .hero-side,
        .status-card,
        .signal-card,
        .telemetry-card,
        .vision-card,
        .feed-card,
        .standby-shell {
            background: linear-gradient(180deg, rgba(11, 18, 32, 0.92), rgba(8, 13, 24, 0.9));
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: var(--shadow);
        }

        .hero-panel {
            padding: 26px 28px;
            min-height: 168px;
            position: relative;
            overflow: hidden;
        }

        .hero-panel::after {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(130deg, rgba(83, 224, 255, 0.13), transparent 34%),
                linear-gradient(180deg, transparent 0%, rgba(83, 224, 255, 0.03) 100%);
            pointer-events: none;
        }

        .eyebrow {
            font-family: 'Rajdhani', sans-serif;
            color: var(--cyan);
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            margin-bottom: 10px;
        }

        .hero-title {
            font-size: clamp(2rem, 2.8vw, 3.2rem);
            line-height: 0.95;
            margin-bottom: 14px;
        }

        .hero-subtitle {
            max-width: 52ch;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.6;
            margin-bottom: 18px;
        }

        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .tag-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(255,255,255,0.03);
            color: var(--text);
            font-size: 0.85rem;
            white-space: nowrap;
        }

        .tag-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--green);
            box-shadow: 0 0 10px rgba(36, 213, 138, 0.5);
        }

        .hero-side {
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .side-stat-label,
        .section-label,
        .subtle-label {
            color: var(--muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
        }

        .side-stat-value {
            font-family: 'Rajdhani', sans-serif;
            font-size: 2rem;
            color: var(--cyan);
            font-weight: 700;
        }

        .metrics-band {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 0 0 20px 0;
        }

        .metric-tile {
            padding: 18px 18px 16px;
            background: linear-gradient(180deg, rgba(13, 21, 36, 0.92), rgba(10, 16, 28, 0.9));
            border: 1px solid var(--line);
            border-radius: 8px;
            min-height: 112px;
        }

        .metric-value {
            font-family: 'Rajdhani', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
            margin-top: 10px;
        }

        .metric-trend {
            margin-top: 8px;
            color: var(--muted);
            font-size: 0.84rem;
        }

        .status-card, .signal-card, .telemetry-card, .vision-card, .feed-card {
            padding: 18px;
        }

        .section-head {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }

        .section-title {
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.45rem;
            color: var(--text);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .section-note {
            color: var(--muted);
            font-size: 0.82rem;
        }

        .status-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 16px 18px;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.025);
            margin-bottom: 16px;
        }

        .status-banner.live {
            border-color: rgba(36, 213, 138, 0.35);
            background: linear-gradient(90deg, rgba(36, 213, 138, 0.14), rgba(83, 224, 255, 0.06));
        }

        .status-banner.warn {
            border-color: rgba(255, 190, 85, 0.35);
            background: linear-gradient(90deg, rgba(255, 190, 85, 0.13), rgba(255,255,255,0.03));
        }

        .status-title {
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.2rem;
            color: var(--text);
        }

        .status-caption {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 4px;
        }

        .countdown-chip {
            min-width: 86px;
            text-align: center;
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: rgba(7, 12, 21, 0.85);
        }

        .countdown-chip strong {
            display: block;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.5rem;
            color: var(--text);
            line-height: 1;
        }

        .sensor-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }

        .sensor-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 12px;
            align-items: center;
            padding: 14px 16px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.025);
        }

        .sensor-name {
            font-family: 'Rajdhani', sans-serif;
            color: var(--text);
            font-size: 1rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .sensor-detail {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 3px;
        }

        .sensor-badge {
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .sensor-badge.live {
            color: #bbffe2;
            background: rgba(36, 213, 138, 0.14);
            border-color: rgba(36, 213, 138, 0.28);
        }

        .sensor-badge.idle {
            color: #c8d6e8;
            background: rgba(140, 160, 184, 0.12);
            border-color: rgba(140, 160, 184, 0.22);
        }

        .sensor-badge.warn {
            color: #ffe0a8;
            background: rgba(255, 190, 85, 0.13);
            border-color: rgba(255, 190, 85, 0.22);
        }

        .route-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 14px 0 0;
        }

        .route-stop {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px;
            background: rgba(255,255,255,0.02);
        }

        .route-stop.active {
            border-color: rgba(83, 224, 255, 0.36);
            background: linear-gradient(180deg, rgba(83, 224, 255, 0.12), rgba(255,255,255,0.03));
        }

        .route-id {
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.95rem;
            color: var(--text);
            margin-bottom: 4px;
        }

        .route-name {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }

        .map-frame {
            overflow: hidden;
            border-radius: 8px;
            border: 1px solid var(--line);
        }

        .vision-shell {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: #04070f;
        }

        .vision-overlay {
            position: absolute;
            inset: 0;
            background:
                repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0px, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 4px),
                linear-gradient(180deg, rgba(5, 8, 16, 0.08), rgba(5, 8, 16, 0.38));
            pointer-events: none;
            z-index: 3;
        }

        .vision-tag {
            position: absolute;
            top: 12px;
            right: 12px;
            z-index: 4;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(7, 12, 20, 0.84);
            border: 1px solid rgba(255, 190, 85, 0.35);
            color: var(--amber);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .feed-empty {
            min-height: 360px;
            border-radius: 8px;
            border: 1px dashed rgba(83, 224, 255, 0.22);
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                linear-gradient(180deg, rgba(9, 13, 24, 0.98), rgba(7, 10, 19, 0.95));
        }

        .feed-empty-inner {
            text-align: center;
        }

        .feed-empty-title {
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.6rem;
            color: var(--text);
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }

        .feed-empty-copy {
            color: var(--muted);
            font-size: 0.92rem;
        }

        .audio-shell {
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid var(--line);
        }

        .standby-shell {
            padding: 52px;
            text-align: center;
            margin-top: 24px;
        }

        .standby-title {
            font-family: 'Rajdhani', sans-serif;
            font-size: clamp(2.8rem, 5vw, 5rem);
            color: var(--text);
            letter-spacing: 0.05em;
            margin-bottom: 14px;
        }

        .standby-copy {
            color: var(--muted);
            font-size: 1rem;
            max-width: 48ch;
            margin: 0 auto;
            line-height: 1.7;
        }

        .stButton > button {
            border-radius: 8px;
            min-height: 48px;
            border: 1px solid var(--line-strong);
            background: linear-gradient(180deg, rgba(83, 224, 255, 0.12), rgba(83, 224, 255, 0.06));
            color: var(--text);
            font-family: 'Rajdhani', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(83, 224, 255, 0.7);
            box-shadow: 0 10px 26px rgba(83, 224, 255, 0.12);
        }

        .stButton > button:focus {
            box-shadow: 0 0 0 1px rgba(83, 224, 255, 0.3);
        }

        .stAudio audio {
            width: 100%;
        }

        [data-testid="stMetric"] {
            background: transparent;
            border: 0;
            padding: 0;
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.76rem !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--text) !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 2rem !important;
            line-height: 1.1;
        }

        @media (max-width: 1200px) {
            .top-shell,
            .metrics-band,
            .route-strip {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 900px) {
            .top-shell,
            .metrics-band,
            .route-strip {
                grid-template-columns: 1fr;
            }

            .hero-panel,
            .hero-side,
            .standby-shell {
                padding: 20px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_banner(current_time, emergency_type, is_preempted):
    mode = "Preemption live" if is_preempted else "Monitoring all lanes"
    vehicle = emergency_type if emergency_type else "No emergency dispatch"
    st.markdown(
        dedent(
            f"""
            <div class="top-shell">
                <div class="hero-panel">
                    <div class="eyebrow">Urban Mobility Command</div>
                    <div class="hero-title">OMNISENSE</div>
                    <div class="hero-subtitle">
                        Coordinate emergency vehicle priority, live signal control, and route assurance from one tactical surface.
                    </div>
                    <div class="tag-row">
                        <div class="tag-pill"><span class="tag-dot"></span>{mode}</div>
                        <div class="tag-pill">Dispatch: {vehicle}</div>
                        <div class="tag-pill">Corridor: Alpha-7</div>
                    </div>
                </div>
                <div class="hero-side">
                    <div>
                        <div class="side-stat-label">System clock</div>
                        <div class="side-stat-value">{current_time}</div>
                    </div>
                    <div>
                        <div class="side-stat-label">Network status</div>
                        <div class="tag-pill" style="width: fit-content; margin-top: 6px;">
                            <span class="tag-dot"></span>All modules online
                        </div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_metric_tiles(metrics, countdown, active_sector, is_preempted):
    tiles = [
        ("ETA reduction", f"+{metrics['eta_reduction']:.1f}%", "Priority corridor gain"),
        ("Detection accuracy", f"{metrics['detection_accuracy']:.2f}%", "Cross-sensor agreement"),
        ("Node latency", f"{metrics['latency_ms']:.0f} ms", "Signal response window"),
        (
            "Countdown" if not is_preempted else "Clearance",
            f"{countdown}s" if not is_preempted else "Live",
            f"Active sector {active_sector}",
        ),
    ]
    markup = "".join(
        (
            f'<div class="metric-tile">'
            f'<div class="section-label">{label}</div>'
            f'<div class="metric-value">{value}</div>'
            f'<div class="metric-trend">{caption}</div>'
            f"</div>"
        )
        for label, value, caption in tiles
    )
    st.markdown(f'<div class="metrics-band">{markup}</div>', unsafe_allow_html=True)


def render_section_heading(title, note):
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-title">{title}</div>
            <div class="section-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(signal_state, countdown, is_preempted):
    mode_class = "live" if is_preempted else ("warn" if signal_state == "YELLOW" else "")
    headline = "Preemption lock engaged" if is_preempted else "Standard flow routine"
    caption = (
        "Emergency vehicle path is being held open across the active corridor."
        if is_preempted
        else "Monitoring for RFID, acoustic, and visual confirmation before signal override."
    )
    countdown_label = "Live" if is_preempted else f"{countdown}s"
    st.markdown(
        dedent(
            f"""
            <div class="status-banner {mode_class}">
                <div>
                    <div class="status-title">{headline}</div>
                    <div class="status-caption">{caption}</div>
                </div>
                <div class="countdown-chip">
                    <span class="subtle-label">Window</span>
                    <strong>{countdown_label}</strong>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_sensor_matrix(rfid, acoustic, vision):
    rows = [
        (
            "RFID handshake",
            rfid["vehicle_id"],
            "Verified" if rfid["authenticated"] else "Awaiting auth",
            "live" if rfid["authenticated"] else "idle",
        ),
        (
            "Acoustic model",
            f"{acoustic['label']} • {acoustic['decibel']:.0f} dB",
            f"{acoustic['confidence'] * 100:.1f}% confidence",
            "live" if acoustic["siren_detected"] else "warn",
        ),
        (
            "Vision model",
            f"{vision['label']} • {vision['distance_m']:.0f} m",
            f"{vision['confidence'] * 100:.1f}% confidence",
            "live" if vision["detected"] else "idle",
        ),
    ]
    markup = "".join(
        (
            f'<div class="sensor-row">'
            f"<div>"
            f'<div class="sensor-name">{name}</div>'
            f'<div class="sensor-detail">{detail}</div>'
            f"</div>"
            f'<div class="sensor-badge {badge_class}">{badge}</div>'
            f"</div>"
        )
        for name, detail, badge, badge_class in rows
    )
    st.markdown(f'<div class="sensor-grid">{markup}</div>', unsafe_allow_html=True)


def traffic_signal_ui(state="RED"):
    """Display a framed traffic light stack with active lamp emphasis."""
    lamp_styles = {
        "RED": ("#ff5d73", "0 0 18px rgba(255, 93, 115, 0.8)", "rgba(255, 93, 115, 0.15)"),
        "YELLOW": ("#ffbe55", "0 0 18px rgba(255, 190, 85, 0.8)", "rgba(255, 190, 85, 0.14)"),
        "GREEN": ("#24d58a", "0 0 18px rgba(36, 213, 138, 0.8)", "rgba(36, 213, 138, 0.14)"),
    }

    def lamp_markup(label):
        color, glow, halo = lamp_styles[label]
        is_active = label == state
        background = color if is_active else "rgba(255,255,255,0.08)"
        box_shadow = glow if is_active else "inset 0 0 0 1px rgba(255,255,255,0.03)"
        halo_markup = (
            f'<div style="position:absolute; inset:-10px; border-radius:999px; background:{halo}; filter: blur(8px);"></div>'
            if is_active
            else ""
        )
        return f"""
            <div style="display:flex; align-items:center; gap:14px;">
                <div style="position:relative; width:56px; height:56px;">
                    {halo_markup}
                    <div style="position:relative; z-index:2; width:56px; height:56px; border-radius:999px; background:{background}; border:1px solid rgba(255,255,255,0.08); box-shadow:{box_shadow};"></div>
                </div>
                <div style="font-family:Inter,sans-serif; color:{'#e8f3ff' if is_active else '#8ca0b8'}; font-size:13px; letter-spacing:0.18em; text-transform:uppercase; font-weight:700;">{label}</div>
            </div>
        """

    html = dedent(
        f"""
        <html>
        <body style="margin:0; background:transparent;">
            <div style="border:1px solid rgba(90, 129, 173, 0.24); border-radius:8px; background:linear-gradient(180deg, rgba(6,9,17,0.96), rgba(11,16,27,0.94)); padding:18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                    <div style="font-family:Inter,sans-serif; color:#8ca0b8; font-size:12px; text-transform:uppercase; letter-spacing:0.16em;">Signal stack</div>
                    <div style="font-family:Rajdhani,sans-serif; color:#e8f3ff; font-size:24px; font-weight:700;">{state}</div>
                </div>
                <div style="display:grid; gap:12px;">
                    {lamp_markup("RED")}
                    {lamp_markup("YELLOW")}
                    {lamp_markup("GREEN")}
                </div>
            </div>
        </body>
        </html>
        """
    ).strip()
    components.html(html, height=250)


def draw_fusion_map(junctions, active_index=0, is_emergency=False, map_key=None):
    """Render the tactical route map with restrained styling."""
    center = junctions[active_index]["coords"]
    map_obj = folium.Map(
        location=center,
        zoom_start=14,
        tiles="cartodbdark_matter",
        control_scale=True,
        zoom_control=True,
    )

    coords = [junction["coords"] for junction in junctions]
    folium.PolyLine(coords, color="#53e0ff", weight=7, opacity=0.18).add_to(map_obj)
    folium.PolyLine(coords, color="#53e0ff", weight=4, opacity=0.85, dash_array="8 7").add_to(map_obj)

    for index, junction in enumerate(junctions):
        is_active = index == active_index
        is_live = is_active and is_emergency
        ring_color = "#24d58a" if is_live else ("#53e0ff" if is_active else "#6a7c93")
        fill_color = "#24d58a" if is_live else ("#53e0ff" if is_active else "#182233")

        folium.CircleMarker(
            location=junction["coords"],
            radius=11 if is_active else 7,
            color=ring_color,
            weight=2,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.95,
            popup=(
                f"<div style='font-family:Inter,sans-serif;'>"
                f"<strong>{junction['id']}</strong><br>{junction['name']}</div>"
            ),
        ).add_to(map_obj)

        if is_live:
            folium.CircleMarker(
                location=junction["coords"],
                radius=20,
                color="#24d58a",
                weight=1,
                fill=True,
                fill_color="#24d58a",
                fill_opacity=0.16,
            ).add_to(map_obj)

    return st_folium(map_obj, width=None, height=390, key=map_key)


def render_route_strip(junctions, active_index, is_preempted):
    tiles = []
    for index, junction in enumerate(junctions):
        active_class = "active" if index == active_index else ""
        suffix = " open" if index == active_index and is_preempted else ""
        tiles.append(
            (
                f'<div class="route-stop {active_class}">'
                f'<div class="route-id">{junction["id"]}{suffix}</div>'
                f'<div class="route-name">{junction["name"]}</div>'
                f"</div>"
            )
        )
    st.markdown(f'<div class="route-strip">{"".join(tiles)}</div>', unsafe_allow_html=True)


def draw_gauge(value, title, accent="#53e0ff"):
    """Draw a premium, compact gauge."""
    percent = value * 100
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percent,
            number={
                "suffix": "%",
                "font": {"color": "#e8f3ff", "family": "Rajdhani", "size": 34},
            },
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": title,
                "font": {"size": 14, "color": "#8ca0b8", "family": "Inter"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 0,
                    "tickcolor": "#223043",
                    "showticklabels": False,
                },
                "bar": {"color": "rgba(0,0,0,0)", "thickness": 0},
                "bgcolor": "rgba(255,255,255,0.04)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, percent], "color": accent},
                    {"range": [percent, 100], "color": "rgba(255,255,255,0.05)"},
                ],
                "threshold": {
                    "line": {"color": "#ffffff", "width": 2},
                    "thickness": 0.76,
                    "value": percent,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=24, b=8),
        height=190,
    )
    return fig


def render_history_chart(history_data):
    """Render the telemetry bar chart."""
    fig = go.Figure()
    colors = ["#24d58a" if value > 0 else "#233246" for value in history_data]
    fig.add_trace(
        go.Bar(
            x=list(range(1, len(history_data) + 1)),
            y=history_data,
            marker_color=colors,
            marker_line_width=0,
            opacity=0.92,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title={
            "text": "Preemption telemetry",
            "font": {"size": 13, "color": "#8ca0b8", "family": "Inter"},
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
            range=[0, 1.2],
            showticklabels=False,
        ),
        margin=dict(l=0, r=0, t=28, b=0),
        height=170,
        bargap=0.24,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
