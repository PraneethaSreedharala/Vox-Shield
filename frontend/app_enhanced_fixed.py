import streamlit as st
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

# Add backend directory to path for importing shared audio data
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from audio_data_share import audio_data_share

st.set_page_config(page_title="Vox-Shield Enhanced", layout="wide")

st.title("Vox-Shield Enhanced")
st.subheader("Real-Time Voice Protection with Frequency Visualization")

# -----------------------------
# STATE MANAGEMENT
# -----------------------------
STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))
MODE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_mode"))

def set_protection_state(is_active):
    st.session_state.active = is_active
    try:
        with open(STATE_FILE, "w") as f:
            f.write("1" if is_active else "0")
    except Exception as e:
        st.error(f"Failed to update state file: {e}")

if "active" not in st.session_state:
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
        try:
            with open(MODE_FILE, "w") as f:
                f.write("balanced")
            st.success("Balanced mode activated - Best audio quality")
        except Exception as e:
            st.error(f"Failed to set mode: {e}")

with col2:
    if st.button("High Protection", use_container_width=True, help="Maximum protection, some quality impact"):
        try:
            with open(MODE_FILE, "w") as f:
                f.write("high")
            st.success("High protection mode activated")
        except Exception as e:
            st.error(f"Failed to set mode: {e}")

# Display current mode
try:
    with open(MODE_FILE, "r") as f:
        current_mode = f.read().strip()
    if current_mode == "high":
        st.info("Current Mode: High Protection")
    else:
        st.info("Current Mode: Balanced Quality")
except:
    st.info("Current Mode: Balanced Quality (default)")

# -----------------------------
# CONTROL BUTTONS
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
else:
    st.warning("Voice Protection INACTIVE")

# -----------------------------
# REAL-TIME FREQUENCY VISUALIZATION
# -----------------------------
st.subheader("Real-Time Frequency Spectrum Analysis")

# Create figure layout
def create_frequency_plot(title, data_color):
    """Create empty frequency plot template"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines',
        name='Magnitude',
        line=dict(color=data_color, width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 123, 255, 0.3)'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Frequency (Hz)',
        yaxis_title='Normalized Magnitude',
        xaxis=dict(range=[0, 4000]),
        yaxis=dict(range=[0, 1.1]),
        height=300,
        showlegend=False,
        template='plotly_dark'
    )
    
    return fig

# Initialize plots
col1, col2 = st.columns(2)

with col1:
    original_plot = create_frequency_plot("Original Voice Spectrum", "rgb(0, 123, 255)")
    st.plotly_chart(original_plot, use_container_width=True, key="original")

with col2:
    protected_plot = create_frequency_plot("Protected Voice Spectrum", "rgb(255, 69, 0)")
    st.plotly_chart(protected_plot, use_container_width=True, key="protected")

# Add explanation
st.info("Protected signal shows altered spectral pattern - AI protection is active!")

# -----------------------------
# VISUALIZATION UPDATE LOOP
# -----------------------------
def update_visualization():
    """Update real-time frequency visualization"""
    
    # Get audio data
    freqs, raw_magnitude, processed_magnitude = audio_data_share.get_visualization_data(max_freq=4000)
    
    if freqs is not None and raw_magnitude is not None and processed_magnitude is not None:
        # Update original spectrum plot
        original_fig = go.Figure()
        original_fig.add_trace(go.Scatter(
            x=freqs,
            y=raw_magnitude,
            mode='lines',
            name='Original',
            line=dict(color='rgb(0, 123, 255)', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 123, 255, 0.3)'
        ))
        
        original_fig.update_layout(
            title="Original Voice Spectrum",
            xaxis_title='Frequency (Hz)',
            yaxis_title='Normalized Magnitude',
            xaxis=dict(range=[0, 4000]),
            yaxis=dict(range=[0, 1.1]),
            height=300,
            showlegend=False,
            template='plotly_dark'
        )
        
        # Update protected spectrum plot
        protected_fig = go.Figure()
        protected_fig.add_trace(go.Scatter(
            x=freqs,
            y=processed_magnitude,
            mode='lines',
            name='Protected',
            line=dict(color='rgb(255, 69, 0)', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 69, 0, 0.3)'
        ))
        
        protected_fig.update_layout(
            title="Protected Voice Spectrum",
            xaxis_title='Frequency (Hz)',
            yaxis_title='Normalized Magnitude',
            xaxis=dict(range=[0, 4000]),
            yaxis=dict(range=[0, 1.1]),
            height=300,
            showlegend=False,
            template='plotly_dark'
        )
        
        # Update plots
        with col1:
            st.plotly_chart(original_fig, use_container_width=True, key="original_live")
        
        with col2:
            st.plotly_chart(protected_fig, use_container_width=True, key="protected_live")
        
        # Calculate and display statistics
        raw_energy = np.sum(raw_magnitude**2)
        processed_energy = np.sum(processed_magnitude**2)
        energy_ratio = processed_energy / raw_energy if raw_energy > 0 else 1.0
        
        # Calculate spectral difference
        spectral_diff = np.mean(np.abs(processed_magnitude - raw_magnitude))
        
        # Update stats
        st.metric("Processing Intensity", f"{spectral_diff:.4f}")
        st.metric("Energy Ratio", f"{energy_ratio:.3f}")
        
        # Get update statistics
        update_stats = audio_data_share.get_update_stats()
        st.metric("Updates/sec", f"{update_stats['updates_per_second']:.1f}")

# Continuous update loop
if st.session_state.active:
    st.markdown("---")
    st.subheader("Live Visualization")
    
    # Create container for live updates
    visualization_container = st.container()
    
    while st.session_state.active:
        with visualization_container:
            update_visualization()
        
        # Update rate: 10 FPS for smooth animation
        time.sleep(0.1)
else:
    st.info("Start protection to see real-time frequency visualization")

# -----------------------------
# ADDITIONAL METRICS
# -----------------------------
st.subheader("System Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Sample Rate", "44.1 kHz")
with col2:
    st.metric("FFT Size", "512 samples")
with col3:
    st.metric("Frequency Range", "0-4000 Hz")

# -----------------------------
# STATUS
# -----------------------------
st.markdown("---")
if st.session_state.active:
    st.success("System Status: PROTECTION ACTIVE")
else:
    st.warning("System Status: INACTIVE")
