"""Two real Mira K3 requests: tool-call SSE then client-supplied tool result.
No tool is executed by this script. Uses only our separate loopback API key.
"""
import json,pathlib,time,urllib.request,sys,datetime
ROOT=pathlib.Path(__file__).resolve().parent
PROTOCOL=ROOT.parent/'kimi-protocol'
key=(ROOT/'.local-api-key').read_text().strip()
base='http://127.0.0.1:18890/v1/chat/completions'
first_model=sys.argv[1] if len(sys.argv)>1 else 'kimi-code/k3'
second_model=sys.argv[2] if len(sys.argv)>2 else first_model
report_name='live-tool-validation-k3.1.json' if 'k3.1' in first_model else 'live-tool-validation.json'
tools=json.loads((PROTOCOL/'tools.json').read_text(encoding='utf-8'))
system=json.loads((PROTOCOL/'system-messages.json').read_text(encoding='utf-8'))
messages=system+[{'role':'user','content':'Read /workspace/fixture.txt using Read. After the tool result, reply with its contents only. Do not call any other tool.'}]

def call(body):
    started=time.monotonic()
    req=urllib.request.Request(base,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    message={'role':'assistant','content':'','reasoning_content':''}; calls={};done=False;finish=None;usage=None;returned_models=set()
    with urllib.request.urlopen(req,timeout=190) as r:
        assert r.status==200
        for raw in r:
            line=raw.decode('utf-8').strip()
            if not line.startswith('data:'):continue
            data=line[5:].strip()
            if data=='[DONE]':done=True;continue
            event=json.loads(data)
            if event.get('model'):returned_models.add(event['model'])
            usage=event.get('usage') or usage
            for choice in event.get('choices',[]):
                finish=choice.get('finish_reason') or finish
                delta=choice.get('delta',{})
                for field in ['content','reasoning_content']:
                    message[field]+=delta.get(field) or ''
                for item in delta.get('tool_calls',[]):
                    index=item['index'];part=calls.setdefault(index,{'id':'','type':'function','function':{'name':'','arguments':''}})
                    if item.get('id'):part['id']=item['id']
                    fn=item.get('function',{})
                    part['function']['name']+=fn.get('name') or ''
                    part['function']['arguments']+=fn.get('arguments') or ''
    assert done,'Missing SSE DONE marker'
    if calls:message['tool_calls']=[calls[x] for x in sorted(calls)]
    return message,{'seconds':round(time.monotonic()-started,2),'finish_reason':finish,'usage':usage,'done':done,'returned_models':sorted(returned_models)}

first,a=call({'model':first_model,'messages':messages,'tools':tools,'tool_choice':{'type':'function','function':{'name':'Read'}},'stream':True,'max_completion_tokens':2048})
assert len(first.get('tool_calls',[]))==1,first.get('content')
tc=first['tool_calls'][0]
assert tc['function']['name']=='Read'
assert json.loads(tc['function']['arguments'])['path']=='/workspace/fixture.txt'
print('Real K3 tool-call SSE passed',flush=True)
result={'role':'tool','tool_call_id':tc['id'],'content':'1\tADAPTER_ROUNDTRIP_OK\n<system>1 line read. End of file reached.</system>'}
second,b=call({'model':second_model,'messages':messages+[first,result],'tools':tools,'stream':True,'max_completion_tokens':2048})
assert 'ADAPTER_ROUNDTRIP_OK' in second['content'],second['content']
assert not second.get('tool_calls')
report={'tested_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_upstream':'Mira platform','requested_aliases':[first_model,second_model],'tools_sent':len(tools),'tool_name':tc['function']['name'],'arguments_are_json_string':isinstance(tc['function']['arguments'],str),'tool_result_correlated':True,'thinking_history_preserved':bool(first['reasoning_content']),'first':a,'second':b,'final_text':second['content'],'tools_executed_by_proxy':False,'passed':True}
(ROOT/report_name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Real K3 client tool-result roundtrip passed',flush=True)
