import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from assistant import Assistant
from agent import Agent
from app import make_server

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.a=Assistant(self.temp.name);self.agent=Agent(self.temp.name)
        self.server=make_server(self.a,self.agent,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.a.close();self.a.store.close();self.agent.db.close();self.temp.cleanup()
    def request(self,path,body=None,auth=True,extra=None):
        headers={'Content-Type':'application/json'}
        if auth:headers['X-Agent-Token']=self.server.token
        if extra:headers.update(extra)
        req=urllib.request.Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
        return urllib.request.urlopen(req)
    def test_dashboard_and_auth(self):
        with self.request('/',auth=False) as r:
            self.assertIn(b'Your personal AI',r.read());self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/state',auth=False)
        self.assertEqual(ctx.exception.code,403)
    def test_origin_and_host_rejected(self):
        for extra in [{'Origin':'https://evil.example'},{'Host':'evil.example'}]:
            with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/item',{'kind':'note','title':'Bad'},extra=extra)
            self.assertEqual(ctx.exception.code,403)
    def test_note_and_import(self):
        with self.request('/api/item',{'kind':'note','title':'Test','content':'Works'}) as r:self.assertEqual(json.load(r)['title'],'Test')
        with self.request('/api/import',{'name':'sample.txt','data':base64.b64encode(b'local knowledge').decode()}) as r:self.assertEqual(json.load(r)['chunks'],1)
        with self.request('/api/state') as r:self.assertEqual(len(json.load(r)['documents']),1)
    def test_bad_request_no_mutation(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/item',{'kind':'note','title':''})
        self.assertEqual(ctx.exception.code,400);self.assertEqual(self.a.store.list('note'),[])
    def test_download_escape_denied(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/download?path=../assistant.sqlite3')
        self.assertEqual(ctx.exception.code,400)

if __name__=='__main__':unittest.main()
