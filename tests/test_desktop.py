from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import helper_runtime
try:
    import gui
except ImportError:
    gui=None


class RuntimeTests(unittest.TestCase):
    def test_control_is_bounded_and_does_not_execute_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            session=helper_runtime.HelperSession(lambda event:None)
            session.temp=Path(folder)
            session.control('pause')
            self.assertEqual((Path(folder)/'control.txt').read_text(encoding='utf-8'),'1|pause')
            session.control('resume')
            self.assertEqual((Path(folder)/'control.txt').read_text(encoding='utf-8'),'2|resume')
            with self.assertRaises(ValueError):session.control('arbitrary command')
            session.control('stop');self.assertTrue(session.stop_requested.is_set())

    def test_control_after_session_ended_is_safe(self):
        session=helper_runtime.HelperSession(lambda event:None)
        session.control('stop')
        self.assertTrue(session.stop_requested.is_set())

    @unittest.skipIf(gui is None,'Tkinter not installed')
    def test_languages_and_event_rendering(self):
        self.assertEqual(set(gui.WORDS['ru']),set(gui.WORDS['en']))
        app=object.__new__(gui.HelperApp);app.words=gui.WORDS
        event=dict(type='clicked',data=dict(count=3,progress='3/44',mod='Example'))
        for language,expected in [('ru','Нажатие'),('en','Click')]:
            app.language=language
            self.assertIn(expected,app.event_text(event))
            self.assertIn('Example',app.event_text(event))


if __name__=='__main__':unittest.main()
