#!/usr/bin/env python3
"""
Shared audio data module for frontend visualization
Provides thread-safe access to real-time audio data
"""
import numpy as np
import threading
import time
from scipy.fft import rfft, rfftfreq

class AudioDataShare:
    def __init__(self, sample_rate=44100, fft_size=512):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        
        # Shared data buffers
        self.raw_audio = None
        self.processed_audio = None
        self.raw_fft = None
        self.processed_fft = None
        self.frequencies = None
        
        # Thread safety
        self.data_lock = threading.Lock()
        
        # Pre-compute frequency bins
        self.frequencies = rfftfreq(fft_size, 1/sample_rate)
        
        # Update tracking
        self.last_update = time.time()
        self.update_count = 0
        self.max_signal_level = 0.0
        
    def update_audio_data(self, raw_chunk, processed_chunk):
        """Update audio data and compute FFT"""
        if raw_chunk is None or processed_chunk is None:
            return
            
        with self.data_lock:
            self.raw_audio = raw_chunk.copy()
            self.processed_audio = processed_chunk.copy()
            
            # Use first channel if stereo
            if len(raw_chunk.shape) > 1:
                raw_mono = raw_chunk[:, 0]
                processed_mono = processed_chunk[:, 0]
            else:
                raw_mono = raw_chunk.flatten()
                processed_mono = processed_chunk.flatten()
            
            # Apply window to reduce spectral leakage
            window = np.hanning(len(raw_mono))
            raw_windowed = raw_mono * window
            processed_windowed = processed_mono * window
            
            # Compute FFT using scipy for better performance
            raw_fft_data = rfft(raw_windowed)
            processed_fft_data = rfft(processed_windowed)
            
            # Get magnitudes (already positive frequencies only)
            self.raw_fft = np.abs(raw_fft_data)
            self.processed_fft = np.abs(processed_fft_data)
            
            # Track maximum signal level
            current_max = np.max(np.abs(raw_mono))
            if current_max > self.max_signal_level:
                self.max_signal_level = current_max
            
            # Normalize for visualization (only if signal is present)
            max_raw = np.max(self.raw_fft)
            max_processed = np.max(self.processed_fft)
            
            if max_raw > 0.001:  # Only normalize if we have meaningful signal
                self.raw_fft = self.raw_fft / max_raw
                self.processed_fft = self.processed_fft / max_processed
            else:
                # Keep as-is for very low signals
                self.raw_fft = self.raw_fft / 0.001 if max_raw > 0 else self.raw_fft
                self.processed_fft = self.processed_fft / 0.001 if max_processed > 0 else self.processed_fft
            
            self.last_update = time.time()
            self.update_count += 1
    
    def get_visualization_data(self, max_freq=4000):
        """Get data suitable for visualization"""
        with self.data_lock:
            if self.raw_fft is None or self.processed_fft is None:
                return None, None, None
            
            # Limit frequency range
            freq_mask = self.frequencies <= max_freq
            freqs = self.frequencies[freq_mask]
            raw_magnitude = self.raw_fft[freq_mask]
            processed_magnitude = self.processed_fft[freq_mask]
            
            return freqs, raw_magnitude, processed_magnitude
    
    def get_update_stats(self):
        """Get update statistics"""
        with self.data_lock:
            current_time = time.time()
            time_diff = current_time - self.last_update
            updates_per_sec = self.update_count / (time_diff + 0.001) if time_diff > 0 else 0
            
            return {
                'last_update': self.last_update,
                'update_count': self.update_count,
                'updates_per_second': updates_per_sec,
                'max_signal_level': self.max_signal_level
            }
    
    def reset_stats(self):
        """Reset statistics"""
        with self.data_lock:
            self.update_count = 0
            self.max_signal_level = 0.0
            self.last_update = time.time()

# Global instance for sharing between backend and frontend
audio_data_share = AudioDataShare()
