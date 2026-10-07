"""Optional offline voice. Models are never downloaded during transcription."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

class Voice:
    def __init__(self, root):
        self.model_path = Path(root) / 'models' / 'whisper-small'
        self.lock=threading.Lock()
        self.model=None
        self.speech=None
        self.speech_lock=threading.RLock()

    def status(self):
        return {'stt_package':importlib.util.find_spec('faster_whisper') is not None,
                'stt_model':(self.model_path/'model.bin').exists(),
                'tts_package':importlib.util.find_spec('pyttsx3') is not None,
                'model_path':str(self.model_path)}

    def transcribe(self, raw):
        if len(raw)>12*1024*1024 or not raw:
            raise ValueError('Audio must be nonempty and below 12 MB')
        if not (self.model_path/'model.bin').exists():
            raise ValueError('Offline voice model missing. Run setup.py --voice once while online.')
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ValueError('Install requirements-voice.txt first') from e
        with self.lock:
            os.environ['HF_HUB_OFFLINE']='1'
            if self.model is None:
                self.model=WhisperModel(str(self.model_path),device='cpu',compute_type='int8',local_files_only=True)
            fd,name=tempfile.mkstemp(suffix='.webm')
            try:
                with os.fdopen(fd,'wb') as f:
                    f.write(raw)
                segments,info=self.model.transcribe(name,beam_size=3,vad_filter=True)
                text=' '.join(s.text.strip() for s in segments)
                return {'text':text,'language':info.language}
            finally:
                Path(name).unlink(missing_ok=True)

    def speak(self,text):
        if not isinstance(text,str) or not text.strip() or len(text)>12000:
            raise ValueError('Speech text must be 1–12000 characters')
        if not importlib.util.find_spec('pyttsx3'):
            raise ValueError('Install requirements-voice.txt to enable offline speech')
        with self.speech_lock:
            self.stop()
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--speak'],
                                      stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.speech=process
        try:
            process.communicate(text.encode('utf-8'),timeout=300)
            if process.returncode:
                raise ValueError('Speech stopped or the OS voice failed. See the voice setup guide.')
            return {'ok':True}
        except subprocess.TimeoutExpired:
            process.kill();process.wait()
            raise ValueError('Speech exceeded the five minute limit')
        finally:
            with self.speech_lock:
                if self.speech is process: self.speech=None

    def stop(self):
        with self.speech_lock:
            p=self.speech
            if p and p.poll() is None:
                p.terminate()
            self.speech=None

if __name__=='__main__':
    import pyttsx3
    engine=pyttsx3.init()
    engine.setProperty('rate',170)
    engine.say(sys.stdin.buffer.read().decode('utf-8'))
    engine.runAndWait()
