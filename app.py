"""Single-user loopback server; Python standard library, no external frontend assets."""
import argparse
import base64
import json
from pathlib import Path
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
import webbrowser
from assistant import Assistant,KINDS
from agent import Agent
from knowledge import search
from instance_lock import InstanceLock

HERE=Path(__file__).resolve().parent

class LocalServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True

def make_server(assistant,agent,port=8765):
    token=secrets.token_urlsafe(32)
    assistant.agent=agent
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def setup(self):
            super().setup()
            self.connection.settimeout(300)
        def send(self,code,data,mime='application/json; charset=utf-8',download=None):
            if not isinstance(data,(bytes,str)): data=json.dumps(data,ensure_ascii=False)
            if isinstance(data,str): data=data.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            if download: self.send_header('Content-Disposition',f'attachment; filename="{download}"')
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError): pass
        def host_ok(self):
            host='127.0.0.1:'+str(self.server.server_port)
            return self.headers.get('Host')==host
        def authorized(self):
            origin=self.headers.get('Origin')
            expected='http://127.0.0.1:'+str(self.server.server_port)
            return self.host_ok() and secrets.compare_digest(self.headers.get('X-Agent-Token',''),token) and origin in (None,expected)
        def do_GET(self):
            if not self.host_ok(): return self.send(403,{'error':'Invalid host. Use 127.0.0.1.'})
            url=urlsplit(self.path);path=url.path;q=parse_qs(url.query)
            if path=='/':
                return self.send(200,(HERE/'static/index.html').read_text(encoding='utf-8').replace('__TOKEN__',token),'text/html; charset=utf-8')
            assets={'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
            if path in assets:
                file,mime=assets[path]
                return self.send(200,(HERE/'static'/file).read_bytes(),mime)
            if not self.authorized(): return self.send(403,{'error':'Session expired. Reload this page.'})
            try:
                ident=q.get('id',[''])[0]
                if path=='/api/state':
                    result={'settings':assistant.settings,'workspace':str(agent.files),
                            'conversations':[dict(id=c['id'],title=c['title'],count=len(c['messages'])) for c in assistant.store.list('conversation')],
                            'documents':[dict(id=d['id'],name=d['name'],chars=d['chars'],chunks=len(d['chunks'])) for d in assistant.store.list('document')],
                            'items':{k:assistant.store.list(k) for k in sorted(KINDS)},
                            'jobs':assistant.store.list('job')[:20],
                            'code':[dict(id=t['id'],goal=t['goal'],status=t['status'],steps=t['steps']) for t in agent.all()],
                            'voice':assistant.voice.status()}
                elif path=='/api/conversation': result=assistant.store.get('conversation',ident)
                elif path=='/api/job': result=assistant.store.get('job',ident)
                elif path=='/api/code/task': result={k:v for k,v in agent.get(ident).items() if k!='messages'}
                elif path=='/api/models': result=assistant.model.status()
                elif path=='/api/search': result={'sources':search(assistant.store,q.get('q',[''])[0])}
                elif path=='/api/files': result=agent.execute('list',{'path':q.get('path',['.'])[0]})
                elif path=='/api/file': result=agent.execute('read',{'path':q.get('path',[''])[0],'offset':int(q.get('offset',['0'])[0])})
                elif path=='/api/download':
                    file=agent.path(q.get('path',[''])[0])
                    if not file.is_file() or file.stat().st_size>10*1024*1024: raise ValueError('File unavailable or above 10 MB')
                    return self.send(200,file.read_bytes(),'application/octet-stream','workspace-file'+file.suffix)
                elif path=='/api/export': return self.send(200,assistant.export(agent),'application/zip','priyan-backup.zip')
                else: return self.send(404,{'error':'Not found'})
                return self.send(200,result)
            except (ValueError,KeyError,TypeError,OSError,RuntimeError) as e: return self.send(400,{'error':str(e)})
        def do_POST(self):
            if not self.authorized(): return self.send(403,{'error':'Unauthorized. Reload the page.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=18*1024*1024: raise ValueError('Request must be below 18 MB')
                b=json.loads(self.rfile.read(size))
                if not isinstance(b,dict): raise ValueError('Request must be an object')
                path=urlsplit(self.path).path
                if path=='/api/settings':
                    if agent.busy() or assistant.gate.locked(): raise ValueError('Wait until active work finishes before changing settings')
                    result=assistant.configure(b)
                    agent.model=result['code_model'];agent.context=result['context'];agent.execution=result['execution']
                    assistant.model.gpu_layers=result['gpu_layers'];assistant.model.close()
                elif path=='/api/conversation': result=assistant.conversation(b.get('title','New conversation'))
                elif path=='/api/chat': result=assistant.new_chat(b['id'],b['prompt'],b.get('documents',False))
                elif path=='/api/chat/stop': result=assistant.stop_chat(b['id'])
                elif path=='/api/item': result=assistant.item(b['kind'],b,b.get('id'))
                elif path=='/api/delete':
                    kind=b['kind'];ident=b['id']
                    if kind not in KINDS|{'document','conversation'}: raise ValueError('Invalid type')
                    if kind=='conversation' and assistant.gate.locked(): raise ValueError('Wait for chat to finish before deleting a conversation')
                    assistant.store.delete(kind,ident)
                    if kind=='conversation':
                        for j in assistant.store.list('job'):
                            if j['conversation']==ident: assistant.store.delete('job',j['id'])
                    result={'ok':True}
                elif path=='/api/reminder/ack': result=assistant.acknowledge(b['id'],b.get('snooze') is True)
                elif path=='/api/import':
                    raw=base64.b64decode(b['data'],validate=True)
                    d=assistant.import_document(b['name'],raw)
                    result={'id':d['id'],'name':d['name'],'chunks':len(d['chunks'])}
                elif path=='/api/code/start': result={'id':agent.new(b['goal'])['id']}
                elif path=='/api/code/decision':
                    if not isinstance(b.get('approve'),bool): raise ValueError('approve must be boolean')
                    agent.decide(b['id'],b['approve']);result={'ok':True}
                elif path=='/api/code/stop': agent.stop(b['id']);result={'ok':True}
                elif path=='/api/code/resume': agent.resume(b['id']);result={'ok':True}
                elif path=='/api/voice/transcribe': result=assistant.voice.transcribe(base64.b64decode(b['data'],validate=True))
                elif path=='/api/voice/speak': result=assistant.voice.speak(b['text'])
                elif path=='/api/voice/stop': assistant.voice.stop();result={'ok':True}
                else: return self.send(404,{'error':'Not found'})
                return self.send(200,result)
            except (ValueError,KeyError,TypeError,OSError,RuntimeError) as e: return self.send(400,{'error':str(e)})
            except Exception as e: return self.send(500,{'error':str(e)})
    server=LocalServer(('127.0.0.1',port),Handler)
    server.token=token
    return server

def main():
    parser=argparse.ArgumentParser(description='Priyan Local: personal AI on your own computer')
    parser.add_argument('--data',default=str(HERE/'agent-data'))
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    # Acquire listener before initializing jobs, so a second launch cannot interrupt them.
    reservation=socket.socket()
    try: reservation.bind(('127.0.0.1',args.port))
    except OSError:
        raise SystemExit(f'Port {args.port} is already in use. Open http://127.0.0.1:{args.port} or choose --port.')
    reservation.close()
    try: instance=InstanceLock(args.data)
    except ValueError as e: raise SystemExit(str(e))
    assistant=Assistant(args.data)
    agent=Agent(args.data,assistant.settings['code_model'],client=assistant.model)
    agent.execution=assistant.settings['execution'];agent.context=assistant.settings['context']
    assistant.model.gpu_layers=assistant.settings.get('gpu_layers',0)
    server=make_server(assistant,agent,args.port)
    assistant.start_clock()
    url=f'http://127.0.0.1:{server.server_port}'
    print('PRIYAN LOCAL · '+url,flush=True)
    print('Data: '+str(assistant.root),flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        for task in agent.all():
            if task['status']=='running': agent.stop(task['id'])
        assistant.close();server.server_close();instance.close()

if __name__=='__main__': main()
