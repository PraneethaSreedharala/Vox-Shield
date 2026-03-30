#!/usr/bin/env python3
"""
Test script for continuous audio streaming
"""
import time
import os
import sys
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from audio_capture import audio_capture
from audio_output import audio_output

def test_continuous_stream():
    """Test continuous streaming for 5 seconds"""
    print("Testing continuous audio streaming...")
    
    try:
        # Start audio capture
        print("1. Starting audio capture...")
        audio_capture.start_stream()
        
        # Start audio output
        print("2. Starting audio output...")
        audio_output.start_output()
        
        print("3. Streaming for 5 seconds...")
        start_time = time.time()
        
        # Simulate adding processed audio chunks to output
        chunk_count = 0
        while time.time() - start_time < 5.0:
            # Simulate processed audio chunk
            test_chunk = np.random.randn(512, 2).astype(np.float32) * 0.1
            audio_output.add_chunk(test_chunk)
            chunk_count += 1
            
            # Print status every second
            if chunk_count % 100 == 0:
                capture_stats = audio_capture.get_stats()
                output_stats = audio_output.get_stats()
                print(f"   Status - Capture callbacks: {capture_stats['callbacks']}, Output chunks: {output_stats['total_chunks']}")
            
            time.sleep(0.01)  # 100Hz chunk generation
        
        print(f"4. Generated {chunk_count} test chunks in 5 seconds")
        
        # Get final stats
        final_capture = audio_capture.get_stats()
        final_output = audio_output.get_stats()
        
        print(f"Final Stats:")
        print(f"   Audio Capture: {final_capture['callbacks']} callbacks processed")
        print(f"   Audio Output: {final_output['total_chunks']} chunks processed")
        print(f"   Capture Rate: {final_capture['callbacks']/5:.1f} callbacks/sec")
        print(f"   Output Rate: {final_output['total_chunks']/5:.1f} chunks/sec")
        
        # Stop streams
        print("5. Stopping streams...")
        audio_capture.stop_stream()
        audio_output.stop_output()
        
        print("Continuous streaming test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        try:
            audio_capture.stop_stream()
            audio_output.stop_output()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_continuous_stream()
    sys.exit(0 if success else 1)
