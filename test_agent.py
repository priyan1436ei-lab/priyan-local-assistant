import json
import tempfile
import time
import unittest
from pathlib import Path
from agent import Agent

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.a = Agent(self.tmp.name)
    def tearDown(self):
        self.a.db.close()
        self.tmp.cleanup()
    def wait(self, ident, status):
        for _ in range(200):
            t = self.a.get(ident)
            if t['status'] == status:
                return t
            time.sleep(.01)
        self.fail(str(t))
    def script(self, actions):
        it = iter(actions)
        self.a.chat = lambda messages: json.dumps(next(it))
    def test_write_read_backup(self):
        self.a.execute('write',dict(path='a.txt',content='first'))
        self.a.execute('write',dict(path='a.txt',content='second'))
        self.assertEqual(self.a.execute('read',dict(path='a.txt'))['content'],'second')
        self.assertEqual(next((Path(self.tmp.name)/'backups').rglob('a.txt')).read_text(),'first')
    def test_escape_and_symlink(self):
        for path in ['../escape','/tmp/escape','.env']:
            with self.assertRaises(ValueError):
                self.a.path(path)
        (self.a.files/'link').symlink_to(Path(self.tmp.name), target_is_directory=True)
        with self.assertRaises(ValueError):
            self.a.path('link/tasks.sqlite3')
    def test_complete_loop(self):
        self.script([{'action':'plan','args':{'steps':['Write','Verify']}},
                     {'action':'write','args':{'path':'hello.txt','content':'Hello Priyan'}},
                     {'action':'read','args':{'path':'hello.txt'}},
                     {'action':'finish','args':{'summary':'Created and read hello.txt'}}])
        t=self.wait(self.a.new('Create hello file')['id'],'completed')
        self.assertEqual(len(t['events']),4)
        self.assertEqual((self.a.files/'hello.txt').read_text(),'Hello Priyan')
    def test_approval_then_execute(self):
        import sys
        self.script([{'action':'run','args':{'argv':[sys.executable,'-c','print(6*7)']}},
                     {'action':'finish','args':{'summary':'Command returned 42'}}])
        ident=self.a.new('Compute')['id']
        self.wait(ident,'approval')
        self.a.decide(ident,True)
        t=self.wait(ident,'completed')
        self.assertEqual(t['events'][1]['result']['output'].strip(),'42')
    def test_deny(self):
        self.script([{'action':'run','args':{'argv':['nonexistent']}},
                     {'action':'blocked','args':{'summary':'Command denied'}}])
        ident=self.a.new('Task')['id'];self.wait(ident,'approval')
        self.a.decide(ident,False)
        t=self.wait(ident,'blocked')
        self.assertTrue(t['events'][1]['result']['denied'])
    def test_recover_bad_action(self):
        self.script([{'action':'invalid','args':{}},{'action':'finish','args':{'summary':'Recovered'}}])
        t=self.wait(self.a.new('Task')['id'],'completed')
        self.assertEqual(t['events'][0]['action'],'error')
    def test_step_limit(self):
        self.a.max_steps=1
        self.script([{'action':'plan','args':{'steps':['Do work']}}])
        self.wait(self.a.new('Task')['id'],'limit')
    def test_restart_marks_interrupted(self):
        t=dict(id='test',status='running')
        self.a.save(t)
        other=Agent(self.tmp.name)
        self.assertEqual(other.get('test')['status'],'interrupted')
        other.db.close()

if __name__=='__main__': unittest.main()
