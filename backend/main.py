import sounddevice as sd
import numpy as np
import time
import os
from audio_capture import audio_capture
from audio_output import audio_output
from audio_recorder import audio_recorder

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))
TIMEOUT_SECONDS = 120  # 2 minutes max session

def main():
    print("VoxShield Backend Started. Waiting for UI trigger...")
    start_time = time.time()
    stream_active = False
    
    try:
        while True:
            # 1. Safety Timeout
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                print("Safety timeout reached (2 mins). Shutting down backend.")
                break
                
            # 2. Check Communication State
            try:
                with open(STATE_FILE, "r") as f:
                    state = f.read().strip()
            except Exception:
                state = "0"
            
            # 3. Manual Override / Exit
            if state == "-1":
                print("Exit signal received from UI. Terminating backend immediately.")
                break
                
            # 4. Handle Protection Lifecycle
            if state == "1":
                if not stream_active:
                    print("Starting continuous audio stream... Protection ACTIVE.")
                    try:
                        # Start continuous audio capture
                        audio_capture.start_stream()
                        
                        # Start audio output processing
                        audio_output.start_output()
                        
                        # Start recording for analysis
                        audio_recorder.start_recording()
                        
                        stream_active = True
                        print("Audio streaming started successfully!")
                        print("Audio recording started for analysis...")
                        
                    except Exception as e:
                        print(f"Failed to start audio stream: {e}")
                        stream_active = False
                        
            else:
                if stream_active:
                    print("Stopping continuous audio stream... Protection INACTIVE.")
                    try:
                        # Stop audio capture
                        audio_capture.stop_stream()
                        
                        # Stop audio output
                        audio_output.stop_output()
                        
                        # Stop recording and save audio files
                        raw_file, protected_file = audio_recorder.stop_recording()
                        
                        stream_active = False
                        print("Audio streaming stopped successfully!")
                        
                        if raw_file and protected_file:
                            print("Audio recording saved successfully for testing!")
                            print(f"Files saved in: {os.path.dirname(raw_file)}")
                        else:
                            print("No audio recording to save.")
                        
                    except Exception as e:
                        print(f"Error stopping audio stream: {e}")
                        stream_active = False
            
            # 5. Status Updates (periodic)
            if stream_active and audio_capture.callback_count % 1000 == 0 and audio_capture.callback_count > 0:
                capture_stats = audio_capture.get_stats()
                output_stats = audio_output.get_stats()
                print(f"[STATUS] Capture: {capture_stats['callbacks']} callbacks, Output: {output_stats['total_chunks']} chunks")
                    
            # Heartbeat / Polling interval
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nManual interrupt via Keyboard. Exiting.")
    finally:
        # Cleanup
        if stream_active:
            print("Cleaning up audio streams...")
            try:
                audio_capture.stop_stream()
                audio_output.stop_output()
                
                # Stop recording and save audio files on shutdown
                raw_file, protected_file = audio_recorder.stop_recording()
                
                print("Audio streams cleaned up successfully.")
                
                if raw_file and protected_file:
                    print("Audio recording saved successfully for testing!")
                    print(f"Files saved in: {os.path.dirname(raw_file)}")
                
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        # Reset state to default Idle so next launch is clean
        try:
            with open(STATE_FILE, "w") as f:
                f.write("0")
        except:
            pass
        print("Backend shutting down.")

if __name__ == "__main__":
    main()