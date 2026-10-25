"""Build only reviewed source files. Never include runtime directories or keys."""
from pathlib import Path
import hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
FILES=['.gitignore','README.md','package.json',
 'kimi-api/native-runtime.cjs','kimi-api/proxy.cjs','kimi-api/start.ps1','kimi-api/stop.ps1',
 'kimi-api/runtime-selection.json','kimi-api/verify_k31.py','kimi-api/validate_tools.py',
 'kimi-protocol/tools.json','kimi-protocol/system-prompt.template.txt','kimi-protocol/adapter.py',
 'docs/完整使用与工具协议.md','docs/validation.json','tests/test_protocol.py','scripts/package.py']
FORBIDDEN=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bgithub_pat_[A-Za-z0-9_]{20,}',r'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}']
def main():
    version=json.loads((ROOT/'package.json').read_text())['version']
    manifest={}
    for name in FILES:
        data=(ROOT/name).read_bytes();text=data.decode('utf-8')
        if any(re.search(pattern,text) for pattern in FORBIDDEN):raise RuntimeError('Possible credential in '+name)
        manifest[name]=hashlib.sha256(data).hexdigest()
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    output=dist/f'mira-kimi-proxy-{version}.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:z.write(ROOT/name,name)
        z.writestr('SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(output) as z:
        assert set(z.namelist())==set(FILES+['SHA256.json'])
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    (dist/'SHA256SUMS').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n',encoding='ascii')
    print('PASS: allowlisted package, credential-pattern scan and archive integrity; files='+str(len(FILES)))
    print(output.name)
if __name__=='__main__':main()
