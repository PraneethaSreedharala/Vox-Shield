#!/usr/bin/env python3
"""
Test real-time visualization system
"""
import numpy as np
import time
import os
from audio_data_share import audio_data_share
from dsp_engine import protect_audio, set_protection_mode

def test_realtime_updates():
    """Test real-time audio data updates"""
    print("Testing Real-Time Audio Visualization...")
    
    # Set protection mode to active
    set_protection_mode('balanced')
    state_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.protection_state'))
    with open(state_file, 'w') as f:
        f.write('1')
    
    print("Simulating real-time audio processing...")
    
    # Simulate 5 seconds of audio processing
    sample_rate = 44100
    chunk_size = 512
    
    for i in range(100):  # 100 chunks = ~1.16 seconds
        # Create test signal with varying frequency
        t = np.linspace(0, chunk_size/sample_rate, chunk_size)
        
        # Vary frequency over time to show dynamic changes
        base_freq = 200 + (i % 50) * 20  # 200-1200 Hz range
        signal = np.sin(2 * np.pi * base_freq * t) * 0.3
        
        # Add some harmonics
        signal += np.sin(2 * np.pi * base_freq * 2 * t) * 0.1
        signal += np.sin(2 * np.pi * base_freq * 3 * t) * 0.05
        
        # Create stereo signal
        stereo_signal = np.column_stack([signal, signal])
        
        # Process through DSP
        processed = protect_audio(stereo_signal.copy(), debug=False)
        
        # Update shared data
        audio_data_share.update_audio_data(stereo_signal, processed)
        
        # Get visualization data
        freqs, raw_mag, processed_mag = audio_data_share.get_visualization_data(max_freq=4000)
        
        if freqs is not None and i % 10 == 0:
            # Check signal levels
            max_raw = np.max(np.abs(raw_mag))
            max_processed = np.max(np.abs(processed_mag))
            
            # Calculate difference
            spectral_diff = np.mean(np.abs(processed_mag - raw_mag))
            
            print(f"Chunk {i:3d}: Freq={base_freq:4.0f}Hz, RawMax={max_raw:.3f}, "
                  f"ProcMax={max_processed:.3f}, Diff={spectral_diff:.4f}")
        
        # Small delay to simulate real-time processing
        time.sleep(0.0116)  # 512/44100 ≈ 0.0116 seconds per chunk
    
    # Get final statistics
    stats = audio_data_share.get_update_stats()
    print(f"\nFinal Statistics:")
    print(f"  Total Updates: {stats['update_count']}")
    print(f"  Updates/sec: {stats['updates_per_second']:.1f}")
    print(f"  Max Signal Level: {stats['max_signal_level']:.4f}")
    
    # Test frequency resolution
    freqs, _, _ = audio_data_share.get_visualization_data(max_freq=4000)
    if freqs is not None:
        print(f"  Frequency Points: {len(freqs)}")
        print(f"  Frequency Range: {np.min(freqs):.1f} - {np.max(freqs):.1f} Hz")
        print(f"  Frequency Resolution: {freqs[1] - freqs[0]:.1f} Hz")
    
    # Clean up
    with open(state_file, 'w') as f:
        f.write('0')
    
    print("\nReal-time test completed successfully!")
    return True

def test_signal_detection():
    """Test signal detection and visualization"""
    print("\nTesting Signal Detection...")
    
    # Test with known frequency patterns
    test_patterns = [
        ("Silence", np.zeros(512)),
        ("Low Freq", np.sin(2 * np.pi * 100 * np.linspace(0, 512/44100, 512)) * 0.5),
        ("Speech Freq", np.sin(2 * np.pi * 440 * np.linspace(0, 512/44100, 512)) * 0.5),
        ("High Freq", np.sin(2 * np.pi * 2000 * np.linspace(0, 512/44100, 512)) * 0.5),
        ("Complex Mix", 
            np.sin(2 * np.pi * 200 * np.linspace(0, 512/44100, 512)) * 0.3 +
            np.sin(2 * np.pi * 400 * np.linspace(0, 512/44100, 512)) * 0.2 +
            np.sin(2 * np.pi * 800 * np.linspace(0, 512/44100, 512)) * 0.1
        )
    ]
    
    for name, signal in test_patterns:
        # Create stereo signal
        stereo_signal = np.column_stack([signal, signal])
        
        # Update shared data
        audio_data_share.update_audio_data(stereo_signal, stereo_signal)
        
        # Get visualization data
        freqs, raw_mag, processed_mag = audio_data_share.get_visualization_data(max_freq=4000)
        
        if freqs is not None:
            max_raw = np.max(np.abs(raw_mag))
            
            # Find peak frequencies
            peak_indices = np.where(raw_mag > 0.5 * max_raw)[0]
            if len(peak_indices) > 0:
                peak_freqs = freqs[peak_indices[:3]]  # Top 3 peaks
                print(f"{name:12s}: Max={max_raw:.3f}, Peaks at {peak_freqs}")
            else:
                print(f"{name:12s}: Max={max_raw:.3f}, No significant peaks")
    
    print("Signal detection test completed!")

if __name__ == "__main__":
    try:
        test_realtime_updates()
        test_signal_detection()
        print("\nAll real-time tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
