import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
import zipfile
from assistant import Assistant,calculate
from knowledge import extract,search
from local_model import LocalModel,DEFAULT_MODEL
from maintenance import restore

class ScriptedModel:
    def __init__(self,actions):self.actions=iter(actions)
    def chat(self,*args):return json.dumps(next(self.actions))

class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.a=Assistant(self.temp.name)
    def tearDown(self):
        if self.a.worker:self.a.worker.join(3)
        self.a.close();self.a.store.close();self.temp.cleanup()
    def wait(self,job):
        self.a.worker.join(3)
        result=self.a.store.get('job',job['id'])
        self.assertNotEqual(result['status'],'running')
        return result
    def test_note_update_delete(self):
        x=self.a.item('note',{'title':'Study','content':'Python'})
        self.a.item('note',{'content':'Java'},x['id'])
        self.assertEqual(self.a.store.get('note',x['id'])['content'],'Java')
        self.a.store.delete('note',x['id']);self.assertEqual(self.a.store.list('note'),[])
    def test_todo_done(self):
        x=self.a.item('todo',{'title':'Test'})
        self.a.item('todo',{'status':'done'},x['id'])
        self.assertEqual(self.a.store.get('todo',x['id'])['status'],'done')
    def test_reminder_fires_and_acknowledges(self):
        x=self.a.item('reminder',{'title':'Study','due':'2020-01-01T12:00:00+05:30'})
        self.a.tick();self.assertTrue(self.a.store.get('reminder',x['id'])['fired'])
        self.a.acknowledge(x['id']);self.assertTrue(self.a.store.get('reminder',x['id'])['ack'])
    def test_recurring_and_snooze(self):
        x=self.a.item('reminder',{'title':'Review','due':'2020-01-01T00:00:00Z','repeat':'daily'})
        self.a.tick();r=self.a.acknowledge(x['id'])
        self.assertGreater(r['epoch'],time.time());self.assertFalse(r['fired'])
        r=self.a.acknowledge(x['id'],True);self.assertAlmostEqual(r['epoch'],time.time()+600,delta=2)
    def test_timezone_required(self):
        with self.assertRaises(ValueError):self.a.item('reminder',{'title':'Bad','due':'2026-10-05T12:00:00'})
    def test_unicode_document_search(self):
        d=self.a.import_document('தமிழ்.txt','தமிழ் பாடம் கணினி அறிவியல்'.encode())
        self.assertEqual(search(self.a.store,'கணினி')[0]['document_id'],d['id'])
        self.assertEqual(search(self.a.store,'unrelated'),[])
    def test_docx_extraction(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello Priyan</w:t></w:r></w:p></w:body></w:document>')
        self.assertIn('Hello Priyan',extract('x.docx',out.getvalue()))
    def test_reject_unknown_and_empty_document(self):
        for name,raw in [('x.exe',b'abc'),('x.txt',b'')]:
            with self.assertRaises(ValueError):extract(name,raw)
    def test_calculator(self):
        self.assertEqual(calculate('(1000-200)*1.5'),1200)
        for exp in ['__import__("os")','2**100000','[1]*4','True+2']:
            with self.assertRaises(ValueError):calculate(exp)
    def test_chat_tool_then_answer(self):
        self.a.model=ScriptedModel([{'action':'create_note','args':{'title':'Math','content':'Revise derivatives'}},{'action':'answer','args':{'text':'Saved your note.'}}])
        c=self.a.conversation();j=self.wait(self.a.new_chat(c['id'],'Save a math note'))
        self.assertEqual(j['status'],'completed');self.assertEqual(len(self.a.store.list('note')),1)
        self.assertEqual(self.a.store.get('conversation',c['id'])['messages'][-1]['content'],'Saved your note.')
    def test_document_sources_attached(self):
        self.a.import_document('guide.txt',b'Priyan Agent stores all notes locally in SQLite.')
        self.a.model=ScriptedModel([{'action':'answer','args':{'text':'Notes use SQLite [D1].'}}])
        c=self.a.conversation();self.wait(self.a.new_chat(c['id'],'Where are notes stored?',True))
        m=self.a.store.get('conversation',c['id'])['messages'][-1]
        self.assertEqual(m['sources'][0]['name'],'guide.txt')
    def test_bad_model_action_recovers(self):
        self.a.model=ScriptedModel([{'action':'missing','args':{}},{'action':'answer','args':{'text':'I can help.'}}])
        j=self.wait(self.a.new_chat(self.a.conversation()['id'],'Hi'))
        self.assertEqual(j['status'],'completed');self.assertEqual(j['events'][0]['action'],'error')
    def test_stop_prevents_tool_execution(self):
        entered=threading.Event();release=threading.Event()
        class Delayed:
            def chat(self,*args):
                entered.set();release.wait(3)
                return json.dumps({'action':'create_note','args':{'title':'Should not exist','content':'No'}})
        self.a.model=Delayed();j=self.a.new_chat(self.a.conversation()['id'],'Stop me')
        self.assertTrue(entered.wait(2));self.a.stop_chat(j['id']);release.set();self.wait(j)
        self.assertEqual(self.a.store.list('note'),[])
    def test_memory_off(self):
        self.a.configure({'use_memory':False})
        with self.assertRaises(ValueError):self.a.tool('remember',{'title':'Fact','content':'Test'})
    def test_missing_engine_or_model_clear_error(self):
        with self.assertRaisesRegex(ValueError,'Local model missing'):self.a.model.chat([],DEFAULT_MODEL)
    def test_model_paths_rejected(self):
        for name in ['../evil.gguf','C:\\evil.gguf','model:cloud']:
            with self.assertRaises(ValueError):self.a.configure({'chat_model':name})
    def test_backup_restore(self):
        self.a.item('note',{'title':'Keep me','content':'Saved locally'})
        blob=self.a.export();archive=Path(self.temp.name)/'backup.zip';archive.write_bytes(blob)
        dest=Path(self.temp.name)/'restored';restore(archive,dest)
        b=Assistant(dest)
        try:self.assertEqual(b.store.list('note')[0]['title'],'Keep me')
        finally:b.close();b.store.close()
    def test_restore_blocks_zip_slip(self):
        archive=Path(self.temp.name)/'evil.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape','bad')
        with self.assertRaises(ValueError):restore(archive,Path(self.temp.name)/'bad')
        self.assertFalse((Path(self.temp.name)/'escape').exists())
    def test_restart_preserves_memory(self):
        self.a.item('memory',{'title':'Language','content':'Tamil'})
        b=Assistant(self.temp.name)
        try:self.assertEqual(b.store.list('memory')[0]['content'],'Tamil')
        finally:b.close();b.store.close()

if __name__=='__main__':unittest.main()
