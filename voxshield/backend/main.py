import sounddevice as sd
import numpy as np
import time
import os
from dsp_engine import protect_audio

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))
TIMEOUT_SECONDS = 120  # 2 minutes max session

def process_audio(indata, outdata, frames, time_info, status):
    # Pass straight to DSP (which ALSO checks the state, but we only open stream if active)
    outdata[:] = protect_audio(indata, debug=True)

def get_state():
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "0"

def main():
    print("VoxShield Backend Started. Waiting for UI trigger...")
    start_time = time.time()
    stream = None
    
    try:
        while True:
            # 1. Safety Timeout
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                print("Safety timeout reached (2 mins). Shutting down backend.")
                break
                
            # 2. Check Communication State
            state = get_state()
            
            # 3. Manual Override / Exit
            if state == "-1":
                print("Exit signal received from UI. Terminating backend immediately.")
                break
                
            # 4. Handle Protection Lifecycle
            if state == "1":
                if stream is None:
                    print("Initializing microphone stream... Protection ACTIVE.")
                    stream = sd.Stream(callback=process_audio, blocksize=512, channels=2, dtype='float32')
                    stream.start()
            else:
                if stream is not None:
                    print("Releasing microphone stream... Protection INACTIVE.")
                    stream.stop()
                    stream.close()
                    stream = None
                    
            # Heartbeat / Polling interval
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nManual interrupt via Keyboard. Exiting.")
    finally:
        # Cleanup
        if stream is not None:
            stream.stop()
            stream.close()
            print("Microphone released successfully.")
        
        # Reset state to default Idle so next launch is clean
        try:
            with open(STATE_FILE, "w") as f:
                f.write("0")
        except:
            pass
        print("Backend shutting down.")

if __name__ == "__main__":
    main()