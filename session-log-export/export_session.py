"""Export via the installed official Mira CLI; no direct credential/transcript access."""
import argparse,datetime,json,os,pathlib,shutil,subprocess,sys

def find_cli(override=None):
    if override:
        p=pathlib.Path(override).expanduser()
    else:
        p=pathlib.Path(os.environ.get('MIRASIM_HOME') or pathlib.Path.home()/'.mirasim')/'bin'/('mirasim.cmd' if os.name=='nt' else 'mirasim')
        if not p.is_file():
            found=shutil.which('mirasim')
            if found:p=pathlib.Path(found)
    if not p.is_file():raise ValueError('Official Mira CLI not found. Start Mira or pass --mira PATH.')
    return p.resolve()

def command(cli,args):
    values=[str(cli),*args]
    if os.name=='nt' and cli.suffix.lower() in ('.cmd','.bat'):
        # Windows batch launchers interpret metacharacters even with shell=False.
        if any(any(c in value for c in '&|<>^%!"\r\n\0') for value in values):
            raise ValueError('Batch launcher arguments contain unsupported shell characters.')
    return values

def read_json(cli,args):
    result=subprocess.run(command(cli,args),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,shell=False)
    if result.returncode:
        raise RuntimeError('Mira CLI failed (exit '+str(result.returncode)+'). Check the chosen host/port and official command help; no export was written.')
    try:return json.loads(result.stdout.decode('utf-8-sig'))
    except (UnicodeError,json.JSONDecodeError) as e:
        raise RuntimeError('CLI output was not UTF-8 JSON; no partial export was written.') from e

def write_export(output,data,session_key,port):
    output=pathlib.Path(output).expanduser().resolve()
    content={'exported_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'source':'Mira official ui-cli history','host_port':port,'session_key':session_key,
             'scope':'Recorded settled turns returned by this host; not guaranteed to be the full native agent transcript.',
             'history':data}
    fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:
        json.dump(content,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mira',help='Absolute path to official mirasim or mirasim.cmd')
    p.add_argument('--port',type=int,default=4970)
    sub=p.add_subparsers(dest='action',required=True)
    ls=sub.add_parser('list');ls.add_argument('--query');ls.add_argument('--cwd');ls.add_argument('--limit',type=int,default=50)
    ex=sub.add_parser('export');ex.add_argument('--session',required=True);ex.add_argument('--output',required=True);ex.add_argument('--limit',type=int)
    a=p.parse_args()
    if not 1<=a.port<=65535:p.error('Invalid port')
    if a.limit is not None and a.limit<1:p.error('limit must be positive')
    cli=find_cli(a.mira);args=['ui-cli','--port',str(a.port)]
    if a.action=='list':
        args+=['sessions','--limit',str(a.limit)]
        if a.query:args+=['--query',a.query]
        if a.cwd:args+=['--cwd',a.cwd]
        print(json.dumps(read_json(cli,args),ensure_ascii=False,indent=2))
    else:
        if pathlib.Path(a.output).expanduser().exists():raise FileExistsError('Output already exists; choose a new filename.')
        args+=['history','--session',a.session]
        if a.limit is not None:args+=['--limit',str(a.limit)]
        data=read_json(cli,args)
        print('Saved: '+str(write_export(a.output,data,a.session,a.port)))

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
