import numpy as np
import os
import time

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".protection_state"))

_last_check = 0
_is_active = False

def check_active():
    global _last_check, _is_active
    now = time.time()
    if now - _last_check > 0.5:  # Read file every 0.5s to avoid heavy I/O
        _last_check = now
        try:
            with open(STATE_FILE, "r") as f:
                _is_active = (f.read().strip() == "1")
        except:
            _is_active = False
    return _is_active

def protect_audio(audio):
    if not check_active():
        return audio  # Return raw mic input when protection is OFF

    noise = np.random.normal(0, 0.002, audio.shape)
    return audio * 0.98 + noise