#!/usr/bin/env python3
"""
Audio Recording Module for VoxShield
Records and saves raw and protected audio for analysis
"""
import numpy as np
import time
import os
from scipy.io.wavfile import write
from datetime import datetime

class AudioRecorder:
    def __init__(self, sample_rate=44100, max_duration=30):
        self.sample_rate = sample_rate
        self.max_duration = max_duration  # Maximum recording duration in seconds
        self.max_samples = sample_rate * max_duration
        
        # Recording buffers
        self.raw_buffer = []
        self.processed_buffer = []
        self.is_recording = False
        self.start_time = None
        
        # Export settings
        self.export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exports'))
        self.ensure_export_dir()
        
    def ensure_export_dir(self):
        """Create export directory if it doesn't exist"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            print(f"[RECORDER] Created export directory: {self.export_dir}")
    
    def start_recording(self):
        """Start recording audio"""
        self.raw_buffer = []
        self.processed_buffer = []
        self.is_recording = True
        self.start_time = time.time()
        print(f"[RECORDER] Started recording (max {self.max_duration}s)")
    
    def stop_recording(self):
        """Stop recording and save audio"""
        if not self.is_recording:
            return None, None
        
        self.is_recording = False
        end_time = time.time()
        duration = end_time - self.start_time
        
        print(f"[RECORDER] Stopped recording after {duration:.2f}s")
        
        # Check if we have any audio data
        if len(self.raw_buffer) == 0 or len(self.processed_buffer) == 0:
            print("[RECORDER] No audio data to save")
            return None, None
        
        # Combine buffers
        try:
            raw_audio = np.concatenate(self.raw_buffer, axis=0)
            processed_audio = np.concatenate(self.processed_buffer, axis=0)
            
            print(f"[RECORDER] Combined audio - Raw: {raw_audio.shape}, Processed: {processed_audio.shape}")
            
            # Save audio files
            raw_file, protected_file = self.save_audio_files(raw_audio, processed_audio)
            
            return raw_file, protected_file
            
        except Exception as e:
            print(f"[RECORDER] Error combining audio: {e}")
            return None, None
    
    def add_audio_chunk(self, raw_chunk, processed_chunk):
        """Add audio chunks to recording buffers"""
        if not self.is_recording:
            return
        
        try:
            # Add chunks to buffers
            self.raw_buffer.append(raw_chunk.copy())
            self.processed_buffer.append(processed_chunk.copy())
            
            # Check maximum duration
            total_samples = sum(len(chunk) for chunk in self.raw_buffer)
            if total_samples >= self.max_samples:
                print(f"[RECORDER] Maximum duration reached ({self.max_duration}s)")
                self.stop_recording()
                
        except Exception as e:
            print(f"[RECORDER] Error adding audio chunk: {e}")
    
    def save_audio_files(self, raw_audio, processed_audio):
        """Save raw and processed audio to WAV files"""
        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # File paths
            raw_file = os.path.join(self.export_dir, f"raw_audio_{timestamp}.wav")
            protected_file = os.path.join(self.export_dir, f"protected_audio_{timestamp}.wav")
            
            # Convert to int16 for WAV format (standard audio format)
            def normalize_to_int16(audio):
                """Normalize audio to int16 range"""
                if len(audio.shape) > 1:
                    # Stereo - normalize each channel
                    max_val = np.max(np.abs(audio))
                    if max_val > 0:
                        normalized = audio / max_val
                    else:
                        normalized = audio
                    return (normalized * 32767).astype(np.int16)
                else:
                    # Mono
                    max_val = np.max(np.abs(audio))
                    if max_val > 0:
                        normalized = audio / max_val
                    else:
                        normalized = audio
                    return (normalized * 32767).astype(np.int16)
            
            # Normalize and convert
            raw_int16 = normalize_to_int16(raw_audio)
            processed_int16 = normalize_to_int16(processed_audio)
            
            # Save files
            write(raw_file, self.sample_rate, raw_int16)
            write(protected_file, self.sample_rate, processed_int16)
            
            # Get file sizes
            raw_size = os.path.getsize(raw_file) / (1024 * 1024)  # MB
            protected_size = os.path.getsize(protected_file) / (1024 * 1024)  # MB
            
            print(f"[RECORDER] Saved audio files:")
            print(f"  Raw: {raw_file} ({raw_size:.2f} MB)")
            print(f"  Protected: {protected_file} ({protected_size:.2f} MB)")
            
            return raw_file, protected_file
            
        except Exception as e:
            print(f"[RECORDER] Error saving audio files: {e}")
            return None, None
    
    def get_recording_info(self):
        """Get current recording information"""
        if not self.is_recording:
            return None
        
        current_time = time.time()
        duration = current_time - self.start_time
        
        total_samples = sum(len(chunk) for chunk in self.raw_buffer)
        current_duration = total_samples / self.sample_rate
        
        return {
            'duration': duration,
            'current_duration': current_duration,
            'total_samples': total_samples,
            'chunks_recorded': len(self.raw_buffer)
        }
    
    def clear_buffers(self):
        """Clear recording buffers"""
        self.raw_buffer = []
        self.processed_buffer = []
        print("[RECORDER] Cleared recording buffers")

# Global recorder instance
audio_recorder = AudioRecorder()
