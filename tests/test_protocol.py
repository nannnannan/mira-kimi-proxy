import importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adapter',ROOT/'kimi-protocol/adapter.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class ProtocolTests(unittest.TestCase):
    def test_tool_subset_and_default_model(self):
        p=adapter.build_request([{'role':'user','content':'test'}],'/workspace',tool_names=['Read'])
        self.assertEqual(p['model'],'kimi-k3.1-pro')
        self.assertEqual([t['function']['name'] for t in p['tools']],['Read'])
        self.assertEqual(p['thinking']['keep'],'all')
    def test_roundtrip_preserves_assistant_fields(self):
        call={'id':'fixture-1','type':'function','function':{'name':'Read','arguments':'{"path":"/workspace/a"}'}}
        original={'role':'assistant','content':None,'reasoning_content':'synthetic reasoning','tool_calls':[call]}
        result=adapter.tool_result(call,'fixture result')
        p=adapter.build_request([original,result],'/workspace')
        self.assertEqual(p['messages'][-2],original)
        self.assertEqual(p['messages'][-1]['tool_call_id'],'fixture-1')
        self.assertEqual(p['messages'][-1]['content'],'fixture result')
    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):adapter.build_request([],'/workspace',tool_names=['not-a-tool'])
    def test_captured_schemas_complete(self):
        tools=adapter.TOOLS
        self.assertEqual(len(tools),25)
        self.assertEqual(len({t['function']['name'] for t in tools}),25)
        read=next(t['function'] for t in tools if t['function']['name']=='Read')
        self.assertIn('path',read['parameters']['properties'])

if __name__=='__main__':unittest.main()
