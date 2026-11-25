"""Standard-library web playground for Bhasha."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
from dataclasses import asdict
from .cli import compile_text
from .backend.vm import run
from .cfg_new import build_cfg
from .optimizer import optimize

ROOT = Path(__file__).parents[2] / "tools" / "playground"
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_POST(self):
        if self.path != "/api/compile": self.send_error(404); return
        try:
            raw=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            source=raw.get("source",""); tokens,tree,diagnostics,ir=compile_text(source,"playground.bh")
            response={"diagnostics":[d.render(source) for d in diagnostics], "tokens":[asdict(t) for t in tokens]}
            if not diagnostics:
                opt,stats=optimize(ir); response.update({"ast":asdict(tree),"tac":ir,"optTac":opt,"stats":stats,"cfg":build_cfg(ir).dot(),"output":run(tree)})
            self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers(); self.wfile.write(json.dumps(response,ensure_ascii=False).encode())
        except Exception as e: self.send_error(400,str(e))
def main():
    print("Bhasha playground: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
if __name__ == "__main__": main()
