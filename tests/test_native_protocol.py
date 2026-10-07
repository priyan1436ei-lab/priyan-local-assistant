"""Tests worker protocol with a stand-in API, not language model intelligence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from instance_lock import InstanceLock

class NativeProtocolTests(unittest.TestCase):
    def test_native_worker_stdio_and_model_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'llama_cpp.py').write_text('''class Llama:
 def __init__(self, **kwargs): self.path=kwargs['model_path']
 def tokenize(self, data, add_bos=False): return list(data[:10])
 def create_chat_completion(self, **kwargs): return {'choices':[{'message':{'content':'{"action":"answer","args":{"text":"Local protocol works"}}'}}]}
 def close(self): pass
''')
            env=dict(os.environ,PYTHONPATH=tmp)
            req={'messages':[{'role':'system','content':'JSON'},{'role':'user','content':'Hi'}],'model_path':'fake.gguf','context':4096,'gpu_layers':0}
            process=subprocess.run([sys.executable,str(Path(__file__).parents[1]/'native_worker.py')],
                    input=json.dumps(req)+'\n'+json.dumps(dict(req,context=2048))+'\n',text=True,
                    capture_output=True,env=env,timeout=5)
            self.assertEqual(process.returncode,0)
            lines=process.stdout.splitlines();self.assertEqual(len(lines),2)
            self.assertEqual(json.loads(json.loads(lines[0])['content'])['args']['text'],'Local protocol works')
    def test_instance_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            first=InstanceLock(tmp)
            try:
                with self.assertRaises(ValueError):InstanceLock(tmp)
            finally:first.close()
            second=InstanceLock(tmp);second.close()

if __name__=='__main__':unittest.main()
