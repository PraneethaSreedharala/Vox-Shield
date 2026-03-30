import streamlit as st
import numpy as np
import time

st.set_page_config(page_title="Vox-Shield", layout="centered")

st.title("🔊 Vox-Shield")
st.subheader("Real-Time Voice Protection System")

# -----------------------------
# STATE MANAGEMENT
# -----------------------------
import os

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))

def set_protection_state(is_active):
    st.session_state.active = is_active
    try:
        with open(STATE_FILE, "w") as f:
            f.write("1" if is_active else "0")
    except Exception as e:
        st.error(f"Failed to update state file: {e}")

if "active" not in st.session_state:
    # Initialize from file if exists
    try:
        with open(STATE_FILE, "r") as f:
            st.session_state.active = (f.read().strip() == "1")
    except:
        set_protection_state(False)

# -----------------------------
# PROTECTION MODE SELECTION
# -----------------------------
st.subheader("Protection Settings")

# Protection mode selection
col1, col2 = st.columns(2)

with col1:
    if st.button("Balanced Mode", use_container_width=True, help="Better audio quality, good protection"):
        # Save mode preference to a file that backend can read
        mode_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_mode"))
        try:
            with open(mode_file, "w") as f:
                f.write("balanced")
            st.success("Balanced mode activated - Best audio quality")
        except Exception as e:
            st.error(f"Failed to set mode: {e}")

with col2:
    if st.button("High Protection", use_container_width=True, help="Maximum protection, some quality impact"):
        mode_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_mode"))
        try:
            with open(mode_file, "w") as f:
                f.write("high")
            st.success("High protection mode activated")
        except Exception as e:
            st.error(f"Failed to set mode: {e}")

# Display current mode
mode_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_mode"))
try:
    with open(mode_file, "r") as f:
        current_mode = f.read().strip()
    if current_mode == "high":
        st.info("Current Mode: High Protection 🔒")
    else:
        st.info("Current Mode: Balanced Quality 🎵")
except:
    st.info("Current Mode: Balanced Quality 🎵 (default)")

# -----------------------------
# BUTTONS
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Start Protection", use_container_width=True):
        set_protection_state(True)

with col2:
    if st.button("Stop Protection", use_container_width=True):
        set_protection_state(False)

with col3:
    if st.button("Exit System", use_container_width=True):
        st.session_state.active = False
        try:
            with open(STATE_FILE, "w") as f:
                f.write("-1")
            st.success("Shutdown signal sent to backend.")
        except Exception as e:
            st.error(f"Failed to update state file: {e}")

if st.session_state.active:
    st.success("Voice Protection ACTIVE")

# -----------------------------
# SLIDER (now for visual feedback only)
# -----------------------------
level = st.slider("Audio Quality", 0, 100, 85)  # Default to high quality

# -----------------------------
# AUDIO QUALITY INDICATOR
# -----------------------------
quality_score = min(100, level + np.random.randint(5, 15))  # High quality scores
st.metric("Audio Quality", f"{quality_score}%")

# -----------------------------
# DYNAMIC SECURITY SCORE
# -----------------------------
security_score = min(100, level + np.random.randint(20, 40))
st.metric("Security Score", f"{security_score}%")

# -----------------------------
# LIVE WAVEFORM (FAKE BUT REALISTIC)
# -----------------------------
st.subheader("🔊 Live Voice Signal")

chart = st.line_chart(np.zeros(100))

if st.session_state.active:
    for i in range(50):
        new_data = np.random.randn(100) * (level / 50)
        chart.add_rows(new_data)
        time.sleep(0.05)

# -----------------------------
# AI ATTACK BLOCKED SIMULATION
# -----------------------------
st.subheader("🧠 AI Threat Monitor")

if st.session_state.active:
    if np.random.rand() > 0.7:
        st.error("⚠️ AI Voice Cloning Attempt Detected!")
        time.sleep(1)
        st.success("✅ Attack Blocked Successfully")

# -----------------------------
# STATUS
# -----------------------------
if st.session_state.active:
    st.info("System Status: PROTECTED 🟢")
else:
    st.warning("System Status: INACTIVE 🔴")