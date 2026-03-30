#!/usr/bin/env python3
"""
Audio Output Module for VoxShield
Handles continuous audio output with proper buffering
"""
import numpy as np
import time
import threading
from collections import deque

class AudioOutput:
    def __init__(self, buffer_size=10):
        """
        Initialize audio output manager
        
        Args:
            buffer_size: Number of audio chunks to buffer
        """
        self.buffer_size = buffer_size
        self.output_buffer = deque(maxlen=buffer_size)
        self.running = False
        self.output_thread = None
        self.total_chunks_output = 0
        self.last_output_time = time.time()
        
    def add_chunk(self, audio_chunk):
        """
        Add processed audio chunk to output buffer
        
        Args:
            audio_chunk: Processed audio data
        """
        if self.running:
            self.output_buffer.append(audio_chunk.copy())
    
    def start_output(self):
        """Start continuous output processing"""
        if self.running:
            print("[AUDIO OUTPUT] Output already running")
            return
            
        print("[AUDIO OUTPUT] Starting continuous audio output...")
        self.running = True
        self.total_chunks_output = 0
        self.last_output_time = time.time()
        
        # Start output processing thread
        self.output_thread = threading.Thread(target=self._output_loop, daemon=True)
        self.output_thread.start()
        print("[AUDIO OUTPUT] Output processing started")
    
    def stop_output(self):
        """Stop audio output processing"""
        if not self.running:
            print("[AUDIO OUTPUT] Output already stopped")
            return
            
        print("[AUDIO OUTPUT] Stopping audio output...")
        self.running = False
        
        # Wait for thread to finish
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=1.0)
        
        # Clear buffer
        self.output_buffer.clear()
        print(f"[AUDIO OUTPUT] Output stopped - Total chunks output: {self.total_chunks_output}")
    
    def _output_loop(self):
        """Continuous output processing loop"""
        while self.running:
            try:
                if len(self.output_buffer) > 0:
                    # Get next chunk from buffer
                    chunk = self.output_buffer.popleft()
                    
                    # Process output (in real implementation, this would send to audio device)
                    self.total_chunks_output += 1
                    
                    # Debug logging every 500 chunks
                    if self.total_chunks_output % 500 == 0:
                        current_time = time.time()
                        elapsed = current_time - self.last_output_time
                        chunks_per_sec = 500 / elapsed if elapsed > 0 else 0
                        max_amp = np.max(np.abs(chunk))
                        rms = np.sqrt(np.mean(chunk**2))
                        print(f"[AUDIO OUTPUT] Chunk #{self.total_chunks_output}, Rate: {chunks_per_sec:.1f}/sec, Max: {max_amp:.3f}, RMS: {rms:.3f}")
                        self.last_output_time = current_time
                else:
                    # No data in buffer, brief sleep
                    time.sleep(0.001)
                    
            except Exception as e:
                print(f"[AUDIO OUTPUT ERROR] Output loop error: {e}")
                time.sleep(0.01)
    
    def get_stats(self):
        """Get output statistics"""
        return {
            'running': self.running,
            'buffer_size': len(self.output_buffer),
            'total_chunks': self.total_chunks_output,
            'max_buffer': self.buffer_size
        }
    
    def is_healthy(self):
        """Check if output system is healthy"""
        if not self.running:
            return True  # Not running is considered healthy
            
        # Check if buffer is not overflowing
        buffer_health = len(self.output_buffer) < self.buffer_size * 0.8
        
        # Check if we're actually outputting data
        current_time = time.time()
        recent_output = (current_time - self.last_output_time) < 5.0 if self.total_chunks_output > 0 else True
        
        return buffer_health and recent_output

# Global instance for the application
audio_output = AudioOutput()

if __name__ == "__main__":
    # Test the audio output
    print("[AUDIO OUTPUT] Testing audio output...")
    
    try:
        audio_output.start_output()
        
        # Simulate adding audio chunks
        print("[AUDIO OUTPUT] Adding test chunks...")
        for i in range(50):
            test_chunk = np.random.randn(512, 2).astype(np.float32) * 0.1
            audio_output.add_chunk(test_chunk)
            time.sleep(0.01)
        
        print("[AUDIO OUTPUT] Running for 3 seconds...")
        time.sleep(3)
        
        audio_output.stop_output()
        print("[AUDIO OUTPUT] Test completed")
        
    except KeyboardInterrupt:
        print("[AUDIO OUTPUT] Test interrupted")
        audio_output.stop_output()
