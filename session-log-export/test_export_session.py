import json,pathlib,tempfile,unittest
from unittest.mock import patch
import export_session as e

class ExportTest(unittest.TestCase):
    def test_utf8_preserves_complete_response(self):
        fixture={'turns':[{'prompt':'你好','text':'回答','tools':[{'name':'Read','output':'测试'}]}]}
        with tempfile.TemporaryDirectory() as d:
            path=e.write_export(pathlib.Path(d)/'会话.json',fixture,'example:key',4970)
            data=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(data['history'],fixture)
            with self.assertRaises(FileExistsError):e.write_export(path,{},'example:key',4970)
    def test_invalid_output_is_not_exported(self):
        with patch.object(e.subprocess,'run',return_value=e.subprocess.CompletedProcess([],0,b'not json',b'')):
            with self.assertRaises(RuntimeError):e.read_json(pathlib.Path('mirasim'),['ui-cli'])
    def test_command_failure_hides_raw_stderr(self):
        with patch.object(e.subprocess,'run',return_value=e.subprocess.CompletedProcess([],1,b'',b'private text')):
            with self.assertRaises(RuntimeError) as ex:e.read_json(pathlib.Path('mirasim'),['ui-cli'])
            self.assertNotIn('private text',str(ex.exception))
    @unittest.skipUnless(e.os.name=='nt','Windows batch launcher guard')
    def test_batch_arguments_reject_shell_operators(self):
        with self.assertRaises(ValueError):e.command(pathlib.Path('mirasim.cmd'),['history','--session','x&whoami'])
        self.assertEqual(e.command(pathlib.Path('mirasim.cmd'),['history','--session','kimi:example-id'])[-1],'kimi:example-id')

if __name__=='__main__':unittest.main()
