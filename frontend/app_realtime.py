import streamlit as st
import numpy as np
import time
import plotly.graph_objects as go
import sys
import os
from scipy.fft import rfft, rfftfreq

# Add backend directory to path for importing shared audio data
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from audio_data_share import audio_data_share

st.set_page_config(page_title="Vox-Shield Real-Time", layout="wide")

st.title("Vox-Shield Real-Time")
st.subheader("Real-Time Voice Protection with Live Frequency Visualization")

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

# Initialize session state
if "active" not in st.session_state:
    try:
        with open(STATE_FILE, "r") as f:
            st.session_state.active = (f.read().strip() == "1")
    except:
        set_protection_state(False)

if "update_count" not in st.session_state:
    st.session_state.update_count = 0

# -----------------------------
# PROTECTION MODE SELECTION
# -----------------------------
st.subheader("Protection Settings")

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
col1, col2, col3, col4 = st.columns(4)

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

with col4:
    if st.button("Export Sample", use_container_width=True, help="Manually export current audio sample"):
        st.info("Export feature: Audio is automatically saved when you stop protection")

if st.session_state.active:
    st.success("Voice Protection ACTIVE")
else:
    st.warning("Voice Protection INACTIVE")

# -----------------------------
# RECORDING STATUS
# -----------------------------
st.subheader("Audio Recording Status")

# Check for recently saved files
exports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exports'))
if os.path.exists(exports_dir):
    # Get recent WAV files
    wav_files = [f for f in os.listdir(exports_dir) if f.endswith('.wav')]
    if wav_files:
        # Sort by modification time
        wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(exports_dir, f)), reverse=True)
        
        # Show most recent files
        recent_files = wav_files[:4]  # Show up to 4 recent files
        
        st.info(f"Found {len(wav_files)} recorded audio file(s) in exports folder")
        
        # Display recent files
        col1, col2 = st.columns(2)
        for i, file in enumerate(recent_files):
            file_path = os.path.join(exports_dir, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            mod_time = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(file_path)))
            
            if i % 2 == 0:
                with col1:
                    if 'raw' in file.lower():
                        st.success(f"🎙️ {file} ({file_size:.1f}MB) - {mod_time}")
                    else:
                        st.warning(f"🔒 {file} ({file_size:.1f}MB) - {mod_time}")
            else:
                with col2:
                    if 'raw' in file.lower():
                        st.success(f"🎙️ {file} ({file_size:.1f}MB) - {mod_time}")
                    else:
                        st.warning(f"🔒 {file} ({file_size:.1f}MB) - {mod_time}")
        
        # Export info
        st.info("📁 Files saved in: " + exports_dir)
        st.info("💡 Use these files for AI cloning vulnerability testing")
    else:
        st.info("No recorded audio files found. Start protection to record audio.")
else:
    st.info("Exports folder will be created when you stop protection.")

# -----------------------------
# REAL-TIME FREQUENCY VISUALIZATION
# -----------------------------
st.subheader("Real-Time Frequency Spectrum Analysis")

# Create placeholders for dynamic updates
original_placeholder = st.empty()
protected_placeholder = st.empty()
stats_placeholder = st.empty()

def create_frequency_plot(title, data_color):
    """Create frequency plot template"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines',
        name='Magnitude',
        line=dict(color=data_color, width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 123, 255, 0.3)' if data_color == 'blue' else 'rgba(255, 69, 0, 0.3)'
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

# Create plot placeholders
col1, col2 = st.columns(2)

with col1:
    original_chart = st.empty()

with col2:
    protected_chart = st.empty()

# Add explanation
st.info("Protected signal shows altered spectral pattern - AI protection is active!")

# -----------------------------
# REAL-TIME UPDATE FUNCTION
# -----------------------------
def update_frequency_plots():
    """Update frequency plots with real-time data"""
    
    # Get audio data from shared module
    freqs, raw_magnitude, processed_magnitude = audio_data_share.get_visualization_data(max_freq=4000)
    
    if freqs is not None and raw_magnitude is not None and processed_magnitude is not None:
        # Check if we have actual audio data (not just zeros)
        max_raw = np.max(np.abs(raw_magnitude))
        max_processed = np.max(np.abs(processed_magnitude))
        
        if max_raw > 0.001:  # Only update if we have meaningful signal
            # Create original spectrum plot
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
            
            # Create protected spectrum plot
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
            
            # Update charts
            with original_chart:
                st.plotly_chart(original_fig, use_container_width=True, key=f"original_{st.session_state.update_count}")
            
            with protected_chart:
                st.plotly_chart(protected_fig, use_container_width=True, key=f"protected_{st.session_state.update_count}")
            
            # Calculate and display statistics
            raw_energy = np.sum(raw_magnitude**2)
            processed_energy = np.sum(processed_magnitude**2)
            energy_ratio = processed_energy / raw_energy if raw_energy > 0 else 1.0
            
            spectral_diff = np.mean(np.abs(processed_magnitude - raw_magnitude))
            
            # Update stats
            with stats_placeholder:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Processing Intensity", f"{spectral_diff:.4f}")
                with col2:
                    st.metric("Energy Ratio", f"{energy_ratio:.3f}")
                with col3:
                    update_stats = audio_data_share.get_update_stats()
                    st.metric("Updates/sec", f"{update_stats['updates_per_second']:.1f}")
            
            # Increment update counter
            st.session_state.update_count += 1
            
            return True
        else:
            # No meaningful audio data
            return False
    else:
        # No data available
        return False

# -----------------------------
# AUTO-REFRESH MECHANISM
# -----------------------------
if st.session_state.active:
    st.markdown("---")
    st.subheader("Live Frequency Visualization")
    
    # Add refresh control
    auto_refresh = st.checkbox("Auto-refresh (10 FPS)", value=True)
    refresh_rate = st.slider("Refresh Rate (FPS)", 1, 30, 10) if auto_refresh else 0
    
    if auto_refresh and refresh_rate > 0:
        # Create a placeholder for the entire visualization section
        viz_container = st.empty()
        
        # Use Streamlit's rerun mechanism for real-time updates
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        current_time = time.time()
        if current_time - st.session_state.last_refresh >= (1.0 / refresh_rate):
            with viz_container:
                if update_frequency_plots():
                    st.session_state.last_refresh = current_time
                    st.rerun()
        else:
            with viz_container:
                st.info("Waiting for audio signal...")
                st.session_state.last_refresh = current_time
                st.rerun()
    else:
        # Manual refresh button
        if st.button("Refresh Now"):
            update_frequency_plots()
            st.rerun()
        
        # Show current data status
        freqs, raw_magnitude, processed_magnitude = audio_data_share.get_visualization_data(max_freq=4000)
        if freqs is not None:
            max_raw = np.max(np.abs(raw_magnitude))
            st.info(f"Current signal level: {max_raw:.4f}")
        else:
            st.warning("No audio data available - ensure backend is running")
else:
    st.info("Start protection to see real-time frequency visualization")

# -----------------------------
# DEBUG INFORMATION
# -----------------------------
st.markdown("---")
st.subheader("System Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Sample Rate", "44.1 kHz")
with col2:
    st.metric("FFT Size", "512 samples")
with col3:
    st.metric("Frequency Range", "0-4000 Hz")

# Show update count
st.metric("Total Updates", st.session_state.update_count)

# -----------------------------
# STATUS
# -----------------------------
st.markdown("---")
if st.session_state.active:
    st.success("System Status: PROTECTION ACTIVE")
else:
    st.warning("System Status: INACTIVE")
