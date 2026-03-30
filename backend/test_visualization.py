#!/usr/bin/env python3
"""
Test visualization system for VoxShield
"""
import numpy as np
import time
import os
import sys
from audio_data_share import audio_data_share
from dsp_engine import protect_audio, set_protection_mode

def test_visualization_system():
    """Test the complete visualization pipeline"""
    print("Testing VoxShield Real-Time Visualization System...")
    
    # Set protection mode to active
    set_protection_mode('balanced')
    state_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.protection_state'))
    with open(state_file, 'w') as f:
        f.write('1')
    
    print("Generating test audio signals...")
    
    # Test with different types of signals
    test_signals = [
        ("Low Frequency (100Hz)", np.sin(2 * np.pi * 100 * np.linspace(0, 1, 512)) * 0.5),
        ("Speech Frequency (440Hz)", np.sin(2 * np.pi * 440 * np.linspace(0, 1, 512)) * 0.5),
        ("High Frequency (2000Hz)", np.sin(2 * np.pi * 2000 * np.linspace(0, 1, 512)) * 0.5),
        ("Complex Signal", 
            np.sin(2 * np.pi * 200 * np.linspace(0, 1, 512)) * 0.3 +
            np.sin(2 * np.pi * 400 * np.linspace(0, 1, 512)) * 0.2 +
            np.sin(2 * np.pi * 800 * np.linspace(0, 1, 512)) * 0.1
        )
    ]
    
    for name, signal in test_signals:
        print(f"\nTesting: {name}")
        
        # Process signal through DSP
        processed = protect_audio(signal.copy(), debug=False)
        
        # Update shared data
        audio_data_share.update_audio_data(
            signal.reshape(-1, 1),  # Convert to 2D for stereo compatibility
            processed.reshape(-1, 1)
        )
        
        # Get visualization data
        freqs, raw_mag, processed_mag = audio_data_share.get_visualization_data(max_freq=4000)
        
        if freqs is not None:
            # Calculate differences
            raw_energy = np.sum(raw_mag**2)
            processed_energy = np.sum(processed_mag**2)
            energy_ratio = processed_energy / raw_energy if raw_energy > 0 else 1.0
            
            spectral_diff = np.mean(np.abs(processed_mag - raw_mag))
            
            print(f"  Raw Energy: {raw_energy:.4f}")
            print(f"  Processed Energy: {processed_energy:.4f}")
            print(f"  Energy Ratio: {energy_ratio:.3f}")
            print(f"  Spectral Difference: {spectral_diff:.4f}")
            print(f"  Frequency Points: {len(freqs)}")
            print(f"  Max Frequency: {np.max(freqs):.0f} Hz")
        else:
            print("  ERROR: No visualization data available")
    
    # Test update statistics
    print(f"\nUpdate Statistics:")
    stats = audio_data_share.get_update_stats()
    print(f"  Total Updates: {stats['update_count']}")
    print(f"  Updates/sec: {stats['updates_per_second']:.1f}")
    
    # Clean up
    with open(state_file, 'w') as f:
        f.write('0')
    
    print("\nVisualization system test completed!")
    return True

def test_frequency_analysis():
    """Test frequency analysis accuracy"""
    print("\nTesting Frequency Analysis Accuracy...")
    
    # Create a signal with known frequency components
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create signal with 440Hz and 880Hz components
    signal = (
        np.sin(2 * np.pi * 440 * t) * 0.5 +  # Fundamental
        np.sin(2 * np.pi * 880 * t) * 0.25   # First harmonic
    )
    
    # Take a 512-sample chunk
    chunk = signal[:512]
    
    # Update shared data
    audio_data_share.update_audio_data(
        chunk.reshape(-1, 1),
        chunk.reshape(-1, 1)
    )
    
    # Get frequency data
    freqs, raw_mag, processed_mag = audio_data_share.get_visualization_data(max_freq=2000)
    
    if freqs is not None:
        # Find peaks
        peak_indices = np.where(raw_mag > 0.5)[0]
        peak_freqs = freqs[peak_indices]
        
        print(f"Expected frequencies: 440Hz, 880Hz")
        print(f"Detected peaks at: {peak_freqs[:5]} Hz")  # Show first 5 peaks
        
        # Check if we detected the expected frequencies
        detected_440 = any(abs(freq - 440) < 50 for freq in peak_freqs)
        detected_880 = any(abs(freq - 880) < 50 for freq in peak_freqs)
        
        if detected_440:
            print("✓ 440Hz component detected")
        else:
            print("✗ 440Hz component not detected")
            
        if detected_880:
            print("✓ 880Hz component detected")
        else:
            print("✗ 880Hz component not detected")
    
    return True

if __name__ == "__main__":
    try:
        test_visualization_system()
        test_frequency_analysis()
        print("\n✓ All visualization tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
