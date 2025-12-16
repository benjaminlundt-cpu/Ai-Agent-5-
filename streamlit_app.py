import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --------------------------------
# PAGE SETUP
# --------------------------------
st.set_page_config(
    page_title="Soccer Injury Prevention AI",
    layout="wide"
)

st.title("⚽ Soccer Injury Prediction & Session Planning AI")
st.caption("Browser-only | Explainable | Elite soccer workflow")

# --------------------------------
# SIDEBAR — LIVE MODE
# --------------------------------
st.sidebar.header("Live Settings")

live_mode = st.sidebar.checkbox("📡 Live Training Mode", value=False)
refresh_rate = st.sidebar.slider("Refresh every (seconds)", 10, 120, 30)

# --------------------------------
# SIDEBAR — MATCH CONTEXT
# --------------------------------
st.sidebar.header("Match Context")

days_to_match = st.sidebar.selectbox(
    "Days Until Next Match",
    options=[0, 1, 2, 3, 4, 5, 6],
    format_func=lambda x: "MD" if x == 0 else f"MD-{x}"
)

match_congestion = st.sidebar.checkbox("Fixture Congestion")

# --------------------------------
# MOCK GPS DATA (API SIMULATION)
# --------------------------------
def get_mock_gps_data():
    players = []
    for i in range(25):
        players.append({
            "player": f"Player {i+1}",
            "total_distance": np.random.randint(4500, 11000),
            "high_speed_distance": np.random.randint(300, 1500),
            "accelerations": np.random.randint(40, 95),
            "decelerations": np.random.randint(40, 95),
            "rpe": np.random.uniform(4.5, 8.5),
            "duration": np.random.randint(60, 110),
            "fatigue_z": np.random.normal(0.5, 0.8),
            "soreness_z": np.random.normal(0.4, 0.7),
            "acwr": np.random.uniform(0.7, 1.8),
        })
    return pd.DataFrame(players)

# --------------------------------
# INJURY RISK ENGINE
# --------------------------------
def compute_injury_risk(acwr, fatigue, soreness, hsr, acc, dec, congestion, rtp):
    risk = 0.0

    # ACWR
    if acwr > 1.6:
        risk += 0.40
    elif acwr > 1.3:
        risk += 0.25
    elif acwr < 0.8:
        risk += 0.10

    # Wellness
    risk += max(0, fatigue) * 0.12
    risk += max(0, soreness) * 0.15

    # High-speed running
    if hsr > 1200:
        risk += 0.20
    elif hsr > 800:
        risk += 0.10

    # Acc / Dec
    if acc + dec > 140:
        risk += 0.15
    elif acc + dec > 100:
        risk += 0.08

    # Congestion & RTP
    if congestion:
        risk += 0.15
    if rtp:
        risk *= 1.25

    return min(risk, 1.0)

# --------------------------------
# SESSION PLANNING ENGINE (MD-AWARE)
# --------------------------------
def session_plan(risk, rtp, days_to_match):
    if days_to_match == 0:
        return "MATCH DAY", "Game Load", "Match Demands"

    if rtp:
        return "Return-to-Play", "Low–Moderate", "< 60% HSR"

    if days_to_match == 1:
        return "MD-1 Activation", "Very Low", "< 50% HSR"

    if days_to_match == 2:
        if risk >= 0.55:
            return "MD-2 Modified", "-30% Load", "< 60% HSR"
        else:
            return "MD-2 Tactical", "Moderate", "< 75% HSR"

    # MD-3+
    if risk >= 0.75:
        return "Recovery / Medical", "Very Low", "None"
    elif risk >= 0.55:
        return "Modified Training", "-30%", "< 70% HSR"
    elif risk >= 0.35:
        return "Normal Training", "Normal", "< 85% HSR"
    else:
        return "Full Training", "Full", "No Limit"

# --------------------------------
# RTP SELECTION
# --------------------------------
st.sidebar.header("Return-to-Play")
rtp_players = st.sidebar.multiselect(
    "Players in RTP",
    [f"Player {i+1}" for i in range(25)]
)

# --------------------------------
# PIPELINE
# --------------------------------
df = get_mock_gps_data()

risks = []
plans = []

for _, r in df.iterrows():
    risk = compute_injury_risk(
        r["acwr"],
        r["fatigue_z"],
        r["soreness_z"],
        r["high_speed_distance"],
        r["accelerations"],
        r["decelerations"],
        match_congestion,
        r["player"] in rtp_players
    )
    plan = session_plan(risk, r["player"] in rtp_players, days_to_match)

    risks.append(risk * 100)
    plans.append(plan)

df["Injury Risk (%)"] = risks
df["Session Type"] = [p[0] for p in plans]
df["Load Target"] = [p[1] for p in plans]
df["HSR Limit"] = [p[2] for p in plans]

# --------------------------------
# SQUAD VIEW
# --------------------------------
st.subheader("🧑‍🤝‍🧑 Squad Injury Risk Overview")

st.dataframe(
    df[["player", "Injury Risk (%)", "Session Type"]]
    .sort_values("Injury Risk (%)", ascending=False),
    use_container_width=True
)

# --------------------------------
# PLAYER DETAIL VIEW
# --------------------------------
st.subheader("📅 Individual Session Planning")

player = st.selectbox("Select Player", df["player"])
p = df[df.player == player].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Injury Risk", f"{p['Injury Risk (%)']:.1f}%")
col2.metric("ACWR", f"{p.acwr:.2f}")
col3.metric("HSR (m)", int(p.high_speed_distance))

st.success(f"**Recommended Session:** {p['Session Type']}")

st.markdown(
f"""
- **Load Target:** {p['Load Target']}
- **High-Speed Running:** {p['HSR Limit']}
"""
)

# --------------------------------
# EXPLAINABILITY
# --------------------------------
st.subheader("🧠 Risk Drivers")

drivers = []
if p.acwr > 1.3:
    drivers.append("📈 Acute workload spike (ACWR)")
if p.fatigue_z > 1:
    drivers.append("😴 Elevated fatigue")
if p.soreness_z > 1:
    drivers.append("🦵 Increased muscle soreness")
if p.high_speed_distance > 800:
    drivers.append("🏃 High-speed running exposure")
if p.accelerations + p.decelerations > 120:
    drivers.append("⚡ High neuromuscular load")

if drivers:
    for d in drivers:
        st.write(d)
else:
    st.write("✅ No major injury risk flags detected")

# --------------------------------
# FOOTER
# --------------------------------
st.caption(
    f"Last updated {datetime.now().strftime('%H:%M:%S')} | Elite soccer injury prevention demo"
)

# --------------------------------
# LIVE REFRESH (SAFE)
# --------------------------------
if live_mode:
    time.sleep(refresh_rate)
    st.rerun()
