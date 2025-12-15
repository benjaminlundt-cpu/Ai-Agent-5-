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

st.title("⚽ Soccer Injury Prediction & Prevention AI")
st.caption("Live GPS monitoring | Session planning | Browser-only demo")

# --------------------------------
# AUTO REFRESH (LIVE MODE)
# --------------------------------
st.sidebar.header("Live Settings")

live_mode = st.sidebar.checkbox("📡 Live Training Mode", value=True)
refresh_rate = st.sidebar.slider(
    "Refresh every (seconds)", 10, 120, 30
)

if live_mode:
    st.sidebar.info("Live mode simulates real-time GPS updates")
    time.sleep(0.1)
   if live_mode:
    time.sleep(refresh_rate)
    st.rerun()


# --------------------------------
# MOCK GPS API
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
            "session_rpe": np.random.uniform(4.5, 8.5),
            "duration": np.random.randint(60, 110),
        })
    return pd.DataFrame(players)

# --------------------------------
# FEATURE ENGINEERING
# --------------------------------
def build_features(df):
    df = df.copy()
    df["session_load"] = df["session_rpe"] * df["duration"]
    df["acwr"] = np.random.uniform(0.7, 1.8, len(df))
    df["fatigue_z"] = np.random.normal(0.5, 0.8, len(df))
    df["soreness_z"] = np.random.normal(0.4, 0.7, len(df))
    return df

# --------------------------------
# RISK ENGINE
# --------------------------------
def compute_injury_risk(acwr, fatigue, soreness, hsr, acc, dec, congestion=False, rtp=False):
    risk = 0.0

    if acwr > 1.6:
        risk += 0.40
    elif acwr > 1.3:
        risk += 0.25
    elif acwr < 0.8:
        risk += 0.10

    risk += max(0, fatigue) * 0.12
    risk += max(0, soreness) * 0.15

    if hsr > 1200:
        risk += 0.20
    elif hsr > 800:
        risk += 0.10

    if acc + dec > 140:
        risk += 0.15
    elif acc + dec > 100:
        risk += 0.08

    if congestion:
        risk += 0.15

    if rtp:
        risk *= 1.25

    return min(risk, 1.0)

# --------------------------------
# SESSION PLANNING AGENT
# --------------------------------
def session_plan(risk, rtp):
    if rtp:
        return {
            "Session Type": "Return-to-Play",
            "Load Target": "Low–Moderate",
            "HSR Limit": "< 60%",
            "Accel/Decel": "Controlled",
        }

    if risk >= 0.75:
        return {
            "Session Type": "Recovery / Medical",
            "Load Target": "Very Low",
            "HSR Limit": "None",
            "Accel/Decel": "None",
        }
    elif risk >= 0.55:
        return {
            "Session Type": "Modified Training",
            "Load Target": "-30%",
            "HSR Limit": "< 70%",
            "Accel/Decel": "Reduced",
        }
    elif risk >= 0.35:
        return {
            "Session Type": "Normal Training",
            "Load Target": "Normal",
            "HSR Limit": "< 85%",
            "Accel/Decel": "Monitor",
        }
    else:
        return {
            "Session Type": "Full Training",
            "Load Target": "Full",
            "HSR Limit": "No limit",
            "Accel/Decel": "Full",
        }

# --------------------------------
# SIDEBAR CONTEXT
# --------------------------------
st.sidebar.header("Context")

match_congestion = st.sidebar.checkbox("Match Congestion")
rtp_players = st.sidebar.multiselect(
    "Return-to-Play Players",
    [f"Player {i+1}" for i in range(25)]
)

# --------------------------------
# PIPELINE
# --------------------------------
gps = get_mock_gps_data()
df = build_features(gps)

risks, plans = [], []

for _, r in df.iterrows():
    risk = compute_injury_risk(
        r["acwr"],
        r["fatigue_z"],
        r["soreness_z"],
        r["high_speed_distance"],
        r["accelerations"],
        r["decelerations"],
        congestion=match_congestion,
        rtp=r["player"] in rtp_players
    )
    risks.append(risk)
    plans.append(session_plan(risk, r["player"] in rtp_players))

df["risk_pct"] = np.array(risks) * 100
df["session_plan"] = plans

# --------------------------------
# SQUAD VIEW
# --------------------------------
st.subheader("🧑‍🤝‍🧑 Live Squad Risk")

st.dataframe(
    df[["player", "risk_pct"]]
    .sort_values("risk_pct", ascending=False),
    use_container_width=True
)

# --------------------------------
# PLAYER DETAIL + SESSION PLAN
# --------------------------------
st.subheader("📅 Session Planning Recommendation")

player = st.selectbox("Select Player", df["player"])
p = df[df.player == player].iloc[0]
plan = p.session_plan

col1, col2, col3 = st.columns(3)
col1.metric("Injury Risk", f"{p.risk_pct:.1f}%")
col2.metric("ACWR", f"{p.acwr:.2f}")
col3.metric("HSR (m)", int(p.high_speed_distance))

st.success(f"**Recommended Session:** {plan['Session Type']}")

st.markdown(
f"""
- **Load Target:** {plan['Load Target']}
- **High-Speed Running:** {plan['HSR Limit']}
- **Accelerations / Decelerations:** {plan['Accel/Decel']}
"""
)

# --------------------------------
# FOOTER
# --------------------------------
st.caption(
    f"Live demo updated at {datetime.now().strftime('%H:%M:%S')} | Elite soccer workflow simulation"
)
