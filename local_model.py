"""Embedded GGUF inference in a local child process. No model server, HTTP or Ollama."""
import atexit
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading

DEFAULT_MODEL='qwen2.5-3b-instruct-q4_k_m.gguf'

class LocalModel:
    def __init__(self,root=None):
        self.root=Path(root or Path(__file__).parent/'agent-data').resolve()
        self.directory=self.root/'models';self.directory.mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock();self.process=None;self.gpu_layers=0
        atexit.register(self.close)

    def models(self):
        return sorted(p.name for p in self.directory.glob('*.gguf') if p.is_file() and not p.is_symlink())

    def status(self):
        return {'engine_installed':importlib.util.find_spec('llama_cpp') is not None,
                'models':self.models(),'backend':'Embedded llama.cpp','gpu_layers':self.gpu_layers,
                'model_directory':str(self.directory)}

    def close(self):
        p=self.process
        if p and p.poll() is None:
            p.kill()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: pass
        self.process=None

    def chat(self,messages,model,context=4096):
        if model not in self.models():
            raise ValueError('Local model missing. Run the included installer once, or place a GGUF model in agent-data/models. No Ollama required.')
        if not importlib.util.find_spec('llama_cpp'):
            raise ValueError('Embedded AI engine is not installed. Run install-windows.bat or follow SETUP.md.')
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self.process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('native_worker.py'))],
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                    text=True,encoding='utf-8',bufsize=1)
            p=self.process
            request={'messages':messages,'model_path':str(self.directory/model),'context':context,'gpu_layers':self.gpu_layers}
            try:
                p.stdin.write(json.dumps(request,ensure_ascii=False)+'\n');p.stdin.flush()
                result=queue.Queue(maxsize=1)
                def receive():
                    try: result.put(p.stdout.readline())
                    except Exception: result.put('')
                threading.Thread(target=receive,daemon=True).start()
                line=result.get(timeout=300)
                if not line: raise RuntimeError('Local engine exited. Check available RAM and the engine installation.')
                data=json.loads(line)
                if data.get('error'): raise RuntimeError(data['error'])
                return data['content']
            except queue.Empty as e:
                self.close()
                raise RuntimeError('Local inference exceeded five minutes. Use a smaller model/context or enable a compatible GPU engine.') from e
            except Exception:
                self.close();raise
