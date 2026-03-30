#!/usr/bin/env python3
"""
Debug script for DSP engine
"""
import numpy as np
import os
from dsp_engine import protect_audio, set_protection_mode

# Create test signal
signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 512)) * 0.5

# Set protection mode
set_protection_mode('balanced')

# Create state file to activate protection
state_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.protection_state'))
with open(state_file, 'w') as f:
    f.write('1')

print("Testing DSP with active protection...")
processed = protect_audio(signal, debug=True)

diff = np.mean(np.abs(processed - signal))
print(f'Difference: {diff:.8f}')
print(f'Original max: {np.max(np.abs(signal)):.4f}')
print(f'Processed max: {np.max(np.abs(processed)):.4f}')

# Test with high protection mode
set_protection_mode('high')
processed_high = protect_audio(signal, debug=True)
diff_high = np.mean(np.abs(processed_high - signal))
print(f'High mode difference: {diff_high:.8f}')

# Clean up
with open(state_file, 'w') as f:
    f.write('0')
