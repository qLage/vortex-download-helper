"""Real UI Automation against our isolated fake Vortex.exe; no real downloads."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from helper_runtime import HelperSession


@unittest.skipUnless(os.name=='nt' and os.environ.get('VORTEX_UI_TEST')=='1','Set VORTEX_UI_TEST=1 for the isolated native UI test')
class WindowsIntegrationTests(unittest.TestCase):
    def test_move_deduplicate_pause_resume_stop_and_check_only(self):
        framework=Path(os.environ['SystemRoot'])/'Microsoft.NET/Framework64/v4.0.30319'
        fixture=None;session=None
        with tempfile.TemporaryDirectory(prefix='vortex-isolated-test-') as directory:
            directory=Path(directory);exe=directory/'Vortex.exe'
            compile_command=[str(framework/'csc.exe'),'/nologo','/target:winexe','/out:'+str(exe)]
            for filename in ('WindowsBase.dll','PresentationCore.dll','PresentationFramework.dll'):
                compile_command+=['/reference:'+str(framework/'WPF'/filename)]
            compile_command += ['/reference:System.Xaml.dll',str(Path(__file__).parent/'fixtures/VortexFixture.cs')]
            subprocess.run(compile_command,check=True,capture_output=True)
            events=[]
            def until(predicate,seconds=12):
                end=time.monotonic()+seconds
                while time.monotonic()<end:
                    if predicate():return
                    time.sleep(.08)
                self.fail('Timed out waiting for fixture event: '+str(events[-5:]))
            def clicks():return int((directory/'clicks.txt').read_text())
            try:
                fixture=subprocess.Popen([str(exe),str(directory)])
                until(lambda:(directory/'ready').exists())
                session=HelperSession(events.append,language='en',vortex_path=str(exe))
                session.start();until(lambda:any(e['type']=='clicked' for e in events))
                self.assertEqual(clicks(),1)
                (directory/'fixture-control.txt').write_text('move-1')
                time.sleep(1.8);self.assertEqual(clicks(),1,'Moving the button must not trigger another click')
                session.control('pause');until(lambda:any(e['type']=='paused' for e in events))
                (directory/'fixture-control.txt').write_text('next-2')
                time.sleep(1.2);self.assertEqual(clicks(),1,'No clicks while paused')
                session.control('resume');until(lambda:clicks()==2)
                session.stop(wait=True);until(lambda:any(e['type']=='ended' for e in events))
                (directory/'fixture-control.txt').write_text('next-3')
                time.sleep(1.0);self.assertEqual(clicks(),2,'No clicks after stop')
                check_events=[]
                session=HelperSession(check_events.append,language='ru',vortex_path=str(exe),check_only=True)
                session.start();until(lambda:any(e['type']=='ended' for e in check_events))
                self.assertTrue(any(e['type']=='detected' for e in check_events),check_events)
                self.assertEqual(clicks(),2,'Check-only must not invoke the button')
            finally:
                if session:session.stop(wait=True)
                if fixture and fixture.poll() is None:fixture.terminate();fixture.wait(5)


if __name__=='__main__':unittest.main(verbosity=2)
