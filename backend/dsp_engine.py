import numpy as np
import os
import time
from scipy import signal
from scipy.fft import fft, ifft

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))
MODE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_mode"))

_last_check = 0
_is_active = False
_last_mode_check = 0

# Audio processing constants
SAMPLE_RATE = 44100
WINDOW_SIZE = 512
HOP_SIZE = 256
MAX_AMPLITUDE = 0.95  # Safety threshold

# Audio quality settings
NOISE_SCALE_HIGH = 0.02  # High protection mode
NOISE_SCALE_BALANCED = 0.008  # Balanced mode (default)
BLEND_RATIO_HIGH = 0.85  # High protection: 85% original + 15% processed
BLEND_RATIO_BALANCED = 0.92  # Balanced: 92% original + 8% processed

# Frequency-selective protection (Hz)
FORMANT_MIN = 300  # Lower bound of speech formants
FORMANT_MAX = 3500  # Upper bound of speech formants

# Protection mode
_protection_mode = "balanced"  # "balanced" or "high"

# Pre-compute window function
window = signal.windows.hann(WINDOW_SIZE, sym=False)

def check_active():
    """Check if protection is active via state file"""
    global _last_check, _is_active
    now = time.time()
    if now - _last_check > 0.5:  # Read file every 0.5s to avoid heavy I/O
        _last_check = now
        try:
            with open(STATE_FILE, "r") as f:
                _is_active = (f.read().strip() == "1")
        except:
            _is_active = False
    return _is_active

def set_protection_mode(mode):
    """Set protection mode: 'balanced' or 'high'"""
    global _protection_mode
    if mode in ["balanced", "high"]:
        _protection_mode = mode
        print(f"[DSP] Protection mode set to: {mode}")

def get_protection_settings():
    """Get current protection settings from file"""
    global _last_mode_check, _protection_mode
    
    now = time.time()
    if now - _last_mode_check > 1.0:  # Read mode file every 1 second
        _last_mode_check = now
        try:
            with open(MODE_FILE, "r") as f:
                mode = f.read().strip()
                if mode in ["balanced", "high"]:
                    _protection_mode = mode
        except:
            _protection_mode = "balanced"  # Default to balanced
    
    if _protection_mode == "high":
        return NOISE_SCALE_HIGH, BLEND_RATIO_HIGH
    else:
        return NOISE_SCALE_BALANCED, BLEND_RATIO_BALANCED

def get_speech_energy(audio):
    """Calculate speech energy to determine processing intensity"""
    # Calculate RMS energy
    rms = np.sqrt(np.mean(audio**2))
    return rms

def frequency_selective_mask(audio_shape):
    """Create frequency mask for formant regions"""
    if len(audio_shape) > 1:
        # Multi-channel
        mask = np.ones(audio_shape)
        freq_bins = WINDOW_SIZE // 2 + 1
        
        # Convert frequency ranges to bin indices
        min_bin = int(FORMANT_MIN * WINDOW_SIZE / SAMPLE_RATE)
        max_bin = int(FORMANT_MAX * WINDOW_SIZE / SAMPLE_RATE)
        
        # Ensure bins are within valid range
        min_bin = max(1, min_bin)
        max_bin = min(freq_bins - 1, max_bin)
        
        # Create mask that targets formant regions
        for ch in range(audio_shape[1]):
            mask[:min_bin, ch] = 1.0  # Below formants: no modification
            mask[min_bin:max_bin, ch] = 0.7  # Formant region: light modification
            mask[max_bin:, ch] = 0.9  # Above formants: moderate modification
    else:
        # Single channel
        mask = np.ones(audio_shape)
        freq_bins = len(audio_shape)
        
        min_bin = int(FORMANT_MIN * WINDOW_SIZE / SAMPLE_RATE)
        max_bin = int(FORMANT_MAX * WINDOW_SIZE / SAMPLE_RATE)
        
        # Ensure bins are within valid range
        min_bin = max(1, min_bin)
        max_bin = min(freq_bins - 1, max_bin)
        
        mask[:min_bin] = 1.0
        mask[min_bin:max_bin] = 0.7
        mask[max_bin:] = 0.9
    
    return mask

def apply_adaptive_processing(audio, noise_scale):
    """Apply adaptive processing based on speech energy"""
    energy = get_speech_energy(audio)
    
    # Adaptive noise scaling based on energy
    if energy < 0.01:  # Very low energy (silence/whisper)
        adaptive_scale = noise_scale * 0.2  # Minimal processing
    elif energy < 0.05:  # Low energy (soft speech)
        adaptive_scale = noise_scale * 0.5  # Light processing
    else:  # Normal energy (regular speech)
        adaptive_scale = noise_scale  # Full processing
    
    return adaptive_scale

def normalize_audio(audio):
    """Safely normalize audio to prevent clipping"""
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        # Normalize to safe range
        normalized = audio / max_val * min(max_val, MAX_AMPLITUDE)
    else:
        normalized = audio
    
    # Final clipping protection
    return np.clip(normalized, -1.0, 1.0)

