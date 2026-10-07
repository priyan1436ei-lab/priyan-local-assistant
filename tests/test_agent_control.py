import json
import sys
import tempfile
import time
import unittest
from agent import Agent

class ControlTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.a=Agent(self.temp.name)
    def tearDown(self):
        for _ in range(100):
            if not self.a.workers:break
            time.sleep(.02)
        self.a.db.close();self.temp.cleanup()
    def wait(self,ident,status):
        for _ in range(300):
            t=self.a.get(ident)
            if t['status']==status and (status=='running' or not self.a.workers):return t
            time.sleep(.01)
        self.fail(str(t))
    def test_stop_approved_subprocess(self):
        self.a.chat=lambda m:json.dumps({'action':'run','args':{'argv':[sys.executable,'-c','import time;time.sleep(30)']}})
        ident=self.a.new('Run slow command')['id'];self.wait(ident,'approval')
        self.a.decide(ident,True);time.sleep(.1);self.a.stop(ident)
        t=self.wait(ident,'stopped')
        self.assertEqual(t['events'][-1]['result']['termination'],'stopped')
    def test_resume_from_limit(self):
        self.a.max_steps=1
        replies=iter([{'action':'plan','args':{'steps':['Create result']}},{'action':'finish','args':{'summary':'Finished'}}])
        self.a.chat=lambda m:json.dumps(next(replies))
        ident=self.a.new('Do a task')['id'];self.wait(ident,'limit')
        self.a.resume(ident);self.wait(ident,'completed')
    def test_sandbox_dispatch_has_no_host_fallback(self):
        self.a.execution='sandbox'
        replies=iter([{'action':'run','args':{'argv':['python','-V']}},{'action':'finish','args':{'summary':'Reviewed run'}}])
        self.a.chat=lambda m:json.dumps(next(replies))
        calls=[]
        def execute(ident,argv,sandbox=False):
            calls.append((argv,sandbox));return {'error':'Docker unavailable'}
        self.a.run_command=execute
        ident=self.a.new('Test sandbox dispatch')['id'];self.wait(ident,'completed')
        self.assertEqual(calls,[(['python','-V'],True)])

if __name__=='__main__':unittest.main()
