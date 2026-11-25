import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from bhasha.cli import compile_text
from bhasha.backend.vm import run
from bhasha.backend.native_x86 import CEmitter
from bhasha.playground import Handler

def compiled(source):
    _, tree, diagnostics, _ = compile_text(source)
    assert not diagnostics
    return tree

def test_vm_arrays_loop_if_break_continue_and_bool():
    tree = compiled('''
dhoro purno[3] a;
dhoro purno x = 0;
cholo i = 0 theke 3 { a[i] = i + 1; x += a[i]; }
jotokkhon x > 0 { x -= 1; jodi x == 2 { choluk; } jodi x == 1 { thamo; } }
dekhao x == 1;
''')
    assert run(tree) == 'true\n'

def test_vm_else_and_float():
    tree = compiled('dhoro doshomik x = 2.5; jodi x < 2 { dekhao 0; } nahole { dekhao x; }')
    assert run(tree) == '2.5\n'

def test_native_emitter_handles_control_flow_and_arrays():
    tree = compiled('dhoro purno[2] a; a[0] = 4; jodi a[0] == 4 { dekhao a[0]; }')
    code = CEmitter().generate(tree)
    assert 'long a[2]' in code and 'if (' in code and 'printf' in code

def test_playground_api_success_and_diagnostics():
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f'http://127.0.0.1:{server.server_port}/api/compile'
        req = Request(url, data=json.dumps({'source':'dekhao 8;'}).encode(), headers={'Content-Type':'application/json'}, method='POST')
        with urlopen(req) as response: payload=json.load(response)
        assert payload['output'] == '8\n' and payload['tac'] and payload['cfgBlocks']
        req = Request(url, data=json.dumps({'source':'dekhao @;'}).encode(), headers={'Content-Type':'application/json'}, method='POST')
        with urlopen(req) as response: payload=json.load(response)
        assert payload['diagnostics']
    finally:
        server.shutdown(); server.server_close(); thread.join()
