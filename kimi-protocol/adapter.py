"""Build requests using the exported Kimi tools; execute tools in YOUR client.
No account credentials are required to import this module.
"""
import copy,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
TOOLS=json.loads((ROOT/'tools.json').read_text(encoding='utf-8'))

def build_request(messages,workspace,*,model='kimi-k3.1-pro',stream=True,max_tokens=4096,tool_names=None):
    prompt=(ROOT/'system-prompt.template.txt').read_text(encoding='utf-8').replace('{{WORKSPACE}}',workspace)
    selected=TOOLS if tool_names is None else [t for t in TOOLS if t['function']['name'] in tool_names]
    if tool_names is not None and len(selected)!=len(set(tool_names)):
        raise ValueError('Unknown tool name')
    # Existing assistant reasoning_content/tool_calls and tool messages are retained.
    return {'model':model,'messages':[{'role':'system','content':prompt}]+copy.deepcopy(messages),
            'tools':copy.deepcopy(selected),'stream':stream,'max_completion_tokens':max_tokens,
            'thinking':{'type':'enabled','keep':'all'},**({'stream_options':{'include_usage':True}} if stream else {})}

def tool_result(call,output):
    """Call your own executor with json.loads(call['function']['arguments']) first."""
    if not isinstance(call.get('id'),str):raise ValueError('Missing tool-call id')
    return {'role':'tool','tool_call_id':call['id'],'content':output if isinstance(output,str) else json.dumps(output,ensure_ascii=False)}
