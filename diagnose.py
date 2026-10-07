"""Run offline installation checks without loading the full model."""
import importlib.util
from pathlib import Path
import platform
import shutil
import struct
import sys
from local_model import LocalModel

print('PRIYAN LOCAL - offline diagnostics')
print('Python:',sys.version.split()[0], '|',struct.calcsize('P')*8,'bit')
print('Platform:',platform.platform())
for name in ('llama_cpp','pypdf','faster_whisper','pyttsx3'):
    print(name+':','installed' if importlib.util.find_spec(name) else 'not installed')
model=LocalModel()
print('GGUF models:',model.models() or 'None. Run setup.py --model')
print('Voice model:',(model.directory/'whisper-small/model.bin').exists())
print('Docker:',shutil.which('docker') or 'Not installed (only required for automatic isolated commands)')
print('No internet requests were made by this diagnostic.')
