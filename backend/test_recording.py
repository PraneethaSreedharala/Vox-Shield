#!/usr/bin/env python3
"""
Test audio recording functionality
"""
import numpy as np
import time
import os
from audio_recorder import audio_recorder
from dsp_engine import protect_audio, set_protection_mode

def test_audio_recording():
    """Test complete audio recording pipeline"""
    print("Testing Audio Recording System...")
    
    # Set protection mode to active
    set_protection_mode('balanced')
    state_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.protection_state'))
    with open(state_file, 'w') as f:
        f.write('1')
    
    print("Starting recording test...")
    
    # Start recording
    audio_recorder.start_recording()
    
    # Simulate 3 seconds of audio processing
    sample_rate = 44100
    chunk_size = 512
    num_chunks = int(3.0 * sample_rate / chunk_size)  # 3 seconds worth
    
    print(f"Simulating {num_chunks} audio chunks (3 seconds)...")
    
    for i in range(num_chunks):
        # Create test signal with varying frequency
        t = np.linspace(0, chunk_size/sample_rate, chunk_size)
        
        # Create a more realistic speech-like signal
        base_freq = 150 + (i % 20) * 25  # 150-650 Hz range (speech range)
        signal = (
            np.sin(2 * np.pi * base_freq * t) * 0.4 +  # Fundamental
            np.sin(2 * np.pi * base_freq * 2 * t) * 0.2 +  # First harmonic
            np.sin(2 * np.pi * base_freq * 3 * t) * 0.1    # Second harmonic
        )
        
        # Add some noise for realism
        signal += np.random.randn(len(signal)) * 0.02
        
        # Create stereo signal
        stereo_signal = np.column_stack([signal, signal])
        
        # Process through DSP
        processed = protect_audio(stereo_signal.copy(), debug=False)
        
        # Add to recording buffer
        audio_recorder.add_audio_chunk(stereo_signal, processed)
        
        # Show progress
        if i % 100 == 0:
            current_time = i * chunk_size / sample_rate
            rec_info = audio_recorder.get_recording_info()
            if rec_info:
                print(f"  Time: {current_time:.1f}s, Chunks: {rec_info['chunks_recorded']}, Duration: {rec_info['current_duration']:.1f}s")
    
    # Stop recording and save
    print("Stopping recording...")
    raw_file, protected_file = audio_recorder.stop_recording()
    
    if raw_file and protected_file:
        print(f"\nRecording successful!")
        print(f"Raw file: {raw_file}")
        print(f"Protected file: {protected_file}")
        
        # Check file sizes
        raw_size = os.path.getsize(raw_file) / (1024 * 1024)  # MB
        protected_size = os.path.getsize(protected_file) / (1024 * 1024)  # MB
        
        print(f"Raw file size: {raw_size:.2f} MB")
        print(f"Protected file size: {protected_size:.2f} MB")
        
        # Verify files are playable (check WAV format)
        try:
            from scipy.io.wavfile import read as wav_read
            
            # Read raw file
            raw_rate, raw_data = wav_read(raw_file)
            print(f"Raw file: {raw_rate} Hz, {raw_data.shape}, {raw_data.dtype}")
            
            # Read protected file
            protected_rate, protected_data = wav_read(protected_file)
            print(f"Protected file: {protected_rate} Hz, {protected_data.shape}, {protected_data.dtype}")
            
            # Check sample rate
            if raw_rate == sample_rate and protected_rate == sample_rate:
                print("Sample rates correct!")
            else:
                print("Sample rate mismatch!")
            
            # Check data type
            if raw_data.dtype == np.int16 and protected_data.dtype == np.int16:
                print("Data types correct (int16)!")
            else:
                print("Data type issue!")
            
            # Check duration
            raw_duration = len(raw_data) / raw_rate
            protected_duration = len(protected_data) / protected_rate
            
            print(f"Raw duration: {raw_duration:.2f} seconds")
            print(f"Protected duration: {protected_duration:.2f} seconds")
            
            if abs(raw_duration - protected_duration) < 0.1:
                print("Durations match!")
            else:
                print("Duration mismatch!")
            
            return True
            
        except Exception as e:
            print(f"Error verifying files: {e}")
            return False
    else:
        print("Recording failed - no files saved")
        return False

def test_export_directory():
    """Test export directory creation and file management"""
    print("\nTesting Export Directory...")
    
    exports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exports'))
    print(f"Export directory: {exports_dir}")
    
    # Check if directory exists
    if os.path.exists(exports_dir):
        print("Export directory exists")
        
        # List files
        files = os.listdir(exports_dir)
        wav_files = [f for f in files if f.endswith('.wav')]
        
        print(f"Total files: {len(files)}")
        print(f"WAV files: {len(wav_files)}")
        
        if wav_files:
            print("WAV files found:")
            for file in wav_files[:5]:  # Show first 5
                file_path = os.path.join(exports_dir, file)
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                print(f"  {file} ({size:.2f} MB) - {mod_time}")
        else:
            print("No WAV files found")
    else:
        print("Export directory does not exist (will be created when recording)")

def test_recording_limits():
    """Test recording duration limits"""
    print("\nTesting Recording Duration Limits...")
    
    # Create a recorder with 5-second limit
    test_recorder = audio_recorder.__class__(max_duration=5)
    
    test_recorder.start_recording()
    
    # Simulate 7 seconds of audio (should stop at 5)
    sample_rate = 44100
    chunk_size = 512
    num_chunks = int(7.0 * sample_rate / chunk_size)
    
    recorded_chunks = 0
    for i in range(num_chunks):
        if not test_recorder.is_recording:
            print(f"Recording stopped automatically at chunk {i}")
            break
        
        # Add dummy audio
        dummy_audio = np.random.randn(chunk_size, 2) * 0.1
        test_recorder.add_audio_chunk(dummy_audio, dummy_audio)
        recorded_chunks += 1
    
    # Check actual duration
    actual_duration = recorded_chunks * chunk_size / sample_rate
    print(f"Recorded duration: {actual_duration:.2f} seconds")
    print(f"Expected max: 5.00 seconds")
    
    if actual_duration <= 5.5:  # Allow some tolerance
        print("Duration limit working correctly!")
        return True
    else:
        print("Duration limit not working!")
        return False

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("VOXSHIELD AUDIO RECORDING TEST SUITE")
        print("=" * 60)
        
        # Test recording functionality
        success1 = test_audio_recording()
        
        # Test export directory
        test_export_directory()
        
        # Test recording limits
        success3 = test_recording_limits()
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        if success1:
            print("Audio recording: PASSED")
        else:
            print("Audio recording: FAILED")
        
        if success3:
            print("Duration limits: PASSED")
        else:
            print("Duration limits: FAILED")
        
        if success1 and success3:
            print("\nAll recording tests PASSED!")
            print("Audio files are ready for vulnerability testing!")
        else:
            print("\nSome tests FAILED - check implementation")
        
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