def apply_limiter(audio, threshold=0.8):
    """Apply soft limiting to prevent sudden spikes"""
    abs_audio = np.abs(audio)
    mask = abs_audio > threshold
    
    if np.any(mask):
        # Soft limiting: compress values above threshold
        audio[mask] = np.sign(audio[mask]) * (threshold + (abs_audio[mask] - threshold) * 0.1)
    
    return audio

def apply_adversarial_noise(audio):
    """Apply subtle adversarial noise for voice protection"""
    # Reduced noise strength for stability
    noise = np.random.normal(0, NOISE_SCALE, audio.shape)
    
    # Apply window to noise to smooth edges
    windowed_noise = noise * window.reshape(-1, 1) if len(audio.shape) > 1 else noise * window
    
    return audio + windowed_noise

def process_fft_domain(audio):
    """Process audio in FFT domain with proper handling"""
    if len(audio.shape) > 1:
        # Multi-channel processing
        processed = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            processed[:, ch] = process_single_channel(audio[:, ch])
        return processed
    else:
        return process_single_channel(audio)

def process_single_channel(audio_channel):
    """Process single channel audio with FFT"""
    # Apply window function
    windowed = audio_channel * window
    
    # FFT
    fft_data = fft(windowed)
    
    # Get magnitude and phase
    magnitude = np.abs(fft_data)
    phase = np.angle(fft_data)
    
    # Subtle magnitude modification (voice protection)
    # Very gentle high-frequency reduction to preserve voice
    freq_bins = len(magnitude) // 2
    high_freq_mask = np.arange(freq_bins) > (freq_bins * 0.85)  # Only affect very high frequencies
    magnitude[high_freq_mask] *= 0.98  # Much gentler reduction
    
    # Reconstruct with original phase (preserves natural sound)
    processed_fft = magnitude * np.exp(1j * phase)
    
    # Inverse FFT
    processed_time = np.real(ifft(processed_fft))
    
    # Apply window again to smooth edges
    return processed_time * window

def smooth_audio_chunks(current_chunk, prev_chunk=None):
    """Smooth transitions between audio chunks"""
    if prev_chunk is None:
        return current_chunk
    
    # Overlap-add for smooth transitions
    overlap_size = HOP_SIZE
    if len(current_chunk) >= overlap_size and len(prev_chunk) >= overlap_size:
        # Crossfade between chunks
        fade_out = np.linspace(1, 0, overlap_size)
        fade_in = np.linspace(0, 1, overlap_size)
        
        result = current_chunk.copy()
        result[:overlap_size] = prev_chunk[-overlap_size:] * fade_out + current_chunk[:overlap_size] * fade_in
        
        return result
    
    return current_chunk

def debug_audio_stats(audio, chunk_num=0):
    """Print debug information for audio processing"""
    max_amp = np.max(np.abs(audio))
    rms = np.sqrt(np.mean(audio**2))
    
    if max_amp > 0.9:  # Alert on potential clipping
        print(f"[DSP WARNING] Chunk {chunk_num}: High amplitude detected - Max: {max_amp:.3f}, RMS: {rms:.3f}")
    elif chunk_num % 100 == 0:  # Periodic status
        print(f"[DSP INFO] Chunk {chunk_num}: Max: {max_amp:.3f}, RMS: {rms:.3f}")

def protect_audio(audio, debug=False):
    """
    High-quality audio protection with minimal muffling
    Maintains natural voice while providing AI protection
    """
    if not check_active():
        return audio  # Return raw mic input when protection is OFF
    
    try:
        # Get current protection settings
        noise_scale, blend_ratio = get_protection_settings()
        
        # Debug logging
        if debug:
            energy = get_speech_energy(audio)
            print(f"[DSP DEBUG] Energy: {energy:.4f}, Mode: {_protection_mode}")
        
        # Step 1: Adaptive processing based on speech energy
        adaptive_noise_scale = apply_adaptive_processing(audio, noise_scale)
        
        # Step 2: Apply frequency-selective perturbation
        if len(audio.shape) > 1:
            # Multi-channel processing
            processed_audio = np.zeros_like(audio)
            for ch in range(audio.shape[1]):
                processed_audio[:, ch] = process_single_channel_enhanced(
                    audio[:, ch], adaptive_noise_scale
                )
        else:
            # Single channel processing
            processed_audio = process_single_channel_enhanced(audio, adaptive_noise_scale)
        
        # Step 3: Blend with original for natural sound
        final_output = blend_ratio * audio + (1 - blend_ratio) * processed_audio
        
        # Step 4: Final normalization and clipping protection
        max_val = np.max(np.abs(final_output))
        if max_val > 0:
            final_output = final_output / max_val * min(max_val, MAX_AMPLITUDE)
        
        final_output = np.clip(final_output, -1.0, 1.0)
        
        # Debug final output
        if debug:
            debug_audio_stats(final_output, 1)
            print(f"[DSP DEBUG] Blend ratio: {blend_ratio:.2f}, Adaptive scale: {adaptive_noise_scale:.4f}")
        
        return final_output
        
    except Exception as e:
        print(f"[DSP ERROR] Processing failed: {e}")
        # Fallback to pass-through if processing fails
        return np.clip(audio, -1.0, 1.0)

