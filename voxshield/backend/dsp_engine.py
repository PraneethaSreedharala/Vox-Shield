import numpy as np
import os
import time
from scipy import signal
from scipy.fft import fft, ifft

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))

_last_check = 0
_is_active = False

# Audio processing constants
SAMPLE_RATE = 44100
WINDOW_SIZE = 512
HOP_SIZE = 256
MAX_AMPLITUDE = 0.95  # Safety threshold
NOISE_SCALE = 0.005  # Much reduced adversarial noise strength for voice clarity

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
    Main audio protection function with voice priority
    """
    if not check_active():
        return audio  # Return raw mic input when protection is OFF
    
    try:
        # Debug logging
        if debug:
            debug_audio_stats(audio, 0)
        
        # Step 1: Very gentle noise addition only (minimal processing)
        noise = np.random.normal(0, NOISE_SCALE, audio.shape)
        with_noise = audio + noise
        
        # Step 2: Simple normalization to prevent clipping
        max_val = np.max(np.abs(with_noise))
        if max_val > 0:
            normalized = with_noise / max_val * min(max_val, MAX_AMPLITUDE)
        else:
            normalized = with_noise
        
        # Step 3: Final clipping protection
        final_output = np.clip(normalized, -1.0, 1.0)
        
        # Debug final output
        if debug:
            debug_audio_stats(final_output, 1)
        
        return final_output
        
    except Exception as e:
        print(f"[DSP ERROR] Processing failed: {e}")
        # Fallback to pass-through if processing fails
        return np.clip(audio, -1.0, 1.0)

# Legacy compatibility
def protect_audio_legacy(audio):
    """Legacy function for backward compatibility"""
    return protect_audio(audio)

# Test function
def test_stability():
    """Test the DSP engine for stability"""
    print("[DSP TEST] Testing audio processing stability...")
    
    # Generate test signal
    test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, SAMPLE_RATE)) * 0.5
    
    # Process multiple chunks
    for i in range(10):
        chunk = test_signal[i*WINDOW_SIZE:(i+1)*WINDOW_SIZE]
        if len(chunk) == WINDOW_SIZE:
            processed = protect_audio(chunk, debug=True)
            max_amp = np.max(np.abs(processed))
            if max_amp > 1.0:
                print(f"[DSP TEST FAIL] Clipping detected in chunk {i}")
                return False
    
    print("[DSP TEST] Stability test passed!")
    return True

if __name__ == "__main__":
    test_stability()
