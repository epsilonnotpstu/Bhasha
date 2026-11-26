"""Standard-library web playground for Bhasha."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
from difflib import SequenceMatcher
from dataclasses import asdict
from .cli import compile_text
from .backend.vm import VM
from .cfg_new import build_cfg
from .optimizer import optimize
from .semantic import analyze

ROOT = Path(__file__).parents[2] / "tools" / "playground"
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_POST(self):
        if self.path != "/api/compile": self.send_error(404); return
        try:
            raw=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            source=raw.get("source",""); tokens,tree,diagnostics,ir=compile_text(source,"playground.bh")
            response={"diagnostics":[d.render(source) for d in diagnostics], "diagnosticItems":[{'line':d.line,'column':d.column,'message':d.message,'rendered':d.render(source)} for d in diagnostics], "warnings":[],"tokens":[asdict(t) for t in tokens]}
            if not diagnostics:
                opt,stats=optimize(ir); cfg=build_cfg(ir);_,analyzer=analyze(tree,'playground.bh')
                response['warnings']=[d.render(source) for d in analyzer.warnings]
                inputs=iter(raw.get('input','').splitlines())
                def read_input():
                    try: return next(inputs)
                    except StopIteration: raise ValueError('Program requires input; supply it in the API input field')
                vm=VM(input_fn=read_input,max_steps=100000)
                try:vm.exec(tree,vm.global_env)
                except (ValueError,ZeroDivisionError,RuntimeError,IndexError,RecursionError) as exc:response['diagnostics'].append(f'runtime error: {exc}')
                output='\n'.join(vm.output)+ ('\n' if vm.output else '')
                diff=[]
                for tag,a,b,c,d in SequenceMatcher(a=ir,b=opt,autojunk=False).get_opcodes():
                    if tag in ('delete','replace'):diff.extend({'kind':'removed','line':line} for line in ir[a:b])
                    if tag=='equal':diff.extend({'kind':'unchanged','line':line} for line in ir[a:b])
                    if tag in ('insert','replace'):diff.extend({'kind':'added','line':line} for line in opt[c:d])
                response.update({"ast":asdict(tree),"symbols":analyzer.symbol_tables(),"tac":ir,"optTac":opt,"tacDiff":diff,"stats":stats,"cfg":cfg.dot(),"cfgBlocks":cfg.blocks,"cfgEdges":cfg.edges,"output":output})
            self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers(); self.wfile.write(json.dumps(response,ensure_ascii=False).encode())
        except Exception as e: self.send_error(400,str(e))
def main():
    print("Bhasha playground: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
if __name__ == "__main__": main()
