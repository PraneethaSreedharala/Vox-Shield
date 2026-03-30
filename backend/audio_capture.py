#!/usr/bin/env python3
"""
Continuous Audio Capture Module for VoxShield
Maintains persistent audio stream until manually stopped
"""
import sounddevice as sd
import numpy as np
import time
import threading
from dsp_engine import protect_audio, check_active
from audio_data_share import audio_data_share
from audio_recorder import audio_recorder

class AudioCapture:
    def __init__(self, sample_rate=44100, blocksize=512, channels=2):
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.channels = channels
        self.stream = None
        self.running = False
        self.callback_count = 0
        self.last_callback_time = time.time()
        
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Continuous audio callback - never stops unless running=False"""
        try:
            self.callback_count += 1
            current_time = time.time()
            
            # Debug logging every 100 callbacks
            if self.callback_count % 100 == 0:
                elapsed = current_time - self.last_callback_time
                callbacks_per_sec = 100 / elapsed if elapsed > 0 else 0
                print(f"[AUDIO CAPTURE] Callback #{self.callback_count}, Rate: {callbacks_per_sec:.1f}/sec, Running: {self.running}")
                self.last_callback_time = current_time
            
            # Only process if protection is active and stream is running
            if self.running and check_active():
                # Process audio through DSP engine
                processed_audio = protect_audio(indata, debug=(self.callback_count % 500 == 0))
                
                # Share audio data for visualization
                audio_data_share.update_audio_data(indata, processed_audio)
                
                # Add to recording buffer if recording is active
                audio_recorder.add_audio_chunk(indata, processed_audio)
                
                # Write to output (this creates the output stream)
                outdata[:] = processed_audio
                
                # Debug occasional chunks
                if self.callback_count % 500 == 0:
                    max_amp = np.max(np.abs(processed_audio))
                    rms = np.sqrt(np.mean(processed_audio**2))
                    print(f"[AUDIO CAPTURE] Processed chunk - Max: {max_amp:.3f}, RMS: {rms:.3f}")
                    
                    # Show recording info if active
                    rec_info = audio_recorder.get_recording_info()
                    if rec_info:
                        print(f"[AUDIO CAPTURE] Recording: {rec_info['current_duration']:.1f}s, {rec_info['chunks_recorded']} chunks")
            else:
                # Pass through audio when protection is inactive
                # Still share data for visualization (showing no processing)
                audio_data_share.update_audio_data(indata, indata)
                outdata[:] = indata
                
        except Exception as e:
            print(f"[AUDIO CAPTURE ERROR] Callback failed: {e}")
            # Fallback to pass-through
            outdata[:] = indata
    
    def start_stream(self):
        """Start continuous audio stream"""
        if self.stream is not None:
            print("[AUDIO CAPTURE] Stream already exists")
            return
            
        print(f"[AUDIO CAPTURE] Starting stream - Sample Rate: {self.sample_rate}, Blocksize: {self.blocksize}, Channels: {self.channels}")
        
        self.running = True
        self.callback_count = 0
        
        try:
            # Create full-duplex stream (input and output)
            self.stream = sd.Stream(
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                channels=self.channels,
                dtype='float32',
                callback=self.audio_callback
            )
            
            self.stream.start()
            print("[AUDIO CAPTURE] Stream started successfully - Audio processing ACTIVE")
            
        except Exception as e:
            print(f"[AUDIO CAPTURE ERROR] Failed to start stream: {e}")
            self.running = False
            self.stream = None
            raise
    
    def stop_stream(self):
        """Stop audio stream gracefully"""
        if self.stream is None:
            print("[AUDIO CAPTURE] No stream to stop")
            return
            
        print("[AUDIO CAPTURE] Stopping stream...")
        self.running = False
        
        try:
            # Stop and close stream
            self.stream.stop()
            self.stream.close()
            print(f"[AUDIO CAPTURE] Stream stopped - Total callbacks processed: {self.callback_count}")
        except Exception as e:
            print(f"[AUDIO CAPTURE ERROR] Error stopping stream: {e}")
        finally:
            self.stream = None
    
    def is_active(self):
        """Check if stream is active"""
        return self.running and self.stream is not None and self.stream.active
    
    def get_stats(self):
        """Get streaming statistics"""
        return {
            'running': self.running,
            'callbacks': self.callback_count,
            'stream_active': self.stream.active if self.stream else False,
            'sample_rate': self.sample_rate,
            'blocksize': self.blocksize
        }

# Global instance for the application
audio_capture = AudioCapture()

if __name__ == "__main__":
    # Test the audio capture
    print("[AUDIO CAPTURE] Testing audio capture...")
    
    try:
        audio_capture.start_stream()
        print("[AUDIO CAPTURE] Audio capture running for 10 seconds...")
        time.sleep(10)
        audio_capture.stop_stream()
        print("[AUDIO CAPTURE] Test completed")
    except KeyboardInterrupt:
        print("[AUDIO CAPTURE] Test interrupted")
        audio_capture.stop_stream()
