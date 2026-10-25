import json,pathlib,time,urllib.request,urllib.error,datetime
root=pathlib.Path(__file__).resolve().parent
key=(root/'.local-api-key').read_text().strip()
base='http://127.0.0.1:18890'
def call(route,payload=None,auth=key):
    req=urllib.request.Request(base+route,data=None if payload is None else json.dumps(payload).encode(),headers={'Authorization':'Bearer '+auth,'Content-Type':'application/json'})
    return urllib.request.urlopen(req,timeout=190)
report={'tested_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with call('/health') as f:report['health']=json.load(f)
assert report['health']['defaultModel']=='kimi-k3.1-pro'
with call('/v1/models') as f:report['models']=[x['id'] for x in json.load(f)['data']]
assert all(x in report['models'] for x in ['kimi-k3.1-pro','kimi-code/k3.1-pro','kimi-code/k3'])
start=time.monotonic()
try:
    with call('/v1/chat/completions',{'messages':[{'role':'user','content':'Reply exactly MIRA_K31_OK.'}],'stream':False,'max_completion_tokens':512}) as f:
        d=json.load(f);answer=d['choices'][0]['message'].get('content')
        report['plain']={'status':f.status,'returned_model':d.get('model'),'answer':answer,'seconds':round(time.monotonic()-start,2),'model_omitted':True}
        report['passed']=answer=='MIRA_K31_OK' and 'k3.1' in (d.get('model') or '')
except urllib.error.HTTPError as e:
    report['plain']={'status':e.code,'error':e.read(2000).decode(errors='replace')};report['passed']=False
(root/'validation-k3.1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True),flush=True)
if not report['passed']:raise SystemExit(1)