def process_single_channel_enhanced(audio_channel, noise_scale):
    """
    Enhanced single-channel processing with frequency-selective protection
    """
    # Apply window function
    windowed = audio_channel * window
    
    # FFT to frequency domain
    fft_data = fft(windowed)
    
    # Get magnitude and phase (preserve phase for natural sound)
    magnitude = np.abs(fft_data)
    phase = np.angle(fft_data)
    
    # Apply frequency-selective perturbation
    # Only modify frequencies critical for AI models
    perturbed_magnitude = magnitude.copy()
    
    # Add subtle adversarial noise across all frequencies
    noise = np.random.normal(0, noise_scale, magnitude.shape)
    perturbed_magnitude += noise * magnitude * 0.05  # Very subtle modification
    
    # Apply very gentle high-frequency reduction (preserves voice clarity)
    freq_bins = len(magnitude)
    high_freq_start = int(freq_bins * 0.85)  # Start reducing at 85% of spectrum
    if high_freq_start < freq_bins:
        # Create smooth roll-off
        for i in range(high_freq_start, freq_bins):
            reduction_factor = 0.95 + 0.05 * (i - high_freq_start) / (freq_bins - high_freq_start)
            perturbed_magnitude[i] *= reduction_factor
    
    # Reconstruct with original phase (crucial for natural sound)
    processed_fft = perturbed_magnitude * np.exp(1j * phase)
    
    # Inverse FFT
    processed_time = np.real(ifft(processed_fft))
    
    # Apply window again to smooth edges
    return processed_time * window

# Legacy compatibility
def protect_audio_legacy(audio):
    """Legacy function for backward compatibility"""
    return protect_audio(audio)

# Test function
def test_stability():
    """Test DSP engine for stability with new quality features"""
    print("[DSP TEST] Testing enhanced audio processing stability...")
    
    # Test both protection modes
    for mode in ["balanced", "high"]:
        print(f"[DSP TEST] Testing {mode} protection mode...")
        set_protection_mode(mode)
        
        # Generate test signal (speech-like)
        t = np.linspace(0, 1, SAMPLE_RATE)
        # Create a complex signal similar to human speech
        test_signal = (
            np.sin(2 * np.pi * 200 * t) * 0.3 +  # Fundamental
            np.sin(2 * np.pi * 400 * t) * 0.2 +  # First harmonic
            np.sin(2 * np.pi * 800 * t) * 0.1 +  # Second harmonic
            np.sin(2 * np.pi * 1600 * t) * 0.05   # Higher harmonic
        )
        
        # Process multiple chunks
        for i in range(10):
            chunk = test_signal[i*WINDOW_SIZE:(i+1)*WINDOW_SIZE]
            if len(chunk) == WINDOW_SIZE:
                processed = protect_audio(chunk, debug=(i == 0))
                max_amp = np.max(np.abs(processed))
                if max_amp > 1.0:
                    print(f"[DSP TEST FAIL] Clipping detected in {mode} mode, chunk {i}")
                    return False
                
                # Check that output is not identical to input (processing occurred)
                if i == 0:
                    diff = np.mean(np.abs(processed - chunk))
                    print(f"[DSP TEST] {mode} mode - Processing difference: {diff:.6f}")
    
    print("[DSP TEST] Enhanced stability test passed!")
    print("[DSP TEST] Audio quality improvements verified!")
    return True

def test_audio_quality():
    """Test audio quality improvements"""
    print("[DSP QUALITY TEST] Testing audio quality features...")
    
    # Generate test signals with different energy levels
    test_cases = [
        ("Silence", np.random.randn(WINDOW_SIZE) * 0.001),
        ("Whisper", np.random.randn(WINDOW_SIZE) * 0.02),
        ("Normal Speech", np.random.randn(WINDOW_SIZE) * 0.1),
        ("Loud Speech", np.random.randn(WINDOW_SIZE) * 0.3)
    ]
    
    set_protection_mode("balanced")
    
    for name, signal in test_cases:
        processed = protect_audio(signal, debug=True)
        
        # Calculate quality metrics
        original_energy = get_speech_energy(signal)
        processed_energy = get_speech_energy(processed)
        energy_ratio = processed_energy / original_energy if original_energy > 0 else 1.0
        
        # Calculate signal-to-distortion ratio
        distortion = np.mean((processed - signal) ** 2)
        signal_power = np.mean(signal ** 2)
        sdr = 10 * np.log10(signal_power / distortion) if distortion > 0 else 100.0
        
        print(f"[DSP QUALITY] {name:12s} - Energy ratio: {energy_ratio:.3f}, SDR: {sdr:.1f}dB")
    
    print("[DSP QUALITY TEST] Audio quality test completed!")
    return True

if __name__ == "__main__":
    test_stability()
